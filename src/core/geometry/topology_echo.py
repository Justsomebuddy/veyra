"""Topology-like finite deformation echoes for Veyra corridor/shell shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

logger = logging.getLogger(__name__)
Edge = tuple[str, str]


@dataclass(frozen=True)
class EchoShape:
    """Finite corridor/shell shadow: nodes plus undirected corridor echoes."""

    name: str
    nodes: tuple[str, ...]
    corridors: tuple[Edge, ...]
    kind: str = "corridor-family"

    def __post_init__(self) -> None:
        """Validate finite shape data."""
        logger.debug("EchoShape.__post_init__ entry name=%s", self.name)
        if not self.nodes:
            logger.error("EchoShape empty nodes name=%s", self.name)
            raise ValueError("shape must have nodes")
        missing = {node for edge in self.corridors for node in edge if node not in self.nodes}
        if missing:
            logger.error("EchoShape missing nodes name=%s missing=%r", self.name, missing)
            raise ValueError("corridor endpoint missing from nodes")
        logger.debug("EchoShape.__post_init__ exit corridors=%d", len(self.corridors))

    @property
    def boundary_count(self) -> int:
        """Return number of degree-one boundary nodes."""
        logger.debug("EchoShape.boundary_count entry name=%s", self.name)
        degrees = _degrees(self)
        result = sum(value == 1 for value in degrees.values())
        logger.debug("EchoShape.boundary_count exit result=%d", result)
        return result

    @property
    def component_count(self) -> int:
        """Return finite connected-component count."""
        logger.debug("EchoShape.component_count entry name=%s", self.name)
        result = len(_components(self))
        logger.debug("EchoShape.component_count exit result=%d", result)
        return result

    @property
    def cycle_rank(self) -> int:
        """Return first finite cycle rank: edges - nodes + components."""
        logger.debug("EchoShape.cycle_rank entry name=%s", self.name)
        result = len(self.corridors) - len(self.nodes) + self.component_count
        logger.debug("EchoShape.cycle_rank exit result=%d", result)
        return result


@dataclass(frozen=True)
class DeformationEchoRow:
    """One invariant check across a finite deformation."""

    name: str
    before: str
    after: str
    invariant: str
    before_value: int
    after_value: int
    status: str
    obstruction: str


@dataclass(frozen=True)
class TopologyObstructionCard:
    """Blocked deformation that changes a declared topology-like echo."""

    name: str
    deformation: str
    invariant: str
    before_value: int
    after_value: int
    status: str
    obstruction: str


def _edge(left: str, right: str) -> Edge:
    """Return canonical undirected corridor edge."""
    logger.debug("_edge entry left=%s right=%s", left, right)
    result = (left, right) if left <= right else (right, left)
    logger.debug("_edge exit result=%r", result)
    return result


def echo_shape(name: str, nodes: Iterable[str], corridors: Iterable[Edge], kind: str = "corridor-family") -> EchoShape:
    """Create a normalized finite echo shape."""
    logger.debug("echo_shape entry name=%s kind=%s", name, kind)
    node_tuple = tuple(dict.fromkeys(nodes))
    corridor_tuple = tuple(dict.fromkeys(_edge(a, b) for a, b in corridors if a != b))
    result = EchoShape(name, node_tuple, corridor_tuple, kind)
    logger.debug("echo_shape exit nodes=%d corridors=%d", len(result.nodes), len(result.corridors))
    return result


def _degrees(shape: EchoShape) -> dict[str, int]:
    """Return node degrees for a shape."""
    logger.debug("_degrees entry shape=%s", shape.name)
    degrees = {node: 0 for node in shape.nodes}
    for left, right in shape.corridors:
        degrees[left] += 1
        degrees[right] += 1
    logger.debug("_degrees exit degrees=%r", degrees)
    return degrees


def _components(shape: EchoShape) -> tuple[tuple[str, ...], ...]:
    """Return finite connected components."""
    logger.debug("_components entry shape=%s", shape.name)
    adjacency = {node: set() for node in shape.nodes}
    for left, right in shape.corridors:
        adjacency[left].add(right)
        adjacency[right].add(left)
    seen: set[str] = set(); components: list[tuple[str, ...]] = []
    for node in shape.nodes:
        if node in seen:
            continue
        stack = [node]; comp: list[str] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current); comp.append(current)
            stack.extend(sorted(adjacency[current] - seen, reverse=True))
        components.append(tuple(sorted(comp)))
    result = tuple(components)
    logger.debug("_components exit count=%d", len(result))
    return result


def invariant_value(shape: EchoShape, invariant: str) -> int:
    """Return a declared topology-like invariant value."""
    logger.debug("invariant_value entry shape=%s invariant=%s", shape.name, invariant)
    if invariant == "components":
        result = shape.component_count
    elif invariant == "boundary":
        result = shape.boundary_count
    elif invariant == "cycle-rank":
        result = shape.cycle_rank
    else:
        logger.error("invariant_value unknown invariant=%s", invariant)
        raise ValueError("unknown invariant")
    logger.debug("invariant_value exit result=%d", result)
    return result


def deform_shape(shape: EchoShape, mapping: dict[str, str], name: str, drop: tuple[Edge, ...] = ()) -> EchoShape:
    """Apply a finite deformation by relabel/collapse plus optional corridor removal."""
    logger.debug("deform_shape entry shape=%s name=%s", shape.name, name)
    drop_set = {_edge(a, b) for a, b in drop}
    nodes = tuple(dict.fromkeys(mapping.get(node, node) for node in shape.nodes))
    corridors = []
    for edge in shape.corridors:
        if edge in drop_set:
            continue
        left, right = mapping.get(edge[0], edge[0]), mapping.get(edge[1], edge[1])
        if left != right:
            corridors.append((left, right))
    result = echo_shape(name, nodes, corridors, shape.kind)
    logger.debug("deform_shape exit nodes=%d corridors=%d", len(result.nodes), len(result.corridors))
    return result


def subdivide_corridor(shape: EchoShape, corridor: Edge, inserted: str, name: str) -> EchoShape:
    """Subdivide one corridor by inserting a new node."""
    logger.debug("subdivide_corridor entry shape=%s corridor=%r inserted=%s", shape.name, corridor, inserted)
    target = _edge(*corridor)
    corridors: list[Edge] = []
    for edge in shape.corridors:
        if edge == target:
            corridors.extend(((edge[0], inserted), (inserted, edge[1])))
        else:
            corridors.append(edge)
    result = echo_shape(name, shape.nodes + (inserted,), tuple(corridors), shape.kind)
    logger.debug("subdivide_corridor exit corridors=%d", len(result.corridors))
    return result


def deformation_echo_row(name: str, before: EchoShape, after: EchoShape, invariant: str) -> DeformationEchoRow:
    """Compare a declared invariant before/after deformation."""
    logger.debug("deformation_echo_row entry name=%s invariant=%s", name, invariant)
    left = invariant_value(before, invariant); right = invariant_value(after, invariant)
    status = "invariant" if left == right else "broken"
    result = DeformationEchoRow(name, before.name, after.name, invariant, left, right, status, "none" if status == "invariant" else f"{invariant}-changed")
    logger.debug("deformation_echo_row exit result=%r", result)
    return result


def topology_echo_shapes() -> tuple[EchoShape, ...]:
    """Return default corridor and shell deformation examples."""
    logger.debug("topology_echo_shapes entry")
    corridor = echo_shape("corridor", ("A", "B", "C"), (("A", "B"), ("B", "C")), "corridor")
    corridor_drift = subdivide_corridor(corridor, ("A", "B"), "X", "corridor_drift")
    shell = echo_shape("shell", ("A", "B", "C"), (("A", "B"), ("B", "C"), ("C", "A")), "shell")
    shell_relabel = deform_shape(shell, {"A": "X", "B": "Y", "C": "Z"}, "shell_relabel")
    result = (corridor, corridor_drift, shell, shell_relabel)
    logger.debug("topology_echo_shapes exit count=%d", len(result))
    return result


def topology_invariant_rows() -> tuple[DeformationEchoRow, ...]:
    """Return invariant rows for relabel/drift deformations."""
    logger.debug("topology_invariant_rows entry")
    corridor, corridor_drift, shell, shell_relabel = topology_echo_shapes()
    result = (
        deformation_echo_row("corridor-drift-components", corridor, corridor_drift, "components"),
        deformation_echo_row("corridor-drift-boundary", corridor, corridor_drift, "boundary"),
        deformation_echo_row("shell-relabel-cycle", shell, shell_relabel, "cycle-rank"),
        deformation_echo_row("shell-relabel-boundary", shell, shell_relabel, "boundary"),
    )
    logger.debug("topology_invariant_rows exit count=%d", len(result))
    return result


def topology_obstruction_cards() -> tuple[TopologyObstructionCard, ...]:
    """Return blocked non-invariant deformation cards."""
    logger.debug("topology_obstruction_cards entry")
    corridor, _, shell, _ = topology_echo_shapes()
    torn = deform_shape(corridor, {}, "corridor_torn", drop=(("B", "C"),))
    collapsed = deform_shape(shell, {"C": "A"}, "shell_collapsed")
    tear_before = invariant_value(corridor, "components"); tear_after = invariant_value(torn, "components")
    cyc_before = invariant_value(shell, "cycle-rank"); cyc_after = invariant_value(collapsed, "cycle-rank")
    result = (
        TopologyObstructionCard("corridor-tear", "drop B-C", "components", tear_before, tear_after, "blocked", "component-split"),
        TopologyObstructionCard("shell-collapse", "C -> A", "cycle-rank", cyc_before, cyc_after, "blocked", "cycle-collapse"),
    )
    logger.debug("topology_obstruction_cards exit count=%d", len(result))
    return result


def topology_echo_checklist() -> tuple[str, ...]:
    """Return Sprint X4 acceptance checklist."""
    logger.debug("topology_echo_checklist entry")
    result = ("topology-like claims are finite deformation echo tests", "corridor drift preserves component and boundary echoes", "shell relabel preserves cycle-rank and boundary echoes", "tears/collapses produce explicit obstruction cards")
    logger.debug("topology_echo_checklist exit count=%d", len(result))
    return result


def topology_echo_summary() -> dict[str, int]:
    """Return compact X4 topology-echo summary."""
    logger.debug("topology_echo_summary entry")
    rows = topology_invariant_rows(); cards = topology_obstruction_cards()
    result = {"shapes": len(topology_echo_shapes()), "invariants": len(rows), "invariant_hits": sum(row.status == "invariant" for row in rows), "obstructions": len(cards), "blocked": sum(card.status == "blocked" for card in cards), "checklist": len(topology_echo_checklist())}
    logger.debug("topology_echo_summary exit result=%r", result)
    return result
