"""R14.3b deterministic TRAIN-only CEGIS calibration regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging

import pytest

from src.core import observer_synthesis_v2_budget as budget_module
from src.core import observer_synthesis_v2_corpus as corpus_module
from src.core.observer_synthesis_v2_budget import BudgetLedger
from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_cegis_types import (
    CegisEventV2,
    CegisTerminalReasonV2,
)
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_evaluation import (
    EvaluationCacheV2,
    evaluate_observer_case_v2,
)
from src.core.observer_synthesis_v2_grammar import (
    EXPECTED_DEFAULT_CANONICAL_BYTES,
    EXPECTED_DEFAULT_CANDIDATES,
    enumerate_observer_grammar_v2,
)
from src.core.observer_synthesis_v2_protocol import CaseEvaluationV2
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)

EXPECTED_TRACE_DIGEST = "d27aaa2d61a7a7bd69e46bfd43eab76fadd1ac666e144d9241466bc5222e0da7"
EXPECTED_WINNER_DIGEST = "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
EXPECTED_WINNER_CANONICAL = (
    b'{"observer":{"child":{"tag":"input"},"primitive":"crest","tag":"apply"},'
    b'"schema":"veyra.observer-core.v2"}'
)


@pytest.fixture
def exact_catalog(monkeypatch: pytest.MonkeyPatch) -> object:
    logger.debug("exact_catalog fixture entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 100)
    result = enumerate_observer_grammar_v2()
    logger.debug("exact_catalog fixture exit")
    return result


def test_exact_default_cegis_trace_and_winner_pins(exact_catalog: object) -> None:
    logger.info("R14.3b exact trace test entry")
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.FOUND
    assert report.terminal_reason is CegisTerminalReasonV2.FOUND
    assert report.detail == "first-train-satisfying-candidate"
    assert tuple(step.event for step in report.trace) == (
        CegisEventV2.SEED,
        CegisEventV2.COUNTEREXAMPLE,
        CegisEventV2.WINNER,
    )
    assert tuple(step.candidate_ordinal for step in report.trace) == (0, 0, 1)
    assert tuple(step.counterexample_case_id for step in report.trace) == (
        None,
        102,
        None,
    )
    assert tuple(step.charged_evaluations for step in report.trace) == (0, 2, 6)
    assert report.trace_digest == EXPECTED_TRACE_DIGEST
    assert report.traversed_candidates == 2
    assert report.active_case_ids == (101, 102)
    assert report.winner is not None
    assert report.winner.ordinal == 1
    assert report.winner.cost == report.winner.depth == 1
    assert report.winner.digest == EXPECTED_WINNER_DIGEST
    assert report.winner.canonical == EXPECTED_WINNER_CANONICAL
    assert report.ledger is not None
    assert report.ledger.candidates == EXPECTED_DEFAULT_CANDIDATES
    assert report.ledger.canonical_bytes == EXPECTED_DEFAULT_CANONICAL_BYTES
    assert report.ledger.evaluations == 6
    assert report.ledger.transcript_output_bytes == 1463
    logger.info("R14.3b exact trace test exit")


def test_trace_is_byte_identical_across_private_clocks_and_fresh_caches(
    exact_catalog: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b deterministic transcript test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 200)
    first = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 999_999)
    second = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    assert first.trace == second.trace
    assert first.trace_digest == second.trace_digest == EXPECTED_TRACE_DIGEST
    assert first.winner == second.winner
    transcript = b"".join(step.canonical for step in first.trace)
    assert b"elapsed" not in transcript
    assert b"nonce" not in transcript
    assert b"cache" not in transcript
    assert b"transcript_output_bytes" not in transcript
    logger.info("R14.3b deterministic transcript test exit")


def test_fit_never_calls_corpus_split_or_winner_selectors(
    exact_catalog: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b train isolation test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        logger.error("forbidden corpus selector called")
        raise AssertionError("post-fit-split-leakage")

    monkeypatch.setattr(corpus_module, "cases_for_split_v2", forbidden)
    monkeypatch.setattr(corpus_module, "winner_required_cases_v2", forbidden)
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.FOUND
    assert report.active_case_ids == (101, 102)
    logger.info("R14.3b train isolation test exit")


def test_locked_winner_cannot_be_reranked_by_post_fit_rows(
    exact_catalog: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b winner lock test entry")
    private_train = tuple(replace(case) for case in DEFAULT_CASES[:2])
    report = fit_observer_cegis_v2(exact_catalog, private_train)
    before = report.winner, report.trace, report.trace_digest
    assert report.winner is not None
    observer = exact_catalog.candidates[report.winner.ordinal].observer
    post_ledger = BudgetLedger()
    post_results = tuple(
        evaluate_observer_case_v2(
            observer,
            case,
            post_ledger,
            EvaluationCacheV2(),
        )
        for case in DEFAULT_CASES[2:]
    )
    assert all(type(row) is CaseEvaluationV2 for row in post_results)
    object.__setattr__(private_train[1], "case_id", 999)
    assert (report.winner, report.trace, report.trace_digest) == before
    assert report.active_case_ids == (101, 102)
    logger.info("R14.3b winner lock test exit")


def test_result_types_are_frozen(exact_catalog: object) -> None:
    logger.info("R14.3b frozen result test entry")
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    with pytest.raises(FrozenInstanceError):
        report.status = SynthesisStatus.INVALID  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.trace[0].sequence = 0  # type: ignore[misc]
    assert report.winner is not None
    with pytest.raises(FrozenInstanceError):
        report.winner.ordinal = 5  # type: ignore[misc]
    logger.info("R14.3b frozen result test exit")
