from __future__ import annotations

from dataclasses import replace
import json
import subprocess

import pytest

from src.core.observer_discovery_v3.dsl.runtime import (
    ClosedDslError,
    canonical_value_data,
    canonical_value_from_data,
    enumerate_closed_terms,
    grammar_data,
    grammar_from_data,
    observer_program_digest,
    term_data,
    term_from_data,
    terms_digest,
)
from src.core.observer_discovery_v3.dsl.types import (
    ClosedEvaluationReceipt,
    ClosedObserverGrammar,
    ClosedObserverTerm,
    ClosedWorkerConfig,
)
from src.core.observer_discovery_v3.worker.runtime import (
    BLOCKED,
    BOUNDARY,
    READY,
    run_closed_observers_isolated,
    validate_closed_receipt,
)
from src.core.proof_core_codec import canonical_json


def grammar(ops: tuple[str, ...] = ("column", "xor")) -> ClosedObserverGrammar:
    return ClosedObserverGrammar("closed-test-v1", 2, (0, 1), ops, 2, 1, 3)


def terms() -> tuple[ClosedObserverTerm, ...]:
    return (ClosedObserverTerm("column", (0,)), ClosedObserverTerm("xor", (0, 1)))


def rows() -> tuple[tuple[int, int], ...]:
    return ((0, 0), (0, 1), (1, 0), (1, 1))


def config(**changes: int) -> ClosedWorkerConfig:
    return replace(ClosedWorkerConfig(), **changes)


def test_closed_ast_grammar_and_values_have_strict_canonical_roundtrips() -> None:
    grammar_record = grammar()
    term = terms()[1]
    assert grammar_from_data(grammar_data(grammar_record)) == grammar_record
    assert term_from_data(term_data(term)) == term
    assert canonical_value_from_data(canonical_value_data((True, 1, "x"))) == (True, 1, "x")

    extra = grammar_data(grammar_record) | {"evaluator": "forbidden"}
    with pytest.raises(ClosedDslError, match="grammar-shape"):
        grammar_from_data(extra)
    with pytest.raises(TypeError):
        ClosedObserverGrammar("bad", 2, (0, 1), ("xor",), 2, 1, 2, lambda value: value)  # type: ignore[call-arg]


def test_complete_enumerator_is_deterministic_and_cutoff_fails_closed() -> None:
    paired = grammar(("column", "pair", "xor"))
    first = enumerate_closed_terms(paired, 16)
    second = enumerate_closed_terms(paired, 16)
    assert first == second
    assert {term.op for term in first} == {"column", "xor", "pair"}
    with pytest.raises(ClosedDslError, match="catalog-cutoff"):
        enumerate_closed_terms(paired, 2)

    exponential = ClosedObserverGrammar(
        "exponential-cutoff",
        64,
        tuple(range(64)),
        ("xor",),
        64,
        0,
        64,
    )
    with pytest.raises(ClosedDslError, match="catalog-cutoff"):
        enumerate_closed_terms(exponential, 10)


def test_isolated_worker_returns_exact_deterministic_receipt() -> None:
    first = run_closed_observers_isolated(grammar(), terms(), rows(), config())
    second = run_closed_observers_isolated(grammar(), terms(), rows(), config())
    assert first == second
    assert first.status == READY
    assert first.outputs == ((0, 0, 1, 1), (0, 1, 1, 0))
    assert all(
        len(value) == 64
        for value in (
            first.request_digest,
            first.grammar_digest,
            first.terms_digest,
            first.rows_digest,
            first.output_digest,
            first.result_digest,
        )
    )
    assert validate_closed_receipt(first, expected_request_digest=first.request_digest)
    assert "not a container" in first.boundary
    assert "one-shot ledger" in first.boundary


def test_request_roots_bind_grammar_terms_rows_and_config() -> None:
    original = run_closed_observers_isolated(grammar(), terms(), rows(), config())
    changed_term = run_closed_observers_isolated(
        grammar(),
        (ClosedObserverTerm("column", (1,)),),
        rows(),
        config(),
    )
    changed_rows = run_closed_observers_isolated(
        grammar(),
        terms(),
        tuple(reversed(rows())),
        config(),
    )
    changed_config = run_closed_observers_isolated(
        grammar(),
        terms(),
        rows(),
        config(determinism_checks=3),
    )
    assert (
        len(
            {
                original.request_digest,
                changed_term.request_digest,
                changed_rows.request_digest,
                changed_config.request_digest,
            }
        )
        == 4
    )
    assert changed_term.terms_digest != original.terms_digest
    assert changed_rows.rows_digest != original.rows_digest


def test_expected_program_pin_blocks_transplanted_program_before_outputs() -> None:
    pinned_program = observer_program_digest(grammar(), terms())
    transplanted = run_closed_observers_isolated(
        grammar(),
        (ClosedObserverTerm("column", (1,)),),
        rows(),
        config(),
        expected_program_digest=pinned_program,
    )

    assert transplanted.status == BLOCKED
    assert transplanted.obstruction == "expected-program-mismatch"
    assert transplanted.outputs == ()
    assert validate_closed_receipt(transplanted)


def test_request_snapshot_survives_caller_ast_and_config_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.core.observer_discovery_v3.worker.runtime as worker

    caller_grammar = grammar()
    caller_term = ClosedObserverTerm("xor", (0, 1))
    caller_config = config()
    original_invoke = worker._invoke_worker

    def mutate_after_snapshot(request: bytes, snapshotted_config: ClosedWorkerConfig):
        object.__setattr__(caller_grammar, "input_arity", 1)
        object.__setattr__(caller_term, "indices", (1,))
        object.__setattr__(caller_config, "max_rows", 1)
        return original_invoke(request, snapshotted_config)

    monkeypatch.setattr(worker, "_invoke_worker", mutate_after_snapshot)
    receipt = run_closed_observers_isolated(
        caller_grammar,
        (caller_term,),
        rows(),
        caller_config,
    )

    assert receipt.status == READY
    assert receipt.outputs == ((0, 1, 1, 0),)
    assert validate_closed_receipt(receipt)
    assert not hasattr(ClosedWorkerConfig(), "__dict__")


def test_preflight_rejects_cycle_bad_bits_and_resource_caps() -> None:
    cyclic = ClosedObserverTerm("pair")
    object.__setattr__(cyclic, "children", (cyclic, ClosedObserverTerm("column", (0,))))
    cycle = run_closed_observers_isolated(grammar(("column", "pair")), (cyclic,), rows(), config())
    bad_bits = run_closed_observers_isolated(
        grammar(),
        (ClosedObserverTerm("xor", (0, 1)),),
        ((0, 2),),
        config(),
    )
    capped = run_closed_observers_isolated(grammar(), terms(), rows(), config(max_terms=1))
    nested_cell = run_closed_observers_isolated(
        grammar(),
        terms(),
        (((0,), 0),),
        config(),
    )
    strict = run_closed_observers_isolated(
        grammar(),
        terms(),
        rows(),
        replace(config(), isolation_profile="strict"),
    )
    assert {
        cycle.status,
        bad_bits.status,
        capped.status,
        nested_cell.status,
        strict.status,
    } == {BLOCKED}
    assert cycle.obstruction == "cyclic-term"
    assert bad_bits.obstruction.startswith("worker-blocked-non-bit-xor-input")
    assert capped.obstruction == "term-count"
    assert nested_cell.obstruction == "row-cell-type"
    assert strict.obstruction == "strict-isolation-unavailable"
    assert all(validate_closed_receipt(receipt) for receipt in (cycle, bad_bits, capped, strict))


def test_direct_decoders_digests_and_receipts_enforce_preconstruction_caps() -> None:
    grammar_record = grammar()
    grammar_payload = grammar_data(grammar_record)
    grammar_payload["bit_columns"] = list(range(65))
    with pytest.raises(ClosedDslError, match="grammar-shape"):
        grammar_from_data(grammar_payload)

    oversized_term = term_data(ClosedObserverTerm("column", (0,)))
    oversized_term["children"] = [term_data(ClosedObserverTerm("column", (0,)))] * 3
    with pytest.raises(ClosedDslError, match="term-shape"):
        term_from_data(oversized_term)

    oversized_value = {"tag": "tuple", "value": [{"tag": "int", "value": 0}] * 4097}
    with pytest.raises(ClosedDslError, match="canonical-size"):
        canonical_value_from_data(oversized_value)
    with pytest.raises(ClosedDslError, match="term-count"):
        terms_digest((ClosedObserverTerm("column", (0,)),) * 4097, grammar_record)
    with pytest.raises(ClosedDslError, match="invalid-grammar"):
        grammar_data(replace(grammar_record, grammar_id="x" * 1_000_000))
    with pytest.raises(ClosedDslError, match="invalid-grammar"):
        grammar_data(replace(grammar_record, grammar_id="\ud800"))
    with pytest.raises(ClosedDslError, match="string-size"):
        canonical_value_data("x" * 1_000_000)
    with pytest.raises(ClosedDslError, match="string-size"):
        canonical_value_data("\ud800")

    receipt = run_closed_observers_isolated(grammar_record, terms(), rows(), config())
    assert not validate_closed_receipt(replace(receipt, outputs=((),) * 4097))
    assert not validate_closed_receipt(replace(receipt, obstruction="x" * 1_000_000))
    assert not validate_closed_receipt(replace(receipt, obstruction="\ud800"))


def test_receipt_validator_caps_occurrence_expansion_of_shared_wide_values() -> None:
    wide_value = tuple(range(4095))
    hostile = ClosedEvaluationReceipt(
        READY,
        "a" * 64,
        "b" * 64,
        "c" * 64,
        "d" * 64,
        ((wide_value,) * 245,),
        "e" * 64,
        "f" * 64,
        "",
        BOUNDARY,
    )

    assert not validate_closed_receipt(hostile)
    oversized_shallow = replace(hostile, outputs=(((0,) * 100_000,),))
    assert not validate_closed_receipt(oversized_shallow)
    oversized_string = replace(hostile, outputs=(("x" * 1_000_000,),))
    assert not validate_closed_receipt(oversized_string)


def test_timeout_and_transport_errors_become_blocked_without_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.observer_discovery_v3.worker.runtime as worker

    def timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(("closed-worker",), 0.1)

    monkeypatch.setattr(worker, "_invoke_worker", timeout)
    receipt = run_closed_observers_isolated(grammar(), terms(), rows(), config())
    assert receipt.status == BLOCKED
    assert receipt.obstruction == "worker-timeout"
    assert receipt.outputs == ()
    assert validate_closed_receipt(receipt)


def test_parent_subprocess_launch_uses_no_python_preexec_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.observer_discovery_v3.worker.runtime as worker

    captured: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured.update(kwargs)
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(worker.subprocess, "run", fake_run)
    worker._invoke_worker(b"{}", config())

    assert "preexec_fn" not in captured


def test_receipt_validator_rejects_output_result_and_expected_root_transplants() -> None:
    receipt = run_closed_observers_isolated(grammar(), terms(), rows(), config())
    assert receipt.status == READY
    assert not validate_closed_receipt(replace(receipt, output_digest="0" * 64))
    assert not validate_closed_receipt(replace(receipt, result_digest="0" * 64))
    assert not validate_closed_receipt(receipt, expected_request_digest="0" * 64)
    assert not validate_closed_receipt(receipt, expected_grammar_digest="0" * 64)
    assert not validate_closed_receipt(receipt, expected_terms_digest="0" * 64)
    assert not validate_closed_receipt(receipt, expected_rows_digest="0" * 64)


def test_worker_request_is_canonical_and_logs_do_not_expose_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    marker = "PRIVATE-CLOSED-ROW-MARKER"
    marked_rows = ((marker, 0), (marker, 1))
    marked_grammar = ClosedObserverGrammar(
        "log-test",
        2,
        (1,),
        ("column",),
        1,
        0,
        1,
    )
    with caplog.at_level("DEBUG"):
        receipt = run_closed_observers_isolated(
            marked_grammar,
            (ClosedObserverTerm("column", (0,)),),
            marked_rows,
            config(),
        )
    assert receipt.status == READY
    assert marker not in caplog.text

    payload = canonical_value_data(marked_rows[0])
    assert canonical_json(payload) == json.dumps(payload, sort_keys=True, separators=(",", ":"))
