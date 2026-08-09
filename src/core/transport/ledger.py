"""Exact acyclic formal assumption ledger for P3-C2."""

from __future__ import annotations
import logging
from .common import digest, exact_digest, exact_shape, exact_text, reject
from .types import TransportAssumptionLedger

logger = logging.getLogger(__name__)
LEDGER_VERSION = "p3-c2-ledger-v1"
LEDGER_ROWS = (
    "natural-numbers",
    "propositions-equality",
    "propext",
    "lean-kernel",
    "lean-pinned-toolchain",
    "private-bounded-compiler",
    "strict-rank-descent",
    "typed-state-setoids",
    "Path",
    "Path.append",
    "Path.rank_le",
    "edgeMap",
    "edge-setoid-respect",
    "pathTransport",
    "transportAppend",
    "transportRespects",
    "complete-root-reachable-local-commuting-squares",
    "THM_P3C2_001_ranked_local_to_generated_transport",
    "NatOp.modulus",
    "NatOp.ZMod",
    "NatOp.reduce",
    "THM_P3C2_002_natop_reduction_identity",
    "THM_P3C2_003_natop_reduction_composition",
)
LEDGER_EDGES = (
    ("lean-pinned-toolchain", "lean-kernel"),
    ("private-bounded-compiler", "lean-pinned-toolchain"),
    ("typed-state-setoids", "propositions-equality"),
    ("Path", "propositions-equality"),
    ("Path.append", "Path"),
    ("Path.rank_le", "Path"),
    ("Path.rank_le", "strict-rank-descent"),
    ("Path.rank_le", "natural-numbers"),
    ("edgeMap", "propositions-equality"),
    ("edge-setoid-respect", "edgeMap"),
    ("edge-setoid-respect", "typed-state-setoids"),
    ("pathTransport", "Path"),
    ("pathTransport", "edgeMap"),
    ("transportAppend", "pathTransport"),
    ("transportAppend", "Path.append"),
    ("transportAppend", "propositions-equality"),
    ("transportRespects", "pathTransport"),
    ("transportRespects", "edge-setoid-respect"),
    ("transportRespects", "typed-state-setoids"),
    ("complete-root-reachable-local-commuting-squares", "pathTransport"),
    ("complete-root-reachable-local-commuting-squares", "edgeMap"),
    ("complete-root-reachable-local-commuting-squares", "typed-state-setoids"),
    ("complete-root-reachable-local-commuting-squares", "Path"),
    ("complete-root-reachable-local-commuting-squares", "propositions-equality"),
    ("THM_P3C2_001_ranked_local_to_generated_transport", "strict-rank-descent"),
    ("THM_P3C2_001_ranked_local_to_generated_transport", "Path.rank_le"),
    ("THM_P3C2_001_ranked_local_to_generated_transport", "transportAppend"),
    ("THM_P3C2_001_ranked_local_to_generated_transport", "transportRespects"),
    (
        "THM_P3C2_001_ranked_local_to_generated_transport",
        "complete-root-reachable-local-commuting-squares",
    ),
    ("THM_P3C2_001_ranked_local_to_generated_transport", "private-bounded-compiler"),
    ("NatOp.modulus", "natural-numbers"),
    ("NatOp.ZMod", "NatOp.modulus"),
    ("NatOp.reduce", "NatOp.ZMod"),
    ("NatOp.reduce", "NatOp.modulus"),
    ("THM_P3C2_002_natop_reduction_identity", "NatOp.reduce"),
    ("THM_P3C2_002_natop_reduction_identity", "propext"),
    ("THM_P3C2_002_natop_reduction_identity", "private-bounded-compiler"),
    ("THM_P3C2_003_natop_reduction_composition", "NatOp.reduce"),
    ("THM_P3C2_003_natop_reduction_composition", "NatOp.modulus"),
    ("THM_P3C2_003_natop_reduction_composition", "propext"),
    ("THM_P3C2_003_natop_reduction_composition", "private-bounded-compiler"),
)
AXIOM_CLOSURE = ("propext",)
LEDGER_DIGEST_ORACLE = "b634ea8c4936c2ff024f3f593498ab426b4fb8c4edcb14f833fb2060c8a9e6cb"


def transport_assumption_ledger() -> TransportAssumptionLedger:
    """Construct exact ordered graph and enforce its literal digest oracle."""
    logger.debug("transport_assumption_ledger entry")
    value = digest(
        "veyra.p3c2.ledger.v1",
        (
            ("version", LEDGER_VERSION.encode()),
            *((f"row-{i}", x.encode()) for i, x in enumerate(LEDGER_ROWS)),
            *((f"edge-{i}", f"{a}\0{b}".encode()) for i, (a, b) in enumerate(LEDGER_EDGES)),
            *(("axiom", x.encode()) for x in AXIOM_CLOSURE),
        ),
    )
    if value != LEDGER_DIGEST_ORACLE:
        raise RuntimeError("internal P3-C2 ledger oracle drift")
    result = TransportAssumptionLedger(LEDGER_VERSION, LEDGER_ROWS, LEDGER_EDGES, AXIOM_CLOSURE, value)
    logger.debug("transport_assumption_ledger exit rows=%d edges=%d", len(LEDGER_ROWS), len(LEDGER_EDGES))
    return result


def snapshot_ledger(raw: TransportAssumptionLedger) -> TransportAssumptionLedger:
    """Reject alternate, duplicate, missing, forward, or circular dependency graphs."""
    logger.debug("snapshot_ledger entry")
    exact_shape(raw, TransportAssumptionLedger, "transport-ledger")
    exact_text(object.__getattribute__(raw, "version"), "transport-ledger-version")
    if (
        type(raw.ordered_rows) is not tuple
        or type(raw.direct_edges) is not tuple
        or type(raw.theorem_axiom_closure) is not tuple
    ):
        reject("transport-ledger-container-invalid")
    if any(type(x) is not str for x in (*raw.ordered_rows, *raw.theorem_axiom_closure)):
        reject("transport-ledger-row-invalid")
    if any(type(e) is not tuple or len(e) != 2 or any(type(x) is not str for x in e) for e in raw.direct_edges):
        reject("transport-ledger-edge-invalid")
    exact_digest(raw.ledger_digest, "transport-ledger-digest")
    expected = transport_assumption_ledger()
    if raw != expected:
        reject("transport-ledger-drift")
    pos = {x: i for i, x in enumerate(raw.ordered_rows)}
    if len(pos) != len(raw.ordered_rows) or len(set(raw.direct_edges)) != len(raw.direct_edges):
        reject("transport-ledger-duplicate")
    if any(a not in pos or b not in pos or pos[b] >= pos[a] for a, b in raw.direct_edges):
        reject("transport-ledger-missing-forward-or-cycle")
    logger.debug("snapshot_ledger exit")
    return expected
