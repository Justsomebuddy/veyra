"""Fresh component replay for the P1-C4 formation rule."""

from __future__ import annotations

from dataclasses import replace
import json
import logging

from .confluence_aggregate_runtime import finite_confluence_aggregate
from .confluence_aggregate_types import (
    FiniteConfluenceAggregate, GlobalDeclaredFiniteStatus, LocalFiniteStatus,
)
from .confluence_path import replay_diagram_path
from .confluence_types import ConfluenceStatus
from .construction.finite_builder.types import FormalGenerability
from .finite_construction import finite_construction_judgment
from .observer_core_codec import decode_observer
from .observer_core_semantics import echo, observe
from .observer_core_support import outcome_data
from .observer_core_types import DomainBlocked, Echo, Mismatch, Ready
from .observer_relation_resource_types import RelationResourceLimit
from .observer_relation_runtime import observer_relation_judgment
from .observer_morphism import observer_morphism_judgment
from .observer_morphism_types import MorphismStatus
from .observer_relation_types import (
    ObserverRelationJudgment, ProposalStatus, RelationClass,
)
from .scoped_formation_codec import digest
from .positive_ontology_doctrine import stage_commitment
from .scoped_formation_g4 import replay_bound_g4_bridge
from .scoped_formation_types import (
    FormationComponentRow, FormationRefinementRequirement, FormationScope,
    RequiredConfluenceLevel, ScopedFormationStatus, SurvivalMode,
)
from .translated_confluence_runtime import translated_confluence_judgment
from .translated_confluence_types import (
    TranslatedConfluenceJudgment, TranslatedConfluenceResourceLimit,
)

logger = logging.getLogger(__name__)

def replay_components(scope: FormationScope):
    """Replay components in the exact SFP rule order."""
    logger.debug("replay_components entry")
    construction = finite_construction_judgment(scope.doctrine, scope.construction_source, scope.target)
    rows = [_row(
        "construction", scope.construction_source.membership_digest,
        ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE if construction.formal_generability is FormalGenerability.GENERABLE else ScopedFormationStatus.REFUTED,
        construction.replay.trace_digest, construction.obstruction,
    )]
    matches = tuple(x for x in scope.diagram.stages if x.stage_id == scope.target.stage_id)
    member = len(matches) == 1 and stage_commitment(matches[0]) == stage_commitment(scope.target)
    rows.append(_row(
        "target-membership", scope.target.stage_id,
        ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE if member else ScopedFormationStatus.REFUTED,
        digest("c4.target-membership", scope.diagram.source_digest, scope.target.stage_id, stage_commitment(scope.target), member),
        "" if member else "target-not-exact-diagram-member",
    ))
    rows.extend(_support_rows(scope))
    g4 = replay_bound_g4_bridge(scope.doctrine, scope.diagram, scope.g4_bridge)
    rows.append(_row("g4", scope.g4_bridge.bridge_digest, g4.status, g4.judgment_digest, g4.first_obstruction))
    rows.extend(_persistence_rows(scope))
    rows.append(_c2_row(scope))
    a2_results = []
    for requirement in scope.refinements:
        a2, p1a_digest, a2_row = _a2_row(requirement)
        a2_results.append((a2, p1a_digest))
        rows.append(a2_row)
    for requirement, (a2, p1a_digest) in zip(scope.refinements, a2_results, strict=True):
        rows.append(_survival_row(scope, requirement, a2, p1a_digest))
    result = g4, tuple(rows)
    logger.debug("replay_components exit rows=%d", len(rows))
    return result

def expected_component_keys(scope: FormationScope) -> tuple[tuple[str, str], ...]:
    """Derive complete ordered component keys without semantic replay."""
    logger.debug("expected_component_keys entry")
    result = (
        ("construction", scope.construction_source.membership_digest),
        ("target-membership", scope.target.stage_id),
        *(("support", x) for x in scope.support_observer_ids),
        ("g4", scope.g4_bridge.bridge_digest),
        *(("persistence", f"{x.observer_id}@{x.path_id}") for x in scope.persistence),
        ("c2-confluence", scope.c2_catalog.catalog_digest),
        *(("a2-refinement", x.requirement_id) for x in scope.refinements),
        *(("survival", x.requirement_id) for x in scope.refinements),
    )
    logger.debug("expected_component_keys exit rows=%d", len(result))
    return result

def _row(component: str, key: str, status: ScopedFormationStatus, evidence: str, obstruction: str) -> FormationComponentRow:
    """Commit one bounded derived component row."""
    logger.debug("_row entry component=%s", component)
    provisional = FormationComponentRow(component, key, status, evidence, obstruction, "")
    result = replace(provisional, row_digest=digest("c4.component", provisional))
    logger.debug("_row exit status=%s", status.value)
    return result

def _support_rows(scope: FormationScope) -> tuple[FormationComponentRow, ...]:
    """Freshly require each demanded target support response to be ready."""
    logger.debug("_support_rows entry")
    target_members = {x.observer_id: x for x in scope.target.observers}
    rows = []
    for observer_id in scope.support_observer_ids:
        observer = target_members.get(observer_id)
        if observer is None:
            rows.append(_row("support", observer_id, ScopedFormationStatus.OPEN, digest("c4.support.missing", observer_id), "observer-not-in-target-prefix"))
            continue
        result = observe(decode_observer(observer.canonical), scope.target.representative)
        encoded = json.dumps(outcome_data(result), sort_keys=True, separators=(",", ":")).encode()
        status = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE if type(result) is Ready else ScopedFormationStatus.OPEN
        rows.append(_row("support", observer_id, status, digest("c4.support", encoded), "" if status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE else "support-domain-blocked"))
    result = tuple(rows)
    logger.debug("_support_rows exit rows=%d", len(result))
    return result

def _persistence_rows(scope: FormationScope) -> tuple[FormationComponentRow, ...]:
    """Freshly replay each demanded observer on every path occurrence."""
    logger.debug("_persistence_rows entry")
    observers = {x.observer_id: x for x in scope.doctrine.observers}
    rows = []
    for requirement in scope.persistence:
        replay = replay_diagram_path(scope.doctrine, scope.diagram, requirement.path_id)
        outcomes = tuple(
            echo(decode_observer(observers[requirement.observer_id].canonical), left.representative, right.representative)
            for left, right in zip(replay.stages, replay.stages[1:])
        )
        status, obstruction = _echo_status(outcomes, "persistence")
        payloads = tuple(
            json.dumps(outcome_data(x), sort_keys=True, separators=(",", ":")).encode()
            for x in outcomes
        )
        evidence = digest(
            "c4.persistence.trace", requirement.requirement_digest, payloads,
        )
        rows.append(_row("persistence", f"{requirement.observer_id}@{requirement.path_id}", status, evidence, obstruction))
    result = tuple(rows)
    logger.debug("_persistence_rows exit rows=%d", len(result))
    return result

def _c2_row(scope: FormationScope) -> FormationComponentRow:
    """Freshly replay and require exactly the declared C2 confluence level."""
    logger.debug("_c2_row entry")
    value = finite_confluence_aggregate(scope.doctrine, scope.diagram, scope.c2_catalog)
    if not isinstance(value, FiniteConfluenceAggregate):
        logger.error("_c2_row unexpected nested refusal")
        raise RuntimeError("nested C2 refusal after admitted outer preflight")
    actual = value.local_status if scope.required_confluence is RequiredConfluenceLevel.LOCAL_FINITE else value.global_status
    established = actual in (LocalFiniteStatus.CONFLUENT, GlobalDeclaredFiniteStatus.CONFLUENT)
    refuted = actual in (LocalFiniteStatus.REFUTED, GlobalDeclaredFiniteStatus.REFUTED)
    status = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE if established else ScopedFormationStatus.REFUTED if refuted else ScopedFormationStatus.OPEN
    result = _row("c2-confluence", scope.c2_catalog.catalog_digest, status, value.aggregate_digest, "" if established else f"c2-{actual.value}")
    logger.debug("_c2_row exit status=%s", status.value)
    return result

def _a2_row(requirement: FormationRefinementRequirement):
    """Freshly replay exact raw A2 and require every declared field."""
    logger.debug("_a2_row entry id=%s", requirement.requirement_id)
    raw = observer_morphism_judgment(
        requirement.a2_doctrine, requirement.a2_observer_source,
        requirement.morphism.morphism_id, requirement.fine_observer_id,
        requirement.coarse_observer_id, requirement.morphism.projection,
    )
    translation = raw.translation
    members = {x.observer_id: x for x in requirement.a2_doctrine.observers}
    fine_kind = members[requirement.fine_observer_id].response_kind
    coarse_kind = members[requirement.coarse_observer_id].response_kind
    translation_exact = (
        translation is not None
        and translation.translation_id == requirement.morphism.morphism_id
        and translation.doctrine_fingerprint == requirement.a2_doctrine.fingerprint
        and translation.source_binding_digest == requirement.a2_observer_source.membership_digest
        and translation.fine_observer_id == requirement.fine_observer_id
        and translation.coarse_observer_id == requirement.coarse_observer_id
        and translation.projection == requirement.morphism.projection
        and type(translation.fine_kind) is type(fine_kind)
        and translation.fine_kind == fine_kind
        and type(translation.coarse_kind) is type(coarse_kind)
        and translation.coarse_kind == coarse_kind
    )
    strong = (
        raw.status is MorphismStatus.STRONG
        and raw.information_factorizes_on_comparison
        and raw.coarse_domain_in_fine_domain and raw.witness_checked
        and translation_exact
    )
    value = observer_relation_judgment(
        requirement.a2_doctrine, requirement.a2_observer_source,
        requirement.a2_stage_source, requirement.relation_scope,
        requirement.morphism, None, requirement.relation_policy,
    )
    if type(value) is RelationResourceLimit:
        logger.error("_a2_row nested resource refusal")
        raise RuntimeError("nested A2 refusal after admitted outer preflight")
    if type(value) is not ObserverRelationJudgment:
        logger.error("_a2_row unexpected result variant")
        raise RuntimeError("unexpected A2 result variant")
    passed = (
        strong
        and
        value.classification is requirement.required_class
        and value.preservation is requirement.required_preservation
        and value.reflection is requirement.required_reflection
        and value.domain_equality is requirement.required_domain_equality
        and value.forward.morphism_status is requirement.required_translation
        and value.forward.proposal_status is ProposalStatus.COMMUTES_ON_SCOPE
        and all(
            x.status is ProposalStatus.COMMUTES_ON_SCOPE
            for x in value.forward.triangles
        )
        and value.information_loss is requirement.required_loss
        and value.classification in (RelationClass.STRICT_REFINEMENT_ON_SCOPE, RelationClass.EQUIVALENT_ON_SCOPE)
    )
    if passed:
        status, obstruction = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, ""
    elif raw.status is MorphismStatus.INFORMATION_ONLY:
        status, obstruction = ScopedFormationStatus.OPEN, "p1a-morphism-not-strong"
    elif value.classification is RelationClass.OPEN or any(x.value == "open" for x in (value.preservation, value.reflection, value.domain_equality)):
        status, obstruction = ScopedFormationStatus.OPEN, "a2-evidence-open"
    else:
        status, obstruction = ScopedFormationStatus.REFUTED, "a2-required-relation-mismatch"
    p1a_digest = digest("c4.p1a-strong-replay", raw, None if translation is None else translation.translation_digest)
    evidence = digest("c4.a2-joint", requirement.joint_square_digest, p1a_digest, value.judgment_digest)
    row = _row("a2-refinement", requirement.requirement_id, status, evidence, obstruction)
    logger.debug("_a2_row exit status=%s", status.value)
    return value, p1a_digest, row

def _survival_row(scope: FormationScope, requirement: FormationRefinementRequirement, a2: ObserverRelationJudgment, p1a_digest: str) -> FormationComponentRow:
    """Replay direct occurrences or the complete bound translated C3 cell."""
    logger.debug("_survival_row entry id=%s", requirement.requirement_id)
    if requirement.survival_mode is SurvivalMode.DIRECT:
        observer = next(x for x in scope.doctrine.observers if x.observer_id == requirement.direct_observer_id)
        outcomes = []
        for path_id in requirement.path_ids:
            replay = replay_diagram_path(scope.doctrine, scope.diagram, path_id)
            outcomes.extend(echo(decode_observer(observer.canonical), x.representative, y.representative) for x, y in zip(replay.stages, replay.stages[1:]))
        status, obstruction = _echo_status(tuple(outcomes), "direct-survival")
        payloads = tuple(
            json.dumps(outcome_data(x), sort_keys=True, separators=(",", ":")).encode()
            for x in outcomes
        )
        evidence = digest(
            "c4.direct-survival", requirement.requirement_digest,
            requirement.joint_square_digest, a2.judgment_digest, p1a_digest,
            requirement.direct_bridge.bridge_digest, payloads,
        )
    else:
        value = translated_confluence_judgment(
            scope.doctrine, scope.diagram, requirement.translated_plan,
            requirement.a2_doctrine, requirement.a2_observer_source,
            requirement.a2_stage_source, requirement.translated_bridge,
            requirement.translated_spec, requirement.translated_policy,
        )
        if type(value) is TranslatedConfluenceResourceLimit:
            logger.error("_survival_row nested C3 resource refusal")
            raise RuntimeError("nested C3 refusal after admitted outer preflight")
        if type(value) is not TranslatedConfluenceJudgment:
            logger.error("_survival_row unexpected C3 result variant")
            raise RuntimeError("unexpected C3 result variant")
        same_replay = value.a2_result_digest == a2.judgment_digest
        status = _confluence_status(value.status) if same_replay else ScopedFormationStatus.REFUTED
        obstruction = "" if status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE else (
            "translated-a2-replay-mismatch" if not same_replay
            else "translated-survival-not-established"
        )
        evidence = digest(
            "c4.translated-survival", requirement.joint_square_digest,
            a2.judgment_digest, p1a_digest, value.judgment_digest,
        )
    result = _row("survival", requirement.requirement_id, status, evidence, obstruction)
    logger.debug("_survival_row exit status=%s", status.value)
    return result

def _echo_status(outcomes: tuple[object, ...], lane: str) -> tuple[ScopedFormationStatus, str]:
    """Apply REFUTED-over-OPEN precedence to exact echo outcomes."""
    logger.debug("_echo_status entry lane=%s", lane)
    if any(type(x) is Mismatch for x in outcomes):
        result = ScopedFormationStatus.REFUTED, f"{lane}-mismatch"
    elif any(type(x) is DomainBlocked for x in outcomes):
        result = ScopedFormationStatus.OPEN, f"{lane}-domain-blocked"
    elif all(type(x) is Echo for x in outcomes):
        result = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, ""
    else:
        logger.error("_echo_status unexpected outcome lane=%s", lane)
        raise RuntimeError("unexpected echo outcome")
    logger.debug("_echo_status exit status=%s", result[0].value)
    return result

def _confluence_status(value: ConfluenceStatus) -> ScopedFormationStatus:
    """Map the exact C3 three-valued result without promotion."""
    logger.debug("_confluence_status entry")
    result = {
        ConfluenceStatus.ESTABLISHED: ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE,
        ConfluenceStatus.REFUTED: ScopedFormationStatus.REFUTED,
        ConfluenceStatus.OPEN: ScopedFormationStatus.OPEN,
    }[value]
    logger.debug("_confluence_status exit status=%s", result.value)
    return result
