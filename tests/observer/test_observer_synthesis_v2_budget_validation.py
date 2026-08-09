"""R14.2a hostile budget snapshot validation regressions."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.observer_synthesis_v2_budget as budget_module
from src.core.observer_synthesis_v2_budget import (
    MAX_CANDIDATES,
    BudgetLimits,
    BudgetCutoffReason,
    BudgetLedger,
    BudgetLimitExceeded,
)
from src.core.observer_synthesis_v2_budget_validation import (
    verify_budget_ledger_snapshot,
)

logger = logging.getLogger(__name__)


def test_exact_live_snapshots_validate(monkeypatch: pytest.MonkeyPatch) -> None:
    logger.info("R14.2a snapshot positive validation entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 100)
    ledger = BudgetLedger()
    assert verify_budget_ledger_snapshot(ledger.snapshot())
    assert verify_budget_ledger_snapshot(ledger.charge_candidate(1))
    assert verify_budget_ledger_snapshot(ledger.charge_evaluations())
    assert verify_budget_ledger_snapshot(ledger.charge_output(1))
    logger.info("R14.2a snapshot positive validation exit")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("candidates", True),
        ("candidates", -1),
        ("candidates", MAX_CANDIDATES + 1),
        ("canonical_bytes", -1),
        ("evaluations", -1),
        ("transcript_output_bytes", -1),
        ("elapsed_ns", -1),
        ("cutoff_reason", "wall-time-limit"),
    ),
)
def test_hostile_snapshot_fields_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    logger.info("R14.2a snapshot hostile validation entry field=%s", field)
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 200)
    snapshot = BudgetLedger().snapshot()
    assert not verify_budget_ledger_snapshot(replace(snapshot, **{field: value}))
    logger.info("R14.2a snapshot hostile validation exit field=%s", field)


def test_accounting_and_wall_cutoff_consistency_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a snapshot consistency validation entry")
    ticks = iter((0, 5_000_000_000))
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: next(ticks))
    ledger = BudgetLedger()
    with pytest.raises(BudgetLimitExceeded):
        ledger.checkpoint()
    cutoff = ledger.snapshot()
    assert verify_budget_ledger_snapshot(cutoff)
    assert not verify_budget_ledger_snapshot(
        replace(cutoff, cutoff_reason=BudgetCutoffReason.EVALUATIONS)
    )
    assert not verify_budget_ledger_snapshot(
        replace(cutoff, candidates=1, canonical_bytes=0)
    )
    ready = replace(cutoff, elapsed_ns=0, cutoff_reason=None)
    assert verify_budget_ledger_snapshot(ready)
    assert not verify_budget_ledger_snapshot(
        replace(ready, cutoff_reason=BudgetCutoffReason.CANDIDATES)
    )
    logger.info("R14.2a snapshot consistency validation exit")


def test_ledger_validates_fresh_snapshot_after_caller_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a limits snapshot TOCTOU regression entry")
    limits = BudgetLimits()
    original = budget_module.validate_budget_limits

    def mutate_then_validate(captured: object) -> BudgetLimits:
        object.__setattr__(limits, "candidate_limit", MAX_CANDIDATES + 1)
        return original(captured)

    monkeypatch.setattr(budget_module, "validate_budget_limits", mutate_then_validate)
    ledger = BudgetLedger(limits)
    assert ledger.snapshot().limits.candidate_limit == MAX_CANDIDATES
    logger.info("R14.2a limits snapshot TOCTOU regression exit")


def test_snapshot_cannot_mutate_live_ledger_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2a snapshot limits isolation regression entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 0)
    ledger = BudgetLedger(BudgetLimits(candidate_limit=1))
    exposed = ledger.snapshot()
    assert exposed.limits is not ledger._limits
    object.__setattr__(exposed.limits, "candidate_limit", 3)
    ledger.charge_candidate(1)
    with pytest.raises(BudgetLimitExceeded) as exc_info:
        ledger.charge_candidate(1)
    assert exc_info.value.reason is BudgetCutoffReason.CANDIDATES
    logger.info("R14.2a snapshot limits isolation regression exit")
