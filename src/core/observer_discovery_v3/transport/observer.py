"""Frozen closed-observer commuting squares across exact representations."""

from __future__ import annotations

from dataclasses import replace
import logging

from ..dsl.runtime import (
    ClosedDslError,
    observer_program_digest,
    term_kind_cost,
)
from ..dsl.types import ClosedObserverGrammar, ClosedObserverTerm, ClosedWorkerConfig
from ..schema.canonical import canonical_presentation
from ..schema.types import (
    CanonicalPresentation,
    RepresentationProtocolError,
    RepresentationScalar,
)
from ..worker.runtime import READY, run_closed_observers_isolated, validate_closed_receipt
from ...proof_core_codec import digest_data
from .observer_types import (
    OBSERVER_TRANSPORT_BLOCKED,
    OBSERVER_TRANSPORT_BOUNDARY,
    OBSERVER_TRANSPORT_REFUTED,
    OBSERVER_TRANSPORT_VERIFIED,
    ObserverTransportReceipt,
    ObserverTransportResult,
)
from .protocol import apply_representation_transport, validate_representation_transport_result
from .types import (
    TRANSPORT_APPLIED,
    CategoryBijection,
    RepresentationObstruction,
    RepresentationTransportResult,
    RepresentationTransportSpec,
)

logger = logging.getLogger(__name__)

_MAX_RESPONSE_ENTRIES = 128
_MAX_TEXT_BYTES = 512
_HEX = frozenset("0123456789abcdef")


def check_observer_representation_transport(
    source: CanonicalPresentation,
    transport_spec: RepresentationTransportSpec,
    transport_result: RepresentationTransportResult,
    source_grammar: ClosedObserverGrammar,
    source_term: ClosedObserverTerm,
    destination_grammar: ClosedObserverGrammar,
    destination_term: ClosedObserverTerm,
    response_bijection: CategoryBijection,
    worker_config: ClosedWorkerConfig = ClosedWorkerConfig(),
) -> ObserverTransportResult:
    """Check one predeclared finite observer/data/response commuting square."""
    logger.debug("check_observer_representation_transport entry")
    try:
        if type(source) is not CanonicalPresentation:
            raise RepresentationProtocolError("invalid-presentation", "source")
        source_snapshot = canonical_presentation(source.schema, source.rows)
        if source_snapshot != source:
            raise RepresentationProtocolError("invalid-presentation", "source")
        source = source_snapshot
        expected_transport = apply_representation_transport(source, transport_spec)
        if (
            transport_result.status != TRANSPORT_APPLIED
            or transport_result.destination is None
            or transport_result.receipt is None
            or transport_result != expected_transport
            or not validate_representation_transport_result(expected_transport, source, transport_spec)
        ):
            raise RepresentationProtocolError("invalid-transport", "applied-transport-required")
        transport_result = expected_transport
        if (
            term_kind_cost(source_term, source_grammar)[0] != "scalar"
            or term_kind_cost(
                destination_term,
                destination_grammar,
            )[0]
            != "scalar"
        ):
            raise RepresentationProtocolError("invalid-observer", "scalar-terms-required")
        response, response_pairs = _response_map(response_bijection)
        source_program = _program_digest(source_grammar, source_term)
        destination_program = _program_digest(destination_grammar, destination_term)
        source_worker = run_closed_observers_isolated(
            source_grammar,
            (source_term,),
            tuple(tuple(row.values) for row in source.rows),
            worker_config,
            expected_program_digest=source_program,
        )
        destination = transport_result.destination
        destination_worker = run_closed_observers_isolated(
            destination_grammar,
            (destination_term,),
            tuple(tuple(row.values) for row in destination.rows),
            worker_config,
            expected_program_digest=destination_program,
        )
        if (
            source_worker.status != READY
            or destination_worker.status != READY
            or not validate_closed_receipt(source_worker)
            or not validate_closed_receipt(destination_worker)
        ):
            raise RepresentationProtocolError("worker-blocked", "closed-evaluation-required")
        source_outputs = dict(zip((row.row_id for row in source.rows), source_worker.outputs[0], strict=True))
        destination_outputs = dict(
            zip((row.row_id for row in destination.rows), destination_worker.outputs[0], strict=True)
        )
        if set(source_outputs) != set(destination_outputs):
            raise RepresentationProtocolError("invalid-transport", "lineage-row-set")
        source_keys = {_scalar_key(value) for value in source_outputs.values()}
        if not source_keys <= set(response):
            raise RepresentationProtocolError("invalid-response-map", "observed-domain-not-covered")
        mismatches = sum(
            _scalar_key(response[_scalar_key(source_outputs[row_id])]) != _scalar_key(destination_outputs[row_id])
            for row_id in source_outputs
        )
        response_digest = digest_data(
            [{"source": _scalar_data(left), "destination": _scalar_data(right)} for left, right in response_pairs],
            "veyra.observer-discovery.v3.observer-transport-response.v1",
        )
        draft = ObserverTransportReceipt(
            transport_result.receipt.receipt_digest,
            source_program,
            destination_program,
            response_digest,
            source_worker.result_digest,
            destination_worker.result_digest,
            len(source.rows),
            mismatches,
            "",
            OBSERVER_TRANSPORT_BOUNDARY,
        )
        receipt = _bind_receipt(draft)
        if mismatches:
            status = OBSERVER_TRANSPORT_REFUTED
            obstructions = (RepresentationObstruction("commuting-square-failed", str(mismatches)),)
        else:
            status = OBSERVER_TRANSPORT_VERIFIED
            obstructions = ()
        result = ObserverTransportResult(status, receipt, obstructions, OBSERVER_TRANSPORT_BOUNDARY)
        logger.info("check_observer_representation_transport state=%s mismatches=%d", status, mismatches)
        logger.debug("check_observer_representation_transport exit status=%s", status)
        return result
    except (ClosedDslError, RepresentationProtocolError, AttributeError, TypeError, ValueError) as exc:
        reason = exc.reason if isinstance(exc, (ClosedDslError, RepresentationProtocolError)) else type(exc).__name__
        logger.error("check_observer_representation_transport state=BLOCKED reason=%s", reason)
        return ObserverTransportResult(
            OBSERVER_TRANSPORT_BLOCKED,
            None,
            (RepresentationObstruction(reason, "observer-transport-blocked"),),
            OBSERVER_TRANSPORT_BOUNDARY,
        )


def validate_observer_transport_result(
    result: object,
    source: CanonicalPresentation,
    transport_spec: RepresentationTransportSpec,
    transport_result: RepresentationTransportResult,
    source_grammar: ClosedObserverGrammar,
    source_term: ClosedObserverTerm,
    destination_grammar: ClosedObserverGrammar,
    destination_term: ClosedObserverTerm,
    response_bijection: CategoryBijection,
    worker_config: ClosedWorkerConfig = ClosedWorkerConfig(),
) -> bool:
    """Replay the complete finite experiment and require exact terminal equality."""
    logger.debug("validate_observer_transport_result entry type=%s", type(result).__name__)
    if type(result) is not ObserverTransportResult:
        return False
    try:
        expected = check_observer_representation_transport(
            source,
            transport_spec,
            transport_result,
            source_grammar,
            source_term,
            destination_grammar,
            destination_term,
            response_bijection,
            worker_config,
        )
        valid = result == expected and (result.receipt is None or _receipt_valid(result.receipt))
    except (AttributeError, TypeError, ValueError):
        logger.error("validate_observer_transport_result malformed")
        return False
    logger.debug("validate_observer_transport_result exit valid=%s", valid)
    return valid


def _response_map(
    bijection: CategoryBijection,
) -> tuple[
    dict[tuple[str, object], RepresentationScalar],
    tuple[tuple[RepresentationScalar, RepresentationScalar], ...],
]:
    logger.debug("_response_map entry type=%s", type(bijection).__name__)
    if (
        type(bijection) is not CategoryBijection
        or type(bijection.entries) is not tuple
        or not 1 <= len(bijection.entries) <= _MAX_RESPONSE_ENTRIES
        or any(type(entry) is not tuple or len(entry) != 2 for entry in bijection.entries)
    ):
        raise RepresentationProtocolError("invalid-response-map", "shape")
    pairs = tuple((_validated_scalar(left), _validated_scalar(right)) for left, right in bijection.entries)
    sources = tuple(_scalar_key(left) for left, _right in pairs)
    destinations = tuple(_scalar_key(right) for _left, right in pairs)
    if len(set(sources)) != len(sources) or len(set(destinations)) != len(destinations):
        raise RepresentationProtocolError("invalid-response-map", "bijection")
    mapping = {source_key: right for source_key, (_left, right) in zip(sources, pairs, strict=True)}
    result = mapping, pairs
    logger.debug("_response_map exit entries=%d", len(mapping))
    return result


def _validated_scalar(value: object) -> RepresentationScalar:
    logger.debug("_validated_scalar entry type=%s", type(value).__name__)
    if type(value) is str:
        if not value or len(value) > _MAX_TEXT_BYTES or len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise RepresentationProtocolError("invalid-response-map", "string")
        result: RepresentationScalar = value
    elif type(value) is int:
        if value.bit_length() > 256:
            raise RepresentationProtocolError("invalid-response-map", "integer")
        result = value
    elif type(value) is bool:
        result = value
    else:
        raise RepresentationProtocolError("invalid-response-map", "scalar")
    logger.debug("_validated_scalar exit")
    return result


def _program_digest(grammar: ClosedObserverGrammar, term: ClosedObserverTerm) -> str:
    logger.debug("_program_digest entry")
    result = observer_program_digest(grammar, (term,))
    logger.debug("_program_digest exit digest=%s", result[:12])
    return result


def _bind_receipt(receipt: ObserverTransportReceipt) -> ObserverTransportReceipt:
    logger.debug("_bind_receipt entry")
    result = replace(
        receipt,
        result_digest=digest_data(
            _receipt_data(receipt),
            "veyra.observer-discovery.v3.observer-transport-result.v1",
        ),
    )
    logger.debug("_bind_receipt exit")
    return result


def _receipt_valid(receipt: ObserverTransportReceipt) -> bool:
    logger.debug("_receipt_valid entry type=%s", type(receipt).__name__)
    valid = (
        type(receipt) is ObserverTransportReceipt
        and receipt.boundary == OBSERVER_TRANSPORT_BOUNDARY
        and all(
            _is_digest(value)
            for value in (
                receipt.representation_transport_receipt,
                receipt.source_program_digest,
                receipt.destination_program_digest,
                receipt.response_map_digest,
                receipt.source_worker_result,
                receipt.destination_worker_result,
                receipt.result_digest,
            )
        )
        and type(receipt.checked_rows) is int
        and receipt.checked_rows > 0
        and type(receipt.mismatch_count) is int
        and 0 <= receipt.mismatch_count <= receipt.checked_rows
        and _bind_receipt(replace(receipt, result_digest="")) == receipt
    )
    logger.debug("_receipt_valid exit valid=%s", valid)
    return valid


def _receipt_data(receipt: ObserverTransportReceipt) -> dict[str, object]:
    logger.debug("_receipt_data entry")
    result = {
        "representation_transport_receipt": receipt.representation_transport_receipt,
        "source_program": receipt.source_program_digest,
        "destination_program": receipt.destination_program_digest,
        "response_map": receipt.response_map_digest,
        "source_worker": receipt.source_worker_result,
        "destination_worker": receipt.destination_worker_result,
        "checked_rows": receipt.checked_rows,
        "mismatches": receipt.mismatch_count,
        "boundary": receipt.boundary,
    }
    logger.debug("_receipt_data exit")
    return result


def _scalar_data(value: RepresentationScalar) -> dict[str, object]:
    logger.debug("_scalar_data entry type=%s", type(value).__name__)
    result = {"type": type(value).__name__, "value": value}
    logger.debug("_scalar_data exit")
    return result


def _scalar_key(value: RepresentationScalar) -> tuple[str, object]:
    logger.debug("_scalar_key entry type=%s", type(value).__name__)
    result = (type(value).__name__, value)
    logger.debug("_scalar_key exit")
    return result


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in _HEX for character in value)
    logger.debug("_is_digest exit valid=%s", result)
    return result
