"""Normalized full nested result validation for isolated P3-N0 terminals."""

from __future__ import annotations

import logging

from ...padic.family_introduction.result_validation import validate_n1_result
from ...padic.family_introduction.types import (
    N1FamilyJudgment, N1FormalFailure, N1ResourceLimit,
)
from .common import (
    N0ValidationError, exact_hex, exact_shape, reject,
)
from .nested_validation import (
    bounded_text, exact_bounded_int, exact_tuple,
)
from .types import N0Source
from ..reduction_network.types import (
    BoundaryStatus as N2BoundaryStatus, FailedBound as N2FailedBound,
    FiniteArrowJudgment, FiniteRelation, FormalFailureKind as N2FormalFailureKind,
    N2FormalFailure, N2ResourceLimit, PrimePowerReductionJudgment, RelativeStatus,
    ResultStatus, SymbolicKind,
)
from ..reduction_network.validation import validate_prime_power_reduction_result

logger = logging.getLogger(__name__)


def _n2_arrow_shape(value, index) -> None:
    """Validate every field of one exact finite-arrow judgment."""
    logger.debug("_n2_arrow_shape entry index=%d", index)
    raw = exact_shape(value, FiniteArrowJudgment, f"n0-nested-n2-arrow-{index}")
    exact_bounded_int(raw["fine_depth"], f"n0-n2-arrow-{index}-fine", maximum=64)
    exact_bounded_int(raw["coarse_depth"], f"n0-n2-arrow-{index}-coarse", maximum=64)
    for name in ("total", "square_commutes", "preservation"):
        if type(raw[name]) is not bool:
            reject(f"n0-n2-arrow-{index}-{name}-bool-invalid")
    if type(raw["relation"]) is not FiniteRelation:
        reject(f"n0-n2-arrow-{index}-relation-invalid")
    separators = raw["separator_family_ids"]
    if separators is not None:
        separators = exact_tuple(
            separators, f"n0-n2-arrow-{index}-separators", maximum=2, length=2,
        )
        for position, item in enumerate(separators):
            bounded_text(item, f"n0-n2-arrow-{index}-separator-{position}", maximum=256)
    exact_hex(raw["map_digest"], f"n0-n2-arrow-{index}-map")
    exact_hex(raw["judgment_digest"], f"n0-n2-arrow-{index}-judgment")
    logger.debug("_n2_arrow_shape exit index=%d", index)


def validate_n2_positive_shape(value) -> None:
    """Fully validate all positive N2 fields before delegated fresh replay."""
    logger.debug("validate_n2_positive_shape entry")
    raw = exact_shape(value, PrimePowerReductionJudgment, "n0-nested-n2-positive")
    for name in (
        "finite_status", "symbolic_status", "identity", "composition", "rho_square",
        "proof_witness_independence",
    ):
        if type(raw[name]) is not RelativeStatus:
            reject(f"n0-nested-n2-{name}-status-invalid")
    if (type(raw["symbolic_kind"]) is not SymbolicKind
            or type(raw["completed_carrier"]) is not N2BoundaryStatus):
        reject("n0-nested-n2-symbolic-or-boundary-invalid")
    for name in ("pomega2_final_judgment_consumed", "p3c2_status_consumed"):
        if type(raw[name]) is not bool:
            reject(f"n0-nested-n2-{name}-bool-invalid")
    if type(raw["promotions"]) is not int or raw["promotions"] != 0:
        reject("n0-nested-n2-promotions-invalid")
    arrows = exact_tuple(raw["finite_arrows"], "n0-nested-n2-arrows", maximum=1024)
    for index, item in enumerate(arrows):
        _n2_arrow_shape(item, index)
    for name in (
        "p3t_source_digest", "p3t_replay_digest", "theorem_source_digest",
        "ledger_digest", "judgment_digest",
    ):
        exact_hex(raw[name], f"n0-nested-n2-{name}")
    theorem_ids = exact_tuple(
        raw["theorem_ids"], "n0-nested-n2-theorem-ids", maximum=7, length=7,
    )
    for index, item in enumerate(theorem_ids):
        bounded_text(item, f"n0-nested-n2-theorem-{index}", maximum=256)
    axiom_rows = exact_tuple(
        raw["axiom_rows"], "n0-nested-n2-axiom-rows", maximum=7, length=7,
    )
    for index, item in enumerate(axiom_rows):
        row = exact_tuple(item, f"n0-nested-n2-axiom-row-{index}", maximum=2, length=2)
        bounded_text(row[0], f"n0-nested-n2-axiom-name-{index}", maximum=256)
        axioms = exact_tuple(row[1], f"n0-nested-n2-axioms-{index}", maximum=16)
        for position, axiom in enumerate(axioms):
            bounded_text(axiom, f"n0-nested-n2-axiom-{index}-{position}", maximum=256)
    nonclaims = exact_tuple(raw["nonclaims"], "n0-nested-n2-nonclaims", maximum=64)
    for index, item in enumerate(nonclaims):
        bounded_text(item, f"n0-nested-n2-nonclaim-{index}", maximum=256)
    logger.debug("validate_n2_positive_shape exit")


def _normalized(label, callback):
    """Normalize foreign lower-layer failures while preserving local semantic rejection."""
    logger.debug("_normalized entry label=%s", label)
    try:
        result = callback()
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("nested validation rejected label=%s type=%s", label,
                         type(exc).__name__)
        reject(f"n0-nested-{label}-validation-rejected-{type(exc).__name__}")
    logger.debug("_normalized exit label=%s", label)
    return result


def validate_positive_children(source, n1_results, n2_results) -> None:
    """Fully validate every N1/N2 positive child against its matching raw package."""
    logger.debug("validate_positive_children entry")
    n1 = exact_tuple(n1_results, "n0-positive-n1", maximum=3, length=3)
    n2 = exact_tuple(n2_results, "n0-positive-n2", maximum=2, length=2)
    if any(type(item) is not N1FamilyJudgment for item in n1):
        reject("n0-positive-n1-variant-invalid")
    if any(type(item) is not PrimePowerReductionJudgment for item in n2):
        reject("n0-positive-n2-variant-invalid")
    for index, (package, claimed) in enumerate(zip(source.n1_packages, n1, strict=True)):
        _normalized(f"n1-positive-{index}", lambda p=package, c=claimed: validate_n1_result(p, c))
    wrappers = (source.strict_package, source.open_package)
    for index, (wrapper, claimed) in enumerate(zip(wrappers, n2, strict=True)):
        validate_n2_positive_shape(claimed)
        _normalized(
            f"n2-positive-{index}",
            lambda p=wrapper.raw_package, c=claimed: validate_prime_power_reduction_result(p, c),
        )
    logger.debug("validate_positive_children exit")


def _n2_resource_shape(value) -> str:
    """Validate all exact N2 resource fields before package selection or replay."""
    logger.debug("_n2_resource_shape entry")
    raw = exact_shape(value, N2ResourceLimit, "n0-nested-n2-resource")
    if (type(raw["status"]) is not ResultStatus
            or raw["status"] is not ResultStatus.RESOURCE_LIMIT
            or type(raw["failed_bound"]) is not N2FailedBound):
        reject("n0-nested-n2-resource-enum-invalid")
    required = exact_bounded_int(
        raw["required"], "n0-nested-n2-resource-required", maximum=2**63 - 1,
    )
    allowed = exact_bounded_int(
        raw["allowed"], "n0-nested-n2-resource-allowed", maximum=2**63 - 1,
    )
    if required <= allowed:
        reject("n0-nested-n2-resource-order-invalid")
    exact_hex(raw["package_digest"], "n0-nested-n2-resource-package")
    exact_hex(raw["refusal_digest"], "n0-nested-n2-resource-digest")
    logger.debug("_n2_resource_shape exit")
    return raw["package_digest"]


def _n2_failure_shape(value) -> str:
    """Validate all exact N2 formal-failure fields before lower replay."""
    logger.debug("_n2_failure_shape entry")
    raw = exact_shape(value, N2FormalFailure, "n0-nested-n2-formal-failure")
    if type(raw["kind"]) is not N2FormalFailureKind:
        reject("n0-nested-n2-failure-kind-invalid")
    bounded_text(raw["diagnostic"], "n0-nested-n2-failure-diagnostic",
                 maximum=256, empty=True)
    exact_hex(raw["package_digest"], "n0-nested-n2-failure-package")
    exact_hex(raw["attempt_digest"], "n0-nested-n2-failure-attempt")
    logger.debug("_n2_failure_shape exit")
    return raw["package_digest"]


def validate_native_nested(source: N0Source, nested) -> None:
    """Validate a complete native resource/formal child against its exact package."""
    logger.debug("validate_native_nested entry type=%s", type(nested).__name__)
    if type(nested) in (N1ResourceLimit, N1FormalFailure):
        cls = N1ResourceLimit if type(nested) is N1ResourceLimit else N1FormalFailure
        raw = exact_shape(nested, cls, "n0-nested-n1-terminal")
        package_digest = exact_hex(raw["package_digest"], "n0-nested-n1-package")
        matches = tuple(item for item in source.n1_packages
                        if item.package_digest == package_digest)
        if len(matches) != 1:
            reject("n0-nested-n1-package-match-invalid")
        _normalized("n1-terminal", lambda: validate_n1_result(matches[0], nested))
    elif type(nested) in (N2ResourceLimit, N2FormalFailure):
        package_digest = (_n2_resource_shape(nested) if type(nested) is N2ResourceLimit
                          else _n2_failure_shape(nested))
        wrappers = (source.strict_package, source.open_package)
        matches = tuple(item.raw_package for item in wrappers
                        if item.raw_package.package_digest == package_digest)
        if len(matches) != 1:
            reject("n0-nested-n2-package-match-invalid")
        _normalized(
            "n2-terminal",
            lambda: validate_prime_power_reduction_result(matches[0], nested),
        )
    else:
        reject("n0-nested-native-terminal-variant-invalid")
    logger.debug("validate_native_nested exit")
