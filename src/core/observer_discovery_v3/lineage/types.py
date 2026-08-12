"""Immutable records for declared adaptive experiment research lines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


LINEAGE_SCHEMA = "veyra.observer-discovery.research-line.v1"
LINEAGE_BOUNDARY = (
    "canonical declared research-line history only; no trusted chronology, completeness of disclosure, "
    "statistical independence, family-wise error control, significance, or population-generalization proof"
)
ASSESSMENT_BOUNDARY = (
    "local governed-result validation and declared-family recording are separate from adaptive validity; "
    "named but unverified statistical policy never licenses significance or population wording"
)


class ExperimentDesignMode(str, Enum):
    """Whether a node is isolated, predeclared, or outcome-adaptive."""

    ISOLATED = "ISOLATED"
    PREDECLARED_CONTINUATION = "PREDECLARED_CONTINUATION"
    ADAPTIVE_AFTER_OUTCOME = "ADAPTIVE_AFTER_OUTCOME"


class TerminalLocalStatus(str, Enum):
    """Declared terminal status before independent local-result replay."""

    LOCALLY_VALID = "LOCALLY_VALID"
    LOCALLY_BLOCKED = "LOCALLY_BLOCKED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class PolicyClaimScope(str, Enum):
    """Claim class requested by one named family-level policy."""

    EXPLORATORY_ONLY = "EXPLORATORY_ONLY"
    INFERENTIAL = "INFERENTIAL"


class LocalValidityStatus(str, Enum):
    """Executable validation status for the selected terminal experiment."""

    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class FamilyRecordingStatus(str, Enum):
    """Whether the supplied bounded lineage is internally complete and canonical."""

    RECORDED_RELATIVE_TO_DECLARATION = "RECORDED_RELATIVE_TO_DECLARATION"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class AdaptiveValidityStatus(str, Enum):
    """Family/adaptive inference status kept separate from local validity."""

    ISOLATED_LOCAL_ONLY = "ISOLATED_LOCAL_ONLY"
    EXPLORATORY_NO_INFERENCE_CLAIMED = "EXPLORATORY_NO_INFERENCE_CLAIMED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class AdaptivePolicyStatus(str, Enum):
    """How far a named policy is established by this implementation."""

    NOT_REQUIRED_FOR_ISOLATED_LOCAL_RESULT = "NOT_REQUIRED_FOR_ISOLATED_LOCAL_RESULT"
    ABSENT = "ABSENT"
    EXPLORATORY_ONLY = "EXPLORATORY_ONLY"
    DECLARED_UNVERIFIED = "DECLARED_UNVERIFIED"


@dataclass(frozen=True, slots=True)
class ExperimentLineageNode:
    """One content-bound experiment and its declared design ancestry."""

    experiment_root: str
    parent_nodes: tuple[str, ...]
    doctrine_root: str
    grammar_root: str
    baseline_root: str
    decision_policy_root: str
    data_commitment_roots: tuple[str, ...]
    prior_outcomes_visible_before_design: tuple[str, ...]
    design_mode: ExperimentDesignMode
    adaptation_reason: str
    terminal_local_status: TerminalLocalStatus
    terminal_outcome_root: str
    node_digest: str


@dataclass(frozen=True, slots=True)
class ExperimentResearchLine:
    """One canonical bounded DAG of declared experiment attempts."""

    schema_version: str
    nodes: tuple[ExperimentLineageNode, ...]
    lineage_digest: str
    boundary: str = LINEAGE_BOUNDARY


@dataclass(frozen=True, slots=True)
class AdaptiveInferencePolicy:
    """A named pluggable family policy; this layer does not verify its mathematics."""

    policy_id: str
    policy_family: str
    policy_root: str
    evidence_root: str
    claim_scope: PolicyClaimScope


@dataclass(frozen=True, slots=True)
class ResearchLineAssessment:
    """Orthogonal local, family-recording, and adaptive-validity statuses."""

    terminal_node: str
    local_validity: LocalValidityStatus
    family_recording: FamilyRecordingStatus
    adaptive_validity: AdaptiveValidityStatus
    policy_status: AdaptivePolicyStatus
    policy_id: str
    policy_family: str
    policy_root: str
    policy_evidence_root: str
    significance_wording_allowed: bool
    population_wording_allowed: bool
    allowed_claims: tuple[str, ...]
    assessment_digest: str
    boundary: str = ASSESSMENT_BOUNDARY


@dataclass(frozen=True, slots=True)
class AdaptiveRetryWitness:
    """Exact independent-null witness that local alpha does not compose."""

    attempts: int
    alpha_numerator: int
    alpha_denominator: int
    any_positive_numerator: int
    any_positive_denominator: int
    local_protocol_validity_compatible: bool
    family_policy_accounted: bool
    adaptive_validity: AdaptiveValidityStatus
    assumptions: tuple[str, ...]
    witness_digest: str
