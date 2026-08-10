"""Nonpromoting claim projection for bounded observer-discovery reports.

The projection describes what one valid report licenses.  It deliberately
does not turn an R5 research observer into a P0-admitted observer, a dataset
into an object, or an association into causality, explanation, or theoremhood.
"""

from __future__ import annotations

from dataclasses import replace
import logging

from .observer_discovery import BLOCKED, FOUND, NOT_FOUND_WITHIN_BUDGET
from .observer_discovery_claim_types import (
    ClaimDisposition,
    DiscoveryClaimEnvelope,
    DiscoveryClaimScope,
    DiscoveryExecutionLevel,
    DiscoveryInterpretationLevel,
    DiscoveryObserverRole,
    DiscoveryOntologyLevel,
)
from .observer_discovery_types import ObserverDiscoveryReport
from .observer_discovery_validation import validate_discovery_report
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

_CLAIM_DOMAIN = "veyra.observer-discovery.claim.v1"


def observer_discovery_claim(
    report: ObserverDiscoveryReport,
    *,
    expected_train_evaluation: str | None = None,
) -> DiscoveryClaimEnvelope:
    """Project one valid report into an explicit nonpromoting claim tuple."""
    logger.debug(
        "observer_discovery_claim entry status=%s",
        getattr(report, "status", "<invalid>"),
    )
    if not validate_discovery_report(
        report,
        expected_train_evaluation=expected_train_evaluation,
    ):
        logger.error("observer_discovery_claim rejected invalid report")
        raise ValueError("invalid-discovery-report")

    execution, interpretation, association, absence = _claim_levels(report.status)
    scope = _claim_scope(report)
    draft = DiscoveryClaimEnvelope(
        source_status=report.status,
        execution=execution,
        interpretation=interpretation,
        ontology=DiscoveryOntologyLevel.PRESENTATION_ONLY,
        observer_role=DiscoveryObserverRole.RESEARCH_SHADOW,
        association_witness=association,
        bounded_search_nonfinding=absence,
        causality=ClaimDisposition.NOT_CLAIMED,
        semantic_explanation=ClaimDisposition.NOT_CLAIMED,
        theoremhood=ClaimDisposition.NOT_CLAIMED,
        object_formation=ClaimDisposition.NOT_CLAIMED,
        p0_admission=ClaimDisposition.NOT_CLAIMED,
        historical_novelty=ClaimDisposition.NOT_CLAIMED,
        scope=scope,
        claim_digest="",
    )
    result = replace(draft, claim_digest=_claim_digest(draft))
    logger.debug(
        "observer_discovery_claim exit execution=%s interpretation=%s",
        result.execution.value,
        result.interpretation.value,
    )
    return result


def validate_observer_discovery_claim(
    claim: object,
    report: ObserverDiscoveryReport,
    *,
    expected_train_evaluation: str | None = None,
) -> bool:
    """Rebuild a claim from its source report and require exact equality."""
    logger.debug(
        "validate_observer_discovery_claim entry type=%s",
        type(claim).__name__,
    )
    if type(claim) is not DiscoveryClaimEnvelope:
        logger.error("validate_observer_discovery_claim rejected claim type")
        return False
    try:
        expected = observer_discovery_claim(
            report,
            expected_train_evaluation=expected_train_evaluation,
        )
    except (AttributeError, TypeError, ValueError):
        logger.error("validate_observer_discovery_claim rejected source report")
        return False
    valid = claim == expected
    if not valid:
        logger.error("validate_observer_discovery_claim rejected claim drift")
    logger.debug("validate_observer_discovery_claim exit valid=%s", valid)
    return valid


def _claim_levels(
    status: str,
) -> tuple[
    DiscoveryExecutionLevel,
    DiscoveryInterpretationLevel,
    ClaimDisposition,
    ClaimDisposition,
]:
    logger.debug("_claim_levels entry status=%s", status)
    if status == FOUND:
        result = (
            DiscoveryExecutionLevel.LOCKED_HOLDOUT_PASSED,
            DiscoveryInterpretationLevel.DECLARED_BASELINE_GAP,
            ClaimDisposition.SUPPORTED,
            ClaimDisposition.NOT_CLAIMED,
        )
    elif status == NOT_FOUND_WITHIN_BUDGET:
        result = (
            DiscoveryExecutionLevel.BOUNDED_SEARCH_COMPLETE,
            DiscoveryInterpretationLevel.NONE,
            ClaimDisposition.NOT_ESTABLISHED,
            ClaimDisposition.SUPPORTED,
        )
    elif status == BLOCKED:
        result = (
            DiscoveryExecutionLevel.BLOCKED,
            DiscoveryInterpretationLevel.NONE,
            ClaimDisposition.NOT_CLAIMED,
            ClaimDisposition.NOT_CLAIMED,
        )
    else:  # The report validator should make this unreachable.
        logger.error("_claim_levels rejected unknown status")
        raise ValueError("unknown-discovery-status")
    logger.debug("_claim_levels exit execution=%s", result[0].value)
    return result


def _claim_scope(report: ObserverDiscoveryReport) -> DiscoveryClaimScope:
    logger.debug("_claim_scope entry status=%s", report.status)
    result = DiscoveryClaimScope(
        protocol_digest=report.digests.protocol,
        result_digest=report.digests.result,
        grammar_digest=report.digests.grammar,
        train_data_digest=report.digests.train_data,
        holdout_data_digest=report.digests.holdout_data,
        catalog_digest=report.digests.catalog,
        boundary=report.boundary,
    )
    logger.debug("_claim_scope exit")
    return result


def _claim_digest(claim: DiscoveryClaimEnvelope) -> str:
    logger.debug("_claim_digest entry status=%s", claim.source_status)
    result = digest_data(_claim_data(claim), _CLAIM_DOMAIN)
    logger.debug("_claim_digest exit digest=%s", result[:12])
    return result


def _claim_data(claim: DiscoveryClaimEnvelope) -> dict[str, object]:
    logger.debug("_claim_data entry status=%s", claim.source_status)
    result = {
        "source_status": claim.source_status,
        "execution": claim.execution.value,
        "interpretation": claim.interpretation.value,
        "ontology": claim.ontology.value,
        "observer_role": claim.observer_role.value,
        "claims": {
            "association_witness": claim.association_witness.value,
            "bounded_search_nonfinding": claim.bounded_search_nonfinding.value,
            "causality": claim.causality.value,
            "semantic_explanation": claim.semantic_explanation.value,
            "theoremhood": claim.theoremhood.value,
            "object_formation": claim.object_formation.value,
            "p0_admission": claim.p0_admission.value,
            "historical_novelty": claim.historical_novelty.value,
        },
        "scope": {
            "protocol": claim.scope.protocol_digest,
            "result": claim.scope.result_digest,
            "grammar": claim.scope.grammar_digest,
            "train_data": claim.scope.train_data_digest,
            "holdout_data": claim.scope.holdout_data_digest,
            "catalog": claim.scope.catalog_digest,
            "boundary": claim.scope.boundary,
        },
    }
    logger.debug("_claim_data exit")
    return result
