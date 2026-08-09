"""Positive structural and domain tests for provisional P1-A morphisms."""

import logging

from src.core.observer_core_codec import decode_observer
from src.core.observer_core_semantics import observe
from src.core.observer_core_support import response_data
from src.core.observer_core_types import Ready
from src.core.observer_morphism import (
    compose_observer_morphisms,
    identity_observer_morphism,
    observer_morphism_judgment,
    observer_source_binding,
    p1a_observer_morphism_doctrine,
    r11_domain_profile,
)
from src.core.observer_morphism_runtime import translate_response
from src.core.observer_morphism_types import InformationLoss, MorphismStatus, ProjectionStep
from src.core.proof_core_types import Silence

logger = logging.getLogger(__name__)


def _fixture():
    logger.debug("_fixture entry")
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "test-source",
        (
            "coarse-crest", "fine-total", "fine-domain-hole", "fine-nested",
            "fine-triply-nested",
        ),
    )
    logger.debug("_fixture exit")
    return doctrine, binding


def _semantic_data(row):
    logger.debug("_semantic_data entry")
    projection = row.translation.projection if row.translation is not None else None
    result = (
        row.fine_observer_id, row.coarse_observer_id, projection,
        row.fine_domain, row.coarse_domain, row.comparison_domain,
        row.information_factorizes_on_comparison, row.coarse_domain_in_fine_domain,
        row.witness_checked, row.status, row.information_loss, row.obstruction,
        row.doctrine_fingerprint, row.source_binding_digest,
    )
    logger.debug("_semantic_data exit")
    return result


def test_pair_projection_has_typed_response_translation_on_exact_c():
    logger.debug("test_pair_projection_typed entry")
    doctrine, binding = _fixture()
    row = observer_morphism_judgment(
        doctrine, binding, "pair-left", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    members = {item.observer_id: item for item in doctrine.observers}
    fine = observe(decode_observer(members["fine-total"].canonical), Silence())
    coarse = observe(decode_observer(members["coarse-crest"].canonical), Silence())
    assert type(fine) is Ready and type(coarse) is Ready
    assert row.status is MorphismStatus.STRONG
    assert row.information_loss is InformationLoss.DROPS_PAIR_COMPONENTS
    assert row.information_factorizes_on_comparison
    assert row.coarse_domain_in_fine_domain
    assert row.comparison_domain.confirmed_nonempty
    assert row.comparison_domain.witness_depth == 0
    assert row.translation is not None
    assert response_data(translate_response(doctrine, binding, row.translation, fine.value)) == response_data(coarse.value)
    logger.debug("test_pair_projection_typed exit")


def test_tail_domain_hole_is_information_only_not_strong():
    logger.debug("test_tail_domain_hole entry")
    doctrine, binding = _fixture()
    row = observer_morphism_judgment(
        doctrine, binding, "domain-hole", "fine-domain-hole", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert row.status is MorphismStatus.INFORMATION_ONLY
    assert row.information_loss is InformationLoss.DROPS_PAIR_COMPONENTS
    assert row.information_factorizes_on_comparison
    assert not row.coarse_domain_in_fine_domain
    assert row.fine_domain.minimum_pulse_depth == 1
    assert row.coarse_domain.minimum_pulse_depth == 0
    assert row.comparison_domain.witness_depth == 1
    assert row.comparison_domain.confirmed_nonempty and row.witness_checked
    logger.debug("test_tail_domain_hole exit")


def test_wrong_projection_is_incomparable_without_vacuous_translation():
    logger.debug("test_wrong_projection entry")
    doctrine, binding = _fixture()
    row = observer_morphism_judgment(
        doctrine, binding, "wrong-side", "fine-total", "coarse-crest",
        (ProjectionStep.RIGHT,),
    )
    assert row.status is MorphismStatus.INCOMPARABLE
    assert row.information_loss is InformationLoss.UNAVAILABLE
    assert row.obstruction == "declared-projection-does-not-factorize"
    assert not row.information_factorizes_on_comparison
    assert not row.witness_checked and row.translation is None
    assert row.comparison_domain.confirmed_nonempty
    logger.debug("test_wrong_projection exit")


def test_empty_identity_and_composition_inherit_exact_sources_and_domains():
    logger.debug("test_identity_composition entry")
    doctrine, binding = _fixture()
    identity = identity_observer_morphism(
        doctrine, binding, "coarse-identity", "coarse-crest"
    )
    first = observer_morphism_judgment(
        doctrine, binding, "nested-left", "fine-nested", "fine-total",
        (ProjectionStep.LEFT,),
    )
    second = observer_morphism_judgment(
        doctrine, binding, "total-left", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert first.translation is not None and second.translation is not None
    composite = compose_observer_morphisms(
        doctrine, binding, "nested-to-coarse", first.translation, second.translation
    )
    assert identity.status is MorphismStatus.STRONG
    assert identity.information_loss is InformationLoss.LOSSLESS_IDENTITY
    assert identity.translation is not None and identity.translation.projection == ()
    assert composite.status is MorphismStatus.STRONG
    assert composite.information_loss is InformationLoss.DROPS_PAIR_COMPONENTS
    assert composite.translation is not None
    assert composite.translation.projection == (ProjectionStep.LEFT, ProjectionStep.LEFT)
    for row in (identity, first, second, composite):
        assert row.doctrine_fingerprint == doctrine.fingerprint
        assert row.source_binding_digest == binding.membership_digest
        assert row.comparison_domain.confirmed_nonempty
    logger.debug("test_identity_composition exit")


def test_domain_profiles_are_exact_minimum_depths_and_binding_is_not_chronology():
    logger.debug("test_profiles_binding_scope entry")
    doctrine, binding = _fixture()
    assert r11_domain_profile(doctrine, binding, "fine-total").minimum_pulse_depth == 0
    assert r11_domain_profile(doctrine, binding, "fine-domain-hole").minimum_pulse_depth == 1
    assert binding.scope == "immutability-membership-not-chronology"
    assert not hasattr(binding, "created_at") and not hasattr(binding, "sequence")
    logger.debug("test_profiles_binding_scope exit")


def test_units_and_three_morphism_associativity_hold_semantically_not_by_ids():
    logger.debug("test_morphism_laws entry")
    doctrine, binding = _fixture()
    fine_identity = identity_observer_morphism(
        doctrine, binding, "fine-id", "fine-total"
    )
    coarse_identity = identity_observer_morphism(
        doctrine, binding, "coarse-id", "coarse-crest"
    )
    first = observer_morphism_judgment(
        doctrine, binding, "a", "fine-triply-nested", "fine-nested",
        (ProjectionStep.LEFT,),
    )
    second = observer_morphism_judgment(
        doctrine, binding, "b", "fine-nested", "fine-total",
        (ProjectionStep.LEFT,),
    )
    third = observer_morphism_judgment(
        doctrine, binding, "c", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert all(
        row.translation is not None
        for row in (fine_identity, coarse_identity, first, second, third)
    )
    fine_unit = compose_observer_morphisms(
        doctrine, binding, "fine-unit-result", fine_identity.translation,
        third.translation,
    )
    coarse_unit = compose_observer_morphisms(
        doctrine, binding, "coarse-unit-result", third.translation,
        coarse_identity.translation,
    )
    first_two = compose_observer_morphisms(
        doctrine, binding, "first-two", first.translation, second.translation
    )
    last_two = compose_observer_morphisms(
        doctrine, binding, "last-two", second.translation, third.translation
    )
    assert first_two.translation is not None and last_two.translation is not None
    associative_left = compose_observer_morphisms(
        doctrine, binding, "assoc-left", first.translation, last_two.translation
    )
    associative_right = compose_observer_morphisms(
        doctrine, binding, "assoc-right", first_two.translation, third.translation
    )
    assert _semantic_data(fine_unit) == _semantic_data(third)
    assert _semantic_data(coarse_unit) == _semantic_data(third)
    assert _semantic_data(associative_left) == _semantic_data(associative_right)
    assert fine_unit.morphism_id != third.morphism_id
    assert associative_left.morphism_id != associative_right.morphism_id
    logger.debug("test_morphism_laws exit")
