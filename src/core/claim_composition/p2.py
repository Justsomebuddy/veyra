"""Exact nonpromoting bridge from claim composition into P2 premise syntax."""

from __future__ import annotations

import logging

from ..proof_core_codec import digest_data
from ..status_promotion_types import PremiseArtifact
from ..status_promotion_validation import evidence_field, premise_artifact
from .protocol import ClaimCompositionError, validate_composition_receipt
from .types import ClaimCompositionSource, ClaimContract, CompositionLicense, CompositionReceipt

logger = logging.getLogger(__name__)

COMPOSITION_PREMISE_NAME = "composition"
COMPOSITION_PREMISE_KIND = "claim-composition-receipt"
COMPOSITION_PREMISE_BOUNDARY = (
    "validated composition may enter P2 only as typed premise syntax; no P2 rule, "
    "conclusion, promotion, assumption discharge, independence, or truth follows"
)


def build_composition_p2_premise(
    receipt: CompositionReceipt,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> PremiseArtifact:
    """Replay one exact composition and expose only its bound P2 premise artifact."""
    logger.debug("build_composition_p2_premise entry")
    if not validate_composition_receipt(receipt, sources, target, license):
        logger.error("build_composition_p2_premise rejected reason=composition-p2-replay")
        raise ClaimCompositionError("composition-p2-replay")
    result = premise_artifact(
        COMPOSITION_PREMISE_NAME,
        COMPOSITION_PREMISE_KIND,
        receipt.receipt_digest,
        (),
        (
            evidence_field("target-contract", target.contract_digest),
            evidence_field("composition-license", license.license_digest),
            evidence_field("composition-assessment", receipt.assessment_digest),
            evidence_field("source-family", _source_family_digest(receipt)),
            evidence_field("nonpromotion", _nonpromotion_digest(receipt)),
        ),
    )
    logger.info("build_composition_p2_premise state=TYPED_PREMISE promotion=False")
    logger.debug("build_composition_p2_premise exit digest=%s", result.artifact_digest[:12])
    return result


def validate_composition_p2_premise(
    value: object,
    receipt: CompositionReceipt,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> bool:
    """Freshly replay and exact-compare one composition-backed P2 premise."""
    logger.debug("validate_composition_p2_premise entry type=%s", type(value).__name__)
    try:
        valid = type(value) is PremiseArtifact and value == build_composition_p2_premise(
            receipt,
            sources,
            target,
            license,
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_p2_premise rejected")
        valid = False
    logger.debug("validate_composition_p2_premise exit valid=%s", valid)
    return valid


def _source_family_digest(receipt: CompositionReceipt) -> str:
    """Bind the already canonical source family without exposing its payloads."""
    logger.debug("_source_family_digest entry count=%d", len(receipt.source_receipt_digests))
    result = digest_data(
        {"source_receipt_digests": list(receipt.source_receipt_digests)},
        "veyra.claim-composition.p2-source-family.v1",
    )
    logger.debug("_source_family_digest exit")
    return result


def _nonpromotion_digest(receipt: CompositionReceipt) -> str:
    """Commit the permanent false promotion bit and the public bridge boundary."""
    logger.debug("_nonpromotion_digest entry")
    result = digest_data(
        {
            "p2_promotion_established": receipt.p2_promotion_established,
            "boundary": COMPOSITION_PREMISE_BOUNDARY,
        },
        "veyra.claim-composition.p2-nonpromotion.v1",
    )
    logger.debug("_nonpromotion_digest exit")
    return result
