from dataclasses import replace

from src.core.proof_core_resonance import (
    BOUNDARY, THEOREM_ID, intrinsic_resonance_statement,
    intrinsic_resonance_theorem, qualifies_as_intrinsic_resonance,
)
from src.core.proof_core_types import NativeLawId, RuleId
from src.core.theorem_language import (
    check_theorem_statement, default_theorem_environments, parse_theorem_statement,
)


def test_intrinsic_resonance_is_a_general_kernel_derived_theorem():
    theorem = intrinsic_resonance_theorem()
    assert theorem.theorem_id == THEOREM_ID == "THM-R7-004"
    assert theorem.statement == intrinsic_resonance_statement()
    assert theorem.rule_closure == (
        RuleId.FORALL_INTRO, RuleId.NATIVE_LAW, RuleId.RESONANCE_INTRO,
    )
    assert theorem.native_law_closure == (NativeLawId.WEAVE_UNIT_RIGHT,)
    assert theorem.artifact.context.endswith('"types":[]}')
    assert qualifies_as_intrinsic_resonance(theorem.artifact)


def test_intrinsic_boundary_does_not_promote_cyclic_phase_shadows():
    assert "cyclic phase" in BOUNDARY
    assert "weighted" in BOUNDARY
    assert "remain external shadows" in BOUNDARY


def test_finite_theorem_language_ledger_cannot_qualify_as_r7_proof():
    statement = parse_theorem_statement(
        "theorem old forall x:nod :: ready(echo($x,$x,observer:kind))"
    )
    ledger = check_theorem_statement(statement, default_theorem_environments()[:1])
    assert ledger.status == "ready"
    assert not qualifies_as_intrinsic_resonance(ledger)


def test_artifact_metadata_drift_loses_theorem_qualification():
    artifact = intrinsic_resonance_theorem().artifact
    assert not qualifies_as_intrinsic_resonance(replace(artifact, theorem_id="THM-FORGED"))
