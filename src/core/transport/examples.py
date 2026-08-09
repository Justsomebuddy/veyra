"""Small exact positive and separating finite systems for P3-C2 QA."""

from __future__ import annotations
from dataclasses import dataclass
import logging
from ..confluence.generated.core import (
    StateRank,
    continuation_edge,
    continuation_state,
    generated_local_peaks,
    ranked_continuation_system,
)
from .common import digest
from .formal import transport_theorem_source
from .ledger import transport_assumption_ledger
from .package import local_commuting_filler, transport_package, transport_policy
from .source import (
    edge_transport_map,
    state_setoid_carrier,
    total_transport_doctrine,
    transport_value,
)
from .types import GeneratedTransportFiller, SetoidClassRow, TransportMapEntry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExampleBundle:
    package: object
    alternate_fillers: tuple[GeneratedTransportFiller, ...]


def positive_example(**caps) -> ExampleBundle:
    """Build the canonical five-state identity-transport diamond."""
    logger.debug("positive_example entry")
    system = _system(
        ("v", "w", "x", "y", "z"),
        (
            ("wv", "w", "v"),
            ("xy", "x", "y"),
            ("xz", "x", "z"),
            ("yw", "y", "w"),
            ("zw", "z", "w"),
        ),
        (("v", 0), ("w", 1), ("x", 3), ("y", 2), ("z", 2)),
        "positive",
    )
    doctrine = _doctrine(system, {})
    paths = {("xy", "xz"): ("yw",), ("xz", "xy"): ("zw",)}
    fillers = tuple(
        local_commuting_filler(
            system,
            doctrine,
            p.peak_id,
            paths[(p.left_edge_id, p.right_edge_id)],
            paths[(p.right_edge_id, p.left_edge_id)],
            "w",
        )
        for p in generated_local_peaks(system)
    )
    package = transport_package(
        system, doctrine, fillers, transport_theorem_source(), transport_assumption_ledger(), transport_policy(**caps)
    )
    first = _filler(
        system.system_digest, doctrine.doctrine_digest, "x", ("xy",), ("xz",), "w", ("yw",), ("zw",)
    )
    second = _filler(
        system.system_digest,
        doctrine.doctrine_digest,
        "x",
        ("xy",),
        ("xz",),
        "v",
        ("yw", "wv"),
        ("zw", "wv"),
    )
    result = ExampleBundle(package, (first, second))
    logger.debug("positive_example exit")
    return result


def unequal_transport_example() -> ExampleBundle:
    """Preserve endpoint joinability while one local transported square differs."""
    logger.debug("unequal_transport_example entry")
    base = positive_example().package
    swaps = {"xz": (("0", "1"), ("1", "0"))}
    doctrine = _doctrine(base.system, swaps)
    paths = {("xy", "xz"): ("yw",), ("xz", "xy"): ("zw",)}
    fillers = tuple(
        local_commuting_filler(
            base.system,
            doctrine,
            p.peak_id,
            paths[(p.left_edge_id, p.right_edge_id)],
            paths[(p.right_edge_id, p.left_edge_id)],
            "w",
        )
        for p in generated_local_peaks(base.system)
    )
    package = transport_package(
        base.system, doctrine, fillers, transport_theorem_source(), transport_assumption_ledger(), transport_policy()
    )
    result = ExampleBundle(package, ())
    logger.debug("unequal_transport_example exit")
    return result


def _system(names, edges, ranks, tag):
    """Construct one strict-ranked exact continuation system."""
    logger.debug("_system entry")
    states = tuple(continuation_state(x, "transport-node", x.encode()) for x in names)
    edge_rows = tuple(continuation_edge(i, s, t, "transport-step", i.encode()) for i, s, t in edges)
    rank_rows = tuple(StateRank(x, n) for x, n in ranks)
    result = ranked_continuation_system(
        "p3c2-example-doctrine", f"p3c2-{tag}", "v1", states, edge_rows, ("x",), rank_rows
    )
    logger.debug("_system exit")
    return result


def _doctrine(system, overrides):
    """Construct two-point discrete carriers and exact total edge maps."""
    logger.debug("_doctrine entry")
    carriers = []
    for state in system.states:
        values = tuple(transport_value(state.state_id, x, f"{state.state_id}:{x}".encode()) for x in ("0", "1"))
        classes = tuple(SetoidClassRow(x, f"class-{x}") for x in ("0", "1"))
        carriers.append(state_setoid_carrier(state.state_id, state.state_commitment, values, classes))
    cmap = {x.state_id: x for x in carriers}
    maps = []
    for edge in system.edges:
        rows = overrides.get(edge.edge_id, (("0", "0"), ("1", "1")))
        maps.append(
            edge_transport_map(
                edge.edge_id,
                edge.edge_commitment,
                cmap[edge.source_id],
                cmap[edge.target_id],
                tuple(TransportMapEntry(*x) for x in rows),
            )
        )
    result = total_transport_doctrine(system, "finite-total-discrete-setoid-v1", tuple(carriers), tuple(maps))
    logger.debug("_doctrine exit")
    return result


def _filler(system_digest, doctrine_digest, root, left, right, target, a, b):
    """Construct an exact QA filler identity from derived same-system paths."""
    logger.debug("_filler entry")
    value = digest(
        "veyra.p3c2.global-filler.v1",
        (
            ("system", system_digest.encode()),
            ("doctrine", doctrine_digest.encode()),
            ("root", root.encode()),
            ("left", repr(left).encode()),
            ("right", repr(right).encode()),
            ("target", target.encode()),
            ("left-post", repr(a).encode()),
            ("right-post", repr(b).encode()),
        ),
    )
    result = GeneratedTransportFiller(root, left, right, target, a, b, value)
    logger.debug("_filler exit")
    return result
