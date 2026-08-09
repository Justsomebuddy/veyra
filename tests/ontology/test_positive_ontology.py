"""Focused positive-path tests for the bounded executable P0 contract."""

import logging

from src.core.infinity_prefix import periodic_prefix_window, prefix_alphabet, prefix_stage
from src.core.observer_core_kernel import tail_observer
from src.core.observer_patch_atlas import (
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
    triangle_counterexample,
)
from src.core.positive_ontology import (
    presentation_commitment,
    continuation_witness,
    observer_support_judgment,
    family_extension_judgment,
    internal_observer,
    metalanguage_boundary,
    ontology_presentation,
    ontology_stage,
    persistence_judgment,
)
from src.core.positive_ontology_boundaries import (
    bounded_window_judgment,
    diagram_coherence_judgment,
    local_extension_judgment,
    nonfinite_infinity_boundary,
    positive_ontology_checklist,
    silence_boundary_judgment,
)
from src.core.positive_ontology_doctrine import observer_doctrine, p0_observer_doctrine
from src.core.positive_ontology_facets import ontology_facet_report
from src.core.positive_ontology_types import (
    ObserverSupport,
    FacetStatus,
    InfinityLevel,
    RelationStatus,
    RunStatus,
    SilenceModality,
)
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def _tail_doctrine():
    logger.debug("_tail_doctrine entry")
    result = observer_doctrine(
        "tail-only-test", "closed-r11-test", ("fixed-before-target",),
        (internal_observer("tail", tail_observer()),),
    )
    logger.debug("_tail_doctrine exit")
    return result


def test_metalanguage_identity_is_explicit_and_does_not_reflect_echo():
    logger.debug("test_metalanguage_identity_is_explicit_and_does_not_reflect_echo entry")
    row = metalanguage_boundary()
    assert row.object_relation == "observer-indexed echo"
    assert row.metatheory_identity == (
        "canonical observer bytes", "typed response identity", "control identifiers",
    )
    assert not row.echo_reflects_identity and not row.metaphysical_proof
    logger.debug("test_metalanguage_identity_is_explicit_and_does_not_reflect_echo exit")


def test_silent_ready_blocked_and_unqueried_are_separate_support_judgments():
    logger.debug("test_silent_ready_blocked_and_unqueried entry")
    fixed = p0_observer_doctrine()
    tail = _tail_doctrine()
    ready = observer_support_judgment(ontology_stage("ready", Silence(), fixed, 1))
    blocked = observer_support_judgment(ontology_stage("blocked", Silence(), tail, 1))
    unqueried = observer_support_judgment(ontology_stage("unqueried", Silence(), fixed, 0))
    assert ready.support is ObserverSupport.SUPPORTED
    assert ready.runs[0].status is RunStatus.READY
    assert ready.silence == (SilenceModality.INTRINSIC, SilenceModality.RESPONSE)
    assert blocked.support is ObserverSupport.OPEN
    assert blocked.runs[0].status is RunStatus.BLOCKED
    assert blocked.silence == (
        SilenceModality.INTRINSIC,
        SilenceModality.DOMAIN_UNDEFINED,
        SilenceModality.OBSTRUCTION,
    )
    assert unqueried.support is ObserverSupport.OPEN and not unqueried.runs
    assert unqueried.silence == (SilenceModality.NOT_QUERIED,)
    logger.debug("test_silent_ready_blocked_and_unqueried exit")


def test_fixed_family_inherited_persistence_survives_full_extension_split():
    logger.debug("test_fixed_family_extension_split entry")
    doctrine = p0_observer_doctrine()
    lower = ontology_stage("s0", Pulse(Silence()), doctrine, 1)
    upper = ontology_stage("s1", Pulse(Pulse(Silence())), doctrine, 2)
    witness = continuation_witness("w01", "history", "s0", "s1", ("crest",))
    presentation = ontology_presentation(doctrine, "family-split", (lower, upper), (witness,))
    persistence = persistence_judgment(presentation, "history")
    family = family_extension_judgment(presentation, "w01")
    assert persistence.status is RelationStatus.ECHO
    assert (persistence.checked_witnesses, persistence.checked_observers) == (1, 1)
    assert family.inherited_status is RelationStatus.ECHO
    assert family.full_status is RelationStatus.SPLIT
    assert (family.inherited_checks, family.full_checks) == (1, 2)
    assert family.first_obstruction is not None
    assert family.first_obstruction.observer_id == "tail"
    logger.debug("test_fixed_family_extension_split exit")


def test_separate_presentations_are_robust_only_through_observer_echo():
    logger.debug("test_separate_presentations_are_robust_only_through_observer_echo entry")
    doctrine = p0_observer_doctrine()
    lower = ontology_stage("r0", Pulse(Silence()), doctrine, 1)
    upper = ontology_stage("r1", Pulse(Silence()), doctrine, 2)
    witness = continuation_witness("rw", "robust", "r0", "r1", ("crest",))
    presentation = ontology_presentation(doctrine, "robust-copy", (lower, upper), (witness,))
    row = family_extension_judgment(presentation, "rw")
    assert row.inherited_status is row.full_status is RelationStatus.ECHO
    assert (row.inherited_checks, row.full_checks) == (1, 2)
    assert lower.representative is not upper.representative
    logger.debug("test_separate_presentations_are_robust_only_through_observer_echo exit")


def test_pairwise_compatible_triangle_remains_globally_obstructed():
    logger.debug("test_pairwise_compatible_triangle_remains_globally_obstructed entry")
    triangle = triangle_counterexample()
    row = diagram_coherence_judgment(triangle.atlas, triangle.sections)
    assert row.pairwise_compatible and not row.global_coherent
    assert row.obstruction_count == 1
    logger.debug("test_pairwise_compatible_triangle_remains_globally_obstructed exit")


def test_five_infinity_levels_never_receive_finite_promotion():
    logger.debug("test_five_infinity_levels_never_receive_finite_promotion entry")
    alphabet = prefix_alphabet(("a", "b"))
    window = periodic_prefix_window(alphabet, ("a", "b"), 3)
    bounded = bounded_window_judgment(window)
    extension = local_extension_judgment(
        window, prefix_stage(alphabet, 4, ("a", "b", "a", "b"))
    )
    higher = tuple(
        nonfinite_infinity_boundary(level)
        for level in (
            InfinityLevel.PRODUCTIVE_PROCESS,
            InfinityLevel.ALL_DEPTH_HYPOTHESIS,
            InfinityLevel.COMPLETED_CARRIER,
        )
    )
    assert bounded.level is InfinityLevel.BOUNDED_WINDOW and bounded.verified
    assert extension.level is InfinityLevel.LOCAL_EXTENSION and extension.verified
    assert all(not row.verified and not row.finite_promoted for row in higher)
    assert {bounded.level, extension.level, *(row.level for row in higher)} == set(InfinityLevel)
    assert len(positive_ontology_checklist()) == 10
    logger.debug("test_five_infinity_levels_never_receive_finite_promotion exit")


def test_constructed_and_nonpersistent_facets_are_replayed_and_independent():
    logger.debug("test_constructed_and_nonpersistent_facets entry")
    doctrine = p0_observer_doctrine()
    unobserved = ontology_stage("constructed", Silence(), doctrine, 0)
    first = ontology_facet_report(
        unobserved, doctrine, presentation=presentation_commitment("builder-1", unobserved)
    )
    assert first.constructible is FacetStatus.OPEN
    assert first.observable is first.witnessed is FacetStatus.OPEN
    assert first.coherent is first.persistent is FacetStatus.NOT_EVALUATED
    assert first.scoped_object is FacetStatus.OPEN
    lower = ontology_stage("f0", Silence(), doctrine, 1)
    upper = ontology_stage("f1", Pulse(Silence()), doctrine, 1)
    witness = continuation_witness("fw", "fp", "f0", "f1", ("crest",))
    presentation = ontology_presentation(doctrine, "ready-split", (lower, upper), (witness,))
    second = ontology_facet_report(
        lower, doctrine, presentation=presentation_commitment("builder-2", lower),
        persistence_presentation=presentation, persistence_path_id="fp",
    )
    assert second.witnessed is FacetStatus.ESTABLISHED
    assert second.persistent is FacetStatus.REFUTED
    assert second.scoped_object is FacetStatus.REFUTED
    logger.debug("test_constructed_and_nonpersistent_facets exit")


def test_unbound_triangle_obstruction_does_not_refute_stage_or_scoped_object():
    logger.debug("test_unbound_triangle_does_not_refute_stage entry")
    doctrine = p0_observer_doctrine()
    triangle = triangle_counterexample()
    stage = ontology_stage("triangle", Silence(), doctrine, 0)
    row = ontology_facet_report(
        stage, doctrine, coherence_atlas=triangle.atlas,
        coherence_sections=triangle.sections,
    )
    assert row.coherent is FacetStatus.OPEN
    assert row.scoped_object is FacetStatus.OPEN
    logger.debug("test_unbound_triangle_does_not_refute_stage exit")


def test_unrelated_globally_coherent_atlas_cannot_establish_stage_coherence():
    logger.debug("test_unrelated_atlas_cannot_establish_coherence entry")
    doctrine = p0_observer_doctrine()
    stage = ontology_stage("unrelated-coherence", Silence(), doctrine, 0)
    atlas = observer_patch_atlas(("a",), (observer_patch("A", ("a",)),))
    sections = (local_observer_section(atlas, "A", (("a",),)),)
    row = ontology_facet_report(
        stage, doctrine, coherence_atlas=atlas, coherence_sections=sections
    )
    assert row.coherent is FacetStatus.OPEN
    assert row.scoped_object is FacetStatus.OPEN
    logger.debug("test_unrelated_atlas_cannot_establish_coherence exit")


def test_nonobservational_silence_modalities_require_named_evidence():
    logger.debug("test_nonobservational_silence_modalities entry")
    for modality in (
        SilenceModality.OPERATIONAL_ABSENCE,
        SilenceModality.OBSERVER_BLINDNESS,
        SilenceModality.EPISTEMIC_OPEN,
        SilenceModality.RESOURCE_LIMITED,
        SilenceModality.DIVERGENT,
        SilenceModality.INCONSISTENT,
        SilenceModality.UNRESOLVED_IN_SYSTEM,
    ):
        row = silence_boundary_judgment(modality, f"evidence-{modality.value}")
        assert row.modality is modality and not row.derived_from_observation
    logger.debug("test_nonobservational_silence_modalities exit")


def test_all_blocked_support_stays_open_without_a_p0_object_claim():
    logger.debug("test_all_blocked_support_stays_open entry")
    doctrine = _tail_doctrine()
    stage = ontology_stage("blocked-facet", Silence(), doctrine, 1)
    row = observer_support_judgment(stage)
    assert row.support is ObserverSupport.OPEN
    logger.debug("test_all_blocked_support_stays_open exit")
