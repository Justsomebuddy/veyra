"""Frozen exact dependency-graph auditing for isolated P3-N3/N4."""

from __future__ import annotations

import logging

from .common import digest, reject
from .types import BridgeDependencyRow, BridgeDependencyUnion

logger = logging.getLogger(__name__)
LEDGER_VERSION = "p3n3n4-minimal-proof-union-v1"
SCHEMA_ORACLES = {
    "n3": "de3173ee9ce80c1105ea2c6bfd24343d4cb435dd0a91356e56273a5ac12d928f",
    "left": "71ab57790ea142ec79822ad83d279320f8b284bcc5999e96da2dba1d95e094af",
    "right": "5a684dee10b9084ea91e94276412df00fcb32bbad97d57bd47962776415b7064",
    "premise": "97a422d1a1f5cb3a263bee567e48db3d0df672b1c1b45889b93b5dd61f1211e8",
    "all-depth": "d5c2ff42f265b03aefb391d9e7a6d1a8fe4443ec6045a1c6c2d8ce56dcb8bf4a",
    "n4": "42a18d391e50cee4cf1027630bbdb5001736efa14d997020f9f7e9daded967de",
}


def schema_digest(rows: tuple[BridgeDependencyRow, ...]) -> str:
    """Commit only the ordered allowed row/edge schema."""
    logger.debug("schema_digest entry rows=%d", len(rows))
    result = digest("veyra.p3n3n4.schema.v1", tuple(
        (f"row-{i}", f"{row.row_id}|{row.direct_dependencies}".encode())
        for i, row in enumerate(rows)))
    logger.debug("schema_digest exit")
    return result


def _reachable(rows: tuple[BridgeDependencyRow, ...], roots: tuple[str, ...]) -> set[str]:
    """Return dependency-reachable row identities from exact theorem roots."""
    logger.debug("_reachable entry roots=%d", len(roots))
    dependencies = {row.row_id: row.direct_dependencies for row in rows}
    if any(root not in dependencies for root in roots):
        reject("bridge-ledger-root-missing")
    seen, work = set(roots), list(roots)
    while work:
        for dependency in dependencies[work.pop()]:
            if dependency not in seen:
                seen.add(dependency)
                work.append(dependency)
    logger.debug("_reachable exit rows=%d", len(seen))
    return seen


def audit_exact_rows(candidate: tuple[BridgeDependencyRow, ...],
                     expected: tuple[BridgeDependencyRow, ...], roots: tuple[str, ...],
                     oracle_name: str) -> BridgeDependencyUnion:
    """Reject every missing/extra/unused row or edge against a frozen schema oracle."""
    logger.debug("audit_exact_rows entry oracle=%s", oracle_name)
    if type(candidate) is not tuple or type(expected) is not tuple:
        reject("bridge-ledger-exact-tuple-required")
    if any(type(row) is not BridgeDependencyRow for row in (*candidate, *expected)):
        reject("bridge-ledger-row-exact-type-required")
    oracle = SCHEMA_ORACLES.get(oracle_name)
    if oracle is None or schema_digest(expected) != oracle:
        reject("bridge-ledger-frozen-schema-oracle-drift")
    if candidate != expected:
        candidate_ids = tuple(row.row_id for row in candidate)
        expected_ids = tuple(row.row_id for row in expected)
        if candidate_ids != expected_ids:
            reject("bridge-ledger-missing-extra-or-reordered-row")
        reject("bridge-ledger-missing-extra-edge-or-source-drift")
    ids = tuple(row.row_id for row in candidate)
    if len(set(ids)) != len(ids):
        reject("bridge-ledger-duplicate-row")
    positions = {name: index for index, name in enumerate(ids)}
    if any(dependency not in positions or positions[dependency] >= positions[row.row_id]
           for row in candidate for dependency in row.direct_dependencies):
        reject("bridge-ledger-forward-missing-or-cycle")
    if _reachable(candidate, roots) != set(ids):
        reject("bridge-ledger-unused-or-unreachable-row")
    closures: dict[str, tuple[str, ...]] = {}
    for row in candidate:
        inherited = tuple(sorted({axiom for dependency in row.direct_dependencies
                                  for axiom in closures[dependency]}))
        if row.direct_dependencies and row.axiom_closure != inherited:
            reject("bridge-ledger-row-axiom-closure-drift")
        closures[row.row_id] = row.axiom_closure
    closure = tuple(sorted({axiom for row in candidate for axiom in row.axiom_closure}))
    ledger = digest("veyra.p3n3n4.bridge-ledger.v1", (
        *((f"row-{i}",
           f"{row.row_id}|{row.source_digest}|{row.direct_dependencies}|{row.axiom_closure}".encode())
          for i, row in enumerate(candidate)),
        *(("axiom", axiom.encode()) for axiom in closure),
    ))
    result = BridgeDependencyUnion(LEDGER_VERSION, candidate, closure, ledger)
    logger.debug("audit_exact_rows exit rows=%d", len(candidate))
    return result
