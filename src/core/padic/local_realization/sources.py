"""Pinned sources, minimal dependency unions, and request builders for P3-N3/N4."""

from __future__ import annotations

import logging

from ..completion.formal import (
    ARTIFACT_PATH as P2_PATH, ARTIFACT_SHA256 as P2_SHA, TCB_DIGEST as P2_TCB,
    THEOREM_IDS as P2_THEOREMS, TOOLCHAIN_ID,
)
from ..completion.package import snapshot_package as snapshot_p2
from ..family_introduction.package import snapshot_package as snapshot_n1
from ..family_introduction.sources import (
    ARTIFACT_PATH as N1_PATH, ARTIFACT_SHA256 as N1_SHA,
    FAMILY_DEFINITION_ID, THEOREM_IDS as N1_THEOREMS,
)
from .common import digest, realized_digest, reject, role_term_digest
from .ledger import audit_exact_rows
from .types import (
    AllDepthCoordinateEqualitySource, BridgeDependencyRow,
    BridgeDependencyUnion, N34Policy, N34TheoremSource,
)

logger = logging.getLogger(__name__)
VERSION = "p3n3n4-v1"
ARTIFACT_PATH = "proofs/lean/VeyraPadicLocalRealization.lean"
ARTIFACT_SHA256 = "db273191f8ca9ab23e182e5ed30c6cd1e328b7c87698fedd6c0992e7b180d2da"
THEOREM_IDS = (
    "THM_P3N3_001_realize_integer_family",
    "THM_P3N3_002_realized_integer_family_coordinate",
    "THM_P3N4_001_scoped_joint_separation",
)
PREMISE_PATH = "proofs/lean/VeyraPadicAllDepthEquality.lean"
PREMISE_SHA256 = "3d59ef92d345266d62eedba5418b24fa309a9106c8d8ee0544a934ee043ac27a"
PREMISE_THEOREMS = ("THM_P3N4_PREMISE_001_same_integer_coordinates",)
RHO_DEFINITION_ID = "veyraRho"
TCB_DIGEST = digest("veyra.p3n3n4.tcb.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("pomega2-tcb", P2_TCB.encode()),
    ("process", b"bounded-private-three-source-compile-and-continuity"),))
HARD_CAPTURED = 8 * 1024 * 1024
HARD_STATIC = 16 * 1024 * 1024


def theorem_source() -> N34TheoremSource:
    """Construct the sole pinned N3/N4 theorem source."""
    logger.debug("theorem_source entry")
    imports = ((P2_PATH, P2_SHA), (N1_PATH, N1_SHA))
    value = digest("veyra.p3n3n4.source.v1", (
        ("artifact", ARTIFACT_PATH.encode()), ("sha", ARTIFACT_SHA256.encode()),
        *((f"theorem-{i}", x.encode()) for i, x in enumerate(THEOREM_IDS)),
        *((f"import-{i}", f"{p}|{s}".encode()) for i, (p, s) in enumerate(imports)),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode()),
    ))
    result = N34TheoremSource(VERSION, ARTIFACT_PATH, ARTIFACT_SHA256,
        THEOREM_IDS, imports, TOOLCHAIN_ID, TCB_DIGEST, value)
    logger.debug("theorem_source exit")
    return result


def policy(max_captured_bytes: int = 6 * 1024 * 1024,
           max_static_cost: int = 12 * 1024 * 1024, max_ledger_rows: int = 128,
           max_ledger_edges: int = 256, timeout_seconds: int = 180,
           max_output_bytes: int = 1024 * 1024) -> N34Policy:
    """Construct one exact hard-bounded N3/N4 policy."""
    logger.debug("policy entry")
    values = (max_captured_bytes, max_static_cost, max_ledger_rows,
              max_ledger_edges, timeout_seconds, max_output_bytes)
    if any(type(x) is not int for x in values):
        reject("policy-exact-integers-required")
    caps = (HARD_CAPTURED, HARD_STATIC, 256, 512, 300, 4 * 1024 * 1024)
    if any(not 1 <= x <= cap for x, cap in zip(values, caps, strict=True)):
        reject("policy-bound-invalid")
    value = digest("veyra.p3n3n4.policy.v1", tuple(
        (f"value-{i}", x.to_bytes(8, "big")) for i, x in enumerate(values)))
    result = N34Policy(VERSION, *values, value)
    logger.debug("policy exit")
    return result


def _family_digest(package) -> str:
    """Derive the exact N1 family-term source identity without a judgment."""
    logger.debug("_family_digest entry")
    result = digest("veyra.p3n1.family-term.v1", (
        ("prime", package.prime.source_digest.encode()),
        ("integer", package.integer.source_digest.encode()),
        ("doctrine", package.doctrine.doctrine_digest.encode()),
        ("family-class", package.doctrine.family_class_id.encode()),
        ("coordinate-definition", package.theorem_source.coordinate_definition_id.encode()),
        ("family-definition", package.theorem_source.family_definition_id.encode()),
    ))
    logger.debug("_family_digest exit")
    return result


def _dependency_ids(targets: tuple[str, ...], edges: tuple[tuple[str, str], ...]) -> set[str]:
    """Return the exact reverse-reachable dependency set."""
    logger.debug("_dependency_ids entry targets=%d", len(targets))
    by_source: dict[str, tuple[str, ...]] = {}
    for source, dependency in edges:
        by_source[source] = (*by_source.get(source, ()), dependency)
    selected = set(targets)
    work = list(targets)
    while work:
        for dependency in by_source.get(work.pop(), ()):
            if dependency not in selected:
                selected.add(dependency)
                work.append(dependency)
    logger.debug("_dependency_ids exit rows=%d", len(selected))
    return selected


def _n1_rows(package, namespace: str) -> tuple[BridgeDependencyRow, ...]:
    """Select only the N1 family-introduction transitive closure."""
    logger.debug("_n1_rows entry namespace=%s", namespace)
    selected = _dependency_ids((N1_THEOREMS[2],), package.ledger.direct_edges)
    deps = {row: tuple(b for a, b in package.ledger.direct_edges if a == row and b in selected)
            for row in selected}
    closures: dict[str, tuple[str, ...]] = {}
    result = []
    for row in package.ledger.ordered_rows:
        if row not in selected:
            continue
        closure = {"propext"} if row == "propext" else set()
        for dependency in deps[row]:
            closure.update(closures[dependency])
        closures[row] = tuple(sorted(closure))
        result.append(BridgeDependencyRow(f"{namespace}:{row}",
            tuple(f"{namespace}:{x}" for x in deps[row]),
            digest("veyra.p3n3n4.n1-row-source.v1", (("row", row.encode()),
                ("ledger", package.ledger.ledger_digest.encode()),
                ("artifact", package.theorem_source.artifact_sha256.encode()),
                ("theorem-source", package.theorem_source.source_digest.encode()),
                ("tcb", package.theorem_source.tcb_digest.encode()))),
            closures[row]))
    rows = tuple(result)
    logger.debug("_n1_rows exit rows=%d", len(rows))
    return rows


def _p2_rows(package, theorem_id: str, namespace: str) -> tuple[BridgeDependencyRow, ...]:
    """Select one exact PΩ2 theorem's transitive row closure."""
    logger.debug("_p2_rows entry theorem=%s", theorem_id)
    by_id = {row.row_id: row for row in package.ledger.rows}
    edges = tuple((row.row_id, dep) for row in package.ledger.rows
                  for dep in row.direct_dependencies)
    selected = _dependency_ids((theorem_id,), edges)
    rows = tuple(BridgeDependencyRow(f"{namespace}:{row.row_id}",
        tuple(f"{namespace}:{x}" for x in row.direct_dependencies),
        row.source_digest, row.axiom_closure)
        for row in package.ledger.rows if row.row_id in selected)
    if theorem_id not in by_id:
        reject("pomega2-required-theorem-missing")
    logger.debug("_p2_rows exit rows=%d", len(rows))
    return rows


def n3_dependency_union(n1, pomega2, namespace: str = "n3") -> BridgeDependencyUnion:
    """Build only N1-introduction plus THM007/rho/definition proof closure."""
    logger.debug("n3_dependency_union entry")
    if (type(namespace) is not str or not 1 <= len(namespace) <= 32
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in namespace)):
        reject("bridge-namespace-invalid")
    n1, pomega2 = snapshot_n1(n1), snapshot_p2(pomega2)
    rows = (*_n1_rows(n1, f"{namespace}:n1"),
        *_p2_rows(pomega2, P2_THEOREMS[6], f"{namespace}:p2-007"))
    closure = tuple(sorted({axiom for row in rows for axiom in row.axiom_closure}))
    rho = BridgeDependencyRow(f"{namespace}:def:{RHO_DEFINITION_ID}",
        (f"{namespace}:p2-007:ZpVeyra-carrier",),
        digest("veyra.p3n3n4.definition-source.v1", (("id", RHO_DEFINITION_ID.encode()),
            ("artifact", P2_SHA.encode()))), ())
    own1 = BridgeDependencyRow(f"{namespace}:own:{THEOREM_IDS[0]}",
        (f"{namespace}:n1:{N1_THEOREMS[2]}", f"{namespace}:p2-007:{P2_THEOREMS[6]}",
         rho.row_id),
        theorem_source().source_digest, closure)
    own2 = BridgeDependencyRow(f"{namespace}:own:{THEOREM_IDS[1]}",
        (own1.row_id, rho.row_id, f"{namespace}:n1:{FAMILY_DEFINITION_ID}"),
        theorem_source().source_digest, closure)
    expected = (*rows, rho, own1, own2)
    result = audit_exact_rows(expected, expected, (own2.row_id,), namespace)
    logger.debug("n3_dependency_union exit")
    return result


def all_depth_source(left_n1, right_n1, pomega2) -> AllDepthCoordinateEqualitySource:
    """Bind the owned reflexive all-depth premise to two exact same-family terms."""
    logger.debug("all_depth_source entry")
    left, right, pomega2 = snapshot_n1(left_n1), snapshot_n1(right_n1), snapshot_p2(pomega2)
    left_family, right_family = _family_digest(left), _family_digest(right)
    if left_family != right_family:
        reject("all-depth-source-requires-exact-same-family")
    imports = ((P2_PATH, P2_SHA), (N1_PATH, N1_SHA),
               (ARTIFACT_PATH, ARTIFACT_SHA256))
    term_ledger = n3_dependency_union(left, pomega2)
    n3_ledger = n3_dependency_union(left, pomega2, "premise")
    base = n3_ledger.ordered_rows
    realized = realized_digest(left_family, pomega2.doctrine.carrier_id,
        pomega2.theorem_source.theorem_ids[6], term_ledger.ledger_digest)
    left_term, right_term = (role_term_digest(realized, role)
                             for role in ("left", "right"))
    term_rows = (
        BridgeDependencyRow("premise:term:left",
            (f"premise:own:{THEOREM_IDS[1]}",), left_term, n3_ledger.theorem_axiom_closure),
        BridgeDependencyRow("premise:term:right",
            (f"premise:own:{THEOREM_IDS[1]}",), right_term, n3_ledger.theorem_axiom_closure),
    )
    premise_row_source = digest("veyra.p3n3n4.premise-row-source.v1", (
        ("artifact", PREMISE_SHA256.encode()), ("tcb", TCB_DIGEST.encode())))
    theorem = BridgeDependencyRow(f"premise:own:{PREMISE_THEOREMS[0]}",
        (term_rows[0].row_id, term_rows[1].row_id), premise_row_source,
        n3_ledger.theorem_axiom_closure)
    rows = (*base, *term_rows, theorem)
    ledger = audit_exact_rows(rows, rows, (theorem.row_id,), "all-depth")
    value = digest("veyra.p3n3n4.all-depth-source.v1", (
        ("artifact", PREMISE_PATH.encode()), ("sha", PREMISE_SHA256.encode()),
        ("p2", pomega2.package_digest.encode()),
        ("left", left_family.encode()), ("right", right_family.encode()),
        ("left-term", left_term.encode()), ("right-term", right_term.encode()),
        ("rho", RHO_DEFINITION_ID.encode()), ("ledger", ledger.ledger_digest.encode()),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode())))
    result = AllDepthCoordinateEqualitySource(VERSION, PREMISE_PATH, PREMISE_SHA256,
        PREMISE_THEOREMS, imports, TOOLCHAIN_ID, TCB_DIGEST,
        pomega2.package_digest, left_family, right_family, left_term, right_term,
        RHO_DEFINITION_ID, rows, ledger.theorem_axiom_closure,
        ledger.ledger_digest, value)
    logger.debug("all_depth_source exit")
    return result


def n4_dependency_union(left, right, pomega2,
                        premise: AllDepthCoordinateEqualitySource) -> BridgeDependencyUnion:
    """Build two N3 closures plus THM009 and the owned premise closure."""
    logger.debug("n4_dependency_union entry")
    left, right, pomega2 = snapshot_n1(left), snapshot_n1(right), snapshot_p2(pomega2)
    if type(premise) is not AllDepthCoordinateEqualitySource:
        reject("all-depth-source-exact-type-required")
    if premise != all_depth_source(left, right, pomega2):
        reject("all-depth-source-drift-or-transplant")
    left_rows = n3_dependency_union(left, pomega2, "left").ordered_rows
    right_rows = n3_dependency_union(right, pomega2, "right").ordered_rows
    p2rows = _p2_rows(pomega2, P2_THEOREMS[8], "n4:p2-009")
    premise_rows = tuple(BridgeDependencyRow(f"n4:{row.row_id}",
        tuple(f"n4:{x}" for x in row.direct_dependencies), row.source_digest,
        row.axiom_closure) for row in premise.ordered_rows)
    own = BridgeDependencyRow(f"n4:own:{THEOREM_IDS[2]}",
        (f"left:own:{THEOREM_IDS[1]}", f"right:own:{THEOREM_IDS[1]}",
         f"n4:premise:own:{PREMISE_THEOREMS[0]}", f"n4:p2-009:{P2_THEOREMS[8]}"),
        theorem_source().source_digest, ("Quot.sound", "propext"))
    expected = (*left_rows, *right_rows, *p2rows, *premise_rows, own)
    result = audit_exact_rows(expected, expected, (own.row_id,), "n4")
    logger.debug("n4_dependency_union exit")
    return result
