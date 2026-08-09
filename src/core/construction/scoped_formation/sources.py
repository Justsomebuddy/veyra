"""Exact raw-source constructors and snapshots for P1-C4."""

from __future__ import annotations

from dataclasses import replace
import logging

from ...confluence.validation import snapshot_finite_diagram_source
from ...observer.patch_atlas import validate_atlas_shape
from ...ontology.doctrine import snapshot_observer_doctrine, stage_commitment
from .codec import (
    ScopedFormationValidationError, bounded_int, digest, exact_tuple, hex_digest, identifier,
    unique,
)
from .observers import require_observer_at_stage, require_observer_on_path
from .types import (
    BoundG4BridgeSource, BoundPatchRequirement, FiniteScopedFormationRuleSource,
    FormationPersistenceRequirement, FormationPolicy,
    G4BridgeMappings,
    StageMapRow,
)

logger = logging.getLogger(__name__)

RULE_VERSION = "p1-c4-sfp-rule-v1"
RULE_ID = "FiniteScopedFormationPrinciple"
TRUST_LEDGER_ID = "veyra-kernel-ledger-v1"
SCHEMAS = ("p1-b-v1", "g4-response-derived-v1", "p1-c2-v1", "p1-c3-v1", "p1-a2-v1")
COMPONENT_ORDER = (
    "construction", "target-membership", "support", "g4", "persistence",
    "c2-confluence", "a2-refinement", "survival",
)
STATEMENT = (
    "constructed-target+nonempty-ready-support+response-derived-g4+"
    "nonempty-persistence+demanded-c2+genuine-a2-survival=>finite-scoped-presentation"
)


def formation_policy(*, max_checks: int = 4096, max_bytes: int = 4 * 1024 * 1024) -> FormationPolicy:
    """Construct one exact outer C4 resource policy."""
    logger.debug("formation_policy entry")
    max_checks = bounded_int(max_checks, "formation-policy-checks", 1, 4096)
    max_bytes = bounded_int(max_bytes, "formation-policy-bytes", 1, 4 * 1024 * 1024)
    version = "p1-c4-policy-v1"
    result = FormationPolicy(version, max_checks, max_bytes, digest("c4.policy", version, max_checks, max_bytes))
    logger.debug("formation_policy exit")
    return result


def finite_scoped_formation_rule_source(doctrine, trust_ledger_id: str = TRUST_LEDGER_ID) -> FiniteScopedFormationRuleSource:
    """Return the sole allowlisted, doctrine-bound, nonrecursive SFP rule."""
    logger.debug("finite_scoped_formation_rule_source entry")
    doctrine = snapshot_observer_doctrine(doctrine)
    trust = identifier(trust_ledger_id, "trust-ledger-id")
    if trust != TRUST_LEDGER_ID:
        logger.error("finite_scoped_formation_rule_source ledger rejected")
        raise ScopedFormationValidationError("formation-rule-ledger-not-allowlisted")
    statement = digest("c4.rule.statement", STATEMENT)
    source = FiniteScopedFormationRuleSource(
        RULE_VERSION, doctrine.fingerprint, RULE_ID, SCHEMAS, COMPONENT_ORDER,
        statement, trust, "",
    )
    result = replace(source, source_digest=digest("c4.rule.source", source))
    logger.debug("finite_scoped_formation_rule_source exit")
    return result


def stage_map_row(node_id: str, stage_id: str, commitment: str) -> StageMapRow:
    """Bind one atlas node to one exact diagram stage key."""
    logger.debug("stage_map_row entry")
    node, stage = identifier(node_id, "atlas-node-id"), identifier(stage_id, "stage-id")
    commitment = hex_digest(commitment, "stage-commitment")
    result = StageMapRow(node, stage, commitment, digest("c4.g4.stage-map", node, stage, commitment))
    logger.debug("stage_map_row exit")
    return result


def bound_patch_requirement(patch_id: str, path_ids: tuple[str, ...], observer_ids: tuple[str, ...], expected_nodes: tuple[str, ...]) -> BoundPatchRequirement:
    """Bind exact histories and observers to every node of one atlas patch."""
    logger.debug("bound_patch_requirement entry")
    patch = identifier(patch_id, "patch-id")
    paths = tuple(identifier(x, "path-id") for x in exact_tuple(path_ids, "patch-paths", 1, 64))
    observers = tuple(identifier(x, "observer-id") for x in exact_tuple(observer_ids, "patch-observers", 1, 64))
    nodes = tuple(identifier(x, "atlas-node-id") for x in exact_tuple(expected_nodes, "patch-nodes", 1, 128))
    unique(paths, "patch-paths")
    unique(observers, "patch-observers")
    unique(nodes, "patch-nodes")
    result = BoundPatchRequirement(patch, paths, observers, nodes, digest("c4.g4.patch", patch, paths, observers, nodes))
    logger.debug("bound_patch_requirement exit")
    return result


def g4_bridge_mappings(stage_map: tuple[StageMapRow, ...], patch_requirements: tuple[BoundPatchRequirement, ...]) -> G4BridgeMappings:
    """Package the two exact G4 bridge catalogs without derived evidence."""
    logger.debug("g4_bridge_mappings entry")
    result = G4BridgeMappings(
        tuple(_stage_map_row(x) for x in exact_tuple(stage_map, "stage-map", 1, 128)),
        tuple(_patch_requirement(x) for x in exact_tuple(patch_requirements, "patch-requirements", 1, 128)),
    )
    logger.debug("g4_bridge_mappings exit")
    return result


def bound_g4_bridge_source(raw_atlas_inputs, raw_doctrine, raw_diagram, mappings: G4BridgeMappings) -> BoundG4BridgeSource:
    """Bind raw atlas membership and total diagram mappings, never a G4 result."""
    logger.debug("bound_g4_bridge_source entry")
    doctrine = snapshot_observer_doctrine(raw_doctrine)
    diagram = snapshot_finite_diagram_source(raw_diagram, doctrine)
    atlas = validate_atlas_shape(raw_atlas_inputs)
    if type(mappings) is not G4BridgeMappings:
        logger.error("bound_g4_bridge_source mappings type rejected")
        raise ScopedFormationValidationError("g4-mappings-must-be-exact")
    mappings = g4_bridge_mappings(mappings.stage_map, mappings.patch_requirements)
    if tuple(x.node_id for x in mappings.stage_map) != atlas.universe:
        logger.error("bound_g4_bridge_source node map rejected")
        raise ScopedFormationValidationError("g4-node-map-not-exact-total-order")
    if tuple(x.patch_id for x in mappings.patch_requirements) != tuple(x.name for x in atlas.patches):
        logger.error("bound_g4_bridge_source patch map rejected")
        raise ScopedFormationValidationError("g4-patch-map-not-exact-total-order")
    stages = {x.stage_id: x for x in diagram.stages}
    for row in mappings.stage_map:
        if row.stage_id not in stages or stage_commitment(stages[row.stage_id]) != row.stage_commitment:
            logger.error("bound_g4_bridge_source stage transplant")
            raise ScopedFormationValidationError("g4-stage-map-transplant")
    paths = {x.path_id for x in diagram.paths}
    observers = {x.observer_id for x in doctrine.observers}
    for raw_patch, req in zip(atlas.patches, mappings.patch_requirements, strict=True):
        if req.expected_nodes != raw_patch.nodes or any(x not in paths for x in req.path_ids) or any(x not in observers for x in req.observer_ids):
            logger.error("bound_g4_bridge_source patch requirement drift")
            raise ScopedFormationValidationError("g4-patch-requirement-drift")
        for observer_id in req.observer_ids:
            for node in raw_patch.nodes:
                mapped = next(x for x in mappings.stage_map if x.node_id == node)
                require_observer_at_stage(doctrine, stages[mapped.stage_id], observer_id, "g4")
            for path_id in req.path_ids:
                require_observer_on_path(doctrine, diagram, path_id, observer_id, "g4")
    provisional = BoundG4BridgeSource(
        "p1-c4-g4-bridge-v1", doctrine.fingerprint, diagram.source_digest,
        atlas, mappings.stage_map, mappings.patch_requirements, "",
    )
    result = replace(provisional, bridge_digest=digest("c4.g4.bridge", provisional))
    logger.debug("bound_g4_bridge_source exit")
    return result


def formation_persistence_requirement(observer_id: str, path_id: str) -> FormationPersistenceRequirement:
    """Bind one exact observer to one declared formation history."""
    logger.debug("formation_persistence_requirement entry")
    observer, path = identifier(observer_id, "observer-id"), identifier(path_id, "path-id")
    result = FormationPersistenceRequirement(observer, path, digest("c4.persistence", observer, path))
    logger.debug("formation_persistence_requirement exit")
    return result


def snapshot_rule_source(value, doctrine) -> FiniteScopedFormationRuleSource:
    """Rebuild and allowlist the exact SFP rule source."""
    logger.debug("snapshot_rule_source entry")
    if type(value) is not FiniteScopedFormationRuleSource:
        logger.error("snapshot_rule_source exact type rejected")
        raise ScopedFormationValidationError("formation-rule-source-must-be-exact")
    try:
        scalar = (value.version, value.doctrine_fingerprint, value.rule_id, value.trust_ledger_id)
        schemas, order = value.accepted_schema_ids, value.component_order
        statement, supplied = value.statement_digest, value.source_digest
    except AttributeError as exc:
        logger.error("snapshot_rule_source missing fields")
        raise ScopedFormationValidationError("formation-rule-source-missing-fields") from exc
    if any(type(x) is not str or len(x.encode()) > 128 for x in scalar):
        logger.error("snapshot_rule_source scalar drift")
        raise ScopedFormationValidationError("formation-rule-source-scalar-drift")
    if (
        type(schemas) is not tuple or len(schemas) != len(SCHEMAS)
        or type(order) is not tuple or len(order) != len(COMPONENT_ORDER)
        or any(type(x) is not str or len(x.encode()) > 128 for x in (*schemas, *order))
    ):
        logger.error("snapshot_rule_source catalog drift")
        raise ScopedFormationValidationError("formation-rule-source-catalog-drift")
    hex_digest(statement, "formation-rule-statement-digest")
    hex_digest(supplied, "formation-rule-source-digest")
    expected = finite_scoped_formation_rule_source(doctrine, value.trust_ledger_id)
    if value != expected or RULE_ID in value.accepted_schema_ids:
        logger.error("snapshot_rule_source allowlist mismatch")
        raise ScopedFormationValidationError("formation-rule-not-allowlisted")
    logger.debug("snapshot_rule_source exit")
    return expected


def snapshot_policy(value: FormationPolicy) -> FormationPolicy:
    """Rebuild the exact outer formation policy."""
    logger.debug("snapshot_policy entry")
    if type(value) is not FormationPolicy:
        logger.error("snapshot_policy exact type rejected")
        raise ScopedFormationValidationError("formation-policy-must-be-exact")
    expected = formation_policy(max_checks=value.max_checks, max_bytes=value.max_bytes)
    if value != expected:
        logger.error("snapshot_policy drift")
        raise ScopedFormationValidationError("formation-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def _stage_map_row(value) -> StageMapRow:
    """Rebuild one exact stage-map row."""
    logger.debug("_stage_map_row entry")
    if type(value) is not StageMapRow:
        logger.error("_stage_map_row exact type rejected")
        raise ScopedFormationValidationError("stage-map-row-must-be-exact")
    expected = stage_map_row(value.node_id, value.stage_id, value.stage_commitment)
    if value != expected:
        logger.error("_stage_map_row drift")
        raise ScopedFormationValidationError("stage-map-row-drift")
    logger.debug("_stage_map_row exit")
    return expected


def _patch_requirement(value) -> BoundPatchRequirement:
    """Rebuild one exact patch requirement."""
    logger.debug("_patch_requirement entry")
    if type(value) is not BoundPatchRequirement:
        logger.error("_patch_requirement exact type rejected")
        raise ScopedFormationValidationError("patch-requirement-must-be-exact")
    expected = bound_patch_requirement(value.patch_id, value.path_ids, value.observer_ids, value.expected_nodes)
    if value != expected:
        logger.error("_patch_requirement drift")
        raise ScopedFormationValidationError("patch-requirement-drift")
    logger.debug("_patch_requirement exit")
    return expected
