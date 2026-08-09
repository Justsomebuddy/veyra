"""Explicit finite assumption-ledger closure for P1-D3 AFIP."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_identifier, exact_shape, reject
from .digest import ledger_digest as make_ledger_digest
from .types import AssumptionKind, AssumptionLedger, AssumptionRow

logger = logging.getLogger(__name__)
LEDGER_VERSION = "p1-d3-ledger-v1"
FOUNDATION_ID = "lean4-inductive-nat-functions-v4.30.0-rc2"
LEAN_TCB_DIGEST = "3888939ec1f36e809a4921cffdb773a6e87390ea8576ff3cee569892060a022d"
MAX_LEDGER_ROWS = 64
_PERIODIC_ROWS = (
    AssumptionRow("inductive-naturals", AssumptionKind.FOUNDATION, ()),
    AssumptionRow("finite-index-types", AssumptionKind.DEFINITION, ("inductive-naturals",)),
    AssumptionRow("finite-prefix-family", AssumptionKind.DEFINITION, ("finite-index-types",)),
    AssumptionRow("natural-recursion", AssumptionKind.FOUNDATION, ("inductive-naturals",)),
    AssumptionRow("dependent-function-formation", AssumptionKind.FOUNDATION, ("finite-index-types",)),
    AssumptionRow("coordinatewise-family-equivalence", AssumptionKind.DEFINITION, (
        "finite-prefix-family", "dependent-function-formation",
    )),
    AssumptionRow("lean-kernel-and-core-import-trust", AssumptionKind.TRUSTED_IMPORT, ()),
)


def assumption_row(
    assumption_id: str, kind: AssumptionKind, depends_on: tuple[str, ...] = (),
) -> AssumptionRow:
    """Construct one immutable exact ledger row."""
    logger.debug("assumption_row entry")
    assumption_id = exact_identifier(assumption_id, "assumption-id")
    if type(kind) is not AssumptionKind:
        reject("assumption-kind-must-be-exact")
    if type(depends_on) is not tuple:
        reject("assumption-dependencies-must-be-exact-tuple")
    deps = tuple(exact_identifier(item, "assumption-dependency") for item in depends_on)
    if len(set(deps)) != len(deps) or assumption_id in deps:
        reject("invalid-assumption-dependencies")
    result = AssumptionRow(assumption_id, kind, deps)
    logger.debug("assumption_row exit id=%s", assumption_id)
    return result


def snapshot_assumption_row(value: AssumptionRow) -> AssumptionRow:
    """Deeply capture an exact row and reject string-enum lookalikes."""
    logger.debug("snapshot_assumption_row entry")
    exact_shape(value, AssumptionRow, "assumption-row")
    try:
        result = assumption_row(value.assumption_id, value.kind, value.depends_on)
    except AttributeError:
        reject("assumption-row-missing-fields")
    logger.debug("snapshot_assumption_row exit")
    return result


def assumption_ledger(
    rows: tuple[AssumptionRow, ...], foundation_id: str = FOUNDATION_ID,
    tcb_digest: str = LEAN_TCB_DIGEST,
) -> AssumptionLedger:
    """Build an acyclic ledger and its deterministic transitive closure."""
    logger.debug("assumption_ledger entry")
    foundation_id = exact_identifier(foundation_id, "foundation-id")
    tcb_digest = exact_digest(tcb_digest, "tcb-digest")
    if type(rows) is not tuple or not 1 <= len(rows) <= MAX_LEDGER_ROWS:
        reject("invalid-ledger-rows")
    captured = tuple(snapshot_assumption_row(row) for row in rows)
    ids = tuple(row.assumption_id for row in captured)
    if len(set(ids)) != len(ids):
        reject("duplicate-assumption-id")
    position = {name: index for index, name in enumerate(ids)}
    for index, row in enumerate(captured):
        if any(dep not in position for dep in row.depends_on):
            reject("missing-assumption-dependency")
        if any(position[dep] >= index for dep in row.depends_on):
            reject("cyclic-or-forward-assumption-dependency")
    closure = tuple(sorted(ids))
    packed = tuple((r.assumption_id, r.kind.value, r.depends_on) for r in captured)
    digest = make_ledger_digest(LEDGER_VERSION, foundation_id, tcb_digest, packed, closure)
    result = AssumptionLedger(
        LEDGER_VERSION, foundation_id, tcb_digest, captured, closure, digest,
    )
    logger.debug("assumption_ledger exit rows=%d", len(captured))
    return result


def hypothesis_family_ledger(assumption_ids: tuple[str, ...]) -> AssumptionLedger:
    """Extend the constructive base with explicit source-hypothesis identities."""
    logger.debug("hypothesis_family_ledger entry")
    if type(assumption_ids) is not tuple or not assumption_ids:
        reject("invalid-family-hypothesis-ledger-ids")
    captured = tuple(exact_identifier(item, "hypothesis-ledger-id") for item in assumption_ids)
    if len(set(captured)) != len(captured):
        reject("duplicate-family-hypothesis-ledger-id")
    rows = tuple(_PERIODIC_ROWS) + tuple(
        assumption_row(item, AssumptionKind.HYPOTHESIS) for item in captured
    )
    result = assumption_ledger(rows)
    logger.debug("hypothesis_family_ledger exit hypotheses=%d", len(captured))
    return result


def periodic_family_ledger() -> AssumptionLedger:
    """Return the exact constructive ledger for the first derived row."""
    logger.debug("periodic_family_ledger entry")
    result = assumption_ledger(tuple(_PERIODIC_ROWS))
    logger.debug("periodic_family_ledger exit")
    return result


def snapshot_assumption_ledger(value: AssumptionLedger) -> AssumptionLedger:
    """Rebuild exact ledger identity and reject stale closure or cycles."""
    logger.debug("snapshot_assumption_ledger entry")
    exact_shape(value, AssumptionLedger, "assumption-ledger")
    try:
        if type(value.version) is not str or value.version != LEDGER_VERSION:
            reject("ledger-version-drift")
        expected = assumption_ledger(value.rows, value.foundation_id, value.tcb_digest)
        exact_digest(value.ledger_digest, "ledger-digest")
        if type(value.closure) is not tuple or any(type(x) is not str for x in value.closure):
            reject("ledger-closure-must-be-exact")
    except AttributeError:
        reject("assumption-ledger-missing-fields")
    if value.closure != expected.closure or value.ledger_digest != expected.ledger_digest:
        reject("assumption-ledger-drift")
    logger.debug("snapshot_assumption_ledger exit")
    return expected


def require_periodic_ledger(value: AssumptionLedger) -> AssumptionLedger:
    """Require exact AFIP premise closure for the formal periodic constructor."""
    logger.debug("require_periodic_ledger entry")
    value = snapshot_assumption_ledger(value)
    expected = periodic_family_ledger()
    if value != expected:
        reject("periodic-family-ledger-required")
    logger.debug("require_periodic_ledger exit")
    return expected
