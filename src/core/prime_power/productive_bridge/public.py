"""Collision-safe root aliases for released P3-A1b productive bridge."""

from __future__ import annotations

from . import core as _p3a1b
from . import pressure as _pressure
from . import sources as _sources

P3A1B_PROGRAM_VERSION = _sources.PROGRAM_VERSION
P3A1B_PROGRAM_CONSTRUCTOR = _sources.PROGRAM_CONSTRUCTOR
P3A1B_PROGRAM_GRAMMAR_ID = _sources.PROGRAM_GRAMMAR_ID
P3A1B_FORMAL_VERSION = _sources.FORMAL_VERSION
P3A1B_ARTIFACT_PATH = _sources.ARTIFACT_PATH
P3A1B_ARTIFACT_SHA256 = _sources.ARTIFACT_SHA256
P3A1B_THEOREM_IDS = _sources.THEOREM_IDS
P3A1B_AXIOM_ROWS = _sources.AXIOM_ROWS
P3A1B_TCB_DIGEST = _sources.TCB_DIGEST
P3A1B_LEDGER_DIGEST_ORACLE = _sources.LEDGER_DIGEST_ORACLE
P3A1B_PRESSURE_VERSION = _pressure.PRESSURE_VERSION
P3A1B_PRESSURE_CONSTRUCTOR = _pressure.PRESSURE_CONSTRUCTOR
P3A1B_PRESSURE_GRAMMAR_ID = _pressure.PRESSURE_GRAMMAR_ID
P3A1B_PRESSURE_ARTIFACT_PATH = _pressure.PRESSURE_ARTIFACT_PATH
P3A1B_PRESSURE_ARTIFACT_SHA256 = _pressure.PRESSURE_ARTIFACT_SHA256
P3A1B_PRESSURE_THEOREM_IDS = _pressure.PRESSURE_THEOREM_IDS
P3A1B_PRESSURE_AXIOM_ROWS = _pressure.PRESSURE_AXIOM_ROWS
P3A1B_NONCLAIMS = _p3a1b.A1B_NONCLAIMS

P3A1BValidationError = _p3a1b.ProductiveBridgeValidationError
P3A1BBoundaryStatus = _p3a1b.BoundaryStatus
P3A1BBridgeEvidenceKind = _p3a1b.BridgeEvidenceKind
P3A1BBridgeFormalFailure = _p3a1b.BridgeFormalFailure
P3A1BBridgeLedger = _p3a1b.BridgeLedger
P3A1BBridgeOpen = _p3a1b.BridgeOpen
P3A1BBridgePolicy = _p3a1b.BridgePolicy
P3A1BBridgeProvenance = _p3a1b.BridgeProvenance
P3A1BBridgeRefutation = _p3a1b.BridgeRefutation
P3A1BBridgeResourceLimit = _p3a1b.BridgeResourceLimit
P3A1BBridgeResult = _p3a1b.BridgeResult
P3A1BBridgeStatus = _p3a1b.BridgeStatus
P3A1BBridgeTheoremSource = _p3a1b.BridgeTheoremSource
P3A1BFailedBound = _p3a1b.FailedBound
P3A1BFamilyKind = _p3a1b.FamilyKind
P3A1BFormalFailureKind = _p3a1b.FormalFailureKind
P3A1BOffsetResidueProgramSource = _p3a1b.OffsetResidueProgramSource
P3A1BProductiveBridgeJudgment = _p3a1b.ProductiveBridgeJudgment
P3A1BProductiveBridgePackage = _p3a1b.ProductiveBridgePackage
P3A1BProjectionArtifact = _p3a1b.ProjectionArtifact
P3A1BResidueProgramSource = _p3a1b.ResidueProgramSource
P3A1BResultStatus = _p3a1b.ResultStatus
P3A1BUniformizationRoute = _p3a1b.UniformizationRoute

p3a1b_bridge_ledger = _p3a1b.bridge_ledger
p3a1b_bridge_policy = _p3a1b.bridge_policy
p3a1b_productive_bridge_package = _p3a1b.productive_bridge_package
p3a1b_offset_residue_program_source = _p3a1b.offset_residue_program_source
p3a1b_validate_productive_bridge_result = _p3a1b.validate_productive_bridge_result
p3a1b_validate_projection_result = _p3a1b.validate_projection_result
p3a1b_validate_offset_refutation_result = _p3a1b.validate_offset_refutation_result
p3a1b_validate_open_result = _p3a1b.validate_open_result
p3a1b_establish_productive_family_bridge = _p3a1b.establish_productive_family_bridge
p3a1b_project_residue = _p3a1b.project_residue
p3a1b_refute_offset_program = _p3a1b.refute_offset_program
p3a1b_report_missing_bridge_evidence = _p3a1b.report_missing_bridge_evidence
p3a1b_bridge_theorem_source = _p3a1b.bridge_theorem_source
p3a1b_exact_n1_theorem_source = _p3a1b.exact_n1_theorem_source
p3a1b_residue_program_source = _p3a1b.residue_program_source

__all__ = (
    "P3A1B_PROGRAM_VERSION", "P3A1B_PROGRAM_CONSTRUCTOR", "P3A1B_PROGRAM_GRAMMAR_ID",
    "P3A1B_FORMAL_VERSION", "P3A1B_ARTIFACT_PATH", "P3A1B_ARTIFACT_SHA256",
    "P3A1B_THEOREM_IDS", "P3A1B_AXIOM_ROWS", "P3A1B_TCB_DIGEST",
    "P3A1B_LEDGER_DIGEST_ORACLE", "P3A1B_PRESSURE_VERSION",
    "P3A1B_PRESSURE_CONSTRUCTOR", "P3A1B_PRESSURE_GRAMMAR_ID",
    "P3A1B_PRESSURE_ARTIFACT_PATH", "P3A1B_PRESSURE_ARTIFACT_SHA256",
    "P3A1B_PRESSURE_THEOREM_IDS", "P3A1B_PRESSURE_AXIOM_ROWS", "P3A1B_NONCLAIMS",
    "P3A1BValidationError", "P3A1BBoundaryStatus", "P3A1BBridgeEvidenceKind",
    "P3A1BBridgeFormalFailure", "P3A1BBridgeLedger", "P3A1BBridgeOpen",
    "P3A1BBridgePolicy", "P3A1BBridgeProvenance", "P3A1BBridgeRefutation",
    "P3A1BBridgeResourceLimit", "P3A1BBridgeResult", "P3A1BBridgeStatus",
    "P3A1BBridgeTheoremSource", "P3A1BFailedBound", "P3A1BFamilyKind",
    "P3A1BFormalFailureKind", "P3A1BOffsetResidueProgramSource",
    "P3A1BProductiveBridgeJudgment", "P3A1BProductiveBridgePackage",
    "P3A1BProjectionArtifact", "P3A1BResidueProgramSource", "P3A1BResultStatus",
    "P3A1BUniformizationRoute", "p3a1b_bridge_ledger", "p3a1b_bridge_policy",
    "p3a1b_productive_bridge_package", "p3a1b_offset_residue_program_source",
    "p3a1b_validate_productive_bridge_result", "p3a1b_validate_projection_result",
    "p3a1b_validate_offset_refutation_result", "p3a1b_validate_open_result",
    "p3a1b_establish_productive_family_bridge", "p3a1b_project_residue",
    "p3a1b_refute_offset_program", "p3a1b_report_missing_bridge_evidence",
    "p3a1b_bridge_theorem_source", "p3a1b_exact_n1_theorem_source",
    "p3a1b_residue_program_source",
)
