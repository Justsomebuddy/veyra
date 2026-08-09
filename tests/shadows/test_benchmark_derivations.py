from src.core.benchmark_derivations import benchmark_derivation_checklist, benchmark_derivation_rows, benchmark_derivation_summary, derive_benchmark_verdict
from src.core.classical_benchmarks import classical_benchmark_cards
import pytest

pytestmark = pytest.mark.requires_lean


def test_benchmark_derivation_rows_follow_named_rules():
    rows = benchmark_derivation_rows()
    assert [row.benchmark_id for row in rows] == [
        "BM-F001", "BM-F002", "BM-F003", "BM-F004",
        "BM-F005", "BM-F006", "BM-F007", "BM-F009",
    ]
    assert all(row.status == "derived" for row in rows)
    assert rows[0].rule == "same-tiny-reflexivity-scope"
    assert rows[3].rule == "explicit-obstruction-row"
    assert rows[-1].rule == "strict-observer-class-separation"


def test_benchmark_derivation_summary_has_one_supported_scoped_claim():
    summary = benchmark_derivation_summary()
    assert summary == {"rows": 8, "derived": 8, "blocked": 0, "stronger": 1, "unsupported_stronger": 0, "scoped_claims": True}


def test_derive_benchmark_verdict_has_boundary():
    card = classical_benchmark_cards()[2]
    row = derive_benchmark_verdict(card)
    assert row.verdict == "weaker"
    assert "does not derive" in row.boundary


def test_benchmark_derivation_checklist_names_rules():
    assert benchmark_derivation_checklist()[0] == "named verdict rule"
