"""Hostile-output envelopes and fresh result replay for P3-N2."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .pressure import (
    OPEN_REASON, refute_pressure_candidate, report_missing_symbolic_evidence,
)
from .runtime import prime_power_reduction_judgment
from .types import (
    FiniteArrowJudgment, N2FormalFailure, N2Open,
    N2PressureKind, N2Refutation, N2ResourceLimit, PrimePowerReductionJudgment,
    ResultStatus,
)

logger = logging.getLogger(__name__)
MAX_ARROWS = 1024


def validate_prime_power_reduction_result(package, claimed):
    """Bound the claimed envelope before freshly replaying exact raw sources."""
    logger.debug("validate_prime_power_reduction_result entry")
    if type(claimed) is PrimePowerReductionJudgment:
        raw = exact_shape(claimed, PrimePowerReductionJudgment, "n2-judgment")
        arrows = raw["finite_arrows"]
        if type(arrows) is not tuple or len(arrows) > MAX_ARROWS:
            reject("n2-result-arrow-envelope-invalid")
        if any(type(x) is not FiniteArrowJudgment for x in arrows):
            reject("n2-result-arrow-type-invalid")
        for name in ("p3t_source_digest", "p3t_replay_digest", "theorem_source_digest",
                     "ledger_digest", "judgment_digest"):
            exact_digest(raw[name], f"n2-result-{name}")
        if type(raw["theorem_ids"]) is not tuple or len(raw["theorem_ids"]) != 7:
            reject("n2-result-theorem-envelope-invalid")
        if type(raw["axiom_rows"]) is not tuple or len(raw["axiom_rows"]) != 7:
            reject("n2-result-axiom-envelope-invalid")
        if type(raw["nonclaims"]) is not tuple or len(raw["nonclaims"]) > 64:
            reject("n2-result-nonclaim-envelope-invalid")
    elif type(claimed) is N2ResourceLimit:
        raw = exact_shape(claimed, N2ResourceLimit, "n2-resource")
        exact_digest(raw["package_digest"], "n2-resource-package")
        exact_digest(raw["refusal_digest"], "n2-resource-digest")
    elif type(claimed) is N2FormalFailure:
        raw = exact_shape(claimed, N2FormalFailure, "n2-formal-failure")
        if type(raw["diagnostic"]) is not str or len(raw["diagnostic"]) > 256:
            reject("n2-formal-diagnostic-invalid")
        exact_digest(raw["attempt_digest"], "n2-formal-attempt")
    else:
        reject("n2-result-exact-type-invalid")
    expected = prime_power_reduction_judgment(package)
    if claimed != expected:
        reject("n2-result-mismatch")
    logger.debug("validate_prime_power_reduction_result exit")
    return expected


def _validate_resource(value: N2ResourceLimit) -> None:
    """Validate an exact typed resource refusal envelope."""
    logger.debug("_validate_resource entry")
    raw = exact_shape(value, N2ResourceLimit, "n2-pressure-resource")
    if type(raw["status"]) is not ResultStatus or raw["status"] is not ResultStatus.RESOURCE_LIMIT:
        reject("n2-pressure-resource-status-invalid")
    if type(raw["required"]) is not int or type(raw["allowed"]) is not int:
        reject("n2-pressure-resource-scalars-invalid")
    exact_digest(raw["package_digest"], "n2-pressure-resource-package")
    exact_digest(raw["refusal_digest"], "n2-pressure-resource-digest")
    logger.debug("_validate_resource exit")


def _validate_failure(value: N2FormalFailure) -> None:
    """Validate an exact typed formal-failure envelope."""
    logger.debug("_validate_failure entry")
    raw = exact_shape(value, N2FormalFailure, "n2-pressure-formal-failure")
    exact_digest(raw["package_digest"], "n2-pressure-failure-package")
    exact_digest(raw["attempt_digest"], "n2-pressure-failure-attempt")
    if type(raw["diagnostic"]) is not str or len(raw["diagnostic"].encode()) > 4096:
        reject("n2-pressure-failure-diagnostic-invalid")
    logger.debug("_validate_failure exit")


def _validate_refutation(value: N2Refutation) -> None:
    """Bound an exact negative witness before fresh arithmetic replay."""
    logger.debug("_validate_refutation entry")
    raw = exact_shape(value, N2Refutation, "n2-refutation")
    if (type(raw["status"]) is not ResultStatus or raw["status"] is not ResultStatus.REFUTED
            or type(raw["kind"]) is not N2PressureKind):
        reject("n2-refutation-status-or-kind-invalid")
    if raw["kind"] is N2PressureKind.WRONG_SQUARE:
        if type(raw["family_id"]) is not str:
            reject("n2-refutation-square-family-invalid")
    elif raw["family_id"] is not None:
        reject("n2-refutation-path-family-invalid")
    path = raw["path_depths"]
    if (type(path) is not tuple or not 2 <= len(path) <= 32
            or any(type(x) is not int or x < 0 for x in path)
            or any(type(raw[name]) is not int or raw[name] < 0 for name in (
                "source_residue", "expected_target_residue", "claimed_target_residue"))
            or raw["expected_target_residue"] == raw["claimed_target_residue"]):
        reject("n2-refutation-values-invalid")
    for name in ("finite_source_digest", "package_digest", "candidate_digest",
                 "witness_digest", "refutation_digest"):
        exact_digest(raw[name], f"n2-refutation-{name}")
    logger.debug("_validate_refutation exit")


def validate_n2_refutation(raw_package, raw_candidate, claimed):
    """Validate a pressure union and freshly replay its candidate and package."""
    logger.debug("validate_n2_refutation entry")
    if type(claimed) is N2Refutation:
        _validate_refutation(claimed)
    elif type(claimed) is N2ResourceLimit:
        _validate_resource(claimed)
    elif type(claimed) is N2FormalFailure:
        _validate_failure(claimed)
    else:
        reject("n2-refutation-result-variant-invalid")
    expected = refute_pressure_candidate(raw_package, raw_candidate)
    if type(claimed) is not type(expected) or claimed != expected:
        reject("n2-refutation-result-replay-mismatch")
    logger.debug("validate_n2_refutation exit")
    return expected


def _validate_open(value: N2Open) -> None:
    """Validate an exact evidence-absence envelope before source replay."""
    logger.debug("_validate_open entry")
    raw = exact_shape(value, N2Open, "n2-open")
    if (type(raw["status"]) is not ResultStatus or raw["status"] is not ResultStatus.OPEN
            or type(raw["reason"]) is not str or raw["reason"] != OPEN_REASON):
        reject("n2-open-status-or-reason-invalid")
    for name in ("prime_digest", "doctrine_digest", "source_digest",
                 "p3t_source_digest", "open_digest"):
        exact_digest(raw[name], f"n2-open-{name}")
    logger.debug("_validate_open exit")


def validate_n2_open(raw_finite, claimed):
    """Freshly reconstruct the admissible finite source and identical OPEN value."""
    logger.debug("validate_n2_open entry")
    _validate_open(claimed)
    expected = report_missing_symbolic_evidence(raw_finite)
    if type(expected) is not N2Open or claimed != expected:
        reject("n2-open-result-replay-mismatch")
    logger.debug("validate_n2_open exit")
    return expected
