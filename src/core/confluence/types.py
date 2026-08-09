"""Closed DTOs for provisional P1-C1 direct-echo confluence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..ontology.types import OntologyStage


class ConfluenceStatus(str, Enum):
    """Exact outcomes for one fully validated finite fork."""

    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"


class TransportMode(str, Enum):
    """C1 admits only direct echo; translation is not represented."""

    DIRECT_ECHO = "direct-echo"


class HigherConfluence(str, Enum):
    """C1 cannot promote one fork to finite or unbounded confluence."""

    OPEN = "open"


class ScopedFormation(str, Enum):
    """C1 supplies no scoped-object formation rule."""

    OPEN = "open"


@dataclass(frozen=True)
class DiagramEdge:
    """One exact directed stage transition with named persistence observers."""

    edge_id: str
    lower_stage_id: str
    upper_stage_id: str
    preserved_observer_ids: tuple[str, ...]


@dataclass(frozen=True)
class DiagramPath:
    """A nonempty ordered edge history with claimed endpoints."""

    path_id: str
    edge_ids: tuple[str, ...]
    start_stage_id: str
    end_stage_id: str


@dataclass(frozen=True)
class FiniteDiagramSource:
    """Doctrine-bound immutable source for a generic finite diagram."""

    source_id: str
    doctrine_fingerprint: str
    stages: tuple[OntologyStage, ...]
    stage_commitments: tuple[str, ...]
    edges: tuple[DiagramEdge, ...]
    paths: tuple[DiagramPath, ...]
    path_commitments: tuple[str, ...]
    source_digest: str
    version: str = "p1-c1-v1"
    scope: str = "finite-declared-diagram-membership-not-universal-coverage"


@dataclass(frozen=True)
class AlignmentPoint:
    """One monotone comparison coordinate in two complete histories."""

    left_index: int
    right_index: int


@dataclass(frozen=True)
class DirectEchoTransport:
    """An exact ordered observer family for direct response comparison."""

    observer_ids: tuple[str, ...]
    transport_digest: str
    mode: TransportMode = TransportMode.DIRECT_ECHO
    scope: str = "direct-echo-only-no-translation"


@dataclass(frozen=True)
class ForkJoinPlan:
    """Two distinct branches, optional separate joins, and full alignment."""

    plan_id: str
    diagram_digest: str
    fork_stage_commitment: str
    left_branch_path_id: str
    right_branch_path_id: str
    left_join_path_id: str | None
    right_join_path_id: str | None
    join_stage_commitment: str | None
    alignment: tuple[AlignmentPoint, ...]
    transport_digest: str
    plan_digest: str
    version: str = "p1-c1-plan-v1"
    scope: str = "one-declared-fork-direct-echo"


@dataclass(frozen=True)
class DiagramPathReplay:
    """Fresh reconstruction of one or more composable declared paths."""

    source_path_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    stages: tuple[OntologyStage, ...]
    stage_commitments: tuple[str, ...]
    history_digest: str
    scope: str = "fresh-finite-path-replay"


@dataclass(frozen=True)
class TransportResponseRow:
    """One complete derived aligned response record."""

    point_index: int
    left_index: int
    right_index: int
    left_stage_id: str
    right_stage_id: str
    observer_id: str
    status: ConfluenceStatus
    outcome: str
    outcome_payload: bytes
    row_digest: str


@dataclass(frozen=True)
class ConfluenceObstruction:
    """The first canonical mismatch, block, or missing evidence."""

    lane: str
    occurrence: int
    observer_id: str
    outcome: str


@dataclass(frozen=True)
class Transport2CellArtifact:
    """Derived direct-echo 2-cell over both complete joined histories."""

    doctrine_fingerprint: str
    diagram_digest: str
    plan_digest: str
    fork_stage_commitment: str
    left_history_digest: str
    right_history_digest: str
    left_join_history_digest: str
    right_join_history_digest: str
    join_stage_commitment: str
    required_observer_ids: tuple[str, ...]
    mode: TransportMode
    transport_digest: str
    response_rows: tuple[TransportResponseRow, ...]
    left_trace_digest: str
    right_trace_digest: str
    trace_digest: str
    first_obstruction: ConfluenceObstruction | None
    status: ConfluenceStatus
    scope: str = "derived-direct-echo-2-cell"


@dataclass(frozen=True)
class ForkConfluenceJudgment:
    """One source-relative fork result with all higher claims open."""

    plan_id: str
    plan_digest: str
    status: ConfluenceStatus
    transport_cell: Transport2CellArtifact | None
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    local_finite_confluence: HigherConfluence = HigherConfluence.OPEN
    global_confluence: HigherConfluence = HigherConfluence.OPEN
    scoped_formation: ScopedFormation = ScopedFormation.OPEN
    scope: str = "one-bound-fork-no-aggregation-or-promotion"


@dataclass(frozen=True)
class ConfluencePreflightCharge:
    """Shared C1-C4 accounting inputs, all charged before observation."""

    edge_path_occurrences: int
    alignment_points: int
    transport_observers: int
    target_support: int = 0
    response_g4_rows: int = 0
    refinement_checks: int = 0
    direct_survival_checks: int = 0
