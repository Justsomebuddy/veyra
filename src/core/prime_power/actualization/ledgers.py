"""Three independent frozen source schemas for P3-N0."""

from __future__ import annotations

import logging

from .common import digest, indexed, reject
from .types import N0Ledger

logger = logging.getLogger(__name__)

PREBIRTH_ROWS = tuple(f"LA{i:02d}" for i in range(1, 19)) + ("LA21",)
PREBIRTH_EDGES = (
    ("LA04", "LA01"), ("LA04", "LA02"),
    ("LA05", "LA01"), ("LA05", "LA02"),
    ("LA06", "LA01"), ("LA06", "LA02"), ("LA06", "LA03"),
    *(("LA07", x) for x in ("LA04", "LA05", "LA06")),
    *(("LA08", x) for x in ("LA07", "LA04")),
    *(("LA09", x) for x in ("LA07", "LA05")),
    *(("LA10", x) for x in ("LA07", "LA06")),
    *(("LA11", x) for x in ("LA01", "LA02", "LA03", "LA08", "LA10")),
    *(("LA12", x) for x in ("LA01", "LA02", "LA03", "LA08", "LA09")),
    *(("LA13", x) for x in ("LA11", "LA08", "LA10")),
    *(("LA14", x) for x in ("LA12", "LA08", "LA09")),
    ("LA15", "LA13"), ("LA15", "LA14"),
    *(("LA16", x) for x in ("LA15", "LA08", "LA09")),
    ("LA17", "LA08"), ("LA17", "LA09"),
    *(("LA18", x) for x in ("LA08", "LA10", "LA13")),
    *(("LA21", x) for x in ("LA15", "LA16", "LA17", "LA18")),
)
POSTBIRTH_ROWS = ("LA19", "LA20", "LA22")
POSTBIRTH_EDGES = (
    *(("LA19", x) for x in ("LA21", "LA13", "LA18", "LH08", "LH09", "LH11")),
    *(("LA20", x) for x in ("LA21", "LA14", "LA17", "LH08", "LH09", "LH11")),
    ("LA22", "LA19"), ("LA22", "LA20"),
)
HISTORY_ROWS = tuple(f"LH{i:02d}" for i in range(1, 16))
HISTORY_EDGES = (
    ("LH02", "LA21"), ("LH03", "LH01"), ("LH03", "LH02"),
    *(("LH04", x) for x in ("LA21", "LH01", "LH02", "LH03")),
    ("LH05", "LH03"), ("LH05", "LH04"),
    ("LH06", "LH04"), ("LH06", "LH05"),
    ("LH07", "LH04"), ("LH07", "LH06"),
    ("LH08", "LH03"), ("LH08", "LH07"),
    *(("LH09", x) for x in ("LH08", "LA16", "LA17")),
    ("LH10", "LH02"), ("LH10", "LH08"),
    ("LH11", "LH09"), ("LH11", "LH10"),
    ("LH12", "LH11"), ("LH12", "LA19"),
    ("LH13", "LH11"), ("LH13", "LA20"),
    *(("LH14", x) for x in ("LH07", "LH08", "LH12", "LH13", "LA22")),
    *(("LH15", x) for x in ("LH01", "LH05", "LH09", "LH14")),
)

NONADMITTED_ROWS = ("NA01", "NA02", "NA03", "NA04")
NONADMITTED_EDGES = (("NA02", "NA01"), ("NA03", "NA02"), ("NA04", "NA03"))
PREBIRTH_IMPORTS = ("P3-N1:x3", "P3-N2-F:x2", "P3-T:x2", "P3-N0:theorem-source-v2")
POSTBIRTH_IMPORTS = ("N0:token-bound-strict", "N0:token-bound-open")
HISTORY_IMPORTS = ("N0:prebirth-root", "N0:postbirth-root")
NONADMITTED_IMPORTS = ("P3-N1:x3", "P3-N2-F:x2", "P3-T:x2",
                       "P3-N0:theorem-source-v2", "N0:not-admitted-terminal")
ADMITTED_AXIOMS = ("A-HAP-admitted-model-doctrine",)
NONADMITTED_AXIOMS = ()

N0_PREBIRTH_LEDGER_DIGEST_ORACLE = "73994d8f980025d6e0ca3390f0f70d6e0a8d2583ffca46d0bcf36cfaf2af7c19"
N0_POSTBIRTH_LEDGER_DIGEST_ORACLE = "566558c1c92cc2b98ac76752db2ee473601541b79575b25fa1500136c9dff277"
N0_HISTORY_LEDGER_DIGEST_ORACLE = "f7fe48e8a7c669e131146656212f770e433227a085c9f946c5f65505b14c1a24"
N0_NONADMITTED_PREBIRTH_LEDGER_DIGEST_ORACLE = "6ed2f4429035aad0459ae3b06de2868d796d87e3fe113f680cb9dd5b16b85ae8"
N0_NONADMITTED_POSTBIRTH_LEDGER_DIGEST_ORACLE = "7c177e44c9ca501995a4de5d18e3d723a7c90374b9c408794368d7689a911eac"
N0_NONADMITTED_HISTORY_LEDGER_DIGEST_ORACLE = "e2189a837286f8fc023c3fb779b35f7d9dc71b3d7bdfdaca5cae87ced8180e4a"


def _ledger_digest(version, rows, edges, roots, imports, axioms, provenance) -> str:
    """Compute one schema identity from fully frozen ordered content."""
    logger.debug("_ledger_digest entry version=%s", version)
    result = digest("veyra.p3n0.ledger.v1", (
        ("version", version.encode()), *indexed("row", rows),
        *indexed("edge", (f"{a}\0{b}" for a, b in edges)),
        *indexed("root", roots), *indexed("import", imports),
        *indexed("axiom", axioms), ("provenance", provenance.encode()),
    ))
    logger.debug("_ledger_digest exit version=%s", version)
    return result


def _validate_graph(rows, edges, roots, external) -> None:
    """Require ordered, acyclic, exactly used, root-reachable schema rows."""
    logger.debug("_validate_graph entry rows=%d edges=%d", len(rows), len(edges))
    if len(rows) != len(set(rows)) or len(edges) != len(set(edges)) or not roots:
        reject("n0-ledger-duplicate-or-root-invalid")
    positions = {row: i for i, row in enumerate(rows)}
    for child, parent in edges:
        if child not in positions or (parent not in positions and parent not in external):
            reject("n0-ledger-endpoint-invalid")
        if parent in positions and positions[parent] >= positions[child]:
            reject("n0-ledger-order-or-cycle-invalid")
    reachable = set(roots)
    changed = True
    while changed:
        before = len(reachable)
        reachable.update(parent for child, parent in edges if child in reachable and parent in positions)
        changed = len(reachable) != before
    if set(rows) != reachable:
        reject("n0-ledger-unused-or-unreachable-row")
    logger.debug("_validate_graph exit")


def _make(version, rows, edges, roots, imports, axioms, provenance, oracle,
          external=()) -> N0Ledger:
    """Construct one exact frozen ledger and enforce its independent pin."""
    logger.debug("_make entry version=%s", version)
    _validate_graph(rows, edges, roots, set(external))
    value = _ledger_digest(version, rows, edges, roots, imports, axioms, provenance)
    if value != oracle:
        raise RuntimeError(f"internal {version} ledger oracle drift")
    result = N0Ledger(version, rows, edges, roots, imports, axioms, provenance, value)
    logger.debug("_make exit version=%s", version)
    return result


def prebirth_ledger(admitted=True) -> N0Ledger:
    """Return LA01..LA18,LA21 with sole root LA21."""
    logger.debug("prebirth_ledger entry")
    if type(admitted) is not bool:
        reject("n0-ledger-admission-bool-required")
    if admitted:
        result = _make(
            "p3n0-prebirth-ledger-v2", PREBIRTH_ROWS, PREBIRTH_EDGES, ("LA21",),
            PREBIRTH_IMPORTS, ADMITTED_AXIOMS, "admitted-raw-no-result-root-v2",
            N0_PREBIRTH_LEDGER_DIGEST_ORACLE,
        )
    else:
        result = _make(
            "p3n0-nonadmitted-prebirth-ledger-v2", NONADMITTED_ROWS,
            NONADMITTED_EDGES, ("NA04",), NONADMITTED_IMPORTS,
            NONADMITTED_AXIOMS, "not-admitted-no-birth-v2",
            N0_NONADMITTED_PREBIRTH_LEDGER_DIGEST_ORACLE,
        )
    logger.debug("prebirth_ledger exit")
    return result


def postbirth_ledger(admitted=True) -> N0Ledger:
    """Return LA19,LA20,LA22 without authenticating birth backwards."""
    logger.debug("postbirth_ledger entry")
    if type(admitted) is not bool:
        reject("n0-ledger-admission-bool-required")
    if admitted:
        external = {"LA21", "LA13", "LA18", "LA14", "LA17", "LH08", "LH09", "LH11"}
        result = _make(
            "p3n0-postbirth-ledger-v2", POSTBIRTH_ROWS, POSTBIRTH_EDGES,
            ("LA22",), POSTBIRTH_IMPORTS, ADMITTED_AXIOMS,
            "admitted-token-bound-outcome-schema-v2",
            N0_POSTBIRTH_LEDGER_DIGEST_ORACLE, external,
        )
    else:
        result = _make(
            "p3n0-nonadmitted-postbirth-ledger-v2", NONADMITTED_ROWS,
            NONADMITTED_EDGES, ("NA04",), NONADMITTED_IMPORTS,
            NONADMITTED_AXIOMS, "not-admitted-no-postbirth-v2",
            N0_NONADMITTED_POSTBIRTH_LEDGER_DIGEST_ORACLE,
        )
    logger.debug("postbirth_ledger exit")
    return result


def history_ledger(admitted=True) -> N0Ledger:
    """Return LH01..LH15 with sole root LH15."""
    logger.debug("history_ledger entry")
    if type(admitted) is not bool:
        reject("n0-ledger-admission-bool-required")
    if admitted:
        external = {"LA21", "LA16", "LA17", "LA19", "LA20", "LA22"}
        result = _make(
            "p3n0-history-ledger-v2", HISTORY_ROWS, HISTORY_EDGES,
            ("LH15",), HISTORY_IMPORTS, ADMITTED_AXIOMS,
            "admitted-history-schema-v2", N0_HISTORY_LEDGER_DIGEST_ORACLE, external,
        )
    else:
        result = _make(
            "p3n0-nonadmitted-history-ledger-v2", NONADMITTED_ROWS,
            NONADMITTED_EDGES, ("NA04",), NONADMITTED_IMPORTS,
            NONADMITTED_AXIOMS, "not-admitted-no-history-v2",
            N0_NONADMITTED_HISTORY_LEDGER_DIGEST_ORACLE,
        )
    logger.debug("history_ledger exit")
    return result
