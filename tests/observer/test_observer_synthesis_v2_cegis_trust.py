"""R14.3b hostile catalog hook and trusted-snapshot regressions."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core import observer_synthesis_v2_budget as budget_module
from src.core.observer_core_types import Apply, Input, PrimitiveId
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS
from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_cegis_validation import (
    InvalidCegisV2,
    _trusted_recurrence,
)
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def test_fit_rejects_response_kind_hook_without_semantic_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b hostile response-kind fit test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 700)
    catalog = enumerate_observer_grammar_v2()
    first = catalog.candidates[0]
    hook_called = False

    class Trap:
        def __eq__(self, other: object) -> bool:
            nonlocal hook_called
            hook_called = True
            object.__setattr__(
                first,
                "observer",
                Apply(PrimitiveId.CREST, Input()),
            )
            return True

    poisoned = replace(catalog.candidates[-1], response_kind=Trap())
    hostile = replace(
        catalog,
        candidates=catalog.candidates[:-1] + (poisoned,),
    )
    report = fit_observer_cegis_v2(hostile, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-exact-default-catalog"
    assert report.winner is None
    assert hook_called is False
    assert type(first.observer) is Input
    logger.info("R14.3b hostile response-kind fit test exit")


def test_trusted_recurrence_copy_rejects_cycle_without_second_pass_hang() -> None:
    logger.info("R14.3b trusted recurrence cycle test entry")
    cyclic = Pulse(Silence())
    object.__setattr__(cyclic, "tail", cyclic)
    with pytest.raises(
        InvalidCegisV2,
        match="train-recurrence-resource-or-cycle",
    ):
        _trusted_recurrence(cyclic)
    logger.info("R14.3b trusted recurrence cycle test exit")


def test_fit_and_terminal_report_do_not_retain_caller_budget_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b trusted budget snapshot test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 800)
    limits = replace(DEFAULT_BUDGET_LIMITS)
    report = fit_observer_cegis_v2(
        enumerate_observer_grammar_v2(),
        DEFAULT_CASES[:2],
        limits,
    )
    assert report.status is SynthesisStatus.FOUND
    assert report.ledger is not None
    assert report.ledger.limits is not limits
    pinned = report.ledger.limits.evaluation_limit
    object.__setattr__(limits, "evaluation_limit", 1)
    assert report.ledger.limits.evaluation_limit == pinned == 100_000
    logger.info("R14.3b trusted budget snapshot test exit")


def test_counterexample_becomes_active_only_after_trace_precharge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b counterexample trace atomicity test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 900)
    limits = replace(
        DEFAULT_BUDGET_LIMITS,
        transcript_output_bytes_limit=926,
    )
    report = fit_observer_cegis_v2(
        enumerate_observer_grammar_v2(),
        DEFAULT_CASES[:2],
        limits,
    )
    assert report.status is SynthesisStatus.INCOMPLETE
    assert report.active_case_ids == (101,)
    assert len(report.trace) == 1
    assert report.ledger is not None
    assert report.ledger.transcript_output_bytes == 428
    logger.info("R14.3b counterexample trace atomicity test exit")
