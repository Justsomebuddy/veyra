"""Immutable DTOs for the finite P3-T observer translation network."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..morphism import ObserverSourceBinding, ProjectionStep
from ..relations.types import PairOutcome, RelationEvaluationSource
from ...ontology.types import ObserverDoctrine


class ResponseStatus(str, Enum):
    READY = "ready"
    SILENT = "silent"
    BLOCKED = "blocked"


class LawStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"
    NOT_ESTABLISHED = "not-established"
    VACUOUS_TYPED = "vacuous-typed"


class RefinementStatus(str, Enum):
    NONSTRICT = "nonstrict"
    STRICT = "strict"
    ISOMORPHIC = "isomorphic"
    INCOMPARABLE = "incomparable"
    OPEN = "open"


class TriangleStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"
    AGREES_ON_DOMAIN_INTERSECTION = "agrees-on-domain-intersection"


@dataclass(frozen=True)
class NetworkResourcePolicy:
    max_inputs: int
    max_observers: int
    max_edges: int
    max_rows: int
    max_evaluations: int
    max_paths: int
    max_canonical_bytes: int
    max_result_nodes: int
    max_result_depth: int
    max_result_bytes: int


@dataclass(frozen=True)
class RawObserverPairSource:
    pair_id: str
    source_observer_id: str
    target_observer_id: str
    morphism_id: str
    projection: tuple[ProjectionStep, ...] | None
    pair_digest: str


@dataclass(frozen=True)
class InputSnapshot:
    input_id: str
    type_id: str
    payload: bytes
    stage_commitment: str
    commitment: str


@dataclass(frozen=True)
class TypedValue:
    grammar_id: str
    kind_id: str
    payload: bytes
    value_digest: str


@dataclass(frozen=True)
class Response:
    status: ResponseStatus
    value: TypedValue | None
    reason_id: str
    response_digest: str


@dataclass(frozen=True)
class ObservationRow:
    input_commitment: str
    response: Response
    row_digest: str


@dataclass(frozen=True)
class GrammarDescriptor:
    grammar_id: str
    kind_id: str
    canonical_source: bytes
    commitment: str


@dataclass(frozen=True)
class ObserverSource:
    observer_id: str
    input_type_id: str
    ready_grammar_id: str
    ready_kind_id: str
    grammar_descriptor: GrammarDescriptor
    rows: tuple[ObservationRow, ...]
    observer_digest: str


@dataclass(frozen=True)
class TranslationRow:
    source_value: TypedValue
    target_value: TypedValue
    row_digest: str


@dataclass(frozen=True)
class TranslationSource:
    edge_id: str
    source_observer_id: str
    target_observer_id: str
    declared_domain: tuple[str, ...]
    rows: tuple[TranslationRow, ...]
    dependency_ids: tuple[str, ...]
    translation_digest: str


@dataclass(frozen=True)
class TriangleDemand:
    demand_id: str
    direct_edge_id: str
    indirect_edge_ids: tuple[str, ...]


@dataclass(frozen=True)
class ObserverNetworkSource:
    version: str
    doctrine_id: str
    source_id: str
    source_version: str
    inputs: tuple[InputSnapshot, ...]
    observers: tuple[ObserverSource, ...]
    translations: tuple[TranslationSource, ...]
    triangles: tuple[TriangleDemand, ...]
    p1a_doctrine: ObserverDoctrine
    p1a_binding: ObserverSourceBinding
    p1a_stage_source: RelationEvaluationSource
    raw_pairs: tuple[RawObserverPairSource, ...]
    network_digest: str


@dataclass(frozen=True)
class PartialMap:
    path_edge_ids: tuple[str, ...]
    source_observer_id: str
    target_observer_id: str
    domain: tuple[str, ...]
    rows: tuple[tuple[str, str], ...]
    map_digest: str


@dataclass(frozen=True)
class EvaluationDomainJudgment:
    observer_id: str
    input_commitments: tuple[str, ...]
    statuses: tuple[ResponseStatus, ...]
    response_digests: tuple[str, ...]
    ready_input_commitments: tuple[str, ...]
    judgment_digest: str


@dataclass(frozen=True)
class RelationReplayRow:
    pair_index: int
    left_input_commitment: str
    right_input_commitment: str
    source_outcome: PairOutcome
    target_outcome: PairOutcome
    row_digest: str


@dataclass(frozen=True)
class EdgeJudgment:
    edge_id: str
    operational_map: PartialMap
    relation_rows: tuple[RelationReplayRow, ...]
    relation_counterexample: tuple[str, str] | None
    translatable: LawStatus
    relation_preserving: LawStatus
    translation_preserving: LawStatus
    equal_evaluation_domain: LawStatus
    refinement: RefinementStatus
    separator_input_ids: tuple[str, str] | None
    judgment_digest: str


@dataclass(frozen=True)
class IsomorphismJudgment:
    forward_edge_id: str
    reverse_edge_id: str
    status: LawStatus
    evaluation_domains_agree: LawStatus
    forward_round_trip: LawStatus
    reverse_round_trip: LawStatus
    forward_evaluation_commutes: LawStatus
    reverse_evaluation_commutes: LawStatus
    judgment_digest: str


@dataclass(frozen=True)
class CompositionJudgment:
    edge_ids: tuple[str, str]
    operational_map: PartialMap
    relation_composed: LawStatus
    translation_composed: LawStatus
    judgment_digest: str


@dataclass(frozen=True)
class IdentityLawJudgment:
    edge_id: str
    left_exact_domain: bool
    right_exact_domain: bool
    left_status: LawStatus
    right_status: LawStatus
    judgment_digest: str


@dataclass(frozen=True)
class ObserverPairJudgment:
    source_observer_id: str
    target_observer_id: str
    path_edge_ids: tuple[str, ...]
    status: RefinementStatus
    forward_counterexample: tuple[str, str] | None
    reverse_counterexample: tuple[str, str] | None
    judgment_digest: str


@dataclass(frozen=True)
class AssociativityJudgment:
    edge_ids: tuple[str, str, str]
    left_map_digest: str
    right_map_digest: str
    exact_domain_equal: bool
    status: LawStatus
    judgment_digest: str


@dataclass(frozen=True)
class TriangleJudgment:
    demand_id: str
    direct_map_digest: str
    indirect_map_digest: str
    direct_domain: tuple[str, ...]
    indirect_domain: tuple[str, ...]
    status: TriangleStatus
    first_mismatch_digest: str
    judgment_digest: str


@dataclass(frozen=True)
class ObserverNetworkJudgment:
    source_digest: str
    identities: tuple[PartialMap, ...]
    evaluation_domains: tuple[EvaluationDomainJudgment, ...]
    identity_laws: tuple[IdentityLawJudgment, ...]
    edges: tuple[EdgeJudgment, ...]
    isomorphisms: tuple[IsomorphismJudgment, ...]
    observer_pairs: tuple[ObserverPairJudgment, ...]
    compositions: tuple[CompositionJudgment, ...]
    associativity: tuple[AssociativityJudgment, ...]
    triangles: tuple[TriangleJudgment, ...]
    strict_cycle_status: LawStatus
    strict_cycle_edge_ids: tuple[str, ...]
    promotions: int
    nonclaims: tuple[str, ...]
    judgment_digest: str
