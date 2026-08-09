from src.core.formal_bridge import check_formal_proof, check_lean_echo_export, echo_reflexive_certificate, echo_reflexive_proof_steps, formal_bridge_checklist, formal_bridge_summary
import pytest

pytestmark = pytest.mark.requires_lean


def test_internal_formal_bridge_checks_echo_reflexive_theorem():
    cert = echo_reflexive_certificate()
    assert cert.theorem_id == "THM-F001"
    assert cert.status == "checked"
    assert cert.diagnostics == ()
    assert len(cert.steps) == 3


def test_formal_kernel_blocks_bad_rule_order():
    steps = echo_reflexive_proof_steps()
    status, diagnostics = check_formal_proof((steps[-1],))
    assert status == "blocked"
    assert diagnostics


def test_lean_echo_bridge_file_checks():
    result = check_lean_echo_export()
    assert result.status == "checked"
    assert result.path.endswith("proofs/lean/VeyraEcho.lean")


def test_formal_bridge_summary_and_checklist():
    summary = formal_bridge_summary()
    assert summary == {"theorem": "THM-F001", "internal": "checked", "lean": "checked", "steps": 3}
    assert formal_bridge_checklist()[-1] == "Lean command check"
