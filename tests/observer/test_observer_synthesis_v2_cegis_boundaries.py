"""R14.3b cutoff, invalid-input, and exact-exhaustion regressions."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core import observer_synthesis_v2_budget as budget_module
from src.core import observer_synthesis_v2_cegis as cegis_module
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetCutoffReason,
)
from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_cegis_types import CegisTerminalReasonV2
from src.core.observer_synthesis_v2_cegis_validation import (
    validate_cegis_catalog_v2,
    validate_cegis_train_cases_v2,
)
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES, PULSE_4, PULSE_5
from src.core.observer_synthesis_v2_grammar import (
    EXPECTED_DEFAULT_CANDIDATES,
    enumerate_observer_grammar_v2,
)
from src.core.observer_synthesis_v2_protocol import (
    ExpectedRelation,
    SplitId,
    build_observer_case_v2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


@pytest.fixture
def exact_catalog(monkeypatch: pytest.MonkeyPatch) -> object:
    logger.debug("boundary exact_catalog fixture entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 300)
    result = enumerate_observer_grammar_v2()
    logger.debug("boundary exact_catalog fixture exit")
    return result


@pytest.mark.parametrize(
    ("limits", "reason"),
    (
        (
            replace(DEFAULT_BUDGET_LIMITS, candidate_limit=1564),
            BudgetCutoffReason.CANDIDATES,
        ),
        (
            replace(DEFAULT_BUDGET_LIMITS, canonical_bytes_limit=488_549),
            BudgetCutoffReason.CANONICAL_BYTES,
        ),
        (
            replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=1),
            BudgetCutoffReason.EVALUATIONS,
        ),
        (
            replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=1),
            BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES,
        ),
    ),
)
def test_every_search_cutoff_is_incomplete_never_exhausted(
    exact_catalog: object,
    limits: object,
    reason: BudgetCutoffReason,
) -> None:
    logger.info("R14.3b cutoff test entry reason=%s", reason.value)
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2], limits)
    assert report.status is SynthesisStatus.INCOMPLETE
    assert report.status is not SynthesisStatus.EXHAUSTED
    assert report.terminal_reason is CegisTerminalReasonV2.BUDGET_CUTOFF
    assert report.detail == reason.value
    assert report.winner is None
    assert report.ledger is not None
    assert report.ledger.cutoff_reason is reason
    if reason is BudgetCutoffReason.CANDIDATES:
        assert report.ledger.candidates == 1564
        assert report.traversed_candidates == 0
    if reason is BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES:
        assert report.trace == ()
        assert report.ledger.transcript_output_bytes == 0
    logger.info("R14.3b cutoff test exit reason=%s", reason.value)


def test_impossible_obligation_exhausts_exactly_the_full_catalog(
    exact_catalog: object,
) -> None:
    logger.info("R14.3b exact exhaustion test entry")
    impossible = build_observer_case_v2(
        101,
        9101,
        SplitId.TRAIN,
        PULSE_4,
        PULSE_5,
        ExpectedRelation.DOMAIN_BLOCKED,
        True,
    )
    report = fit_observer_cegis_v2(exact_catalog, (impossible,))
    assert report.status is SynthesisStatus.EXHAUSTED
    assert report.terminal_reason is CegisTerminalReasonV2.COMPLETE_TRAVERSAL
    assert report.detail == "exact-catalog-exhausted"
    assert report.traversed_candidates == EXPECTED_DEFAULT_CANDIDATES
    assert report.winner is None
    assert report.active_case_ids == (101,)
    assert report.ledger is not None
    assert report.ledger.candidates == EXPECTED_DEFAULT_CANDIDATES
    assert report.ledger.evaluations == EXPECTED_DEFAULT_CANDIDATES
    assert report.ledger.cutoff_reason is None
    logger.info("R14.3b exact exhaustion test exit")


def test_counterexample_then_full_pass_can_only_end_exhausted(
    exact_catalog: object,
) -> None:
    logger.info("R14.3b multi-round exhaustion test entry")
    impossible_second = build_observer_case_v2(
        102,
        9102,
        SplitId.TRAIN,
        PULSE_4,
        PULSE_5,
        ExpectedRelation.DOMAIN_BLOCKED,
        True,
    )
    report = fit_observer_cegis_v2(
        exact_catalog,
        (DEFAULT_CASES[0], impossible_second),
    )
    assert report.status is SynthesisStatus.EXHAUSTED
    assert report.terminal_reason is CegisTerminalReasonV2.COMPLETE_TRAVERSAL
    assert report.traversed_candidates == EXPECTED_DEFAULT_CANDIDATES
    assert report.active_case_ids == (101, 102)
    assert report.winner is None
    logger.info("R14.3b multi-round exhaustion test exit")


@pytest.mark.parametrize(
    "train",
    (
        DEFAULT_CASES[2:3],
        DEFAULT_CASES[:1] + DEFAULT_CASES[2:3],
        tuple(reversed(DEFAULT_CASES[:2])),
        [DEFAULT_CASES[0]],
        (),
        object(),
    ),
)
def test_nontrain_or_hostile_case_containers_are_invalid(
    exact_catalog: object,
    train: object,
) -> None:
    logger.info("R14.3b invalid train test entry type=%s", type(train).__name__)
    report = fit_observer_cegis_v2(exact_catalog, train)
    assert report.status is SynthesisStatus.INVALID
    assert report.terminal_reason is CegisTerminalReasonV2.INVALID_INPUT
    assert report.winner is None
    assert report.traversed_candidates == 0
    logger.info("R14.3b invalid train test exit")


def test_hostile_catalog_and_limits_are_invalid(exact_catalog: object) -> None:
    logger.info("R14.3b invalid config test entry")
    forged_catalog = replace(exact_catalog, catalog_digest="0" * 64)
    catalog_report = fit_observer_cegis_v2(forged_catalog, DEFAULT_CASES[:2])
    limits_report = fit_observer_cegis_v2(
        exact_catalog,
        DEFAULT_CASES[:2],
        object(),
    )
    assert catalog_report.status is limits_report.status is SynthesisStatus.INVALID
    assert catalog_report.terminal_reason is CegisTerminalReasonV2.INVALID_INPUT
    assert limits_report.terminal_reason is CegisTerminalReasonV2.INVALID_INPUT
    assert catalog_report.detail == "invalid-exact-default-catalog"
    assert limits_report.detail == "invalid-budget-configuration"
    assert catalog_report.winner is limits_report.winner is None
    logger.info("R14.3b invalid config test exit")


def test_catalog_shape_gate_never_invokes_hostile_length_hook(
    exact_catalog: object,
) -> None:
    logger.info("R14.3b hostile catalog hook test entry")

    class LengthTrap:
        def __len__(self) -> int:
            logger.error("LengthTrap.__len__ must not execute")
            raise AssertionError("hostile-length-hook-executed")

    forged = replace(exact_catalog)
    object.__setattr__(forged, "candidates", LengthTrap())
    report = fit_observer_cegis_v2(forged, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-exact-default-catalog"
    logger.info("R14.3b hostile catalog hook test exit")


@pytest.mark.parametrize("duplicate_kind", ("group", "payload-clone"))
def test_train_duplicate_bindings_are_invalid(
    exact_catalog: object,
    duplicate_kind: str,
) -> None:
    logger.info("R14.3b duplicate train test entry kind=%s", duplicate_kind)
    first, second = DEFAULT_CASES[:2]
    if duplicate_kind == "group":
        duplicate = build_observer_case_v2(
            102,
            first.group_id,
            SplitId.TRAIN,
            second.left,
            second.right,
            second.expected,
            True,
        )
    else:
        duplicate = build_observer_case_v2(
            102,
            second.group_id,
            SplitId.TRAIN,
            first.left,
            first.right,
            first.expected,
            True,
        )
    report = fit_observer_cegis_v2(exact_catalog, (first, duplicate))
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-train-case-closure"
    logger.info("R14.3b duplicate train test exit kind=%s", duplicate_kind)


def test_unexpected_internal_runtime_error_is_not_laundered_as_invalid(
    exact_catalog: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b internal crash boundary test entry")

    def crash(_catalog: object) -> object:
        logger.error("synthetic internal crash")
        raise RuntimeError("synthetic-internal-crash")

    monkeypatch.setattr(cegis_module, "validate_cegis_catalog_v2", crash)
    with pytest.raises(RuntimeError, match="synthetic-internal-crash"):
        fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2])
    logger.info("R14.3b internal crash boundary test exit")


def test_output_precharge_retains_no_partial_seed(exact_catalog: object) -> None:
    logger.info("R14.3b output atomicity test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=427)
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2], limits)
    assert report.status is SynthesisStatus.INCOMPLETE
    assert report.detail == BudgetCutoffReason.TRANSCRIPT_OUTPUT_BYTES.value
    assert report.trace == ()
    assert report.trace_digest
    assert report.ledger is not None
    assert report.ledger.transcript_output_bytes == 0
    logger.info("R14.3b output atomicity test exit")


def test_winner_and_trace_output_precharge_is_atomic(exact_catalog: object) -> None:
    logger.info("R14.3b winner output atomicity test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=1033)
    report = fit_observer_cegis_v2(exact_catalog, DEFAULT_CASES[:2], limits)
    assert report.status is SynthesisStatus.INCOMPLETE
    assert report.winner is None
    assert len(report.trace) == 2
    assert report.ledger is not None
    assert report.ledger.transcript_output_bytes == sum(
        len(step.canonical) for step in report.trace
    ) == 927
    logger.info("R14.3b winner output atomicity test exit")


def test_validation_returns_deep_trusted_input_snapshots(
    exact_catalog: object,
) -> None:
    logger.info("R14.3b trusted snapshot identity test entry")
    trusted_catalog = validate_cegis_catalog_v2(exact_catalog)
    trusted_train = validate_cegis_train_cases_v2(DEFAULT_CASES[:2])
    assert trusted_catalog is not exact_catalog
    assert all(
        trusted is not hostile
        for trusted, hostile in zip(
            trusted_catalog.candidates,
            exact_catalog.candidates,
            strict=True,
        )
    )
    assert all(
        trusted is not hostile
        and trusted.left is not hostile.left
        and trusted.right is not hostile.right
        for trusted, hostile in zip(trusted_train, DEFAULT_CASES[:2], strict=True)
    )
    logger.info("R14.3b trusted snapshot identity test exit")
