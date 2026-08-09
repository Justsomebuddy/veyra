from src.core.axiom_kernel import axiom_kernel_checklist, axiom_kernel_report, axiom_witness_rows, layer_axiom_dependencies, unified_axiom_kernel
import pytest

pytestmark = pytest.mark.requires_lean


def test_unified_axiom_kernel_has_executable_witnesses():
    axioms = unified_axiom_kernel()
    witnesses = axiom_witness_rows(axioms)
    assert len(axioms) == 8
    assert [row.axiom_id for row in witnesses] == [row.axiom_id for row in axioms]
    assert all(row.executable for row in witnesses)
    assert witnesses[-1].status == "blocked"
    assert "echo mismatch" in witnesses[-1].obstruction


def test_every_core_layer_is_classified_and_only_receipts_name_axioms():
    rows = layer_axiom_dependencies()
    assert len(rows) == 36
    assert {row.derivation for row in rows} == {"theorem-derived", "receipt-derived-witness", "shadow", "meta"}
    assert all(row.axioms for row in rows if row.derivation == "receipt-derived-witness")
    assert all(not row.axioms for row in rows if row.derivation != "receipt-derived-witness")
    assert any(row.layer == "topology-echo" and row.derivation == "shadow" for row in rows)


def test_axiom_kernel_report_is_ready_and_marks_receipt_boundaries():
    report = axiom_kernel_report()
    assert report.ready
    assert report.summary()["axioms"] == 8
    assert report.summary()["layers"] == 36
    assert report.summary()["theorem_derived"] == 2
    assert report.summary()["receipt_derived_witness"] == 4
    assert report.summary()["shadow"] == 25
    assert report.summary()["meta"] == 5
    assert axiom_kernel_checklist()[-1] == "theorem-derived and meta layers claim no primitive witness axioms"
