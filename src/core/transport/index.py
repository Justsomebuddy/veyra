"""One-shot validated execution index and exact conservative work charge."""

from __future__ import annotations
from dataclasses import dataclass
import logging
from ..confluence.generated.source import snapshot_ranked_system
from ..confluence.generated.types import RankedContinuationSystem
from .common import reject
from .source import snapshot_transport_doctrine
from .types import TotalTransportDoctrine

logger = logging.getLogger(__name__)
HARD_PATH_LENGTH = 128
HARD_GENERATED_PATHS = 16384


@dataclass(frozen=True)
class TransportIndex:
    system: RankedContinuationSystem
    doctrine: TotalTransportDoctrine
    edges: dict
    carriers: dict
    maps: dict
    classes: dict
    paths: dict[str, tuple[tuple[str, ...], ...]]
    endpoints: dict[tuple[str, tuple[str, ...]], str]


@dataclass(frozen=True)
class SemanticWorkCharge:
    boundary_pairs: int
    continuation_candidates: int
    carrier_evaluations: int
    edge_applications: int
    validation_snapshot: int
    total: int


def build_transport_index(
    system: RankedContinuationSystem, doctrine: TotalTransportDoctrine, max_paths: int
) -> TransportIndex:
    """Snapshot sources once and cache every generated path endpoint/map."""
    logger.debug("build_transport_index entry")
    system = snapshot_ranked_system(system)
    doctrine = snapshot_transport_doctrine(system, doctrine)
    if type(max_paths) is not int or type(max_paths) is bool or not 1 <= max_paths <= HARD_GENERATED_PATHS:
        reject("generated-path-cap-invalid")
    edges = {x.edge_id: x for x in system.edges}
    carriers = {x.state_id: x for x in doctrine.carriers}
    maps = {
        x.edge_id: {r.source_value_id: r.target_value_id for r in x.entries}
        for x in doctrine.edge_maps
    }
    classes = {x.state_id: {r.value_id: r.class_id for r in x.classes} for x in doctrine.carriers}
    outgoing = {x.state_id: [] for x in system.states}
    for edge in system.edges:
        outgoing[edge.source_id].append(edge)
    paths, endpoints = {}, {}
    for state in sorted(outgoing):
        rows, stack = [], [(state, ())]
        while stack:
            current, path = stack.pop()
            rows.append(path)
            if len(rows) > max_paths:
                reject("generated-path-count-limit")
            endpoints[(state, path)] = current
            for edge in sorted(outgoing[current], key=lambda x: x.edge_id, reverse=True):
                stack.append((edge.target_id, (*path, edge.edge_id)))
        paths[state] = tuple(sorted(rows, key=lambda x: (len(x), x)))
    result = TransportIndex(system, doctrine, edges, carriers, maps, classes, paths, endpoints)
    logger.debug("build_transport_index exit states=%d", len(paths))
    return result


def index_replay(index: TransportIndex, start: str, path: tuple[str, ...]) -> str:
    """Replay through the validated endpoint cache."""
    if type(start) is not str or type(path) is not tuple or len(path) > HARD_PATH_LENGTH:
        reject("transport-path-shape-invalid")
    if any(type(x) is not str for x in path):
        reject("transport-path-shape-invalid")
    target = index.endpoints.get((start, path))
    if target is None:
        reject("transport-path-not-composable")
    return target


def index_apply(index: TransportIndex, start: str, path: tuple[str, ...], value: str) -> tuple[str, str]:
    """Apply cached total edge maps without resnapshotting in loops."""
    target = index_replay(index, start, path)
    if value not in {x.value_id for x in index.carriers[start].values}:
        reject("transport-source-value-foreign")
    current = value
    for edge in path:
        current = index.maps[edge][current]
    return target, current


def index_equivalent(index: TransportIndex, start: str, left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    """Compare cached composite maps pointwise modulo target setoid."""
    target = index_replay(index, start, left)
    if index_replay(index, start, right) != target:
        reject("transport-map-codomain-mismatch")
    for value in index.carriers[start].values:
        lv = index_apply(index, start, left, value.value_id)[1]
        rv = index_apply(index, start, right, value.value_id)[1]
        if index.classes[target][lv] != index.classes[target][rv]:
            return False
    return True


def semantic_work_charge(index: TransportIndex, canonical_bytes: int, local_fillers: tuple) -> SemanticWorkCharge:
    """Exactly charge the conservative exhaustive search and source validation envelope."""
    boundary_pairs = continuation_candidates = carrier_evaluations = edge_applications = 0
    path_build_edges = sum(len(path) for rows in index.paths.values() for path in rows)
    for root in _reachable_states(index):
        boundaries = index.paths[root]
        values = len(index.carriers[root].values)
        grouped: dict[str, tuple[int, int]] = {}
        for path in boundaries:
            endpoint = index_replay(index, root, path)
            count, lengths = grouped.get(endpoint, (0, 0))
            grouped[endpoint] = count + 1, lengths + len(path)
        for left_endpoint, (left_count, left_lengths) in grouped.items():
            left_posts = index.paths[left_endpoint]
            left_post_count = len(left_posts)
            left_post_lengths = sum(map(len, left_posts))
            for right_endpoint, (right_count, right_lengths) in grouped.items():
                right_posts = index.paths[right_endpoint]
                right_post_count = len(right_posts)
                right_post_lengths = sum(map(len, right_posts))
                pairs = left_count * right_count
                candidates = pairs * left_post_count * right_post_count
                continuation_lengths = pairs * (
                    right_post_count * left_post_lengths + left_post_count * right_post_lengths
                )
                boundary_lengths = left_post_count * right_post_count * (
                    right_count * left_lengths + left_count * right_lengths
                )
                boundary_pairs += pairs
                continuation_candidates += candidates
                carrier_evaluations += values * candidates
                edge_applications += continuation_lengths
                edge_applications += values * (boundary_lengths + continuation_lengths)
    max_values = max((len(x.values) for x in index.doctrine.carriers), default=0)
    for cell in local_fillers:
        # Two branch edges plus both declared postpaths, for every carrier value.
        edge_applications += max_values * (2 + len(cell.left_path) + len(cell.right_path))
    validation = (
        canonical_bytes
        + len(index.system.states)
        + len(index.system.edges)
        + sum(len(x.values) + len(x.classes) for x in index.doctrine.carriers)
        + sum(len(x.entries) for x in index.doctrine.edge_maps)
        + path_build_edges
    )
    total = boundary_pairs + continuation_candidates + carrier_evaluations + edge_applications + validation
    return SemanticWorkCharge(
        boundary_pairs, continuation_candidates, carrier_evaluations, edge_applications, validation, total
    )


def _reachable_states(index: TransportIndex) -> tuple[str, ...]:
    """Return root-reachable states without invoking source snapshots."""
    outgoing = {x: [] for x in index.paths}
    for edge in index.system.edges:
        outgoing[edge.source_id].append(edge.target_id)
    seen, stack = set(index.system.roots), list(index.system.roots)
    while stack:
        for target in outgoing[stack.pop()]:
            if target not in seen:
                seen.add(target)
                stack.append(target)
    return tuple(sorted(seen))
