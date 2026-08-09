"""Direct level-1 certificate for finite P1-E4 history-relative actualization."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..observer.actualization.core import (
    AccessKind, ActualizationStatus, ConsciousnessStatus,
    CounterfactualOutcome, HistoricalActualization, PhysicalInstantiation,
    access_edge, historical_actualization_judgment,
    validate_actualization_result,
)
from ..observer.actualization.certificate_fixture import certificate_source

logger = logging.getLogger(__name__)


def certify_observer_actualization_p1e4() -> Certificate:
    """Certify one exact finite HAP witness and its mandatory pressures."""
    logger.debug("certify_observer_actualization_p1e4 entry")
    source = certificate_source()
    result = historical_actualization_judgment(source)
    fresh = validate_actualization_result(source, result)
    alternative = certificate_source("target-c")
    alternate_result = historical_actualization_judgment(alternative)
    leak_source = certificate_source(access_edges=(
        access_edge("target", "construction", AccessKind.TARGET_READ),
    ))
    leak = historical_actualization_judgment(leak_source)
    statuses = (
        result.oep_role, result.prior_construction, result.birth_event,
        result.target_independence, result.post_birth_efficacy,
    )
    passed = (
        len(source.events) == 6
        and result.past_event_ids == ("construction", "oep")
        and result.future_event_ids == ("target", "intervention", "response")
        and len(result.counterfactual_evidence) == 3
        and all(
            item.outcome is CounterfactualOutcome.PASSED
            for item in result.counterfactual_evidence
        )
        and statuses == (ActualizationStatus.ESTABLISHED,) * 5
        and result.historical_actualization
        is HistoricalActualization.ESTABLISHED_RELATIVE_TO_HISTORY
        and fresh == result and fresh is not result
        and source.birth_core_digest == alternative.birth_core_digest
        and source.historical_token_id == alternative.historical_token_id
        and source.history_digest != alternative.history_digest
        and result.actualization_judgment_digest
        != alternate_result.actualization_judgment_digest
        and leak.target_independence is ActualizationStatus.REFUTED
        and leak.historical_actualization is HistoricalActualization.OPEN
        and result.physical_instantiation is PhysicalInstantiation.NOT_ESTABLISHED
        and result.consciousness is ConsciousnessStatus.NOT_CLAIMED
    )
    detail = (
        "events=6/6 past=2/2 future=3/3 counterfactuals=3/3 "
        "leak_refuted=1 birth_stable=1 actualized=1 "
        "physical_claims=0 consciousness_claims=0"
    )
    certificate = Certificate(
        "observer_actualization_p1e4",
        "finite history-relative HAP; no physical or consciousness claim",
        passed, detail, 1,
    )
    logger.debug("certify_observer_actualization_p1e4 exit passed=%s", passed)
    return certificate
