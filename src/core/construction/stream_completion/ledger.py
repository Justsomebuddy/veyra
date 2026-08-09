"""Exact source-bound dependency DAG and compiler-derived axiom closure."""

from __future__ import annotations

import logging

from .alphabet import GENERATOR_CLOSURE_SHA256
from .common import exact_digest, exact_shape, reject
from .digest import digest, frame, texts
from .doctrine import stream_completion_doctrine
from .formal import (
    ARTIFACT_SHA256, BRIDGE_THEOREM_IDS, SCP_THEOREM_IDS, TCB_DIGEST, THEOREM_IDS,
    TheoremAxiomRows,
)
from .types import (
    LedgerRowClass, StreamCompletionLedger, StreamCompletionLedgerRow,
)

logger = logging.getLogger(__name__)
LEDGER_VERSION = "pomega1-ledger-v2"
AXIOM_CLOSURE = ("Quot.sound",)


def _row_specs() -> tuple[tuple[str, LedgerRowClass, tuple[str, ...], str], ...]:
    """Return the exact topological DAG including every formal theorem row."""
    logger.debug("_row_specs entry")
    specs = (
        ("natural-numbers", LedgerRowClass.FOUNDATION, (), "index formation"),
        ("dependent-function-types", LedgerRowClass.FOUNDATION, (), "prefix/stream formation"),
        ("propositions-and-equality", LedgerRowClass.FOUNDATION, (), "law statements"),
        ("Quot.sound", LedgerRowClass.AXIOM, (), "function extensionality"),
        ("finite-index-types", LedgerRowClass.DEFINITION, ("natural-numbers",), "Fin"),
        ("decidable-alphabet-equality", LedgerRowClass.DEFINITION, ("finite-index-types",), "UTF-8 inverse"),
        ("compatible-family", LedgerRowClass.DEFINITION, ("dependent-function-types", "finite-index-types", "propositions-and-equality"), "family class"),
        ("stream-carrier", LedgerRowClass.DEFINITION, ("natural-numbers", "dependent-function-types"), "Nat stream"),
        ("truncation", LedgerRowClass.DEFINITION, ("finite-index-types", "dependent-function-types"), "prefix truncation"),
        ("finite-restriction", LedgerRowClass.DEFINITION, ("stream-carrier", "finite-index-types"), "rho_n"),
        ("diagonal-realization", LedgerRowClass.DEFINITION, ("compatible-family", "finite-restriction"), "diag"),
        ("alphabet-generator-template", LedgerRowClass.DEFINITION, ("decidable-alphabet-equality",), "ordered UTF-8 Fin-N presentation"),
        ("lean-kernel", LedgerRowClass.TRUSTED_BOUNDARY, (), "proof checking"),
        ("lean-pinned-toolchain", LedgerRowClass.TRUSTED_BOUNDARY, ("lean-kernel",), "attested compilation"),
        ("lean-core-library", LedgerRowClass.TRUSTED_BOUNDARY, ("lean-kernel",), "Nat Fin String"),
        ("runtime-compiler-boundary", LedgerRowClass.TRUSTED_BOUNDARY, ("lean-pinned-toolchain",), "bounded private compile"),
        (SCP_THEOREM_IDS[0], LedgerRowClass.DEFINITION, ("truncation", "Quot.sound"), "truncation identity"),
        (SCP_THEOREM_IDS[1], LedgerRowClass.DEFINITION, ("truncation", "Quot.sound"), "truncation composition"),
        (SCP_THEOREM_IDS[2], LedgerRowClass.DEFINITION, ("finite-restriction",), "rho formation/congruence"),
        (SCP_THEOREM_IDS[3], LedgerRowClass.DEFINITION, ("truncation", "finite-restriction", "Quot.sound"), "restriction compatibility"),
        (SCP_THEOREM_IDS[4], LedgerRowClass.DEFINITION, ("diagonal-realization", "Quot.sound"), "diagonal depth"),
        (SCP_THEOREM_IDS[5], LedgerRowClass.DEFINITION, (SCP_THEOREM_IDS[4],), "universal realization"),
        (SCP_THEOREM_IDS[6], LedgerRowClass.DEFINITION, ("finite-restriction",), "coordinate agreement"),
        (SCP_THEOREM_IDS[7], LedgerRowClass.DEFINITION, (SCP_THEOREM_IDS[6], "Quot.sound"), "joint separation"),
        (SCP_THEOREM_IDS[8], LedgerRowClass.DEFINITION, (SCP_THEOREM_IDS[7], "Quot.sound"), "relative uniqueness"),
        (SCP_THEOREM_IDS[9], LedgerRowClass.DEFINITION, ("compatible-family", "stream-carrier", "Quot.sound"), "nonvacuity/inhabitance"),
        (SCP_THEOREM_IDS[10], LedgerRowClass.DEFINITION, (SCP_THEOREM_IDS[5], SCP_THEOREM_IDS[7], SCP_THEOREM_IDS[8], SCP_THEOREM_IDS[9], "runtime-compiler-boundary", "lean-core-library"), "SCP introduction"),
        *((name, LedgerRowClass.DEFINITION, ("alphabet-generator-template",), "alphabet bridge") for name in BRIDGE_THEOREM_IDS),
        ("proof-irrelevance", LedgerRowClass.NOT_USED, (), "not used"),
        ("choice", LedgerRowClass.NOT_USED, (), "not used"),
        ("compactness", LedgerRowClass.NOT_USED, (), "not used"),
        ("excluded-middle", LedgerRowClass.NOT_USED, (), "not used"),
        ("generic-classical-logic", LedgerRowClass.NOT_USED, (), "not used"),
    )
    logger.debug("_row_specs exit rows=%d", len(specs))
    return specs


def _source_digest(row_id: str, kind: LedgerRowClass, use: str) -> str:
    """Bind each row to actual doctrine, formal artifact, generator, or TCB source."""
    logger.debug("_source_digest entry id=%s", row_id)
    if row_id in SCP_THEOREM_IDS:
        origin = ARTIFACT_SHA256
    elif row_id in BRIDGE_THEOREM_IDS or row_id == "alphabet-generator-template":
        origin = GENERATOR_CLOSURE_SHA256
    elif kind is LedgerRowClass.TRUSTED_BOUNDARY:
        origin = TCB_DIGEST
    else:
        origin = stream_completion_doctrine().doctrine_digest
    result = digest("veyra.pomega1.ledger-row-source.v2", (
        ("id", row_id.encode()), ("class", kind.value.encode()),
        ("use", use.encode()), ("origin", origin.encode()),
    ))
    logger.debug("_source_digest exit id=%s", row_id)
    return result


def _compute_rows() -> tuple[StreamCompletionLedgerRow, ...]:
    """Compute transitive axiom closure from raw direct dependency IDs."""
    logger.debug("_compute_rows entry")
    closures: dict[str, tuple[str, ...]] = {}
    rows = []
    for row_id, kind, deps, use in _row_specs():
        closure = {row_id} if kind is LedgerRowClass.AXIOM else set()
        for dependency in deps:
            if dependency not in closures:
                reject("internal-ledger-forward-or-missing-dependency")
            closure.update(closures[dependency])
        closures[row_id] = tuple(sorted(closure))
        rows.append(StreamCompletionLedgerRow(
            row_id, kind, deps, use, _source_digest(row_id, kind, use), closures[row_id],
        ))
    result = tuple(rows)
    logger.debug("_compute_rows exit rows=%d", len(result))
    return result


def _ledger_digest(rows: tuple[StreamCompletionLedgerRow, ...], closure: tuple[str, ...]) -> str:
    """Commit the exact ordered DAG and recomputed closures."""
    logger.debug("_ledger_digest entry rows=%d", len(rows))
    packed = tuple((f"row-{i}", frame("veyra.pomega1.ledger-row.v2", (
        ("id", row.row_id.encode()), ("class", row.row_class.value.encode()),
        *texts("dependency", row.direct_dependencies), ("use", row.use.encode()),
        ("source", row.source_digest.encode()), *texts("axiom", row.axiom_closure),
    ))) for i, row in enumerate(rows))
    result = digest("veyra.pomega1.ledger.v2", (
        ("version", LEDGER_VERSION.encode()), *packed, *texts("closure", closure),
    ))
    logger.debug("_ledger_digest exit")
    return result


def stream_completion_ledger() -> StreamCompletionLedger:
    """Construct the exact source-bound noncircular ledger."""
    logger.debug("stream_completion_ledger entry")
    rows = _compute_rows()
    theorem_rows = tuple(row for row in rows if row.row_id in THEOREM_IDS)
    closure = tuple(sorted({item for row in theorem_rows for item in row.axiom_closure}))
    result = StreamCompletionLedger(LEDGER_VERSION, rows, closure, _ledger_digest(rows, closure))
    logger.debug("stream_completion_ledger exit")
    return result


def _audit_raw_dag(rows: tuple[StreamCompletionLedgerRow, ...]) -> tuple[str, ...]:
    """Independently audit IDs, topology, cycles, and caller closure rows."""
    logger.debug("_audit_raw_dag entry rows=%d", len(rows))
    ids = tuple(row.row_id for row in rows)
    if len(set(ids)) != len(ids):
        reject("stream-ledger-duplicate-row-id")
    positions = {row_id: index for index, row_id in enumerate(ids)}
    closures = {}
    for index, row in enumerate(rows):
        if row.row_id in row.direct_dependencies:
            reject("stream-ledger-self-cycle")
        if any(dep not in positions or positions[dep] >= index for dep in row.direct_dependencies):
            reject("stream-ledger-missing-forward-or-cyclic-dependency")
        closure = {row.row_id} if row.row_class is LedgerRowClass.AXIOM else set()
        for dependency in row.direct_dependencies:
            closure.update(closures[dependency])
        computed = tuple(sorted(closure))
        closures[row.row_id] = computed
        if row.axiom_closure != computed:
            reject("stream-ledger-row-axiom-closure-drift")
    result = tuple(sorted({item for name in THEOREM_IDS for item in closures.get(name, ())}))
    logger.debug("_audit_raw_dag exit closure=%s", result)
    return result


def snapshot_ledger(value: StreamCompletionLedger) -> StreamCompletionLedger:
    """Deeply validate scalar shapes, actual DAG, closures, sources, and digest."""
    logger.debug("snapshot_ledger entry")
    exact_shape(value, StreamCompletionLedger, "stream-ledger")
    try:
        if type(value.rows) is not tuple or not 1 <= len(value.rows) <= 128:
            reject("stream-ledger-row-count-invalid")
        for row in value.rows:
            exact_shape(row, StreamCompletionLedgerRow, "stream-ledger-row")
            if type(row.row_id) is not str or type(row.row_class) is not LedgerRowClass or type(row.use) is not str:
                reject("stream-ledger-row-scalar-invalid")
            if type(row.direct_dependencies) is not tuple or type(row.axiom_closure) is not tuple:
                reject("stream-ledger-row-tuples-invalid")
            if any(type(item) is not str for item in (*row.direct_dependencies, *row.axiom_closure)):
                reject("stream-ledger-row-member-invalid")
            exact_digest(row.source_digest, "ledger-row-source")
        if sum(len(row.direct_dependencies) for row in value.rows) > 512:
            reject("stream-ledger-edge-count-invalid")
        if type(value.version) is not str or type(value.theorem_axiom_closure) is not tuple:
            reject("stream-ledger-header-invalid")
        if any(type(item) is not str for item in value.theorem_axiom_closure):
            reject("stream-ledger-closure-invalid")
        exact_digest(value.ledger_digest, "stream-ledger-digest")
    except AttributeError:
        reject("stream-ledger-missing-fields")
    closure = _audit_raw_dag(value.rows)
    if value.theorem_axiom_closure != closure:
        reject("stream-ledger-theorem-closure-drift")
    expected = stream_completion_ledger()
    if value != expected:
        reject("stream-ledger-source-or-dag-drift")
    logger.debug("snapshot_ledger exit")
    return expected


def compiler_axiom_closure(
    ledger: StreamCompletionLedger, rows: TheoremAxiomRows,
) -> tuple[str, ...] | None:
    """Compare exact compiler rows to theorem rows and derive aggregate closure."""
    logger.debug("compiler_axiom_closure entry rows=%d", len(rows))
    if type(rows) is not tuple or tuple(name for name, _ in rows) != THEOREM_IDS:
        logger.error("compiler_axiom_closure theorem order mismatch")
        return None
    by_id = {row.row_id: row for row in ledger.rows}
    if any(type(closure) is not tuple or by_id[name].axiom_closure != closure for name, closure in rows):
        logger.error("compiler_axiom_closure per-theorem mismatch")
        return None
    result = tuple(sorted({item for _, closure in rows for item in closure}))
    logger.debug("compiler_axiom_closure exit closure=%s", result)
    return result
