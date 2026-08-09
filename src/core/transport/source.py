"""Exact finite setoid carriers and total edge transports for P3-C2."""

from __future__ import annotations
import logging
from ..confluence.generated.source import snapshot_ranked_system
from ..confluence.generated.types import RankedContinuationSystem
from .common import digest, exact_digest, exact_shape, exact_text, reject
from .types import (
    EdgeTransportMap,
    SetoidClassRow,
    StateSetoidCarrier,
    TotalTransportDoctrine,
    TransportMapEntry,
    TransportValue,
)

logger = logging.getLogger(__name__)
DOCTRINE_VERSION = "p3-c2-total-setoid-transport-v1"
P3T_GATE = "gated-unreleased-no-adapter"
IDENTITY_LAW = "typed-setoid-identity-pointwise-v1"
COMPOSITION_LAW = "edge-derived-path-composition-pointwise-v1"
RESPECT_LAW = "total-edge-map-setoid-respect-v1"
HARD_VALUES = 4096
HARD_MAP_ENTRIES = 16384
HARD_CANONICAL_BYTES = 2 * 1024 * 1024


def _rows(name: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Frame an ordered string tuple."""
    logger.debug("_rows entry name=%s count=%d", name, len(values))
    result = tuple((f"{name}-{i}", x.encode()) for i, x in enumerate(values))
    logger.debug("_rows exit")
    return result


def transport_value(state_id: str, value_id: str, payload: bytes) -> TransportValue:
    """Construct one exact typed carrier value."""
    logger.debug("transport_value entry")
    exact_text(state_id, "value-state")
    exact_text(value_id, "value-id")
    if type(payload) is not bytes or len(payload) > 65536:
        reject("value-payload-invalid")
    commitment = digest(
        "veyra.p3c2.value.v1", (("state", state_id.encode()), ("id", value_id.encode()), ("payload", payload))
    )
    result = TransportValue(state_id, value_id, bytes(payload), commitment)
    logger.debug("transport_value exit id=%s", value_id)
    return result


def state_setoid_carrier(
    state_id: str, state_commitment: str, values: tuple[TransportValue, ...], classes: tuple[SetoidClassRow, ...]
) -> StateSetoidCarrier:
    """Construct one complete finite setoid partition."""
    logger.debug("state_setoid_carrier entry")
    exact_text(state_id, "carrier-state")
    exact_digest(state_commitment, "carrier-state-commitment")
    if type(values) is not tuple or type(classes) is not tuple:
        reject("carrier-container-invalid")
    if len(values) > HARD_VALUES:
        reject("carrier-value-hard-limit")
    values = tuple(sorted((_snapshot_value(x) for x in values), key=lambda x: x.value_id))
    classes = tuple(sorted((_snapshot_class(x) for x in classes), key=lambda x: x.value_id))
    ids = tuple(x.value_id for x in values)
    if not ids or len(set(ids)) != len(ids) or tuple(x.value_id for x in classes) != ids:
        reject("carrier-class-domain-not-exact")
    if any(x.state_id != state_id for x in values):
        reject("carrier-value-state-mismatch")
    value = digest(
        "veyra.p3c2.carrier.v1",
        (
            ("state", state_id.encode()),
            ("commitment", state_commitment.encode()),
            *_rows("value", tuple(x.value_commitment for x in values)),
            *_rows("class", tuple(f"{x.value_id}\0{x.class_id}" for x in classes)),
        ),
    )
    result = StateSetoidCarrier(state_id, state_commitment, values, classes, value)
    logger.debug("state_setoid_carrier exit values=%d", len(values))
    return result


def edge_transport_map(
    edge_id: str,
    edge_commitment: str,
    source: StateSetoidCarrier,
    target: StateSetoidCarrier,
    entries: tuple[TransportMapEntry, ...],
) -> EdgeTransportMap:
    """Construct one exact deterministic total table between typed carriers."""
    logger.debug("edge_transport_map entry")
    exact_text(edge_id, "map-edge")
    exact_digest(edge_commitment, "map-edge-commitment")
    source = _snapshot_carrier(source)
    target = _snapshot_carrier(target)
    if type(entries) is not tuple or len(entries) > HARD_MAP_ENTRIES:
        reject("map-entry-container-or-limit")
    entries = tuple(sorted((_snapshot_entry(x) for x in entries), key=lambda x: x.source_value_id))
    source_ids = tuple(x.value_id for x in source.values)
    target_ids = {x.value_id for x in target.values}
    if tuple(x.source_value_id for x in entries) != source_ids or any(
        x.target_value_id not in target_ids for x in entries
    ):
        reject("map-not-exact-total-typed")
    mapping = {x.source_value_id: x.target_value_id for x in entries}
    sc = {x.value_id: x.class_id for x in source.classes}
    tc = {x.value_id: x.class_id for x in target.classes}
    for left in source_ids:
        for right in source_ids:
            if sc[left] == sc[right] and tc[mapping[left]] != tc[mapping[right]]:
                reject("map-does-not-respect-setoid")
    value = digest(
        "veyra.p3c2.edge-map.v1",
        (
            ("edge", edge_id.encode()),
            ("edge-commitment", edge_commitment.encode()),
            ("source", source.carrier_digest.encode()),
            ("target", target.carrier_digest.encode()),
            *_rows("entry", tuple(f"{x.source_value_id}\0{x.target_value_id}" for x in entries)),
        ),
    )
    result = EdgeTransportMap(edge_id, edge_commitment, source.carrier_digest, target.carrier_digest, entries, value)
    logger.debug("edge_transport_map exit entries=%d", len(entries))
    return result


def total_transport_doctrine(
    system: RankedContinuationSystem,
    doctrine_id: str,
    carriers: tuple[StateSetoidCarrier, ...],
    edge_maps: tuple[EdgeTransportMap, ...],
) -> TotalTransportDoctrine:
    """Bind exact carriers and one total map per source edge occurrence."""
    logger.debug("total_transport_doctrine entry")
    system = snapshot_ranked_system(system)
    exact_text(doctrine_id, "transport-doctrine-id")
    if type(carriers) is not tuple or type(edge_maps) is not tuple:
        reject("transport-doctrine-containers-invalid")
    carriers = tuple(sorted((_snapshot_carrier(x) for x in carriers), key=lambda x: x.state_id))
    edge_maps = tuple(sorted((_snapshot_map(x) for x in edge_maps), key=lambda x: x.edge_id))
    states = {x.state_id: x for x in system.states}
    edges = {x.edge_id: x for x in system.edges}
    cmap = {x.state_id: x for x in carriers}
    if tuple(x.state_id for x in carriers) != tuple(sorted(states)) or tuple(x.edge_id for x in edge_maps) != tuple(
        sorted(edges)
    ):
        reject("transport-doctrine-domain-not-exact")
    if any(c.state_commitment != states[c.state_id].state_commitment for c in carriers):
        reject("carrier-state-transplant")
    for row in edge_maps:
        edge = edges[row.edge_id]
        if (
            row.edge_commitment != edge.edge_commitment
            or row.source_carrier_digest != cmap[edge.source_id].carrier_digest
            or row.target_carrier_digest != cmap[edge.target_id].carrier_digest
        ):
            reject("edge-map-transplant")
        rebuilt = edge_transport_map(
            row.edge_id, row.edge_commitment, cmap[edge.source_id], cmap[edge.target_id], row.entries
        )
        if row != rebuilt:
            reject("edge-map-semantic-drift")
    value = digest(
        "veyra.p3c2.doctrine.v1",
        (
            ("version", DOCTRINE_VERSION.encode()),
            ("id", doctrine_id.encode()),
            ("system", system.system_digest.encode()),
            *_rows("carrier", tuple(x.carrier_digest for x in carriers)),
            *_rows("map", tuple(x.map_digest for x in edge_maps)),
            ("identity", IDENTITY_LAW.encode()),
            ("composition", COMPOSITION_LAW.encode()),
            ("respect", RESPECT_LAW.encode()),
            ("p3t", P3T_GATE.encode()),
        ),
    )
    result = TotalTransportDoctrine(
        DOCTRINE_VERSION,
        doctrine_id,
        system.system_digest,
        carriers,
        edge_maps,
        IDENTITY_LAW,
        COMPOSITION_LAW,
        RESPECT_LAW,
        P3T_GATE,
        value,
    )
    _hard_preflight(result)
    logger.debug("total_transport_doctrine exit")
    return result


def snapshot_transport_doctrine(
    system: RankedContinuationSystem, raw: TotalTransportDoctrine
) -> TotalTransportDoctrine:
    """Hard-first snapshot one canonical doctrine and reject transplant/drift."""
    logger.debug("snapshot_transport_doctrine entry")
    exact_shape(raw, TotalTransportDoctrine, "transport-doctrine")
    _hard_preflight(raw)
    expected = total_transport_doctrine(system, raw.doctrine_id, raw.carriers, raw.edge_maps)
    if raw != expected:
        reject("transport-doctrine-drift")
    logger.debug("snapshot_transport_doctrine exit")
    return expected


def _hard_preflight(raw: TotalTransportDoctrine) -> None:
    """Charge nested counts and bytes without invoking hostile formatting hooks."""
    logger.debug("_hard_preflight entry")
    from .preflight import charge_raw_doctrine

    charge = charge_raw_doctrine(raw)
    if charge.values > HARD_VALUES or charge.map_entries > HARD_MAP_ENTRIES:
        reject("transport-doctrine-hard-count-limit")
    if charge.canonical_bytes > HARD_CANONICAL_BYTES:
        reject("transport-doctrine-hard-byte-limit")
    logger.debug(
        "_hard_preflight exit values=%d entries=%d bytes=%d",
        charge.values,
        charge.map_entries,
        charge.canonical_bytes,
    )


def _snapshot_value(raw: TransportValue) -> TransportValue:
    logger.debug("_snapshot_value entry")
    exact_shape(raw, TransportValue, "transport-value")
    expected = transport_value(raw.state_id, raw.value_id, raw.payload)
    if raw != expected:
        reject("transport-value-drift")
    logger.debug("_snapshot_value exit")
    return expected


def _snapshot_class(raw: SetoidClassRow) -> SetoidClassRow:
    logger.debug("_snapshot_class entry")
    exact_shape(raw, SetoidClassRow, "setoid-class")
    exact_text(raw.value_id, "class-value")
    exact_text(raw.class_id, "class-id")
    result = SetoidClassRow(raw.value_id, raw.class_id)
    logger.debug("_snapshot_class exit")
    return result


def _snapshot_entry(raw: TransportMapEntry) -> TransportMapEntry:
    logger.debug("_snapshot_entry entry")
    exact_shape(raw, TransportMapEntry, "transport-entry")
    exact_text(raw.source_value_id, "entry-source")
    exact_text(raw.target_value_id, "entry-target")
    result = TransportMapEntry(raw.source_value_id, raw.target_value_id)
    logger.debug("_snapshot_entry exit")
    return result


def _snapshot_carrier(raw: StateSetoidCarrier) -> StateSetoidCarrier:
    logger.debug("_snapshot_carrier entry")
    exact_shape(raw, StateSetoidCarrier, "setoid-carrier")
    expected = state_setoid_carrier(raw.state_id, raw.state_commitment, raw.values, raw.classes)
    if raw != expected:
        reject("setoid-carrier-drift")
    logger.debug("_snapshot_carrier exit")
    return expected


def _snapshot_map(raw: EdgeTransportMap) -> EdgeTransportMap:
    logger.debug("_snapshot_map entry")
    exact_shape(raw, EdgeTransportMap, "edge-transport-map")
    exact_text(raw.edge_id, "map-edge")
    exact_digest(raw.edge_commitment, "map-edge-commitment")
    exact_digest(raw.source_carrier_digest, "map-source")
    exact_digest(raw.target_carrier_digest, "map-target")
    exact_digest(raw.map_digest, "map-digest")
    if type(raw.entries) is not tuple or any(type(x) is not TransportMapEntry for x in raw.entries):
        reject("map-entries-invalid")
    entries = tuple(_snapshot_entry(x) for x in raw.entries)
    expected_digest = digest(
        "veyra.p3c2.edge-map.v1",
        (
            ("edge", raw.edge_id.encode()),
            ("edge-commitment", raw.edge_commitment.encode()),
            ("source", raw.source_carrier_digest.encode()),
            ("target", raw.target_carrier_digest.encode()),
            *_rows("entry", tuple(f"{x.source_value_id}\0{x.target_value_id}" for x in entries)),
        ),
    )
    if raw.entries != tuple(sorted(entries, key=lambda x: x.source_value_id)) or raw.map_digest != expected_digest:
        reject("edge-map-drift")
    logger.debug("_snapshot_map exit")
    return EdgeTransportMap(
        raw.edge_id, raw.edge_commitment, raw.source_carrier_digest, raw.target_carrier_digest, entries, raw.map_digest
    )
