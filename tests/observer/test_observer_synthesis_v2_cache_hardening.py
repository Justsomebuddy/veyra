"""R14.3a review regressions for run-bound audited cache hits."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.observer_synthesis_v2_budget as budget_module
import src.core.observer_synthesis_v2_evaluation as evaluation_module
from src.core.observer_core_types import Apply, Input, PrimitiveId
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetCutoffReason,
    BudgetLedger,
    BudgetLimitExceeded,
)
from src.core.observer_synthesis_v2_corpus import (
    DEFAULT_CASES,
    DEFAULT_LOCKED_CORPUS,
    winner_required_cases_v2,
)
from src.core.observer_synthesis_v2_evaluation import (
    EvaluationCacheV2,
    evaluate_observer_case_v2,
)
from src.core.observer_synthesis_v2_protocol import (
    CacheDisposition,
    CaseEvaluationV2,
    EvaluationInvalidReason,
    InvalidCaseEvaluationV2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


def test_hit_wall_checkpoint_propagates_incomplete_before_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a hit wall checkpoint test entry")
    ticks = iter((0, 0, 5_000_000_000))
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: next(ticks))
    ledger = BudgetLedger()
    cache = EvaluationCacheV2()
    first = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert type(first) is CaseEvaluationV2
    with pytest.raises(BudgetLimitExceeded) as caught:
        evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert caught.value.reason is BudgetCutoffReason.WALL_TIME
    assert caught.value.status is SynthesisStatus.INCOMPLETE
    assert ledger.snapshot().evaluations == 1
    logger.info("R14.3a hit wall checkpoint test exit")


def test_sticky_cutoff_propagates_on_existing_hit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a sticky hit cutoff test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 10)
    limits = replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=1)
    ledger = BudgetLedger(limits)
    cache = EvaluationCacheV2()
    assert type(
        evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    ) is CaseEvaluationV2
    with pytest.raises(BudgetLimitExceeded):
        ledger.charge_evaluations(1)
    with pytest.raises(BudgetLimitExceeded) as caught:
        evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert caught.value.reason is BudgetCutoffReason.EVALUATIONS
    assert caught.value.status is SynthesisStatus.INCOMPLETE
    logger.info("R14.3a sticky hit cutoff test exit")


def test_coherent_forged_echo_cache_row_fails_exact_r11_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a coherent cache poison test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 20)
    ledger = BudgetLedger()
    cache = EvaluationCacheV2()
    case = DEFAULT_CASES[1]
    input_result = evaluate_observer_case_v2(Input(), case, ledger, cache)
    crest_result = evaluate_observer_case_v2(
        Apply(PrimitiveId.CREST, Input()),
        case,
        ledger,
        cache,
    )
    assert type(input_result) is type(crest_result) is CaseEvaluationV2
    assert input_result.matched is False and crest_result.matched is True
    forged = replace(
        crest_result,
        observer_digest=input_result.observer_digest,
    )
    key = (input_result.observer_digest, input_result.case_digest)
    cache._rows[key] = evaluation_module._CachedEvaluationV2(
        cache._run_nonce,
        forged,
    )
    result = evaluate_observer_case_v2(Input(), case, ledger, cache)
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert ledger.snapshot().evaluations == 3
    logger.info("R14.3a coherent cache poison test exit")


def test_cache_is_bound_to_exact_ledger_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a cross-ledger cache test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 30)
    first_ledger, second_ledger = BudgetLedger(), BudgetLedger()
    cache = EvaluationCacheV2()
    assert type(
        evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], first_ledger, cache)
    ) is CaseEvaluationV2
    result = evaluate_observer_case_v2(
        Input(),
        DEFAULT_CASES[0],
        second_ledger,
        cache,
    )
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert first_ledger.snapshot().evaluations == 1
    assert second_ledger.snapshot().evaluations == 0
    logger.info("R14.3a cross-ledger cache test exit")


def test_run_nonce_rejects_row_transplant_between_bound_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a cross-run cache row test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 40)
    ledger = BudgetLedger()
    first_cache, second_cache = EvaluationCacheV2(), EvaluationCacheV2()
    first = evaluate_observer_case_v2(
        Input(), DEFAULT_CASES[0], ledger, first_cache
    )
    assert type(first) is CaseEvaluationV2
    assert type(
        evaluate_observer_case_v2(
            Input(), DEFAULT_CASES[1], ledger, second_cache
        )
    ) is CaseEvaluationV2
    key = (first.observer_digest, first.case_digest)
    second_cache._rows[key] = first_cache._rows[key]
    result = evaluate_observer_case_v2(
        Input(), DEFAULT_CASES[0], ledger, second_cache
    )
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert ledger.snapshot().evaluations == 3
    logger.info("R14.3a cross-run cache row test exit")


def test_hits_are_explicit_charged_audit_replays(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a hit charge policy test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 50)
    ledger, cache = BudgetLedger(), EvaluationCacheV2()
    miss = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    hit = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert type(miss) is type(hit) is CaseEvaluationV2
    assert miss.cache_disposition is CacheDisposition.MISS
    assert hit.cache_disposition is CacheDisposition.HIT
    assert miss.evaluation_charge == hit.evaluation_charge == 1
    assert ledger.snapshot().evaluations == 2
    logger.info("R14.3a hit charge policy test exit")


def test_hostile_cached_field_never_executes_equality_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a hostile cached field test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 55)
    ledger, cache = BudgetLedger(), EvaluationCacheV2()
    first = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert type(first) is CaseEvaluationV2
    equality_called = False

    class Trap:
        def __eq__(self, other: object) -> bool:
            nonlocal equality_called
            equality_called = True
            raise AssertionError("cache-eq-hook")

    poisoned = replace(first, observer_digest=Trap())
    key = (first.observer_digest, first.case_digest)
    cache._rows[key] = evaluation_module._CachedEvaluationV2(
        cache._run_nonce,
        poisoned,
    )
    result = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert equality_called is False
    assert ledger.snapshot().evaluations == 2
    logger.info("R14.3a hostile cached field test exit")


def test_hostile_cache_key_never_executes_equality_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a hostile cache key test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 57)
    ledger, cache = BudgetLedger(), EvaluationCacheV2()
    first = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert type(first) is CaseEvaluationV2
    exact_key = (first.observer_digest, first.case_digest)
    equality_called = False

    class KeyTrap:
        def __hash__(self) -> int:
            return hash(exact_key)

        def __eq__(self, other: object) -> bool:
            nonlocal equality_called
            equality_called = True
            raise AssertionError("key-eq-hook")

    stored = cache._rows.pop(exact_key)
    cache._rows.__setitem__(KeyTrap(), stored)  # type: ignore[arg-type]
    result = evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert equality_called is False
    assert ledger.snapshot().evaluations == 1
    logger.info("R14.3a hostile cache key test exit")


def test_miss_hostile_clock_maps_to_typed_invalid_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a hostile miss clock test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 0)
    ledger = BudgetLedger()
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: -1)
    result = evaluate_observer_case_v2(
        Input(),
        DEFAULT_CASES[0],
        ledger,
        EvaluationCacheV2(),
    )
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.LEDGER,
    )
    assert ledger.snapshot().evaluations == 0
    logger.info("R14.3a hostile miss clock test exit")


def test_crest_passes_required_cases_while_tail_edges_are_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a winner validation policy test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 60)
    ledger, cache = BudgetLedger(), EvaluationCacheV2()
    crest = Apply(PrimitiveId.CREST, Input())
    required = tuple(
        evaluate_observer_case_v2(crest, case, ledger, cache)
        for case in winner_required_cases_v2(DEFAULT_LOCKED_CORPUS)
    )
    assert all(type(row) is CaseEvaluationV2 and row.matched for row in required)
    diagnostics = tuple(case for case in DEFAULT_CASES if not case.required_for_winner)
    crest_diagnostics = tuple(
        evaluate_observer_case_v2(crest, case, ledger, cache)
        for case in diagnostics
    )
    assert all(
        type(row) is CaseEvaluationV2 and not row.matched
        for row in crest_diagnostics
    )
    tail = Apply(PrimitiveId.TAIL, Input())
    tail_diagnostics = tuple(
        evaluate_observer_case_v2(tail, case, ledger, cache)
        for case in diagnostics
    )
    assert all(
        type(row) is CaseEvaluationV2 and row.matched
        for row in tail_diagnostics
    )
    logger.info("R14.3a winner validation policy test exit")
