"""Level-3 finite executable certificate for the isolated R14 pipeline."""
from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer_synthesis_v2_pipeline import (
    PIPELINE_BOUNDARY,
    run_observer_synthesis_v2_pipeline,
)
from ..observer_synthesis_v2_pipeline_types import (
    OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
    ObserverSynthesisEvidenceV2,
    ObserverSynthesisPipelineResultV2,
)
from ..observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)

R14_CERTIFICATE_NAME = "observer_synthesis_v2_r14"
R14_CERTIFICATE_METHOD = (
    "finite executable five-plus-one isolated audit; not a theorem, formal "
    "proof, R8 evidence, or promotion contract"
)
R14_CERTIFICATE_DETAIL = (
    "subjects=5 cases=10 required=8/8 diagnostic=0/2 receipts=10 "
    "bundle=740f55aa23a8372d taxonomy=2/4/25/5 layers=36 nonclaims=8"
)
_EXPECTED_PINS = (
    "07dbfe7567f86a2817bd01317ceb14e8c8650fd2ed488a7e1a6a7aad5f890f48",
    "4de40e8fdc41475c7e2f39d4370aecb0447e1b73b0254d723d17b1dc49221317",
    "56287ca10c7de90bb04bb4794ad6fb455511675304357031370b76866531dba9",
    "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb",
    "0afbd94886cef42dc5dda3a3b923f7766948bc53a32fca7481a1b861a3b54720",
    "740f55aa23a8372d01db506e1019cbab2bdb5990796c6c3b158ec048286b0895",
)


def _exact_finite_evidence(value: object) -> bool:
    """Check the aggregate DTO without replaying trial or receipt semantics."""
    logger.debug("_exact_finite_evidence entry type=%s", type(value).__name__)
    if type(value) is not ObserverSynthesisEvidenceV2:
        logger.error("_exact_finite_evidence wrong type")
        return False
    try:
        fields = (
            value.trial_report_digest, value.manifest_digest,
            value.guarantee_digest, value.trial_limits_digest,
            value.receipt_limits_digest, value.receipt_bundle_bytes,
            value.receipt_bundle_sha256, value.receipt_bundle_digest,
            value.subjects, value.cases, value.required_matched,
            value.required_total, value.diagnostic_matched,
            value.diagnostic_total, value.receipt_rows,
            value.taxonomy_counts, value.layers,
            value.general_completeness, value.general_minimality,
            value.novelty, value.superiority, value.evidence_accepted,
            value.promotion_ready, value.taxonomy_changed,
            value.proof_complete, value.boundary,
        )
    except AttributeError:
        logger.exception("_exact_finite_evidence deleted slot")
        return False
    str_indexes = (0, 1, 2, 3, 4, 6, 7, 25)
    int_indexes = (5, 8, 9, 10, 11, 12, 13, 14, 16)
    bool_indexes = tuple(range(17, 25))
    taxonomy = fields[15]
    if (
        any(type(fields[index]) is not str for index in str_indexes)
        or any(type(fields[index]) is not int for index in int_indexes)
        or any(type(fields[index]) is not bool for index in bool_indexes)
        or type(taxonomy) is not tuple
        or any(type(item) is not int for item in taxonomy)
    ):
        logger.error("_exact_finite_evidence scalar type mismatch")
        return False
    pins = fields[:4] + fields[6:8]
    passed = (
        pins == _EXPECTED_PINS
        and fields[4] == _EXPECTED_PINS[3]
        and fields[5] == 27_857
        and fields[8:15] == (5, 10, 8, 8, 0, 2, 10)
        and taxonomy == (2, 4, 25, 5)
        and fields[16] == 36
        and all(flag is False for flag in fields[17:25])
        and fields[25] == PIPELINE_BOUNDARY
    )
    logger.debug("_exact_finite_evidence exit passed=%s", passed)
    return passed


def certify_observer_synthesis_v2_r14() -> Certificate:
    """Certify only the fixed finite executable audit and its nonclaims."""
    logger.debug("certify_observer_synthesis_v2_r14 entry")
    try:
        aggregate = run_observer_synthesis_v2_pipeline()
        if type(aggregate) is not ObserverSynthesisPipelineResultV2:
            raise TypeError("R14 aggregate requires exact terminal type")
        try:
            fields = (
                aggregate.schema, aggregate.status,
                aggregate.detail, aggregate.evidence,
            )
        except AttributeError as error:
            raise TypeError("R14 aggregate requires complete slots") from error
        passed = (
            type(fields[0]) is str
            and type(fields[1]) is SynthesisStatus
            and type(fields[2]) is str
            and fields[0] == OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA
            and fields[1] is SynthesisStatus.FOUND
            and fields[2] == "observer-synthesis-v2-aggregate-complete"
            and _exact_finite_evidence(fields[3])
        )
        detail = R14_CERTIFICATE_DETAIL
    except (AttributeError, OSError, RecursionError, RuntimeError, TypeError, ValueError) as error:
        logger.exception("certify_observer_synthesis_v2_r14 blocked")
        passed, detail = False, f"blocked={type(error).__name__}:{error}"
    result = Certificate(
        R14_CERTIFICATE_NAME,
        R14_CERTIFICATE_METHOD,
        passed,
        detail,
        3,
    )
    if not passed:
        logger.error("certify_observer_synthesis_v2_r14 failed detail=%s", detail)
    logger.debug("certify_observer_synthesis_v2_r14 exit result=%r", result)
    return result
