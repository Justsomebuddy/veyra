"""Tests for the R15 benchmark evidence ledger."""
from dataclasses import replace

from src.core.benchmark_evidence import (
    BenchmarkEvidenceObstructionRow,
    BenchmarkEvidenceRow,
    CARRIER_STRENGTHS,
    PROOF_LENGTH_CLASSES,
    RUNTIME_CLASSES,
    SEARCH_CLASSES,
    TCB_CLASSES,
    benchmark_evidence_checklist,
    benchmark_evidence_rows,
    benchmark_evidence_specs,
    benchmark_evidence_summary,
    evidence_row_problems,
    scoped_stronger_restatement,
    validate_benchmark_evidence,
)
from src.core.classical_benchmarks import ClassicalBenchmarkCard, classical_benchmark_cards


def _ready_rows(rows=None):
    items = benchmark_evidence_rows() if rows is None else rows
    return tuple(row for row in items if isinstance(row, BenchmarkEvidenceRow))


def _fake_card(benchmark_id="BM-X001"):
    return ClassicalBenchmarkCard(
        benchmark_id, "fake-topic", "fake classical statement", "fake classical method",
        "fake veyra statement", "fake artifact", "equivalent", "fake reason", "benchmarked",
    )


def test_every_registered_benchmark_row_has_complete_evidence():
    cards = classical_benchmark_cards()
    rows = benchmark_evidence_rows()
    assert len(rows) == len(cards) == 8
    assert [row.benchmark_id for row in rows] == [card.benchmark_id for card in cards]
    assert all(isinstance(row, BenchmarkEvidenceRow) for row in rows)
    assert validate_benchmark_evidence() == ()
    assert {spec.benchmark_id for spec in benchmark_evidence_specs()} == {card.benchmark_id for card in cards}


def test_evidence_fields_use_declared_vocabularies():
    for row in _ready_rows():
        assert row.status == "ready"
        assert row.claim_tag == "ledger"
        assert row.carrier_strength in CARRIER_STRENGTHS
        assert row.proof_length_class in PROOF_LENGTH_CLASSES
        assert row.assumptions
        assert any(token in row.observer_loss for token in ("discard", "lose", "blind"))
        parts = dict(part.split(":", 1) for part in row.cost_class.split(";"))
        assert parts["tcb"] in TCB_CLASSES
        assert parts["search"] in SEARCH_CLASSES
        assert parts["runtime"] in RUNTIME_CLASSES
        assert evidence_row_problems(row) == ()


def test_scoped_stronger_is_observer_class_scoped_only():
    stronger = [row for row in _ready_rows() if row.verdict == "stronger"]
    assert [row.benchmark_id for row in stronger] == ["BM-F009"]
    note = stronger[0].scope_note
    assert note == scoped_stronger_restatement("BM-F009")
    assert "observer-class-scoped" in note
    assert "proper-subset marginals" in note
    assert "global parity" in note
    assert "proper-marginal-vs-parity observer-class" in note
    assert "never a claim of superiority over classical mathematics" in note
    assert note.count("superiority over classical mathematics") == 1


def test_summary_exact_counts():
    assert benchmark_evidence_summary() == {
        "benchmarks": 8,
        "evidence_rows": 8,
        "obstructions": 0,
        "complete": True,
        "stronger_rows": 1,
        "scoped_stronger": 1,
        "global_superiority_claims": 0,
        "carrier_finite_shadow": 4,
        "carrier_witness": 2,
        "carrier_theorem_derived": 2,
    }


def test_missing_evidence_spec_yields_explicit_obstruction():
    cards = classical_benchmark_cards() + (_fake_card(),)
    rows = benchmark_evidence_rows(cards)
    obstruction = rows[-1]
    assert isinstance(obstruction, BenchmarkEvidenceObstructionRow)
    assert obstruction.benchmark_id == "BM-X001"
    assert obstruction.reason == "missing-evidence-spec"
    assert obstruction.missing_fields == ("evidence_spec",)
    assert obstruction.status == "blocked"
    assert obstruction.claim_tag == "ledger"
    problems = validate_benchmark_evidence(rows)
    assert [row.benchmark_id for row in problems] == ["BM-X001"]


def test_invalid_evidence_fields_are_named_not_raised():
    row = next(row for row in _ready_rows() if row.benchmark_id == "BM-F002")
    broken = replace(row, assumptions="", carrier_strength="absolute", cost_class="tcb:unknown")
    assert evidence_row_problems(broken) == ("assumptions", "carrier_strength", "cost_class")
    problems = validate_benchmark_evidence((broken,))
    assert problems[0].reason == "invalid-evidence"
    assert problems[0].missing_fields == ("assumptions", "carrier_strength", "cost_class")


def test_unscoped_stronger_is_obstruction_not_superiority_claim():
    row = next(row for row in _ready_rows() if row.benchmark_id == "BM-F009")
    tampered = replace(row, scope_note="Veyra is superior to classical mathematics")
    assert evidence_row_problems(tampered) == ("scope_note",)
    problems = validate_benchmark_evidence((tampered,))
    assert problems[0].missing_fields == ("scope_note",)
    summary = benchmark_evidence_summary((tampered,))
    assert summary["scoped_stronger"] == 0
    assert summary["global_superiority_claims"] == 1


def test_orphan_evidence_spec_yields_obstruction():
    rows = benchmark_evidence_rows(classical_benchmark_cards()[:7])
    obstruction = rows[-1]
    assert isinstance(obstruction, BenchmarkEvidenceObstructionRow)
    assert obstruction.benchmark_id == "orphan:BM-F009"
    assert obstruction.reason == "unregistered-evidence-spec"
    assert obstruction.missing_fields == ("benchmark_registry",)
    assert obstruction.status == "blocked"


def test_obstruction_rows_are_well_formed():
    scenarios = (
        benchmark_evidence_rows(classical_benchmark_cards() + (_fake_card(),))[-1],
        benchmark_evidence_rows(classical_benchmark_cards()[:7])[-1],
    )
    for row in scenarios:
        assert isinstance(row, BenchmarkEvidenceObstructionRow)
        assert row.benchmark_id
        assert row.reason
        assert row.status == "blocked"
        assert row.claim_tag == "ledger"
        assert isinstance(row.missing_fields, tuple)
        assert all(row.missing_fields)


def test_ledger_is_deterministic():
    assert benchmark_evidence_rows() == benchmark_evidence_rows()
    assert benchmark_evidence_summary() == benchmark_evidence_summary()
    assert scoped_stronger_restatement() == scoped_stronger_restatement()


def test_checklist_names_required_evidence_fields():
    checklist = benchmark_evidence_checklist()
    assert "explicit assumptions" in checklist
    assert "tcb/search/runtime cost class" in checklist
    assert "observer information-loss note" in checklist
    assert "observer-class-scoped stronger restatement" in checklist
    assert "no global superiority claim" in checklist
