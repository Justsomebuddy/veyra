from dataclasses import asdict

from vam.src.optimizer_obligations import optimizer_obligation_rows
from vam.src.optimizer_proofs import (
    BOUNDARY,
    CLAIM,
    OVERCLAIM_TERMS,
    assert_no_optimizer_proof_overclaim_terms,
    check_lean_optimizer_export,
    lean_optimizer_export_path,
    optimizer_proof_payload,
    optimizer_proof_rows,
    optimizer_proof_rows_from_obligations,
    optimizer_proof_summary,
)
import pytest

pytestmark = pytest.mark.requires_lean


EXPECTED_PASSES = (
    "observer-alias",
    "compress-alias",
    "compress-idempotent",
    "dead-shadow",
)
EXPECTED_PASS_ROWS = (
    "observer-alias",
    "compress-alias",
    "compress-idempotent",
    "compress-idempotent",
    "compress-idempotent",
    "compress-idempotent",
    "dead-shadow",
)
EXPECTED_LOCAL_LAWS = (
    "observer-alias.lookup-invariant",
    "compress-alias.same-pair-local-law",
    "compress-idempotent.same-observer-local-law",
    "compress-idempotent.visible-use-observer-local-law",
    "compress-idempotent.different-observer-reject-local-law",
    "compress-idempotent.obstruction-boundary-reject-local-law",
    "dead-shadow.unused-lookup-local-law",
)


def test_optimizer_proof_rows_are_deterministic_and_cover_current_obligations():
    obligations = optimizer_obligation_rows()
    first = optimizer_proof_rows("checked")
    second = optimizer_proof_rows_from_obligations(obligations, "checked")

    assert first == second
    obligation_by_pass = {row.pass_name: row for row in obligations}
    assert [row.pass_name for row in first] == list(EXPECTED_PASS_ROWS)
    assert [row.obligation_id for row in first] == [obligation_by_pass[row.pass_name].obligation_id for row in first]
    assert [row.local_law for row in first] == list(EXPECTED_LOCAL_LAWS)
    assert all(row.boundary == BOUNDARY for row in first)
    assert all(row.claim == CLAIM for row in first)
    assert optimizer_proof_payload("checked")[0]["pass_name"] == "observer-alias"
    assert_no_optimizer_proof_overclaim_terms(first)


def test_optimizer_proof_bridge_marks_seven_local_laws_as_checked_not_passes():
    rows = optimizer_proof_rows("checked")
    checked = [row for row in rows if row.formal_status == "lean-checked-local-law"]
    pending = [row for row in rows if row.formal_status == "obligation-only"]

    assert [row.pass_name for row in checked] == list(EXPECTED_PASS_ROWS)
    assert [row.local_law for row in checked] == list(EXPECTED_LOCAL_LAWS)
    assert [row.lean_symbol for row in checked] == [
        "Veyra.observerAlias_lookup_invariant",
        "Veyra.compressAlias_samePair_local_law",
        "Veyra.compressIdempotent_sameObserver_local_law",
        "Veyra.compressIdempotent_visibleUseObserver_local_law",
        "Veyra.compressIdempotent_differentObserver_reject_local_law",
        "Veyra.compressIdempotent_obstructionBoundary_reject_local_law",
        "Veyra.deadShadow_unusedLookup_local_law",
    ]
    assert all(row.proof_artifact == "proofs/lean/VeyraOptimizer.lean" for row in checked)
    assert "local lookup law only" in checked[0].evidence_scope
    assert "same source/observer alias law only" in checked[1].evidence_scope
    assert "same-observer compress idempotence law only" in checked[2].evidence_scope
    assert "visible-use observer preservation law only" in checked[3].evidence_scope
    assert "different-observer rejection law only" in checked[4].evidence_scope
    assert "obstruction-boundary rejection law only" in checked[5].evidence_scope
    assert "unused-shadow lookup/drop law only" in checked[6].evidence_scope
    assert all("pass remains obligation-backed" in row.evidence_scope for row in checked)
    assert pending == []


def test_optimizer_proof_summary_does_not_overclaim_other_current_passes():
    summary = optimizer_proof_summary(lean_status="checked")
    rows = optimizer_proof_rows("checked")
    text = "\n".join([str(asdict(summary))] + [str(asdict(row)) for row in rows]).lower()

    assert summary.total_rows == 7
    assert summary.lean_checked_local_laws == 7
    assert summary.obligation_only_rows == 0
    assert summary.checked_local_laws == EXPECTED_LOCAL_LAWS
    assert summary.obligation_backed_passes == EXPECTED_PASSES
    for term in OVERCLAIM_TERMS:
        assert term not in text
    assert_no_optimizer_proof_overclaim_terms((summary, *rows))


def test_optimizer_lean_bridge_path_and_required_symbol_binding():
    path = lean_optimizer_export_path()
    result = check_lean_optimizer_export(path)

    assert path.as_posix().endswith("proofs/lean/VeyraOptimizer.lean")
    assert result.path.endswith("proofs/lean/VeyraOptimizer.lean")
    assert result.status == "checked", result.stderr or result.stdout
