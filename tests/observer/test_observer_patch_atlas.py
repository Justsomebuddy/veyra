import logging

import pytest

from src.core.observer_patch_atlas import (
    LocalObserverSection,
    ObserverPatch,
    ObserverPatchAtlas,
    exact_gluing_criterion,
    exact_gluing_relation,
    generated_echo_closure,
    local_contradictions,
    local_echo_relation,
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
    pairwise_overlap_rows,
    triangle_counterexample,
)

logger = logging.getLogger(__name__)


def test_chain_sections_glue_by_generated_echo_closure():
    logger.debug("test_chain_sections_glue_by_generated_echo_closure entry")
    patches = (observer_patch("AB", ("a", "b")), observer_patch("BC", ("b", "c")))
    atlas = observer_patch_atlas(("a", "b", "c"), patches)
    sections = (
        local_observer_section(atlas, "AB", (("a", "b"),)),
        local_observer_section(atlas, "BC", (("b", "c"),)),
    )

    generated = generated_echo_closure(atlas, sections)
    criterion = exact_gluing_criterion(atlas, sections)

    assert generated == {
        ("a", "a"), ("a", "b"), ("a", "c"),
        ("b", "b"), ("b", "c"), ("c", "c"),
    }
    assert local_contradictions(atlas, sections) == ()
    assert exact_gluing_relation(atlas, sections) == generated
    assert criterion.no_local_contradiction
    assert criterion.exact_gluing_exists
    assert criterion.witness == "generated-echo-closure"
    assert criterion.iff_holds
    logger.debug("test_chain_sections_glue_by_generated_echo_closure exit")


def test_exact_gluing_witness_restricts_to_every_local_partition():
    logger.debug("test_exact_gluing_witness_restricts_to_every_local_partition entry")
    patches = (
        observer_patch("ABC", ("a", "b", "c")),
        observer_patch("CD", ("c", "d")),
    )
    atlas = observer_patch_atlas(("a", "b", "c", "d"), patches)
    sections = (
        local_observer_section(atlas, "ABC", (("a", "b"), ("c",))),
        local_observer_section(atlas, "CD", (("c",), ("d",))),
    )
    witness = exact_gluing_relation(atlas, sections)
    assert witness is not None

    for patch, section in zip(atlas.patches, sections, strict=True):
        restricted = {pair for pair in witness if pair[0] in patch.nodes and pair[1] in patch.nodes}
        assert restricted == local_echo_relation(section)
    logger.debug("test_exact_gluing_witness_restricts_to_every_local_partition exit")


def test_two_node_overlap_disagreement_is_both_pairwise_and_global_obstruction():
    logger.debug("test_two_node_overlap_disagreement_is_both_pairwise_and_global_obstruction entry")
    patches = (
        observer_patch("ABX", ("a", "b", "x")),
        observer_patch("ABY", ("a", "b", "y")),
    )
    atlas = observer_patch_atlas(("a", "b", "x", "y"), patches)
    sections = (
        local_observer_section(atlas, "ABX", (("a", "b"), ("x",))),
        local_observer_section(atlas, "ABY", (("a",), ("b",), ("y",))),
    )

    rows = pairwise_overlap_rows(atlas, sections)
    contradictions = local_contradictions(atlas, sections)
    criterion = exact_gluing_criterion(atlas, sections)

    assert len(rows) == 1 and rows[0].overlap == ("a", "b")
    assert not rows[0].compatible
    assert len(contradictions) == 1
    assert (contradictions[0].patch_name, contradictions[0].left, contradictions[0].right) == (
        "ABY", "a", "b",
    )
    assert criterion.obstruction_count == 1
    assert not criterion.no_local_contradiction
    assert not criterion.exact_gluing_exists
    assert criterion.witness == "blocked"
    assert criterion.iff_holds
    logger.debug("test_two_node_overlap_disagreement_is_both_pairwise_and_global_obstruction exit")


def test_triangle_singleton_overlaps_pass_but_global_gluing_fails():
    logger.debug("test_triangle_singleton_overlaps_pass_but_global_gluing_fails entry")
    card = triangle_counterexample()

    assert [row.overlap for row in card.overlaps] == [("b",), ("a",), ("c",)]
    assert all(row.compatible for row in card.overlaps)
    assert ("a", "c") in card.generated_relation
    assert len(card.contradictions) == 1
    contradiction = card.contradictions[0]
    assert (contradiction.patch_name, {contradiction.left, contradiction.right}) == (
        "CA", {"a", "c"},
    )
    assert not card.criterion.exact_gluing_exists
    assert card.criterion.iff_holds
    logger.debug("test_triangle_singleton_overlaps_pass_but_global_gluing_fails exit")


def test_constructors_reject_noncovers_and_nonpartitions():
    logger.debug("test_constructors_reject_noncovers_and_nonpartitions entry")
    ab = observer_patch("AB", ("a", "b"))
    logger.debug("test_constructors_reject_noncovers_and_nonpartitions expected noncover failure")
    with pytest.raises(ValueError, match="exact finite cover"):
        observer_patch_atlas(("a", "b", "c"), (ab,))
    atlas = observer_patch_atlas(("a", "b"), (ab,))
    logger.debug("test_constructors_reject_noncovers_and_nonpartitions expected missing nod failure")
    with pytest.raises(ValueError, match="partition"):
        local_observer_section(atlas, "AB", (("a",),))
    logger.debug("test_constructors_reject_noncovers_and_nonpartitions expected duplicate nod failure")
    with pytest.raises(ValueError, match="partition"):
        local_observer_section(atlas, "AB", (("a", "b"), ("b",)))
    logger.debug("test_constructors_reject_noncovers_and_nonpartitions exit")


def test_operations_reject_missing_or_duplicate_sections():
    logger.debug("test_operations_reject_missing_or_duplicate_sections entry")
    patches = (observer_patch("A", ("a",)), observer_patch("B", ("b",)))
    atlas = observer_patch_atlas(("a", "b"), patches)
    section_a = local_observer_section(atlas, "A", (("a",),))

    logger.debug("test_operations_reject_missing_or_duplicate_sections expected missing failure")
    with pytest.raises(ValueError, match="exactly one local section"):
        generated_echo_closure(atlas, (section_a,))
    logger.debug("test_operations_reject_missing_or_duplicate_sections expected duplicate failure")
    with pytest.raises(ValueError, match="exactly one local section"):
        generated_echo_closure(atlas, (section_a, section_a))
    logger.debug("test_operations_reject_missing_or_duplicate_sections exit")


def test_direct_constructor_atlas_shapes_fail_closed_without_key_errors():
    logger.debug("test_direct_constructor_atlas_shapes_fail_closed_without_key_errors entry")
    malformed = (
        ObserverPatchAtlas((), ()),
        ObserverPatchAtlas(("a",), (ObserverPatch("", ("a",)),)),
        ObserverPatchAtlas(("a",), (ObserverPatch("A", ("a",)), ObserverPatch("empty", ()))),
        ObserverPatchAtlas(("a",), (ObserverPatch("B", ("b",)),)),
        ObserverPatchAtlas(("a",), (ObserverPatch("A", ("a", "")),)),
        ObserverPatchAtlas(("a",), (ObserverPatch("A", ("a", 7)),)),
    )
    for atlas in malformed:
        logger.debug("direct constructor expected atlas validation failure atlas=%r", atlas)
        with pytest.raises(ValueError):
            generated_echo_closure(atlas, ())
    logger.debug("test_direct_constructor_atlas_shapes_fail_closed_without_key_errors exit")


def test_factory_revalidates_direct_patches_and_rejects_hostile_subclasses():
    logger.debug("test_factory_revalidates_direct_patches_and_rejects_hostile_subclasses entry")

    class HostilePatch(ObserverPatch):
        pass

    malformed = (
        ObserverPatch("", ("a",)), ObserverPatch("empty", ()),
        ObserverPatch("outside", ("b",)), HostilePatch("A", ("a",)),
    )
    for patch in malformed:
        logger.debug("factory expected direct patch failure patch=%r", patch)
        with pytest.raises(ValueError):
            observer_patch_atlas(("a",), (patch,))
    logger.debug("test_factory_revalidates_direct_patches_and_rejects_hostile_subclasses exit")


def test_standalone_relation_rejects_malformed_direct_sections():
    logger.debug("test_standalone_relation_rejects_malformed_direct_sections entry")
    malformed = (
        LocalObserverSection("", (("a",),)),
        LocalObserverSection("A", ()),
        LocalObserverSection("A", ((),)),
        LocalObserverSection("A", (("a",), ("a",))),
        LocalObserverSection("A", (("",),)),
        LocalObserverSection("A", ((3,),)),
    )
    for section in malformed:
        logger.debug("standalone relation expected section failure section=%r", section)
        with pytest.raises(ValueError):
            local_echo_relation(section)
    logger.debug("test_standalone_relation_rejects_malformed_direct_sections exit")
