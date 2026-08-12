"""Bounded metamorphic pressure for exact finite claim composition."""

from __future__ import annotations

from itertools import permutations
import logging

from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimQuantifier,
    CorroborationStatus,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
    build_claim_contract,
    build_composition_receipt,
    build_exact_conjunction_contract,
    build_exact_conjunction_license,
    build_external_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
    validate_composition_receipt,
)

logger = logging.getLogger(__name__)


def _digest(value: int) -> str:
    logger.debug("_digest entry value=%d", value)
    result = f"{value:064x}"
    logger.debug("_digest exit")
    return result


def _source(index: int):
    logger.debug("_source entry index=%d", index)
    contract = build_claim_contract(
        (_digest(100 + index),),
        (_digest(200 + index),),
        (_digest(300 + index),),
        ClaimQuantifier.LOCAL,
        (_digest(400 + index),),
        (_digest(500 + index),),
        (_digest(600 + index),),
        (_digest(700 + index),),
        (_digest(800 + index),),
        (ClaimClass.STRUCTURAL,),
        CorroborationStatus.SINGLE_LOCAL_RECEIPT,
        AdaptiveCapability.LOCAL_ONLY,
        PublicWording.BOUNDED_LOCAL,
    )
    receipt = build_local_claim_receipt(
        contract,
        _digest(900 + index),
        _digest(1000 + index),
        LocalReceiptValidity.ESTABLISHED,
    )
    result = build_external_composition_source(receipt, SourceEffect.INCLUDE_LOCAL_CLAIM)
    logger.debug("_source exit index=%d", index)
    return result


def test_four_source_permutations_have_one_target_license_and_receipt() -> None:
    """All 24 caller permutations canonicalize to identical exact-conjunction artifacts."""
    logger.debug("test_four_source_permutations_have_one_target_license_and_receipt entry")
    raw = tuple(_source(index) for index in range(4))
    canonical = canonical_composition_sources(raw)
    expected_target = build_exact_conjunction_contract(canonical)
    expected_license = build_exact_conjunction_license(canonical, expected_target)
    expected_receipt = build_composition_receipt(canonical, expected_target, expected_license)

    for candidate in permutations(raw):
        sources = canonical_composition_sources(candidate)
        target = build_exact_conjunction_contract(sources)
        license = build_exact_conjunction_license(sources, target)
        receipt = build_composition_receipt(sources, target, license)
        assert target == expected_target
        assert license == expected_license
        assert receipt == expected_receipt
        assert validate_composition_receipt(receipt, sources, target, license)
    logger.debug("test_four_source_permutations_have_one_target_license_and_receipt exit")


def test_exact_conjunction_is_literal_union_without_semantic_upgrade() -> None:
    """Every bound dimension is the source union while stronger axes remain disabled."""
    logger.debug("test_exact_conjunction_is_literal_union_without_semantic_upgrade entry")
    sources = canonical_composition_sources(tuple(_source(index) for index in range(4)))
    target = build_exact_conjunction_contract(sources)
    for field in (
        "claim_roots",
        "scope_roots",
        "assumption_roots",
        "observer_roots",
        "doctrine_roots",
        "execution_lineage_roots",
        "research_lineage_roots",
        "provenance_roots",
    ):
        expected = tuple(
            sorted({root for source in sources for root in getattr(source.receipt.contract, field)})
        )
        assert getattr(target, field) == expected
    assert target.quantifier is ClaimQuantifier.FINITE_CONJUNCTION
    assert target.corroboration is CorroborationStatus.MULTIPLE_LOCAL_RECEIPTS
    assert target.adaptive_capability is AdaptiveCapability.LOCAL_ONLY
    assert target.public_wording is PublicWording.CONJUNCTIVE_SUMMARY
    logger.debug("test_exact_conjunction_is_literal_union_without_semantic_upgrade exit")
