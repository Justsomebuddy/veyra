"""Nonpromoting CompositionReceipt-to-P2 premise bridge controls."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core.claim_composition import (
    COMPOSITION_PREMISE_BOUNDARY,
    COMPOSITION_PREMISE_KIND,
    ClaimCompositionError,
    build_composition_p2_premise,
    build_composition_receipt,
    validate_composition_p2_premise,
)
from src.core.status_promotion import (
    EvidenceStatus,
    JudgmentKind,
    PositiveProvenance,
    StatusPromotionValidationError,
    audit_promotion_request,
    claim_descriptor,
    index_binding,
    promotion_audit_request,
    promotion_policy,
    promotion_registry,
    audit_registry_against_literal_oracle,
)
from src.core.status_promotion_oracle import LITERAL_ORACLE_DIGEST

from test_claim_composition import _positive_case

logger = logging.getLogger(__name__)


def test_composition_receipt_becomes_exact_nonpromoting_p2_premise(tmp_path) -> None:
    """The adapter retains target/license/source evidence but establishes no conclusion."""
    logger.debug("test_composition_receipt_becomes_exact_nonpromoting_p2_premise entry")
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    artifact = build_composition_p2_premise(receipt, sources, target, license)

    assert validate_composition_p2_premise(artifact, receipt, sources, target, license)
    assert artifact.premise_name == "composition"
    assert artifact.artifact_kind == COMPOSITION_PREMISE_KIND
    assert artifact.artifact_digest == receipt.receipt_digest
    assert artifact.indices == ()
    assert tuple(item.name for item in artifact.evidence_fields) == (
        "target-contract",
        "composition-license",
        "composition-assessment",
        "source-family",
        "nonpromotion",
    )
    assert "no P2 rule" in COMPOSITION_PREMISE_BOUNDARY
    assert receipt.p2_promotion_established is False
    logger.debug("test_composition_receipt_becomes_exact_nonpromoting_p2_premise exit")


def test_composition_p2_premise_rejects_replay_drift_and_has_no_generic_rule(tmp_path) -> None:
    """A forged receipt fails and the canonical P2 registry cannot consume the new kind."""
    logger.debug("test_composition_p2_premise_rejects_replay_drift_and_has_no_generic_rule entry")
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    with pytest.raises(ClaimCompositionError, match="composition-p2-replay"):
        build_composition_p2_premise(
            replace(receipt, assessment_digest="0" * 64),
            sources,
            target,
            license,
        )

    artifact = build_composition_p2_premise(receipt, sources, target, license)
    registry = promotion_registry()
    assert registry.version == "p2-s-promotion-registry-v1"
    assert registry.registry_digest == "375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d"
    assert len(registry.rules) == 17
    assert len(registry.premise_projections) == 40
    assert audit_registry_against_literal_oracle(registry) == LITERAL_ORACLE_DIGEST
    assert all(
        signature.artifact_kind != COMPOSITION_PREMISE_KIND
        for rule in registry.rules
        for signature in rule.premise_signatures
    )
    conclusion = claim_descriptor(
        "composition-cannot-self-promote",
        JudgmentKind.COHERENT,
        EvidenceStatus.ESTABLISHED_RELATIVE_TO_SCOPE,
        PositiveProvenance.EXECUTABLE_REPLAY,
        (
            index_binding("doctrine", target.contract_digest),
            index_binding("scope", target.contract_digest),
        ),
        registry,
    )
    request = promotion_audit_request(
        "generic-composition-v1",
        (artifact,),
        (),
        conclusion,
        registry,
    )
    with pytest.raises(StatusPromotionValidationError, match="unknown-or-duplicate-promotion-rule"):
        audit_promotion_request(registry, request, promotion_policy())
    logger.debug("test_composition_p2_premise_rejects_replay_drift_and_has_no_generic_rule exit")
