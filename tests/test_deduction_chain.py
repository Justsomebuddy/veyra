from src.core.deduction_chain import deduction_chain_checklist, deduction_chain_summary, deduction_links, deduction_proof_rows


def test_deduction_links_include_derived_boundaries():
    links = deduction_links()
    assert [row.link_id for row in links] == ["DC-001", "DC-002", "DC-003", "DC-004", "DC-005"]
    assert any(row.status == "derived" and "THM-F001" in row.anchors for row in links)
    assert any(row.status == "derived" and "THM-R3-001" in row.anchors for row in links)
    assert any(row.status == "derived" and row.target == "classical-benchmark" for row in links)
    assert any(row.status == "derived" and "THM-G001" in row.anchors for row in links)


def test_deduction_chain_summary_derives_boundaries():
    summary = deduction_chain_summary()
    assert summary["links"] == 5
    assert summary["verified"] == 5
    assert summary["derived"] == 5
    assert summary["observer-derived"] == 0
    assert summary["shadow-dependent"] == 0
    assert summary["blocked"] == 0
    assert summary["all_derived"] is True


def test_deduction_chain_checklist_names_no_overclaim():
    assert deduction_chain_checklist()[-1] == "all-derived means boundary-derived, not capability claim"


def test_deduction_proof_rows_execute_each_boundary():
    rows = deduction_proof_rows()
    assert len(rows) == 5
    assert all(row.verified for row in rows)
    native_number = next(row for row in rows if row.link_id == "DC-003")
    assert "intrinsic=witnessed" in native_number.evidence
    assert "lean=checked" in native_number.evidence
    assert native_number.status == "derived"
    benchmark = next(row for row in rows if row.link_id == "DC-004")
    assert "verdicts=8/8" in benchmark.evidence
    assert "scoped=True" in benchmark.evidence
    assert benchmark.status == "derived"
    native_geometry = next(row for row in rows if row.link_id == "DC-005")
    assert "native_geometry=3/3" in native_geometry.evidence
    assert native_geometry.status == "derived"
