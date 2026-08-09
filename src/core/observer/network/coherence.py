"""Units, arbitrary-path preorder closure, triangles, and strict-cycle checks."""

from __future__ import annotations

import logging

from .common import reject
from .digest import records_digest
from .maps import compose_maps, compose_path, identity_map, operational_edge_map
from .relations import path_laws, raw_pair_witnesses
from .types import (
    AssociativityJudgment,
    EdgeJudgment,
    IdentityLawJudgment,
    IsomorphismJudgment,
    LawStatus,
    ObserverNetworkSource,
    ObserverPairJudgment,
    RefinementStatus,
    TriangleDemand,
    TriangleJudgment,
    TriangleStatus,
)

logger = logging.getLogger(__name__)


def identity_law(source: ObserverNetworkSource, edge_id: str) -> IdentityLawJudgment:
    """Check both nonvacuous exact-domain unit laws for one edge."""
    logger.debug("identity_law entry edge=%s", edge_id)
    edge = operational_edge_map(source, edge_id)
    left = compose_maps(identity_map(source, edge.source_observer_id), edge)
    right = compose_maps(edge, identity_map(source, edge.target_observer_id))
    left_domain = bool(edge.domain) and left.domain == edge.domain
    right_domain = bool(edge.domain) and right.domain == edge.domain
    if not edge.domain:
        left_status = right_status = LawStatus.NOT_ESTABLISHED
    else:
        left_status = LawStatus.ESTABLISHED if left_domain and left.rows == edge.rows else LawStatus.REFUTED
        right_status = LawStatus.ESTABLISHED if right_domain and right.rows == edge.rows else LawStatus.REFUTED
    jid = records_digest(
        "p3t-identity-law-v2", (edge_id, str(left_domain), str(right_domain), left_status.value, right_status.value), ()
    )
    result = IdentityLawJudgment(edge_id, left_domain, right_domain, left_status, right_status, jid)
    logger.debug("identity_law exit edge=%s", edge_id)
    return result


def associativity_law(source: ObserverNetworkSource, edge_ids: tuple[str, str, str]) -> AssociativityJudgment:
    """Compare both parenthesizations without turning an empty path positive."""
    logger.debug("associativity_law entry")
    if type(edge_ids) is not tuple or len(edge_ids) != 3:
        reject("associativity-edge-ids-invalid")
    a, b, c = tuple(operational_edge_map(source, x) for x in edge_ids)
    left = compose_maps(compose_maps(a, b), c)
    right = compose_maps(a, compose_maps(b, c))
    same_domain = left.domain == right.domain
    if not a.domain or not b.domain or not c.domain or not left.domain:
        status = LawStatus.NOT_ESTABLISHED
    else:
        status = LawStatus.ESTABLISHED if same_domain and left.rows == right.rows else LawStatus.REFUTED
    jid = records_digest(
        "p3t-associativity-v2", (*edge_ids, left.map_digest, right.map_digest, str(same_domain), status.value), ()
    )
    result = AssociativityJudgment(edge_ids, left.map_digest, right.map_digest, same_domain, status, jid)
    logger.debug("associativity_law exit status=%s", status.value)
    return result


def triangle_judgment(source: ObserverNetworkSource, demand: TriangleDemand) -> TriangleJudgment:
    """Separate exact whole-domain coherence from intersection-only agreement."""
    logger.debug("triangle_judgment entry demand=%s", demand.demand_id)
    direct = operational_edge_map(source, demand.direct_edge_id)
    indirect = compose_path(source, demand.indirect_edge_ids)
    drows = dict(direct.rows)
    irows = dict(indirect.rows)
    intersection = tuple(x for x in direct.domain if x in irows)
    mismatch = next((x for x in intersection if drows[x] != irows[x]), "")
    if not direct.domain or not indirect.domain:
        status = TriangleStatus.OPEN
    elif mismatch:
        status = TriangleStatus.REFUTED
    elif direct.domain == indirect.domain:
        status = TriangleStatus.ESTABLISHED
    else:
        status = TriangleStatus.AGREES_ON_DOMAIN_INTERSECTION
    jid = records_digest(
        "p3t-triangle-v2", (demand.demand_id, direct.map_digest, indirect.map_digest, status.value, mismatch), ()
    )
    result = TriangleJudgment(
        demand.demand_id, direct.map_digest, indirect.map_digest, direct.domain, indirect.domain, status, mismatch, jid
    )
    logger.debug("triangle_judgment exit status=%s", status.value)
    return result


def observer_pair_judgments(
    source: ObserverNetworkSource,
    edges: tuple[EdgeJudgment, ...],
    isomorphisms: tuple[IsomorphismJudgment, ...],
    path_cap: int,
) -> tuple[ObserverPairJudgment, ...]:
    """Classify all ordered pairs using arbitrary finite simple positive paths."""
    logger.debug("observer_pair_judgments entry")
    paths = _positive_path_closure(source, edges, path_cap)
    iso_paths = _isomorphism_paths(source, isomorphisms, path_cap)
    edge_by_id = {x.edge_id: x for x in edges}
    output = []
    for src in source.observers:
        for dst in source.observers:
            key = (src.observer_id, dst.observer_id)
            path = ()
            if src is dst:
                status = RefinementStatus.ISOMORPHIC
                forward = reverse = None
            else:
                preservation, reflection, forward, reverse = raw_pair_witnesses(source, *key)
                if key in iso_paths:
                    status = RefinementStatus.ISOMORPHIC
                    path = iso_paths[key]
                elif key in paths:
                    path = paths[key]
                    op = compose_path(source, path)
                    relation, translation = path_laws(source, op, tuple(edge_by_id[x] for x in path))
                    if relation is LawStatus.ESTABLISHED and translation is LawStatus.ESTABLISHED:
                        status = (
                            RefinementStatus.STRICT
                            if reflection is LawStatus.REFUTED and reverse is not None
                            else RefinementStatus.NONSTRICT
                        )
                    else:
                        status = RefinementStatus.OPEN
                elif (
                    preservation is LawStatus.REFUTED
                    and reflection is LawStatus.REFUTED
                    and forward is not None
                    and reverse is not None
                ):
                    status = RefinementStatus.INCOMPARABLE
                else:
                    status = RefinementStatus.OPEN
            jid = records_digest(
                "p3t-observer-pair-v2",
                (src.observer_id, dst.observer_id, *path, status.value, str(forward), str(reverse)),
                (),
            )
            output.append(ObserverPairJudgment(src.observer_id, dst.observer_id, path, status, forward, reverse, jid))
    result = tuple(output)
    logger.debug("observer_pair_judgments exit pairs=%d", len(result))
    return result


def _positive_path_closure(source, edges, cap):
    """Generate one exact arbitrary finite simple positive path per reachable pair."""
    logger.debug("positive_path_closure entry")
    raw_edges = {x.edge_id: x for x in source.translations}
    adjacency = {}
    for item in edges:
        if item.refinement in (RefinementStatus.NONSTRICT, RefinementStatus.STRICT):
            raw = raw_edges[item.edge_id]
            adjacency.setdefault(raw.source_observer_id, []).append((raw.target_observer_id, item.edge_id))
    paths = {}
    generated = 0
    for observer in source.observers:
        stack = [(observer.observer_id, (), (observer.observer_id,))]
        while stack:
            node, path, visited = stack.pop()
            for target, edge_id in reversed(adjacency.get(node, [])):
                if target in visited:
                    continue
                candidate = path + (edge_id,)
                generated += 1
                if generated > cap:
                    reject("refinement-path-hard-limit")
                paths.setdefault((observer.observer_id, target), candidate)
                stack.append((target, candidate, visited + (target,)))
    logger.debug("positive_path_closure exit paths=%d", len(paths))
    return paths


def _isomorphism_paths(source, isomorphisms, cap):
    """Close established two-map isomorphisms under finite representative paths."""
    logger.debug("isomorphism_paths entry")
    raw = {x.edge_id: x for x in source.translations}
    adjacency = {}
    for item in isomorphisms:
        if item.status is LawStatus.ESTABLISHED:
            f = raw[item.forward_edge_id]
            r = raw[item.reverse_edge_id]
            adjacency.setdefault(f.source_observer_id, []).append((f.target_observer_id, f.edge_id))
            adjacency.setdefault(r.source_observer_id, []).append((r.target_observer_id, r.edge_id))
    result = {}
    generated = 0
    for observer in source.observers:
        start = observer.observer_id
        stack = [(start, (), (start,))]
        while stack:
            node, path, visited = stack.pop()
            for target, edge_id in reversed(adjacency.get(node, [])):
                if target in visited:
                    continue
                candidate = path + (edge_id,)
                generated += 1
                if generated > cap:
                    reject("isomorphism-path-hard-limit")
                result.setdefault((start, target), candidate)
                stack.append((target, candidate, visited + (target,)))
    logger.debug("isomorphism_paths exit pairs=%d", len(result))
    return result


def strict_cycle_check(
    source: ObserverNetworkSource, edges: tuple[EdgeJudgment, ...], path_cap: int = 4096
) -> tuple[LawStatus, tuple[str, ...]]:
    """Search strict starts and deterministic node-simple positive return paths."""
    logger.debug("strict_cycle_check entry")
    if type(path_cap) is not int or path_cap <= 0:
        reject("strict-cycle-path-cap-invalid")
    raw = {x.edge_id: x for x in source.translations}
    positive = []
    for item in edges:
        if item.refinement in (RefinementStatus.NONSTRICT, RefinementStatus.STRICT):
            edge = raw[item.edge_id]
            positive.append((
                item.edge_id,
                edge.source_observer_id,
                edge.target_observer_id,
                item.refinement is RefinementStatus.STRICT,
            ))
    adjacency: dict[str, list[tuple[str, str]]] = {}
    seen_arcs: set[tuple[str, str]] = set()
    for edge_id, source_id, target_id, _ in positive:
        arc = (source_id, target_id)
        if arc not in seen_arcs:
            seen_arcs.add(arc)
            adjacency.setdefault(source_id, []).append((target_id, edge_id))
    traversed = 0
    for start_id, start, target, strict in positive:
        if not strict:
            continue
        if target == start:
            logger.debug("strict_cycle_check exit refuted self-loop")
            return LawStatus.REFUTED, (start_id,)
        stack = [(target, (start_id,), frozenset((start, target)))]
        while stack:
            node, path, visited = stack.pop()
            for next_node, edge_id in reversed(adjacency.get(node, ())):
                traversed += 1
                if traversed > path_cap:
                    reject("strict-cycle-path-hard-limit")
                candidate = path + (edge_id,)
                if next_node == start:
                    logger.debug("strict_cycle_check exit refuted")
                    return LawStatus.REFUTED, candidate
                if next_node not in visited:
                    stack.append((next_node, candidate, visited | {next_node}))
    logger.debug("strict_cycle_check exit established")
    return LawStatus.ESTABLISHED, ()
