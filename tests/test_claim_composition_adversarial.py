"""Adversarial contract-upgrade and export-bypass pressure for issue #18."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest
import src.core.claim_composition.protocol as composition_protocol

from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimCompositionSource,
    ClaimCompositionError,
    ClaimQuantifier,
    CompositionStatus,
    CorroborationStatus,
    LocalClaimReceipt,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
    assess_claim_composition,
    build_claim_contract,
    build_composition_receipt,
    build_exact_conjunction_contract,
    build_exact_conjunction_license,
    build_governed_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
    composition_disclosure_json,
    validate_composition_license_shape,
    validate_composition_receipt,
    validate_local_claim_receipt,
)

from test_claim_composition import _digest, _governed_result, _positive_case
from test_claim_composition import _assumption_case

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "changes",
    (
        {"quantifier": ClaimQuantifier.EXISTENTIAL},
        {"component_contract_digests": (_digest("e"),)},
    ),
)
def test_local_receipt_rejects_each_nonleaf_profile_axis(changes) -> None:
    """Neither nonlocal quantification nor component identity can enter as a leaf."""
    logger.debug("test partial aggregate local receipt entry")
    source = _assumption_case()[0]
    partial = _changed_target(source.receipt.contract, **changes)
    with pytest.raises(
        ClaimCompositionError,
        match="^aggregate-contract-local-reentry$",
    ):
        build_local_claim_receipt(
            partial,
            _digest("f"),
            _digest("a"),
            LocalReceiptValidity.ESTABLISHED,
        )
    logger.debug("test partial aggregate local receipt exit")


def test_forged_aggregate_local_receipt_fails_fresh_replay() -> None:
    """Direct DTO construction cannot turn an aggregate target into a local source."""
    logger.debug("test forged aggregate local receipt entry")
    sources = _assumption_case()
    aggregate = build_exact_conjunction_contract(sources)
    forged = LocalClaimReceipt(
        aggregate,
        _digest("e"),
        _digest("f"),
        LocalReceiptValidity.ESTABLISHED,
        _digest("a"),
    )
    assert not validate_local_claim_receipt(forged)
    logger.debug("test forged aggregate local receipt exit")


def _changed_target(target, **changes):
    logger.debug("_changed_target entry changes=%s", tuple(changes))
    fields = {
        "claim_roots": target.claim_roots,
        "scope_roots": target.scope_roots,
        "assumption_roots": target.assumption_roots,
        "quantifier": target.quantifier,
        "observer_roots": target.observer_roots,
        "doctrine_roots": target.doctrine_roots,
        "execution_lineage_roots": target.execution_lineage_roots,
        "research_lineage_roots": target.research_lineage_roots,
        "provenance_roots": target.provenance_roots,
        "claim_classes": target.claim_classes,
        "corroboration": target.corroboration,
        "adaptive_capability": target.adaptive_capability,
        "public_wording": target.public_wording,
        "component_contract_digests": target.component_contract_digests,
    }
    fields.update(changes)
    result = build_claim_contract(**fields)
    logger.debug("_changed_target exit")
    return result


def test_valid_local_receipts_without_license_do_not_license_aggregate(tmp_path) -> None:
    """Receipt multiplicity leaves license and aggregate statuses not established."""
    logger.debug("test_valid_local_receipts_without_license_do_not_license_aggregate entry")
    sources, target, _ = _positive_case(tmp_path)
    assessment = assess_claim_composition(sources, target, None)
    assert assessment.local_receipts_valid is CompositionStatus.ESTABLISHED
    assert assessment.aggregate_claim_well_formed is CompositionStatus.ESTABLISHED
    assert assessment.composition_license_established is CompositionStatus.NOT_ESTABLISHED
    assert assessment.aggregate_claim_licensed is CompositionStatus.NOT_ESTABLISHED
    assert assessment.obstructions == ("composition-license-missing",)
    logger.debug("test_valid_local_receipts_without_license_do_not_license_aggregate exit")


@pytest.mark.parametrize(
    ("changes", "reason"),
    (
        ({"scope_roots": (_digest("e"),)}, "scope-not-exact-union"),
        ({"claim_roots": (_digest("e"),)}, "claim-roots-not-exact-union"),
        ({"observer_roots": (_digest("e"),)}, "observer-binding-not-exact-union"),
        ({"doctrine_roots": (_digest("e"),)}, "doctrine-binding-not-exact-union"),
        ({"execution_lineage_roots": (_digest("e"),)}, "execution-lineage-not-exact-union"),
        ({"research_lineage_roots": (_digest("e"),)}, "research-lineage-not-exact-union"),
        ({"provenance_roots": (_digest("e"),)}, "provenance-binding-not-exact-union"),
        ({"quantifier": ClaimQuantifier.UNIVERSAL}, "quantifier-upgrade"),
        ({"quantifier": ClaimQuantifier.EXISTENTIAL}, "quantifier-upgrade"),
        (
            {"corroboration": CorroborationStatus.INDEPENDENT_CORROBORATION},
            "corroboration-upgrade",
        ),
        ({"corroboration": CorroborationStatus.AGREEMENT}, "corroboration-upgrade"),
        ({"adaptive_capability": AdaptiveCapability.FAMILY_VALID}, "adaptive-capability-upgrade"),
        ({"adaptive_capability": AdaptiveCapability.ADAPTIVE_VALID}, "adaptive-capability-upgrade"),
        ({"public_wording": PublicWording.SIGNIFICANCE}, "public-wording-upgrade"),
        ({"public_wording": PublicWording.FAMILY_INFERENCE}, "public-wording-upgrade"),
        ({"public_wording": PublicWording.POPULATION}, "public-wording-upgrade"),
        (
            {"claim_classes": (ClaimClass.EMPIRICAL, ClaimClass.EPISTEMIC)},
            "claim-class-reinterpretation",
        ),
        ({"claim_classes": (ClaimClass.OBJECTIVITY,)}, "claim-class-reinterpretation"),
        ({"component_contract_digests": (_digest("e"),)}, "component-contracts-not-exact"),
    ),
)
def test_every_implicit_contract_upgrade_is_unlicensed(tmp_path, changes, reason) -> None:
    """A valid license for another target cannot survive one semantic-axis upgrade."""
    logger.debug("test_every_implicit_contract_upgrade_is_unlicensed entry reason=%s", reason)
    sources, target, license = _positive_case(tmp_path)
    changed = _changed_target(target, **changes)
    assessment = assess_claim_composition(sources, changed, license)
    assert assessment.local_receipts_valid is CompositionStatus.ESTABLISHED
    assert assessment.aggregate_claim_well_formed is CompositionStatus.ESTABLISHED
    assert assessment.composition_license_established is CompositionStatus.NOT_ESTABLISHED
    assert assessment.aggregate_claim_licensed is CompositionStatus.NOT_ESTABLISHED
    assert "composition-license-target-mismatch" in assessment.obstructions
    assert reason in assessment.obstructions
    logger.debug("test_every_implicit_contract_upgrade_is_unlicensed exit")


def test_exact_rule_rejects_counterevidence_and_noncanonical_sources(tmp_path) -> None:
    """Only distinct canonical local-claim sources may enter the v1 conjunction rule."""
    logger.debug("test_exact_rule_rejects_counterevidence_and_noncanonical_sources entry")
    sources, target, _ = _positive_case(tmp_path)
    reversed_sources = tuple(reversed(sources))
    if reversed_sources != sources:
        with pytest.raises(ClaimCompositionError, match="noncanonical-composition-sources"):
            build_exact_conjunction_contract(reversed_sources)
    diagnostic = replace(sources[0], effect=SourceEffect.DIAGNOSTIC_ONLY)
    altered = canonical_composition_sources((diagnostic, sources[1]))
    with pytest.raises(ClaimCompositionError, match="exact-conjunction-source-effect"):
        build_exact_conjunction_contract(altered)
    counterevidence = replace(sources[0], effect=SourceEffect.COUNTEREVIDENCE)
    counterevidence_sources = canonical_composition_sources((counterevidence, sources[1]))
    with pytest.raises(ClaimCompositionError, match="exact-conjunction-source-effect"):
        build_exact_conjunction_contract(counterevidence_sources)
    with pytest.raises(ClaimCompositionError, match="duplicate-composition-source"):
        canonical_composition_sources((sources[0], sources[0]))
    assert target.quantifier is ClaimQuantifier.FINITE_CONJUNCTION
    logger.debug("test_exact_rule_rejects_counterevidence_and_noncanonical_sources exit")


def test_assumption_discharge_and_unconditional_aggregate_are_unlicensed() -> None:
    """The exact R_A/R_B fixture rejects dropping A and B from the aggregate target."""
    logger.debug("test_assumption_discharge_and_unconditional_aggregate_are_unlicensed entry")
    sources = _assumption_case()
    target = build_exact_conjunction_contract(sources)
    license = build_exact_conjunction_license(sources, target)
    unconditional = _changed_target(target, assumption_roots=())
    assessment = assess_claim_composition(sources, unconditional, license)
    assert assessment.local_receipts_valid is CompositionStatus.ESTABLISHED
    assert assessment.composition_license_established is CompositionStatus.NOT_ESTABLISHED
    assert assessment.aggregate_claim_licensed is CompositionStatus.NOT_ESTABLISHED
    assert "assumptions-not-exact-union" in assessment.obstructions
    logger.debug("test_assumption_discharge_and_unconditional_aggregate_are_unlicensed exit")


@pytest.mark.requires_posix_file_locks
def test_valid_shaped_blocked_source_keeps_local_and_aggregate_unestablished(tmp_path) -> None:
    """A replayable failed governed result cannot masquerade as local structural completion."""
    logger.debug("test_valid_shaped_blocked_source_keeps_local_and_aggregate_unestablished entry")
    ready = build_governed_composition_source(
        _governed_result(tmp_path / "ready", "a"), SourceEffect.INCLUDE_LOCAL_CLAIM
    )
    blocked = build_governed_composition_source(
        _governed_result(tmp_path / "blocked", "b", ready=False),
        SourceEffect.INCLUDE_LOCAL_CLAIM,
    )
    sources = canonical_composition_sources((ready, blocked))
    target = build_exact_conjunction_contract(sources)
    license = build_exact_conjunction_license(sources, target)
    assessment = assess_claim_composition(sources, target, license)
    assert assessment.local_receipts_valid is CompositionStatus.NOT_ESTABLISHED
    assert assessment.composition_license_established is CompositionStatus.ESTABLISHED
    assert assessment.aggregate_claim_licensed is CompositionStatus.NOT_ESTABLISHED
    assert assessment.obstructions == ("local-receipts-not-established",)
    logger.debug("test_valid_shaped_blocked_source_keeps_local_and_aggregate_unestablished exit")


def test_forged_license_receipt_and_export_fail_closed(tmp_path) -> None:
    """Direct DTO construction and digest drift cannot bypass fresh export replay."""
    logger.debug("test_forged_license_receipt_and_export_fail_closed entry")
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    forged_license = replace(license, capability_roots=(_digest("e"),))
    assert not validate_composition_license_shape(forged_license)
    forged_receipt = replace(receipt, p2_promotion_established=True)
    assert not validate_composition_receipt(forged_receipt, sources, target, license)
    with pytest.raises(ClaimCompositionError, match="public-export-unlicensed"):
        composition_disclosure_json(forged_receipt, sources, target, license)
    with pytest.raises(ClaimCompositionError, match="aggregate-claim-not-licensed"):
        build_composition_receipt(sources, _changed_target(target, public_wording=PublicWording.POPULATION), license)
    logger.debug("test_forged_license_receipt_and_export_fail_closed exit")


def test_resource_and_exact_type_boundaries_precede_composition(tmp_path) -> None:
    """Oversized roots, list substitution, and receipt subclasses fail closed."""
    logger.debug("test_resource_and_exact_type_boundaries_precede_composition entry")
    sources, target, _ = _positive_case(tmp_path)
    with pytest.raises(ClaimCompositionError, match="claim-roots"):
        _changed_target(target, claim_roots=tuple(f"{index:064x}" for index in range(257)))
    with pytest.raises(ClaimCompositionError, match="scope-roots"):
        _changed_target(target, scope_roots=list(target.scope_roots))

    class ReceiptSubclass(LocalClaimReceipt):
        pass

    original = sources[0].receipt
    hostile_receipt = ReceiptSubclass(
        original.contract,
        original.source_receipt_root,
        original.source_validator_root,
        original.validity,
        original.receipt_digest,
    )
    hostile = replace(sources[0], receipt=hostile_receipt)
    with pytest.raises(ClaimCompositionError, match="external-composition-source"):
        build_exact_conjunction_contract((hostile, sources[1]))
    with pytest.raises(ClaimCompositionError, match="composition-source-count"):
        canonical_composition_sources(tuple(sources[0] for _ in range(65)))
    with pytest.raises(ClaimCompositionError, match="contract-total-roots"):
        _changed_target(
            target,
            claim_roots=tuple(f"{index:064x}" for index in range(200)),
            scope_roots=tuple(f"{index + 200:064x}" for index in range(200)),
            assumption_roots=tuple(f"{index + 400:064x}" for index in range(200)),
            observer_roots=tuple(f"{index + 600:064x}" for index in range(200)),
            doctrine_roots=tuple(f"{index + 800:064x}" for index in range(200)),
            execution_lineage_roots=tuple(f"{index + 1000:064x}" for index in range(25)),
        )
    logger.debug("test_resource_and_exact_type_boundaries_precede_composition exit")


@pytest.mark.requires_posix_file_locks
def test_output_precharge_and_hostile_nested_source_fail_closed(tmp_path, monkeypatch) -> None:
    """Aggregate outputs are precharged and hostile governed substitutes are never dereferenced."""
    logger.debug("test_output_precharge_and_hostile_nested_source_fail_closed entry")
    source = build_governed_composition_source(
        _governed_result(tmp_path / "governed", "a"),
        SourceEffect.INCLUDE_LOCAL_CLAIM,
    )
    monkeypatch.setattr(composition_protocol, "MAX_COMPOSITION_OUTPUT_UNITS", 1)
    with pytest.raises(ClaimCompositionError, match="composition-output-units"):
        canonical_composition_sources((source,))
    monkeypatch.setattr(composition_protocol, "MAX_COMPOSITION_OUTPUT_UNITS", 2_000_000)

    class Hostile:
        @property
        def worker_receipt(self):
            logger.error("Hostile.worker_receipt must not be reached")
            raise RuntimeError("hostile getter reached")

    hostile = ClaimCompositionSource(Hostile(), source.receipt, SourceEffect.INCLUDE_LOCAL_CLAIM)
    with pytest.raises(ClaimCompositionError, match="composition-governed-source-type"):
        canonical_composition_sources((hostile,))

    class HostileWorker:
        @property
        def outputs(self):
            logger.error("HostileWorker.outputs must not be reached")
            raise RuntimeError("nested worker getter reached")

    governed = source.governed_result
    assert governed is not None
    nested = replace(governed, worker_receipt=HostileWorker())
    nested_hostile = replace(source, governed_result=nested)
    with pytest.raises(ClaimCompositionError, match="composition-worker-receipt-type"):
        canonical_composition_sources((nested_hostile,))
    logger.debug("test_output_precharge_and_hostile_nested_source_fail_closed exit")
