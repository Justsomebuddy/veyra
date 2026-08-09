"""Collision-safe root aliases for released PΩ2 prime-power completion."""

from __future__ import annotations

from . import core as _pomega2
from . import types as _types

POMEGA2_ARTIFACT_PATH = _pomega2.ARTIFACT_PATH
POMEGA2_ARTIFACT_SHA256 = _pomega2.ARTIFACT_SHA256
POMEGA2_AXIOM_CLOSURE = _pomega2.AXIOM_CLOSURE
POMEGA2_CANONICAL_OPS_ID = _pomega2.CANONICAL_OPS_ID
POMEGA2_CONCRETE_INSTANCE_ID = _pomega2.CONCRETE_INSTANCE_ID
POMEGA2_TCB_DIGEST = _pomega2.TCB_DIGEST
POMEGA2_THEOREM_IDS = _pomega2.THEOREM_IDS
POMEGA2_TOOLCHAIN_ID = _pomega2.TOOLCHAIN_ID
POMEGA2_NONCLAIMS = _types.POMEGA2_NONCLAIMS

Pomega2ValidationError = _pomega2.PadicCompletionValidationError
Pomega2PrimeSource = _types.PrimeSource
Pomega2TowerDoctrine = _types.PadicTowerDoctrine
Pomega2TheoremSource = _types.PadicCompletionTheoremSource
Pomega2LedgerRowClass = _types.PadicLedgerRowClass
Pomega2LedgerRow = _types.PadicCompletionLedgerRow
Pomega2Ledger = _types.PadicCompletionLedger
Pomega2Policy = _types.PadicCompletionPolicy
Pomega2Package = _types.PadicCompletionPackage
Pomega2ObligationStatus = _types.PadicObligationStatus
Pomega2Obligations = _types.PadicCompletionObligations
Pomega2CompletedCarrierStatus = _types.PadicCompletedCarrierStatus
Pomega2NotEstablishedStatus = _types.PadicNotEstablishedStatus
Pomega2NotClaimedStatus = _types.PadicNotClaimedStatus
Pomega2Judgment = _types.PadicCompletionJudgment
Pomega2ResourceLimit = _types.PadicCompletionResourceLimit
Pomega2FormalExecutionFailure = _types.PadicFormalExecutionFailure
Pomega2ExecutionFailureKind = _types.PadicExecutionFailureKind
Pomega2Result = _types.PadicCompletionResult
Pomega2BoundedShadow = _types.BoundedPadicShadow

pomega2_prime_source = _pomega2.prime_source
pomega2_tower_doctrine = _pomega2.padic_tower_doctrine
pomega2_theorem_source = _pomega2.padic_completion_theorem_source
pomega2_ledger = _pomega2.padic_completion_ledger
pomega2_policy = _pomega2.padic_completion_policy
pomega2_package = _pomega2.padic_completion_package
pomega2_judgment = _pomega2.padic_completion_judgment
pomega2_validate_result = _pomega2.validate_padic_completion_result
pomega2_bounded_shadow = _pomega2.bounded_padic_shadow

__all__ = (
    "POMEGA2_ARTIFACT_PATH", "POMEGA2_ARTIFACT_SHA256", "POMEGA2_AXIOM_CLOSURE",
    "POMEGA2_CANONICAL_OPS_ID", "POMEGA2_CONCRETE_INSTANCE_ID", "POMEGA2_TCB_DIGEST",
    "POMEGA2_THEOREM_IDS", "POMEGA2_TOOLCHAIN_ID", "POMEGA2_NONCLAIMS",
    "Pomega2ValidationError", "Pomega2PrimeSource", "Pomega2TowerDoctrine",
    "Pomega2TheoremSource", "Pomega2LedgerRowClass", "Pomega2LedgerRow",
    "Pomega2Ledger", "Pomega2Policy", "Pomega2Package", "Pomega2ObligationStatus",
    "Pomega2Obligations", "Pomega2CompletedCarrierStatus",
    "Pomega2NotEstablishedStatus", "Pomega2NotClaimedStatus", "Pomega2Judgment",
    "Pomega2ResourceLimit", "Pomega2FormalExecutionFailure",
    "Pomega2ExecutionFailureKind", "Pomega2Result", "Pomega2BoundedShadow",
    "pomega2_prime_source", "pomega2_tower_doctrine", "pomega2_theorem_source",
    "pomega2_ledger", "pomega2_policy", "pomega2_package", "pomega2_judgment",
    "pomega2_validate_result", "pomega2_bounded_shadow",
)
