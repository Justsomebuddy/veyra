"""Fail-closed generic doctrine/source snapshots for provisional P1-C1."""

from __future__ import annotations

import logging
from typing import NoReturn

from .digest import diagram_digest, edge_digest, path_digest
from .preflight import ConfluenceValidationError
from .types import DiagramEdge, DiagramPath, FiniteDiagramSource
from ..ontology.doctrine import snapshot_observer_doctrine, stage_commitment
from ..ontology.types import ObserverDoctrine, OntologyStage
from ..ontology.validation import (
    PositiveOntologyValidationError, snapshot_identifier, snapshot_ontology_stage,
)

logger = logging.getLogger(__name__)
MAX_DIAGRAM_STAGES = 64
MAX_DIAGRAM_EDGES = 128
MAX_DIAGRAM_PATHS = 128
MAX_PATH_EDGES = 128
DIAGRAM_VERSION = "p1-c1-v1"
DIAGRAM_SCOPE = "finite-declared-diagram-membership-not-universal-coverage"


def _reject(reason: str) -> NoReturn:
    logger.error("confluence source rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


def snapshot_confluence_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Capture one generic doctrine and normalize lower-layer errors."""
    logger.debug("snapshot_confluence_doctrine entry")
    try:
        result = snapshot_observer_doctrine(value)
    except PositiveOntologyValidationError as exc:
        logger.error("snapshot_confluence_doctrine rejected")
        raise ConfluenceValidationError("invalid-confluence-doctrine") from exc
    logger.debug("snapshot_confluence_doctrine exit observers=%d", len(result.observers))
    return result


def _identifier(value: str, field: str) -> str:
    logger.debug("_identifier entry field=%s", field)
    try:
        result = snapshot_identifier(value, field)
    except PositiveOntologyValidationError as exc:
        logger.error("_identifier rejected field=%s", field)
        raise ConfluenceValidationError(f"invalid-{field}") from exc
    logger.debug("_identifier exit field=%s", field)
    return result


def _hex_digest(value: str, field: str) -> str:
    logger.debug("_hex_digest entry field=%s", field)
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _reject(f"invalid-{field}")
    logger.debug("_hex_digest exit field=%s", field)
    return value


def snapshot_diagram_edge(value: DiagramEdge) -> DiagramEdge:
    """Capture an exact bounded edge before map construction."""
    logger.debug("snapshot_diagram_edge entry")
    if type(value) is not DiagramEdge:
        _reject("diagram-edge-must-be-exact")
    try:
        edge_id, lower, upper, raw_observers = (
            value.edge_id, value.lower_stage_id, value.upper_stage_id,
            value.preserved_observer_ids,
        )
    except AttributeError:
        _reject("diagram-edge-missing-fields")
    if type(raw_observers) is not tuple or len(raw_observers) > 64:
        _reject("invalid-edge-observers")
    observers = tuple(_identifier(item, "edge-observer-id") for item in raw_observers)
    if len(set(observers)) != len(observers):
        _reject("duplicate-edge-observer-id")
    result = DiagramEdge(
        _identifier(edge_id, "edge-id"), _identifier(lower, "lower-stage-id"),
        _identifier(upper, "upper-stage-id"), observers,
    )
    logger.debug("snapshot_diagram_edge exit observers=%d", len(observers))
    return result


def snapshot_diagram_path(value: DiagramPath) -> DiagramPath:
    """Capture a nonempty ordered path claim without resolving it yet."""
    logger.debug("snapshot_diagram_path entry")
    if type(value) is not DiagramPath:
        _reject("diagram-path-must-be-exact")
    try:
        path_id, raw_edges, start, end = (
            value.path_id, value.edge_ids, value.start_stage_id, value.end_stage_id,
        )
    except AttributeError:
        _reject("diagram-path-missing-fields")
    if type(raw_edges) is not tuple or not 1 <= len(raw_edges) <= MAX_PATH_EDGES:
        _reject("invalid-path-edges")
    edges = tuple(_identifier(item, "path-edge-id") for item in raw_edges)
    result = DiagramPath(
        _identifier(path_id, "path-id"), edges,
        _identifier(start, "path-start-stage-id"),
        _identifier(end, "path-end-stage-id"),
    )
    logger.debug("snapshot_diagram_path exit edges=%d", len(edges))
    return result


def _snapshot_stage(value: OntologyStage) -> OntologyStage:
    logger.debug("_snapshot_stage entry")
    try:
        result = snapshot_ontology_stage(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_snapshot_stage rejected")
        raise ConfluenceValidationError("invalid-diagram-stage") from exc
    logger.debug("_snapshot_stage exit observers=%d", len(result.observers))
    return result


def reconstruct_path(
    source_id: str, doctrine_fingerprint: str, path: DiagramPath,
    edge_map: dict[str, DiagramEdge], stage_map: dict[str, OntologyStage],
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Reconstruct exact ordered stage occurrences and history commitment."""
    logger.debug("reconstruct_path entry edges=%d", len(path.edge_ids))
    resolved: list[DiagramEdge] = []
    for edge_id in path.edge_ids:
        edge = edge_map.get(edge_id)
        if edge is None:
            _reject("unknown-path-edge")
        resolved.append(edge)
    for left, right in zip(resolved, resolved[1:]):
        if left.upper_stage_id != right.lower_stage_id:
            _reject("noncomposable-diagram-path")
    if resolved[0].lower_stage_id != path.start_stage_id or resolved[-1].upper_stage_id != path.end_stage_id:
        _reject("path-endpoint-drift")
    stage_ids = (resolved[0].lower_stage_id, *(edge.upper_stage_id for edge in resolved))
    commitments = tuple(stage_commitment(stage_map[item]) for item in stage_ids)
    digest = path_digest(source_id, doctrine_fingerprint, path.path_id, path.edge_ids, commitments)
    logger.debug("reconstruct_path exit stages=%d", len(stage_ids))
    return stage_ids, commitments, digest


def _capture_source_parts(
    doctrine: ObserverDoctrine, source_id: str, raw_stages: tuple[OntologyStage, ...],
    raw_edges: tuple[DiagramEdge, ...], raw_paths: tuple[DiagramPath, ...],
) -> tuple[tuple[OntologyStage, ...], tuple[str, ...], tuple[DiagramEdge, ...], tuple[DiagramPath, ...], tuple[str, ...], str]:
    logger.debug("_capture_source_parts entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    source_id = _identifier(source_id, "diagram-source-id")
    if type(raw_stages) is not tuple or not 1 <= len(raw_stages) <= MAX_DIAGRAM_STAGES:
        _reject("invalid-diagram-stages")
    if type(raw_edges) is not tuple or not 1 <= len(raw_edges) <= MAX_DIAGRAM_EDGES:
        _reject("invalid-diagram-edges")
    if type(raw_paths) is not tuple or not 1 <= len(raw_paths) <= MAX_DIAGRAM_PATHS:
        _reject("invalid-diagram-paths")
    stages = tuple(_snapshot_stage(item) for item in raw_stages)
    edges = tuple(snapshot_diagram_edge(item) for item in raw_edges)
    paths = tuple(snapshot_diagram_path(item) for item in raw_paths)
    stage_map = {item.stage_id: item for item in stages}
    edge_map = {item.edge_id: item for item in edges}
    if len(stage_map) != len(stages):
        _reject("duplicate-stage-id")
    if len(edge_map) != len(edges):
        _reject("duplicate-edge-id")
    path_ids = tuple(item.path_id for item in paths)
    if len(set(path_ids)) != len(path_ids):
        _reject("duplicate-path-id")
    sequences = tuple(item.edge_ids for item in paths)
    if len(set(sequences)) != len(sequences):
        _reject("duplicate-path-history")
    doctrine_ids = tuple(item.observer_id for item in doctrine.observers)
    doctrine_map = {item.observer_id: item for item in doctrine.observers}
    for stage in stages:
        ids = tuple(item.observer_id for item in stage.observers)
        if stage.doctrine_id != doctrine.doctrine_id or ids != doctrine_ids[:len(ids)]:
            _reject("stage-doctrine-prefix-drift")
        for observer in stage.observers:
            admitted = doctrine_map[observer.observer_id]
            if observer.canonical != admitted.canonical or observer.response_kind != admitted.response_kind:
                _reject("stage-doctrine-observer-drift")
    for edge in edges:
        if edge.lower_stage_id not in stage_map or edge.upper_stage_id not in stage_map:
            _reject("unknown-edge-stage")
        lower = {item.observer_id: item for item in stage_map[edge.lower_stage_id].observers}
        upper = {item.observer_id: item for item in stage_map[edge.upper_stage_id].observers}
        if any(item not in lower or item not in upper for item in edge.preserved_observer_ids):
            _reject("edge-observer-not-on-both-endpoints")
    path_commitments = tuple(
        reconstruct_path(source_id, doctrine.fingerprint, path, edge_map, stage_map)[2]
        for path in paths
    )
    stage_commitments = tuple(stage_commitment(item) for item in stages)
    edge_commitments = tuple(edge_digest(doctrine.fingerprint, item) for item in edges)
    digest = diagram_digest(
        DIAGRAM_VERSION, DIAGRAM_SCOPE, source_id, doctrine.fingerprint,
        stage_commitments, edge_commitments, path_commitments,
    )
    logger.debug("_capture_source_parts exit stages=%d edges=%d paths=%d", len(stages), len(edges), len(paths))
    return stages, stage_commitments, edges, paths, path_commitments, digest


def build_finite_diagram_source(
    doctrine: ObserverDoctrine, source_id: str, stages: tuple[OntologyStage, ...],
    edges: tuple[DiagramEdge, ...], paths: tuple[DiagramPath, ...],
) -> FiniteDiagramSource:
    """Construct an exact digest-bound source from raw generic rows."""
    logger.debug("build_finite_diagram_source entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    parts = _capture_source_parts(doctrine, source_id, stages, edges, paths)
    result = FiniteDiagramSource(source_id, doctrine.fingerprint, *parts)
    logger.debug("build_finite_diagram_source exit")
    return result


def snapshot_finite_diagram_source(
    value: FiniteDiagramSource, doctrine: ObserverDoctrine,
) -> FiniteDiagramSource:
    """Deep-rebuild and recompute every source and history commitment."""
    logger.debug("snapshot_finite_diagram_source entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    if type(value) is not FiniteDiagramSource:
        _reject("finite-diagram-source-must-be-exact")
    try:
        source_id, fingerprint = value.source_id, value.doctrine_fingerprint
        stages, supplied_stages = value.stages, value.stage_commitments
        edges, paths = value.edges, value.paths
        supplied_paths, supplied_digest = value.path_commitments, value.source_digest
        version, scope = value.version, value.scope
    except AttributeError:
        _reject("finite-diagram-source-missing-fields")
    parts = _capture_source_parts(doctrine, source_id, stages, edges, paths)
    if type(supplied_stages) is not tuple or type(supplied_paths) is not tuple:
        _reject("finite-diagram-source-drift")
    captured_stages = tuple(
        _hex_digest(item, "stage-commitment") for item in supplied_stages
    )
    captured_paths = tuple(
        _hex_digest(item, "path-commitment") for item in supplied_paths
    )
    fingerprint = _hex_digest(fingerprint, "doctrine-fingerprint")
    supplied_digest = _hex_digest(supplied_digest, "diagram-digest")
    if (
        type(version) is not str or type(scope) is not str
        or fingerprint != doctrine.fingerprint or captured_stages != parts[1]
        or captured_paths != parts[4] or supplied_digest != parts[5]
        or version != DIAGRAM_VERSION or scope != DIAGRAM_SCOPE
    ):
        _reject("finite-diagram-source-drift")
    result = FiniteDiagramSource(source_id, doctrine.fingerprint, *parts)
    logger.debug("snapshot_finite_diagram_source exit")
    return result
