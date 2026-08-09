"""Executable seventeen-attack boundary ledger for isolated P3-C2."""

from __future__ import annotations
from dataclasses import dataclass, replace
import inspect
import logging
from ..confluence.generated.core import (
    StateRank,
    continuation_edge,
    continuation_state,
    generated_local_peaks,
    snapshot_ranked_system,
    ranked_continuation_system,
)
from .common import TransportCoherenceError
from .examples import positive_example, unequal_transport_example
from .package import transport_package
from .paths import paths_equivalent
from .cofinal import cofinal_boundary_reconciliation
from .runtime import generated_transport_coherence
from .source import (
    edge_transport_map,
    state_setoid_carrier,
    total_transport_doctrine,
)
from .types import (
    GeneratedTransportCoherence,
    HigherCellStructureStatus,
    SetoidClassRow,
    TransportCoherenceStatus,
    TransportMapEntry,
    TransportResourceLimit,
)

logger = logging.getLogger(__name__)
ATTACK_IDS = (
    "joinable-endpoint-unequal-transport",
    "sample-only-hidden-value",
    "caller-composite-map",
    "missing-ordered-or-parallel-peak",
    "two-c22-fillers-derived-boundary-reconciliation",
    "formal-ledger-source-drift",
    "endpoint-name-commitment-drift",
    "foreign-map-transplant",
    "untyped-coercion",
    "equal-payload-hidden-cycle",
    "resource-not-semantic",
    "finite-not-symbolic",
    "c22-does-not-admit-higher-cell-structure",
    "natop-not-generic-network",
    "setoid-respect-failure",
    "p3t-partial-adapter-smuggle",
    "proper-domain-intersection",
)


@dataclass(frozen=True)
class TransportAttackRow:
    attack_id: str
    passed: bool


def required_transport_attacks(positive: GeneratedTransportCoherence) -> tuple[TransportAttackRow, ...]:
    """Execute all mandatory separation and hostile-shape attacks."""
    logger.debug("required_transport_attacks entry")
    base = positive_example().package
    unequal = generated_transport_coherence(unequal_transport_example().package)
    missing_package = transport_package(
        base.system, base.doctrine, base.local_fillers[:1], base.theorem_source, base.assumption_ledger, base.policy
    )
    missing = generated_transport_coherence(missing_package)
    f1, f2 = positive_example().alternate_fillers
    reconciliation = cofinal_boundary_reconciliation(base, f1, f2, "v", ("wv",), ())
    theorem_drift = _rejects(
        lambda: transport_package(
            base.system,
            base.doctrine,
            base.local_fillers,
            replace(base.theorem_source, theorem_ids=base.theorem_source.theorem_ids[:1]),
            base.assumption_ledger,
            base.policy,
        )
    )
    bad_states = tuple(replace(x, state_commitment="0" * 64) if x.state_id == "w" else x for x in base.system.states)
    endpoint_drift = _rejects(lambda: snapshot_ranked_system(replace(base.system, states=bad_states)))
    first_map = base.doctrine.edge_maps[0]
    foreign_map = _rejects(
        lambda: total_transport_doctrine(
            base.system,
            "foreign",
            base.doctrine.carriers,
            (replace(first_map, edge_commitment="0" * 64), *base.doctrine.edge_maps[1:]),
        )
    )
    carrier_map = {x.state_id: x for x in base.doctrine.carriers}
    edge = next(x for x in base.system.edges if x.edge_id == "xy")
    untyped = _rejects(
        lambda: edge_transport_map(
            edge.edge_id,
            edge.edge_commitment,
            carrier_map["x"],
            carrier_map["y"],
            (TransportMapEntry("0", "foreign"), TransportMapEntry("1", "1")),
        )
    )
    alias = continuation_state("alias-x", "transport-node", b"x")
    cycle_in = continuation_edge("alias-cycle-in", "alias-x", "x", "cycle", b"same-payload")
    cycle_out = continuation_edge("alias-cycle-out", "x", "alias-x", "cycle", b"same-payload")
    cycle = _rejects(
        lambda: ranked_continuation_system(
            base.system.doctrine_fingerprint,
            "hidden-cycle-source",
            "v1",
            tuple((*base.system.states, alias)),
            tuple((*base.system.edges, cycle_in, cycle_out)),
            base.system.roots,
            tuple((*base.system.ranks, StateRank("alias-x", 4))),
        )
    )
    resource = generated_transport_coherence(positive_example(max_values=1).package)
    collapsed = state_setoid_carrier(
        "x",
        carrier_map["x"].state_commitment,
        carrier_map["x"].values,
        (SetoidClassRow("0", "same"), SetoidClassRow("1", "same")),
    )
    respect = _rejects(
        lambda: edge_transport_map(
            edge.edge_id,
            edge.edge_commitment,
            collapsed,
            carrier_map["y"],
            (TransportMapEntry("0", "0"), TransportMapEntry("1", "1")),
        )
    )
    p3t_partial = _rejects(
        lambda: generated_transport_coherence(replace(base, doctrine={"partial-domain": ("ready",)}))
    )
    intersection = _rejects(
        lambda: edge_transport_map(
            edge.edge_id, edge.edge_commitment, carrier_map["x"], carrier_map["y"], (TransportMapEntry("0", "0"),)
        )
    )
    boundary_ok = paths_equivalent(
        base.system,
        base.doctrine,
        "x",
        (*f1.left_boundary, *f1.left_postpath),
        (*f1.right_boundary, *f1.right_postpath),
    ) and paths_equivalent(
        base.system,
        base.doctrine,
        "x",
        (*f2.left_boundary, *f2.left_postpath),
        (*f2.right_boundary, *f2.right_postpath),
    )
    values = (
        unequal.status is TransportCoherenceStatus.REFUTED,
        unequal.status is TransportCoherenceStatus.REFUTED and len(carrier_map["x"].values) == 2,
        tuple(inspect.signature(generated_transport_coherence).parameters) == ("raw",),
        missing.status is TransportCoherenceStatus.OPEN and len(generated_local_peaks(base.system)) == 2,
        boundary_ok
        and reconciliation.first_filler_digest == f1.filler_digest
        and reconciliation.second_filler_digest == f2.filler_digest,
        theorem_drift,
        endpoint_drift,
        foreign_map,
        untyped,
        cycle,
        type(resource) is TransportResourceLimit,
        positive.finite_tlgc_scope.startswith("finite-ranked")
        and "symbolic-natop-from-finite-tlgc" in positive.nonclaims,
        positive.higher_cell_structure is HigherCellStructureStatus.NOT_IMPLEMENTED
        and "no-admitted-source-bound-3cell-universe" in positive.nonclaims,
        positive.symbolic_natop_scope.startswith("separate-symbolic-natop")
        and "universal-observer-translation" in positive.nonclaims,
        respect,
        p3t_partial,
        intersection,
    )
    result = tuple(TransportAttackRow(name, ok) for name, ok in zip(ATTACK_IDS, values, strict=True))
    logger.debug("required_transport_attacks exit passed=%d", sum(x.passed for x in result))
    return result


def _rejects(action) -> bool:
    """Return true only for typed validation rejection."""
    logger.debug("_rejects entry")
    try:
        action()
    except (TransportCoherenceError, ValueError):
        logger.debug("_rejects exit true")
        return True
    logger.error("_rejects exit false")
    return False
