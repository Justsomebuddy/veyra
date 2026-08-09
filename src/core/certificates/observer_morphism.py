"""Executable provisional P1-A observer-morphism certificate."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer_core_codec import decode_observer
from ..observer_core_semantics import observe
from ..observer_core_support import response_data
from ..observer_core_types import Ready
from ..observer.morphism import (
    InformationLoss,
    MorphismStatus,
    ObserverMorphismJudgment,
    ProjectionStep,
    compose_observer_morphisms,
    identity_observer_morphism,
    observer_morphism_judgment,
    observer_source_binding,
    p1a_observer_morphism_doctrine,
    translate_response,
)
from ..proof_core_types import Silence

logger = logging.getLogger(__name__)


def _morphism_semantic_data(row: ObserverMorphismJudgment) -> tuple[object, ...]:
    """Compare semantics, excluding morphism/translation IDs and their digests."""
    logger.debug("_morphism_semantic_data entry")
    projection = row.translation.projection if row.translation is not None else None
    result = (
        row.fine_observer_id, row.coarse_observer_id, projection,
        row.fine_domain, row.coarse_domain, row.comparison_domain,
        row.information_factorizes_on_comparison, row.coarse_domain_in_fine_domain,
        row.witness_checked, row.status, row.information_loss, row.obstruction,
        row.doctrine_fingerprint, row.source_binding_digest,
    )
    logger.debug("_morphism_semantic_data exit")
    return result


def certify_observer_morphism_p1a() -> Certificate:
    """Certify only structural R11 factorization and its domain distinction."""
    logger.debug("certify_observer_morphism_p1a entry")
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine,
        "p1a-fixed-source",
        (
            "coarse-crest", "fine-total", "fine-domain-hole", "fine-nested",
            "fine-triply-nested",
        ),
    )
    strong = observer_morphism_judgment(
        doctrine, binding, "strong-pair-left", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    information = observer_morphism_judgment(
        doctrine, binding, "information-domain-hole", "fine-domain-hole",
        "coarse-crest", (ProjectionStep.LEFT,),
    )
    incomparable = observer_morphism_judgment(
        doctrine, binding, "incomparable-pair-right", "fine-total",
        "coarse-crest", (ProjectionStep.RIGHT,),
    )
    identity = identity_observer_morphism(
        doctrine, binding, "identity-coarse", "coarse-crest"
    )
    fine_identity = identity_observer_morphism(
        doctrine, binding, "identity-fine", "fine-total"
    )
    first = observer_morphism_judgment(
        doctrine, binding, "nested-first", "fine-nested", "fine-total",
        (ProjectionStep.LEFT,),
    )
    third = observer_morphism_judgment(
        doctrine, binding, "triply-first", "fine-triply-nested", "fine-nested",
        (ProjectionStep.LEFT,),
    )
    if any(
        row.translation is None
        for row in (first, strong, identity, fine_identity, third)
    ):
        result = Certificate(
            "observer_morphism_p1a", "provisional P1-A structural R11 factorization",
            False, "required structural translations were absent", 1,
        )
        logger.error("certify_observer_morphism_p1a missing translation")
        logger.debug("certify_observer_morphism_p1a exit result=%r", result)
        return result
    composition = compose_observer_morphisms(
        doctrine, binding, "nested-composition", first.translation, strong.translation
    )
    fine_unit = compose_observer_morphisms(
        doctrine, binding, "fine-unit", fine_identity.translation, strong.translation
    )
    coarse_unit = compose_observer_morphisms(
        doctrine, binding, "coarse-unit", strong.translation, identity.translation
    )
    first_two = compose_observer_morphisms(
        doctrine, binding, "associative-first-two", third.translation, first.translation
    )
    last_two = compose_observer_morphisms(
        doctrine, binding, "associative-last-two", first.translation, strong.translation
    )
    if first_two.translation is None or last_two.translation is None:
        result = Certificate(
            "observer_morphism_p1a", "provisional P1-A structural R11 factorization",
            False, "required associative translations were absent", 1,
        )
        logger.error("certify_observer_morphism_p1a associative translation missing")
        logger.debug("certify_observer_morphism_p1a exit result=%r", result)
        return result
    associative_left = compose_observer_morphisms(
        doctrine, binding, "associative-left", third.translation, last_two.translation
    )
    associative_right = compose_observer_morphisms(
        doctrine, binding, "associative-right", first_two.translation, strong.translation
    )
    laws = (
        _morphism_semantic_data(fine_unit) == _morphism_semantic_data(strong)
        and _morphism_semantic_data(coarse_unit) == _morphism_semantic_data(strong)
        and _morphism_semantic_data(associative_left)
        == _morphism_semantic_data(associative_right)
    )
    members = {item.observer_id: item for item in doctrine.observers}
    fine = observe(decode_observer(members["fine-total"].canonical), Silence())
    coarse = observe(decode_observer(members["coarse-crest"].canonical), Silence())
    typed = (
        type(fine) is Ready
        and type(coarse) is Ready
        and response_data(translate_response(doctrine, binding, strong.translation, fine.value))
        == response_data(coarse.value)
    )
    exact_binding = all(
        row.doctrine_fingerprint == doctrine.fingerprint
        and row.source_binding_digest == binding.membership_digest
        for row in (
            strong, information, incomparable, identity, composition,
            fine_unit, coarse_unit, associative_left, associative_right,
        )
    )
    passed = (
        strong.status is MorphismStatus.STRONG
        and information.status is MorphismStatus.INFORMATION_ONLY
        and incomparable.status is MorphismStatus.INCOMPARABLE
        and identity.status is MorphismStatus.STRONG
        and identity.translation is not None
        and identity.translation.projection == ()
        and identity.information_loss is InformationLoss.LOSSLESS_IDENTITY
        and strong.information_loss is InformationLoss.DROPS_PAIR_COMPONENTS
        and information.information_loss is InformationLoss.DROPS_PAIR_COMPONENTS
        and incomparable.information_loss is InformationLoss.UNAVAILABLE
        and composition.status is MorphismStatus.STRONG
        and composition.translation is not None
        and composition.translation.projection
        == (ProjectionStep.LEFT, ProjectionStep.LEFT)
        and strong.comparison_domain.confirmed_nonempty
        and information.comparison_domain.confirmed_nonempty
        and strong.witness_checked
        and information.witness_checked
        and strong.coarse_domain_in_fine_domain
        and not information.coarse_domain_in_fine_domain
        and typed
        and exact_binding
        and binding.scope == "immutability-membership-not-chronology"
        and "family-extension-not-refinement" in doctrine.metadata
        and "no-object-promotion" in doctrine.metadata
        and laws
    )
    detail = (
        "strong/information-only/incomparable relative to declared projection; "
        "pair-component loss; lossless empty identity; unit and associativity laws; "
        "composed projections; "
        "exact C depths=0,1; typed response; source membership, not chronology"
    )
    method = (
        "provisional P1-A structural R11 factorization on confirmed nonempty "
        "comparison domains; no constructibility, object, confluence, productivity, "
        "all-depth, infinity, or PΩ promotion; family extension is not refinement"
    )
    result = Certificate("observer_morphism_p1a", method, passed, detail, 1)
    logger.debug("certify_observer_morphism_p1a exit result=%r", result)
    return result
