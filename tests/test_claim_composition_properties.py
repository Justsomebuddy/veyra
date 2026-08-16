"""Bounded metamorphic pressure for exact finite claim composition."""

from __future__ import annotations

from itertools import permutations
import logging

import pytest

from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimCompositionError,
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


def _source_for_contract(contract, index: int, family: int = 0):
    """Build one distinct established occurrence for an existing contract."""
    logger.debug("_source_for_contract entry index=%d family=%d", index, family)
    receipt = build_local_claim_receipt(
        contract,
        _digest(2000 + family * 100 + index),
        _digest(3000 + family * 100 + index),
        LocalReceiptValidity.ESTABLISHED,
    )
    result = build_external_composition_source(receipt, SourceEffect.INCLUDE_LOCAL_CLAIM)
    logger.debug("_source_for_contract exit index=%d family=%d", index, family)
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


def test_exact_conjunction_associativity_is_flat_over_local_leaves() -> None:
    """Flat A∧B∧C is canonical while AB/BC cannot re-enter as local leaves."""
    logger.debug("test flat local-leaf associativity entry")
    leaves = tuple(_source(index) for index in range(3))
    flat_sources = canonical_composition_sources(leaves)
    flat_target = build_exact_conjunction_contract(flat_sources)
    flat_license = build_exact_conjunction_license(flat_sources, flat_target)
    flat_receipt = build_composition_receipt(flat_sources, flat_target, flat_license)
    assert flat_target.component_contract_digests == tuple(
        sorted(source.receipt.contract.contract_digest for source in leaves)
    )
    assert tuple(binding.receipt_digest for binding in flat_license.sources) == tuple(
        source.receipt.receipt_digest for source in flat_sources
    )
    assert validate_composition_receipt(
        flat_receipt,
        flat_sources,
        flat_target,
        flat_license,
    )

    for pair in ((leaves[0], leaves[1]), (leaves[1], leaves[2])):
        aggregate = build_exact_conjunction_contract(canonical_composition_sources(pair))
        with pytest.raises(
            ClaimCompositionError,
            match="^aggregate-contract-local-reentry$",
        ):
            build_local_claim_receipt(
                aggregate,
                _digest(4000),
                _digest(4001),
                LocalReceiptValidity.ESTABLISHED,
            )
    logger.debug("test flat local-leaf associativity exit")


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


def test_component_contracts_are_the_unique_semantic_set() -> None:
    """Component identity is set-valued even when receipt occurrences repeat K."""
    logger.debug("test semantic component set entry")
    first = _source(0).receipt.contract
    second = _source(1).receipt.contract
    raw = (
        _source_for_contract(first, 0),
        _source_for_contract(first, 1),
        _source_for_contract(second, 2),
        _source_for_contract(first, 3),
    )
    sources = canonical_composition_sources(raw)
    target = build_exact_conjunction_contract(sources)
    assert target.component_contract_digests == tuple(
        sorted({source.receipt.contract.contract_digest for source in sources})
    )
    assert len(target.component_contract_digests) == 2
    assert len(sources) == 4
    logger.debug("test semantic component set exit")


def test_repeated_contract_permutations_preserve_target_but_not_occurrence_family() -> None:
    """Permutation is irrelevant, while a different receipt family remains distinct evidence."""
    logger.debug("test repeated-contract permutation entry")
    contract = _source(0).receipt.contract
    raw = tuple(_source_for_contract(contract, index) for index in range(3))
    canonical = canonical_composition_sources(raw)
    expected_target = build_exact_conjunction_contract(canonical)
    expected_license = build_exact_conjunction_license(canonical, expected_target)
    expected_receipt = build_composition_receipt(canonical, expected_target, expected_license)
    for candidate in permutations(raw):
        sources = canonical_composition_sources(candidate)
        target = build_exact_conjunction_contract(sources)
        license = build_exact_conjunction_license(sources, target)
        receipt = build_composition_receipt(sources, target, license)
        assert (target, license, receipt) == (expected_target, expected_license, expected_receipt)

    alternate = canonical_composition_sources(
        tuple(_source_for_contract(contract, index, family=1) for index in range(3))
    )
    alternate_target = build_exact_conjunction_contract(alternate)
    alternate_license = build_exact_conjunction_license(alternate, alternate_target)
    alternate_receipt = build_composition_receipt(alternate, alternate_target, alternate_license)
    assert alternate_target == expected_target
    assert alternate_license != expected_license
    assert alternate_receipt.assessment_digest != expected_receipt.assessment_digest
    assert alternate_receipt != expected_receipt
    logger.debug("test repeated-contract permutation exit")
