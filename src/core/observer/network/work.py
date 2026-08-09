"""Syntactic path and authoritative aggregate work charging for P3-T."""

from __future__ import annotations

import logging

from .common import reject
from .types import ObserverNetworkSource, ResponseStatus

logger = logging.getLogger(__name__)


def network_evaluation_charge(raw: ObserverNetworkSource, path_cap: int = 4096) -> int:
    """Expose deterministic conservative work for exact cap regressions."""
    logger.debug("network_evaluation_charge entry")
    result = network_work_charge(raw, path_cap)[0]
    logger.debug("network_evaluation_charge exit work=%d", result)
    return result


def network_work_charge(raw: ObserverNetworkSource, path_cap: int = 4096) -> tuple[int, int]:
    """Expose total work and its ordered-A2-row component separately."""
    logger.debug("network_work_charge entry")
    if type(raw) is not ObserverNetworkSource or type(path_cap) is not int or path_cap <= 0:
        reject("evaluation-charge-root-invalid")
    groups = (raw.inputs, raw.observers, raw.translations, raw.triangles, raw.raw_pairs)
    if any(type(group) is not tuple for group in groups):
        reject("evaluation-charge-container-invalid")
    if any(type(item.rows) is not tuple for item in (*raw.observers, *raw.translations)):
        reject("evaluation-charge-rows-invalid")
    row_count = sum(len(item.rows) for item in (*raw.observers, *raw.translations))
    result = evaluation_charge(*groups, row_count, path_cap)
    logger.debug("network_work_charge exit work=%d a2_rows=%d", *result)
    return result


def evaluation_charge(inputs, observers, edges, triangles, raw_pairs, row_count, path_cap):
    """Count observer replay, A2 rows, maps, rows, paths, and triangles."""
    logger.debug("evaluation charge entry")
    path_count, _ = _charge_simple_paths(
        observers, edges, len(triangles) + len(raw_pairs), path_cap
    )
    path_replays = _runtime_path_replay_count(observers, edges)
    a2_rows = _ordered_a2_row_charge(inputs, observers, edges, path_replays)
    work = (
        len(inputs) * len(observers)
        + a2_rows
        + row_count
        + len(inputs) * (len(edges) + path_count + len(triangles))
    )
    logger.debug("evaluation charge exit work=%d a2_rows=%d", work, a2_rows)
    return work, a2_rows


def _charge_simple_paths(observers, edges, initial: int, cap: int) -> tuple[int, int]:
    """Syntactically charge every finite simple directed path before replay."""
    logger.debug("charge simple paths entry initial=%d", initial)
    generated = initial
    reachable = set()
    for observer in observers:
        if type(observer.observer_id) is not str:
            reject("observer-identifier-type-invalid")
        stack = [(observer.observer_id, (observer.observer_id,))]
        while stack:
            node, visited = stack.pop()
            for edge in edges:
                if edge.source_observer_id != node or edge.target_observer_id in visited:
                    continue
                generated += 1
                if generated > cap:
                    reject("generated-path-hard-limit")
                reachable.add((observer.observer_id, edge.target_observer_id))
                stack.append((edge.target_observer_id, visited + (edge.target_observer_id,)))
    result = (generated, len(reachable))
    logger.debug("charge simple paths exit total=%d reachable=%d", *result)
    return result


def _ordered_a2_row_charge(inputs, observers, edges, path_replays: int) -> int:
    """Charge every demanded and conservatively reachable ordered A2 row."""
    logger.debug("ordered a2 charge entry")
    distinct = len(observers) * (len(observers) - 1)
    composable_distinct = sum(
        1
        for left in edges
        for right in edges
        if left.target_observer_id == right.source_observer_id
        and left.source_observer_id != right.target_observer_id
    )
    calls = len(edges) + distinct + composable_distinct + path_replays
    result = calls * len(inputs) * len(inputs)
    logger.debug("ordered a2 charge exit calls=%d rows=%d", calls, result)
    return result


def _runtime_path_replay_count(observers, edges) -> int:
    """Count closed-table positive path laws, excluding established iso orientations."""
    logger.debug("runtime path replay count entry")
    by_observer = {item.observer_id: item for item in observers}
    eligible = []
    for edge in edges:
        source = by_observer.get(edge.source_observer_id)
        target = by_observer.get(edge.target_observer_id)
        if source is None or target is None:
            reject("evaluation-charge-edge-endpoint-missing")
        if len(source.rows) != len(target.rows):
            reject("evaluation-charge-observer-row-length-mismatch")
        if any(
            item.response.status is ResponseStatus.READY and item.response.value is None
            for item in (*source.rows, *target.rows)
        ):
            reject("evaluation-charge-ready-value-missing")
        source_image = tuple(
            item.response.value.value_digest
            for item in source.rows
            if item.response.status is ResponseStatus.READY
        )
        table = {item.source_value.value_digest: item.target_value.value_digest for item in edge.rows}
        statuses_equal = tuple(item.response.status for item in source.rows) == tuple(
            item.response.status for item in target.rows
        )
        blocked = any(
            item.response.status is ResponseStatus.BLOCKED for item in (*source.rows, *target.rows)
        )
        commutes = bool(source_image) and set(source_image) <= set(table) and all(
            item.response.status is not ResponseStatus.READY
            or (
                target.rows[index].response.status is ResponseStatus.READY
                and table[item.response.value.value_digest]
                == target.rows[index].response.value.value_digest
            )
            for index, item in enumerate(source.rows)
        )
        if commutes and statuses_equal and not blocked:
            eligible.append(edge)
    adjacency = {}
    for edge in eligible:
        adjacency.setdefault(edge.source_observer_id, []).append(edge.target_observer_id)
    reachable = set()
    for observer in observers:
        start = observer.observer_id
        stack = [(start, (start,))]
        while stack:
            node, visited = stack.pop()
            for target in adjacency.get(node, []):
                if target in visited:
                    continue
                reachable.add((start, target))
                stack.append((target, visited + (target,)))
    iso = set()
    for forward in eligible:
        for reverse in eligible:
            if (
                forward.source_observer_id == reverse.target_observer_id
                and forward.target_observer_id == reverse.source_observer_id
            ):
                frows = {item.source_value.value_digest: item.target_value.value_digest for item in forward.rows}
                rrows = {item.source_value.value_digest: item.target_value.value_digest for item in reverse.rows}
                if all(rrows.get(target) == source for source, target in frows.items()) and all(
                    frows.get(target) == source for source, target in rrows.items()
                ):
                    iso.add((forward.source_observer_id, forward.target_observer_id))
    result = len(reachable - iso)
    logger.debug("runtime path replay count exit count=%d", result)
    return result
