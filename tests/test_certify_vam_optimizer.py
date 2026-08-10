from pathlib import Path

from scripts.project_hygiene import line_limit
from src.core.certify_vam_optimizer import EXPECTED_LOCAL_LAWS, certify_vam_optimizer_gate
from vam.src.optimizer_proof_catalog import (
    CHECKED_LOCAL_LAWS,
    REQUIRED_LEAN_SYMBOLS,
    checked_law_for_pass,
    law_id_for_pass,
    missing_required_lean_symbols,
)

ROOT = Path(__file__).resolve().parents[1]


def _loc(path: str) -> int:
    return len(Path(path).read_text(encoding="utf-8").splitlines())


def test_certify_vam_optimizer_gate_summarizes_current_seven_laws():
    gate = certify_vam_optimizer_gate(ROOT)

    assert gate.proof_bridge_ok
    assert gate.prepost_ok
    assert gate.lean_status == "checked"
    assert gate.proof_docs_ok
    assert gate.prepost_docs_ok
    assert gate.checked_local_laws == EXPECTED_LOCAL_LAWS
    assert gate.prepost_accepted_rows == 5
    assert gate.prepost_safe_equivalence_rows == 7
    assert "optimizer_proof_bridge=True/checked" in gate.detail
    assert "optimizer_prepost=True/5/7" in gate.detail


def test_optimizer_proof_catalog_binds_all_expected_symbols():
    lean_text = (ROOT / "proofs/lean/VeyraOptimizer.lean").read_text(encoding="utf-8")

    assert len(CHECKED_LOCAL_LAWS) == 7
    assert law_id_for_pass("dead-shadow") == "dead-shadow.unused-lookup-local-law"
    assert checked_law_for_pass("compress-alias")[3] == "Veyra.compressAlias_samePair_local_law"
    assert "Veyra.compressIdempotent_differentObserver_reject_local_law" in REQUIRED_LEAN_SYMBOLS
    assert "Veyra.compressIdempotent_obstructionBoundary_reject_local_law" in REQUIRED_LEAN_SYMBOLS
    assert "Veyra.compressIdempotent_visibleUseObserver_local_law" in REQUIRED_LEAN_SYMBOLS
    assert REQUIRED_LEAN_SYMBOLS[-1] == "Veyra.deadShadow_unusedLookup_local_law"
    assert missing_required_lean_symbols(lean_text) == ()


def test_vam_cert_and_optimizer_proof_modules_stay_within_project_target():
    paths = (
        "src/core/certify_vam.py",
        "src/core/certify_vam_optimizer.py",
        "vam/src/optimizer_proofs.py",
        "vam/src/optimizer_proof_catalog.py",
    )

    counts = {path: _loc(path) for path in paths}

    assert all(count <= line_limit(Path(path)) for path, count in counts.items()), counts
