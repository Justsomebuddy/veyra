"""Closed DTOs for the relative P1-to-R16 realization contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observer_descent_types import FiniteObserverDoctrine, State
from .proof_core_types import CoreTerm


class ResponseTotalization(str, Enum):
    """How partial R11 observations enter a total finite response table."""

    STRUCTURED_R11 = "structured-r11-v1"


class RealizationCostPolicy(str, Enum):
    """How costs are assigned to the generated finite join closure."""

    MINIMUM_GENERATOR_SUM = "minimum-generator-sum-v1"


class RealizationClosurePolicy(str, Enum):
    """How admitted source partitions are completed inside R16."""

    FINITE_JOIN_CLOSURE = "finite-join-closure-v1"


class ObservationStatus(str, Enum):
    """The exact R11 sum variant retained by totalization."""

    READY = "ready"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class RealizationInput:
    """One ordered finite state-to-closed-recurrence binding."""

    state: State
    recurrence: CoreTerm


@dataclass(frozen=True, slots=True)
class ObserverCost:
    """One explicit nonnegative base cost for an admitted P1 observer."""

    observer_id: str
    cost: int


@dataclass(frozen=True, slots=True)
class RealizationContext:
    """All non-canonical choices needed to realize one P1 doctrine."""

    realization_id: str
    inputs: tuple[RealizationInput, ...]
    observer_costs: tuple[ObserverCost, ...]
    response_policy: ResponseTotalization
    cost_policy: RealizationCostPolicy
    closure_policy: RealizationClosurePolicy
    version: str
    context_digest: str


@dataclass(frozen=True, slots=True)
class RealizationEvaluationRow:
    """One authoritative replay row with its structured R11 payload."""

    observer_id: str
    state_index: int
    state: State
    input_commitment: str
    status: ObservationStatus
    response_class: int
    observation_payload: bytes
    payload_digest: str


@dataclass(frozen=True, slots=True)
class RealizationClosureRow:
    """Provenance for one bottom/source/join partition in the R16 image."""

    observer_name: str
    generator_ids: tuple[str, ...]
    partition: tuple[int, ...]
    representative_indices: tuple[int, ...]
    partition_digest: str
    cost: int


@dataclass(frozen=True, slots=True)
class ObserverRealizationWitness:
    """Deterministic typed witness for one context-relative P1-to-R16 image."""

    schema: str
    source_doctrine_fingerprint: str
    context_digest: str
    evaluations: tuple[RealizationEvaluationRow, ...]
    source_mapping: tuple[tuple[str, str], ...]
    closure: tuple[RealizationClosureRow, ...]
    doctrine: FiniteObserverDoctrine
    doctrine_digest: str
    witness_digest: str
    scope: str = "finite-relative-replayed-no-functoriality"
