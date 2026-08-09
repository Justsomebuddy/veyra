"""R14.3a exact budgeted evaluation and cache regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
import logging

import pytest

import src.core.observer_synthesis_v2_budget as budget_module
from src.core.observer_core_types import (
    Apply,
    Input,
    PrimitiveId,
)
from src.core.proof_core_types import Pulse, Silence
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetCutoffReason,
    BudgetLedger,
    BudgetLimitExceeded,
)
from src.core.observer_synthesis_v2_corpus import (
    DEFAULT_CASES,
    DEFAULT_LOCKED_CORPUS,
    cases_for_split_v2,
)
from src.core.observer_synthesis_v2_evaluation import (
    EvaluationCacheV2,
    evaluate_observer_case_v2,
)
from src.core.observer_synthesis_v2_protocol import (
    CacheDisposition,
    CaseEvaluationV2,
    EvaluationInvalidReason,
    ExpectedRelation,
    InvalidCaseEvaluationV2,
    SplitId,
    build_observer_case_v2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


@pytest.fixture
def ledger(monkeypatch: pytest.MonkeyPatch) -> BudgetLedger:
    logger.debug("R14.3a ledger fixture entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 100)
    result = BudgetLedger()
    logger.debug("R14.3a ledger fixture exit")
    return result


def test_crest_passes_exact_train_while_input_fails_second(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a calibration evaluation test entry")
    train = cases_for_split_v2(DEFAULT_LOCKED_CORPUS, SplitId.TRAIN)
    crest_results = tuple(
        evaluate_observer_case_v2(
            Apply(PrimitiveId.CREST, Input()),
            case,
            ledger,
            EvaluationCacheV2(),
        )
        for case in train
    )
    assert all(type(result) is CaseEvaluationV2 and result.matched for result in crest_results)

    input_cache = EvaluationCacheV2()
    input_results = tuple(
        evaluate_observer_case_v2(Input(), case, ledger, input_cache)
        for case in train
    )
    assert all(type(result) is CaseEvaluationV2 for result in input_results)
    first, second = input_results
    assert first.actual is ExpectedRelation.SEPARATE and first.matched is True
    assert second.actual is ExpectedRelation.SEPARATE and second.matched is False
    assert second.expected is ExpectedRelation.ECHO
    logger.info("R14.3a calibration evaluation test exit")


def test_tail_boundary_preserves_left_right_domain_blockage(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a tail blockage evaluation test entry")
    by_id = {case.case_id: case for case in DEFAULT_CASES}
    tail = Apply(PrimitiveId.TAIL, Input())
    left = evaluate_observer_case_v2(tail, by_id[403], ledger, EvaluationCacheV2())
    right = evaluate_observer_case_v2(tail, by_id[404], ledger, EvaluationCacheV2())
    assert type(left) is type(right) is CaseEvaluationV2
    assert left.actual is right.actual is ExpectedRelation.DOMAIN_BLOCKED
    assert left.matched is right.matched is True
    left_data = json.loads(left.canonical_outcome)
    right_data = json.loads(right.canonical_outcome)
    assert left_data["outcome"]["left"] and not left_data["outcome"]["right"]
    assert right_data["outcome"]["right"] and not right_data["outcome"]["left"]
    assert left.outcome_digest != right.outcome_digest
    logger.info("R14.3a tail blockage evaluation test exit")


def test_cache_key_is_exact_and_hits_charge_audit_replay(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a cache accounting test entry")
    cache = EvaluationCacheV2()
    case = DEFAULT_CASES[0]
    observer = Apply(PrimitiveId.CREST, Input())
    miss = evaluate_observer_case_v2(observer, case, ledger, cache)
    after_miss = ledger.snapshot()
    hit = evaluate_observer_case_v2(observer, case, ledger, cache)
    after_hit = ledger.snapshot()
    assert type(miss) is type(hit) is CaseEvaluationV2
    assert miss.cache_disposition is CacheDisposition.MISS
    assert miss.evaluation_charge == 1
    assert hit.cache_disposition is CacheDisposition.HIT
    assert hit.evaluation_charge == 1
    assert miss.observer_digest == hit.observer_digest
    assert miss.case_digest == hit.case_digest
    assert miss.canonical_outcome == hit.canonical_outcome
    assert miss.outcome_digest == hit.outcome_digest
    assert after_miss.evaluations == 1
    assert after_hit.evaluations == 2
    assert cache.size() == 1
    with pytest.raises(FrozenInstanceError):
        miss.matched = False  # type: ignore[misc]
    logger.info("R14.3a cache accounting test exit")


def test_fresh_caches_produce_byte_identical_misses(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a deterministic miss test entry")
    first = evaluate_observer_case_v2(
        Input(), DEFAULT_CASES[0], ledger, EvaluationCacheV2()
    )
    second = evaluate_observer_case_v2(
        Input(), DEFAULT_CASES[0], ledger, EvaluationCacheV2()
    )
    assert type(first) is type(second) is CaseEvaluationV2
    assert first == second
    assert first.cache_disposition is CacheDisposition.MISS
    assert ledger.snapshot().evaluations == 2
    logger.info("R14.3a deterministic miss test exit")


@pytest.mark.parametrize("observer", (object(), "crest", lambda: Input()))
def test_extension_observers_return_typed_invalid_without_charge(
    ledger: BudgetLedger,
    observer: object,
) -> None:
    logger.info("R14.3a invalid observer test entry")
    result = evaluate_observer_case_v2(
        observer,
        DEFAULT_CASES[0],
        ledger,
        EvaluationCacheV2(),
    )
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.OBSERVER,
    )
    assert ledger.snapshot().evaluations == 0
    logger.info("R14.3a invalid observer test exit")


def test_cyclic_resource_and_mutated_inputs_never_succeed(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a hostile graph evaluation test entry")
    cyclic_observer = Apply(PrimitiveId.CREST, Input())
    object.__setattr__(cyclic_observer, "child", cyclic_observer)
    deep_observer: object = Input()
    for _ in range(130):
        deep_observer = Apply(PrimitiveId.TAIL, deep_observer)
    cyclic_recurrence = Pulse(Silence())
    object.__setattr__(cyclic_recurrence, "tail", cyclic_recurrence)
    deep_recurrence = Silence()
    for _ in range(130):
        deep_recurrence = Pulse(deep_recurrence)
    forged_case = replace(DEFAULT_CASES[0], left=cyclic_recurrence)
    rows = (
        (cyclic_observer, DEFAULT_CASES[0], EvaluationInvalidReason.OBSERVER),
        (deep_observer, DEFAULT_CASES[0], EvaluationInvalidReason.OBSERVER),
        (Input(), forged_case, EvaluationInvalidReason.CASE),
        (
            Input(),
            replace(DEFAULT_CASES[0], left=deep_recurrence),
            EvaluationInvalidReason.CASE,
        ),
        (Input(), replace(DEFAULT_CASES[0], case_digest="0" * 64), EvaluationInvalidReason.CASE),
    )
    for observer, case, reason in rows:
        result = evaluate_observer_case_v2(
            observer,
            case,
            ledger,
            EvaluationCacheV2(),
        )
        assert result == InvalidCaseEvaluationV2(SynthesisStatus.INVALID, reason)
    assert ledger.snapshot().evaluations == 0
    logger.info("R14.3a hostile graph evaluation test exit")


def test_hostile_ledger_or_cache_returns_typed_invalid() -> None:
    logger.info("R14.3a invalid runtime object test entry")
    case = DEFAULT_CASES[0]
    cache = EvaluationCacheV2()
    invalid_ledger = evaluate_observer_case_v2(Input(), case, object(), cache)
    assert invalid_ledger == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.LEDGER,
    )
    valid_ledger = BudgetLedger()
    invalid_cache = evaluate_observer_case_v2(Input(), case, valid_ledger, object())
    assert invalid_cache == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert valid_ledger.snapshot().evaluations == 0
    logger.info("R14.3a invalid runtime object test exit")


def test_budget_cutoff_propagates_as_incomplete_not_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3a evaluation cutoff test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 200)
    limits = replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=1)
    ledger = BudgetLedger(limits)
    cache = EvaluationCacheV2()
    assert type(evaluate_observer_case_v2(Input(), DEFAULT_CASES[0], ledger, cache)) is (
        CaseEvaluationV2
    )
    with pytest.raises(BudgetLimitExceeded) as caught:
        evaluate_observer_case_v2(Input(), DEFAULT_CASES[1], ledger, cache)
    assert caught.value.reason is BudgetCutoffReason.EVALUATIONS
    assert caught.value.status is SynthesisStatus.INCOMPLETE
    logger.info("R14.3a evaluation cutoff test exit")


def test_case_mutation_after_cache_fill_cannot_be_a_hit(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a cache mutation test entry")
    case = build_observer_case_v2(
        900,
        9000,
        SplitId.TRAIN,
        Silence(),
        Pulse(Silence()),
        ExpectedRelation.SEPARATE,
        True,
    )
    cache = EvaluationCacheV2()
    assert type(evaluate_observer_case_v2(Input(), case, ledger, cache)) is CaseEvaluationV2
    object.__setattr__(case, "expected", ExpectedRelation.ECHO)
    result = evaluate_observer_case_v2(Input(), case, ledger, cache)
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CASE,
    )
    assert ledger.snapshot().evaluations == 1
    assert cache.size() == 1
    logger.info("R14.3a cache mutation test exit")


def test_poisoned_exact_cache_returns_invalid_after_audit_charge(
    ledger: BudgetLedger,
) -> None:
    logger.info("R14.3a poisoned cache test entry")
    cache = EvaluationCacheV2()
    case = DEFAULT_CASES[0]
    first = evaluate_observer_case_v2(Input(), case, ledger, cache)
    assert type(first) is CaseEvaluationV2
    key = (first.observer_digest, first.case_digest)
    cache._rows[key] = replace(first, matched=not first.matched)
    result = evaluate_observer_case_v2(Input(), case, ledger, cache)
    assert result == InvalidCaseEvaluationV2(
        SynthesisStatus.INVALID,
        EvaluationInvalidReason.CACHE,
    )
    assert ledger.snapshot().evaluations == 2
    logger.info("R14.3a poisoned cache test exit")
