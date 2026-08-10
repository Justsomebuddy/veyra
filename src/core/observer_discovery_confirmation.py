"""Fixed-winner replication on one caller-declared third categorical test set."""

from __future__ import annotations

from dataclasses import replace
import logging
from math import ceil, isfinite
import random

from .observer_discovery import (
    FOUND,
    _baseline_comparisons,
    _evaluate_catalog,
    _group_indices,
    _mutual_information,
    _registry,
    _seed,
    _validate_catalog,
    _validate_config,
    _validate_rows,
    _validate_split,
    discover_observer,
)
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
from .observer_discovery_confirmation_validation import (
    bind_confirmation_report,
    confirmation_protocol_digest,
)
from .observer_discovery_evidence import discovery_input_digests, discovery_rows_digest
from .observer_discovery_protocol import (
    enumerate_observer_terms_bounded,
    snapshot_discovery_inputs,
    snapshot_discovery_rows,
)
from .observer_discovery_types import (
    DiscoveryConfig,
    DiscoveryDigests,
    DiscoveryObstruction,
    DiscoveryRow,
    DiscoverySplit,
    ObserverDiscoveryReport,
)
from .observer_discovery_validation import validate_discovery_report
from .observer_synthesis import canonical_term
from .observer_synthesis_types import Canonical, NamedBaseline, ObserverGrammar, ObserverTerm

logger = logging.getLogger(__name__)
BLOCKED = CONFIRMATION_BLOCKED
BOUNDARY = CONFIRMATION_BOUNDARY


class _ConfirmationBlocked(RuntimeError):
    def __init__(self, reason: str, detail: str) -> None:
        logger.error("_ConfirmationBlocked entry reason=%s", reason)
        self.reason, self.detail = reason, detail
        super().__init__(f"{reason}:{detail}")
        logger.debug("_ConfirmationBlocked exit")


def confirm_observer_discovery(
    report: ObserverDiscoveryReport,
    grammar: ObserverGrammar,
    original_split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    discovery_config: DiscoveryConfig,
    test_rows: tuple[DiscoveryRow, ...],
    config: DiscoveryConfirmationConfig = DiscoveryConfirmationConfig(),
) -> DiscoveryConfirmationReport:
    """Confirm one exact valid FOUND winner without searching the test set."""
    logger.debug("confirm_observer_discovery entry")
    parent_result = _safe_parent_result(report)
    trusted_parent: ObserverDiscoveryReport | None = None
    try:
        config = _snapshot_confirmation_config(config)
        if not validate_discovery_report(report) or report.status != FOUND or report.winner is None:
            raise _ConfirmationBlocked("invalid-parent", "exact-valid-found-report-required")
        grammar, original_split, baselines, discovery_config = snapshot_discovery_inputs(
            grammar,
            original_split,
            baselines,
            discovery_config,
        )
        test_rows = snapshot_discovery_rows(test_rows)
        _validate_config(discovery_config)
        registry = _registry(grammar)
        _validate_split(original_split)
        _validate_rows("test", test_rows)
        _validate_test(config, original_split, test_rows, 1 + len(baselines))
        replayed = discover_observer(grammar, original_split, baselines, discovery_config)
        if replayed != report:
            raise _ConfirmationBlocked("parent-replay-mismatch", "exact-report-equality")
        if replayed.status != FOUND or replayed.winner is None:
            raise _ConfirmationBlocked("invalid-parent", "replayed-found-winner-required")
        trusted_parent = replayed
        trusted_winner = replayed.winner
        parent_result = replayed.digests.result
        catalog = enumerate_observer_terms_bounded(grammar, discovery_config.max_catalog_size)
        _validate_catalog(catalog, grammar, baselines, discovery_config, registry)
        expected = discovery_input_digests(grammar, original_split, baselines, discovery_config, catalog)
        fields = ("protocol", "protocol_material", "policy", "grammar", "train_data", "holdout_data", "catalog")
        if any(getattr(expected, name) != getattr(trusted_parent.digests, name) for name in fields):
            raise _ConfirmationBlocked("parent-input-mismatch", "recomputed-evidence-root")
        catalog_shapes = {canonical_term(term) for term in catalog}
        if canonical_term(trusted_winner.term) not in catalog_shapes:
            raise _ConfirmationBlocked("invalid-parent", "winner-outside-catalog")
        terms = (trusted_winner.term,) + tuple(item.term for item in baselines)
        evaluation_config = replace(
            discovery_config,
            determinism_checks=config.determinism_checks,
        )
        outputs = _evaluate_catalog(terms, test_rows, registry, evaluation_config)
        _assert_confirmation_protocol_unchanged(
            expected,
            grammar,
            original_split,
            baselines,
            discovery_config,
            catalog,
        )
        targets = tuple(row.target for row in test_rows)
        winner_information = _mutual_information(outputs[0], targets)
        baseline_rows = _baseline_comparisons(baselines, tuple(item.term for item in baselines), outputs[1:], targets)
        gap = winner_information - max(row.information_bits for row in baseline_rows)
        protocol = confirmation_protocol_digest(
            trusted_parent.digests.result,
            trusted_winner.fingerprint,
            config,
        )
        calibration = _calibrate_association(
            outputs,
            test_rows,
            winner_information,
            config,
            protocol,
        )
        failures = []
        if winner_information <= config.minimum_test_information_bits:
            failures.append(DiscoveryObstruction("test-information", winner_information.hex()))
        if gap <= config.minimum_test_gap_bits:
            failures.append(DiscoveryObstruction("test-gap", gap.hex()))
        if calibration.add_one_p_value > config.significance_alpha:
            failures.append(DiscoveryObstruction("not-significant", calibration.add_one_p_value.hex()))
        status = NOT_REPLICATED if failures else REPLICATED
        result = DiscoveryConfirmationReport(
            status,
            config,
            trusted_winner.fingerprint,
            winner_information,
            baseline_rows,
            gap,
            calibration,
            DiscoveryConfirmationDigests(
                trusted_parent.digests.result,
                protocol,
                discovery_rows_digest(test_rows, "veyra.observer-confirmation.test-data.v1"),
                "",
            ),
            tuple(failures),
            BOUNDARY,
        )
        bound = bind_confirmation_report(result)
        logger.info("confirm_observer_discovery state=%s", status)
        logger.debug("confirm_observer_discovery exit status=%s", status)
        return bound
    except Exception as exc:
        reason = exc.reason if isinstance(exc, _ConfirmationBlocked) else "confirmation-blocked"
        detail = exc.detail if isinstance(exc, _ConfirmationBlocked) else type(exc).__name__
        logger.error("confirm_observer_discovery state=BLOCKED reason=%s", reason)
        result = DiscoveryConfirmationReport(
            BLOCKED,
            None,
            None,
            None,
            (),
            None,
            None,
            DiscoveryConfirmationDigests(
                parent_result,
                "",
                "",
                "",
            ),
            (DiscoveryObstruction(reason, detail),),
            BOUNDARY,
        )
        bound = bind_confirmation_report(result)
        logger.debug("confirm_observer_discovery exit status=BLOCKED")
        return bound


def _assert_confirmation_protocol_unchanged(
    expected: DiscoveryDigests,
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
    catalog: tuple[ObserverTerm, ...],
) -> None:
    """Reject evaluator-time drift in the exact discovery inputs already bound."""
    logger.debug("_assert_confirmation_protocol_unchanged entry")
    actual = discovery_input_digests(grammar, split, baselines, config, catalog)
    if actual != expected:
        logger.error("_assert_confirmation_protocol_unchanged mutation detected")
        raise _ConfirmationBlocked(
            "protocol-mutation",
            "data-catalog-config-or-evaluator-changed",
        )
    logger.debug("_assert_confirmation_protocol_unchanged exit")


def _snapshot_confirmation_config(config: object) -> DiscoveryConfirmationConfig:
    """Require and detach the exact immutable confirmation configuration."""
    logger.debug("_snapshot_confirmation_config entry type=%s", type(config).__name__)
    if type(config) is not DiscoveryConfirmationConfig:
        logger.error("_snapshot_confirmation_config rejected config type")
        raise _ConfirmationBlocked("invalid-config", "exact-config-required")
    result = DiscoveryConfirmationConfig(
        config.minimum_test_information_bits,
        config.minimum_test_gap_bits,
        config.significance_alpha,
        config.permutation_count,
        config.determinism_checks,
        config.max_test_rows,
        config.max_work_items,
        config.random_seed,
    )
    _validate_confirmation_config(result)
    logger.debug("_snapshot_confirmation_config exit")
    return result


def _validate_confirmation_config(config: DiscoveryConfirmationConfig) -> None:
    logger.debug("_validate_confirmation_config entry")
    floats = (config.minimum_test_information_bits, config.minimum_test_gap_bits, config.significance_alpha)
    if any(type(value) is not float or not isfinite(value) for value in floats):
        raise _ConfirmationBlocked("invalid-config", "finite-floats")
    if (
        config.minimum_test_information_bits < 0.0
        or config.minimum_test_gap_bits < 0.0
        or not 0.0 < config.significance_alpha <= 0.05
    ):
        raise _ConfirmationBlocked("invalid-config", "hard-floor")
    ints = (config.permutation_count, config.determinism_checks, config.max_test_rows, config.max_work_items)
    if any(type(value) is not int or value < 1 for value in ints):
        raise _ConfirmationBlocked("invalid-config", "positive-counts")
    if (
        config.permutation_count < 19
        or config.permutation_count < ceil(1 / config.significance_alpha) - 1
        or config.permutation_count > 4095
    ):
        raise _ConfirmationBlocked("insufficient-calibration", "permutation-resolution")
    if config.determinism_checks > 8 or config.max_test_rows > 8192 or config.max_work_items > 5_000_000:
        raise _ConfirmationBlocked("invalid-config", "hard-cap")
    if (
        type(config.random_seed) is not str
        or not config.random_seed
        or len(config.random_seed) > 512
        or len(config.random_seed.encode()) > 512
    ):
        raise _ConfirmationBlocked("invalid-config", "seed")
    logger.debug("_validate_confirmation_config exit")


def _safe_parent_result(report: object) -> str:
    """Return a bounded parent digest without trusting a malformed report graph."""
    logger.debug("_safe_parent_result entry type=%s", type(report).__name__)
    try:
        value = report.digests.result if type(report) is ObserverDiscoveryReport else ""
    except AttributeError:
        logger.error("_safe_parent_result malformed parent digests")
        return ""
    result = value if _is_hex_digest(value) else ""
    logger.debug("_safe_parent_result exit present=%s", bool(result))
    return result


def _is_hex_digest(value: object) -> bool:
    """Recognize one lowercase SHA-256 identity without echoing its contents."""
    logger.debug("_is_hex_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
    logger.debug("_is_hex_digest exit valid=%s", result)
    return result


def _validate_test(
    config: DiscoveryConfirmationConfig,
    split: DiscoverySplit,
    rows: tuple[DiscoveryRow, ...],
    term_count: int,
) -> None:
    logger.debug("_validate_test entry rows=%d", len(rows))
    if len(rows) > config.max_test_rows:
        raise _ConfirmationBlocked("resource-limit", "test-rows")
    checks = max(2, config.determinism_checks)
    work = term_count * len(rows) * (checks + config.permutation_count)
    if work > config.max_work_items:
        raise _ConfirmationBlocked("resource-limit", "confirmation-work")
    for name in ("row_id", "source_id", "content_id", "group_id"):
        prior = {getattr(row, name) for row in split.train + split.holdout}
        if prior & {getattr(row, name) for row in rows}:
            raise _ConfirmationBlocked("split-leakage", f"three-way-{name}-overlap")
    logger.debug("_validate_test exit")


def _calibrate_association(
    outputs: tuple[tuple[Canonical, ...], ...],
    rows: tuple[DiscoveryRow, ...],
    observed_winner_information: float,
    config: DiscoveryConfirmationConfig,
    protocol: str,
) -> FixedFamilyCalibration:
    """Calibrate winner association against the fixed declared family maximum."""
    logger.debug("_calibrate_association entry permutations=%d", config.permutation_count)
    grouped = _group_indices(rows)
    group_ids = tuple(sorted(grouped))
    targets = {group: rows[indices[0]].target for group, indices in grouped.items()}
    labels = [targets[group] for group in group_ids]
    rng = random.Random(_seed(protocol, config.random_seed, "fixed-family-association-permutation"))
    nulls = []
    for _ in range(config.permutation_count):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        mapping = dict(zip(group_ids, shuffled, strict=True))
        permuted = tuple(mapping[row.group_id] for row in rows)
        nulls.append(max(_mutual_information(values, permuted) for values in outputs))
    exceedances = sum(value >= observed_winner_information for value in nulls)
    result = FixedFamilyCalibration(
        config.permutation_count,
        exceedances,
        observed_winner_information,
        (exceedances + 1) / (config.permutation_count + 1),
        tuple(nulls),
    )
    logger.debug("_calibrate_association exit p=%.6f", result.add_one_p_value)
    return result
