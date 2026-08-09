"""Certificate gate for the proof-carrying R7 recurrence theorem."""
from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..kernel.layer_derivations import layer_derivations
from ..proof_core_bridge import proof_core_bridge_report
from ..proof_core_resonance import intrinsic_resonance_statement, intrinsic_resonance_theorem
from ..proof_core_types import NativeLawId, RuleId

logger = logging.getLogger(__name__)


def certify_proof_carrying_core_r7() -> Certificate:
    """Gate exact kernel replay, source binding, Lean soundness, and promotion."""
    logger.debug("certify_proof_carrying_core_r7 entry")
    theorem = intrinsic_resonance_theorem()
    bridge = proof_core_bridge_report()
    layer = next(row for row in layer_derivations() if row.layer == "intrinsic-resonance")
    expected_rules = (
        RuleId.FORALL_INTRO,
        RuleId.NATIVE_LAW,
        RuleId.RESONANCE_INTRO,
    )
    passed = (
        theorem.status == "kernel-checked"
        and theorem.statement == intrinsic_resonance_statement()
        and theorem.rule_closure == expected_rules
        and theorem.native_law_closure == (NativeLawId.WEAVE_UNIT_RIGHT,)
        and bridge.status == "checked"
        and bridge.artifact_checked
        and bridge.source_bound
        and bridge.manifest_checked
        and bridge.lean_checked
        and bridge.artifact_digest == theorem.artifact.proof_digest
        and bridge.theorem_ids == tuple(f"THM-R7-{index:03d}" for index in range(1, 5))
        and layer.classification == "theorem-derived"
        and layer.theorem_id == theorem.theorem_id
        and layer.proof_digest == theorem.artifact.proof_digest
        and layer.axioms == ()
        and "cyclic/phase" in bridge.boundary
    )
    detail = (
        f"theorem={theorem.theorem_id} artifact={theorem.artifact.proof_digest[:16]} "
        f"binding={bridge.binding_digest[:16]} lean={bridge.status}"
    )
    result = Certificate(
        "proof_carrying_core_r7",
        "kernel-replayed proof artifact bound byte-for-byte to Lean checker soundness",
        passed,
        detail,
        2,
    )
    if not passed:
        logger.error("certify_proof_carrying_core_r7 blocked detail=%s bridge=%r layer=%r", detail, bridge, layer)
    logger.debug("certify_proof_carrying_core_r7 exit result=%r", result)
    return result
