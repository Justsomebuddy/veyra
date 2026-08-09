"""Exact edge-derived path transports and finite generated fillers for P3-C2."""

from __future__ import annotations
import logging
from ..confluence.generated.source import snapshot_ranked_system
from ..confluence.generated.types import RankedContinuationSystem
from .common import digest, exact_digest, exact_shape, reject
from .types import GeneratedTransportFiller, TotalTransportDoctrine
from .index import (
    TransportIndex,
    build_transport_index,
    index_apply,
    index_equivalent,
    index_replay,
)

logger = logging.getLogger(__name__)
HARD_PATH_LENGTH = 128
HARD_GENERATED_PATHS = 16384


def replay_path(system: RankedContinuationSystem, start_id: str, path: tuple[str, ...]) -> str:
    """Replay an exact pure same-system edge-occurrence path."""
    logger.debug("replay_path entry")
    system = snapshot_ranked_system(system)
    if type(start_id) is not str or type(path) is not tuple or any(type(x) is not str for x in path):
        reject("transport-path-shape-invalid")
    if len(path) > HARD_PATH_LENGTH:
        reject("transport-path-length-limit")
    edges = {x.edge_id: x for x in system.edges}
    current = start_id
    for edge_id in path:
        edge = edges.get(edge_id)
        if edge is None:
            reject("transport-path-foreign-edge")
        if edge.source_id != current:
            reject("transport-path-not-composable")
        current = edge.target_id
    logger.debug("replay_path exit target=%s", current)
    return current


def apply_path(
    system: RankedContinuationSystem,
    doctrine: TotalTransportDoctrine,
    start_id: str,
    path: tuple[str, ...],
    value_id: str,
) -> tuple[str, str]:
    """Derive canonical transport only by composing exact edge tables."""
    logger.debug("apply_path entry")
    index = build_transport_index(system, doctrine, HARD_GENERATED_PATHS)
    result = index_apply(index, start_id, path, value_id)
    logger.debug("apply_path exit target=%s value=%s", *result)
    return result


def paths_equivalent(
    system: RankedContinuationSystem,
    doctrine: TotalTransportDoctrine,
    start_id: str,
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> bool:
    """Compare total path maps pointwise modulo the exact target setoid."""
    logger.debug("paths_equivalent entry")
    index = build_transport_index(system, doctrine, HARD_GENERATED_PATHS)
    result = index_equivalent(index, start_id, left, right)
    logger.debug("paths_equivalent exit result=%s", result)
    return result


def generated_paths(
    system: RankedContinuationSystem, start_id: str, max_paths: int = HARD_GENERATED_PATHS
) -> tuple[tuple[str, ...], ...]:
    """Generate every finite path from one state in a strict-ranked DAG."""
    logger.debug("generated_paths entry")
    system = snapshot_ranked_system(system)
    if type(max_paths) is not int or type(max_paths) is bool or not 1 <= max_paths <= HARD_GENERATED_PATHS:
        reject("generated-path-cap-invalid")
    if start_id not in {x.state_id for x in system.states}:
        reject("generated-path-start-foreign")
    outgoing = {x.state_id: [] for x in system.states}
    for edge in system.edges:
        outgoing[edge.source_id].append(edge)
    result = []
    stack = [(start_id, ())]
    while stack:
        state, path = stack.pop()
        result.append(path)
        if len(result) > max_paths:
            reject("generated-path-count-limit")
        for edge in sorted(outgoing[state], key=lambda x: x.edge_id, reverse=True):
            stack.append((edge.target_id, (*path, edge.edge_id)))
    final = tuple(sorted(result, key=lambda x: (len(x), x)))
    logger.debug("generated_paths exit count=%d", len(final))
    return final


def derive_global_fillers(
    system: RankedContinuationSystem, doctrine: TotalTransportDoctrine, max_paths: int
) -> tuple[GeneratedTransportFiller, ...]:
    """Exhaustively derive one commuting filler per generated reachable boundary pair."""
    logger.debug("derive_global_fillers entry")
    index = build_transport_index(system, doctrine, max_paths)
    return derive_indexed_global_fillers(index, max_paths)


def derive_indexed_global_fillers(
    index: TransportIndex, max_paths: int
) -> tuple[GeneratedTransportFiller, ...]:
    """Derive fillers through one prevalidated, fully cached execution index."""
    system, doctrine = index.system, index.doctrine
    reachable = _reachable_states(index)
    root_boundaries = tuple((root, index.paths[root]) for root in reachable)
    if sum(len(boundaries) * len(boundaries) for _, boundaries in root_boundaries) > max_paths:
        reject("generated-boundary-count-limit")
    output = []
    for root, boundaries in root_boundaries:
        continuations = {index_replay(index, root, p): index.paths[index_replay(index, root, p)] for p in boundaries}
        for left in boundaries:
            for right in boundaries:
                lu = index_replay(index, root, left)
                rv = index_replay(index, root, right)
                chosen = None
                for a in continuations[lu]:
                    ta = index_replay(index, lu, a)
                    for b in continuations[rv]:
                        if index_replay(index, rv, b) != ta:
                            continue
                        if index_equivalent(index, root, (*left, *a), (*right, *b)):
                            chosen = (ta, a, b)
                            break
                    if chosen is not None:
                        break
                if chosen is None:
                    reject("generated-transport-filler-missing")
                target, a, b = chosen
                fd = digest(
                    "veyra.p3c2.global-filler.v1",
                    (
                        ("system", system.system_digest.encode()),
                        ("doctrine", doctrine.doctrine_digest.encode()),
                        ("root", root.encode()),
                        ("left", repr(left).encode()),
                        ("right", repr(right).encode()),
                        ("target", target.encode()),
                        ("left-post", repr(a).encode()),
                        ("right-post", repr(b).encode()),
                    ),
                )
                output.append(GeneratedTransportFiller(root, left, right, target, a, b, fd))
    result = tuple(output)
    logger.debug("derive_global_fillers exit count=%d", len(result))
    return result


def _reachable_states(index: TransportIndex) -> tuple[str, ...]:
    """Derive root reachability without resnapshotting trusted indexed sources."""
    seen, stack = set(index.system.roots), list(index.system.roots)
    outgoing = {x: [] for x in index.paths}
    for edge in index.system.edges:
        outgoing[edge.source_id].append(edge.target_id)
    while stack:
        for target in outgoing[stack.pop()]:
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return tuple(sorted(seen))


def boundary_digest(filler: GeneratedTransportFiller) -> str:
    """Bind the exact same-boundary identity used by derived reconciliation."""
    logger.debug("boundary_digest entry")
    exact_shape(filler, GeneratedTransportFiller, "generated-filler")
    if type(filler.root_state_id) is not str or type(filler.target_state_id) is not str:
        reject("generated-filler-state-invalid")
    for name in ("left_boundary", "right_boundary", "left_postpath", "right_postpath"):
        row = object.__getattribute__(filler, name)
        if type(row) is not tuple or any(type(x) is not str for x in row):
            reject("generated-filler-path-invalid")
    exact_digest(object.__getattribute__(filler, "filler_digest"), "generated-filler-digest")
    result = digest(
        "veyra.p3c2.boundary.v1",
        (
            ("root", filler.root_state_id.encode()),
            ("left", repr(filler.left_boundary).encode()),
            ("right", repr(filler.right_boundary).encode()),
        ),
    )
    logger.debug("boundary_digest exit")
    return result
