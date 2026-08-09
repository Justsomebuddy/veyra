"""Fresh exact source replay and raw P1-A/P1-A2 closure validation for P3-T."""

from __future__ import annotations

import logging

from ..morphism import snapshot_morphism_doctrine, snapshot_source_binding
from ..relations.request import snapshot_stage_source
from .common import exact_digest, exact_shape, exact_text, reject
from .digest import records_digest
from .preflight import hard_preflight, network_resource_policy
from .source import NETWORK_VERSION
from .value_validation import (
    snapshot_observer,
    snapshot_raw_pair,
    snapshot_translation,
)
from .types import (
    InputSnapshot,
    ObserverNetworkSource,
    TriangleDemand,
)

logger = logging.getLogger(__name__)


def snapshot_network_source(raw: ObserverNetworkSource, policy=None) -> ObserverNetworkSource:
    """Snapshot one exact network only after the aggregate hard-first preflight."""
    logger.debug("snapshot_network_source entry")
    selected = network_resource_policy() if policy is None else policy
    hard_preflight(raw, selected)
    exact_shape(raw, ObserverNetworkSource, "network")
    if raw.version != NETWORK_VERSION:
        reject("network-version-invalid")
    for value, label in (
        (raw.doctrine_id, "network-doctrine-id"),
        (raw.source_id, "network-source-id"),
        (raw.source_version, "network-source-version"),
    ):
        exact_text(value, label)
    exact_digest(raw.network_digest, "network-digest")
    doctrine = snapshot_morphism_doctrine(raw.p1a_doctrine)
    binding = snapshot_source_binding(raw.p1a_binding, doctrine)
    stage_source = snapshot_stage_source(raw.p1a_stage_source, doctrine, binding)
    inputs = tuple(_snapshot_input(x) for x in raw.inputs)
    expected_stage_keys = tuple((x.stage_id, x.commitment) for x in stage_source.stages)
    if tuple((x.input_id, x.stage_commitment) for x in inputs) != expected_stage_keys:
        reject("input-stage-source-not-exact")
    if len({x.input_id for x in inputs}) != len(inputs):
        reject("input-occurrence-duplicate")
    if not inputs or len({x.type_id for x in inputs}) != 1:
        reject("input-scope-type-not-exact")
    members = {x.observer_id: x for x in doctrine.observers}
    observers = tuple(snapshot_observer(x, inputs, stage_source, members) for x in raw.observers)
    if not observers or len({x.observer_id for x in observers}) != len(observers):
        reject("observers-not-distinct-nonempty")
    if tuple(x.observer_id for x in observers) != binding.observer_ids:
        reject("observer-family-not-exact-binding-order")
    observer_map = {x.observer_id: x for x in observers}
    pairs = tuple(snapshot_raw_pair(x, observer_map) for x in raw.raw_pairs)
    required_pairs = tuple((a.observer_id, b.observer_id) for a in observers for b in observers if a is not b)
    if tuple((x.source_observer_id, x.target_observer_id) for x in pairs) != required_pairs:
        reject("raw-p1a2-pair-catalog-not-complete-ordered")
    pair_map = {(x.source_observer_id, x.target_observer_id): x for x in pairs}
    edges = tuple(snapshot_translation(x, observer_map, pair_map) for x in raw.translations)
    if len({x.edge_id for x in edges}) != len(edges):
        reject("translations-not-distinct")
    edge_map = {x.edge_id: x for x in edges}
    triangles = tuple(_snapshot_demand(x, edge_map) for x in raw.triangles)
    if len({x.demand_id for x in triangles}) != len(triangles):
        reject("triangle-demands-not-distinct")
    identity = (
        raw.version,
        raw.doctrine_id,
        raw.source_id,
        raw.source_version,
        doctrine.fingerprint,
        binding.membership_digest,
        stage_source.source_digest,
    )
    children = (
        tuple(item for x in inputs for item in (x.stage_commitment, x.commitment))
        + tuple(x.observer_digest for x in observers)
        + tuple(x.translation_digest for x in edges)
        + tuple(x.pair_digest for x in pairs)
    )
    demands = tuple(
        records_digest("p3t-demand-v2", (x.demand_id, x.direct_edge_id, *x.indirect_edge_ids), ()) for x in triangles
    )
    expected = records_digest("p3t-network-v2", identity, children + demands)
    if expected != raw.network_digest:
        reject("network-digest-mismatch")
    result = ObserverNetworkSource(
        raw.version,
        raw.doctrine_id,
        raw.source_id,
        raw.source_version,
        inputs,
        observers,
        edges,
        triangles,
        doctrine,
        binding,
        stage_source,
        pairs,
        expected,
    )
    logger.debug("snapshot_network_source exit observers=%d edges=%d", len(observers), len(edges))
    return result


def _snapshot_input(raw: InputSnapshot) -> InputSnapshot:
    """Validate and copy one upstream-stage-bound input."""
    logger.debug("snapshot input entry")
    exact_shape(raw, InputSnapshot, "input")
    exact_text(raw.input_id, "input-id")
    exact_text(raw.type_id, "input-type")
    if type(raw.payload) is not bytes:
        reject("input-payload-invalid")
    exact_digest(raw.stage_commitment, "input-stage-commitment")
    exact_digest(raw.commitment, "input-commitment")
    from .digest import input_digest

    expected = input_digest(raw.input_id, raw.type_id, raw.payload)
    if raw.commitment != expected:
        reject("input-canonical-commitment-mismatch")
    result = InputSnapshot(raw.input_id, raw.type_id, bytes(raw.payload), raw.stage_commitment, expected)
    logger.debug("snapshot input exit")
    return result


def _snapshot_demand(raw: TriangleDemand, edges) -> TriangleDemand:
    """Validate one closed composable direct-versus-indirect demand."""
    logger.debug("snapshot demand entry")
    exact_shape(raw, TriangleDemand, "triangle-demand")
    if (
        raw.direct_edge_id not in edges
        or type(raw.indirect_edge_ids) is not tuple
        or len(raw.indirect_edge_ids) < 2
        or any(x not in edges for x in raw.indirect_edge_ids)
    ):
        reject("triangle-edge-not-closed")
    path = tuple(edges[x] for x in raw.indirect_edge_ids)
    direct = edges[raw.direct_edge_id]
    if (
        direct.source_observer_id != path[0].source_observer_id
        or direct.target_observer_id != path[-1].target_observer_id
        or any(a.target_observer_id != b.source_observer_id for a, b in zip(path, path[1:]))
    ):
        reject("triangle-path-not-composable")
    result = TriangleDemand(raw.demand_id, raw.direct_edge_id, raw.indirect_edge_ids)
    logger.debug("snapshot demand exit")
    return result
