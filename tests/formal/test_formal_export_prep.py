from src.core.formal_export_prep import checked_bridge_rows, formal_export_prep_checklist, formal_export_prep_rows, formal_export_prep_summary, stable_card_export_prep_rows
import pytest

pytestmark = pytest.mark.requires_lean


def test_checked_bridge_rows_remain_separate_from_candidates():
    rows = checked_bridge_rows()
    assert [row.theorem_id for row in rows] == ["THM-F001", "THM-F002"]
    assert all(row.export_status == "checked" for row in rows)
    assert all(row.formalized for row in rows)
    assert all("tiny bridge" in row.boundary for row in rows)


def test_stable_card_export_prep_selects_only_stable_cards():
    rows = stable_card_export_prep_rows()
    assert len(rows) == 19
    assert rows[0].theorem_id == "pythagorean-separation"
    assert {row.source_status for row in rows} == {"stable-card-only"}
    assert {row.export_status for row in rows} == {"prep-ready"}
    assert not any(row.formalized for row in rows)
    assert all("no formal proof" in row.boundary for row in rows)


def test_formal_export_summary_blocks_completed_claims():
    summary = formal_export_prep_summary()
    assert summary == {
        "checked_bridges": 2,
        "candidate_rows": 19,
        "prep_ready": 19,
        "candidate_formalized": 0,
        "stable_sources": 19,
        "no_completed_claims": True,
    }
    assert len(formal_export_prep_rows()) == 21
    assert "not completed" in formal_export_prep_checklist()[2]
