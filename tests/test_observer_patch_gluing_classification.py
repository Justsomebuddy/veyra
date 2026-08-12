import logging

import pytest

from src.core.observer_patch_atlas import (
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
    triangle_counterexample,
)
from src.core.observer_patch_gluing_classification import (
    G4_CONFLICT_GRAPH_SCHEMA,
    classify_exact_gluings,
    conflict_safe_quotient_partitions,
    disjoint_singleton_nonuniqueness,
    exact_gluing_relation_from_quotient_partition,
    g4_gluing_classification_boundary,
    quotient_conflict_graph,
)
from src.core.observer_patch_gluing_types import QuotientConflictGraph
from src.core.observer_patch_validation import LocalObserverSection, ObserverPatchAtlas

logger = logging.getLogger(__name__)


def _chain():
    logger.debug("_chain entry")
    atlas = observer_patch_atlas(
        ("a", "b", "c"),
        (observer_patch("AB", ("a", "b")), observer_patch("BC", ("b", "c"))),
    )
    sections = (
        local_observer_section(atlas, "AB", (("a", "b"),)),
        local_observer_section(atlas, "BC", (("b", "c"),)),
    )
    logger.debug("_chain exit")
    return atlas, sections


def test_chain_has_one_exact_gluing_and_complete_conflict_graph():
    logger.debug("test_chain_has_one_exact_gluing_and_complete_conflict_graph entry")
    atlas, sections = _chain()
    result = classify_exact_gluings(atlas, sections)
    assert result.matching_family
    assert result.criterion.exact_gluing_exists
    assert result.conflict_graph.quotient_classes == (("a", "b", "c"),)
    assert result.conflict_graph.complete
    assert result.direct_exact_gluing_count == 1
    assert result.classification_holds
    assert result.unique_exact_gluing
    assert result.uniqueness_iff_conflict_complete
    logger.debug("test_chain_has_one_exact_gluing_and_complete_conflict_graph exit")


def test_disjoint_singletons_have_two_exact_gluings_and_are_not_unique():
    logger.debug("test_disjoint_singletons_have_two_exact_gluings_and_are_not_unique entry")
    witness = disjoint_singleton_nonuniqueness()
    result = witness.classification
    assert result.matching_family
    assert result.criterion.exact_gluing_exists
    assert result.conflict_graph.quotient_classes == (("a",), ("b",))
    assert result.conflict_graph.edges == ()
    assert not result.conflict_graph.complete
    assert result.direct_exact_gluing_count == 2
    assert result.classification_holds
    assert not result.unique_exact_gluing
    assert result.uniqueness_iff_conflict_complete
    assert witness.both_exact and witness.distinct
    logger.debug("test_disjoint_singletons_have_two_exact_gluings_and_are_not_unique exit")


def test_triangle_matching_family_is_nongluable_and_hard_gates_partitions():
    logger.debug("test_triangle_matching_family_is_nongluable_and_hard_gates_partitions entry")
    triangle = triangle_counterexample()
    result = classify_exact_gluings(triangle.atlas, triangle.sections)
    assert result.matching_family
    assert not result.criterion.exact_gluing_exists
    assert result.safe_quotient_partitions == ()
    assert result.direct_exact_gluing_count == 0
    assert result.classification_holds
    assert not result.unique_exact_gluing
    assert result.uniqueness_iff_conflict_complete
    logger.debug("test_triangle_matching_family_is_nongluable_and_hard_gates_partitions exit")


def test_overlap_mismatch_is_not_a_matching_family_or_gluable():
    logger.debug("test_overlap_mismatch_is_not_a_matching_family_or_gluable entry")
    atlas = observer_patch_atlas(
        ("a", "b", "c"),
        (observer_patch("AB", ("a", "b")), observer_patch("ABC", ("a", "b", "c"))),
    )
    sections = (
        local_observer_section(atlas, "AB", (("a", "b"),)),
        local_observer_section(atlas, "ABC", (("a",), ("b", "c"))),
    )
    result = classify_exact_gluings(atlas, sections)
    assert not result.matching_family
    assert not result.criterion.exact_gluing_exists
    assert result.safe_quotient_partitions == ()
    assert result.direct_exact_gluing_count == 0
    assert result.classification_holds
    logger.debug("test_overlap_mismatch_is_not_a_matching_family_or_gluable exit")


def test_every_safe_partition_lifts_to_the_direct_exact_set():
    logger.debug("test_every_safe_partition_lifts_to_the_direct_exact_set entry")
    atlas = observer_patch_atlas(
        ("a", "b", "c"),
        (
            observer_patch("A", ("a",)),
            observer_patch("B", ("b",)),
            observer_patch("C", ("c",)),
        ),
    )
    sections = tuple(
        local_observer_section(atlas, name, ((node,),))
        for name, node in (("A", "a"), ("B", "b"), ("C", "c"))
    )
    result = classify_exact_gluings(atlas, sections)
    lifted = {
        exact_gluing_relation_from_quotient_partition(result.conflict_graph, partition)
        for partition in result.safe_quotient_partitions
    }
    assert len(result.safe_quotient_partitions) == 5
    assert len(lifted) == result.direct_exact_gluing_count == 5
    assert result.classification_holds
    logger.debug("test_every_safe_partition_lifts_to_the_direct_exact_set exit")


def test_conflict_graph_and_partition_validation_fail_closed():
    logger.debug("test_conflict_graph_and_partition_validation_fail_closed entry")
    graph = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, (("a",), ("b",)), ((0, 1),), True
    )
    assert conflict_safe_quotient_partitions(graph) == (((0,), (1,)),)
    with pytest.raises(ValueError, match="not-conflict-safe"):
        exact_gluing_relation_from_quotient_partition(graph, ((0, 1),))
    with pytest.raises(ValueError, match="completeness-drift"):
        conflict_safe_quotient_partitions(
            QuotientConflictGraph(G4_CONFLICT_GRAPH_SCHEMA, (("a",),), (), False)
        )
    with pytest.raises(ValueError, match="invalid-g4-quotient-partition"):
        exact_gluing_relation_from_quotient_partition(graph, ((True,), (1,)))
    oversized_classes = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, (("a",) * 9,), (), True
    )
    with pytest.raises(ValueError, match="invalid-g4-conflict-graph"):
        conflict_safe_quotient_partitions(oversized_classes)
    oversized_edges = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, (("a",), ("b",)), ((0, 1),) * 29, False
    )
    with pytest.raises(ValueError, match="invalid-g4-conflict-graph"):
        conflict_safe_quotient_partitions(oversized_edges)
    unhashable_edge = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, (("a",), ("b",)), ([0, 1],), True  # type: ignore[arg-type,list-item]
    )
    with pytest.raises(ValueError, match="invalid-g4-conflict-graph-edge"):
        conflict_safe_quotient_partitions(unhashable_edge)
    oversized_edge = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, (("a",), ("b",)), ((0,) * 1_000,), True
    )
    with pytest.raises(ValueError, match="invalid-g4-conflict-graph-edge"):
        conflict_safe_quotient_partitions(oversized_edge)
    with pytest.raises(ValueError, match="invalid-g4-quotient-partition"):
        exact_gluing_relation_from_quotient_partition(graph, ((0,) * 9,))
    logger.debug("test_conflict_graph_and_partition_validation_fail_closed exit")


def test_classification_precharges_hostile_shapes_before_legacy_validation():
    logger.debug("test_classification_precharges_hostile_shapes_before_legacy_validation entry")
    atlas, sections = _chain()
    huge_atlas = ObserverPatchAtlas(tuple(str(i) for i in range(9)), atlas.patches)
    with pytest.raises(ValueError, match="atlas-resource-limit"):
        quotient_conflict_graph(huge_atlas, sections)
    huge_section = LocalObserverSection("AB", (tuple(str(i) for i in range(9)),))
    with pytest.raises(ValueError, match="section-resource-limit"):
        classify_exact_gluings(atlas, (huge_section, sections[1]))
    huge_patch_node = "x" * 129
    hostile_atlas = ObserverPatchAtlas(
        atlas.universe,
        (
            type(atlas.patches[0])("AB", (huge_patch_node, "b")),
            atlas.patches[1],
        ),
    )
    with pytest.raises(ValueError, match="identifier-resource-limit"):
        classify_exact_gluings(hostile_atlas, sections)
    logger.debug("test_classification_precharges_hostile_shapes_before_legacy_validation exit")


def test_boundary_states_exact_finite_nonclaims():
    logger.debug("test_boundary_states_exact_finite_nonclaims entry")
    boundary = g4_gluing_classification_boundary()
    assert "classification-assumes-exact-gluing-existence" in boundary
    assert "no-general-sheaf-effective-descent-stack-or-topology-claim" in boundary
    logger.debug("test_boundary_states_exact_finite_nonclaims exit")


def test_duplicate_carriers_reduce_exactly_when_sections_agree_and_block_when_not():
    logger.debug("test_duplicate_carriers_reduce_exactly_when_sections_agree_and_block_when_not entry")
    duplicate = observer_patch_atlas(
        ("a", "b"),
        (observer_patch("AB1", ("a", "b")), observer_patch("AB2", ("a", "b"))),
    )
    agreed = (
        local_observer_section(duplicate, "AB1", (("a",), ("b",))),
        local_observer_section(duplicate, "AB2", (("a",), ("b",))),
    )
    reduced = observer_patch_atlas(("a", "b"), (observer_patch("AB", ("a", "b")),))
    reduced_sections = (local_observer_section(reduced, "AB", (("a",), ("b",))),)
    duplicate_result = classify_exact_gluings(duplicate, agreed)
    reduced_result = classify_exact_gluings(reduced, reduced_sections)
    assert duplicate_result.generated_relation == reduced_result.generated_relation
    assert duplicate_result.conflict_graph.edges == reduced_result.conflict_graph.edges
    assert duplicate_result.direct_exact_gluing_count == reduced_result.direct_exact_gluing_count
    assert duplicate_result.unique_exact_gluing == reduced_result.unique_exact_gluing

    disagreed = (agreed[0], local_observer_section(duplicate, "AB2", (("a", "b"),)))
    blocked = classify_exact_gluings(duplicate, disagreed)
    assert not blocked.matching_family
    assert not blocked.criterion.exact_gluing_exists
    assert blocked.direct_exact_gluing_count == 0
    logger.debug("test_duplicate_carriers_reduce_exactly_when_sections_agree_and_block_when_not exit")


def test_classification_is_invariant_under_declared_order_and_renaming():
    logger.debug("test_classification_is_invariant_under_declared_order_and_renaming entry")
    atlas, sections = _chain()
    baseline = classify_exact_gluings(atlas, sections)
    permuted = observer_patch_atlas(
        ("c", "a", "b"),
        (observer_patch("right", ("c", "b")), observer_patch("left", ("b", "a"))),
    )
    permuted_sections = (
        local_observer_section(permuted, "right", (("b", "c"),)),
        local_observer_section(permuted, "left", (("a", "b"),)),
    )
    result = classify_exact_gluings(permuted, permuted_sections)
    assert result.generated_relation == baseline.generated_relation
    assert result.direct_exact_gluing_count == baseline.direct_exact_gluing_count == 1
    assert result.unique_exact_gluing == baseline.unique_exact_gluing
    assert result.conflict_graph.complete == baseline.conflict_graph.complete
    logger.debug("test_classification_is_invariant_under_declared_order_and_renaming exit")
