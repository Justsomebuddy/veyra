"""P1-C4 genuine refinement and complete scope constructors."""

from __future__ import annotations

from dataclasses import replace
import logging

from .confluence_aggregate_catalog_validation import snapshot_finite_confluence_catalog
from .confluence_validation import snapshot_finite_diagram_source
from .construction.finite_builder.validation import _snapshot_source, _snapshot_target_stage
from .positive_ontology_doctrine import snapshot_observer_doctrine, stage_commitment
from .scoped_formation_codec import (
    ScopedFormationValidationError, canonical_bytes, digest, exact_tuple,
    hex_digest, identifier, unique,
)
from .scoped_formation_observers import require_observer_on_path
from .scoped_formation_refinement_binding import validate_refinement_binding
from .scoped_formation_refinement_source import formation_refinement_requirement
from .scoped_formation_sources import (
    bound_g4_bridge_source, formation_policy, g4_bridge_mappings,
    snapshot_policy, snapshot_rule_source,
)
from .scoped_formation_types import (
    BoundG4BridgeSource, FiniteScopedFormationRuleSource,
    FormationPersistenceRequirement, FormationPolicy,
    FormationRefinementRequirement, FormationScope, RequiredConfluenceLevel,
    SurvivalMode,
)

logger = logging.getLogger(__name__)


def formation_scope(
    rule_source: FiniteScopedFormationRuleSource, scope_id: str,
    presentation_id: str, doctrine, construction_source, target, diagram,
    c2_catalog, required_confluence: RequiredConfluenceLevel,
    support_observer_ids: tuple[str, ...],
    persistence: tuple[FormationPersistenceRequirement, ...],
    g4_bridge: BoundG4BridgeSource,
    refinements: tuple[FormationRefinementRequirement, ...],
    policy: FormationPolicy | None = None,
) -> FormationScope:
    """Construct the exact nonempty raw SFP formation scope."""
    logger.debug("formation_scope entry")
    doctrine = snapshot_observer_doctrine(doctrine)
    rule = snapshot_rule_source(rule_source, doctrine)
    sid, pid = identifier(scope_id, "formation-scope-id"), identifier(presentation_id, "presentation-id")
    if sid == pid:
        logger.error("formation_scope id collision")
        raise ScopedFormationValidationError("formation-scope-presentation-id-collision")
    source = _snapshot_source(construction_source, doctrine)
    target = _snapshot_target_stage(target, doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    matching = tuple(x for x in diagram.stages if x.stage_id == target.stage_id)
    if len(matching) != 1 or stage_commitment(matching[0]) != stage_commitment(target):
        logger.error("formation_scope target is not exact diagram member")
        raise ScopedFormationValidationError("formation-target-not-exact-diagram-stage")
    target = _snapshot_target_stage(matching[0], doctrine)
    catalog = snapshot_finite_confluence_catalog(c2_catalog, doctrine, diagram)
    if type(required_confluence) is not RequiredConfluenceLevel:
        logger.error("formation_scope confluence level rejected")
        raise ScopedFormationValidationError("invalid-required-confluence-level")
    support = tuple(identifier(x, "support-observer-id") for x in exact_tuple(support_observer_ids, "support-observers", 1, 64))
    unique(support, "support-observers")
    observer_ids = {x.observer_id for x in doctrine.observers}
    if any(x not in observer_ids for x in support):
        logger.error("formation_scope support observer unadmitted")
        raise ScopedFormationValidationError("support-observer-not-admitted")
    persistence = _snapshot_persistence(persistence, doctrine, diagram, observer_ids)
    bridge = bound_g4_bridge_source(
        g4_bridge.atlas, doctrine, diagram,
        g4_bridge_mappings(g4_bridge.stage_map, g4_bridge.patch_requirements),
    )
    if bridge != g4_bridge:
        logger.error("formation_scope G4 bridge drift")
        raise ScopedFormationValidationError("g4-bridge-drift")
    refinements = tuple(_snapshot_refinement(x, doctrine, diagram) for x in exact_tuple(refinements, "refinements", 1, 64))
    unique(tuple(x.requirement_id for x in refinements), "refinement-ids")
    selected_policy = formation_policy() if policy is None else snapshot_policy(policy)
    provisional = FormationScope(
        "p1-c4-scope-v1", sid, pid, doctrine, rule.source_digest, source, target,
        target.stage_id, stage_commitment(target), diagram, catalog,
        required_confluence, support, persistence, bridge, refinements,
        selected_policy, "",
    )
    result = replace(provisional, scope_digest=digest("c4.scope", provisional))
    if len(canonical_bytes(result)) > 4 * 1024 * 1024:
        logger.error("formation_scope hard byte limit")
        raise ScopedFormationValidationError("formation-hard-byte-limit")
    logger.debug("formation_scope exit refinements=%d", len(refinements))
    return result


def snapshot_formation_scope(rule_source, value) -> FormationScope:
    """Rebuild a raw scope without trusting its digest or nested equality."""
    logger.debug("snapshot_formation_scope entry")
    if type(value) is not FormationScope:
        logger.error("snapshot_formation_scope exact type rejected")
        raise ScopedFormationValidationError("formation-scope-must-be-exact")
    try:
        if value.version != "p1-c4-scope-v1":
            logger.error("snapshot_formation_scope version drift")
            raise ScopedFormationValidationError("formation-scope-version-drift")
        identifier(value.scope_id, "formation-scope-id")
        identifier(value.presentation_id, "presentation-id")
        identifier(value.expected_target_stage_id, "expected-target-stage-id")
        for supplied in (
            value.rule_source_digest, value.expected_target_commitment,
            value.scope_digest,
        ):
            hex_digest(supplied, "formation-scope-digest")
        if type(value.support_observer_ids) is not tuple or len(value.support_observer_ids) > 64:
            logger.error("snapshot_formation_scope support container drift")
            raise ScopedFormationValidationError("formation-support-container-drift")
        if type(value.persistence) is not tuple or len(value.persistence) > 128:
            logger.error("snapshot_formation_scope persistence container drift")
            raise ScopedFormationValidationError("formation-persistence-container-drift")
        if type(value.refinements) is not tuple or len(value.refinements) > 64:
            logger.error("snapshot_formation_scope refinement container drift")
            raise ScopedFormationValidationError("formation-refinement-container-drift")
    except AttributeError as exc:
        logger.error("snapshot_formation_scope missing fields")
        raise ScopedFormationValidationError("formation-scope-missing-fields") from exc
    expected = formation_scope(
        rule_source, value.scope_id, value.presentation_id, value.doctrine,
        value.construction_source, value.target, value.diagram, value.c2_catalog,
        value.required_confluence, value.support_observer_ids, value.persistence,
        value.g4_bridge, value.refinements, value.policy,
    )
    if value != expected:
        logger.error("snapshot_formation_scope drift")
        raise ScopedFormationValidationError("formation-scope-drift")
    logger.debug("snapshot_formation_scope exit")
    return expected


def _snapshot_persistence(value, doctrine, diagram, observers: set[str]) -> tuple[FormationPersistenceRequirement, ...]:
    """Validate the exact nonempty ordered persistence catalog."""
    logger.debug("_snapshot_persistence entry")
    paths = {x.path_id for x in diagram.paths}
    rows = exact_tuple(value, "persistence", 1, 128)
    out = []
    for row in rows:
        if type(row) is not FormationPersistenceRequirement:
            logger.error("_snapshot_persistence row type rejected")
            raise ScopedFormationValidationError("persistence-row-must-be-exact")
        observer, path = identifier(row.observer_id, "observer-id"), identifier(row.path_id, "path-id")
        expected = digest("c4.persistence", observer, path)
        if observer not in observers or path not in paths or row.requirement_digest != expected:
            logger.error("_snapshot_persistence row drift")
            raise ScopedFormationValidationError("persistence-row-drift")
        require_observer_on_path(doctrine, diagram, path, observer, "persistence")
        out.append(FormationPersistenceRequirement(observer, path, expected))
    unique(tuple(f"{x.observer_id}\0{x.path_id}" for x in out), "persistence-keys")
    result = tuple(out)
    logger.debug("_snapshot_persistence exit rows=%d", len(result))
    return result


def _snapshot_refinement(value, p0_doctrine, diagram) -> FormationRefinementRequirement:
    """Rebuild one raw refinement and enforce exact mapped formation stages."""
    logger.debug("_snapshot_refinement entry")
    if type(value) is not FormationRefinementRequirement:
        logger.error("_snapshot_refinement exact type rejected")
        raise ScopedFormationValidationError("refinement-requirement-must-be-exact")
    kwargs = dict(
        required_class=value.required_class, required_preservation=value.required_preservation,
        required_reflection=value.required_reflection, required_domain_equality=value.required_domain_equality,
        required_loss=value.required_loss, required_translation=value.required_translation,
        path_ids=value.path_ids, survival_mode=value.survival_mode,
        direct_observer_id=value.direct_observer_id, direct_bridge=value.direct_bridge,
        translated_plan=value.translated_plan,
        translated_bridge=value.translated_bridge, translated_spec=value.translated_spec,
        translated_policy=value.translated_policy, relation_policy=value.relation_policy,
    )
    expected = formation_refinement_requirement(
        value.requirement_id, value.a2_doctrine, value.a2_observer_source,
        value.a2_stage_source, value.relation_scope, value.morphism, **kwargs,
    )
    admitted = {x.observer_id for x in p0_doctrine.observers}
    validate_refinement_binding(expected, p0_doctrine, diagram)
    if expected.survival_mode is SurvivalMode.DIRECT:
        if expected.direct_observer_id not in admitted:
            logger.error("_snapshot_refinement direct observer unadmitted")
            raise ScopedFormationValidationError("direct-survival-observer-not-admitted")
    else:
        plan = expected.translated_plan
        selected = (
            plan.left_branch_path_id, plan.right_branch_path_id,
            plan.left_join_path_id, plan.right_join_path_id,
        )
        if expected.path_ids != tuple(x for x in selected if x is not None):
            logger.error("_snapshot_refinement translated path coverage mismatch")
            raise ScopedFormationValidationError(
                "translated-survival-path-coverage-not-exact"
            )
    paths = {x.path_id: x for x in diagram.paths}
    edges = {x.edge_id: x for x in diagram.edges}
    stage_ids: list[str] = []
    for path_id in expected.path_ids:
        if path_id not in paths:
            logger.error("_snapshot_refinement path missing")
            raise ScopedFormationValidationError("refinement-path-not-in-formation")
        path = paths[path_id]
        ids = [path.start_stage_id] + [edges[x].upper_stage_id for x in path.edge_ids]
        stage_ids.extend(x for x in ids if x not in stage_ids)
    relation_ids = tuple(x.stage_id for x in expected.a2_stage_source.stages)
    relation_recurrences = tuple(x.recurrence for x in expected.a2_stage_source.stages)
    diagram_recurrences = tuple(next(x for x in diagram.stages if x.stage_id == sid).representative for sid in stage_ids)
    if relation_ids != tuple(stage_ids) or relation_recurrences != diagram_recurrences:
        logger.error("_snapshot_refinement A2 stage mapping mismatch")
        raise ScopedFormationValidationError("a2-stage-source-not-exact-mapped-formation-stages")
    if expected != value:
        logger.error("_snapshot_refinement drift")
        raise ScopedFormationValidationError("refinement-requirement-drift")
    logger.debug("_snapshot_refinement exit")
    return expected
