from src.core.certify_veyra_magic import certify_veyra_magic_m1
from src.core.veyra_magic import VEYRA_MAGIC_THESIS, magic_audit_checklist, magic_audit_rows, magic_audit_summary
import pytest

pytestmark = pytest.mark.requires_lean


def test_magic_thesis_names_observer_synthesis_not_speedup():
    assert VEYRA_MAGIC_THESIS.startswith("observer synthesis")
    assert "speedup" not in VEYRA_MAGIC_THESIS


def test_magic_audit_rows_are_bounded_and_non_overclaiming():
    rows = magic_audit_rows()
    assert len(rows) == 5
    assert rows[0].row_id == "M1-OBSERVER-SYNTHESIS"
    assert rows[0].verdict == "strongest-current-magic-candidate"
    assert "observer_synthesis_r5" in rows[0].evidence
    assert "observer_class_strength_r6" in rows[0].evidence
    assert all("not a superiority claim" in row.boundary for row in rows)
    assert any(row.verdict == "blocked-claim" for row in rows)


def test_magic_audit_summary_and_certificate_are_stable():
    assert magic_audit_summary() == {
        "rows": 5,
        "strongest_candidates": 1,
        "active_candidates": 2,
        "truth_maintenance": 1,
        "blocked_claims": 1,
        "overclaims": 0,
    }
    assert "observer switch" in "\n".join(magic_audit_checklist())
    cert = certify_veyra_magic_m1()
    assert cert.passed is True
    assert "observer-synthesis" in cert.method
