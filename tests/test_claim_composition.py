"""Positive replay and public-export controls for issue-18 composition."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimQuantifier,
    CompositionStatus,
    CorroborationStatus,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
    assess_claim_composition,
    build_claim_contract,
    build_composition_receipt,
    build_exact_conjunction_contract,
    build_exact_conjunction_license,
    build_external_composition_source,
    build_governed_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
    composition_disclosure_json,
    validate_composition_assessment,
    validate_composition_license_shape,
    validate_composition_receipt,
)
from src.core.observer_discovery_v3.dsl import closed_rows_digest, observer_program_digest
from src.core.observer_discovery_v3.dsl.types import ClosedObserverGrammar, ClosedObserverTerm
from src.core.observer_discovery_v3.ledger import OneShotReservation, reserve_one_shot
from src.core.observer_discovery_v3.schema import (
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
)
from src.core.observer_discovery_v3.service import execute_one_shot_closed_evaluation

logger = logging.getLogger(__name__)


def _digest(symbol: str) -> str:
    logger.debug("_digest entry symbol=%s", symbol)
    result = symbol * 64
    logger.debug("_digest exit")
    return result


def _governed_result(directory: Path, symbol: str, *, ready: bool = True):
    logger.debug("_governed_result entry symbol=%s ready=%s", symbol, ready)
    directory.mkdir(mode=0o700)
    schema = RepresentationSchema(
        f"composition-{symbol}",
        (RepresentationField("bit", "binary", (0, 1)),),
        ("no", "yes"),
    )
    presentation = canonical_presentation(
        schema,
        (
            RepresentationRow(f"{symbol}0", "s0", "c0", "g0", (0,), "no"),
            RepresentationRow(f"{symbol}1", "s1", "c1", "g1", (1,), "yes"),
        ),
    )
    grammar = ClosedObserverGrammar(f"grammar-{symbol}", 1, (0,), ("column",), 1, 0, 1)
    terms = (ClosedObserverTerm("column", (0,)),)
    rows = tuple(tuple(row.values) for row in presentation.rows)
    reservation = OneShotReservation(
        f"reservation-{symbol}",
        "issue-18-positive-control",
        _digest(symbol),
        presentation.payload_digest if ready else _digest("e"),
        presentation.schema_digest,
        closed_rows_digest(rows),
        observer_program_digest(grammar, terms),
        _digest("f"),
    )
    capability = bytes.fromhex(_digest(symbol))
    reserve_one_shot(directory, reservation, capability)
    result = execute_one_shot_closed_evaluation(
        directory,
        reservation.reservation_id,
        capability,
        f"attempt-{symbol}",
        presentation,
        grammar,
        terms,
    )
    logger.debug("_governed_result exit status=%s", result.status)
    return result


def _positive_case(tmp_path: Path):
    logger.debug("_positive_case entry")
    del tmp_path
    sources = _assumption_case()
    target = build_exact_conjunction_contract(sources)
    license = build_exact_conjunction_license(sources, target)
    logger.debug("_positive_case exit")
    return sources, target, license


def _assumption_case():
    """Construct R_A: A -> P(x) and R_B: B -> P(y) under external validators."""
    logger.debug("_assumption_case entry")
    sources = []
    for claim, scope, assumption, validator in (
        ("c", f"{1:064x}", "a", f"{3:064x}"),
        ("d", f"{2:064x}", "b", f"{4:064x}"),
    ):
        contract = build_claim_contract(
            (_digest(claim),),
            (scope,),
            (_digest(assumption),),
            ClaimQuantifier.LOCAL,
            (),
            (),
            (),
            (),
            (),
            (ClaimClass.EMPIRICAL,),
            CorroborationStatus.SINGLE_LOCAL_RECEIPT,
            AdaptiveCapability.LOCAL_ONLY,
            PublicWording.BOUNDED_LOCAL,
        )
        receipt = build_local_claim_receipt(
            contract,
            _digest(claim),
            validator,
            LocalReceiptValidity.ESTABLISHED,
        )
        sources.append(build_external_composition_source(receipt, SourceEffect.INCLUDE_LOCAL_CLAIM))
    result = canonical_composition_sources(tuple(sources))
    logger.debug("_assumption_case exit")
    return result


def test_assumption_bearing_claims_license_only_retained_a_and_b() -> None:
    """R_A and R_B license their conjunction with A and B retained, never unconditional P."""
    logger.debug("test_assumption_bearing_claims_license_only_retained_a_and_b entry")
    sources = _assumption_case()
    target = build_exact_conjunction_contract(sources)
    license = build_exact_conjunction_license(sources, target)
    assessment = assess_claim_composition(sources, target, license)
    assert target.assumption_roots == tuple(sorted((_digest("a"), _digest("b"))))
    assert target.claim_roots == tuple(sorted((_digest("c"), _digest("d"))))
    assert assessment.aggregate_claim_licensed is CompositionStatus.ESTABLISHED
    logger.debug("test_assumption_bearing_claims_license_only_retained_a_and_b exit")


def test_exact_conjunction_replays_all_four_statuses_and_receipt(tmp_path: Path) -> None:
    """The positive rule preserves every source contract and does not promote P2."""
    logger.debug("test_exact_conjunction_replays_all_four_statuses_and_receipt entry")
    sources, target, license = _positive_case(tmp_path)
    assessment = assess_claim_composition(sources, target, license)
    assert assessment.local_receipts_valid is CompositionStatus.ESTABLISHED
    assert assessment.aggregate_claim_well_formed is CompositionStatus.ESTABLISHED
    assert assessment.composition_license_established is CompositionStatus.ESTABLISHED
    assert assessment.aggregate_claim_licensed is CompositionStatus.ESTABLISHED
    assert not assessment.obstructions
    assert validate_composition_license_shape(license)
    assert validate_composition_assessment(assessment, sources, target, license)

    receipt = build_composition_receipt(sources, target, license)
    assert receipt.p2_promotion_established is False
    assert validate_composition_receipt(receipt, sources, target, license)
    logger.debug("test_exact_conjunction_replays_all_four_statuses_and_receipt exit")


@pytest.mark.requires_posix_file_locks
def test_governed_ready_adapter_is_structural_completion_only(tmp_path: Path) -> None:
    """The POSIX one-shot adapter binds execution evidence without inventing assumptions."""
    logger.debug("test_governed_ready_adapter_is_structural_completion_only entry")
    source = build_governed_composition_source(
        _governed_result(tmp_path / "governed", "a"),
        SourceEffect.INCLUDE_LOCAL_CLAIM,
    )
    assert source.receipt.contract.assumption_roots == ()
    assert source.receipt.contract.research_lineage_roots == ()
    assert source.receipt.contract.execution_lineage_roots
    assert source.receipt.contract.claim_classes == (ClaimClass.STRUCTURAL,)
    assert source.receipt.contract.public_wording is PublicWording.EVALUATION_COMPLETION
    logger.debug("test_governed_ready_adapter_is_structural_completion_only exit")


def test_public_export_is_canonical_and_keeps_scope_and_nonpromotion(tmp_path: Path) -> None:
    """The sole public renderer freshly replays and emits structured bounded wording."""
    logger.debug("test_public_export_is_canonical_and_keeps_scope_and_nonpromotion entry")
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    first = composition_disclosure_json(receipt, sources, target, license)
    second = composition_disclosure_json(receipt, sources, target, license)
    assert first == second
    payload = json.loads(first)
    assert payload["target_contract"]["assumption_roots"] == list(target.assumption_roots)
    assert payload["target_contract"]["quantifier"] == "FINITE_CONJUNCTION"
    assert payload["target_contract"]["public_wording"] == "CONJUNCTIVE_SUMMARY"
    assert payload["target_contract"]["claim_classes"] == ["EMPIRICAL"]
    assert payload["receipt"]["p2_promotion_established"] is False
    assert payload["receipt"]["receipt_digest"] == receipt.receipt_digest
    assert payload["license"]["license_digest"] == license.license_digest
    assert payload["assessment"]["aggregate_claim_licensed"] == "ESTABLISHED"
    logger.debug("test_public_export_is_canonical_and_keeps_scope_and_nonpromotion exit")


@pytest.mark.requires_posix_file_locks
def test_nary_source_canonicalization_is_permutation_independent(tmp_path: Path) -> None:
    """The bounded N-ary bundle has one order independent of caller permutation."""
    logger.debug("test_nary_source_canonicalization_is_permutation_independent entry")
    left = build_governed_composition_source(
        _governed_result(tmp_path / "left", "c"), SourceEffect.INCLUDE_LOCAL_CLAIM
    )
    right = build_governed_composition_source(
        _governed_result(tmp_path / "right", "d"), SourceEffect.INCLUDE_LOCAL_CLAIM
    )
    assert canonical_composition_sources((left, right)) == canonical_composition_sources((right, left))
    logger.debug("test_nary_source_canonicalization_is_permutation_independent exit")
