"""Independent exact oracle for adaptive-retry family inflation."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

logger = logging.getLogger(__name__)
MAX_ORACLE_ATTEMPTS = 1_024
MAX_SAGE_ATTEMPTS = 256


@dataclass(frozen=True, slots=True)
class AdaptiveRetryOracleRow:
    """Exact family-positive probability under independent null attempts."""

    attempts: int
    alpha_numerator: int
    alpha_denominator: int
    any_positive_numerator: int
    any_positive_denominator: int
    sage_crosscheck_passed: bool

    def as_dict(self) -> dict[str, object]:
        """Return one JSON-ready exact row."""
        logger.debug("AdaptiveRetryOracleRow.as_dict entry attempts=%d", self.attempts)
        result: dict[str, object] = {
            "attempts": self.attempts,
            "alpha": (self.alpha_numerator, self.alpha_denominator),
            "any_positive": (self.any_positive_numerator, self.any_positive_denominator),
            "decimal": self.any_positive_numerator / self.any_positive_denominator,
            "sage_crosscheck_passed": self.sage_crosscheck_passed,
        }
        logger.debug("AdaptiveRetryOracleRow.as_dict exit")
        return result


def adaptive_retry_oracle(
    attempts: int,
    alpha_numerator: int,
    alpha_denominator: int,
    *,
    require_sage: bool = False,
) -> AdaptiveRetryOracleRow:
    """Compute the independent-null union probability and optionally cross-check Sage."""
    logger.debug("adaptive_retry_oracle entry attempts=%r", attempts)
    if type(attempts) is not int or not 1 <= attempts <= MAX_ORACLE_ATTEMPTS:
        logger.error("adaptive_retry_oracle attempt limit rejected")
        raise ValueError("adaptive-retry-oracle-attempt-limit")
    if (
        type(alpha_numerator) is not int
        or type(alpha_denominator) is not int
        or not 0 < alpha_numerator < alpha_denominator <= 1_000_000
    ):
        logger.error("adaptive_retry_oracle alpha rejected")
        raise ValueError("adaptive-retry-oracle-alpha")
    alpha = Fraction(alpha_numerator, alpha_denominator)
    probability = 1 - (1 - alpha) ** attempts
    sage_passed = False
    if require_sage:
        if attempts > MAX_SAGE_ATTEMPTS:
            logger.error("adaptive_retry_oracle Sage attempt limit rejected")
            raise ValueError("adaptive-retry-oracle-sage-attempt-limit")
        try:
            from sage.all import QQ, binomial  # type: ignore[import-not-found]
        except ImportError as exc:
            logger.error("adaptive_retry_oracle real Sage unavailable")
            raise RuntimeError("real-sage-required-for-adaptive-retry-oracle") from exc
        sage_alpha = QQ(alpha.numerator) / QQ(alpha.denominator)
        complement = (1 - sage_alpha) ** attempts
        binomial_sum = sum(
            binomial(attempts, positives)
            * sage_alpha**positives
            * (1 - sage_alpha) ** (attempts - positives)
            for positives in range(1, attempts + 1)
        )
        sage_passed = (
            1 - complement == binomial_sum
            and int(binomial_sum.numerator()) == probability.numerator
            and int(binomial_sum.denominator()) == probability.denominator
        )
        if not sage_passed:
            logger.error("adaptive_retry_oracle Sage drift")
            raise RuntimeError("adaptive-retry-oracle-sage-drift")
    result = AdaptiveRetryOracleRow(
        attempts,
        alpha.numerator,
        alpha.denominator,
        probability.numerator,
        probability.denominator,
        sage_passed,
    )
    logger.debug("adaptive_retry_oracle exit probability=%d/%d", probability.numerator, probability.denominator)
    return result


class VeyraAdaptiveResearchLineLab:
    """JSON-ready facade for the independent adaptive-retry oracle."""

    def retry_summary(
        self,
        attempts: int = 20,
        alpha_numerator: int = 1,
        alpha_denominator: int = 20,
        *,
        require_sage: bool = False,
    ) -> dict[str, object]:
        """Return exact inflation and the strict interpretation boundary."""
        logger.debug("VeyraAdaptiveResearchLineLab.retry_summary entry")
        row = adaptive_retry_oracle(
            attempts,
            alpha_numerator,
            alpha_denominator,
            require_sage=require_sage,
        )
        result = {
            "backend": "python+real-sage" if require_sage else "python",
            "row": row.as_dict(),
            "local_validity_composes": False,
            "adaptive_validity": "NOT_ESTABLISHED",
            "scope": "independent null attempts with exact per-attempt positive probability alpha",
            "nonclaims": (
                "not a model of every Veyra workflow",
                "not an alpha-spending, reusable-holdout, or anytime-valid policy",
                "not a significance or population-generalization license",
            ),
        }
        logger.debug("VeyraAdaptiveResearchLineLab.retry_summary exit")
        return result
