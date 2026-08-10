from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.observer_discovery_confirmation as confirmation_module
from src.core.observer_discovery import FOUND, discover_observer
from src.core.observer_discovery_confirmation import (
    BLOCKED,
    NOT_REPLICATED,
    REPLICATED,
    confirm_observer_discovery,
)
from src.core.observer_discovery_confirmation_types import (
    DiscoveryConfirmationConfig,
    DiscoveryConfirmationDigests,
    FixedFamilyCalibration,
)
from src.core.observer_discovery_confirmation_validation import (
    bind_confirmation_report,
    confirmation_protocol_digest,
    validate_confirmation_report,
)
from src.core.observer_discovery_types import DiscoveryConfig, DiscoveryRow, DiscoverySplit
from src.core.observer_discovery_validation import bind_discovery_report
from src.core.observer_synthesis_types import NamedBaseline, ObserverGrammar, ObserverPrimitive, ObserverTerm


def first(value: object) -> int:
    return value[0]  # type: ignore[index]


def parity(value: object) -> int:
    return value[0] ^ value[1]  # type: ignore[index]


def zero(_value: object) -> int:
    return 0


def parity_after_code_mutation(value: object) -> int:
    return value[1] ^ value[0]  # type: ignore[index]


def mutate_code_on_marked_test(value: object) -> int:
    if len(value) == 3:  # type: ignore[arg-type]
        mutate_code_on_marked_test.__code__ = parity_after_code_mutation.__code__
    return value[0] ^ value[1]  # type: ignore[index]


def term(name: str) -> ObserverTerm:
    return ObserverTerm("apply", "scalar", name, (ObserverTerm("input", "input"),))


def grammar() -> ObserverGrammar:
    return ObserverGrammar(
        "confirmation-test",
        "input",
        ("scalar",),
        (
            ObserverPrimitive("first", "input", "scalar", 1, first, "confirm:first:v1"),
            ObserverPrimitive("parity", "input", "scalar", 1, parity, "confirm:parity:v1"),
            ObserverPrimitive("zero", "input", "scalar", 1, zero, "confirm:zero:v1"),
        ),
        1,
        1,
    )


def baseline() -> tuple[NamedBaseline, ...]:
    return (NamedBaseline("zero", "constant", term("zero"), "fixed baseline"),)


def rows(name: str, mode: str = "parity") -> tuple[DiscoveryRow, ...]:
    result = []
    for index in range(24):
        bits = ((index // 2) % 2, index % 2)
        target = bits[0] ^ bits[1] if mode == "parity" else bits[0]
        result.append(
            DiscoveryRow(
                f"{name}-row-{index}",
                f"{name}-source-{index}",
                f"{name}-content-{index}",
                f"{name}-group-{index}",
                bits,
                target,
            )
        )
    return tuple(result)


def discovery_config() -> DiscoveryConfig:
    return DiscoveryConfig(permutation_count=39, bootstrap_replicates=16, max_catalog_size=32)


def confirmation_config() -> DiscoveryConfirmationConfig:
    return DiscoveryConfirmationConfig(permutation_count=39)


def parent():
    split = DiscoverySplit(rows("train"), rows("holdout"))
    report = discover_observer(grammar(), split, baseline(), discovery_config())
    assert report.status == FOUND
    return report, split


def rebind(report):
    return bind_confirmation_report(
        replace(report, digests=replace(report.digests, result="")),
    )


def test_fixed_winner_replicates_deterministically_and_validates() -> None:
    report, split = parent()
    first_report = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    second_report = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    assert first_report == second_report
    assert first_report.status == REPLICATED
    assert first_report.winner_fingerprint == report.winner.fingerprint
    assert first_report.observer_gap_bits == 1.0
    assert first_report.calibration is not None
    assert 0.0 < first_report.calibration.add_one_p_value <= 0.05
    assert validate_confirmation_report(first_report, expected_parent_result=report.digests.result)
    assert "one-shot enforced" in first_report.boundary


def test_test_failure_never_substitutes_an_alternate_catalog_observer() -> None:
    report, split = parent()
    result = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test", "first"),
        confirmation_config(),
    )
    assert result.status == NOT_REPLICATED
    assert result.winner_fingerprint == report.winner.fingerprint
    assert result.test_information_bits == 0.0
    assert result.obstructions
    assert validate_confirmation_report(result)


def test_forged_parent_and_three_way_lineage_overlap_block_before_confirmation() -> None:
    report, split = parent()
    forged = replace(report, status="BLOCKED")
    forged_result = confirm_observer_discovery(
        forged,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    test = list(rows("test"))
    test[0] = replace(test[0], content_id=split.train[0].content_id)
    overlap = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        tuple(test),
        confirmation_config(),
    )
    assert forged_result.status == BLOCKED
    assert overlap.status == BLOCKED
    assert overlap.obstructions[0].reason == "split-leakage"
    assert forged_result.winner_fingerprint is overlap.winner_fingerprint is None
    assert validate_confirmation_report(forged_result)
    assert validate_confirmation_report(overlap)


@pytest.mark.parametrize("identity", ("row_id", "source_id", "content_id", "group_id"))
def test_every_three_way_identity_overlap_blocks(identity: str) -> None:
    report, split = parent()
    test = list(rows("test"))
    test[0] = replace(test[0], **{identity: getattr(split.holdout[0], identity)})

    result = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        tuple(test),
        confirmation_config(),
    )

    assert (result.status, result.obstructions[0].reason) == (BLOCKED, "split-leakage")
    assert validate_confirmation_report(result)


def test_parent_protocol_mutation_and_weak_calibration_block() -> None:
    report, split = parent()
    changed = DiscoveryConfig(
        complexity_cost_per_unit=0.02,
        permutation_count=39,
        bootstrap_replicates=16,
        max_catalog_size=32,
    )
    mismatch = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        changed,
        rows("test"),
        confirmation_config(),
    )
    weak = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        DiscoveryConfirmationConfig(permutation_count=18),
    )
    assert (mismatch.status, mismatch.obstructions[0].reason) == (BLOCKED, "parent-replay-mismatch")
    assert (weak.status, weak.obstructions[0].reason) == (BLOCKED, "insufficient-calibration")
    assert validate_confirmation_report(weak, parent_report=report)


def test_test_evaluator_code_mutation_blocks_after_repeatable_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutate_code_on_marked_test,
        "__code__",
        mutate_code_on_marked_test.__code__,
    )
    mutating_grammar = ObserverGrammar(
        "confirmation-self-mutation",
        "input",
        ("scalar",),
        (
            ObserverPrimitive(
                "parity",
                "input",
                "scalar",
                1,
                mutate_code_on_marked_test,
                "confirm:mutating-parity:v1",
            ),
            ObserverPrimitive("zero", "input", "scalar", 1, zero, "confirm:zero:v1"),
        ),
        1,
        1,
    )
    split = DiscoverySplit(rows("mutating-train"), rows("mutating-holdout"))
    report = discover_observer(mutating_grammar, split, baseline(), discovery_config())
    marked_test = tuple(replace(row, features=(*row.features, 7)) for row in rows("mutating-test"))

    result = confirm_observer_discovery(
        report,
        mutating_grammar,
        split,
        baseline(),
        discovery_config(),
        marked_test,
        confirmation_config(),
    )

    assert (result.status, result.obstructions[0].reason) == (BLOCKED, "protocol-mutation")
    assert validate_confirmation_report(result, expected_parent_result=report.digests.result)


def test_caller_parent_mutation_after_replay_cannot_retarget_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report, split = parent()
    original_fingerprint = report.winner.fingerprint
    original_evaluate = confirmation_module._evaluate_catalog

    def mutate_caller_parent(*args, **kwargs):
        object.__setattr__(
            report,
            "winner",
            replace(report.winner, fingerprint="f" * 64),
        )
        return original_evaluate(*args, **kwargs)

    monkeypatch.setattr(confirmation_module, "_evaluate_catalog", mutate_caller_parent)
    result = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )

    assert result.status == REPLICATED
    assert result.winner_fingerprint == original_fingerprint


def test_config_must_be_exact_and_work_precharge_uses_effective_checks() -> None:
    report, split = parent()

    class DuckConfig:
        minimum_test_information_bits = 0.0
        minimum_test_gap_bits = 0.0
        significance_alpha = 0.05
        permutation_count = 39
        determinism_checks = 2
        max_test_rows = 8192
        max_work_items = 5_000_000
        random_seed = "duck"

    duck = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        DuckConfig(),  # type: ignore[arg-type]
    )
    undercharged = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        DiscoveryConfirmationConfig(
            permutation_count=39,
            determinism_checks=1,
            max_work_items=1940,
        ),
    )
    oversized_seed = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        DiscoveryConfirmationConfig(
            permutation_count=39,
            random_seed="x" * 513,
        ),
    )
    assert (duck.status, duck.obstructions[0].detail) == (BLOCKED, "exact-config-required")
    assert (undercharged.status, undercharged.obstructions[0].detail) == (
        BLOCKED,
        "confirmation-work",
    )
    assert (oversized_seed.status, oversized_seed.obstructions[0].detail) == (
        BLOCKED,
        "seed",
    )


def test_self_consistent_parent_forgery_requires_exact_replay_and_digest_pins_hold() -> None:
    report, split = parent()
    forged = replace(
        report, boundary="self-consistent but not replay-identical", digests=replace(report.digests, result="")
    )
    forged = bind_discovery_report(forged)
    result = confirm_observer_discovery(
        forged,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    assert (result.status, result.obstructions[0].reason) == (BLOCKED, "parent-replay-mismatch")

    valid = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    assert not validate_confirmation_report(replace(valid, digests=replace(valid.digests, result="0" * 64)))
    assert not validate_confirmation_report(valid, expected_parent_result="0" * 64)
    assert not validate_confirmation_report(valid, expected_test_data="0" * 64)


def test_malformed_exact_parent_graph_fails_closed() -> None:
    report, split = parent()
    malformed = replace(report, digests=object())  # type: ignore[arg-type]

    result = confirm_observer_discovery(
        malformed,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )

    assert result.status == BLOCKED
    assert result.digests.parent_result == ""
    assert validate_confirmation_report(result)


def test_validator_rejects_semantic_and_nested_record_drift() -> None:
    report, split = parent()
    replicated = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    rejected = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test", "first"),
        confirmation_config(),
    )
    assert rejected.status == NOT_REPLICATED
    assert replicated.calibration is not None
    assert replicated.config is not None
    assert replicated.test_information_bits is not None

    semantic_attacks = (
        replace(replicated, boundary="stronger forged boundary"),
        replace(
            replicated,
            baselines=(replace(replicated.baselines[0], fingerprint="g" * 64),),
        ),
        replace(
            replicated,
            baselines=(replace(replicated.baselines[0], information_bits=-1.0),),
            observer_gap_bits=replicated.test_information_bits + 1.0,
        ),
        replace(
            rejected,
            obstructions=(replace(rejected.obstructions[0], detail="forged"),) + rejected.obstructions[1:],
        ),
        replace(
            replicated,
            calibration=FixedFamilyCalibration(
                replicated.calibration.permutations,
                replicated.calibration.exceedances,
                replicated.calibration.observed_winner_information_bits,
                replicated.calibration.add_one_p_value,
                (replicated.calibration.observed_winner_information_bits + 1.0,) * replicated.calibration.permutations,
            ),
        ),
    )
    assert all(not validate_confirmation_report(rebind(attack)) for attack in semantic_attacks)
    raw_digest_attack = replace(
        replicated,
        digests=DiscoveryConfirmationDigests(
            replicated.digests.parent_result,
            replicated.digests.protocol,
            replicated.digests.test_data,
            "",
        ),
    )
    assert not validate_confirmation_report(raw_digest_attack)
    extended_digests = replace(replicated.digests)
    object.__setattr__(extended_digests, "unexpected", "x")
    assert not validate_confirmation_report(replace(replicated, digests=extended_digests))
    oversized_nulls = replace(
        replicated,
        calibration=replace(
            replicated.calibration,
            null_maxima_bits=(0.0,) * 4096,
        ),
    )
    assert not validate_confirmation_report(oversized_nulls)
    list_nulls = replace(
        replicated,
        calibration=replace(
            replicated.calibration,
            null_maxima_bits=list(replicated.calibration.null_maxima_bits),  # type: ignore[arg-type]
        ),
    )
    assert not validate_confirmation_report(list_nulls)
    assert not validate_confirmation_report(
        replace(replicated, baselines=(object(),) * 4097),  # type: ignore[arg-type]
    )
    assert not validate_confirmation_report(
        replace(replicated, obstructions=(object(),) * 65),  # type: ignore[arg-type]
    )


def test_parent_report_pin_links_the_committed_winner_not_only_parent_identity() -> None:
    report, split = parent()
    replicated = confirm_observer_discovery(
        report,
        grammar(),
        split,
        baseline(),
        discovery_config(),
        rows("test"),
        confirmation_config(),
    )
    fake_winner = "f" * 64
    forged = rebind(
        replace(
            replicated,
            winner_fingerprint=fake_winner,
            digests=replace(
                replicated.digests,
                protocol=confirmation_protocol_digest(
                    replicated.digests.parent_result,
                    fake_winner,
                    replicated.config,
                ),
            ),
        ),
    )

    assert validate_confirmation_report(
        forged,
        expected_parent_result=report.digests.result,
    )
    assert not validate_confirmation_report(forged, parent_report=report)

    substituted_baseline = replace(
        replicated.baselines[0],
        name="substituted",
        observer_class="different-family",
        fingerprint="e" * 64,
        boundary="self-consistent forged baseline",
    )
    baseline_forgery = rebind(
        replace(
            replicated,
            baselines=(substituted_baseline,),
            observer_gap_bits=replicated.test_information_bits - substituted_baseline.information_bits,
        ),
    )
    assert validate_confirmation_report(baseline_forgery)
    assert not validate_confirmation_report(baseline_forgery, parent_report=report)


def test_confirmation_logs_do_not_expose_final_lineage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    report, split = parent()
    sentinel = "private-final-lineage-sentinel"
    test = list(rows("test"))
    test[0] = replace(
        test[0],
        row_id=f"{sentinel}-row",
        source_id=f"{sentinel}-source",
        content_id=f"{sentinel}-content",
        group_id=f"{sentinel}-group",
    )

    with caplog.at_level(logging.DEBUG):
        result = confirm_observer_discovery(
            report,
            grammar(),
            split,
            baseline(),
            discovery_config(),
            tuple(test),
            confirmation_config(),
        )

    assert result.status == REPLICATED
    assert sentinel not in caplog.text
