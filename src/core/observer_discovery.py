"""Certified finite-catalog discovery for binary and categorical data.

The module searches only the supplied typed R5 grammar.  It establishes
association under a locked statistical protocol, never causality, semantic
explanation, universal hidden-variable recovery, or an impossibility result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
import logging
from math import ceil, isfinite, log2
import random

from .observer_discovery_types import (
    BaselineComparison,
    BootstrapStability,
    DiscoveryConfig,
    DiscoveryDigests,
    DiscoveryGrammarReceipt,
    DiscoveryObstruction,
    DiscoveryPolicyReceipt,
    DiscoveryRow,
    DiscoveryScore,
    DiscoverySplit,
    ObserverDiscoveryReport,
    PermutationCalibration,
    HARD_MAX_ALPHA,
    HARD_MIN_BOOTSTRAPS,
    HARD_MIN_PERMUTATIONS,
    HARD_MIN_STABILITY,
)
from .observer_discovery_protocol import (
    DiscoveryProtocolError,
    enumerate_observer_terms_bounded,
    snapshot_discovery_inputs,
)
from .observer_discovery_evidence import discovery_input_digests
from .observer_discovery_validation import (
    bind_discovery_report,
    bind_discovery_train_evaluation,
    discovery_grammar_receipt,
    discovery_policy_receipt,
)
from .observer_synthesis import (
    canonical_term,
    evaluate_observer,
    observer_fingerprint,
    observer_term_cost,
)
from .observer_synthesis_protocol import callable_identity
from .observer_synthesis_types import (
    Canonical,
    NamedBaseline,
    ObserverGrammar,
    ObserverPrimitive,
    ObserverTerm,
)
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

FOUND = "FOUND"
NOT_FOUND_WITHIN_BUDGET = "NOT_FOUND_WITHIN_BUDGET"
BLOCKED = "BLOCKED"
BOUNDARY = (
    "bounded finite declared grammar and locked train/holdout only; empirical "
    "association/compression is not causality or semantic explanation; group "
    "permutation assumes exchangeable groups; finite failure is not impossibility; "
    "holdout isolation is logical in-process isolation, not process-level isolation; "
    "one homogeneous exchangeability stratum is assumed; feature schema, target exclusion, "
    "evaluator purity, and source/content lineage are trusted caller declarations"
)

_HARD_MAX_PERMUTATIONS = 4095
_HARD_MAX_BOOTSTRAPS = 1024
_HARD_MAX_DETERMINISM_CHECKS = 8
_HARD_MAX_ROWS_PER_SPLIT = 8192
_HARD_MAX_FEATURE_NODES = 4096
_HARD_MAX_FEATURE_DEPTH = 16
_HARD_MAX_PRIMITIVES = 12
_HARD_MAX_GRAMMAR_DEPTH = 2
_HARD_MAX_GRAMMAR_COST = 8
_HARD_MAX_CATALOG_SIZE = 4096
_HARD_MAX_WORK_ITEMS = 10_000_000
_HARD_MAX_RETAINED_OUTPUT_UNITS = 1_000_000
_HARD_MAX_STRING_BYTES = 4096
_HARD_MAX_ID_BYTES = 512


class _DiscoveryBlocked(RuntimeError):
    """Internal fail-closed signal carrying a stable obstruction pair."""

    def __init__(self, reason: str, detail: str) -> None:
        logger.error("_DiscoveryBlocked entry reason=%s", reason)
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}:{detail}")
        logger.debug("_DiscoveryBlocked exit reason=%s", reason)


def discover_observer(
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...] = (),
    config: DiscoveryConfig = DiscoveryConfig(),
) -> ObserverDiscoveryReport:
    """Exhaust the grammar, lock a train winner, and validate it on holdout."""
    logger.debug("discover_observer entry grammar=%s", getattr(grammar, "grammar_id", "<invalid>"))
    empty = _empty_digests()
    current_digests = empty
    current_catalog_size = 0
    try:
        grammar, split, baselines, config = snapshot_discovery_inputs(
            grammar,
            split,
            baselines,
            config,
        )
        _validate_config(config)
        registry = _registry(grammar)
        _validate_split(split)
        policy = discovery_policy_receipt(config)
        grammar_receipt = discovery_grammar_receipt(grammar)
        catalog = enumerate_observer_terms_bounded(grammar, config.max_catalog_size)
        _validate_catalog(catalog, grammar, baselines, config, registry)
        _validate_work_budget(len(catalog), split, config)
        current_catalog_size = len(catalog)
        digests = _digests(grammar, split, baselines, config, catalog)
        current_digests = digests
        train_outputs = _evaluate_catalog(catalog, split.train, registry, config)
        train_targets = tuple(row.target for row in split.train)
        scores = _score_catalog(catalog, train_outputs, train_targets, grammar, registry, config)
        winner = scores[0]
        digests = bind_discovery_train_evaluation(digests, winner.objective)
        current_digests = digests
        if winner.objective <= config.minimum_train_objective:
            _assert_protocol_unchanged(digests, grammar, split, baselines, config, catalog)
            logger.info("discover_observer state=NOT_FOUND_WITHIN_BUDGET reason=train-objective")
            return _terminal(
                NOT_FOUND_WITHIN_BUDGET,
                digests,
                len(catalog),
                (DiscoveryObstruction("train-threshold", f"objective={winner.objective.hex()}"),),
                policy,
                grammar_receipt,
                winner.objective,
            )

        stability = _bootstrap_stability(
            winner,
            catalog,
            train_outputs,
            split.train,
            grammar,
            registry,
            config,
            digests.protocol,
        )
        holdout_outputs = _evaluate_catalog(catalog, split.holdout, registry, config)
        holdout_targets = tuple(row.target for row in split.holdout)
        winner_index = next(
            index for index, term in enumerate(catalog) if observer_fingerprint(term) == winner.fingerprint
        )
        holdout_information = _mutual_information(holdout_outputs[winner_index], holdout_targets)
        baseline_rows = _baseline_comparisons(
            baselines,
            catalog,
            holdout_outputs,
            holdout_targets,
        )
        best_baseline = max((row.information_bits for row in baseline_rows), default=0.0)
        observer_gap = holdout_information - best_baseline
        calibration = _permutation_calibration(
            catalog,
            holdout_outputs,
            split.holdout,
            holdout_information,
            config,
            digests.protocol,
        )
        failures = _discovery_failures(
            holdout_information,
            observer_gap,
            calibration,
            stability,
            config,
        )
        _assert_protocol_unchanged(digests, grammar, split, baselines, config, catalog)
        if failures:
            logger.info("discover_observer state=NOT_FOUND_WITHIN_BUDGET failures=%d", len(failures))
            report = ObserverDiscoveryReport(
                status=NOT_FOUND_WITHIN_BUDGET,
                policy=policy,
                grammar=grammar_receipt,
                winner=None,
                train_best_objective=winner.objective,
                holdout_information_bits=holdout_information,
                baselines=baseline_rows,
                observer_gap_bits=observer_gap,
                calibration=calibration,
                stability=stability,
                catalog_size=len(catalog),
                digests=digests,
                obstructions=failures,
                boundary=BOUNDARY,
            )
            result = bind_discovery_report(report)
            logger.debug("discover_observer exit status=%s", result.status)
            return result

        report = ObserverDiscoveryReport(
            status=FOUND,
            policy=policy,
            grammar=grammar_receipt,
            winner=winner,
            train_best_objective=winner.objective,
            holdout_information_bits=holdout_information,
            baselines=baseline_rows,
            observer_gap_bits=observer_gap,
            calibration=calibration,
            stability=stability,
            catalog_size=len(catalog),
            digests=digests,
            obstructions=(),
            boundary=BOUNDARY,
        )
        result = bind_discovery_report(report)
        logger.info("discover_observer state=FOUND fingerprint=%s", winner.fingerprint[:12])
        logger.debug("discover_observer exit status=%s", result.status)
        return result
    except _DiscoveryBlocked as exc:
        logger.error("discover_observer state=BLOCKED reason=%s", exc.reason)
        result = _terminal(
            BLOCKED,
            current_digests,
            current_catalog_size,
            (DiscoveryObstruction(exc.reason, exc.detail),),
        )
        logger.debug("discover_observer exit status=%s", result.status)
        return result
    except DiscoveryProtocolError as exc:
        logger.error("discover_observer state=BLOCKED reason=%s", exc.reason)
        result = _terminal(
            BLOCKED,
            current_digests,
            current_catalog_size,
            (DiscoveryObstruction(exc.reason, exc.detail),),
        )
        logger.debug("discover_observer exit status=%s", result.status)
        return result
    except Exception as exc:  # Extension-point failures must never leak a partial result.
        logger.exception("discover_observer unexpected block type=%s", type(exc).__name__)
        result = _terminal(
            BLOCKED,
            current_digests,
            current_catalog_size,
            (DiscoveryObstruction("internal-error", type(exc).__name__),),
        )
        logger.debug("discover_observer exit status=%s", result.status)
        return result


def _validate_config(config: DiscoveryConfig) -> None:
    logger.debug("_validate_config entry")
    numeric = (
        config.complexity_cost_per_unit,
        config.minimum_train_objective,
        config.minimum_holdout_information_bits,
        config.significance_alpha,
        config.minimum_stability,
    )
    if any(type(value) is not float or not isfinite(value) for value in numeric):
        logger.error("_validate_config invalid numeric")
        raise _DiscoveryBlocked("invalid-config", "non-finite-or-non-float")
    if config.complexity_cost_per_unit < 0.0 or config.minimum_holdout_information_bits < 0.0:
        logger.error("_validate_config invalid nonnegative value")
        raise _DiscoveryBlocked("invalid-config", "nonnegative-cost-and-information-required")
    if not 0.0 < config.significance_alpha < 1.0 or not 0.0 <= config.minimum_stability <= 1.0:
        logger.error("_validate_config invalid probability")
        raise _DiscoveryBlocked("invalid-config", "probability-range")
    counts = (
        config.permutation_count,
        config.bootstrap_replicates,
        config.determinism_checks,
        config.max_catalog_size,
    )
    if any(type(value) is not int or value < 1 for value in counts):
        logger.error("_validate_config invalid count")
        raise _DiscoveryBlocked("invalid-config", "positive-integer-counts-required")
    if (
        config.significance_alpha > HARD_MAX_ALPHA
        or config.minimum_stability < HARD_MIN_STABILITY
        or config.permutation_count > _HARD_MAX_PERMUTATIONS
        or config.bootstrap_replicates > _HARD_MAX_BOOTSTRAPS
        or config.determinism_checks > _HARD_MAX_DETERMINISM_CHECKS
        or config.max_catalog_size > _HARD_MAX_CATALOG_SIZE
    ):
        logger.error("_validate_config hard statistical or resource floor failed")
        raise _DiscoveryBlocked("invalid-config", "hard-statistical-or-resource-bound")
    if config.permutation_count < HARD_MIN_PERMUTATIONS or config.bootstrap_replicates < HARD_MIN_BOOTSTRAPS:
        logger.error("_validate_config insufficient calibration count")
        raise _DiscoveryBlocked("insufficient-calibration", "hard-replicate-floor")
    required_resolution = ceil(1.0 / config.significance_alpha) - 1
    if config.permutation_count < required_resolution:
        logger.error("_validate_config insufficient p-value resolution")
        raise _DiscoveryBlocked("insufficient-calibration", "p-value-resolution")
    if not _bounded_text(config.random_seed):
        logger.error("_validate_config invalid seed")
        raise _DiscoveryBlocked("invalid-config", "random-seed")
    logger.debug("_validate_config exit")


def _validate_split(split: DiscoverySplit) -> None:
    logger.debug("_validate_split entry")
    if type(split) is not DiscoverySplit or not split.train or not split.holdout:
        logger.error("_validate_split empty or invalid")
        raise _DiscoveryBlocked("invalid-data", "nonempty-immutable-split-required")
    for name, rows in (("train", split.train), ("holdout", split.holdout)):
        if type(rows) is not tuple or any(type(row) is not DiscoveryRow for row in rows):
            logger.error("_validate_split invalid rows split=%s", name)
            raise _DiscoveryBlocked("invalid-data", f"{name}-rows-not-canonical-tuple")
        _validate_rows(name, rows)
    fields = (
        ("row", {row.row_id for row in split.train}, {row.row_id for row in split.holdout}),
        ("source", {row.source_id for row in split.train}, {row.source_id for row in split.holdout}),
        ("group", {row.group_id for row in split.train}, {row.group_id for row in split.holdout}),
        (
            "content",
            {row.content_id for row in split.train},
            {row.content_id for row in split.holdout},
        ),
    )
    for name, left, right in fields:
        overlap = left & right
        if overlap:
            logger.error("_validate_split leakage kind=%s count=%d", name, len(overlap))
            raise _DiscoveryBlocked("split-leakage", f"cross-split-{name}-overlap")
    logger.debug("_validate_split exit")


def _validate_rows(name: str, rows: tuple[DiscoveryRow, ...]) -> None:
    logger.debug("_validate_rows entry split=%s count=%d", name, len(rows))
    if len(rows) > _HARD_MAX_ROWS_PER_SPLIT:
        logger.error("_validate_rows resource limit split=%s count=%d", name, len(rows))
        raise _DiscoveryBlocked("resource-limit", f"{name}-row-count")
    ids = [row.row_id for row in rows]
    if len(set(ids)) != len(ids):
        logger.error("_validate_rows duplicate row split=%s", name)
        raise _DiscoveryBlocked("invalid-data", f"{name}-duplicate-row-id")
    group_targets: dict[str, set[object]] = defaultdict(set)
    source_groups: dict[str, set[str]] = defaultdict(set)
    content_groups: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        identities = (row.row_id, row.source_id, row.content_id, row.group_id)
        if any(not _bounded_text(value) for value in identities):
            logger.error("_validate_rows invalid identity split=%s", name)
            raise _DiscoveryBlocked("invalid-data", f"{name}-invalid-identity")
        _validate_canonical(row.features)
        if type(row.target) not in {str, int, bool}:
            logger.error("_validate_rows invalid target split=%s", name)
            raise _DiscoveryBlocked("invalid-data", f"{name}-invalid-target")
        _validate_canonical(row.target)
        group_targets[row.group_id].add(_canonical_key(row.target))
        source_groups[row.source_id].add(row.group_id)
        content_groups[row.content_id].add(row.group_id)
    if any(len(targets) != 1 for targets in group_targets.values()):
        logger.error("_validate_rows multiple targets per group split=%s", name)
        raise _DiscoveryBlocked("invalid-data", f"{name}-one-target-per-group-required")
    if len(group_targets) < 2:
        logger.error("_validate_rows too few groups split=%s", name)
        raise _DiscoveryBlocked("insufficient-calibration", f"{name}-needs-two-groups")
    group_sizes = Counter(row.group_id for row in rows)
    if len(set(group_sizes.values())) != 1:
        logger.error("_validate_rows unequal group sizes split=%s", name)
        raise _DiscoveryBlocked("invalid-data", f"{name}-unequal-group-sizes")
    if any(len(groups) != 1 for groups in (*source_groups.values(), *content_groups.values())):
        logger.error("_validate_rows lineage crosses groups split=%s", name)
        raise _DiscoveryBlocked("invalid-data", f"{name}-lineage-crosses-groups")
    logger.debug("_validate_rows exit split=%s groups=%d", name, len(group_targets))


def _validate_canonical(value: Canonical) -> int:
    logger.debug("_validate_canonical entry type=%s", type(value).__name__)
    stack: list[tuple[Canonical, int]] = [(value, 0)]
    nodes = 0
    units = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > _HARD_MAX_FEATURE_NODES or depth > _HARD_MAX_FEATURE_DEPTH:
            logger.error("_validate_canonical resource limit")
            raise _DiscoveryBlocked("resource-limit", "canonical-feature-shape")
        if item is None or type(item) in {str, int, bool}:
            if type(item) is str:
                if len(item) > _HARD_MAX_STRING_BYTES:
                    logger.error("_validate_canonical string resource limit")
                    raise _DiscoveryBlocked("resource-limit", "canonical-string-bytes")
                size = len(item.encode("utf-8"))
                if size > _HARD_MAX_STRING_BYTES:
                    logger.error("_validate_canonical string byte limit")
                    raise _DiscoveryBlocked("resource-limit", "canonical-string-bytes")
                units += size
            elif type(item) is int and item.bit_length() > _HARD_MAX_STRING_BYTES * 8:
                logger.error("_validate_canonical integer resource limit")
                raise _DiscoveryBlocked("resource-limit", "canonical-integer-bits")
            continue
        if type(item) is float:
            if isfinite(item):
                continue
            logger.error("_validate_canonical nonfinite")
            raise _DiscoveryBlocked("invalid-data", "nan-or-infinity")
        if type(item) is tuple:
            stack.extend((child, depth + 1) for child in item)
            continue
        logger.error("_validate_canonical noncanonical type=%s", type(item).__name__)
        raise _DiscoveryBlocked("invalid-data", f"noncanonical:{type(item).__name__}")
    logger.debug("_validate_canonical exit nodes=%d", nodes)
    return nodes + units


def _registry(grammar: ObserverGrammar) -> dict[str, ObserverPrimitive]:
    logger.debug("_registry entry")
    if (
        type(grammar) is not ObserverGrammar
        or not _bounded_text(grammar.grammar_id)
        or not _bounded_text(grammar.input_kind)
        or type(grammar.accepted_output_kinds) is not tuple
        or not grammar.accepted_output_kinds
        or type(grammar.primitives) is not tuple
        or type(grammar.max_depth) is not int
        or type(grammar.max_cost) is not int
        or grammar.max_depth < 0
        or grammar.max_cost < 0
    ):
        logger.error("_registry invalid grammar")
        raise _DiscoveryBlocked("invalid-grammar", "grammar-record")
    if any(type(item) is not ObserverPrimitive for item in grammar.primitives):
        logger.error("_registry invalid primitive record")
        raise _DiscoveryBlocked("invalid-grammar", "primitive-record")
    if (
        len(grammar.primitives) > _HARD_MAX_PRIMITIVES
        or grammar.max_depth > _HARD_MAX_GRAMMAR_DEPTH
        or grammar.max_cost > _HARD_MAX_GRAMMAR_COST
    ):
        logger.error("_registry grammar resource limit")
        raise _DiscoveryBlocked("resource-limit", "grammar-shape")
    if any(not _bounded_text(kind) for kind in grammar.accepted_output_kinds):
        logger.error("_registry invalid accepted output kind")
        raise _DiscoveryBlocked("invalid-grammar", "accepted-output-kind")
    if any(
        not _bounded_text(item.name)
        or not _bounded_text(item.input_kind)
        or not _bounded_text(item.output_kind)
        or type(item.semantic_id) is not str
        or len(item.semantic_id) > _HARD_MAX_ID_BYTES
        or len(item.semantic_id.encode("utf-8")) > _HARD_MAX_ID_BYTES
        or type(item.cost) is not int
        or item.cost <= 0
        or item.cost > _HARD_MAX_GRAMMAR_COST
        for item in grammar.primitives
    ):
        logger.error("_registry invalid primitive fields")
        raise _DiscoveryBlocked("invalid-grammar", "primitive-fields")
    registry = {item.name: item for item in grammar.primitives}
    if len(registry) != len(grammar.primitives):
        logger.error("_registry duplicate primitive")
        raise _DiscoveryBlocked("invalid-grammar", "duplicate-primitive")
    try:
        for item in grammar.primitives:
            _validate_evaluator_state(item.evaluator)
            callable_identity(item.evaluator, item.semantic_id)
    except (TypeError, ValueError) as exc:
        logger.error("_registry unbound semantics type=%s", type(exc).__name__)
        raise _DiscoveryBlocked("unbound-semantics", str(exc)) from exc
    logger.debug("_registry exit count=%d", len(registry))
    return registry


def _validate_evaluator_state(evaluator: object) -> None:
    """Reject directly reachable mutable state before evaluator callbacks."""
    logger.debug("_validate_evaluator_state entry type=%s", type(evaluator).__name__)
    if getattr(evaluator, "__dict__", None):
        logger.error("_validate_evaluator_state mutable function attributes")
        raise _DiscoveryBlocked("untrusted-evaluator-state", "function-attributes")
    closure = getattr(evaluator, "__closure__", None) or ()
    if any(not _immutable_semantic_state(cell.cell_contents) for cell in closure):
        logger.error("_validate_evaluator_state mutable closure")
        raise _DiscoveryBlocked("untrusted-evaluator-state", "mutable-closure")
    code = getattr(evaluator, "__code__", None)
    namespace = getattr(evaluator, "__globals__", {})
    if code is not None and any(
        name in namespace and not _immutable_semantic_state(namespace[name]) for name in code.co_names
    ):
        logger.error("_validate_evaluator_state mutable global dependency")
        raise _DiscoveryBlocked("untrusted-evaluator-state", "mutable-global")
    logger.debug("_validate_evaluator_state exit")


def _immutable_semantic_state(value: object) -> bool:
    logger.debug("_immutable_semantic_state entry type=%s", type(value).__name__)
    if value is None or type(value) in {str, int, float, bool, bytes} or callable(value):
        result = True
    elif type(value) in {tuple, frozenset}:
        result = all(_immutable_semantic_state(item) for item in value)
    else:
        result = False
    logger.debug("_immutable_semantic_state exit valid=%s", result)
    return result


def _validate_catalog(
    catalog: tuple[ObserverTerm, ...],
    grammar: ObserverGrammar,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
    registry: dict[str, ObserverPrimitive],
) -> None:
    logger.debug("_validate_catalog entry count=%d", len(catalog))
    if not catalog:
        logger.error("_validate_catalog empty")
        raise _DiscoveryBlocked("invalid-grammar", "empty-catalog")
    if len(catalog) > config.max_catalog_size:
        logger.error("_validate_catalog cutoff count=%d", len(catalog))
        raise _DiscoveryBlocked("catalog-cutoff", f"complete-size={len(catalog)}")
    fingerprints = [observer_fingerprint(term) for term in catalog]
    if len(set(fingerprints)) != len(fingerprints):
        logger.error("_validate_catalog duplicate terms")
        raise _DiscoveryBlocked("invalid-grammar", "duplicate-catalog-term")
    if type(baselines) is not tuple or any(type(item) is not NamedBaseline for item in baselines):
        logger.error("_validate_catalog invalid baseline records")
        raise _DiscoveryBlocked("invalid-baseline", "immutable-named-baseline-records-required")
    baseline_names = [item.name for item in baselines]
    if not baseline_names:
        logger.error("_validate_catalog missing baseline")
        raise _DiscoveryBlocked("invalid-baseline", "at-least-one-named-baseline-required")
    if len(set(baseline_names)) != len(baseline_names) or any(not _bounded_text(name) for name in baseline_names):
        logger.error("_validate_catalog invalid baseline names")
        raise _DiscoveryBlocked("invalid-baseline", "names-must-be-unique")
    catalog_terms = {canonical_term(term) for term in catalog}
    for baseline in baselines:
        if not _bounded_text(baseline.observer_class) or not _bounded_text(baseline.boundary):
            logger.error("_validate_catalog invalid baseline metadata")
            raise _DiscoveryBlocked("invalid-baseline", "metadata")
        try:
            observer_term_cost(baseline.term, registry)
        except (KeyError, ValueError) as exc:
            logger.error("_validate_catalog invalid baseline term")
            raise _DiscoveryBlocked("invalid-baseline", "term") from exc
        if canonical_term(baseline.term) not in catalog_terms:
            logger.error("_validate_catalog baseline outside catalog name=%s", baseline.name)
            raise _DiscoveryBlocked("invalid-baseline", "term-outside-complete-catalog")
    logger.debug("_validate_catalog exit")


def _bounded_text(value: object) -> bool:
    logger.debug("_bounded_text entry type=%s", type(value).__name__)
    result = (
        type(value) is str
        and bool(value)
        and len(value) <= _HARD_MAX_ID_BYTES
        and len(value.encode("utf-8")) <= _HARD_MAX_ID_BYTES
    )
    logger.debug("_bounded_text exit valid=%s", result)
    return result


def _validate_work_budget(
    catalog_size: int,
    split: DiscoverySplit,
    config: DiscoveryConfig,
) -> None:
    """Precharge every row-candidate statistic before evaluator execution."""
    logger.debug("_validate_work_budget entry catalog=%d", catalog_size)
    checks = max(2, config.determinism_checks)
    train_rows = len(split.train)
    holdout_rows = len(split.holdout)
    work_items = catalog_size * (
        checks * (train_rows + holdout_rows)
        + config.bootstrap_replicates * train_rows
        + config.permutation_count * holdout_rows
    )
    if work_items > _HARD_MAX_WORK_ITEMS:
        logger.error("_validate_work_budget resource limit work_items=%d", work_items)
        raise _DiscoveryBlocked("resource-limit", "statistical-work-items")
    logger.debug("_validate_work_budget exit work_items=%d", work_items)


def _evaluate_catalog(
    catalog: tuple[ObserverTerm, ...],
    rows: tuple[DiscoveryRow, ...],
    registry: dict[str, ObserverPrimitive],
    config: DiscoveryConfig,
) -> tuple[tuple[Canonical, ...], ...]:
    logger.debug("_evaluate_catalog entry terms=%d rows=%d", len(catalog), len(rows))
    result: list[tuple[Canonical, ...]] = []
    retained_units = 0
    checks = max(2, config.determinism_checks)
    for term in catalog:
        values: list[Canonical] = []
        for row_index, row in enumerate(rows):
            responses = tuple(evaluate_observer(term, row.features, registry) for _ in range(checks))
            response_units = tuple(
                _validate_observer_value(response.value) if response.status == "ready" else 0 for response in responses
            )
            signatures = {
                (
                    response.status,
                    _canonical_key(response.value) if response.status == "ready" else None,
                    response.obstruction,
                    response.trace,
                )
                for response in responses
            }
            if len(signatures) != 1:
                logger.error("_evaluate_catalog nondeterministic row_index=%d", row_index)
                raise _DiscoveryBlocked("nondeterministic-evaluator", f"row-index={row_index}")
            response = responses[0]
            if response.status != "ready":
                logger.error("_evaluate_catalog evaluator failure row_index=%d", row_index)
                raise _DiscoveryBlocked(
                    "evaluator-failure",
                    response.obstruction or f"row-index={row_index}",
                )
            retained_units += response_units[0]
            if retained_units > _HARD_MAX_RETAINED_OUTPUT_UNITS:
                logger.error("_evaluate_catalog retained-output resource limit")
                raise _DiscoveryBlocked("resource-limit", "retained-observer-output")
            values.append(response.value)
        result.append(tuple(values))
    frozen = tuple(result)
    logger.debug("_evaluate_catalog exit terms=%d", len(frozen))
    return frozen


def _validate_observer_value(value: Canonical) -> int:
    logger.debug("_validate_observer_value entry")
    try:
        units = _validate_canonical(value)
    except _DiscoveryBlocked as exc:
        logger.error("_validate_observer_value invalid reason=%s", exc.reason)
        if exc.reason == "resource-limit":
            raise
        raise _DiscoveryBlocked("noncanonical-evaluator-result", exc.detail) from exc
    logger.debug("_validate_observer_value exit")
    return units


def _score_catalog(
    catalog: tuple[ObserverTerm, ...],
    outputs: tuple[tuple[Canonical, ...], ...],
    targets: tuple[str | int | bool, ...],
    grammar: ObserverGrammar,
    registry: dict[str, ObserverPrimitive],
    config: DiscoveryConfig,
) -> tuple[DiscoveryScore, ...]:
    logger.debug("_score_catalog entry count=%d", len(catalog))
    scores = []
    for term, values in zip(catalog, outputs, strict=True):
        information = _mutual_information(values, targets)
        complexity = observer_term_cost(term, registry)
        objective = information - config.complexity_cost_per_unit * complexity
        scores.append(DiscoveryScore(term, observer_fingerprint(term), information, complexity, objective))
    result = tuple(
        sorted(
            scores,
            key=lambda row: (-row.objective, -row.information_bits, row.complexity, row.fingerprint),
        )
    )
    if len(result) != len(catalog):
        logger.error("_score_catalog incomplete")
        raise _DiscoveryBlocked("catalog-cutoff", "scoring-incomplete")
    logger.debug("_score_catalog exit winner=%s", result[0].fingerprint[:12])
    return result


def _mutual_information(
    values: tuple[Canonical, ...],
    targets: tuple[str | int | bool, ...],
) -> float:
    logger.debug("_mutual_information entry count=%d", len(values))
    if len(values) != len(targets) or not values:
        logger.error("_mutual_information invalid shape")
        raise _DiscoveryBlocked("invalid-data", "mutual-information-shape")
    value_keys = tuple(_canonical_key(value) for value in values)
    target_keys = tuple(_canonical_key(target) for target in targets)
    joint = Counter(zip(value_keys, target_keys, strict=True))
    value_counts = Counter(value_keys)
    target_counts = Counter(target_keys)
    total = len(values)
    result = sum(
        (count / total) * log2((count * total) / (value_counts[value] * target_counts[target]))
        for (value, target), count in joint.items()
    )
    if not isfinite(result):
        logger.error("_mutual_information nonfinite")
        raise _DiscoveryBlocked("numeric-failure", "mutual-information")
    logger.debug("_mutual_information exit bits=%.6f", result)
    return result


def _canonical_key(value: Canonical) -> object:
    logger.debug("_canonical_key entry type=%s", type(value).__name__)
    if value is None:
        result: object = ("none",)
    elif type(value) is bool:
        result = ("bool", value)
    elif type(value) is int:
        result = ("int", value)
    elif type(value) is float:
        result = ("float", value.hex())
    elif type(value) is str:
        result = ("str", value)
    elif type(value) is tuple:
        result = ("tuple", tuple(_canonical_key(item) for item in value))
    else:
        logger.error("_canonical_key invalid type=%s", type(value).__name__)
        raise _DiscoveryBlocked("invalid-data", f"noncanonical:{type(value).__name__}")
    logger.debug("_canonical_key exit type=%s", type(value).__name__)
    return result


def _bootstrap_stability(
    winner: DiscoveryScore,
    catalog: tuple[ObserverTerm, ...],
    outputs: tuple[tuple[Canonical, ...], ...],
    rows: tuple[DiscoveryRow, ...],
    grammar: ObserverGrammar,
    registry: dict[str, ObserverPrimitive],
    config: DiscoveryConfig,
    protocol_digest: str,
) -> BootstrapStability:
    logger.debug("_bootstrap_stability entry replicates=%d", config.bootstrap_replicates)
    grouped = _group_indices(rows)
    group_ids = tuple(sorted(grouped))
    rng = random.Random(_seed(protocol_digest, config.random_seed, "bootstrap"))
    matches = 0
    targets = tuple(row.target for row in rows)
    for _ in range(config.bootstrap_replicates):
        sampled = tuple(rng.choice(group_ids) for _ in group_ids)
        indices = tuple(index for group in sampled for index in grouped[group])
        sampled_outputs = tuple(tuple(values[index] for index in indices) for values in outputs)
        sampled_targets = tuple(targets[index] for index in indices)
        selected = _score_catalog(catalog, sampled_outputs, sampled_targets, grammar, registry, config)[0]
        matches += selected.fingerprint == winner.fingerprint
    result = BootstrapStability(config.bootstrap_replicates, matches, matches / config.bootstrap_replicates)
    logger.debug("_bootstrap_stability exit fraction=%.6f", result.fraction)
    return result


def _permutation_calibration(
    catalog: tuple[ObserverTerm, ...],
    outputs: tuple[tuple[Canonical, ...], ...],
    rows: tuple[DiscoveryRow, ...],
    observed_winner_information: float,
    config: DiscoveryConfig,
    protocol_digest: str,
) -> PermutationCalibration:
    logger.debug("_permutation_calibration entry count=%d", config.permutation_count)
    grouped = _group_indices(rows)
    group_ids = tuple(sorted(grouped))
    target_by_group = {group: rows[indices[0]].target for group, indices in grouped.items()}
    rng = random.Random(_seed(protocol_digest, config.random_seed, "permutation"))
    maxima: list[float] = []
    group_targets = [target_by_group[group] for group in group_ids]
    for _ in range(config.permutation_count):
        permuted = group_targets.copy()
        rng.shuffle(permuted)
        target_map = dict(zip(group_ids, permuted, strict=True))
        permuted_targets = tuple(target_map[row.group_id] for row in rows)
        maxima.append(max(_mutual_information(values, permuted_targets) for values in outputs))
    exceedances = sum(value >= observed_winner_information for value in maxima)
    p_value = (exceedances + 1) / (config.permutation_count + 1)
    result = PermutationCalibration(
        config.permutation_count,
        exceedances,
        observed_winner_information,
        p_value,
        tuple(maxima),
    )
    logger.debug("_permutation_calibration exit p=%.6f", p_value)
    return result


def _baseline_comparisons(
    baselines: tuple[NamedBaseline, ...],
    catalog: tuple[ObserverTerm, ...],
    outputs: tuple[tuple[Canonical, ...], ...],
    targets: tuple[str | int | bool, ...],
) -> tuple[BaselineComparison, ...]:
    logger.debug("_baseline_comparisons entry count=%d", len(baselines))
    by_term = {
        canonical_term(term): (observer_fingerprint(term), values)
        for term, values in zip(catalog, outputs, strict=True)
    }
    result = tuple(
        BaselineComparison(
            item.name,
            item.observer_class,
            by_term[canonical_term(item.term)][0],
            _mutual_information(by_term[canonical_term(item.term)][1], targets),
            item.boundary,
        )
        for item in baselines
    )
    logger.debug("_baseline_comparisons exit count=%d", len(result))
    return result


def _discovery_failures(
    holdout_information: float,
    observer_gap: float,
    calibration: PermutationCalibration,
    stability: BootstrapStability,
    config: DiscoveryConfig,
) -> tuple[DiscoveryObstruction, ...]:
    logger.debug("_discovery_failures entry")
    failures = []
    if holdout_information <= config.minimum_holdout_information_bits:
        failures.append(DiscoveryObstruction("holdout-threshold", holdout_information.hex()))
    if observer_gap <= 0.0:
        failures.append(DiscoveryObstruction("no-observer-gap", observer_gap.hex()))
    if calibration.add_one_p_value > config.significance_alpha:
        failures.append(DiscoveryObstruction("not-significant", calibration.add_one_p_value.hex()))
    if stability.fraction < config.minimum_stability:
        failures.append(DiscoveryObstruction("unstable-selection", stability.fraction.hex()))
    result = tuple(failures)
    logger.debug("_discovery_failures exit count=%d", len(result))
    return result


def _group_indices(rows: tuple[DiscoveryRow, ...]) -> dict[str, tuple[int, ...]]:
    logger.debug("_group_indices entry rows=%d", len(rows))
    mutable: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        mutable[row.group_id].append(index)
    result = {group: tuple(indices) for group, indices in mutable.items()}
    logger.debug("_group_indices exit groups=%d", len(result))
    return result


def _digests(
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
    catalog: tuple[ObserverTerm, ...],
) -> DiscoveryDigests:
    logger.debug("_digests entry")
    result = discovery_input_digests(grammar, split, baselines, config, catalog)
    logger.debug("_digests exit protocol=%s", result.protocol[:12])
    return result


def _assert_protocol_unchanged(
    expected: DiscoveryDigests,
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
    catalog: tuple[ObserverTerm, ...],
) -> None:
    logger.debug("_assert_protocol_unchanged entry")
    actual = _digests(grammar, split, baselines, config, catalog)
    if actual != replace(expected, train_evaluation=""):
        logger.error("_assert_protocol_unchanged mutation detected")
        raise _DiscoveryBlocked("protocol-mutation", "data-catalog-config-or-evaluator-changed")
    logger.debug("_assert_protocol_unchanged exit")


def _seed(protocol_digest: str, configured_seed: str, purpose: str) -> int:
    logger.debug("_seed entry purpose=%s", purpose)
    digest = digest_data(
        {"protocol": protocol_digest, "configured_seed": configured_seed, "purpose": purpose},
        "veyra.observer-discovery.rng-seed.v1",
    )
    result = int(digest, 16)
    logger.debug("_seed exit purpose=%s", purpose)
    return result


def _empty_digests() -> DiscoveryDigests:
    logger.debug("_empty_digests entry")
    result = DiscoveryDigests("", "", "", "", "", "", "", "", "")
    logger.debug("_empty_digests exit")
    return result


def _terminal(
    status: str,
    digests: DiscoveryDigests,
    catalog_size: int,
    obstructions: tuple[DiscoveryObstruction, ...],
    policy: DiscoveryPolicyReceipt | None = None,
    grammar: DiscoveryGrammarReceipt | None = None,
    train_best_objective: float | None = None,
) -> ObserverDiscoveryReport:
    logger.debug("_terminal entry status=%s", status)
    result = ObserverDiscoveryReport(
        status=status,
        policy=policy,
        grammar=grammar,
        winner=None,
        train_best_objective=train_best_objective,
        holdout_information_bits=None,
        baselines=(),
        observer_gap_bits=None,
        calibration=None,
        stability=None,
        catalog_size=catalog_size,
        digests=digests,
        obstructions=obstructions,
        boundary=BOUNDARY,
    )
    bound = bind_discovery_report(result)
    logger.debug("_terminal exit status=%s", status)
    return bound
