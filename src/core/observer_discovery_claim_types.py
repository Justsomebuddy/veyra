"""Typed epistemic claim envelope for bounded observer discovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiscoveryExecutionLevel(str, Enum):
    """Operational evidence reached by one discovery report."""

    BLOCKED = "E-blocked"
    BOUNDED_SEARCH_COMPLETE = "E2-bounded-search-complete"
    LOCKED_HOLDOUT_PASSED = "E3V-locked-holdout-passed"
    DECLARED_TEST_REPLICATED = "E3T-declared-test-replicated"


class DiscoveryInterpretationLevel(str, Enum):
    """Interpretation licensed independently of execution level."""

    NONE = "I-none"
    SEPARATOR = "I0-separator"
    DECLARED_BASELINE_GAP = "I1-declared-baseline-gap"


class DiscoveryOntologyLevel(str, Enum):
    """Ontological commitment of the empirical protocol."""

    PRESENTATION_ONLY = "O0-presentation-only"


class DiscoveryObserverRole(str, Enum):
    """Role assigned to the selected R5 callable-backed observer."""

    RESEARCH_SHADOW = "research-shadow"


class ClaimDisposition(str, Enum):
    """Whether the exact scoped claim is supported by this envelope."""

    SUPPORTED = "supported"
    NOT_ESTABLISHED = "not-established"
    NOT_CLAIMED = "not-claimed"


@dataclass(frozen=True)
class DiscoveryClaimScope:
    """Evidence roots that bound an empirical discovery claim."""

    protocol_digest: str
    result_digest: str
    grammar_digest: str
    train_data_digest: str
    holdout_data_digest: str
    catalog_digest: str
    boundary: str


@dataclass(frozen=True)
class DiscoveryClaimEnvelope:
    """Orthogonal execution, interpretation, and ontology judgments."""

    source_status: str
    execution: DiscoveryExecutionLevel
    interpretation: DiscoveryInterpretationLevel
    ontology: DiscoveryOntologyLevel
    observer_role: DiscoveryObserverRole
    association_witness: ClaimDisposition
    bounded_search_nonfinding: ClaimDisposition
    causality: ClaimDisposition
    semantic_explanation: ClaimDisposition
    theoremhood: ClaimDisposition
    object_formation: ClaimDisposition
    p0_admission: ClaimDisposition
    historical_novelty: ClaimDisposition
    scope: DiscoveryClaimScope
    claim_digest: str
