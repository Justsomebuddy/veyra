"""Exact adaptive-retry counterexample for repeated independent null attempts."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import logging

from ...proof_core_codec import digest_data
from .types import AdaptiveRetryWitness, AdaptiveValidityStatus

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 1_024
MAX_ALPHA_DENOMINATOR = 1_000_000


def adaptive_retry_witness(
    attempts: int = 20,
    alpha_numerator: int = 1,
    alpha_denominator: int = 20,
) -> AdaptiveRetryWitness:
    """Return exact `1-(1-alpha)^m` under explicit independent-null assumptions."""
    logger.debug(
        "adaptive_retry_witness entry attempts=%r alpha=%r/%r",
        attempts,
        alpha_numerator,
        alpha_denominator,
    )
    if type(attempts) is not int or not 1 <= attempts <= MAX_RETRY_ATTEMPTS:
        logger.error("adaptive_retry_witness attempt limit rejected")
        raise ValueError("adaptive-retry-attempt-limit")
    if (
        type(alpha_numerator) is not int
        or type(alpha_denominator) is not int
        or not 0 < alpha_numerator < alpha_denominator <= MAX_ALPHA_DENOMINATOR
    ):
        logger.error("adaptive_retry_witness alpha rejected")
        raise ValueError("adaptive-retry-alpha")
    alpha = Fraction(alpha_numerator, alpha_denominator)
    probability = 1 - (1 - alpha) ** attempts
    assumptions = (
        "each attempt is a genuinely independent null experiment",
        "each attempt has exact nominal positive probability alpha",
        "the procedure stops after the first positive or the declared attempt cap",
        "local protocol validity is separate from family-level inference validity",
    )
    draft = AdaptiveRetryWitness(
        attempts,
        alpha.numerator,
        alpha.denominator,
        probability.numerator,
        probability.denominator,
        True,
        False,
        AdaptiveValidityStatus.NOT_ESTABLISHED,
        assumptions,
        "",
    )
    result = replace(
        draft,
        witness_digest=digest_data(
            {
                "attempts": draft.attempts,
                "alpha": [draft.alpha_numerator, draft.alpha_denominator],
                "any_positive": [draft.any_positive_numerator, draft.any_positive_denominator],
                "local_protocol_validity_compatible": draft.local_protocol_validity_compatible,
                "family_policy_accounted": draft.family_policy_accounted,
                "adaptive_validity": draft.adaptive_validity.value,
                "assumptions": list(draft.assumptions),
            },
            "veyra.observer-discovery.adaptive-retry-witness.v1",
        ),
    )
    logger.debug("adaptive_retry_witness exit probability=%d/%d", probability.numerator, probability.denominator)
    return result


def validate_adaptive_retry_witness(value: object) -> bool:
    """Recompute one exact retry witness and every nonpromotion field."""
    logger.debug("validate_adaptive_retry_witness entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is AdaptiveRetryWitness
            and adaptive_retry_witness(
                value.attempts,
                value.alpha_numerator,
                value.alpha_denominator,
            )
            == value
        )
    except (AttributeError, OverflowError, TypeError, ValueError):
        logger.error("validate_adaptive_retry_witness rejected")
        valid = False
    logger.debug("validate_adaptive_retry_witness exit valid=%s", valid)
    return valid
