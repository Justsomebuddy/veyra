"""Pure non-authoritative graph-first preflight for candidate P3-N6 requests."""

from __future__ import annotations

from enum import Enum
import logging

from .padic.completion.types import (
    PadicCompletionLedger, PadicCompletionLedgerRow, PadicCompletionPackage,
    PadicCompletionPolicy, PadicCompletionTheoremSource, PadicTowerDoctrine,
    PrimeSource,
)
from .padic.family_introduction.types import (
    IntegerSource, N1AssumptionLedger, N1IntroductionPackage, N1Policy,
    N1TheoremSource,
)
from .prime_power_unbounded_common import (
    FrozenLayoutV1, exact_shape, freeze_layout, reject,
)
from .prime_power_unbounded_sources import (
    HARD_CAPTURED_BYTES, HARD_LEDGER_EDGES, HARD_LEDGER_ROWS, HARD_STATIC_COST,
)
from .prime_power_unbounded_types import (
    N6ERawRequestV1, N6PolicyV1, N6PrechargeV1, N6TheoremSourceV1,
    N6_E_RAW_REQUEST_LAYOUT, N6_POLICY_LAYOUT, N6_THEOREM_SOURCE_LAYOUT,
)

logger = logging.getLogger(__name__)
_DEFAULT_DESCRIPTOR_CHARGE = 16 * 1024


def _layout(kind: type, names: tuple[str, ...]) -> tuple[type, FrozenLayoutV1]:
    logger.debug("_layout entry fields=%d", len(names))
    result = kind, freeze_layout(kind, names)
    logger.debug("_layout exit fields=%d", len(names))
    return result


_RAW_LAYOUTS = (
    (N6ERawRequestV1, N6_E_RAW_REQUEST_LAYOUT),
    (N6TheoremSourceV1, N6_THEOREM_SOURCE_LAYOUT),
    (N6PolicyV1, N6_POLICY_LAYOUT),
    _layout(PadicCompletionPackage, (
        "prime", "doctrine", "theorem_source", "ledger", "policy", "package_digest",
    )),
    _layout(PadicCompletionPolicy, (
        "version", "max_captured_bytes", "max_static_cost", "compile_timeout_seconds",
        "max_output_bytes", "policy_digest",
    )),
    _layout(PadicCompletionLedger, (
        "version", "rows", "theorem_axiom_closure", "ledger_digest",
    )),
    _layout(PadicCompletionLedgerRow, (
        "row_id", "row_class", "direct_dependencies", "use", "source_digest",
        "axiom_closure",
    )),
    _layout(PadicCompletionTheoremSource, (
        "version", "artifact_path_id", "artifact_sha256", "theorem_ids",
        "representation_id", "canonical_ops_id", "concrete_instance_id",
        "toolchain_id", "tcb_digest", "source_digest",
    )),
    _layout(PadicTowerDoctrine, (
        "version", "doctrine_id", "index_id", "stage_id", "modulus_id",
        "reduction_id", "family_class_id", "carrier_id", "equality_id", "ring_id",
        "ppcp_rule_id", "doctrine_digest",
    )),
    _layout(PrimeSource, (
        "version", "p", "witness_algorithm_id", "generated_witness_bytes",
        "generated_witness_sha256", "source_digest",
    )),
    _layout(N1IntroductionPackage, (
        "prime", "integer", "doctrine", "theorem_source", "ledger", "policy",
        "package_digest",
    )),
    _layout(N1Policy, (
        "version", "max_captured_bytes", "max_static_cost", "compile_timeout_seconds",
        "max_output_bytes", "policy_digest",
    )),
    _layout(N1AssumptionLedger, (
        "version", "ordered_rows", "direct_edges", "theorem_axiom_closure",
        "ledger_digest",
    )),
    _layout(N1TheoremSource, (
        "version", "artifact_path_id", "artifact_sha256", "pomega2_artifact_path_id",
        "pomega2_artifact_sha256", "theorem_ids", "family_definition_id",
        "coordinate_definition_id", "toolchain_id", "tcb_digest", "source_digest",
    )),
    _layout(IntegerSource, ("version", "z", "representation_id", "source_digest")),
)


def _known_layout(value: object) -> FrozenLayoutV1 | None:
    logger.debug("_known_layout entry")
    for kind, layout in _RAW_LAYOUTS:
        if type(value) is kind:
            logger.debug("_known_layout exit found=true")
            return layout
    logger.debug("_known_layout exit found=false")
    return None


def _graph_n1(package: object) -> tuple[int, int]:
    logger.debug("_graph_n1 entry")
    raw_package = exact_shape(package, _RAW_LAYOUTS[10][1], "n6-preflight-n1-package")
    raw_ledger = exact_shape(
        raw_package["ledger"], _RAW_LAYOUTS[12][1], "n6-preflight-n1-ledger"
    )
    rows, edges = raw_ledger["ordered_rows"], raw_ledger["direct_edges"]
    if type(rows) is not tuple or len(rows) > HARD_LEDGER_ROWS:
        reject("n6-preflight-n1-rows-hard-cap")
    if type(edges) is not tuple or len(edges) > HARD_LEDGER_EDGES:
        reject("n6-preflight-n1-edges-hard-cap")
    if any(type(row) is not str for row in rows):
        reject("n6-preflight-n1-row-type-invalid")
    for edge in edges:
        if (type(edge) is not tuple or len(edge) != 2
                or type(edge[0]) is not str or type(edge[1]) is not str):
            reject("n6-preflight-n1-edge-value-invalid")
    result = len(rows), len(edges)
    logger.debug("_graph_n1 exit rows=%d edges=%d", *result)
    return result


def _graph_p2(package: object) -> tuple[int, int]:
    logger.debug("_graph_p2 entry")
    raw_package = exact_shape(package, _RAW_LAYOUTS[3][1], "n6-preflight-pomega2-package")
    raw_ledger = exact_shape(
        raw_package["ledger"], _RAW_LAYOUTS[5][1], "n6-preflight-pomega2-ledger"
    )
    rows = raw_ledger["rows"]
    if type(rows) is not tuple or len(rows) > HARD_LEDGER_ROWS:
        reject("n6-preflight-pomega2-rows-hard-cap")
    edges = 0
    for row in rows:
        raw_row = exact_shape(row, _RAW_LAYOUTS[6][1], "n6-preflight-pomega2-row")
        dependencies = raw_row["direct_dependencies"]
        if type(dependencies) is not tuple or len(dependencies) > HARD_LEDGER_EDGES:
            reject("n6-preflight-pomega2-row-edges-hard-cap")
        if any(type(item) is not str for item in dependencies):
            reject("n6-preflight-pomega2-edge-value-invalid")
        edges += len(dependencies)
        if edges > HARD_LEDGER_EDGES:
            reject("n6-preflight-pomega2-edges-hard-cap")
    result = len(rows), edges
    logger.debug("_graph_p2 exit rows=%d edges=%d", *result)
    return result


def _declared_bytes(root: object) -> int:
    logger.debug("_declared_bytes entry")
    nodes, total = 0, 0
    stack: list[tuple[object, int]] = [(root, 0)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 8192 or depth > 16:
            reject("n6-preflight-raw-shape-hard-cap")
        if item is None or type(item) in (int, bool) or isinstance(item, Enum):
            total += 8
        elif type(item) is bytes:
            if len(item) > HARD_CAPTURED_BYTES:
                reject("n6-preflight-raw-bytes-hard-cap")
            total += len(item)
        elif type(item) is str:
            if len(item) > HARD_CAPTURED_BYTES // 4:
                reject("n6-preflight-raw-text-hard-cap")
            try:
                total += len(item.encode("utf-8", "strict"))
            except UnicodeError:
                reject("n6-preflight-raw-text-invalid")
        elif type(item) is tuple:
            if len(item) > HARD_LEDGER_EDGES:
                reject("n6-preflight-raw-tuple-hard-cap")
            total += 8
            stack.extend((child, depth + 1) for child in reversed(item))
        else:
            layout = _known_layout(item)
            if layout is None:
                reject("n6-preflight-raw-type-invalid")
            raw_item = exact_shape(item, layout, "n6-preflight-raw-dataclass")
            total += 8
            stack.extend((raw_item[name], depth + 1) for name, _ in reversed(layout.fields))
        if total > HARD_CAPTURED_BYTES:
            reject("n6-preflight-raw-declared-hard-cap")
    logger.debug("_declared_bytes exit nodes=%d bytes=%d", nodes, total)
    return total


def preflight_e_request(value: N6ERawRequestV1) -> N6PrechargeV1:
    """Count hard graph and bytes before source/default/hash; never grant authority."""
    logger.debug("preflight_e_request entry")
    raw = exact_shape(value, N6_E_RAW_REQUEST_LAYOUT, "n6-preflight-e-raw-request")
    n1_rows, n1_edges = _graph_n1(raw["n1_zero"])
    p2_rows, p2_edges = _graph_p2(raw["pomega2"])
    rows, edges = n1_rows + p2_rows, n1_edges + p2_edges
    if rows > HARD_LEDGER_ROWS or edges > HARD_LEDGER_EDGES:
        reject("n6-preflight-total-graph-hard-cap")
    captured = _declared_bytes(value)
    captured += (int(raw["theorem"] is None) + int(raw["policy"] is None)) * _DEFAULT_DESCRIPTOR_CHARGE
    static_cost = captured + 256 * rows + 64 * edges
    if captured > HARD_CAPTURED_BYTES:
        reject("n6-preflight-captured-hard-cap")
    if static_cost > HARD_STATIC_COST:
        reject("n6-preflight-static-hard-cap")
    result = N6PrechargeV1(captured, static_cost, rows, edges)
    logger.debug("preflight_e_request exit bytes=%d rows=%d edges=%d", captured, rows, edges)
    return result
