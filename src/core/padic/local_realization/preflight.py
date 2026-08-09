"""Raw-shape hard-first resource preflight for isolated P3-N3/N4."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from ..completion.types import (
    PadicCompletionLedger, PadicCompletionLedgerRow, PadicCompletionPackage,
    PadicCompletionPolicy, PadicCompletionTheoremSource, PadicLedgerRowClass,
    PadicTowerDoctrine, PrimeSource,
)
from ..family_introduction.types import (
    IntegerSource, N1AssumptionLedger, N1IntroductionPackage, N1Policy, N1TheoremSource,
)
from .common import exact_digest, exact_shape, reject
from .formal import _instance
from .sources import (
    ARTIFACT_PATH, HARD_CAPTURED, HARD_STATIC, N1_PATH, P2_PATH, PREMISE_PATH,
    theorem_source,
)
from .types import (
    AllDepthCoordinateEqualitySource, BridgeDependencyRow, FailedBound, N34Policy,
    N34TheoremSource, N3Request, N4Request,
)

logger = logging.getLogger(__name__)
_POLICY_FIELDS = ("max_captured_bytes", "max_static_cost", "max_ledger_rows",
                  "max_ledger_edges", "timeout_seconds", "max_output_bytes")


@dataclass(frozen=True)
class RawCharge:
    captured_bytes: int
    static_cost: int
    ledger_rows: int
    ledger_edges: int


def _tuple(value: object, expected: int, label: str) -> tuple:
    """Require an exact tuple and fixed count before iteration."""
    logger.debug("_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) != expected:
        reject(f"{label}-exact-count-required")
    logger.debug("_tuple exit label=%s", label)
    return value


def _text(value: object, label: str, cap: int = 512) -> str:
    """Bound one exact UTF-8 text field before semantic reconstruction."""
    logger.debug("_text entry label=%s", label)
    if type(value) is not str or len(value) > cap or len(value.encode()) > cap:
        reject(f"{label}-text-envelope-invalid")
    logger.debug("_text exit label=%s", label)
    return value


def _direct_text(raw: dict[str, object], label: str) -> None:
    """Bound every direct string in one already exact-shaped record."""
    logger.debug("_direct_text entry label=%s", label)
    for name, value in raw.items():
        if type(value) is str:
            _text(value, f"{label}-{name}")
    logger.debug("_direct_text exit label=%s", label)


def _policy(value: object) -> N34Policy:
    """Validate the exact policy without package reconstruction."""
    logger.debug("_policy entry")
    raw = exact_shape(value, N34Policy, "n34-policy")
    from .sources import policy
    result = policy(*(raw[name] for name in _POLICY_FIELDS))
    if value != result:
        reject("n34-policy-drift")
    logger.debug("_policy exit")
    return result


def _prime(value: object) -> int:
    """Bound exact raw prime witness bytes before any snapshot."""
    logger.debug("_prime entry")
    raw = exact_shape(value, PrimeSource, "prime-source")
    _direct_text(raw, "prime-source")
    witness = raw["generated_witness_bytes"]
    if type(witness) is not bytes or len(witness) > 2 * 1024 * 1024:
        reject("prime-witness-envelope-invalid")
    if type(raw["p"]) is not int or type(raw["p"]) is bool:
        reject("prime-value-exact-int-required")
    exact_digest(raw["generated_witness_sha256"], "prime-witness-sha")
    exact_digest(raw["source_digest"], "prime-source-digest")
    logger.debug("_prime exit bytes=%d", len(witness))
    return len(witness)


def _n1(value: object) -> tuple[int, int, int]:
    """Bound one exact N1 package's raw ledger without replay."""
    logger.debug("_n1 entry")
    raw = exact_shape(value, N1IntroductionPackage, "n1-package")
    witness = _prime(raw["prime"])
    integer = exact_shape(raw["integer"], IntegerSource, "n1-integer")
    _direct_text(integer, "n1-integer")
    doctrine = exact_shape(raw["doctrine"], PadicTowerDoctrine, "n1-doctrine")
    _direct_text(doctrine, "n1-doctrine")
    theorem = exact_shape(raw["theorem_source"], N1TheoremSource, "n1-theorem-source")
    _direct_text(theorem, "n1-theorem-source")
    theorem_ids = _tuple(theorem["theorem_ids"], 3, "n1-theorem-ids")
    for item in theorem_ids:
        _text(item, "n1-theorem-id", 256)
    n1_policy = exact_shape(raw["policy"], N1Policy, "n1-policy")
    _direct_text(n1_policy, "n1-policy")
    if type(integer.get("z")) is not int or type(integer["z"]) is bool or integer["z"].bit_length() > 4096:
        reject("n1-integer-envelope-invalid")
    ledger = exact_shape(raw["ledger"], N1AssumptionLedger, "n1-ledger")
    rows = _tuple(ledger["ordered_rows"], 20, "n1-ledger-rows")
    edges = _tuple(ledger["direct_edges"], 32, "n1-ledger-edges")
    closure = _tuple(ledger["theorem_axiom_closure"], 1, "n1-ledger-closure")
    for row in rows:
        _text(row, "n1-ledger-row", 256)
    if any(type(edge) is not tuple or len(edge) != 2 for edge in edges):
        reject("n1-ledger-edge-envelope-invalid")
    for edge in edges:
        for item in edge:
            _text(item, "n1-ledger-edge", 256)
    for item in closure:
        _text(item, "n1-ledger-closure", 256)
    exact_digest(raw["package_digest"], "n1-package-digest")
    logger.debug("_n1 exit")
    return witness, len(rows), len(edges)


def _p2(value: object) -> tuple[int, int, int]:
    """Bound one exact PΩ2 package's raw ledger without replay."""
    logger.debug("_p2 entry")
    raw = exact_shape(value, PadicCompletionPackage, "pomega2-package")
    witness = _prime(raw["prime"])
    doctrine = exact_shape(raw["doctrine"], PadicTowerDoctrine, "pomega2-doctrine")
    _direct_text(doctrine, "pomega2-doctrine")
    theorem = exact_shape(raw["theorem_source"], PadicCompletionTheoremSource,
                          "pomega2-theorem-source")
    _direct_text(theorem, "pomega2-theorem-source")
    theorem_ids = _tuple(theorem["theorem_ids"], 17, "pomega2-theorem-ids")
    for item in theorem_ids:
        _text(item, "pomega2-theorem-id", 256)
    p2_policy = exact_shape(raw["policy"], PadicCompletionPolicy, "pomega2-policy")
    _direct_text(p2_policy, "pomega2-policy")
    ledger = exact_shape(raw["ledger"], PadicCompletionLedger, "pomega2-ledger")
    rows = _tuple(ledger["rows"], 45, "pomega2-ledger-rows")
    _tuple(ledger["theorem_axiom_closure"], 2, "pomega2-ledger-closure")
    edges = 0
    for row in rows:
        data = exact_shape(row, PadicCompletionLedgerRow, "pomega2-ledger-row")
        if type(data["row_class"]) is not PadicLedgerRowClass:
            reject("pomega2-row-class-exact-enum-required")
        dependencies = data["direct_dependencies"]
        if type(dependencies) is not tuple or len(dependencies) > 32:
            reject("pomega2-row-dependencies-envelope-invalid")
        closure = data["axiom_closure"]
        if type(closure) is not tuple or len(closure) > 4:
            reject("pomega2-row-closure-envelope-invalid")
        _direct_text(data, "pomega2-row")
        for item in (*dependencies, *closure):
            _text(item, "pomega2-row-item", 256)
        edges += len(dependencies)
    if edges != 68:
        reject("pomega2-ledger-exact-edge-count-required")
    exact_digest(raw["package_digest"], "pomega2-package-digest")
    logger.debug("_p2 exit")
    return witness, len(rows), edges


def _premise(value: object) -> tuple[int, int]:
    """Bound the owned all-depth graph before semantic reconstruction."""
    logger.debug("_premise entry")
    raw = exact_shape(value, AllDepthCoordinateEqualitySource, "all-depth-source")
    _direct_text(raw, "all-depth-source")
    theorem_ids = _tuple(raw["theorem_ids"], 1, "all-depth-theorems")
    imports = _tuple(raw["imports"], 3, "all-depth-imports")
    for item in theorem_ids:
        _text(item, "all-depth-theorem", 256)
    if any(type(item) is not tuple or len(item) != 2 for item in imports):
        reject("all-depth-import-shape-invalid")
    for item in imports:
        for text in item:
            _text(text, "all-depth-import")
    rows = _tuple(raw["ordered_rows"], 34, "all-depth-rows")
    edges = 0
    for row in rows:
        data = exact_shape(row, BridgeDependencyRow, "all-depth-row")
        dependencies = data["direct_dependencies"]
        if type(dependencies) is not tuple or len(dependencies) > 8:
            reject("all-depth-row-dependencies-envelope-invalid")
        if type(data["axiom_closure"]) is not tuple or len(data["axiom_closure"]) > 4:
            reject("all-depth-row-closure-envelope-invalid")
        _direct_text(data, "all-depth-row")
        for item in (*dependencies, *data["axiom_closure"]):
            _text(item, "all-depth-row-item", 256)
        edges += len(dependencies)
    if edges != 49:
        reject("all-depth-exact-edge-count-required")
    exact_digest(raw["source_digest"], "all-depth-source-digest")
    logger.debug("_premise exit")
    return len(rows), edges


def _source_bytes(n4: bool, instance_bytes: int) -> int:
    """Charge pinned source sizes by metadata, never by reading source bodies."""
    logger.debug("_source_bytes entry n4=%s", n4)
    paths = (P2_PATH, N1_PATH, ARTIFACT_PATH, *((PREMISE_PATH,) if n4 else ()))
    total = instance_bytes
    try:
        for path in paths:
            size = Path(path).stat().st_size
            if size > 2 * 1024 * 1024:
                reject("formal-source-drift-or-too-large")
            total += size
    except OSError:
        reject("formal-source-unavailable")
    logger.debug("_source_bytes exit bytes=%d", total)
    return total


def raw_request_preflight(value: object) -> tuple[dict[str, object], RawCharge,
                                                  tuple[FailedBound, int, int] | None]:
    """Apply exact raw envelopes and first-bound refusal before all deep work."""
    logger.debug("raw_request_preflight entry type=%s", type(value).__name__)
    if type(value) is N3Request:
        raw = exact_shape(value, N3Request, "n3-request")
        _, n1_rows, n1_edges = _n1(raw["n1"])
        witness, p2_rows, p2_edges = _p2(raw["pomega2"])
        minimal_rows, minimal_edges, extra_rows, extra_edges = 31, 45, 0, 0
        n4 = False
    elif type(value) is N4Request:
        raw = exact_shape(value, N4Request, "n4-request")
        _, left_rows, left_edges = _n1(raw["left_n1"])
        _, right_rows, right_edges = _n1(raw["right_n1"])
        witness, p2_rows, p2_edges = _p2(raw["pomega2"])
        extra_rows, extra_edges = _premise(raw["all_depth"])
        n1_rows, n1_edges = left_rows + right_rows, left_edges + right_edges
        minimal_rows, minimal_edges, n4 = 108, 155, True
    else:
        reject("n34-request-exact-type-required")
    theorem = raw["theorem"]
    theorem_raw = exact_shape(theorem, N34TheoremSource, "n34-theorem-source")
    _direct_text(theorem_raw, "n34-theorem-source")
    theorem_ids = _tuple(theorem_raw["theorem_ids"], 3, "n34-theorem-ids")
    for item in theorem_ids:
        _text(item, "n34-theorem-id", 256)
    imports = _tuple(theorem_raw["imports"], 2, "n34-theorem-imports")
    if any(type(item) is not tuple or len(item) != 2 for item in imports):
        reject("n34-theorem-import-shape-invalid")
    for item in imports:
        for text in item:
            _text(text, "n34-theorem-import")
    if theorem != theorem_source():
        reject("n34-theorem-source-drift")
    execution = _policy(raw["policy"])
    exact_digest(raw["request_digest"], "n34-request-digest")
    captured = _source_bytes(n4, len(_instance(value))) + witness
    raw_rows, raw_edges = n1_rows + p2_rows + extra_rows, n1_edges + p2_edges + extra_edges
    static = captured + 256 * (raw_rows + minimal_rows) + 64 * (raw_edges + minimal_edges)
    charge = RawCharge(captured, static, minimal_rows, minimal_edges)
    if captured > HARD_CAPTURED or static > HARD_STATIC or minimal_rows > 256 or minimal_edges > 512:
        reject("hard-resource-envelope")
    kinds = (FailedBound.CAPTURED_BYTES, FailedBound.STATIC_COST,
             FailedBound.LEDGER_ROWS, FailedBound.LEDGER_EDGES)
    required = (captured, static, minimal_rows, minimal_edges)
    allowed = (execution.max_captured_bytes, execution.max_static_cost,
               execution.max_ledger_rows, execution.max_ledger_edges)
    failure = next(((kind, need, cap) for kind, need, cap in
                    zip(kinds, required, allowed, strict=True) if need > cap), None)
    logger.debug("raw_request_preflight exit failure=%s", failure is not None)
    return raw, charge, failure
