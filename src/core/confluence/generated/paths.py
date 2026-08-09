"""Source-derived reachability, peaks, and path replay for P3-C1."""

from __future__ import annotations

import logging

from .common import reject
from .digest import peak_digest
from .types import GeneratedLocalPeak, RankedContinuationSystem

logger = logging.getLogger(__name__)


def generated_reachable(system: RankedContinuationSystem) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Derive the whole root-reachable subgraph from source edges."""
    logger.debug("generated_reachable entry")
    from .source import snapshot_ranked_system

    system = snapshot_ranked_system(system)
    outgoing: dict[str, list] = {}
    for edge in system.edges:
        outgoing.setdefault(edge.source_id, []).append(edge)
    seen = set(system.roots)
    frontier = list(system.roots)
    used: set[str] = set()
    while frontier:
        source = frontier.pop(0)
        for edge in outgoing.get(source, ()):
            used.add(edge.edge_id)
            if edge.target_id not in seen:
                seen.add(edge.target_id)
                frontier.append(edge.target_id)
    result = tuple(sorted(seen)), tuple(sorted(used))
    logger.debug("generated_reachable exit states=%d edges=%d", len(result[0]), len(result[1]))
    return result


def generated_local_peaks(
    system: RankedContinuationSystem,
) -> tuple[GeneratedLocalPeak, ...]:
    """Generate every ordered pair of distinct outgoing edge occurrences."""
    logger.debug("generated_local_peaks entry")
    system = __snapshot(system)
    reachable_states, _ = generated_reachable(system)
    outgoing = {
        state_id: tuple(edge for edge in system.edges if edge.source_id == state_id) for state_id in reachable_states
    }
    rows = []
    for source in reachable_states:
        edges = outgoing[source]
        for left in edges:
            for right in edges:
                if left.edge_id == right.edge_id:
                    continue
                value = peak_digest(system.system_digest, source, left.edge_commitment, right.edge_commitment)
                rows.append(GeneratedLocalPeak(value, source, left.edge_id, right.edge_id, value))
    result = tuple(rows)
    logger.debug("generated_local_peaks exit peaks=%d", len(result))
    return result


def replay_edge_path(system: RankedContinuationSystem, start_id: str, edge_ids: tuple[str, ...]) -> str:
    """Replay only exact edges of this system; identity is an empty path."""
    logger.debug("replay_edge_path entry")
    system = __snapshot(system)
    if type(start_id) is not str:
        reject("join-path-start-type-invalid")
    if type(edge_ids) is not tuple or any(type(item) is not str for item in edge_ids):
        reject("join-path-type-invalid")
    logger.debug("replay_edge_path validated start=%s edges=%d", start_id, len(edge_ids))
    if len(edge_ids) > 128:
        reject("join-path-edge-limit")
    edges = {edge.edge_id: edge for edge in system.edges}
    current = start_id
    for edge_id in edge_ids:
        edge = edges.get(edge_id)
        if edge is None:
            reject("join-path-foreign-edge")
        if edge.source_id != current:
            reject("join-path-not-composable")
        current = edge.target_id
    logger.debug("replay_edge_path exit endpoint=%s", current)
    return current


def branch_targets(system: RankedContinuationSystem, peak: GeneratedLocalPeak) -> tuple[str, str]:
    """Extract exact branch endpoints from source edge occurrences."""
    logger.debug("branch_targets entry")
    system = __snapshot(system)
    if type(peak) is not GeneratedLocalPeak:
        reject("peak-type-invalid")
    edges = {edge.edge_id: edge for edge in system.edges}
    try:
        result = edges[peak.left_edge_id].target_id, edges[peak.right_edge_id].target_id
    except KeyError:
        reject("peak-edge-missing")
    logger.debug("branch_targets exit peak=%s", peak.peak_id)
    return result


def __snapshot(system: RankedContinuationSystem) -> RankedContinuationSystem:
    logger.debug("__snapshot entry")
    from .source import snapshot_ranked_system

    result = snapshot_ranked_system(system)
    logger.debug("__snapshot exit")
    return result
