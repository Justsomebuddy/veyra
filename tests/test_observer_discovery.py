from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from math import inf, nan
from os import urandom

import pytest

from src.core.observer_discovery import (
    BLOCKED,
    FOUND,
    NOT_FOUND_WITHIN_BUDGET,
    discover_observer,
)
from src.core.observer_discovery_types import (
    DiscoveryConfig,
    DiscoveryObstruction,
    DiscoveryRow,
    DiscoverySplit,
)
from src.core.observer_discovery_protocol import enumerate_observer_terms_bounded
from src.core.observer_discovery_protocol import DiscoveryProtocolError
from src.core.observer_discovery_validation import (
    bind_discovery_report,
    bind_discovery_train_evaluation,
    validate_discovery_report,
)
from src.core.observer_synthesis import canonical_term, enumerate_observer_terms, observer_fingerprint
from src.core.observer_synthesis_types import (
    NamedBaseline,
    ObserverGrammar,
    ObserverPrimitive,
    ObserverTerm,
)


def first_bit(value: object) -> int:
    return value[0]  # type: ignore[index]


def parity(value: object) -> int:
    return value[0] ^ value[1]  # type: ignore[index]


def constant_zero(_value: object) -> int:
    return 0


def fail(_value: object) -> object:
    raise RuntimeError("deliberate")


def noncanonical(_value: object) -> object:
    return {"not": "canonical"}


def nonfinite(_value: object) -> float:
    return nan


def random_bit(_value: object) -> int:
    return urandom(8)[0]


def _term(name: str) -> ObserverTerm:
    return ObserverTerm("apply", "scalar", name, (ObserverTerm("input", "input"),))


def _grammar(*extra: ObserverPrimitive) -> ObserverGrammar:
    primitives = (
        ObserverPrimitive("first", "input", "scalar", 1, first_bit, "test:first:v1"),
        ObserverPrimitive("parity", "input", "scalar", 1, parity, "test:parity:v1"),
        ObserverPrimitive("constant", "input", "scalar", 1, constant_zero, "test:constant:v1"),
    ) + extra
    return ObserverGrammar("test-discovery", "input", ("scalar",), primitives, 1, 1)


def _ordered_pair(left: ObserverTerm, right: ObserverTerm) -> ObserverTerm:
    children = tuple(sorted((left, right), key=canonical_term))
    return ObserverTerm("pair", "pair", children=children)


def _pair_grammar() -> ObserverGrammar:
    base = _grammar()
    return ObserverGrammar("test-pair-discovery", "input", ("pair",), base.primitives, 2, 3)


def _baseline() -> tuple[NamedBaseline, ...]:
    return (NamedBaseline("constant", "constant-observers", _term("constant"), "declared test baseline"),)


def _config(**changes: object) -> DiscoveryConfig:
    values: dict[str, object] = {
        "complexity_cost_per_unit": 0.01,
        "minimum_train_objective": 0.0,
        "minimum_holdout_information_bits": 0.0,
        "significance_alpha": 0.05,
        "permutation_count": 39,
        "bootstrap_replicates": 16,
        "minimum_stability": 0.5,
        "determinism_checks": 2,
        "max_catalog_size": 32,
        "random_seed": "focused-test-seed",
    }
    values.update(changes)
    return DiscoveryConfig(**values)  # type: ignore[arg-type]


def _rows(split_name: str, target_mode: str = "parity", count: int = 24) -> tuple[DiscoveryRow, ...]:
    result = []
    for index in range(count):
        bits = ((index // 2) % 2, index % 2)
        target = bits[0] ^ bits[1] if target_mode == "parity" else bits[0]
        result.append(
            DiscoveryRow(
                row_id=f"{split_name}-row-{index}",
                source_id=f"{split_name}-source-{index}",
                content_id=f"{split_name}-content-{index}",
                group_id=f"{split_name}-group-{index}",
                features=bits,
                target=target,
            ),
        )
    return tuple(result)


def _split(holdout_mode: str = "parity") -> DiscoverySplit:
    return DiscoverySplit(_rows("train"), _rows("holdout", holdout_mode))


def _replace_row(row: DiscoveryRow, **changes: object) -> DiscoveryRow:
    values = {
        "row_id": row.row_id,
        "source_id": row.source_id,
        "content_id": row.content_id,
        "group_id": row.group_id,
        "features": row.features,
        "target": row.target,
    }
    values.update(changes)
    return DiscoveryRow(**values)  # type: ignore[arg-type]


def test_finds_parity_reproducibly_with_locked_winner_and_nonzero_add_one_p() -> None:
    first = discover_observer(_grammar(), _split(), _baseline(), _config())
    second = discover_observer(_grammar(), _split(), _baseline(), _config())

    assert first == second
    assert first.status == FOUND
    assert first.winner is not None
    assert first.policy is not None
    assert first.policy.complexity_cost_per_unit == _config().complexity_cost_per_unit
    assert first.winner.term == _term("parity")
    assert first.winner.information_bits == pytest.approx(1.0)
    assert first.holdout_information_bits == pytest.approx(1.0)
    assert first.observer_gap_bits == pytest.approx(1.0)
    assert first.calibration is not None
    assert first.calibration.add_one_p_value > 0.0
    assert first.calibration.add_one_p_value <= 0.05
    assert len(first.calibration.null_maxima_bits) == 39
    assert first.stability is not None and first.stability.fraction >= 0.5
    assert first.catalog_size == 3
    assert all(len(value) == 64 for value in first.digests.__dict__.values())
    assert "not causality" in first.boundary
    assert "not process-level isolation" in first.boundary
    assert "trusted caller declarations" in first.boundary


def test_records_are_frozen_and_repeated_categories_are_allowed_across_splits() -> None:
    row = _rows("one", count=2)[0]
    with pytest.raises(FrozenInstanceError):
        row.target = 7  # type: ignore[misc]

    report = discover_observer(_grammar(), _split(), _baseline(), _config())
    assert report.status == FOUND


def test_protocol_data_catalog_and_result_digests_are_separate_and_bound() -> None:
    original = discover_observer(_grammar(), _split(), _baseline(), _config())
    config_changed = discover_observer(
        _grammar(), _split(), _baseline(), _config(complexity_cost_per_unit=0.02),
    )
    holdout = list(_split().holdout)
    holdout[0] = _replace_row(holdout[0], target=not bool(holdout[0].target))
    data_changed = discover_observer(
        _grammar(), DiscoverySplit(_split().train, tuple(holdout)), _baseline(), _config(),
    )

    assert len(set(original.digests.__dict__.values())) == 9
    assert config_changed.digests.protocol != original.digests.protocol
    assert config_changed.digests.policy != original.digests.policy
    assert config_changed.digests.protocol_material == original.digests.protocol_material
    assert config_changed.digests.train_data == original.digests.train_data
    assert data_changed.digests.holdout_data != original.digests.holdout_data
    assert data_changed.digests.result != original.digests.result


def test_holdout_calibration_uses_frozen_train_winner_not_holdout_best() -> None:
    report = discover_observer(_grammar(), _split("first"), _baseline(), _config())

    assert report.status == NOT_FOUND_WITHIN_BUDGET
    assert report.winner is None
    assert report.calibration is not None
    assert report.holdout_information_bits == pytest.approx(0.0)
    assert report.calibration.observed_winner_information_bits == pytest.approx(0.0)
    assert report.calibration.add_one_p_value == pytest.approx(1.0)
    assert max(report.calibration.null_maxima_bits) > 0.0
    assert "holdout-threshold" in {row.reason for row in report.obstructions}
    assert validate_discovery_report(report)

    forged = replace(
        report,
        observer_gap_bits=0.5,
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(forged))


def test_null_train_data_returns_not_found_without_partial_winner() -> None:
    train = tuple(_replace_row(row, target=0) for row in _split().train)
    report = discover_observer(
        _grammar(), DiscoverySplit(train, _split().holdout), _baseline(), _config(),
    )

    assert report.status == NOT_FOUND_WITHIN_BUDGET
    assert report.winner is None
    assert report.calibration is None
    assert report.obstructions[0].reason == "train-threshold"
    assert report.policy is not None
    assert validate_discovery_report(report)
    assert validate_discovery_report(
        report, expected_train_evaluation=report.digests.train_evaluation,
    )
    assert not validate_discovery_report(report, expected_train_evaluation="0" * 64)


@pytest.mark.parametrize("identity", ["row_id", "source_id", "content_id", "group_id"])
def test_cross_split_identity_leakage_blocks_without_partial_winner(identity: str) -> None:
    split = _split()
    holdout = list(split.holdout)
    holdout[0] = _replace_row(holdout[0], **{identity: getattr(split.train[0], identity)})

    report = discover_observer(
        _grammar(), DiscoverySplit(split.train, tuple(holdout)), _baseline(), _config(),
    )

    assert report.status == BLOCKED
    assert report.winner is None
    assert report.calibration is None
    assert report.obstructions[0].reason == "split-leakage"


@pytest.mark.parametrize("bad_features", [[0, 1], nan, inf, -inf])
def test_noncanonical_or_nonfinite_input_blocks(bad_features: object) -> None:
    split = _split()
    train = list(split.train)
    train[0] = _replace_row(train[0], features=bad_features)
    report = discover_observer(
        _grammar(), DiscoverySplit(tuple(train), split.holdout), _baseline(), _config(),
    )
    assert report.status == BLOCKED
    assert report.winner is None
    assert report.obstructions[0].reason == "invalid-data"


def test_one_target_per_group_is_required() -> None:
    split = _split()
    train = list(split.train)
    train[1] = _replace_row(train[1], group_id=train[0].group_id)
    report = discover_observer(
        _grammar(), DiscoverySplit(tuple(train), split.holdout), _baseline(), _config(),
    )
    assert report.status == BLOCKED
    assert report.obstructions[0].detail == "train-one-target-per-group-required"


def test_missing_baseline_catalog_cutoff_and_insufficient_calibration_block() -> None:
    missing = discover_observer(_grammar(), _split(), (), _config())
    cutoff = discover_observer(
        _grammar(), _split(), _baseline(), _config(max_catalog_size=2),
    )
    calibration = discover_observer(
        _grammar(), _split(), _baseline(), _config(permutation_count=18),
    )

    assert (missing.status, missing.obstructions[0].reason) == (BLOCKED, "invalid-baseline")
    assert (cutoff.status, cutoff.obstructions[0].reason) == (BLOCKED, "catalog-cutoff")
    assert (calibration.status, calibration.obstructions[0].reason) == (
        BLOCKED,
        "insufficient-calibration",
    )
    assert missing.winner is cutoff.winner is calibration.winner is None
    assert all(validate_discovery_report(report) for report in (missing, cutoff, calibration))


def test_hard_statistical_floors_cannot_be_disabled() -> None:
    weak_alpha = discover_observer(
        _grammar(), _split(), _baseline(), _config(significance_alpha=0.99),
    )
    weak_stability = discover_observer(
        _grammar(), _split(), _baseline(), _config(minimum_stability=0.0),
    )
    weak_bootstrap = discover_observer(
        _grammar(), _split(), _baseline(), _config(bootstrap_replicates=1),
    )
    assert {weak_alpha.status, weak_stability.status, weak_bootstrap.status} == {BLOCKED}
    assert [report.obstructions[0].reason for report in (weak_alpha, weak_stability, weak_bootstrap)] == [
        "invalid-config", "invalid-config", "insufficient-calibration",
    ]


def test_grammar_and_statistical_work_are_preflight_bounded() -> None:
    deep = ObserverGrammar(
        "too-deep", "input", ("scalar",), _grammar().primitives, 3, 1,
    )
    grammar_report = discover_observer(deep, _split(), _baseline(), _config())
    work_report = discover_observer(
        _grammar(),
        DiscoverySplit(_rows("large-train", count=8192), _rows("large-holdout", count=8192)),
        _baseline(),
        _config(permutation_count=4095, bootstrap_replicates=1024),
    )
    assert (grammar_report.status, grammar_report.obstructions[0].reason) == (
        BLOCKED, "resource-limit",
    )
    assert (work_report.status, work_report.obstructions[0].reason) == (
        BLOCKED, "resource-limit",
    )


@pytest.mark.parametrize("identity", ["source_id", "content_id"])
def test_lineage_cannot_cross_exchangeability_groups(identity: str) -> None:
    split = _split()
    train = list(split.train)
    train[1] = _replace_row(train[1], **{identity: getattr(train[0], identity)})
    report = discover_observer(
        _grammar(), DiscoverySplit(tuple(train), split.holdout), _baseline(), _config(),
    )
    assert (report.status, report.obstructions[0].detail) == (
        BLOCKED, "train-lineage-crosses-groups",
    )


def test_unequal_exchangeability_group_sizes_block() -> None:
    split = _split()
    train = list(split.train)
    train[1] = _replace_row(train[1], group_id=train[0].group_id, target=train[0].target)
    report = discover_observer(
        _grammar(), DiscoverySplit(tuple(train), split.holdout), _baseline(), _config(),
    )
    assert (report.status, report.obstructions[0].detail) == (
        BLOCKED, "train-unequal-group-sizes",
    )


def test_report_validator_rejects_status_and_digest_transplants() -> None:
    report = discover_observer(_grammar(), _split(), _baseline(), _config())
    assert validate_discovery_report(report)
    assert not validate_discovery_report(replace(report, status=BLOCKED))
    assert not validate_discovery_report(
        replace(report, digests=replace(report.digests, result="0" * 64)),
    )
    assert report.calibration is not None
    forged = replace(
        report,
        calibration=replace(report.calibration, add_one_p_value=1.0),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(forged))
    assert report.winner is not None
    bad_winner = replace(
        report,
        winner=replace(report.winner, fingerprint="0" * 64),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_winner))
    forged_complexity = replace(
        report,
        winner=replace(
            report.winner,
            complexity=0,
            objective=report.winner.information_bits,
        ),
        train_best_objective=report.winner.information_bits,
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(forged_complexity))
    forged_not_found = replace(
        report,
        status=NOT_FOUND_WITHIN_BUDGET,
        winner=None,
        obstructions=(DiscoveryObstruction("forged", "no threshold failed"),),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(forged_not_found))
    forged_train_not_found = replace(
        report,
        status=NOT_FOUND_WITHIN_BUDGET,
        winner=None,
        train_best_objective=0.0,
        holdout_information_bits=None,
        baselines=(),
        observer_gap_bits=None,
        calibration=None,
        stability=None,
        obstructions=(DiscoveryObstruction("train-threshold", "forged"),),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(forged_train_not_found))
    bad_catalog_size = replace(
        report,
        catalog_size=0,
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_catalog_size))


def test_report_validator_recomputes_gap_and_published_policy_decisions() -> None:
    report = discover_observer(_grammar(), _split(), _baseline(), _config())
    assert report.status == FOUND
    assert report.policy is not None

    bad_gap = replace(
        report,
        observer_gap_bits=0.5,
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_gap))

    bad_cost = replace(
        report,
        policy=replace(report.policy, complexity_cost_per_unit=0.02),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_cost))

    bad_alpha = replace(
        report,
        policy=replace(report.policy, significance_alpha=0.01),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_alpha))

    bad_seed = replace(
        report,
        policy=replace(report.policy, random_seed="rebound-with-old-protocol"),
        digests=replace(report.digests, result=""),
    )
    assert not validate_discovery_report(bind_discovery_report(bad_seed))


def test_report_validator_rejects_cyclic_observer_term_without_recursing() -> None:
    report = discover_observer(_grammar(), _split(), _baseline(), _config())
    assert report.winner is not None
    cyclic = ObserverTerm("apply", "scalar", "parity")
    object.__setattr__(cyclic, "children", (cyclic,))
    forged = replace(report, winner=replace(report.winner, term=cyclic))

    assert not validate_discovery_report(forged)


def test_report_validator_rejects_typed_term_outside_grammar_depth() -> None:
    baseline_term = _ordered_pair(_term("constant"), _term("constant"))
    baselines = (NamedBaseline("constant-pair", "pair-baseline", baseline_term, "test"),)
    report = discover_observer(_pair_grammar(), _split(), baselines, _config())
    assert report.status == FOUND
    assert report.winner is not None

    seed = ObserverTerm("input", "input")
    too_deep = _ordered_pair(_ordered_pair(_ordered_pair(seed, seed), seed), seed)
    objective = report.winner.information_bits - 0.01 * 3
    forged = replace(
        report,
        winner=replace(
            report.winner,
            term=too_deep,
            fingerprint=observer_fingerprint(too_deep),
            complexity=3,
            objective=objective,
        ),
        train_best_objective=objective,
        digests=replace(report.digests, result=""),
    )
    forged = replace(
        forged,
        digests=bind_discovery_train_evaluation(forged.digests, objective),
    )
    assert not validate_discovery_report(bind_discovery_report(forged))


def test_logs_do_not_expose_record_lineage_identifiers(caplog: pytest.LogCaptureFixture) -> None:
    marker = "PRIVATE-ROW-LINEAGE-MARKER"
    split = _split()
    train = list(split.train)
    train[0] = _replace_row(
        train[0], row_id=marker, source_id=marker, content_id=marker,
    )
    with caplog.at_level("DEBUG"):
        discover_observer(_grammar(), DiscoverySplit(tuple(train), split.holdout), _baseline(), _config())
    assert marker not in caplog.text


@pytest.mark.parametrize(
    ("name", "evaluator", "expected"),
    [
        ("failure", fail, "evaluator-failure"),
        ("noncanonical", noncanonical, "evaluator-failure"),
        ("nonfinite", nonfinite, "noncanonical-evaluator-result"),
    ],
)
def test_evaluator_failure_and_noncanonical_result_block(
    name: str, evaluator: object, expected: str,
) -> None:
    primitive = ObserverPrimitive(
        name, "input", "scalar", 1, evaluator, f"test:{name}:v1",  # type: ignore[arg-type]
    )
    report = discover_observer(_grammar(primitive), _split(), _baseline(), _config())
    assert report.status == BLOCKED
    assert report.winner is None
    assert report.obstructions[0].reason == expected


def test_nondeterministic_evaluator_blocks() -> None:
    primitive = ObserverPrimitive("random", "input", "scalar", 1, random_bit, "test:random:v1")
    report = discover_observer(_grammar(primitive), _split(), _baseline(), _config())
    assert report.status == BLOCKED
    assert report.winner is None
    assert report.obstructions[0].reason == "nondeterministic-evaluator"


def test_mutable_evaluator_closure_is_rejected_before_callbacks() -> None:
    state = [0]

    def mutate(_value: object) -> int:
        state[0] += 1
        return 0

    primitive = ObserverPrimitive("mutate", "input", "scalar", 1, mutate, "test:mutate:v1")
    report = discover_observer(_grammar(primitive), _split(), _baseline(), _config())
    assert report.status == BLOCKED
    assert report.winner is None
    assert report.obstructions[0].reason == "untrusted-evaluator-state"


def test_oversized_evaluator_semantic_identity_blocks_before_hashing() -> None:
    primitive = ObserverPrimitive(
        "large-semantic-id", "input", "scalar", 1, constant_zero, "x" * 513,
    )
    report = discover_observer(_grammar(primitive), _split(), _baseline(), _config())
    assert (report.status, report.obstructions[0].reason) == (BLOCKED, "invalid-grammar")


def test_bounded_enumerator_matches_r5_order_for_the_focused_grammar() -> None:
    assert enumerate_observer_terms_bounded(_grammar(), 32) == enumerate_observer_terms(_grammar())


def test_streamed_catalog_constructor_stops_at_construction_limit() -> None:
    primitives = tuple(
        ObserverPrimitive(f"identity-{index}", "input", "input", 1, first_bit, f"identity-{index}:v1")
        for index in range(8)
    )
    grammar = ObserverGrammar("construction-cutoff", "input", ("input",), primitives, 2, 8)
    with pytest.raises(DiscoveryProtocolError, match="catalog-cutoff:construction-term-limit"):
        enumerate_observer_terms_bounded(grammar, 2)


def test_oversized_observer_output_blocks_before_retention() -> None:
    def oversized(_value: object) -> tuple[int, ...]:
        return (0,) * 4097

    primitive = ObserverPrimitive("oversized", "input", "scalar", 1, oversized, "test:oversized:v1")
    report = discover_observer(_grammar(primitive), _split(), _baseline(), _config())
    assert (report.status, report.obstructions[0].reason) == (BLOCKED, "resource-limit")


def test_snapshot_blocks_oversized_rows_before_copying_them() -> None:
    row = _rows("oversized", count=1)[0]
    split = DiscoverySplit((row,) * 8193, _rows("holdout"))
    report = discover_observer(_grammar(), split, _baseline(), _config())
    assert (report.status, report.obstructions[0].reason) == (BLOCKED, "resource-limit")


def test_snapshot_counts_shared_term_expansion_before_recursive_copy() -> None:
    shared = ObserverTerm("input", "input")
    for _ in range(16):
        shared = ObserverTerm("pair", "pair", children=(shared, shared))
    baseline = (NamedBaseline("shared", "hostile-dag", shared, "test boundary"),)
    report = discover_observer(_grammar(), _split(), baseline, _config())
    assert (report.status, report.obstructions[0].reason) == (BLOCKED, "resource-limit")
