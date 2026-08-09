"""Collision-safe root aliases for released P3-N1 direct family introduction."""

from __future__ import annotations

from . import core as _p3n1
from . import types as _types

P3N1_ARTIFACT_PATH = _p3n1.ARTIFACT_PATH
P3N1_ARTIFACT_SHA256 = _p3n1.ARTIFACT_SHA256
P3N1_AXIOM_CLOSURE = _p3n1.AXIOM_CLOSURE
P3N1_COORDINATE_DEFINITION_ID = _p3n1.COORDINATE_DEFINITION_ID
P3N1_FAMILY_DEFINITION_ID = _p3n1.FAMILY_DEFINITION_ID
P3N1_MAX_INTEGER_BITS = _p3n1.MAX_INTEGER_BITS
P3N1_TCB_DIGEST = _p3n1.TCB_DIGEST
P3N1_THEOREM_IDS = _p3n1.THEOREM_IDS
P3N1_TOOLCHAIN_ID = _p3n1.TOOLCHAIN_ID
P3N1_NONCLAIMS = _types.N1_NONCLAIMS

P3N1ValidationError = _p3n1.PadicFamilyIntroductionValidationError
P3N1EvidenceStatus = _types.N1EvidenceStatus
P3N1EvidenceProvenance = _types.N1EvidenceProvenance
P3N1JudgmentKind = _types.N1JudgmentKind
P3N1ResultStatus = _types.N1ResultStatus
P3N1FailedBound = _types.N1FailedBound
P3N1ExecutionFailureKind = _types.N1ExecutionFailureKind
P3N1IntegerSource = _types.IntegerSource
P3N1TheoremSource = _types.N1TheoremSource
P3N1AssumptionLedger = _types.N1AssumptionLedger
P3N1Policy = _types.N1Policy
P3N1IntroductionPackage = _types.N1IntroductionPackage
P3N1FamilyJudgment = _types.N1FamilyJudgment
P3N1ResourceLimit = _types.N1ResourceLimit
P3N1FormalFailure = _types.N1FormalFailure
P3N1Result = _types.N1Result

p3n1_integer_source = _p3n1.integer_source
p3n1_theorem_source = _p3n1.n1_theorem_source
p3n1_assumption_ledger = _p3n1.n1_assumption_ledger
p3n1_policy = _p3n1.n1_policy
p3n1_introduction_package = _p3n1.n1_introduction_package
p3n1_introduce_integer_residue_family = _p3n1.introduce_integer_residue_family
p3n1_validate_result = _p3n1.validate_n1_result

__all__ = (
    "P3N1_ARTIFACT_PATH", "P3N1_ARTIFACT_SHA256", "P3N1_AXIOM_CLOSURE",
    "P3N1_COORDINATE_DEFINITION_ID", "P3N1_FAMILY_DEFINITION_ID",
    "P3N1_MAX_INTEGER_BITS", "P3N1_TCB_DIGEST", "P3N1_THEOREM_IDS",
    "P3N1_TOOLCHAIN_ID", "P3N1_NONCLAIMS", "P3N1ValidationError",
    "P3N1EvidenceStatus", "P3N1EvidenceProvenance", "P3N1JudgmentKind",
    "P3N1ResultStatus", "P3N1FailedBound", "P3N1ExecutionFailureKind",
    "P3N1IntegerSource", "P3N1TheoremSource", "P3N1AssumptionLedger",
    "P3N1Policy", "P3N1IntroductionPackage", "P3N1FamilyJudgment",
    "P3N1ResourceLimit", "P3N1FormalFailure", "P3N1Result",
    "p3n1_integer_source", "p3n1_theorem_source", "p3n1_assumption_ledger",
    "p3n1_policy", "p3n1_introduction_package",
    "p3n1_introduce_integer_residue_family", "p3n1_validate_result",
)
