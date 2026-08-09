"""Construction and joint-square validation of refinement survival."""

from __future__ import annotations

from dataclasses import replace
import logging

from ...confluence import direct_echo_transport
from ...confluence.plan import snapshot_fork_join_plan
from ...confluence.translated.bridge import snapshot_response_bridge
from ...confluence.translated.transport import (
    snapshot_translated_policy, snapshot_translated_spec,
)
from ...confluence.translated.types import (
    ObserverProgramBridgeRow, P0P1AResponseBridgeSource,
    TranslatedEchoTransportSpec, TranslationDirection,
)
from ...confluence.types import ForkJoinPlan
from ...observer.morphism import ObserverSourceBinding
from ...observer.relations.preflight import snapshot_policy as snapshot_relation_policy
from ...observer.relations.request import (
    snapshot_scope as snapshot_relation_scope, snapshot_stage_source,
)
from ...observer.relations.translation import snapshot_translation_input
from ...observer.relations.types import (
    ComparisonMode, LawStatus, LossStatus, MorphismEvidenceStatus,
    MorphismReplaySpec, RelationClass,
)
from ...ontology.doctrine import snapshot_observer_doctrine
from .codec import (
    ScopedFormationValidationError, digest, exact_tuple, hex_digest, identifier,
    unique,
)
from .observers import require_observer_on_path
from .types import FormationRefinementRequirement, SurvivalMode

logger = logging.getLogger(__name__)


# Requirement construction

logger = logging.getLogger(__name__)

def formation_refinement_requirement(
    requirement_id: str, a2_doctrine, a2_observer_source: ObserverSourceBinding,
    a2_stage_source, relation_scope, morphism: MorphismReplaySpec, *,
    required_class: RelationClass, required_preservation: LawStatus,
    required_reflection: LawStatus, required_domain_equality: LawStatus,
    required_loss: LossStatus, path_ids: tuple[str, ...],
    required_translation: MorphismEvidenceStatus = MorphismEvidenceStatus.P1A_ESTABLISHED,
    survival_mode: SurvivalMode, direct_observer_id: str | None = None,
    direct_bridge: P0P1AResponseBridgeSource | None = None,
    translated_plan=None, translated_bridge=None, translated_spec=None,
    translated_policy=None, relation_policy=None,
) -> FormationRefinementRequirement:
    """Bind raw A2 replay and one exact direct or translated survival demand."""
    logger.debug("formation_refinement_requirement entry")
    rid = identifier(requirement_id, "refinement-id")
    if required_class not in (RelationClass.STRICT_REFINEMENT_ON_SCOPE, RelationClass.EQUIVALENT_ON_SCOPE):
        logger.error("formation_refinement_requirement nongenuine class")
        raise ScopedFormationValidationError("nongenuine-refinement-class")
    if any(type(x) is not LawStatus for x in (required_preservation, required_reflection, required_domain_equality)):
        logger.error("formation_refinement_requirement law type rejected")
        raise ScopedFormationValidationError("invalid-refinement-law-status")
    if type(required_loss) is not LossStatus or type(survival_mode) is not SurvivalMode:
        logger.error("formation_refinement_requirement loss/mode rejected")
        raise ScopedFormationValidationError("invalid-refinement-loss-or-mode")
    if required_translation is not MorphismEvidenceStatus.P1A_ESTABLISHED:
        logger.error("formation_refinement_requirement translation status rejected")
        raise ScopedFormationValidationError("refinement-requires-p1a-established-translation")
    doctrine = snapshot_observer_doctrine(a2_doctrine)
    source = snapshot_stage_source(a2_stage_source, doctrine, a2_observer_source)
    scope = snapshot_relation_scope(relation_scope, doctrine, a2_observer_source, source)
    morphism = snapshot_translation_input(
        morphism, scope.fine_observer_id, scope.coarse_observer_id,
        doctrine, a2_observer_source,
    )
    if type(morphism) is not MorphismReplaySpec or scope.mode is not ComparisonMode.WITH_P1A_REPLAY:
        logger.error("formation_refinement_requirement raw morphism rejected")
        raise ScopedFormationValidationError("refinement-requires-raw-p1a-morphism")
    paths = tuple(identifier(x, "refinement-path-id") for x in exact_tuple(path_ids, "refinement-paths", 1, 64))
    unique(paths, "refinement-paths")
    policy = snapshot_relation_policy(relation_policy)
    direct = None
    direct_row_digest = None
    if survival_mode is SurvivalMode.DIRECT:
        direct = identifier(direct_observer_id, "direct-survival-observer")
        if type(direct_bridge) is not P0P1AResponseBridgeSource:
            logger.error("formation_refinement_requirement direct bridge missing")
            raise ScopedFormationValidationError("direct-survival-bridge-required")
        hex_digest(direct_bridge.bridge_digest, "direct-bridge-digest")
        if any(x is not None for x in (translated_plan, translated_bridge, translated_spec, translated_policy)):
            logger.error("formation_refinement_requirement direct fields crossed")
            raise ScopedFormationValidationError("direct-survival-translated-fields")
        rows = exact_tuple(direct_bridge.observer_rows, "direct-bridge-observer-rows", 1, 64)
        matches = tuple(
            x for x in rows if type(x) is ObserverProgramBridgeRow
            and x.diagram_observer_id == direct
            and x.p1a_observer_id == scope.coarse_observer_id
        )
        if len(matches) != 1:
            logger.error("formation_refinement_requirement direct bridge pair mismatch")
            raise ScopedFormationValidationError("direct-refinement-bridge-pair-mismatch")
        direct_row_digest = hex_digest(matches[0].row_digest, "direct-bridge-row-digest")
    else:
        if direct_observer_id is not None or direct_bridge is not None or any(x is None for x in (translated_plan, translated_bridge, translated_spec, translated_policy)):
            logger.error("formation_refinement_requirement translated fields incomplete")
            raise ScopedFormationValidationError("translated-survival-fields")
        if (
            type(translated_plan) is not ForkJoinPlan
            or type(translated_bridge) is not P0P1AResponseBridgeSource
            or type(translated_spec) is not TranslatedEchoTransportSpec
        ):
            logger.error("formation_refinement_requirement translated field types rejected")
            raise ScopedFormationValidationError("translated-survival-field-types")
        hex_digest(translated_plan.plan_digest, "translated-plan-digest")
        hex_digest(translated_bridge.bridge_digest, "translated-bridge-digest")
        hex_digest(translated_spec.spec_digest, "translated-spec-digest")
        translated_policy = snapshot_translated_policy(translated_policy)
    joint = digest(
        "c4.refinement.joint-square", doctrine.fingerprint, source.source_digest,
        scope.scope_digest, morphism, scope.fine_observer_id, scope.coarse_observer_id,
        required_class, required_preservation, required_reflection,
        required_domain_equality, required_translation, required_loss, paths,
        survival_mode, direct, None if direct_bridge is None else direct_bridge.bridge_digest,
        direct_row_digest,
        None if translated_bridge is None else translated_bridge.bridge_digest,
        None if translated_spec is None else translated_spec.spec_digest,
        None if translated_plan is None else translated_plan.plan_digest,
        None if translated_policy is None else translated_policy.policy_digest,
        policy.policy_digest,
    )
    provisional = FormationRefinementRequirement(
        rid, doctrine, a2_observer_source, source, scope, morphism,
        scope.fine_observer_id, scope.coarse_observer_id, required_class,
        required_preservation, required_reflection, required_domain_equality,
        required_translation, required_loss, paths, survival_mode, direct,
        direct_bridge, translated_plan, translated_bridge, translated_spec,
        translated_policy, policy, joint, "",
    )
    result = replace(provisional, requirement_digest=digest("c4.refinement", provisional))
    logger.debug("formation_refinement_requirement exit mode=%s", survival_mode.value)
    return result


# Survival binding

logger = logging.getLogger(__name__)

def validate_refinement_binding(requirement: FormationRefinementRequirement, p0_doctrine, diagram) -> None:
    """Require one exact P0/P1-A bridge or one jointly bound C3 square."""
    logger.debug("validate_refinement_binding entry id=%s", requirement.requirement_id)
    if requirement.survival_mode is SurvivalMode.DIRECT:
        bridge = snapshot_response_bridge(
            p0_doctrine, diagram, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            requirement.direct_bridge,
        )
        pairs = tuple(
            x for x in bridge.observer_rows
            if x.diagram_observer_id == requirement.direct_observer_id
            and x.p1a_observer_id == requirement.coarse_observer_id
        )
        if len(pairs) != 1:
            logger.error("direct refinement bridge pair is not exact id=%s", requirement.requirement_id)
            raise ScopedFormationValidationError("direct-refinement-bridge-pair-mismatch")
        for path_id in requirement.path_ids:
            require_observer_on_path(
                p0_doctrine, diagram, path_id,
                requirement.direct_observer_id, "direct-survival",
            )
    else:
        bridge = snapshot_response_bridge(
            p0_doctrine, diagram, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            requirement.translated_bridge,
        )
        spec = requirement.translated_spec
        placeholder = direct_echo_transport(
            p0_doctrine,
            (spec.diagram_fine_observer_id, spec.diagram_coarse_observer_id),
        )
        plan = snapshot_fork_join_plan(
            requirement.translated_plan, diagram, placeholder, p0_doctrine,
        )
        checked = snapshot_translated_spec(
            p0_doctrine, diagram, plan, requirement.a2_doctrine,
            requirement.a2_observer_source, requirement.a2_stage_source,
            bridge, spec,
        )
        exact = (
            checked.p1a_fine_observer_id == requirement.fine_observer_id
            and checked.p1a_coarse_observer_id == requirement.coarse_observer_id
            and checked.morphism == requirement.morphism
            and checked.relation_scope == requirement.relation_scope
            and checked.relation_policy == requirement.relation_policy
            and checked.required_class is requirement.required_class
            and checked.required_preservation is requirement.required_preservation
            and checked.required_domain_equality is requirement.required_domain_equality
            and checked.required_loss is requirement.required_loss
            and checked.bridge_digest == bridge.bridge_digest
            and checked.plan_digest == plan.plan_digest
        )
        if not exact:
            logger.error("translated refinement joint square mismatch id=%s", requirement.requirement_id)
            raise ScopedFormationValidationError("translated-refinement-joint-square-mismatch")
        fine_slots = {0, 2} if checked.direction is TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE else {1, 3}
        for index, path_id in enumerate(requirement.path_ids):
            observer_id = (
                checked.diagram_fine_observer_id if index in fine_slots
                else checked.diagram_coarse_observer_id
            )
            require_observer_on_path(
                p0_doctrine, diagram, path_id, observer_id,
                "translated-survival",
            )
    logger.debug("validate_refinement_binding exit id=%s", requirement.requirement_id)

