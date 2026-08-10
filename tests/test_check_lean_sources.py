"""Static checks for the portable whole-source Lean harness."""

import logging

from scripts.check_lean_sources import source_graph, topological_layers

logger = logging.getLogger(__name__)


def test_whole_source_lean_graph_is_complete_and_acyclic():
    """All 42 public Lean sources occur exactly once in dependency order."""
    logger.debug("test_whole_source_lean_graph entry")
    graph = source_graph()
    layers = topological_layers(graph)
    flattened = tuple(source for layer in layers for source in layer)
    assert len(graph) == 42
    assert len(flattened) == 42
    assert set(flattened) == set(graph)
    positions = {source: index for index, source in enumerate(flattened)}
    assert all(
        positions[dependency] < positions[source]
        for source, dependencies in graph.items()
        for dependency in dependencies
    )
    logger.debug("test_whole_source_lean_graph exit layers=%d", len(layers))
