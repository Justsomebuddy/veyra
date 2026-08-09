"""Bounded topological-order separation for declared finite observer classes."""
from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

THEOREM_ID = "THM-S7-001"
MAX_ISOLATES = 4


@dataclass(frozen=True, slots=True)
class FiniteDAG:
    """A labelled finite directed graph intended to be acyclic."""

    graph_id: str
    vertices: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ObserverClassDefinition:
    """An explicit finite-observer class and its factorization boundary."""

    class_id: str
    observables: tuple[str, ...]
    factorization: str
    scope: str


@dataclass(frozen=True, slots=True)
class TopologyBaselineSignature:
    """The complete signature visible to the declared baseline class."""

    vertex_count: int
    edge_count: int
    degree_profile: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class TopologicalOrderSeparationRow:
    """One equal-baseline pair separated by exact topological-order count."""

    isolate_count: int
    connected_signature: TopologyBaselineSignature
    split_signature: TopologyBaselineSignature
    connected_orders: int
    split_orders: int
    baseline_equal: bool
    observer_separates: bool


@dataclass(frozen=True, slots=True)
class FiniteSeparationTheoremCard:
    """A theorem-card-like record for exactly one bounded separation claim."""

    theorem_id: str
    title: str
    baseline_class_id: str
    observer_class_id: str
    hypotheses: tuple[str, ...]
    conclusion: str
    witness_rows: tuple[TopologicalOrderSeparationRow, ...]
    proof_method: str
    status: str
    boundary: str


def observer_class_definitions() -> tuple[ObserverClassDefinition, ObserverClassDefinition]:
    """Return the baseline factor class and its one-observer extension."""
    logger.debug("observer_class_definitions entry")
    baseline = ObserverClassDefinition(
        "S7-degree-factor",
        ("vertex count", "edge count", "sorted (in-degree, out-degree) profile"),
        "every baseline observer is a deterministic postprocessor of the full S7 baseline signature",
        "labelled DAG pairs in the five-row S7 corpus only",
    )
    extended = ObserverClassDefinition(
        "S7-degree-plus-linear-extensions",
        (*baseline.observables, "exact topological-order count"),
        "deterministic postprocessors may additionally use the exact topological-order count",
        baseline.scope,
    )
    result = (baseline, extended)
    logger.debug("observer_class_definitions exit ids=%s", tuple(item.class_id for item in result))
    return result


def _validate_graph(graph: FiniteDAG) -> dict[str, int]:
    """Validate labels and edges, returning the vertex-index map."""
    logger.debug("_validate_graph entry graph=%s", graph.graph_id)
    if not graph.graph_id or not graph.vertices or len(set(graph.vertices)) != len(graph.vertices):
        logger.error("_validate_graph invalid graph metadata graph=%r", graph)
        raise ValueError("graph requires a non-empty id and unique vertices")
    index = {vertex: position for position, vertex in enumerate(graph.vertices)}
    if len(set(graph.edges)) != len(graph.edges):
        logger.error("_validate_graph duplicate edges graph=%s", graph.graph_id)
        raise ValueError("duplicate edges are not allowed")
    for source, target in graph.edges:
        if source not in index or target not in index or source == target:
            logger.error("_validate_graph invalid edge graph=%s edge=%r", graph.graph_id, (source, target))
            raise ValueError("edges require distinct known endpoints")
    logger.debug("_validate_graph exit graph=%s vertices=%d edges=%d", graph.graph_id, len(index), len(graph.edges))
    return index


def topological_order_count(graph: FiniteDAG) -> int:
    """Count all topological orders by deterministic subset dynamic programming."""
    logger.debug("topological_order_count entry graph=%s", graph.graph_id)
    index = _validate_graph(graph)
    if len(index) > 16:
        logger.error("topological_order_count resource bound graph=%s vertices=%d", graph.graph_id, len(index))
        raise ValueError("bounded checker accepts at most 16 vertices")
    predecessors = [0] * len(index)
    for source, target in graph.edges:
        predecessors[index[target]] |= 1 << index[source]
    counts = [0] * (1 << len(index))
    counts[0] = 1
    for chosen in range(len(counts)):
        if counts[chosen] == 0:
            continue
        for vertex, required in enumerate(predecessors):
            bit = 1 << vertex
            if not chosen & bit and required & ~chosen == 0:
                counts[chosen | bit] += counts[chosen]
    result = counts[-1]
    if result == 0:
        logger.error("topological_order_count cycle detected graph=%s", graph.graph_id)
        raise ValueError("graph must be acyclic")
    logger.debug("topological_order_count exit graph=%s count=%d", graph.graph_id, result)
    return result


def topological_baseline_signature(graph: FiniteDAG) -> TopologyBaselineSignature:
    """Compute the exact signature defining the S7 baseline factor class."""
    logger.debug("topological_baseline_signature entry graph=%s", graph.graph_id)
    index = _validate_graph(graph)
    incoming = [0] * len(index)
    outgoing = [0] * len(index)
    for source, target in graph.edges:
        outgoing[index[source]] += 1
        incoming[index[target]] += 1
    result = TopologyBaselineSignature(
        len(index), len(graph.edges), tuple(sorted(zip(incoming, outgoing, strict=True)))
    )
    logger.debug("topological_baseline_signature exit graph=%s signature=%r", graph.graph_id, result)
    return result


def base_witness_graphs() -> tuple[FiniteDAG, FiniteDAG]:
    """Return an eight-cycle incidence DAG and two disjoint square-incidence DAGs."""
    logger.debug("base_witness_graphs entry")
    sources = tuple(f"s{index}" for index in range(4))
    sinks = tuple(f"t{index}" for index in range(4))
    connected_edges = tuple(
        edge for index in range(4) for edge in ((sources[index], sinks[index]), (sources[index], sinks[(index - 1) % 4]))
    )
    split_edges = tuple(
        (source, sink)
        for group in ((0, 1), (2, 3))
        for source in (sources[group[0]], sources[group[1]])
        for sink in (sinks[group[0]], sinks[group[1]])
    )
    result = (
        FiniteDAG("cycle-incidence-8", sources + sinks, connected_edges),
        FiniteDAG("split-square-incidence-8", sources + sinks, split_edges),
    )
    logger.debug("base_witness_graphs exit edges=%s", tuple(len(graph.edges) for graph in result))
    return result


def isolated_extension(graph: FiniteDAG, isolate_count: int) -> FiniteDAG:
    """Adjoin a bounded number of labelled isolated vertices."""
    logger.debug("isolated_extension entry graph=%s isolates=%d", graph.graph_id, isolate_count)
    _validate_graph(graph)
    if not 0 <= isolate_count <= MAX_ISOLATES:
        logger.error("isolated_extension invalid isolates=%d", isolate_count)
        raise ValueError(f"isolate_count must be between 0 and {MAX_ISOLATES}")
    isolates = tuple(f"z{index}" for index in range(isolate_count))
    if set(isolates) & set(graph.vertices):
        logger.error("isolated_extension label collision graph=%s", graph.graph_id)
        raise ValueError("generated isolate label collides with graph vertex")
    result = FiniteDAG(f"{graph.graph_id}+{isolate_count}I", graph.vertices + isolates, graph.edges)
    logger.debug("isolated_extension exit graph=%s vertices=%d", result.graph_id, len(result.vertices))
    return result


def topological_order_separation_family() -> tuple[TopologicalOrderSeparationRow, ...]:
    """Return five exact separation rows obtained by adjoining 0..4 isolates."""
    logger.debug("topological_order_separation_family entry")
    connected, split = base_witness_graphs()
    rows = []
    for isolate_count in range(MAX_ISOLATES + 1):
        left = isolated_extension(connected, isolate_count)
        right = isolated_extension(split, isolate_count)
        left_signature = topological_baseline_signature(left)
        right_signature = topological_baseline_signature(right)
        left_orders = topological_order_count(left)
        right_orders = topological_order_count(right)
        rows.append(
            TopologicalOrderSeparationRow(
                isolate_count,
                left_signature,
                right_signature,
                left_orders,
                right_orders,
                left_signature == right_signature,
                left_orders != right_orders,
            )
        )
        logger.debug(
            "topological_order_separation_family state isolates=%d orders=%d/%d",
            isolate_count,
            left_orders,
            right_orders,
        )
    result = tuple(rows)
    logger.debug("topological_order_separation_family exit rows=%d", len(result))
    return result


def finite_topological_separation_theorem() -> FiniteSeparationTheoremCard:
    """Return the single S7 theorem card when every bounded witness checks."""
    logger.debug("finite_topological_separation_theorem entry")
    baseline, extended = observer_class_definitions()
    rows = topological_order_separation_family()
    checked = all(row.baseline_equal and row.observer_separates for row in rows)
    result = FiniteSeparationTheoremCard(
        THEOREM_ID,
        "Degree-factor blindness under bounded isolated extension",
        baseline.class_id,
        extended.class_id,
        (
            "the witness DAGs are cycle-incidence-8 and split-square-incidence-8",
            "t is one of 0, 1, 2, 3, 4 labelled isolated vertices",
            "baseline observers factor through the declared S7 signature",
        ),
        "for each checked t, baseline signatures agree while exact topological-order counts differ",
        rows,
        "exact subset-DP enumeration over at most 12 labelled vertices",
        "finite-checked" if checked else "blocked",
        "one five-row finite corpus; no minimality, all-DAG, discovery, or superiority claim",
    )
    logger.debug("finite_topological_separation_theorem exit status=%s", result.status)
    return result


def observer_gap_topology_summary() -> dict[str, int | bool | str]:
    """Return compact counters for integration and certificate hooks."""
    logger.debug("observer_gap_topology_summary entry")
    card = finite_topological_separation_theorem()
    result: dict[str, int | bool | str] = {
        "theorem_id": card.theorem_id,
        "rows": len(card.witness_rows),
        "baseline_equal": sum(row.baseline_equal for row in card.witness_rows),
        "observer_separates": sum(row.observer_separates for row in card.witness_rows),
        "status": card.status,
        "bounded": "no minimality" in card.boundary,
    }
    logger.debug("observer_gap_topology_summary exit result=%r", result)
    return result
