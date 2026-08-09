"""Operational barT maps, identities, and pullback composition for P3-T."""

from __future__ import annotations

import logging

from .common import reject
from .digest import map_digest
from .types import ObserverNetworkSource, PartialMap, ResponseStatus

logger = logging.getLogger(__name__)


def ready_image(source: ObserverNetworkSource, observer_id: str) -> tuple[str, ...]:
    """Return first-occurrence-deduplicated reachable ready value digests."""
    logger.debug("ready_image entry observer=%s", observer_id)
    observer = next((x for x in source.observers if x.observer_id == observer_id), None)
    if observer is None:
        reject("ready-image-observer-missing")
    values: list[str] = []
    for row in observer.rows:
        if row.response.status is ResponseStatus.READY:
            item = row.response.value.value_digest
            if item not in values:
                values.append(item)
    result = tuple(values)
    logger.debug("ready_image exit observer=%s values=%d", observer_id, len(result))
    return result


def identity_map(source: ObserverNetworkSource, observer_id: str) -> PartialMap:
    """Derive identity on the full nonempty reachable image."""
    logger.debug("identity_map entry observer=%s", observer_id)
    image = ready_image(source, observer_id)
    if not image:
        reject("identity-image-vacuous")
    rows = tuple((x, x) for x in image)
    result = PartialMap((), observer_id, observer_id, image, rows, map_digest((), observer_id, observer_id, rows))
    logger.debug("identity_map exit observer=%s rows=%d", observer_id, len(rows))
    return result


def operational_edge_map(source: ObserverNetworkSource, edge_id: str) -> PartialMap:
    """Derive barT by intersecting declared domain with reachable source image."""
    logger.debug("operational_edge_map entry edge=%s", edge_id)
    edge = next((x for x in source.translations if x.edge_id == edge_id), None)
    if edge is None:
        reject("operational-edge-missing")
    declared = {x.source_value.value_digest: x.target_value.value_digest for x in edge.rows}
    image = ready_image(source, edge.source_observer_id)
    rows = tuple((x, declared[x]) for x in image if x in declared)
    domain = tuple(x for x, _ in rows)
    result = PartialMap(
        (edge_id,),
        edge.source_observer_id,
        edge.target_observer_id,
        domain,
        rows,
        map_digest((edge_id,), edge.source_observer_id, edge.target_observer_id, rows),
    )
    logger.debug("operational_edge_map exit edge=%s rows=%d", edge_id, len(rows))
    return result


def compose_maps(left: PartialMap, right: PartialMap) -> PartialMap:
    """Derive exact pullback-domain composition, never a supplied truth table."""
    logger.debug("compose_maps entry left_type=%s right_type=%s", type(left).__name__, type(right).__name__)
    if (
        type(left) is not PartialMap
        or type(right) is not PartialMap
        or left.target_observer_id != right.source_observer_id
    ):
        reject("partial-maps-not-composable")
    logger.debug("compose_maps validated left=%d right=%d", len(left.path_edge_ids), len(right.path_edge_ids))
    right_rows = dict(right.rows)
    rows = tuple((source, right_rows[mid]) for source, mid in left.rows if mid in right_rows)
    path = left.path_edge_ids + right.path_edge_ids
    result = PartialMap(
        path,
        left.source_observer_id,
        right.target_observer_id,
        tuple(x for x, _ in rows),
        rows,
        map_digest(path, left.source_observer_id, right.target_observer_id, rows),
    )
    logger.debug("compose_maps exit rows=%d", len(rows))
    return result


def compose_path(source: ObserverNetworkSource, edge_ids: tuple[str, ...]) -> PartialMap:
    """Derive one nonempty finite path from raw operational edge maps."""
    logger.debug("compose_path entry edges=%d", len(edge_ids))
    if type(edge_ids) is not tuple or not edge_ids or any(type(x) is not str for x in edge_ids):
        reject("composition-path-invalid")
    result = operational_edge_map(source, edge_ids[0])
    for edge_id in edge_ids[1:]:
        result = compose_maps(result, operational_edge_map(source, edge_id))
    logger.debug("compose_path exit rows=%d", len(result.rows))
    return result
