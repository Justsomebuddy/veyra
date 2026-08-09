"""Hook-free atomic raw byte/count charging for P3-C2."""

from __future__ import annotations
from dataclasses import dataclass, fields
import logging
from ..confluence.generated.types import ContinuationEdge, ContinuationState, RankedContinuationSystem, StateRank
from .common import exact_shape, reject
from .types import (
    EdgeTransportMap,
    LocalCommutingFiller,
    SetoidClassRow,
    StateSetoidCarrier,
    TotalTransportDoctrine,
    TransportMapEntry,
    TransportAssumptionLedger,
    TransportPackage,
    TransportPolicy,
    TransportTheoremSource,
    TransportValue,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawCharge:
    values: int
    map_entries: int
    local_fillers: int
    canonical_bytes: int
    validation_nodes: int


def charge_raw_doctrine(raw: TotalTransportDoctrine) -> RawCharge:
    """Charge a doctrine without invoking nested repr/equality/user hooks."""
    logger.debug("charge_raw_doctrine entry")
    exact_shape(raw, TotalTransportDoctrine, "transport-doctrine")
    carriers = object.__getattribute__(raw, "carriers")
    maps = object.__getattribute__(raw, "edge_maps")
    if type(carriers) is not tuple or type(maps) is not tuple:
        reject("transport-doctrine-containers-invalid")
    if len(carriers) > 64 or len(maps) > 128:
        reject("transport-doctrine-outer-hard-limit")
    size = _fields_size(raw, TotalTransportDoctrine, {"carriers", "edge_maps"})
    value_count = 0
    entry_count = 0
    for carrier in carriers:
        exact_shape(carrier, StateSetoidCarrier, "setoid-carrier")
        values = object.__getattribute__(carrier, "values")
        classes = object.__getattribute__(carrier, "classes")
        if type(values) is not tuple or type(classes) is not tuple:
            reject("carrier-container-invalid")
        if len(values) > 4096 or len(classes) > 4096 or value_count + len(values) > 4096:
            reject("carrier-raw-hard-limit")
        size += _fields_size(carrier, StateSetoidCarrier, {"values", "classes"})
        value_count += len(values)
        for value in values:
            exact_shape(value, TransportValue, "transport-value")
            size += _fields_size(value, TransportValue, set())
        for row in classes:
            exact_shape(row, SetoidClassRow, "setoid-class")
            size += _fields_size(row, SetoidClassRow, set())
    for edge_map in maps:
        exact_shape(edge_map, EdgeTransportMap, "edge-map")
        entries = object.__getattribute__(edge_map, "entries")
        if type(entries) is not tuple:
            reject("map-entries-invalid")
        if len(entries) > 16384 or entry_count + len(entries) > 16384:
            reject("map-entry-raw-hard-limit")
        size += _fields_size(edge_map, EdgeTransportMap, {"entries"})
        entry_count += len(entries)
        for row in entries:
            exact_shape(row, TransportMapEntry, "map-entry")
            size += _fields_size(row, TransportMapEntry, set())
    nodes = len(carriers) + len(maps) + value_count + entry_count + sum(len(x.classes) for x in carriers)
    result = RawCharge(value_count, entry_count, 0, size, nodes)
    logger.debug("charge_raw_doctrine exit values=%d entries=%d bytes=%d", value_count, entry_count, size)
    return result


def charge_raw_package(raw: TransportPackage) -> RawCharge:
    """Atomically charge system, doctrine, fillers, theorem, policy, and digest."""
    logger.debug("charge_raw_package entry")
    exact_shape(raw, TransportPackage, "transport-package")
    system = object.__getattribute__(raw, "system")
    doctrine = object.__getattribute__(raw, "doctrine")
    fillers = object.__getattribute__(raw, "local_fillers")
    theorem = object.__getattribute__(raw, "theorem_source")
    ledger = object.__getattribute__(raw, "assumption_ledger")
    policy = object.__getattribute__(raw, "policy")
    exact_shape(policy, TransportPolicy, "transport-policy")
    policy_bounds = tuple(
        object.__getattribute__(policy, name)
        for name in (
            "max_values",
            "max_map_entries",
            "max_local_fillers",
            "max_generated_paths",
            "max_semantic_work",
            "max_canonical_bytes",
            "compile_timeout_seconds",
            "max_output_bytes",
        )
    )
    maxima = (4096, 16384, 16384, 16384, 10**12, 2 * 1024 * 1024, 300, 4 * 1024 * 1024)
    if any(type(x) is not int for x in policy_bounds) or any(
        not 1 <= value <= maximum for value, maximum in zip(policy_bounds, maxima, strict=True)
    ):
        reject("transport-policy-bound-invalid")
    _charge_system(system)
    dcharge = charge_raw_doctrine(doctrine)
    if type(fillers) is not tuple:
        reject("local-fillers-container-invalid")
    if len(fillers) > 16384:
        reject("local-fillers-raw-hard-limit")
    size = dcharge.canonical_bytes + _system_size(system) + _atom_size(object.__getattribute__(raw, "package_digest"))
    for filler in fillers:
        exact_shape(filler, LocalCommutingFiller, "local-filler")
        size += _fields_size(filler, LocalCommutingFiller, {"left_path", "right_path"})
        size += _string_tuple_size(object.__getattribute__(filler, "left_path"), "local-left-path")
        size += _string_tuple_size(object.__getattribute__(filler, "right_path"), "local-right-path")
    exact_shape(theorem, TransportTheoremSource, "transport-theorem-source")
    theorem_ids = object.__getattribute__(theorem, "theorem_ids")
    if type(theorem_ids) is not tuple or len(theorem_ids) > 16:
        reject("theorem-ids-raw-hard-limit")
    size += _fields_size(theorem, TransportTheoremSource, {"theorem_ids"}) + _string_tuple_size(
        theorem_ids, "theorem-ids"
    )
    exact_shape(ledger, TransportAssumptionLedger, "transport-ledger")
    if (
        type(object.__getattribute__(ledger, "ordered_rows")) is not tuple
        or type(object.__getattribute__(ledger, "direct_edges")) is not tuple
        or type(object.__getattribute__(ledger, "theorem_axiom_closure")) is not tuple
        or len(object.__getattribute__(ledger, "ordered_rows")) > 256
        or len(object.__getattribute__(ledger, "direct_edges")) > 1024
        or len(object.__getattribute__(ledger, "theorem_axiom_closure")) > 256
    ):
        reject("transport-ledger-raw-hard-limit")
    size += _fields_size(
        ledger,
        TransportAssumptionLedger,
        {"ordered_rows", "direct_edges", "theorem_axiom_closure"},
    )
    size += _string_tuple_size(object.__getattribute__(ledger, "ordered_rows"), "ledger-rows")
    size += _string_tuple_size(object.__getattribute__(ledger, "theorem_axiom_closure"), "ledger-axioms")
    edges = object.__getattribute__(ledger, "direct_edges")
    if type(edges) is not tuple or any(type(edge) is not tuple or len(edge) != 2 for edge in edges):
        reject("ledger-edges-invalid")
    for edge in edges:
        size += _string_tuple_size(edge, "ledger-edge")
    exact_shape(policy, TransportPolicy, "transport-policy")
    size += _fields_size(policy, TransportPolicy, set())
    nodes = dcharge.validation_nodes + len(fillers) + len(system.states) + len(system.edges) + len(system.ranks)
    result = RawCharge(dcharge.values, dcharge.map_entries, len(fillers), size, nodes)
    logger.debug("charge_raw_package exit bytes=%d", size)
    return result


def _charge_system(raw: RankedContinuationSystem) -> None:
    """Validate only safe raw shapes/types needed for system byte charging."""
    logger.debug("_charge_system entry")
    exact_shape(raw, RankedContinuationSystem, "ranked-system")
    maxima = {"states": 64, "edges": 128, "ranks": 64}
    for name, cls in (("states", ContinuationState), ("edges", ContinuationEdge), ("ranks", StateRank)):
        rows = object.__getattribute__(raw, name)
        if type(rows) is not tuple or len(rows) > maxima[name] or any(type(x) is not cls for x in rows):
            reject("ranked-system-member-shape-invalid")
        for row in rows:
            _fields_size(row, cls, set())
    roots = object.__getattribute__(raw, "roots")
    if type(roots) is not tuple or len(roots) > 64:
        reject("ranked-system-roots-hard-limit")
    _string_tuple_size(roots, "roots")
    _fields_size(raw, RankedContinuationSystem, {"states", "edges", "ranks", "roots"})
    logger.debug("_charge_system exit")


def _system_size(raw: RankedContinuationSystem) -> int:
    """Return size after `_charge_system` has established exact primitive fields."""
    logger.debug("_system_size entry")
    size = _fields_size(raw, RankedContinuationSystem, {"states", "edges", "ranks", "roots"}) + _string_tuple_size(
        raw.roots, "roots"
    )
    for name, cls in (("states", ContinuationState), ("edges", ContinuationEdge), ("ranks", StateRank)):
        size += sum(_fields_size(x, cls, set()) for x in object.__getattribute__(raw, name))
    logger.debug("_system_size exit bytes=%d", size)
    return size


def _fields_size(raw: object, cls: type, skip: set[str]) -> int:
    """Charge exact dataclass primitive fields without formatting values."""
    logger.debug("_fields_size entry cls=%s", cls.__name__)
    exact_shape(raw, cls, cls.__name__)
    size = 0
    for field in fields(cls):
        name = field.name
        if name not in skip:
            size += _atom_size(object.__getattribute__(raw, name))
    logger.debug("_fields_size exit bytes=%d", size)
    return size


def _atom_size(value: object) -> int:
    """Charge only exact immutable scalar atoms."""
    logger.debug("_atom_size entry type=%s", type(value).__name__)
    if type(value) is str:
        result = len(value.encode("utf-8"))
    elif type(value) is bytes:
        result = len(value)
    elif type(value) is int:
        result = 8
    else:
        reject("raw-charge-nonprimitive-field")
    logger.debug("_atom_size exit bytes=%d", result)
    return result


def _string_tuple_size(value: object, label: str) -> int:
    """Charge one exact tuple of plain strings."""
    logger.debug("_string_tuple_size entry label=%s", label)
    if type(value) is not tuple or any(type(x) is not str for x in value):
        reject(f"{label}-invalid")
    result = sum(len(x.encode("utf-8")) for x in value)
    logger.debug("_string_tuple_size exit bytes=%d", result)
    return result
