"""Binding and independent structural replay for observer-discovery reports."""
from __future__ import annotations

from dataclasses import replace
import logging
from math import ceil, isfinite

from .observer_discovery_types import (
    BaselineComparison,
    BootstrapStability,
    DiscoveryConfig,
    DiscoveryDigests,
    DiscoveryGrammarReceipt,
    DiscoveryObstruction,
    DiscoveryPolicyReceipt,
    DiscoveryPrimitiveReceipt,
    DiscoveryScore,
    ObserverDiscoveryReport,
    PermutationCalibration,
    HARD_MAX_ALPHA,
    HARD_MIN_BOOTSTRAPS,
    HARD_MIN_PERMUTATIONS,
    HARD_MIN_STABILITY,
)
from .observer_synthesis import canonical_term, observer_fingerprint
from .observer_synthesis_types import ObserverGrammar, ObserverTerm
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

_STATUSES = frozenset({"FOUND", "NOT_FOUND_WITHIN_BUDGET", "BLOCKED"})
_MAX_PERMUTATIONS = 4095
_MAX_BOOTSTRAPS = 1024
_MAX_DETERMINISM_CHECKS = 8
_MAX_CATALOG_SIZE = 4096
_MAX_TERM_NODES = 4096
_MAX_TERM_DEPTH = 16
_MAX_TERM_TEXT_BYTES = 4096
_MAX_TERM_TOTAL_TEXT_BYTES = 1_000_000
_MAX_POLICY_TEXT_BYTES = 512
_MAX_BASELINES = 4096
_MAX_OBSTRUCTIONS = 64
_MAX_REPORT_TEXT_BYTES = 4096
_MAX_PRIMITIVES = 12
_MAX_GRAMMAR_DEPTH = 2
_MAX_GRAMMAR_COST = 8


def discovery_policy_receipt(config: DiscoveryConfig) -> DiscoveryPolicyReceipt:
    """Publish the complete configuration embedded in a terminal report."""
    logger.debug("discovery_policy_receipt entry")
    result = DiscoveryPolicyReceipt(
        complexity_cost_per_unit=config.complexity_cost_per_unit,
        minimum_train_objective=config.minimum_train_objective,
        minimum_holdout_information_bits=config.minimum_holdout_information_bits,
        significance_alpha=config.significance_alpha,
        permutation_count=config.permutation_count,
        bootstrap_replicates=config.bootstrap_replicates,
        minimum_stability=config.minimum_stability,
        determinism_checks=config.determinism_checks,
        max_catalog_size=config.max_catalog_size,
        random_seed=config.random_seed,
    )
    logger.debug("discovery_policy_receipt exit")
    return result


def discovery_policy_data(policy: DiscoveryPolicyReceipt) -> dict[str, object]:
    """Return the canonical complete configuration receipt payload."""
    logger.debug("discovery_policy_data entry")
    result = {
        "complexity_cost_per_unit": policy.complexity_cost_per_unit.hex(),
        "minimum_train_objective": policy.minimum_train_objective.hex(),
        "minimum_holdout_information_bits": policy.minimum_holdout_information_bits.hex(),
        "significance_alpha": policy.significance_alpha.hex(),
        "permutation_count": policy.permutation_count,
        "bootstrap_replicates": policy.bootstrap_replicates,
        "minimum_stability": policy.minimum_stability.hex(),
        "determinism_checks": policy.determinism_checks,
        "max_catalog_size": policy.max_catalog_size,
        "random_seed": policy.random_seed,
    }
    logger.debug("discovery_policy_data exit")
    return result


def discovery_grammar_receipt(grammar: ObserverGrammar) -> DiscoveryGrammarReceipt:
    """Publish the structural grammar required for independent cost replay."""
    logger.debug("discovery_grammar_receipt entry")
    result = DiscoveryGrammarReceipt(
        grammar.grammar_id,
        grammar.input_kind,
        grammar.accepted_output_kinds,
        tuple(
            DiscoveryPrimitiveReceipt(row.name, row.input_kind, row.output_kind, row.cost)
            for row in grammar.primitives
        ),
        grammar.max_depth,
        grammar.max_cost,
    )
    logger.debug("discovery_grammar_receipt exit")
    return result


def discovery_grammar_data(receipt: DiscoveryGrammarReceipt) -> dict[str, object]:
    """Return the canonical public structural-grammar payload."""
    logger.debug("discovery_grammar_data entry")
    result = {
        "grammar_id": receipt.grammar_id,
        "input_kind": receipt.input_kind,
        "accepted_output_kinds": list(receipt.accepted_output_kinds),
        "primitives": [
            {
                "name": row.name,
                "input_kind": row.input_kind,
                "output_kind": row.output_kind,
                "cost": row.cost,
            }
            for row in receipt.primitives
        ],
        "max_depth": receipt.max_depth,
        "max_cost": receipt.max_cost,
    }
    logger.debug("discovery_grammar_data exit")
    return result


def bind_discovery_train_evaluation(
    digests: DiscoveryDigests, train_best_objective: float,
) -> DiscoveryDigests:
    """Bind the reported train optimum to the existing protocol/data/catalog roots."""
    logger.debug("bind_discovery_train_evaluation entry")
    value = digest_data(
        {
            "protocol": digests.protocol,
            "train_data": digests.train_data,
            "catalog": digests.catalog,
            "train_best_objective": train_best_objective.hex(),
        },
        "veyra.observer-discovery.train-evaluation.v1",
    )
    result = replace(digests, train_evaluation=value)
    logger.debug("bind_discovery_train_evaluation exit digest=%s", value[:12])
    return result


def bind_discovery_report(report: ObserverDiscoveryReport) -> ObserverDiscoveryReport:
    """Return a report with its domain-separated terminal result digest bound."""
    logger.debug("bind_discovery_report entry status=%s", getattr(report, "status", "<invalid>"))
    if type(report) is not ObserverDiscoveryReport:
        logger.error("bind_discovery_report invalid report type")
        raise TypeError("invalid-discovery-report")
    result_digest = digest_data(_report_data(report), "veyra.observer-discovery.result.v1")
    result = replace(report, digests=replace(report.digests, result=result_digest))
    logger.debug("bind_discovery_report exit digest=%s", result_digest[:12])
    return result


def validate_discovery_report(
    report: object, *, expected_train_evaluation: str | None = None,
) -> bool:
    """Replay local invariants, optionally pinning a trusted train-evaluation root."""
    logger.debug("validate_discovery_report entry type=%s", type(report).__name__)
    try:
        valid = _validate_shape(report)
        if expected_train_evaluation is not None:
            valid = (
                valid
                and _hex_digest(expected_train_evaluation)
                and report.digests.train_evaluation == expected_train_evaluation
            )
        blank = replace(report, digests=replace(report.digests, result=""))
        valid = valid and bind_discovery_report(blank) == report
    except (AttributeError, TypeError, ValueError, RecursionError, OverflowError):
        logger.error("validate_discovery_report rejected malformed report")
        return False
    logger.debug("validate_discovery_report exit valid=%s", valid)
    return valid


def _validate_shape(report: object) -> bool:
    logger.debug("_validate_shape entry")
    if (
        type(report) is not ObserverDiscoveryReport
        or report.status not in _STATUSES
        or type(report.catalog_size) is not int
        or report.catalog_size < 0
        or report.catalog_size > _MAX_CATALOG_SIZE
        or type(report.boundary) is not str
        or not _bounded_report_text(report.boundary)
        or type(report.digests) is not DiscoveryDigests
        or type(report.baselines) is not tuple
        or len(report.baselines) > _MAX_BASELINES
        or any(type(row) is not BaselineComparison for row in report.baselines)
        or type(report.obstructions) is not tuple
        or len(report.obstructions) > _MAX_OBSTRUCTIONS
        or any(type(row) is not DiscoveryObstruction for row in report.obstructions)
    ):
        return False
    if report.status == "BLOCKED":
        if report.policy is not None or report.grammar is not None:
            return False
    elif not _valid_policy(report.policy) or not _valid_grammar(report.grammar):
        return False
    elif not _finite(report.train_best_objective):
        return False
    elif not 1 <= report.catalog_size <= report.policy.max_catalog_size:
        return False
    evidence_digests = (
        report.digests.protocol,
        report.digests.protocol_material,
        report.digests.policy,
        report.digests.grammar,
        report.digests.train_data,
        report.digests.train_evaluation,
        report.digests.holdout_data,
        report.digests.catalog,
    )
    if (
        not _hex_digest(report.digests.result)
        or any(value != "" and not _hex_digest(value) for value in evidence_digests)
        or (report.status != "BLOCKED" and any(not _hex_digest(value) for value in evidence_digests))
    ):
        return False
    if report.status != "BLOCKED":
        expected_policy = digest_data(
            discovery_policy_data(report.policy),
            "veyra.observer-discovery.policy.v1",
        )
        expected_protocol = digest_data(
            {
                "protocol_material": report.digests.protocol_material,
                "policy": expected_policy,
                "grammar": report.digests.grammar,
            },
            "veyra.observer-discovery.protocol.v1",
        )
        expected_grammar = digest_data(
            discovery_grammar_data(report.grammar),
            "veyra.observer-discovery.grammar.v1",
        )
        if (
            report.digests.policy != expected_policy
            or report.digests.grammar != expected_grammar
            or report.digests.protocol != expected_protocol
        ):
            return False
        expected_train = bind_discovery_train_evaluation(
            replace(report.digests, train_evaluation=""), report.train_best_objective,
        ).train_evaluation
        if report.digests.train_evaluation != expected_train:
            return False
    if (
        any(not _valid_baseline(row) for row in report.baselines)
        or len({row.name for row in report.baselines}) != len(report.baselines)
        or any(not _valid_obstruction(row) for row in report.obstructions)
        or (report.calibration is not None and not _valid_calibration(report.calibration))
        or (report.stability is not None and not _valid_stability(report.stability))
    ):
        return False
    if report.status == "FOUND":
        policy = report.policy
        if type(policy) is not DiscoveryPolicyReceipt:
            return False
        best_baseline = max(row.information_bits for row in report.baselines)
        valid = (
            _valid_score(report.winner, report.grammar)
            and report.train_best_objective == report.winner.objective
            and report.winner.objective
            == report.winner.information_bits
            - policy.complexity_cost_per_unit * report.winner.complexity
            and report.winner.objective > policy.minimum_train_objective
            and _finite(report.holdout_information_bits)
            and report.holdout_information_bits > policy.minimum_holdout_information_bits
            and bool(report.baselines)
            and _finite(report.observer_gap_bits)
            and report.observer_gap_bits > 0.0
            and report.observer_gap_bits
            == report.holdout_information_bits - best_baseline
            and type(report.calibration) is PermutationCalibration
            and report.calibration.permutations == policy.permutation_count
            and report.calibration.observed_winner_information_bits
            == report.holdout_information_bits
            and report.calibration.add_one_p_value <= policy.significance_alpha
            and type(report.stability) is BootstrapStability
            and report.stability.replicates == policy.bootstrap_replicates
            and report.stability.fraction >= policy.minimum_stability
            and not report.obstructions
        )
    elif report.status == "BLOCKED":
        valid = (
            report.winner is None
            and report.train_best_objective is None
            and report.holdout_information_bits is None
            and not report.baselines
            and report.observer_gap_bits is None
            and report.calibration is None
            and report.stability is None
            and bool(report.obstructions)
        )
    else:
        valid = _valid_not_found(report)
    logger.debug("_validate_shape exit valid=%s", valid)
    return valid


def _report_data(report: ObserverDiscoveryReport) -> dict[str, object]:
    logger.debug("_report_data entry status=%s", report.status)
    result = {
        "status": report.status,
        "policy": None if report.policy is None else discovery_policy_data(report.policy),
        "grammar": None if report.grammar is None else discovery_grammar_data(report.grammar),
        "winner": None if report.winner is None else _score_data(report.winner),
        "train_best_objective": _float_data(report.train_best_objective),
        "holdout_information_bits": _float_data(report.holdout_information_bits),
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
        "observer_gap_bits": _float_data(report.observer_gap_bits),
        "calibration": None if report.calibration is None else {
            "permutations": report.calibration.permutations,
            "exceedances": report.calibration.exceedances,
            "observed_winner_information_bits": report.calibration.observed_winner_information_bits.hex(),
            "add_one_p_value": report.calibration.add_one_p_value.hex(),
            "null_maxima_bits": [value.hex() for value in report.calibration.null_maxima_bits],
        },
        "stability": None if report.stability is None else {
            "replicates": report.stability.replicates,
            "winner_matches": report.stability.winner_matches,
            "fraction": report.stability.fraction.hex(),
        },
        "catalog_size": report.catalog_size,
        "protocol": report.digests.protocol,
        "protocol_material": report.digests.protocol_material,
        "policy_digest": report.digests.policy,
        "grammar_digest": report.digests.grammar,
        "train_data": report.digests.train_data,
        "train_evaluation": report.digests.train_evaluation,
        "holdout_data": report.digests.holdout_data,
        "catalog": report.digests.catalog,
        "obstructions": [
            {"reason": row.reason, "detail": row.detail} for row in report.obstructions
        ],
        "boundary": report.boundary,
    }
    logger.debug("_report_data exit")
    return result


def _score_data(score: DiscoveryScore) -> dict[str, object]:
    logger.debug("_score_data entry fingerprint=%s", score.fingerprint[:12])
    result = {
        "term": canonical_term(score.term),
        "fingerprint": score.fingerprint,
        "information_bits": score.information_bits.hex(),
        "complexity": score.complexity,
        "objective": score.objective.hex(),
    }
    logger.debug("_score_data exit")
    return result


def _float_data(value: float | None) -> str | None:
    logger.debug("_float_data entry is_none=%s", value is None)
    result = None if value is None else value.hex()
    logger.debug("_float_data exit")
    return result


def _finite(value: object) -> bool:
    logger.debug("_finite entry type=%s", type(value).__name__)
    result = type(value) is float and isfinite(value)
    logger.debug("_finite exit valid=%s", result)
    return result


def _hex_digest(value: object) -> bool:
    logger.debug("_hex_digest entry type=%s", type(value).__name__)
    result = (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )
    logger.debug("_hex_digest exit valid=%s", result)
    return result


def _valid_score(score: object, grammar: DiscoveryGrammarReceipt) -> bool:
    logger.debug("_valid_score entry type=%s", type(score).__name__)
    if type(score) is not DiscoveryScore or not _valid_term(score.term):
        return False
    derived_cost = _receipt_term_cost(score.term, grammar)
    result = (
        score.term.output_kind in grammar.accepted_output_kinds
        and 0 <= derived_cost <= grammar.max_cost
        and _receipt_term_depth(score.term) <= grammar.max_depth
        and _canonical_pair_order(score.term)
        and _hex_digest(score.fingerprint)
        and observer_fingerprint(score.term) == score.fingerprint
        and _finite(score.information_bits)
        and score.information_bits >= 0.0
        and type(score.complexity) is int
        and score.complexity >= 0
        and score.complexity == derived_cost
        and _finite(score.objective)
    )
    logger.debug("_valid_score exit valid=%s", result)
    return result


def _receipt_term_depth(term: ObserverTerm) -> int:
    """Return R5 construction depth after absolute shape validation."""
    return 0 if not term.children else 1 + max(_receipt_term_depth(row) for row in term.children)


def _canonical_pair_order(term: ObserverTerm) -> bool:
    """Replay the enumerator's canonical commutative-pair ordering."""
    if term.op == "pair" and canonical_term(term.children[0]) > canonical_term(term.children[1]):
        return False
    return all(_canonical_pair_order(child) for child in term.children)


def _receipt_term_cost(term: ObserverTerm, grammar: DiscoveryGrammarReceipt) -> int:
    """Replay exact R5 cost and typing from the protocol-bound grammar receipt."""
    registry = {row.name: row for row in grammar.primitives}
    if term.op == "input" and term.output_kind == grammar.input_kind:
        return 0
    if term.op == "apply" and term.primitive in registry:
        primitive = registry[term.primitive]
        child = term.children[0]
        if child.output_kind != primitive.input_kind or term.output_kind != primitive.output_kind:
            return -1
        child_cost = _receipt_term_cost(child, grammar)
        return -1 if child_cost < 0 else primitive.cost + child_cost
    if term.op == "pair" and term.output_kind == "pair":
        child_costs = tuple(_receipt_term_cost(child, grammar) for child in term.children)
        return -1 if any(cost < 0 for cost in child_costs) else 1 + sum(child_costs)
    return -1


def _valid_grammar(grammar: object) -> bool:
    logger.debug("_valid_grammar entry type=%s", type(grammar).__name__)
    if type(grammar) is not DiscoveryGrammarReceipt:
        return False
    primitives = grammar.primitives
    valid = (
        _bounded_report_text(grammar.grammar_id)
        and _bounded_report_text(grammar.input_kind)
        and type(grammar.accepted_output_kinds) is tuple
        and bool(grammar.accepted_output_kinds)
        and len(grammar.accepted_output_kinds) <= _MAX_BASELINES
        and all(_bounded_report_text(value) for value in grammar.accepted_output_kinds)
        and type(primitives) is tuple
        and len(primitives) <= _MAX_PRIMITIVES
        and all(type(row) is DiscoveryPrimitiveReceipt for row in primitives)
        and all(
            _bounded_report_text(row.name)
            and _bounded_report_text(row.input_kind)
            and _bounded_report_text(row.output_kind)
            and type(row.cost) is int
            and 0 < row.cost <= _MAX_GRAMMAR_COST
            for row in primitives
        )
        and len({row.name for row in primitives}) == len(primitives)
        and type(grammar.max_depth) is int
        and 0 <= grammar.max_depth <= _MAX_GRAMMAR_DEPTH
        and type(grammar.max_cost) is int
        and 0 <= grammar.max_cost <= _MAX_GRAMMAR_COST
    )
    logger.debug("_valid_grammar exit valid=%s", valid)
    return valid


def _valid_term(term: object) -> bool:
    """Validate an exact, bounded, acyclic observer AST before recursive helpers."""
    logger.debug("_valid_term entry type=%s", type(term).__name__)
    stack: list[tuple[object, bool, int]] = [(term, False, 0)]
    visiting: set[int] = set()
    nodes = 0
    text_bytes = 0
    while stack:
        node, exiting, depth = stack.pop()
        if type(node) is not ObserverTerm:
            return False
        identity = id(node)
        if exiting:
            visiting.discard(identity)
            continue
        if identity in visiting or depth > _MAX_TERM_DEPTH:
            return False
        if (
            type(node.op) is not str
            or type(node.output_kind) is not str
            or type(node.primitive) is not str
            or not node.output_kind
            or any(
                len(value) > _MAX_TERM_TEXT_BYTES
                or len(value.encode("utf-8")) > _MAX_TERM_TEXT_BYTES
                for value in (node.op, node.output_kind, node.primitive)
            )
            or type(node.children) is not tuple
        ):
            return False
        text_bytes += sum(len(value.encode("utf-8")) for value in (
            node.op, node.output_kind, node.primitive,
        ))
        expected_children = {"input": 0, "apply": 1, "pair": 2}.get(node.op)
        if expected_children is None or len(node.children) != expected_children:
            return False
        if node.op == "apply" and not node.primitive:
            return False
        if node.op != "apply" and node.primitive:
            return False
        nodes += 1
        if nodes > _MAX_TERM_NODES or text_bytes > _MAX_TERM_TOTAL_TEXT_BYTES:
            return False
        visiting.add(identity)
        stack.append((node, True, depth))
        stack.extend((child, False, depth + 1) for child in reversed(node.children))
    logger.debug("_valid_term exit valid=True nodes=%d", nodes)
    return True


def _valid_policy(policy: object) -> bool:
    logger.debug("_valid_policy entry type=%s", type(policy).__name__)
    result = (
        type(policy) is DiscoveryPolicyReceipt
        and _finite(policy.complexity_cost_per_unit)
        and policy.complexity_cost_per_unit >= 0.0
        and _finite(policy.minimum_train_objective)
        and _finite(policy.minimum_holdout_information_bits)
        and policy.minimum_holdout_information_bits >= 0.0
        and _finite(policy.significance_alpha)
        and 0.0 < policy.significance_alpha <= HARD_MAX_ALPHA
        and type(policy.permutation_count) is int
        and HARD_MIN_PERMUTATIONS <= policy.permutation_count <= _MAX_PERMUTATIONS
        and policy.permutation_count >= ceil(1.0 / policy.significance_alpha) - 1
        and type(policy.bootstrap_replicates) is int
        and HARD_MIN_BOOTSTRAPS <= policy.bootstrap_replicates <= _MAX_BOOTSTRAPS
        and _finite(policy.minimum_stability)
        and HARD_MIN_STABILITY <= policy.minimum_stability <= 1.0
        and type(policy.determinism_checks) is int
        and 1 <= policy.determinism_checks <= _MAX_DETERMINISM_CHECKS
        and type(policy.max_catalog_size) is int
        and 1 <= policy.max_catalog_size <= _MAX_CATALOG_SIZE
        and type(policy.random_seed) is str
        and bool(policy.random_seed)
        and len(policy.random_seed) <= _MAX_POLICY_TEXT_BYTES
        and len(policy.random_seed.encode("utf-8")) <= _MAX_POLICY_TEXT_BYTES
    )
    logger.debug("_valid_policy exit valid=%s", result)
    return result


def _valid_not_found(report: ObserverDiscoveryReport) -> bool:
    """Recompute whether a complete non-FOUND report actually failed policy."""
    logger.debug("_valid_not_found entry")
    if report.winner is not None or not report.obstructions:
        return False
    if type(report.policy) is not DiscoveryPolicyReceipt:
        return False
    if not _finite(report.train_best_objective):
        return False
    if report.holdout_information_bits is None:
        result = (
            not report.baselines
            and report.observer_gap_bits is None
            and report.calibration is None
            and report.stability is None
            and report.train_best_objective <= report.policy.minimum_train_objective
            and any(row.reason == "train-threshold" for row in report.obstructions)
        )
        logger.debug("_valid_not_found exit train_only=%s", result)
        return result
    if (
        not _finite(report.holdout_information_bits)
        or not report.baselines
        or not _finite(report.observer_gap_bits)
        or type(report.calibration) is not PermutationCalibration
        or type(report.stability) is not BootstrapStability
        or report.calibration.permutations != report.policy.permutation_count
        or report.stability.replicates != report.policy.bootstrap_replicates
        or report.calibration.observed_winner_information_bits
        != report.holdout_information_bits
        or report.observer_gap_bits
        != report.holdout_information_bits
        - max(row.information_bits for row in report.baselines)
        or report.train_best_objective <= report.policy.minimum_train_objective
    ):
        return False
    result = (
        report.holdout_information_bits <= report.policy.minimum_holdout_information_bits
        or report.observer_gap_bits <= 0.0
        or report.calibration.add_one_p_value > report.policy.significance_alpha
        or report.stability.fraction < report.policy.minimum_stability
    )
    logger.debug("_valid_not_found exit complete=%s", result)
    return result


def _valid_baseline(row: BaselineComparison) -> bool:
    logger.debug("_valid_baseline entry")
    result = (
        _bounded_report_text(row.name)
        and _bounded_report_text(row.observer_class)
        and _hex_digest(row.fingerprint)
        and _finite(row.information_bits)
        and row.information_bits >= 0.0
        and _bounded_report_text(row.boundary)
    )
    logger.debug("_valid_baseline exit valid=%s", result)
    return result


def _valid_calibration(row: PermutationCalibration) -> bool:
    logger.debug("_valid_calibration entry")
    maxima_valid = (
        type(row.permutations) is int
        and HARD_MIN_PERMUTATIONS <= row.permutations <= _MAX_PERMUTATIONS
        and type(row.null_maxima_bits) is tuple
        and len(row.null_maxima_bits) == row.permutations
        and all(_finite(value) and value >= 0.0 for value in row.null_maxima_bits)
    )
    expected_exceedances = (
        sum(value >= row.observed_winner_information_bits for value in row.null_maxima_bits)
        if maxima_valid and _finite(row.observed_winner_information_bits)
        else -1
    )
    result = (
        type(row.exceedances) is int
        and row.exceedances == expected_exceedances
        and _finite(row.observed_winner_information_bits)
        and row.observed_winner_information_bits >= 0.0
        and _finite(row.add_one_p_value)
        and row.add_one_p_value == (row.exceedances + 1) / (row.permutations + 1)
        and maxima_valid
    )
    logger.debug("_valid_calibration exit valid=%s", result)
    return result


def _valid_stability(row: BootstrapStability) -> bool:
    logger.debug("_valid_stability entry")
    result = (
        type(row.replicates) is int
        and row.replicates >= HARD_MIN_BOOTSTRAPS
        and type(row.winner_matches) is int
        and 0 <= row.winner_matches <= row.replicates
        and _finite(row.fraction)
        and row.fraction == row.winner_matches / row.replicates
    )
    logger.debug("_valid_stability exit valid=%s", result)
    return result


def _valid_obstruction(row: DiscoveryObstruction) -> bool:
    logger.debug("_valid_obstruction entry")
    result = (
        _bounded_report_text(row.reason)
        and _bounded_report_text(row.detail)
    )
    logger.debug("_valid_obstruction exit valid=%s", result)
    return result


def _bounded_report_text(value: object) -> bool:
    logger.debug("_bounded_report_text entry type=%s", type(value).__name__)
    result = (
        type(value) is str
        and bool(value)
        and len(value) <= _MAX_REPORT_TEXT_BYTES
        and len(value.encode("utf-8")) <= _MAX_REPORT_TEXT_BYTES
    )
    logger.debug("_bounded_report_text exit valid=%s", result)
    return result
