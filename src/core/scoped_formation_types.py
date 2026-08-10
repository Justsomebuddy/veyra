"""Closed DTOs for P1-C4 finite scoped-object formation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .confluence_aggregate_types import FiniteConfluenceCatalogSource
from .confluence_types import FiniteDiagramSource, ForkJoinPlan
from .construction.finite_builder.types import ConstructionSourceBinding
from .observer_patch_validation import LocalObserverSection, ObserverPatchAtlas
from .observer_relation_resource_types import RelationResourcePolicy
from .observer_morphism_types import ObserverSourceBinding
from .observer_relation_types import (
    LawStatus, LossStatus, MorphismEvidenceStatus, MorphismReplaySpec,
    ObserverRelationScope, RelationClass, RelationEvaluationSource,
)
from .positive_ontology_types import ObserverDoctrine, OntologyStage
from .translated_confluence_types import (
    P0P1AResponseBridgeSource, TranslatedConfluencePolicy,
    TranslatedEchoTransportSpec,
)


SCOPED_FORMATION_NONCLAIMS = (
    "necessary-object-criterion", "ontic-genesis", "chronology",
    "target-independent-selection", "primitive-identity", "absolute-identity",
    "absolute-existence", "physical-instantiation", "universal-refinement",
    "graph-wide-confluence", "unbounded-confluence", "productivity",
    "all-depth-family", "completed-carrier", "consciousness", "novelty",
    "r8-promotion", "layer-promotion", "sage-promotion",
)


class ScopedFormationStatus(str, Enum):
    ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE = "established-relative-to-formation-scope"
    REFUTED = "refuted"
    OPEN = "open"


class RequiredConfluenceLevel(str, Enum):
    LOCAL_FINITE = "local-finite"
    GLOBAL_DECLARED_FINITE = "global-declared-finite"


class SurvivalMode(str, Enum):
    DIRECT = "direct"
    TRANSLATED = "translated"


class FormationFailedBound(str, Enum):
    BYTES = "bytes"
    CHECKS = "checks"


class FormationLimitSource(str, Enum):
    OUTER = "outer"
    NESTED_C2 = "nested-c2"
    NESTED_A2 = "nested-a2"
    NESTED_C3 = "nested-c3"


@dataclass(frozen=True, slots=True)
class FormationPolicy:
    version: str
    max_checks: int
    max_bytes: int
    policy_digest: str


@dataclass(frozen=True, slots=True)
class FiniteScopedFormationRuleSource:
    version: str
    doctrine_fingerprint: str
    rule_id: str
    accepted_schema_ids: tuple[str, ...]
    component_order: tuple[str, ...]
    statement_digest: str
    trust_ledger_id: str
    source_digest: str


@dataclass(frozen=True, slots=True)
class StageMapRow:
    node_id: str
    stage_id: str
    stage_commitment: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class BoundPatchRequirement:
    patch_id: str
    path_ids: tuple[str, ...]
    observer_ids: tuple[str, ...]
    expected_nodes: tuple[str, ...]
    requirement_digest: str


@dataclass(frozen=True, slots=True)
class G4BridgeMappings:
    stage_map: tuple[StageMapRow, ...]
    patch_requirements: tuple[BoundPatchRequirement, ...]


@dataclass(frozen=True, slots=True)
class BoundG4BridgeSource:
    version: str
    doctrine_fingerprint: str
    diagram_digest: str
    atlas: ObserverPatchAtlas
    stage_map: tuple[StageMapRow, ...]
    patch_requirements: tuple[BoundPatchRequirement, ...]
    bridge_digest: str


@dataclass(frozen=True, slots=True)
class FormationPersistenceRequirement:
    observer_id: str
    path_id: str
    requirement_digest: str


@dataclass(frozen=True, slots=True)
class FormationRefinementRequirement:
    requirement_id: str
    a2_doctrine: ObserverDoctrine
    a2_observer_source: ObserverSourceBinding
    a2_stage_source: RelationEvaluationSource
    relation_scope: ObserverRelationScope
    morphism: MorphismReplaySpec
    fine_observer_id: str
    coarse_observer_id: str
    required_class: RelationClass
    required_preservation: LawStatus
    required_reflection: LawStatus
    required_domain_equality: LawStatus
    required_translation: MorphismEvidenceStatus
    required_loss: LossStatus
    path_ids: tuple[str, ...]
    survival_mode: SurvivalMode
    direct_observer_id: str | None
    direct_bridge: P0P1AResponseBridgeSource | None
    translated_plan: ForkJoinPlan | None
    translated_bridge: P0P1AResponseBridgeSource | None
    translated_spec: TranslatedEchoTransportSpec | None
    translated_policy: TranslatedConfluencePolicy | None
    relation_policy: RelationResourcePolicy
    joint_square_digest: str
    requirement_digest: str


@dataclass(frozen=True, slots=True)
class FormationScope:
    version: str
    scope_id: str
    presentation_id: str
    doctrine: ObserverDoctrine
    rule_source_digest: str
    construction_source: ConstructionSourceBinding
    target: OntologyStage
    expected_target_stage_id: str
    expected_target_commitment: str
    diagram: FiniteDiagramSource
    c2_catalog: FiniteConfluenceCatalogSource
    required_confluence: RequiredConfluenceLevel
    support_observer_ids: tuple[str, ...]
    persistence: tuple[FormationPersistenceRequirement, ...]
    g4_bridge: BoundG4BridgeSource
    refinements: tuple[FormationRefinementRequirement, ...]
    policy: FormationPolicy
    scope_digest: str


@dataclass(frozen=True, slots=True)
class FormationComponentRow:
    component: str
    key: str
    status: ScopedFormationStatus
    evidence_digest: str
    obstruction: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class G4ResponseRow:
    patch_id: str
    observer_id: str
    left_node: str
    right_node: str
    status: ScopedFormationStatus
    outcome: str
    left_payload_digest: str
    right_payload_digest: str
    row_digest: str


@dataclass(frozen=True, slots=True)
class G4ContradictionRow:
    patch_id: str
    left_node: str
    right_node: str
    contradiction_digest: str


@dataclass(frozen=True, slots=True)
class BoundG4BridgeJudgment:
    doctrine_fingerprint: str
    diagram_digest: str
    bridge_digest: str
    expected_patch_keys: tuple[str, ...]
    expected_response_keys: tuple[tuple[str, str, str, str], ...]
    response_rows: tuple[G4ResponseRow, ...]
    sections: tuple[LocalObserverSection, ...]
    section_digests: tuple[str, ...]
    contradiction_rows: tuple[G4ContradictionRow, ...]
    first_contradiction: G4ContradictionRow | None
    criterion_digest: str
    status: ScopedFormationStatus
    first_obstruction: str
    trace_digest: str
    run_digest: str
    judgment_digest: str


@dataclass(frozen=True, slots=True)
class FiniteScopedObjectPresentation:
    presentation_id: str
    target_stage: OntologyStage
    target_stage_id: str
    target_commitment: str
    doctrine_fingerprint: str
    rule_source_digest: str
    scope_digest: str
    construction_digest: str
    support_digest: str
    persistence_digest: str
    g4_digest: str
    confluence_digest: str
    refinement_digest: str
    survival_digest: str
    component_order_digest: str
    presentation_digest: str
    status: ScopedFormationStatus = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE


@dataclass(frozen=True, slots=True)
class ScopedFormationJudgment:
    rule_source_digest: str
    scope_digest: str
    policy_digest: str
    run_digest: str
    source_digests: tuple[str, ...]
    target_commitment: str
    g4: BoundG4BridgeJudgment
    component_rows: tuple[FormationComponentRow, ...]
    expected_component_keys: tuple[tuple[str, str], ...]
    status: ScopedFormationStatus
    first_obstruction: str
    presentation: FiniteScopedObjectPresentation | None
    charged_checks: int
    canonical_bytes: int
    judgment_digest: str
    nonclaims: tuple[str, ...] = SCOPED_FORMATION_NONCLAIMS


@dataclass(frozen=True, slots=True)
class ScopedFormationResourceLimit:
    rule_source_digest: str
    scope_digest: str
    policy_digest: str
    run_digest: str
    source_digests: tuple[str, ...]
    failed_bound: FormationFailedBound
    limit_source: FormationLimitSource
    required_value: int
    allowed_value: int
    refusal_digest: str
    status: str = "resource-limit"
    nonclaims: tuple[str, ...] = SCOPED_FORMATION_NONCLAIMS


ScopedFormationResult: TypeAlias = ScopedFormationJudgment | ScopedFormationResourceLimit
