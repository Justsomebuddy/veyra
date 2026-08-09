"""Collision-safe root aliases for released prime-power P3-N2."""

from __future__ import annotations

from . import core as _p3n2
from . import p3t as _p3t
from . import pressure as _pressure
from . import sources as _sources

P3N2_FINITE_VERSION = _sources.FINITE_VERSION
P3N2_FORMAL_VERSION = _sources.FORMAL_VERSION
P3N2_ARTIFACT_PATH = _sources.ARTIFACT_PATH
P3N2_ARTIFACT_SHA256 = _sources.ARTIFACT_SHA256
P3N2_THEOREM_IDS = _sources.THEOREM_IDS
P3N2_AXIOM_ROWS = _sources.AXIOM_ROWS
P3N2_TCB_DIGEST = _sources.TCB_DIGEST
P3N2_LEDGER_DIGEST_ORACLE = _sources.LEDGER_DIGEST_ORACLE
P3N2_P3T_ADAPTER_VERSION = _p3t.P3T_ADAPTER_VERSION
P3N2_PRESSURE_VERSION = _pressure.PRESSURE_VERSION
P3N2_ATTACK_LABELS = _pressure.ATTACK_LABELS
P3N2_NONCLAIMS = _p3n2.N2_NONCLAIMS

P3N2ValidationError = _p3n2.PrimePowerReductionValidationError
P3N2RelativeStatus = _p3n2.RelativeStatus
P3N2FiniteRelation = _p3n2.FiniteRelation
P3N2SymbolicKind = _p3n2.SymbolicKind
P3N2BoundaryStatus = _p3n2.BoundaryStatus
P3N2ResultStatus = _p3n2.ResultStatus
P3N2PressureKind = _p3n2.N2PressureKind
P3N2FailedBound = _p3n2.FailedBound
P3N2FormalFailureKind = _p3n2.FormalFailureKind
P3N2DepthNode = _p3n2.DepthNode
P3N2FamilyCoordinate = _p3n2.FamilyCoordinate
P3N2FiniteFamilySource = _p3n2.FiniteFamilySource
P3N2ReductionRow = _p3n2.ReductionRow
P3N2ReductionArrowSource = _p3n2.ReductionArrowSource
P3N2FiniteReductionSource = _p3n2.FiniteReductionSource
P3N2TheoremSource = _p3n2.N2TheoremSource
P3N2Ledger = _p3n2.N2Ledger
P3N2Policy = _p3n2.N2Policy
P3N2Package = _p3n2.PrimePowerReductionPackage
P3N2FiniteArrowJudgment = _p3n2.FiniteArrowJudgment
P3N2Judgment = _p3n2.PrimePowerReductionJudgment
P3N2ResourceLimit = _p3n2.N2ResourceLimit
P3N2FormalFailure = _p3n2.N2FormalFailure
P3N2PressureCandidate = _p3n2.N2PressureCandidate
P3N2Refutation = _p3n2.N2Refutation
P3N2Open = _p3n2.N2Open
P3N2Result = _p3n2.N2Result

p3n2_exact_reduction_network_package = _p3n2.exact_reduction_network_package
p3n2_finite_reduction_source = _p3n2.finite_reduction_source
p3n2_theorem_source = _p3n2.theorem_source
p3n2_exact_n1_theorem_source = _p3n2.exact_n1_theorem_source
p3n2_ledger = _p3n2.n2_ledger
p3n2_policy = _p3n2.n2_policy
p3n2_reduction_network_package = _p3n2.reduction_network_package
p3n2_reduction_judgment = _p3n2.prime_power_reduction_judgment
p3n2_validate_reduction_result = _p3n2.validate_prime_power_reduction_result
p3n2_square_pressure_candidate = _p3n2.square_pressure_candidate
p3n2_path_pressure_candidate = _p3n2.path_pressure_candidate
p3n2_refute_pressure_candidate = _p3n2.refute_pressure_candidate
p3n2_refute_wrong_square_candidate = _p3n2.refute_wrong_square_candidate
p3n2_refute_wrong_path_candidate = _p3n2.refute_wrong_path_candidate
p3n2_report_missing_symbolic_evidence = _p3n2.report_missing_symbolic_evidence
p3n2_validate_refutation = _p3n2.validate_n2_refutation
p3n2_validate_open = _p3n2.validate_n2_open

__all__ = (
    "P3N2_FINITE_VERSION", "P3N2_FORMAL_VERSION", "P3N2_ARTIFACT_PATH",
    "P3N2_ARTIFACT_SHA256", "P3N2_THEOREM_IDS", "P3N2_AXIOM_ROWS",
    "P3N2_TCB_DIGEST", "P3N2_LEDGER_DIGEST_ORACLE", "P3N2_P3T_ADAPTER_VERSION",
    "P3N2_PRESSURE_VERSION", "P3N2_ATTACK_LABELS", "P3N2_NONCLAIMS",
    "P3N2ValidationError", "P3N2RelativeStatus", "P3N2FiniteRelation",
    "P3N2SymbolicKind", "P3N2BoundaryStatus", "P3N2ResultStatus",
    "P3N2PressureKind", "P3N2FailedBound", "P3N2FormalFailureKind",
    "P3N2DepthNode", "P3N2FamilyCoordinate", "P3N2FiniteFamilySource",
    "P3N2ReductionRow", "P3N2ReductionArrowSource", "P3N2FiniteReductionSource",
    "P3N2TheoremSource", "P3N2Ledger", "P3N2Policy", "P3N2Package",
    "P3N2FiniteArrowJudgment", "P3N2Judgment", "P3N2ResourceLimit",
    "P3N2FormalFailure", "P3N2PressureCandidate", "P3N2Refutation",
    "P3N2Open", "P3N2Result", "p3n2_exact_reduction_network_package",
    "p3n2_finite_reduction_source", "p3n2_theorem_source",
    "p3n2_exact_n1_theorem_source", "p3n2_ledger", "p3n2_policy",
    "p3n2_reduction_network_package", "p3n2_reduction_judgment",
    "p3n2_validate_reduction_result", "p3n2_square_pressure_candidate",
    "p3n2_path_pressure_candidate", "p3n2_refute_pressure_candidate",
    "p3n2_refute_wrong_square_candidate", "p3n2_refute_wrong_path_candidate",
    "p3n2_report_missing_symbolic_evidence", "p3n2_validate_refutation",
    "p3n2_validate_open",
)
