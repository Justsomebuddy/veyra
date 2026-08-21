"""Isolated subprocess boundary for the closed Phase-III observer DSL."""

from __future__ import annotations

from dataclasses import replace
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, NoReturn

from ..dsl.runtime import (
    ClosedDslError,
    canonical_value_data,
    canonical_value_from_data,
    closed_rows_digest,
    evaluate_closed_term,
    grammar_data,
    grammar_digest,
    grammar_from_data,
    observer_program_digest,
    term_data,
    term_from_data,
    term_kind_cost,
    terms_digest,
)
from ..dsl.types import (
    ClosedEvaluationReceipt,
    ClosedObserverGrammar,
    ClosedObserverTerm,
    ClosedValue,
    ClosedWorkerConfig,
)
from ...proof_core_codec import canonical_json, digest_data

logger = logging.getLogger(__name__)
READY = "READY"
BLOCKED = "BLOCKED"
BOUNDARY = (
    "closed built-in categorical semantics only; evaluation occurs in a resource-bounded subprocess; "
    "the parent controls local interpreter/path and timeout but this is not a container, syscall sandbox, "
    "authentication, one-shot ledger, causal claim, or semantic explanation"
)
_WORKER_CODE = """import runpy
import sys
import types
root = sys.argv[1]
packages = (
    ("src", root + "/src"),
    ("src.core", root + "/src/core"),
    ("src.core.observer_discovery_v3", root + "/src/core/observer_discovery_v3"),
    ("src.core.observer_discovery_v3.dsl", root + "/src/core/observer_discovery_v3/dsl"),
    ("src.core.observer_discovery_v3.worker", root + "/src/core/observer_discovery_v3/worker"),
)
for name, path in packages:
    package = types.ModuleType(name)
    package.__package__ = name
    package.__path__ = [path]
    sys.modules[name] = package
runpy.run_module("src.core.observer_discovery_v3.worker.runtime", run_name="__main__")
"""
_MAX_RECEIPT_OUTPUT_UNITS = 1_000_000


class ClosedWorkerError(ValueError):
    """Stable host-side preflight, transport, or receipt rejection."""

    def __init__(self, reason: str) -> None:
        logger.error("ClosedWorkerError entry reason=%s", reason)
        self.reason = reason
        super().__init__(reason)
        logger.debug("ClosedWorkerError exit")


def run_closed_observers_isolated(
    grammar: ClosedObserverGrammar,
    terms: tuple[ClosedObserverTerm, ...],
    rows: tuple[ClosedValue, ...],
    config: ClosedWorkerConfig = ClosedWorkerConfig(),
    *,
    expected_program_digest: str | None = None,
) -> ClosedEvaluationReceipt:
    """Preflight, execute, and verify the closed evaluator in a child process."""
    logger.debug("run_closed_observers_isolated entry")
    request_digest = grammar_root = terms_root = rows_root = ""
    try:
        request = _request_data(grammar, terms, rows, config)
        grammar, terms, rows, config = _request_from_data(request)
        request_text = canonical_json(request)
        request_bytes = request_text.encode()
        if len(request_bytes) > config.max_request_bytes:
            raise ClosedWorkerError("request-size")
        request_digest = digest_data(request, "veyra.closed-observer.request.v1")
        grammar_root = grammar_digest(grammar)
        terms_root = terms_digest(terms, grammar)
        program_root = observer_program_digest(grammar, terms)
        if expected_program_digest is not None and (
            type(expected_program_digest) is not str
            or not _hex_digest(expected_program_digest)
            or expected_program_digest != program_root
        ):
            raise ClosedWorkerError("expected-program-mismatch")
        rows_root = closed_rows_digest(rows)
        completed = _invoke_worker(request_bytes, config)
        if len(completed.stdout) > config.max_response_bytes:
            raise ClosedWorkerError("response-size")
        if completed.returncode != 0:
            raise ClosedWorkerError("worker-exit")
        response = json.loads(completed.stdout)
        if canonical_json(response).encode() != completed.stdout:
            raise ClosedWorkerError("noncanonical-response")
        outputs = _validate_worker_response(response, request_digest, grammar, terms, rows, config)
        output_root = digest_data(
            [[canonical_value_data(value) for value in column] for column in outputs],
            "veyra.closed-observer.outputs.v1",
        )
        receipt = ClosedEvaluationReceipt(
            READY,
            request_digest,
            grammar_root,
            terms_root,
            rows_root,
            outputs,
            output_root,
            "",
            "",
            BOUNDARY,
        )
        result = bind_closed_receipt(receipt)
        logger.info("run_closed_observers_isolated state=READY terms=%d rows=%d", len(terms), len(rows))
        logger.debug("run_closed_observers_isolated exit status=READY")
        return result
    except subprocess.TimeoutExpired:
        logger.error("run_closed_observers_isolated state=BLOCKED reason=worker-timeout")
        return _blocked_receipt(request_digest, grammar_root, terms_root, rows_root, "worker-timeout")
    except (ClosedDslError, ClosedWorkerError, TypeError, ValueError, OSError) as exc:
        reason = exc.reason if isinstance(exc, (ClosedDslError, ClosedWorkerError)) else type(exc).__name__
        logger.error("run_closed_observers_isolated state=BLOCKED reason=%s", reason)
        return _blocked_receipt(request_digest, grammar_root, terms_root, rows_root, reason)


def validate_closed_receipt(
    receipt: object,
    *,
    expected_request_digest: str | None = None,
    expected_grammar_digest: str | None = None,
    expected_terms_digest: str | None = None,
    expected_rows_digest: str | None = None,
) -> bool:
    """Replay exact receipt shape, output root, boundary, and result binding."""
    logger.debug("validate_closed_receipt entry type=%s", type(receipt).__name__)
    try:
        if type(receipt) is not ClosedEvaluationReceipt or receipt.status not in {READY, BLOCKED}:
            return False
        digests = (
            receipt.request_digest,
            receipt.grammar_digest,
            receipt.terms_digest,
            receipt.rows_digest,
            receipt.output_digest,
            receipt.result_digest,
        )
        if any(type(value) is not str or (value and not _hex_digest(value)) for value in digests):
            return False
        if expected_request_digest is not None and receipt.request_digest != expected_request_digest:
            return False
        if expected_grammar_digest is not None and receipt.grammar_digest != expected_grammar_digest:
            return False
        if expected_terms_digest is not None and receipt.terms_digest != expected_terms_digest:
            return False
        if expected_rows_digest is not None and receipt.rows_digest != expected_rows_digest:
            return False
        if (
            type(receipt.outputs) is not tuple
            or len(receipt.outputs) > 4096
            or sum(len(column) for column in receipt.outputs if type(column) is tuple) > _MAX_RECEIPT_OUTPUT_UNITS
            or any(type(column) is not tuple or len(column) > 8192 for column in receipt.outputs)
            or type(receipt.obstruction) is not str
            or type(receipt.boundary) is not str
            or receipt.boundary != BOUNDARY
        ):
            return False
        if not _receipt_outputs_within_budget(receipt.outputs):
            return False
        if len(receipt.obstruction) > 256 or len(receipt.obstruction.encode()) > 256:
            return False
        if receipt.status == READY:
            if any(not value for value in digests) or receipt.obstruction:
                return False
            expected_output = digest_data(
                [[canonical_value_data(value) for value in column] for column in receipt.outputs],
                "veyra.closed-observer.outputs.v1",
            )
            if expected_output != receipt.output_digest:
                return False
        elif receipt.outputs or receipt.output_digest or not receipt.obstruction:
            return False
        blank = replace(receipt, result_digest="")
        valid = bind_closed_receipt(blank) == receipt
    except (AttributeError, TypeError, ValueError, RecursionError, OverflowError):
        logger.error("validate_closed_receipt malformed")
        return False
    logger.debug("validate_closed_receipt exit valid=%s", valid)
    return valid


def bind_closed_receipt(receipt: ClosedEvaluationReceipt) -> ClosedEvaluationReceipt:
    """Bind every receipt field under the terminal result domain."""
    logger.debug("bind_closed_receipt entry status=%s", receipt.status)
    digest = digest_data(_receipt_data(receipt), "veyra.closed-observer.result.v1")
    result = replace(receipt, result_digest=digest)
    logger.debug("bind_closed_receipt exit digest=%s", digest[:12])
    return result


def _request_data(
    grammar: ClosedObserverGrammar,
    terms: tuple[ClosedObserverTerm, ...],
    rows: tuple[ClosedValue, ...],
    config: ClosedWorkerConfig,
) -> dict[str, object]:
    logger.debug("_request_data entry")
    _validate_config(config)
    if type(terms) is not tuple or not terms or len(terms) > config.max_terms:
        raise ClosedWorkerError("term-count")
    if type(rows) is not tuple or not rows or len(rows) > config.max_rows:
        raise ClosedWorkerError("row-count")
    for term in terms:
        term_kind_cost(term, grammar)
    if any(type(row) is not tuple or len(row) != grammar.input_arity for row in rows):
        raise ClosedWorkerError("row-shape")
    if any(type(value) not in {str, int, bool} for row in rows for value in row):
        raise ClosedWorkerError("row-cell-type")
    row_data = [canonical_value_data(row) for row in rows]
    node_count = sum(_term_nodes(term) for term in terms)
    if (
        node_count > config.max_ast_nodes
        or len(terms) * len(rows) * config.determinism_checks > config.max_output_units
    ):
        raise ClosedWorkerError("work-limit")
    result = {
        "tag": "closed-observer-request-v1",
        "grammar": grammar_data(grammar),
        "terms": [term_data(term) for term in terms],
        "rows": row_data,
        "config": _config_data(config),
    }
    logger.debug("_request_data exit terms=%d rows=%d", len(terms), len(rows))
    return result


def _validate_config(config: ClosedWorkerConfig) -> None:
    logger.debug("_validate_config entry")
    if type(config) is not ClosedWorkerConfig:
        raise ClosedWorkerError("config-type")
    if type(config.isolation_profile) is not str or config.isolation_profile not in {
        "logical-subprocess",
        "strict",
    }:
        raise ClosedWorkerError("isolation-profile")
    if config.isolation_profile == "strict":
        raise ClosedWorkerError("strict-isolation-unavailable")
    values = (
        config.timeout_ms,
        config.cpu_seconds,
        config.memory_limit_mb,
        config.max_request_bytes,
        config.max_response_bytes,
        config.max_rows,
        config.max_terms,
        config.max_ast_nodes,
        config.max_output_units,
        config.determinism_checks,
    )
    if any(type(value) is not int or value < 1 for value in values):
        raise ClosedWorkerError("config-positive-integers")
    if (
        not 50 <= config.timeout_ms <= 30_000
        or not 1 <= config.cpu_seconds <= 10
        or not 128 <= config.memory_limit_mb <= 2048
    ):
        raise ClosedWorkerError("host-limit-range")
    if (
        config.max_request_bytes > 4_000_000
        or config.max_response_bytes > 16_000_000
        or config.max_rows > 8192
        or config.max_terms > 4096
        or config.max_ast_nodes > 65536
        or config.max_output_units > 1_000_000
        or config.determinism_checks > 8
    ):
        raise ClosedWorkerError("worker-limit-range")
    logger.debug("_validate_config exit")


def _config_data(config: ClosedWorkerConfig) -> dict[str, object]:
    logger.debug("_config_data entry")
    result = {
        "isolation_profile": config.isolation_profile,
        "timeout_ms": config.timeout_ms,
        "cpu_seconds": config.cpu_seconds,
        "memory_limit_mb": config.memory_limit_mb,
        "max_request_bytes": config.max_request_bytes,
        "max_response_bytes": config.max_response_bytes,
        "max_rows": config.max_rows,
        "max_terms": config.max_terms,
        "max_ast_nodes": config.max_ast_nodes,
        "max_output_units": config.max_output_units,
        "determinism_checks": config.determinism_checks,
    }
    logger.debug("_config_data exit")
    return result


def _config_from_data(data: object) -> ClosedWorkerConfig:
    logger.debug("_config_from_data entry")
    if type(data) is not dict or set(data) != set(_config_data(ClosedWorkerConfig())):
        raise ClosedWorkerError("config-shape")
    result = ClosedWorkerConfig(**data)
    _validate_config(result)
    logger.debug("_config_from_data exit")
    return result


def _request_from_data(
    data: object,
) -> tuple[
    ClosedObserverGrammar,
    tuple[ClosedObserverTerm, ...],
    tuple[ClosedValue, ...],
    ClosedWorkerConfig,
]:
    """Detach one exact canonical request graph before worker or host evaluation."""
    logger.debug("_request_from_data entry")
    if (
        type(data) is not dict
        or set(data) != {"tag", "grammar", "terms", "rows", "config"}
        or data.get("tag") != "closed-observer-request-v1"
        or type(data["terms"]) is not list
        or type(data["rows"]) is not list
        or len(data["terms"]) > 4096
        or len(data["rows"]) > 8192
    ):
        raise ClosedWorkerError("request-shape")
    config = _config_from_data(data["config"])
    grammar = grammar_from_data(data["grammar"])
    terms = tuple(term_from_data(item, node_limit=config.max_ast_nodes) for item in data["terms"])
    rows = tuple(canonical_value_from_data(item) for item in data["rows"])
    logger.debug("_request_from_data exit terms=%d rows=%d", len(terms), len(rows))
    return grammar, terms, rows, config


def _invoke_worker(request: bytes, config: ClosedWorkerConfig) -> subprocess.CompletedProcess[bytes]:
    logger.debug("_invoke_worker entry bytes=%d", len(request))
    if os.name != "posix":
        raise ClosedWorkerError("isolation-unavailable")
    root = str(Path(__file__).resolve().parents[4])
    command = (sys.executable, "-I", "-c", _WORKER_CODE, root)
    result = subprocess.run(
        command,
        input=request,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=config.timeout_ms / 1000,
        check=False,
        close_fds=True,
        env={"PYTHONHASHSEED": "0"},
    )
    logger.debug("_invoke_worker exit returncode=%d", result.returncode)
    return result


def _set_resource_limit(
    resource_module: Any,
    kind: int,
    requested: int,
    *,
    allow_darwin_as_unavailable: bool = False,
) -> bool:
    """Install one non-raising ceiling while preserving stricter inherited limits."""
    logger.debug("_set_resource_limit entry")
    inherited = resource_module.getrlimit(kind)
    infinity = resource_module.RLIM_INFINITY
    target = requested
    for inherited_limit in inherited:
        if inherited_limit != infinity:
            target = min(target, inherited_limit)
    expected = (target, target)
    try:
        resource_module.setrlimit(kind, expected)
    except ValueError as exc:
        confirmed_darwin_as_gap = (
            allow_darwin_as_unavailable
            and sys.platform == "darwin"
            and kind == resource_module.RLIMIT_AS
            and getattr(resource_module, "RLIMIT_RSS", None) == resource_module.RLIMIT_AS
            and inherited == (infinity, infinity)
        )
        if not confirmed_darwin_as_gap:
            raise
        try:
            resource_module.setrlimit(kind, inherited)
        except (OSError, ValueError):
            raise exc
        if resource_module.getrlimit(kind) != inherited:
            raise ClosedWorkerError("resource-limit-probe-mismatch") from exc
        logger.warning("_set_resource_limit confirmed unavailable resource=RLIMIT_AS platform=darwin")
        logger.debug("_set_resource_limit exit applied=False")
        return False
    if resource_module.getrlimit(kind) != expected:
        raise ClosedWorkerError("resource-limit-not-applied")
    logger.debug("_set_resource_limit exit applied=True")
    return True


def _apply_limits(config: ClosedWorkerConfig, resource_module: Any | None = None) -> None:
    logger.debug("_apply_limits entry")
    if resource_module is None:
        import resource as resource_module

    memory = config.memory_limit_mb * 1024 * 1024
    _set_resource_limit(resource_module, resource_module.RLIMIT_CPU, config.cpu_seconds)
    _set_resource_limit(
        resource_module,
        resource_module.RLIMIT_AS,
        memory,
        allow_darwin_as_unavailable=True,
    )
    _set_resource_limit(resource_module, resource_module.RLIMIT_FSIZE, config.max_response_bytes)
    _set_resource_limit(resource_module, resource_module.RLIMIT_NOFILE, 32)
    logger.debug("_apply_limits exit")


def _apply_hard_limits(resource_module: Any | None = None) -> None:
    """Install absolute child ceilings before decoding the bounded request."""
    logger.debug("_apply_hard_limits entry")
    if resource_module is None:
        import resource as resource_module

    _set_resource_limit(resource_module, resource_module.RLIMIT_CPU, 10)
    _set_resource_limit(
        resource_module,
        resource_module.RLIMIT_AS,
        2048 * 1024 * 1024,
        allow_darwin_as_unavailable=True,
    )
    _set_resource_limit(resource_module, resource_module.RLIMIT_FSIZE, 16_000_000)
    _set_resource_limit(resource_module, resource_module.RLIMIT_NOFILE, 32)
    logger.debug("_apply_hard_limits exit")


def _worker_main() -> int:
    logger.debug("_worker_main entry")
    try:
        _apply_hard_limits()
        raw = sys.stdin.buffer.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ClosedWorkerError("request-size")
        data = json.loads(raw)
        grammar, terms, rows, config = _request_from_data(data)
        _apply_limits(config)
        if len(raw) > config.max_request_bytes:
            raise ClosedWorkerError("request-size")
        canonical_request = _request_data(grammar, terms, rows, config)
        if canonical_json(canonical_request).encode() != raw:
            raise ClosedWorkerError("noncanonical-request")
        request_digest = digest_data(canonical_request, "veyra.closed-observer.request.v1")
        outputs = []
        retained = 0
        for term in terms:
            column = []
            for row in rows:
                values = tuple(evaluate_closed_term(term, row, grammar) for _ in range(config.determinism_checks))
                if len(set(canonical_json(canonical_value_data(value)) for value in values)) != 1:
                    raise ClosedWorkerError("nondeterministic-closed-semantics")
                retained += 1
                if retained > config.max_output_units:
                    raise ClosedWorkerError("output-limit")
                column.append(values[0])
            outputs.append(tuple(column))
        response = {
            "tag": "closed-observer-response-v1",
            "status": READY,
            "request_digest": request_digest,
            "outputs": [[canonical_value_data(value) for value in column] for column in outputs],
        }
        response_text = canonical_json(response)
        if len(response_text.encode()) > config.max_response_bytes:
            raise ClosedWorkerError("response-size")
        sys.stdout.write(response_text)
        logger.debug("_worker_main exit status=READY")
        return 0
    except Exception as exc:
        reason = exc.reason if isinstance(exc, (ClosedDslError, ClosedWorkerError)) else type(exc).__name__
        logger.error("_worker_main blocked reason=%s", reason)
        response = {"tag": "closed-observer-response-v1", "status": BLOCKED, "request_digest": "", "reason": reason}
        sys.stdout.write(canonical_json(response))
        logger.debug("_worker_main exit status=BLOCKED")
        return 0


def _validate_worker_response(
    data: object,
    request_digest: str,
    grammar: ClosedObserverGrammar,
    terms: tuple[ClosedObserverTerm, ...],
    rows: tuple[ClosedValue, ...],
    config: ClosedWorkerConfig,
) -> tuple[tuple[ClosedValue, ...], ...]:
    logger.debug("_validate_worker_response entry")
    if type(data) is not dict or data.get("tag") != "closed-observer-response-v1":
        raise ClosedWorkerError("response-shape")
    if data.get("status") == BLOCKED:
        if set(data) != {"tag", "status", "request_digest", "reason"} or type(data.get("reason")) is not str:
            raise ClosedWorkerError("response-shape")
        raise ClosedWorkerError(f"worker-blocked-{data['reason']}")
    if (
        set(data) != {"tag", "status", "request_digest", "outputs"}
        or data.get("status") != READY
        or data.get("request_digest") != request_digest
        or type(data.get("outputs")) is not list
    ):
        raise ClosedWorkerError("response-mismatch")
    outputs = tuple(tuple(canonical_value_from_data(value) for value in column) for column in data["outputs"])
    if len(outputs) != len(terms) or any(len(column) != len(rows) for column in outputs):
        raise ClosedWorkerError("response-dimensions")
    if sum(len(column) for column in outputs) > config.max_output_units:
        raise ClosedWorkerError("response-output-limit")
    for term, column in zip(terms, outputs, strict=True):
        for row, value in zip(rows, column, strict=True):
            expected = canonical_json(canonical_value_data(evaluate_closed_term(term, row, grammar)))
            if expected != canonical_json(canonical_value_data(value)):
                raise ClosedWorkerError("response-replay-mismatch")
    logger.debug("_validate_worker_response exit")
    return outputs


def _term_nodes(term: ClosedObserverTerm) -> int:
    logger.debug("_term_nodes entry")
    active: set[int] = set()

    def count(node: ClosedObserverTerm) -> int:
        if id(node) in active:
            raise ClosedWorkerError("cyclic-term")
        active.add(id(node))
        result = 1 + sum(count(child) for child in node.children)
        active.remove(id(node))
        return result

    result = count(term)
    logger.debug("_term_nodes exit count=%d", result)
    return result


def _receipt_data(receipt: ClosedEvaluationReceipt) -> dict[str, object]:
    logger.debug("_receipt_data entry status=%s", receipt.status)
    result = {
        "status": receipt.status,
        "request_digest": receipt.request_digest,
        "grammar_digest": receipt.grammar_digest,
        "terms_digest": receipt.terms_digest,
        "rows_digest": receipt.rows_digest,
        "outputs": [[canonical_value_data(value) for value in column] for column in receipt.outputs],
        "output_digest": receipt.output_digest,
        "obstruction": receipt.obstruction,
        "boundary": receipt.boundary,
    }
    logger.debug("_receipt_data exit")
    return result


def _receipt_outputs_within_budget(outputs: tuple[tuple[ClosedValue, ...], ...]) -> bool:
    """Bound the occurrence-expanded canonical work before hashing a receipt."""
    logger.debug("_receipt_outputs_within_budget entry columns=%d", len(outputs))
    total_units = 0
    try:
        for column in outputs:
            for value in column:
                value_units = 0
                stack: list[tuple[object, int]] = [(value, 0)]
                while stack:
                    node, depth = stack.pop()
                    total_units += 1
                    value_units += 1
                    if total_units > _MAX_RECEIPT_OUTPUT_UNITS or value_units > 4096 or depth > 16:
                        logger.error("_receipt_outputs_within_budget exceeded")
                        return False
                    if type(node) is tuple:
                        child_count = len(node)
                        if child_count > 4096 - value_units or child_count > _MAX_RECEIPT_OUTPUT_UNITS - total_units:
                            logger.error("_receipt_outputs_within_budget child fanout exceeded")
                            return False
                        stack.extend((item, depth + 1) for item in reversed(node))
                    elif type(node) is str:
                        if len(node) > 4096 or len(node.encode("utf-8")) > 4096:
                            return False
                    elif type(node) is int:
                        if node.bit_length() > 32768:
                            return False
                    elif type(node) is not bool:
                        return False
    except (AttributeError, TypeError, UnicodeError, OverflowError):
        logger.error("_receipt_outputs_within_budget malformed")
        return False
    logger.debug("_receipt_outputs_within_budget exit units=%d", total_units)
    return True


def _blocked_receipt(
    request: str,
    grammar: str,
    terms: str,
    rows: str,
    obstruction: str,
) -> ClosedEvaluationReceipt:
    logger.debug("_blocked_receipt entry obstruction=%s", obstruction)
    result = bind_closed_receipt(
        ClosedEvaluationReceipt(
            BLOCKED,
            request,
            grammar,
            terms,
            rows,
            (),
            "",
            "",
            obstruction,
            BOUNDARY,
        )
    )
    logger.debug("_blocked_receipt exit")
    return result


def _hex_digest(value: str) -> bool:
    logger.debug("_hex_digest entry")
    result = len(value) == 64 and all(character in "0123456789abcdef" for character in value)
    logger.debug("_hex_digest exit valid=%s", result)
    return result


def main() -> NoReturn:
    """Run one request and exit without exposing an interactive surface."""
    logger.debug("main entry")
    raise SystemExit(_worker_main())


if __name__ == "__main__":
    main()
