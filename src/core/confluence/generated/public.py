"""Collision-safe root aliases for released P3-C1 generated confluence."""

from __future__ import annotations

from . import core as _p3c1
from . import formal as _formal

P3C1GeneratedConfluenceError = _p3c1.GeneratedConfluenceError
P3C1CellMode = _p3c1.CellMode
P3C1GeneratedConfluenceStatus = _p3c1.GeneratedConfluenceStatus
P3C1GeneratedFailureKind = _p3c1.GeneratedFailureKind
P3C1FailedBound = _p3c1.FailedBound
P3C1ContinuationState = _p3c1.ContinuationState
P3C1ContinuationEdge = _p3c1.ContinuationEdge
P3C1StateRank = _p3c1.StateRank
P3C1RankedContinuationSystem = _p3c1.RankedContinuationSystem
P3C1GeneratedLocalPeak = _p3c1.GeneratedLocalPeak
P3C1LocalJoinCell = _p3c1.LocalJoinCell
P3C1BlockedLocalJoinCell = _p3c1.BlockedLocalJoinCell
P3C1LocalPeakRow = _p3c1.LocalPeakRow
P3C1GeneratedConfluenceTheoremSource = _p3c1.GeneratedConfluenceTheoremSource
P3C1GeneratedFormalPhaseReceipt = _p3c1.GeneratedFormalPhaseReceipt
P3C1GeneratedFiniteConfluence = _p3c1.GeneratedFiniteConfluence
P3C1GeneratedConfluenceResourceLimit = _p3c1.GeneratedConfluenceResourceLimit
P3C1CarryNormalizationProbeRow = _p3c1.CarryNormalizationProbeRow
P3C1NonterminatingCountermodel = _p3c1.NonterminatingCountermodel

P3C1_ARTIFACT_PATH = _p3c1.ARTIFACT_PATH
P3C1_ARTIFACT_SHA256 = _p3c1.ARTIFACT_SHA256
P3C1_THEOREM_IDS = _p3c1.THEOREM_IDS
P3C1_TOOLCHAIN_ID = _p3c1.TOOLCHAIN_ID
P3C1_ELAN_SHA256 = _formal.ELAN_SHA256
P3C1_LEAN_SHA256 = _formal.LEAN_SHA256
P3C1_LEAN_VERSION = _formal.LEAN_VERSION
P3C1_TCB_DIGEST = _formal.TCB_DIGEST
P3C1_NONCLAIMS = _p3c1.P3C1_NONCLAIMS
P3C1_NO_C1_C3_TRANSPORT_CLAIM = _p3c1.NO_C1_C3_TRANSPORT_CLAIM

p3c1_continuation_state = _p3c1.continuation_state
p3c1_continuation_edge = _p3c1.continuation_edge
p3c1_ranked_continuation_system = _p3c1.ranked_continuation_system
p3c1_snapshot_ranked_system = _p3c1.snapshot_ranked_system
p3c1_generated_reachable = _p3c1.generated_reachable
p3c1_generated_local_peaks = _p3c1.generated_local_peaks
p3c1_local_join_cell = _p3c1.local_join_cell
p3c1_blocked_local_join_cell = _p3c1.blocked_local_join_cell
p3c1_generated_finite_confluence = _p3c1.generated_finite_confluence
p3c1_validate_generated_confluence_result = _p3c1.validate_generated_confluence_result
p3c1_generated_confluence_theorem_source = _p3c1.generated_confluence_theorem_source
p3c1_check_generated_confluence_theorem = _p3c1.check_generated_confluence_theorem
p3c1_local_nonterminating_countermodel = _p3c1.local_nonterminating_countermodel
p3c1_carry_normalization_probe = _p3c1.carry_normalization_probe

__all__ = (
    "P3C1GeneratedConfluenceError", "P3C1CellMode", "P3C1GeneratedConfluenceStatus",
    "P3C1GeneratedFailureKind", "P3C1FailedBound", "P3C1ContinuationState",
    "P3C1ContinuationEdge", "P3C1StateRank", "P3C1RankedContinuationSystem",
    "P3C1GeneratedLocalPeak", "P3C1LocalJoinCell", "P3C1BlockedLocalJoinCell",
    "P3C1LocalPeakRow", "P3C1GeneratedConfluenceTheoremSource",
    "P3C1GeneratedFormalPhaseReceipt", "P3C1GeneratedFiniteConfluence",
    "P3C1GeneratedConfluenceResourceLimit", "P3C1CarryNormalizationProbeRow",
    "P3C1NonterminatingCountermodel", "P3C1_ARTIFACT_PATH", "P3C1_ARTIFACT_SHA256",
    "P3C1_THEOREM_IDS", "P3C1_TOOLCHAIN_ID", "P3C1_ELAN_SHA256", "P3C1_LEAN_SHA256",
    "P3C1_LEAN_VERSION", "P3C1_TCB_DIGEST", "P3C1_NONCLAIMS",
    "P3C1_NO_C1_C3_TRANSPORT_CLAIM", "p3c1_continuation_state",
    "p3c1_continuation_edge", "p3c1_ranked_continuation_system",
    "p3c1_snapshot_ranked_system", "p3c1_generated_reachable",
    "p3c1_generated_local_peaks", "p3c1_local_join_cell",
    "p3c1_blocked_local_join_cell", "p3c1_generated_finite_confluence",
    "p3c1_validate_generated_confluence_result",
    "p3c1_generated_confluence_theorem_source", "p3c1_check_generated_confluence_theorem",
    "p3c1_local_nonterminating_countermodel", "p3c1_carry_normalization_probe",
)
