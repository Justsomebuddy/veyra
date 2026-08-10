"""Independent local validation for fixed-winner confirmation receipts."""

from __future__ import annotations

from dataclasses import replace
import logging
from math import ceil, isfinite

from .observer_discovery_confirmation_types import (
    CONFIRMATION_BLOCKED,
    CONFIRMATION_BOUNDARY,
    NOT_REPLICATED,
    REPLICATED,
    DiscoveryConfirmationConfig,
    DiscoveryConfirmationDigests,
    DiscoveryConfirmationReport,
    FixedFamilyCalibration,
)
from .observer_discovery_types import (
    BaselineComparison,
    DiscoveryObstruction,
    ObserverDiscoveryReport,
)
from .observer_discovery_validation import validate_discovery_report
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)
_STATUSES = {REPLICATED, NOT_REPLICATED, CONFIRMATION_BLOCKED}
_MAX_TEXT_BYTES = 4096


def bind_confirmation_report(report: DiscoveryConfirmationReport) -> DiscoveryConfirmationReport:
    """Bind every published confirmation field under a result domain."""
    logger.debug("bind_confirmation_report entry status=%s", getattr(report, "status", "<invalid>"))
    if type(report) is not DiscoveryConfirmationReport:
        logger.error("bind_confirmation_report rejected report type")
        raise TypeError("invalid-confirmation-report")
    digest = digest_data(_report_data(report), "veyra.observer-confirmation.result.v1")
    result = replace(report, digests=replace(report.digests, result=digest))
    logger.debug("bind_confirmation_report exit digest=%s", digest[:12])
    return result


def confirmation_protocol_digest(
    parent_result: str,
    winner_fingerprint: str,
    config: DiscoveryConfirmationConfig,
) -> str:
    """Bind the parent, fixed winner, and complete confirmation decision policy."""
    logger.debug("confirmation_protocol_digest entry")
    result = digest_data(
        {
            "parent": parent_result,
            "winner": winner_fingerprint,
            "minimum_test_information_bits": config.minimum_test_information_bits.hex(),
            "minimum_test_gap_bits": config.minimum_test_gap_bits.hex(),
            "alpha": config.significance_alpha.hex(),
            "permutations": config.permutation_count,
            "checks": config.determinism_checks,
            "max_rows": config.max_test_rows,
            "max_work": config.max_work_items,
            "seed": config.random_seed,
        },
        "veyra.observer-confirmation.protocol.v1",
    )
    logger.debug("confirmation_protocol_digest exit digest=%s", result[:12])
    return result


def validate_confirmation_report(
    report: object,
    *,
    expected_parent_result: str | None = None,
    expected_test_data: str | None = None,
    parent_report: ObserverDiscoveryReport | None = None,
) -> bool:
    """Validate local evidence and optionally bind it to a valid parent report."""
    logger.debug("validate_confirmation_report entry type=%s", type(report).__name__)
    try:
        if type(report) is not DiscoveryConfirmationReport or report.status not in _STATUSES:
            logger.error("validate_confirmation_report invalid shape")
            return False
        if type(report.digests) is not DiscoveryConfirmationDigests:
            logger.error("validate_confirmation_report invalid digests")
            return False
        if (
            type(report.baselines) is not tuple
            or type(report.obstructions) is not tuple
            or len(report.baselines) > 4096
            or len(report.obstructions) > 64
        ):
            logger.error("validate_confirmation_report nested resource limit")
            return False
        if (
            any(type(row) is not BaselineComparison for row in report.baselines)
            or any(type(row) is not DiscoveryObstruction for row in report.obstructions)
            or report.boundary != CONFIRMATION_BOUNDARY
            or any(
                not _bounded_text(row.name)
                or not _bounded_text(row.observer_class)
                or not _hex_digest(row.fingerprint)
                or not _finite(row.information_bits)
                or row.information_bits < 0.0
                or not _bounded_text(row.boundary)
                for row in report.baselines
            )
            or any(not _bounded_text(row.reason) or not _bounded_text(row.detail) for row in report.obstructions)
        ):
            logger.error("validate_confirmation_report invalid nested records")
            return False
        if len(report.digests.__dict__) != 4:
            logger.error("validate_confirmation_report unexpected digest fields")
            return False
        digest_values = (
            report.digests.parent_result,
            report.digests.protocol,
            report.digests.test_data,
            report.digests.result,
        )
        if any(
            type(value) is not str or (value and (len(value) != 64 or any(c not in "0123456789abcdef" for c in value)))
            for value in digest_values
        ):
            logger.error("validate_confirmation_report invalid digest")
            return False
        if report.status != "BLOCKED" and any(not value for value in digest_values):
            logger.error("validate_confirmation_report missing evidence digest")
            return False
        if expected_parent_result is not None and report.digests.parent_result != expected_parent_result:
            logger.error("validate_confirmation_report parent mismatch")
            return False
        if expected_test_data is not None and report.digests.test_data != expected_test_data:
            logger.error("validate_confirmation_report test mismatch")
            return False
        if parent_report is not None and (
            not validate_discovery_report(parent_report)
            or parent_report.status != "FOUND"
            or parent_report.winner is None
            or report.digests.parent_result != parent_report.digests.result
            or (report.status != CONFIRMATION_BLOCKED and report.winner_fingerprint != parent_report.winner.fingerprint)
            or (
                report.status != CONFIRMATION_BLOCKED
                and tuple((row.name, row.observer_class, row.fingerprint, row.boundary) for row in report.baselines)
                != tuple(
                    (row.name, row.observer_class, row.fingerprint, row.boundary) for row in parent_report.baselines
                )
            )
        ):
            logger.error("validate_confirmation_report parent report mismatch")
            return False
        if report.status == CONFIRMATION_BLOCKED:
            valid = (
                report.config is None
                and report.winner_fingerprint is None
                and report.test_information_bits is None
                and not report.baselines
                and report.observer_gap_bits is None
                and report.calibration is None
                and report.digests.protocol == ""
                and report.digests.test_data == ""
                and bool(report.obstructions)
            )
        else:
            calibration = report.calibration
            config = report.config
            valid = (
                type(config) is DiscoveryConfirmationConfig
                and _valid_config(config)
                and _hex_digest(report.winner_fingerprint)
                and _finite(report.test_information_bits)
                and report.test_information_bits >= 0.0
                and _finite(report.observer_gap_bits)
                and type(calibration) is FixedFamilyCalibration
                and calibration.permutations == config.permutation_count
                and 0 <= calibration.exceedances <= calibration.permutations
                and type(calibration.null_maxima_bits) is tuple
                and len(calibration.null_maxima_bits) == calibration.permutations
                and calibration.exceedances
                == sum(value >= calibration.observed_winner_information_bits for value in calibration.null_maxima_bits)
                and calibration.add_one_p_value == (calibration.exceedances + 1) / (calibration.permutations + 1)
                and calibration.observed_winner_information_bits == report.test_information_bits
                and all(_finite(value) and value >= 0.0 for value in calibration.null_maxima_bits)
                and bool(report.baselines)
                and len({row.name for row in report.baselines}) == len(report.baselines)
                and report.observer_gap_bits
                == report.test_information_bits - max(row.information_bits for row in report.baselines)
                and report.digests.protocol
                == confirmation_protocol_digest(
                    report.digests.parent_result,
                    report.winner_fingerprint,
                    config,
                )
            )
            if report.status == REPLICATED:
                valid = (
                    valid
                    and not report.obstructions
                    and report.test_information_bits > config.minimum_test_information_bits
                    and report.observer_gap_bits > config.minimum_test_gap_bits
                    and calibration.add_one_p_value <= config.significance_alpha
                )
            else:
                expected = []
                if report.test_information_bits <= config.minimum_test_information_bits:
                    expected.append(DiscoveryObstruction("test-information", report.test_information_bits.hex()))
                if report.observer_gap_bits <= config.minimum_test_gap_bits:
                    expected.append(DiscoveryObstruction("test-gap", report.observer_gap_bits.hex()))
                if calibration.add_one_p_value > config.significance_alpha:
                    expected.append(DiscoveryObstruction("not-significant", calibration.add_one_p_value.hex()))
                valid = valid and bool(expected) and report.obstructions == tuple(expected)
        blank = replace(report, digests=replace(report.digests, result=""))
        valid = valid and bind_confirmation_report(blank) == report
    except (AttributeError, TypeError, ValueError, OverflowError):
        logger.error("validate_confirmation_report malformed")
        return False
    logger.debug("validate_confirmation_report exit valid=%s", valid)
    return valid


def _finite(value: object) -> bool:
    logger.debug("_finite entry type=%s", type(value).__name__)
    result = type(value) is float and isfinite(value)
    logger.debug("_finite exit valid=%s", result)
    return result


def _hex_digest(value: object) -> bool:
    logger.debug("_hex_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
    logger.debug("_hex_digest exit valid=%s", result)
    return result


def _bounded_text(value: object) -> bool:
    logger.debug("_bounded_text entry type=%s", type(value).__name__)
    result = (
        type(value) is str
        and bool(value)
        and len(value) <= _MAX_TEXT_BYTES
        and len(value.encode("utf-8")) <= _MAX_TEXT_BYTES
    )
    logger.debug("_bounded_text exit valid=%s", result)
    return result


def _valid_config(config: DiscoveryConfirmationConfig) -> bool:
    logger.debug("_valid_config entry")
    result = (
        _finite(config.minimum_test_information_bits)
        and config.minimum_test_information_bits >= 0.0
        and _finite(config.minimum_test_gap_bits)
        and config.minimum_test_gap_bits >= 0.0
        and _finite(config.significance_alpha)
        and 0.0 < config.significance_alpha <= 0.05
        and type(config.permutation_count) is int
        and 19 <= config.permutation_count <= 4095
        and config.permutation_count >= ceil(1 / config.significance_alpha) - 1
        and type(config.determinism_checks) is int
        and 1 <= config.determinism_checks <= 8
        and type(config.max_test_rows) is int
        and 1 <= config.max_test_rows <= 8192
        and type(config.max_work_items) is int
        and 1 <= config.max_work_items <= 5_000_000
        and type(config.random_seed) is str
        and bool(config.random_seed)
        and len(config.random_seed) <= 512
        and len(config.random_seed.encode()) <= 512
    )
    logger.debug("_valid_config exit valid=%s", result)
    return result


def _report_data(report: DiscoveryConfirmationReport) -> dict[str, object]:
    logger.debug("_report_data entry status=%s", report.status)
    result = {
        "status": report.status,
        "config": None
        if report.config is None
        else {
            "minimum_test_information_bits": report.config.minimum_test_information_bits.hex(),
            "minimum_test_gap_bits": report.config.minimum_test_gap_bits.hex(),
            "significance_alpha": report.config.significance_alpha.hex(),
            "permutation_count": report.config.permutation_count,
            "determinism_checks": report.config.determinism_checks,
            "max_test_rows": report.config.max_test_rows,
            "max_work_items": report.config.max_work_items,
            "random_seed": report.config.random_seed,
        },
        "winner_fingerprint": report.winner_fingerprint,
        "test_information_bits": None if report.test_information_bits is None else report.test_information_bits.hex(),
        "baselines": [
            {
                "name": row.name,
                "class": row.observer_class,
                "fingerprint": row.fingerprint,
                "information_bits": row.information_bits.hex(),
                "boundary": row.boundary,
            }
            for row in report.baselines
        ],
        "observer_gap_bits": None if report.observer_gap_bits is None else report.observer_gap_bits.hex(),
        "calibration": None
        if report.calibration is None
        else {
            "permutations": report.calibration.permutations,
            "exceedances": report.calibration.exceedances,
            "observed_winner_information_bits": report.calibration.observed_winner_information_bits.hex(),
            "add_one_p_value": report.calibration.add_one_p_value.hex(),
            "null_maxima_bits": [value.hex() for value in report.calibration.null_maxima_bits],
        },
        "parent_result": report.digests.parent_result,
        "protocol": report.digests.protocol,
        "test_data": report.digests.test_data,
        "obstructions": [{"reason": row.reason, "detail": row.detail} for row in report.obstructions],
        "boundary": report.boundary,
    }
    logger.debug("_report_data exit")
    return result
