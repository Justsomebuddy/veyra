"""Exact PΩ2 dependency DAG and compiler-derived axiom closure."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .digest import digest, frame, texts
from .doctrine import padic_tower_doctrine
from .formal import (
    ARTIFACT_SHA256, CANONICAL_OPS_ID, CONCRETE_INSTANCE_ID, TCB_DIGEST,
    THEOREM_IDS, TheoremAxiomRows,
)
from .types import (
    PadicCompletionLedger, PadicCompletionLedgerRow, PadicLedgerRowClass,
)

logger = logging.getLogger(__name__)
LEDGER_VERSION = "pomega2-ledger-v1"
AXIOM_CLOSURE = ("Quot.sound", "propext")
_THEOREM_AXIOMS = (
    (), ("propext",), (), ("propext",), ("propext",), (), (), (),
    ("Quot.sound",), ("Quot.sound",), (), (), (), ("Quot.sound",), (),
    ("Quot.sound",), ("Quot.sound", "propext"),
)


def _row_specs() -> tuple[tuple[str, PadicLedgerRowClass, tuple[str, ...], str], ...]:
    """Return the exact topological assumptions/source graph."""
    logger.debug("_row_specs entry")
    base = (
        ("natural-numbers", PadicLedgerRowClass.FOUNDATION, (), "stage and modulus indices"),
        ("dependent-function-types", PadicLedgerRowClass.FOUNDATION, (), "all-depth family formation"),
        ("propositions-equality", PadicLedgerRowClass.FOUNDATION, (), "compatibility laws"),
        ("propext", PadicLedgerRowClass.AXIOM, (), "propositional extensionality in Nat lemmas"),
        ("Quot.sound", PadicLedgerRowClass.AXIOM, (), "function extensionality implementation"),
        ("proof-irrelevance", PadicLedgerRowClass.FOUNDATION, ("propositions-equality",), "subtype proof-field erasure in carrier equality"),
        ("finite-residue-ZMod", PadicLedgerRowClass.DEFINITION, ("natural-numbers",), "canonical Fin residue presentation"),
        ("prime-witness", PadicLedgerRowClass.DEFINITION, ("natural-numbers", "propositions-equality"), "bounded no-proper-divisor witness"),
        ("prime-power-modulus", PadicLedgerRowClass.DEFINITION, ("natural-numbers",), "p^(n+1)"),
        ("canonical-reduction", PadicLedgerRowClass.DEFINITION, ("finite-residue-ZMod", "prime-power-modulus"), "remainder reduction"),
        ("stage-ring-laws", PadicLedgerRowClass.DEFINITION, ("finite-residue-ZMod", "canonical-reduction"), "ring-law witness interface"),
        ("compatible-family", PadicLedgerRowClass.DEFINITION, ("dependent-function-types", "canonical-reduction", "propositions-equality"), "literal dependent subtype"),
        ("ZpVeyra-carrier", PadicLedgerRowClass.DEFINITION, ("compatible-family",), "exact family subtype presentation"),
        ("lean-kernel", PadicLedgerRowClass.TRUSTED_BOUNDARY, (), "proof checking"),
        ("lean-pinned-toolchain", PadicLedgerRowClass.TRUSTED_BOUNDARY, ("lean-kernel",), "attested executable"),
        ("lean-Std.Tactic", PadicLedgerRowClass.TRUSTED_BOUNDARY, ("lean-kernel",), "captured import"),
        ("lean-Init.GrindInstances.Ring.Fin", PadicLedgerRowClass.TRUSTED_BOUNDARY, ("lean-kernel",), "captured canonical Fin ring import"),
        ("runtime-compiler-boundary", PadicLedgerRowClass.TRUSTED_BOUNDARY, ("lean-pinned-toolchain",), "private bounded compile"),
        (CANONICAL_OPS_ID, PadicLedgerRowClass.DEFINITION, ("stage-ring-laws", "canonical-reduction", "propext", "lean-Init.GrindInstances.Ring.Fin"), "constructed canonical stage ring witness"),
    )
    theorem_deps = (
        ("prime-witness",), ("prime-power-modulus", "propext"),
        ("canonical-reduction",), ("canonical-reduction", "propext"),
        (THEOREM_IDS[1], "canonical-reduction"), ("compatible-family",),
        ("ZpVeyra-carrier",), ("ZpVeyra-carrier",),
        ("ZpVeyra-carrier", "proof-irrelevance", "Quot.sound"), (THEOREM_IDS[8],),
        ("stage-ring-laws",), ("stage-ring-laws",), ("stage-ring-laws",),
        ("stage-ring-laws", THEOREM_IDS[8]), ("stage-ring-laws",),
        ("stage-ring-laws", THEOREM_IDS[8]),
        (*THEOREM_IDS[:16], CANONICAL_OPS_ID, "runtime-compiler-boundary",
         "lean-Std.Tactic", "lean-Init.GrindInstances.Ring.Fin"),
    )
    theorem_rows = tuple(
        (name, PadicLedgerRowClass.DEFINITION, deps, f"formal obligation {index + 1}")
        for index, (name, deps) in enumerate(zip(THEOREM_IDS, theorem_deps, strict=True))
    )
    concrete = ((CONCRETE_INSTANCE_ID, PadicLedgerRowClass.DEFINITION,
                 (THEOREM_IDS[-1], "prime-witness", CANONICAL_OPS_ID,
                  "runtime-compiler-boundary"), "p-specific canonical THM017 application"),)
    not_used = tuple(
        (name, PadicLedgerRowClass.NOT_USED, (), "not used") for name in (
            "integers", "choice", "excluded-middle",
            "classical-choice", "compactness", "topological-completeness",
            "generic-inverse-limit-existence", "mathlib-padic-int",
        )
    )
    result = base + theorem_rows + concrete + not_used
    logger.debug("_row_specs exit rows=%d", len(result))
    return result


def _source_digest(row_id: str, kind: PadicLedgerRowClass, use: str) -> str:
    """Bind each row to the actual doctrine, artifact, or toolchain source."""
    logger.debug("_source_digest entry id=%s", row_id)
    if row_id in (*THEOREM_IDS, CANONICAL_OPS_ID, CONCRETE_INSTANCE_ID):
        origin = ARTIFACT_SHA256
    elif kind is PadicLedgerRowClass.TRUSTED_BOUNDARY:
        origin = TCB_DIGEST
    else:
        origin = padic_tower_doctrine().doctrine_digest
    result = digest("veyra.pomega2.ledger-row-source.v1", (
        ("id", row_id.encode()), ("class", kind.value.encode()),
        ("use", use.encode()), ("origin", origin.encode()),
    ))
    logger.debug("_source_digest exit id=%s", row_id)
    return result


def _compute_rows() -> tuple[PadicCompletionLedgerRow, ...]:
    """Compute exact transitive axiom closures from the raw DAG."""
    logger.debug("_compute_rows entry")
    closures: dict[str, tuple[str, ...]] = {}
    rows = []
    for row_id, kind, dependencies, use in _row_specs():
        closure = {row_id} if kind is PadicLedgerRowClass.AXIOM else set()
        for dependency in dependencies:
            if dependency not in closures:
                reject("internal-padic-ledger-forward-or-missing-dependency")
            closure.update(closures[dependency])
        closures[row_id] = tuple(sorted(closure))
        rows.append(PadicCompletionLedgerRow(
            row_id, kind, dependencies, use, _source_digest(row_id, kind, use),
            closures[row_id],
        ))
    result = tuple(rows)
    logger.debug("_compute_rows exit rows=%d", len(result))
    return result


def _ledger_digest(rows: tuple[PadicCompletionLedgerRow, ...], closure: tuple[str, ...]) -> str:
    """Commit the full ordered graph, sources, and recomputed closure."""
    logger.debug("_ledger_digest entry rows=%d", len(rows))
    packed = tuple((f"row-{index}", frame("veyra.pomega2.ledger-row.v1", (
        ("id", row.row_id.encode()), ("class", row.row_class.value.encode()),
        *texts("dependency", row.direct_dependencies), ("use", row.use.encode()),
        ("source", row.source_digest.encode()), *texts("axiom", row.axiom_closure),
    ))) for index, row in enumerate(rows))
    result = digest("veyra.pomega2.ledger.v1", (
        ("version", LEDGER_VERSION.encode()), *packed, *texts("closure", closure),
    ))
    logger.debug("_ledger_digest exit")
    return result


def padic_completion_ledger() -> PadicCompletionLedger:
    """Construct the exact noncircular ledger."""
    logger.debug("padic_completion_ledger entry")
    rows = _compute_rows()
    theorem_rows = tuple(row for row in rows if row.row_id in THEOREM_IDS)
    if tuple(row.axiom_closure for row in theorem_rows) != _THEOREM_AXIOMS:
        reject("internal-padic-ledger-theorem-axiom-oracle-drift")
    closure = tuple(sorted({item for row in rows if row.row_id in THEOREM_IDS for item in row.axiom_closure}))
    result = PadicCompletionLedger(LEDGER_VERSION, rows, closure, _ledger_digest(rows, closure))
    logger.debug("padic_completion_ledger exit")
    return result


def _audit_raw(rows: tuple[PadicCompletionLedgerRow, ...]) -> tuple[str, ...]:
    """Independently audit topology, cycles, types, and caller closure rows."""
    logger.debug("_audit_raw entry rows=%d", len(rows))
    ids = tuple(row.row_id for row in rows)
    if len(set(ids)) != len(ids):
        reject("padic-ledger-duplicate-row-id")
    positions = {name: index for index, name in enumerate(ids)}
    closures: dict[str, tuple[str, ...]] = {}
    for index, row in enumerate(rows):
        exact_shape(row, PadicCompletionLedgerRow, "padic-ledger-row")
        if type(row.row_id) is not str or type(row.row_class) is not PadicLedgerRowClass or type(row.use) is not str:
            reject("padic-ledger-row-scalar-invalid")
        if type(row.direct_dependencies) is not tuple or type(row.axiom_closure) is not tuple:
            reject("padic-ledger-row-tuples-invalid")
        if any(type(item) is not str for item in (*row.direct_dependencies, *row.axiom_closure)):
            reject("padic-ledger-row-member-invalid")
        exact_digest(row.source_digest, "padic-ledger-row-source")
        if any(dep not in positions or positions[dep] >= index for dep in row.direct_dependencies):
            reject("padic-ledger-forward-missing-or-cycle")
        closure = {row.row_id} if row.row_class is PadicLedgerRowClass.AXIOM else set()
        for dependency in row.direct_dependencies:
            closure.update(closures[dependency])
        closures[row.row_id] = tuple(sorted(closure))
        if row.axiom_closure != closures[row.row_id]:
            reject("padic-ledger-row-closure-drift")
    result = tuple(sorted({item for name in THEOREM_IDS for item in closures.get(name, ())}))
    logger.debug("_audit_raw exit closure=%r", result)
    return result


def snapshot_ledger(value: PadicCompletionLedger) -> PadicCompletionLedger:
    """Deeply reject any graph, source, or closure drift."""
    logger.debug("snapshot_ledger entry")
    exact_shape(value, PadicCompletionLedger, "padic-ledger")
    try:
        if type(value.rows) is not tuple or not 1 <= len(value.rows) <= 128:
            reject("padic-ledger-row-count-invalid")
        if type(value.version) is not str or type(value.theorem_axiom_closure) is not tuple:
            reject("padic-ledger-header-invalid")
        if any(type(item) is not str for item in value.theorem_axiom_closure):
            reject("padic-ledger-closure-member-invalid")
        exact_digest(value.ledger_digest, "padic-ledger-digest")
    except AttributeError:
        reject("padic-ledger-missing-fields")
    closure = _audit_raw(value.rows)
    if value.theorem_axiom_closure != closure:
        reject("padic-ledger-theorem-closure-drift")
    expected = padic_completion_ledger()
    if value != expected:
        reject("padic-ledger-source-or-dag-drift")
    logger.debug("snapshot_ledger exit")
    return expected


def compiler_axiom_closure(
    ledger: PadicCompletionLedger, rows: TheoremAxiomRows,
) -> tuple[str, ...] | None:
    """Require the exact per-theorem compiler/ledger closure agreement."""
    logger.debug("compiler_axiom_closure entry rows=%d", len(rows))
    if type(rows) is not tuple or tuple(name for name, _ in rows) != THEOREM_IDS:
        logger.error("compiler_axiom_closure theorem order mismatch")
        return None
    by_id = {row.row_id: row for row in ledger.rows}
    if any(type(closure) is not tuple or by_id[name].axiom_closure != closure for name, closure in rows):
        logger.error("compiler_axiom_closure per-theorem mismatch")
        return None
    result = tuple(sorted({item for _, closure in rows for item in closure}))
    logger.debug("compiler_axiom_closure exit closure=%r", result)
    return result
