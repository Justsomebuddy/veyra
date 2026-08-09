"""R14.4 trusted-copy and retained-output cutoff regressions."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.observer_synthesis_v2_budget as budget_module
from src.core import observer_synthesis_v2_trial as trial_module
from src.core.observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetLimits,
    BudgetCutoffReason,
    BudgetLimitExceeded,
)
from src.core.observer_synthesis_v2_corpus import (
    DEFAULT_CASES,
    DEFAULT_LOCKED_CORPUS,
    build_locked_corpus_v2,
)
from src.core.observer_synthesis_v2_protocol import build_observer_case_v2
from src.core.observer_synthesis_v2_trial import _evaluate_subject, run_locked_trials_v2
from src.core.observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    InvalidTrialV2,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def test_winner_snapshot_is_exact_fresh_and_fail_closed() -> None:
    logger.info("R14.4 winner trusted-copy test entry")
    trusted = snapshot_locked_winner_v2(DEFAULT_LOCKED_WINNER_V2)
    assert trusted == DEFAULT_LOCKED_WINNER_V2
    assert trusted is not DEFAULT_LOCKED_WINNER_V2
    assert trusted.canonical is not DEFAULT_LOCKED_WINNER_V2.canonical
    for forged in (
        object(),
        replace(DEFAULT_LOCKED_WINNER_V2, ordinal=True),
        replace(DEFAULT_LOCKED_WINNER_V2, ordinal=0),
        replace(DEFAULT_LOCKED_WINNER_V2, canonical=b"crest"),
        replace(DEFAULT_LOCKED_WINNER_V2, digest="0" * 64),
    ):
        with pytest.raises(InvalidTrialV2):
            snapshot_locked_winner_v2(forged)
    logger.info("R14.4 winner trusted-copy test exit")


def test_corpus_snapshot_deep_copies_every_recurrence() -> None:
    logger.info("R14.4 corpus trusted-copy test entry")
    trusted = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    assert trusted is not DEFAULT_LOCKED_CORPUS
    assert trusted.cases is not DEFAULT_LOCKED_CORPUS.cases
    for actual, source in zip(trusted.cases, DEFAULT_CASES, strict=True):
        assert actual is not source
        assert actual.left is not source.left
        assert actual.right is not source.right
        assert actual.case_digest == source.case_digest
    logger.info("R14.4 corpus trusted-copy test exit")


def test_mutated_case_and_cyclic_payload_are_rejected_before_trial() -> None:
    logger.info("R14.4 hostile corpus test entry")
    forged_case = replace(DEFAULT_CASES[0], required_for_winner=False)
    forged_corpus = replace(
        DEFAULT_LOCKED_CORPUS,
        cases=(forged_case,) + DEFAULT_CASES[1:],
    )
    with pytest.raises(InvalidTrialV2):
        run_locked_trials_v2(corpus=forged_corpus)

    cyclic = Pulse(Silence())
    object.__setattr__(cyclic, "tail", cyclic)
    cyclic_case = replace(DEFAULT_CASES[0], left=cyclic)
    cyclic_corpus = replace(
        DEFAULT_LOCKED_CORPUS,
        cases=(cyclic_case,) + DEFAULT_CASES[1:],
    )
    with pytest.raises(InvalidTrialV2):
        run_locked_trials_v2(corpus=cyclic_corpus)
    logger.info("R14.4 hostile corpus test exit")


def test_output_cutoff_occurs_before_subject_result_retention() -> None:
    logger.info("R14.4 atomic retained-output cutoff test entry")
    trusted = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    subject = build_trial_subject_manifest_v2(DEFAULT_LOCKED_WINNER_V2).subjects[0]
    limits = replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=3450)
    with pytest.raises(BudgetLimitExceeded) as caught:
        _evaluate_subject(subject, trusted, limits)
    assert caught.value.reason is BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES
    logger.info("R14.4 atomic retained-output cutoff test exit")


def test_evaluation_cutoff_propagates_as_incomplete_not_invalid() -> None:
    logger.info("R14.4 evaluation cutoff propagation test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=9)
    with pytest.raises(BudgetLimitExceeded) as caught:
        run_locked_trials_v2(limits=limits)
    assert caught.value.reason is BudgetCutoffReason.EVALUATIONS
    logger.info("R14.4 evaluation cutoff propagation test exit")


def test_mutated_public_default_cannot_redefine_literal_corpus_root() -> None:
    logger.info("R14.4 mutable default trust-root regression entry")
    source = DEFAULT_CASES[0]
    original_required = source.required_for_winner
    original_case_digest = source.case_digest
    original_corpus_digest = DEFAULT_LOCKED_CORPUS.corpus_digest
    forged = build_observer_case_v2(
        source.case_id,
        source.group_id,
        source.split,
        source.left,
        source.right,
        source.expected,
        False,
    )
    try:
        object.__setattr__(source, "required_for_winner", False)
        object.__setattr__(source, "case_digest", forged.case_digest)
        poisoned = build_locked_corpus_v2(DEFAULT_CASES)
        object.__setattr__(
            DEFAULT_LOCKED_CORPUS,
            "corpus_digest",
            poisoned.corpus_digest,
        )
        with pytest.raises(InvalidTrialV2):
            snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    finally:
        object.__setattr__(source, "required_for_winner", original_required)
        object.__setattr__(source, "case_digest", original_case_digest)
        object.__setattr__(
            DEFAULT_LOCKED_CORPUS,
            "corpus_digest",
            original_corpus_digest,
        )
    logger.info("R14.4 mutable default trust-root regression exit")


def test_catalog_winner_metadata_is_independently_replayed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4 catalog winner binding regression entry")
    original = trial_module.enumerate_observer_grammar_v2

    def forged_catalog() -> object:
        report = original()
        winner = replace(report.candidates[1], cost=2)
        return replace(
            report,
            candidates=(report.candidates[0], winner) + report.candidates[2:],
        )

    monkeypatch.setattr(trial_module, "enumerate_observer_grammar_v2", forged_catalog)
    with pytest.raises(InvalidTrialV2, match="invalid-trial-catalog"):
        run_locked_trials_v2()
    logger.info("R14.4 catalog winner binding regression exit")


def test_deleted_slots_map_to_typed_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4 deleted-slot regression entry")
    winner = replace(DEFAULT_LOCKED_WINNER_V2)
    object.__delattr__(winner, "canonical")
    with pytest.raises(InvalidTrialV2):
        run_locked_trials_v2(winner=winner)

    corpus = replace(DEFAULT_LOCKED_CORPUS)
    object.__delattr__(corpus, "cases")
    with pytest.raises(InvalidTrialV2):
        run_locked_trials_v2(corpus=corpus)

    pulse = Pulse(Silence())
    object.__delattr__(pulse, "tail")
    broken_case = replace(DEFAULT_CASES[0], left=pulse)
    broken_corpus = replace(
        DEFAULT_LOCKED_CORPUS,
        cases=(broken_case,) + DEFAULT_CASES[1:],
    )
    with pytest.raises(InvalidTrialV2):
        run_locked_trials_v2(corpus=broken_corpus)

    limits = BudgetLimits()
    object.__delattr__(limits, "candidate_limit")
    with pytest.raises(InvalidTrialV2, match="invalid-trial-limits"):
        run_locked_trials_v2(limits=limits)

    catalog = trial_module.enumerate_observer_grammar_v2()
    object.__delattr__(catalog, "grammar")
    monkeypatch.setattr(trial_module, "enumerate_observer_grammar_v2", lambda: catalog)
    with pytest.raises(InvalidTrialV2, match="invalid-trial-catalog"):
        run_locked_trials_v2()
    logger.info("R14.4 deleted-slot regression exit")


def test_runtime_clock_malformation_maps_to_typed_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4 hostile runtime clock regression entry")
    ticks = iter((1, "bad"))
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: next(ticks))
    with pytest.raises(InvalidTrialV2, match="invalid-trial-budget-runtime"):
        run_locked_trials_v2()
    logger.info("R14.4 hostile runtime clock regression exit")
