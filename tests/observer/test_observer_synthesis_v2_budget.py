"""R14.2a deterministic budget-ledger regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging

import pytest

from src.core import observer_synthesis_v2_budget as budget_module
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    MAX_CANONICAL_BYTES,
    MAX_CANDIDATES,
    MAX_EVALUATIONS,
    MAX_LEDGER_INTEGER,
    MAX_PROCESS_AS_BYTES,
    MAX_TRANSCRIPT_OUTPUT_BYTES,
    MAX_WALL_SECONDS,
    BudgetCutoffReason,
    BudgetLedger,
    BudgetLimitExceeded,
    BudgetLimits,
    BudgetValidationError,
    validate_budget_limits,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


def test_exact_frozen_default_and_maximum_contract() -> None:
    logger.info("R14.2a exact defaults test entry")
    assert DEFAULT_BUDGET_LIMITS == BudgetLimits(
        candidate_limit=2048,
        canonical_bytes_limit=8 * 1024 * 1024,
        evaluation_limit=100_000,
        transcript_output_bytes_limit=8 * 1024 * 1024,
        wall_seconds=5,
        process_as_bytes_limit=512 * 1024 * 1024,
    )
    with pytest.raises(FrozenInstanceError):
        DEFAULT_BUDGET_LIMITS.candidate_limit = 1  # type: ignore[misc]
    assert validate_budget_limits(DEFAULT_BUDGET_LIMITS) is DEFAULT_BUDGET_LIMITS
    logger.info("R14.2a exact defaults test exit")


@pytest.mark.parametrize(
    ("field", "maximum"),
    (
        ("candidate_limit", MAX_CANDIDATES),
        ("canonical_bytes_limit", MAX_CANONICAL_BYTES),
        ("evaluation_limit", MAX_EVALUATIONS),
        ("transcript_output_bytes_limit", MAX_TRANSCRIPT_OUTPUT_BYTES),
        ("wall_seconds", MAX_WALL_SECONDS),
        ("process_as_bytes_limit", MAX_PROCESS_AS_BYTES),
    ),
)
def test_every_limit_accepts_one_below_and_rejects_upward_drift(
    field: str,
    maximum: int,
) -> None:
    logger.info("R14.2a config ceiling test entry field=%s", field)
    lowered = replace(DEFAULT_BUDGET_LIMITS, **{field: maximum - 1})
    assert validate_budget_limits(lowered) is lowered
    with pytest.raises(BudgetValidationError, match="invalid-budget-limits"):
        validate_budget_limits(
            replace(DEFAULT_BUDGET_LIMITS, **{field: maximum + 1})
        )
    logger.info("R14.2a config ceiling test exit field=%s", field)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidate_limit", True),
        ("canonical_bytes_limit", 1.0),
        ("evaluation_limit", "1"),
        ("transcript_output_bytes_limit", -1),
        ("wall_seconds", False),
        ("process_as_bytes_limit", -1),
    ),
)
def test_hostile_or_negative_limit_fields_are_invalid(
    field: str,
    value: object,
) -> None:
    logger.info("R14.2a hostile config test entry field=%s", field)
    with pytest.raises(BudgetValidationError, match="invalid-budget-limits"):
        validate_budget_limits(replace(DEFAULT_BUDGET_LIMITS, **{field: value}))
    logger.info("R14.2a hostile config test exit field=%s", field)


@pytest.mark.parametrize(
    "field",
    (
        "candidate_limit",
        "canonical_bytes_limit",
        "evaluation_limit",
        "transcript_output_bytes_limit",
        "wall_seconds",
        "process_as_bytes_limit",
    ),
)
def test_zero_limit_fields_are_invalid(field: str) -> None:
    logger.info("R14.2a zero config test entry field=%s", field)
    with pytest.raises(BudgetValidationError, match="invalid-budget-limits"):
        validate_budget_limits(replace(DEFAULT_BUDGET_LIMITS, **{field: 0}))
    logger.info("R14.2a zero config test exit field=%s", field)


def test_exact_budget_type_rejects_subclass_and_arbitrary_objects() -> None:
    logger.info("R14.2a exact config type test entry")

    class ForgedBudgetLimits(BudgetLimits):
        pass

    with pytest.raises(BudgetValidationError, match="invalid-budget-limits-type"):
        validate_budget_limits(ForgedBudgetLimits())
    with pytest.raises(BudgetValidationError, match="invalid-budget-limits-type"):
        validate_budget_limits(object())
    logger.info("R14.2a exact config type test exit")


def test_candidate_and_canonical_charges_are_atomic_at_exact_caps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a candidate precharge test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 10)
    ledger = BudgetLedger()
    for _ in range(MAX_CANDIDATES - 1):
        ledger.charge_candidate(1)
    assert ledger.snapshot().candidates == MAX_CANDIDATES - 1
    assert ledger.charge_candidate(1).candidates == MAX_CANDIDATES
    with pytest.raises(BudgetLimitExceeded) as caught:
        ledger.charge_candidate(1)
    assert caught.value.reason is BudgetCutoffReason.CANDIDATES
    assert ledger.snapshot().candidates == MAX_CANDIDATES

    byte_ledger = BudgetLedger()
    byte_ledger.charge_candidate(MAX_CANONICAL_BYTES - 1)
    byte_ledger.charge_candidate(1)
    before = byte_ledger.snapshot()
    with pytest.raises(BudgetLimitExceeded) as byte_cutoff:
        byte_ledger.charge_candidate(1)
    after = byte_ledger.snapshot()
    assert byte_cutoff.value.reason is BudgetCutoffReason.CANONICAL_BYTES
    assert (after.candidates, after.canonical_bytes) == (
        before.candidates,
        before.canonical_bytes,
    )
    with pytest.raises(BudgetValidationError, match="invalid-budget-charge"):
        BudgetLedger().charge_candidate(0)
    logger.info("R14.2a candidate precharge test exit")


def test_evaluation_and_output_charges_accept_exact_cap_then_cut_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a eval/output precharge test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 20)
    evaluations = BudgetLedger()
    below = evaluations.charge_evaluations(MAX_EVALUATIONS - 1)
    assert below.evaluations == MAX_EVALUATIONS - 1
    assert evaluations.charge_evaluations().evaluations == MAX_EVALUATIONS
    with pytest.raises(BudgetLimitExceeded) as eval_cutoff:
        evaluations.charge_evaluations()
    assert eval_cutoff.value.reason is BudgetCutoffReason.EVALUATIONS
    assert evaluations.snapshot().evaluations == MAX_EVALUATIONS

    output = BudgetLedger()
    below_output = output.charge_output(MAX_TRANSCRIPT_OUTPUT_BYTES - 1)
    assert below_output.transcript_output_bytes == MAX_TRANSCRIPT_OUTPUT_BYTES - 1
    assert output.charge_output(1).transcript_output_bytes == MAX_TRANSCRIPT_OUTPUT_BYTES
    with pytest.raises(BudgetLimitExceeded) as output_cutoff:
        output.charge_output(1)
    assert output_cutoff.value.reason is BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES
    assert output.snapshot().transcript_output_bytes == MAX_TRANSCRIPT_OUTPUT_BYTES
    logger.info("R14.2a eval/output precharge test exit")


def test_private_monotonic_checkpoint_times_out_at_exact_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a fake clock timeout test entry")
    ticks = iter((100, 100 + 5_000_000_000 - 1, 100 + 5_000_000_000))
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: next(ticks))
    ledger = BudgetLedger()
    assert ledger.checkpoint().elapsed_ns == 5_000_000_000 - 1
    with pytest.raises(BudgetLimitExceeded) as caught:
        ledger.checkpoint()
    assert caught.value.reason is BudgetCutoffReason.WALL_TIME
    assert caught.value.status is SynthesisStatus.INCOMPLETE
    assert caught.value.status is not SynthesisStatus.EXHAUSTED
    assert ledger.snapshot().cutoff_reason is BudgetCutoffReason.WALL_TIME
    logger.info("R14.2a fake clock timeout test exit")


def test_terminal_cutoff_is_sticky_and_always_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a sticky terminal test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 30)
    ledger = BudgetLedger(replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=1))
    ledger.charge_evaluations()
    with pytest.raises(BudgetLimitExceeded) as first:
        ledger.charge_evaluations()
    with pytest.raises(BudgetLimitExceeded) as second:
        ledger.charge_output(0)
    assert first.value.reason is second.value.reason is BudgetCutoffReason.EVALUATIONS
    assert first.value.status is second.value.status is SynthesisStatus.INCOMPLETE
    logger.info("R14.2a sticky terminal test exit")


def test_snapshots_are_frozen_and_all_counters_are_monotone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a monotone snapshot test entry")
    ticks = iter((40, 41, 42, 43, 44))
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: next(ticks))
    ledger = BudgetLedger()
    snapshots = (
        ledger.snapshot(),
        ledger.charge_candidate(2),
        ledger.charge_evaluations(3),
        ledger.charge_output(4),
        ledger.checkpoint(),
    )
    vectors = tuple(
        (
            item.candidates,
            item.canonical_bytes,
            item.evaluations,
            item.transcript_output_bytes,
            item.elapsed_ns,
        )
        for item in snapshots
    )
    assert all(
        all(left <= right for left, right in zip(before, after, strict=True))
        for before, after in zip(vectors, vectors[1:])
    )
    with pytest.raises(FrozenInstanceError):
        snapshots[-1].evaluations = 0  # type: ignore[misc]
    logger.info("R14.2a monotone snapshot test exit")


@pytest.mark.parametrize("value", (-1, True, 1.0, "1", MAX_LEDGER_INTEGER + 1))
@pytest.mark.parametrize(
    "method_name",
    ("charge_candidate", "charge_evaluations", "charge_output"),
)
def test_negative_overflow_and_hostile_charges_are_invalid_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
    value: object,
) -> None:
    logger.info("R14.2a invalid charge test entry method=%s", method_name)
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 50)
    ledger = BudgetLedger()
    before = ledger.snapshot()
    method = getattr(ledger, method_name)
    with pytest.raises(BudgetValidationError, match="invalid-budget-charge"):
        method(value)
    assert ledger.snapshot() == before
    logger.info("R14.2a invalid charge test exit method=%s", method_name)


def test_hostile_or_regressing_private_clock_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a hostile clock test entry")
    ticks: list[object] = [100, 99]
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: ticks.pop(0))
    ledger = BudgetLedger()
    with pytest.raises(BudgetValidationError, match="budget-clock-regressed"):
        ledger.checkpoint()

    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: True)
    with pytest.raises(BudgetValidationError, match="invalid-budget-clock"):
        BudgetLedger()
    logger.info("R14.2a hostile clock test exit")


def test_all_typed_cutoff_reasons_are_reserved_for_incomplete() -> None:
    logger.info("R14.2a cutoff status vocabulary test entry")
    assert tuple(BudgetCutoffReason) == (
        BudgetCutoffReason.CANDIDATES,
        BudgetCutoffReason.CANONICAL_BYTES,
        BudgetCutoffReason.EVALUATIONS,
        BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES,
        BudgetCutoffReason.WALL_TIME,
        BudgetCutoffReason.PROCESS_ADDRESS_SPACE,
    )
    for reason in BudgetCutoffReason:
        cutoff = BudgetLimitExceeded(reason)
        assert cutoff.reason is reason
        assert cutoff.status is SynthesisStatus.INCOMPLETE
        assert cutoff.status is not SynthesisStatus.EXHAUSTED
    logger.info("R14.2a cutoff status vocabulary test exit")
