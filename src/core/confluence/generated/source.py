"""Construct and snapshot the exact ranked continuation source."""

from __future__ import annotations

from dataclasses import replace
import logging

from .common import exact_digest, exact_shape, exact_text, reject
from .digest import edge_digest, state_digest, system_digest
from .types import (
    ContinuationEdge,
    ContinuationState,
    RankedContinuationSystem,
    StateRank,
)

logger = logging.getLogger(__name__)
SYSTEM_VERSION = "p3-c1-ranked-system-v1"
SYSTEM_SCOPE = "finite-ranked-generated-continuation-system"
MAX_STATES = 64
MAX_EDGES = 128
MAX_CANONICAL_BYTES = 1_048_576


def continuation_state(state_id: str, kind: str, payload: bytes) -> ContinuationState:
    """Create one exact state commitment."""
    logger.debug("continuation_state entry")
    exact_text(state_id, "state-id")
    exact_text(kind, "state-kind")
    if type(payload) is not bytes:
        reject("state-payload-type-invalid")
    result = ContinuationState(state_id, kind, bytes(payload), state_digest(state_id, kind, payload))
    logger.debug("continuation_state exit id=%s", state_id)
    return result


def continuation_edge(
    edge_id: str, source_id: str, target_id: str, rule_kind: str, rule_payload: bytes
) -> ContinuationEdge:
    """Create one exact edge occurrence commitment."""
    logger.debug("continuation_edge entry")
    for label, value in (
        ("edge-id", edge_id),
        ("edge-source", source_id),
        ("edge-target", target_id),
        ("rule-kind", rule_kind),
    ):
        exact_text(value, label)
    if type(rule_payload) is not bytes:
        reject("edge-payload-type-invalid")
    result = ContinuationEdge(
        edge_id,
        source_id,
        target_id,
        rule_kind,
        bytes(rule_payload),
        edge_digest(edge_id, source_id, target_id, rule_kind, rule_payload),
    )
    logger.debug("continuation_edge exit id=%s", edge_id)
    return result


def ranked_continuation_system(
    doctrine_fingerprint: str,
    source_id: str,
    source_version: str,
    states: tuple[ContinuationState, ...],
    edges: tuple[ContinuationEdge, ...],
    roots: tuple[str, ...],
    ranks: tuple[StateRank, ...],
) -> RankedContinuationSystem:
    """Canonicalize and bind one finite ranked source."""
    logger.debug("ranked_continuation_system entry")
    for label, value in (
        ("doctrine", doctrine_fingerprint),
        ("source-id", source_id),
        ("source-version", source_version),
    ):
        exact_text(value, label)
    if type(states) is not tuple or type(edges) is not tuple or type(roots) is not tuple or type(ranks) is not tuple:
        reject("ranked-system-constructor-container-invalid")
    states = tuple(_snapshot_state(item) for item in states)
    edges = tuple(_snapshot_edge(item) for item in edges)
    ranks = tuple(_snapshot_rank(item) for item in ranks)
    if any(type(item) is not str for item in roots):
        reject("ranked-system-constructor-root-type-invalid")
    value = RankedContinuationSystem(
        SYSTEM_VERSION,
        doctrine_fingerprint,
        source_id,
        source_version,
        tuple(sorted(states, key=lambda item: item.state_id)),
        tuple(sorted(edges, key=lambda item: item.edge_id)),
        tuple(sorted(roots)),
        tuple(sorted(ranks, key=lambda item: item.state_id)),
        "",
        SYSTEM_SCOPE,
    )
    result = snapshot_ranked_system(replace(value, system_digest=system_digest(value)))
    logger.debug("ranked_continuation_system exit states=%d edges=%d", len(result.states), len(result.edges))
    return result


def snapshot_ranked_system(raw: RankedContinuationSystem) -> RankedContinuationSystem:
    """Hard-bound first, then validate every canonical source invariant."""
    logger.debug("snapshot_ranked_system entry")
    exact_shape(raw, RankedContinuationSystem, "ranked-system")
    _hard_preflight(raw)
    if raw.version != SYSTEM_VERSION or raw.scope != SYSTEM_SCOPE:
        reject("ranked-system-contract-drift")
    for label, value in (
        ("doctrine", raw.doctrine_fingerprint),
        ("source-id", raw.source_id),
        ("source-version", raw.source_version),
    ):
        exact_text(value, label)
    exact_digest(raw.system_digest, "system-digest")
    if (
        type(raw.states) is not tuple
        or type(raw.edges) is not tuple
        or type(raw.roots) is not tuple
        or type(raw.ranks) is not tuple
    ):
        reject("ranked-system-container-type-invalid")
    states = tuple(_snapshot_state(item) for item in raw.states)
    edges = tuple(_snapshot_edge(item) for item in raw.edges)
    if states != tuple(sorted(states, key=lambda item: item.state_id)) or edges != tuple(
        sorted(edges, key=lambda item: item.edge_id)
    ):
        reject("ranked-system-order-invalid")
    state_ids = tuple(item.state_id for item in states)
    if (
        not state_ids
        or len(set(state_ids)) != len(state_ids)
        or len({item.state_commitment for item in states}) != len(states)
    ):
        reject("state-identity-not-distinct")
    if type(raw.roots) is not tuple or not raw.roots or any(type(item) is not str for item in raw.roots):
        reject("roots-invalid")
    if (
        raw.roots != tuple(sorted(raw.roots))
        or len(set(raw.roots)) != len(raw.roots)
        or not set(raw.roots) <= set(state_ids)
    ):
        reject("roots-not-canonical-closed")
    ranks = tuple(_snapshot_rank(item) for item in raw.ranks)
    if (
        ranks != tuple(sorted(ranks, key=lambda item: item.state_id))
        or tuple(item.state_id for item in ranks) != state_ids
    ):
        reject("rank-domain-not-exact")
    rank_map = {item.state_id: item.rank for item in ranks}
    if any(edge.source_id not in rank_map or edge.target_id not in rank_map for edge in edges):
        reject("edge-dangling")
    if len({item.edge_id for item in edges}) != len(edges) or len({item.edge_commitment for item in edges}) != len(
        edges
    ):
        reject("edge-identity-not-distinct")
    if any(rank_map[edge.target_id] >= rank_map[edge.source_id] for edge in edges):
        reject("edge-does-not-strictly-decrease-bound-rank")
    fresh = RankedContinuationSystem(
        raw.version,
        raw.doctrine_fingerprint,
        raw.source_id,
        raw.source_version,
        states,
        edges,
        tuple(raw.roots),
        ranks,
        raw.system_digest,
        raw.scope,
    )
    if system_digest(fresh) != raw.system_digest:
        reject("system-digest-mismatch")
    logger.debug("snapshot_ranked_system exit")
    return fresh


def _hard_preflight(raw: RankedContinuationSystem) -> None:
    logger.debug("_hard_preflight entry")
    for name in ("states", "edges", "roots", "ranks"):
        if type(object.__getattribute__(raw, name)) is not tuple:
            reject("ranked-system-container-type-invalid")
    states = object.__getattribute__(raw, "states")
    edges = object.__getattribute__(raw, "edges")
    if len(states) > MAX_STATES:
        reject("state-hard-limit")
    if len(edges) > MAX_EDGES:
        reject("edge-hard-limit")
    size = sum(
        len(item) if type(item) is bytes else len(item.encode("utf-8")) if type(item) is str else 8
        for item in (
            object.__getattribute__(raw, "doctrine_fingerprint"),
            object.__getattribute__(raw, "source_id"),
        )
    )
    for item in (*states, *edges):
        if type(item) not in (ContinuationState, ContinuationEdge):
            reject("source-member-type-invalid")
        size += sum(
            len(value) if type(value) is bytes else len(value.encode()) if type(value) is str else 8
            for value in item.__dict__.values()
        )
    if size > MAX_CANONICAL_BYTES:
        reject("canonical-byte-hard-limit")
    logger.debug("_hard_preflight exit bytes=%d", size)


def _snapshot_state(raw: ContinuationState) -> ContinuationState:
    logger.debug("_snapshot_state entry")
    exact_shape(raw, ContinuationState, "continuation-state")
    exact_text(raw.state_id, "state-id")
    exact_text(raw.kind, "state-kind")
    exact_digest(raw.state_commitment, "state-commitment")
    if type(raw.payload) is not bytes or state_digest(raw.state_id, raw.kind, raw.payload) != raw.state_commitment:
        reject("state-commitment-mismatch")
    result = ContinuationState(raw.state_id, raw.kind, bytes(raw.payload), raw.state_commitment)
    logger.debug("_snapshot_state exit id=%s", result.state_id)
    return result


def _snapshot_edge(raw: ContinuationEdge) -> ContinuationEdge:
    logger.debug("_snapshot_edge entry")
    exact_shape(raw, ContinuationEdge, "continuation-edge")
    for label, value in (
        ("edge-id", raw.edge_id),
        ("source", raw.source_id),
        ("target", raw.target_id),
        ("rule-kind", raw.rule_kind),
    ):
        exact_text(value, label)
    exact_digest(raw.edge_commitment, "edge-commitment")
    if (
        type(raw.rule_payload) is not bytes
        or edge_digest(raw.edge_id, raw.source_id, raw.target_id, raw.rule_kind, raw.rule_payload)
        != raw.edge_commitment
    ):
        reject("edge-commitment-mismatch")
    result = ContinuationEdge(
        raw.edge_id, raw.source_id, raw.target_id, raw.rule_kind, bytes(raw.rule_payload), raw.edge_commitment
    )
    logger.debug("_snapshot_edge exit id=%s", result.edge_id)
    return result


def _snapshot_rank(raw: StateRank) -> StateRank:
    logger.debug("_snapshot_rank entry")
    exact_shape(raw, StateRank, "state-rank")
    exact_text(raw.state_id, "rank-state-id")
    if type(raw.rank) is not int or type(raw.rank) is bool or not 0 <= raw.rank <= 63:
        reject("rank-invalid")
    result = StateRank(raw.state_id, raw.rank)
    logger.debug("_snapshot_rank exit id=%s", result.state_id)
    return result
