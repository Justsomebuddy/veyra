from src.core.classical_benchmarks import classical_benchmark_cards, classical_benchmark_checklist, classical_benchmark_summary
import pytest

pytestmark = pytest.mark.requires_lean


def test_classical_benchmark_cards_are_paired_and_statused():
    cards = classical_benchmark_cards()
    assert [row.benchmark_id for row in cards] == [*(f"BM-F{idx:03d}" for idx in range(1, 8)), "BM-F009"]
    assert all(row.classical_statement and row.veyra_artifact for row in cards)
    assert all(row.status == "benchmarked" for row in cards)


def test_classical_benchmark_summary_is_honest_about_strength():
    summary = classical_benchmark_summary()
    assert summary["cards"] == 8
    assert summary["equivalent"] == 1
    assert summary["weaker"] == 4
    assert summary["clearer"] == 2
    assert summary["stronger"] == 1
    assert summary["unsupported_stronger"] == 0
    assert summary["overclaims"] == 0
    assert summary["all_status"] is True


def test_pythagorean_card_records_finite_weaker_scope():
    pyth = {row.benchmark_id: row for row in classical_benchmark_cards()}["BM-F003"]
    assert pyth.verdict == "weaker"
    assert "finite" in pyth.reason
    assert "pythagorean_card" in pyth.veyra_artifact


def test_classical_benchmark_checklist_blocks_overclaiming():
    text = "\n".join(classical_benchmark_checklist())
    assert "paired classical" in text
    assert "strict certificate" in text


def test_extended_benchmark_rows_cover_number_topology_likelihood():
    rows = {row.benchmark_id: row for row in classical_benchmark_cards()}
    assert rows["BM-F005"].topic == "euclid-product-plus-one"
    assert rows["BM-F006"].verdict == "weaker"
    assert rows["BM-F007"].verdict == "clearer"


def test_stronger_row_is_scoped_and_formally_supported():
    row = {item.benchmark_id: item for item in classical_benchmark_cards()}["BM-F009"]
    assert row.verdict == "stronger"
    assert row.verdict_dimension == "declared-observer-class-discrimination"
    assert "proper-subset marginals" in row.comparison_scope
    assert row.evidence_id == "observer_class_strength_r6"
    assert "not global" in row.boundary
