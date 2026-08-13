"""Closed DTOs for bounded same-doctrine realization transport."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..observer_realization_types import ObservationStatus


class CostTransportStatus(str, Enum):
    """Strength of the checked cost comparison for one pulled-back row."""

    NONINCREASING = "cost-nonincreasing"
    EXACT = "cost-exact"


@dataclass(frozen=True, slots=True)
class ContextMorphism:
    """A total source-index to target-index graph between bound contexts."""

    morphism_id: str
    source_context_digest: str
    target_context_digest: str
    state_index_map: tuple[int, ...]
    version: str
    morphism_digest: str


@dataclass(frozen=True, slots=True)
class RecurrenceCommutingRow:
    """Exact source/target recurrence commitments for one state-map edge."""

    source_index: int
    target_index: int
    source_input_commitment: str
    target_input_commitment: str


@dataclass(frozen=True, slots=True)
class EvaluationCommutingRow:
    """One full structured observation equality across a state-map edge."""

    observer_id: str
    source_index: int
    target_index: int
    status: ObservationStatus
    payload_digest: str


@dataclass(frozen=True, slots=True)
class ClosureActionRow:
    """Contravariant pullback of one target closure partition."""

    target_partition_digest: str
    source_partition: tuple[int, ...]
    source_partition_digest: str
    source_closure_index: int


@dataclass(frozen=True, slots=True)
class CostTransportRow:
    """Checked cost relation for one target-to-source closure action."""

    target_partition_digest: str
    source_partition_digest: str
    source_cost: int
    target_cost: int
    status: CostTransportStatus


@dataclass(frozen=True, slots=True)
class RealizationTransportReceipt:
    """Reconstructible receipt for one bounded, replayed context arrow."""

    schema: str
    doctrine_fingerprint: str
    source_context_digest: str
    target_context_digest: str
    source_witness_digest: str
    target_witness_digest: str
    morphism: ContextMorphism
    recurrence_rows: tuple[RecurrenceCommutingRow, ...]
    evaluation_rows: tuple[EvaluationCommutingRow, ...]
    closure_action: tuple[ClosureActionRow, ...]
    cost_rows: tuple[CostTransportRow, ...]
    bottom_preserved: bool
    joins_preserved: bool
    receipt_digest: str
    scope: str
