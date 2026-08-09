"""Closed DTOs for P1-C3 typed translated confluence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ..types import ConfluenceObstruction, ConfluenceStatus, DirectEchoTransport
from ...observer.relations.types import RelationResourcePolicy
from ...observer.relations.types import (
    LawStatus, LossStatus, MorphismReplaySpec, ObserverRelationScope,
    RelationClass,
)
from ...proof_core_types import CoreTerm


TRANSLATED_CONFLUENCE_NONCLAIMS = (
    "observer-identity", "reverse-translation", "universal-refinement",
    "catalog-confluence", "object-formation", "chronology",
    "ontic-observer-genesis", "unbounded-confluence", "all-depth-family",
    "completed-carrier", "novelty", "r8-promotion", "layer-promotion",
    "sage-promotion",
)


class TranslationDirection(str, Enum):
    """The fine and coarse sides of one asymmetric translated cell."""

    LEFT_FINE_TO_RIGHT_COARSE = "left-fine-to-right-coarse"
    RIGHT_FINE_TO_LEFT_COARSE = "right-fine-to-left-coarse"


class C3TransportMode(str, Enum):
    """C3 keeps the accepted direct lane disjoint from translation."""

    DIRECT_ECHO = "direct-echo"
    TYPED_TRANSLATION = "typed-translation"


class TranslatedResourceBound(str, Enum):
    """Closed resource dimension selected by bytes-before-checks priority."""

    BYTES = "bytes"
    CHECKS = "checks"


class TranslatedResourceSource(str, Enum):
    """Closed policy source responsible for a reachable refusal."""

    OUTER = "outer"
    NESTED_A2 = "nested-a2"


@dataclass(frozen=True, slots=True)
class ObserverProgramBridgeRow:
    """One exact byte-and-kind P0 to P1-A observer correspondence."""

    diagram_observer_id: str
    p1a_observer_id: str
    canonical_observer: bytes
    response_kind_digest: str
    diagram_membership_digest: str
    p1a_membership_digest: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class StageInputBridgeRow:
    """One immutable P0 stage recurrence bound to one A2 stage key."""

    diagram_stage_id: str
    diagram_stage_commitment: str
    recurrence: CoreTerm
    recurrence_digest: str
    relation_stage_id: str
    relation_stage_commitment: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class P0P1AResponseBridgeSource:
    """Raw-source bridge; it contains no response or prior judgment."""

    p0_doctrine_fingerprint: str
    diagram_digest: str
    p1a_doctrine_fingerprint: str
    p1a_observer_source_digest: str
    a2_stage_source_digest: str
    observer_rows: tuple[ObserverProgramBridgeRow, ...]
    stage_rows: tuple[StageInputBridgeRow, ...]
    a2_ordered_commitments: tuple[str, ...]
    bridge_digest: str
    version: str = "p1-c3-bridge-v1"
    scope: str = "exact-byte-kind-and-recurrence-source-bridge"


@dataclass(frozen=True, slots=True)
class TranslatedEchoTransportSpec:
    """Raw P1-A/A2 evidence requirements for one directed translation."""

    spec_id: str
    bridge_digest: str
    plan_digest: str
    direction: TranslationDirection
    diagram_fine_observer_id: str
    diagram_coarse_observer_id: str
    p1a_fine_observer_id: str
    p1a_coarse_observer_id: str
    morphism: MorphismReplaySpec
    relation_scope: ObserverRelationScope
    relation_policy: RelationResourcePolicy
    required_preservation: LawStatus
    required_domain_equality: LawStatus
    required_class: RelationClass
    required_loss: LossStatus | None
    spec_digest: str
    version: str = "p1-c3-spec-v1"
    mode: C3TransportMode = C3TransportMode.TYPED_TRANSLATION
    scope: str = "one-directed-finite-translated-cell"


C3TransportSpec: TypeAlias = DirectEchoTransport | TranslatedEchoTransportSpec


@dataclass(frozen=True, slots=True)
class TranslatedResponseRow:
    """One occurrence-complete freshly evaluated response triangle."""

    point_index: int
    left_index: int
    right_index: int
    fine_stage_id: str
    coarse_stage_id: str
    diagram_fine_observer_id: str
    diagram_coarse_observer_id: str
    p1a_fine_observer_id: str
    p1a_coarse_observer_id: str
    status: ConfluenceStatus
    outcome: str
    fine_payload_digest: str
    translated_payload_digest: str
    coarse_payload_digest: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class TranslatedTransport2CellArtifact:
    """One typed translated 2-cell over two exact complete histories."""

    doctrine_fingerprint: str
    diagram_digest: str
    plan_digest: str
    fork_stage_commitment: str
    left_history_digest: str
    right_history_digest: str
    left_join_history_digest: str
    right_join_history_digest: str
    join_stage_commitment: str
    alignment_digest: str
    bridge_digest: str
    spec_digest: str
    a2_source_digest: str
    a2_result_digest: str
    direction: TranslationDirection
    observer_pair: tuple[str, str]
    response_rows: tuple[TranslatedResponseRow, ...]
    left_trace_digest: str
    right_trace_digest: str
    trace_digest: str
    artifact_digest: str
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    status: ConfluenceStatus
    mode: C3TransportMode = C3TransportMode.TYPED_TRANSLATION
    scope: str = "derived-one-directed-translated-2-cell"


@dataclass(frozen=True, slots=True)
class TranslatedConfluencePolicy:
    """Outer atomic resource policy for C3."""

    version: str
    max_checks: int
    max_bytes: int
    policy_digest: str


@dataclass(frozen=True, slots=True)
class TranslatedConfluenceResourceLimit:
    """Payload-free policy refusal after a valid hard-bounded snapshot."""

    policy_version: str
    policy_digest: str
    diagram_digest: str
    plan_digest: str
    bridge_digest: str
    spec_digest: str
    required_checks: int
    allowed_checks: int
    required_bytes: int
    allowed_bytes: int
    failed_bound: TranslatedResourceBound
    limit_source: TranslatedResourceSource
    failed_required: int
    failed_allowed: int
    refusal_digest: str
    status: str = "resource-limit"
    nonclaims: tuple[str, ...] = TRANSLATED_CONFLUENCE_NONCLAIMS


@dataclass(frozen=True, slots=True)
class TranslatedConfluenceJudgment:
    """One finite asymmetric translated-confluence result."""

    doctrine_fingerprint: str
    diagram_digest: str
    plan_digest: str
    p1a_doctrine_fingerprint: str
    p1a_observer_source_digest: str
    a2_stage_source_digest: str
    bridge_digest: str
    spec_digest: str
    policy_digest: str
    a2_scope_digest: str
    a2_result_digest: str
    preservation: LawStatus
    domain_equality: LawStatus
    relation_class: RelationClass
    information_loss: LossStatus
    direction: TranslationDirection
    status: ConfluenceStatus
    transport_cell: TranslatedTransport2CellArtifact | None
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    run_digest: str
    judgment_digest: str
    mode: C3TransportMode = C3TransportMode.TYPED_TRANSLATION
    nonclaims: tuple[str, ...] = TRANSLATED_CONFLUENCE_NONCLAIMS


TranslatedConfluenceResult: TypeAlias = (
    TranslatedConfluenceJudgment | TranslatedConfluenceResourceLimit
)
