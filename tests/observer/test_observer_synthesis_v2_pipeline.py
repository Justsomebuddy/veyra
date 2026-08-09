"""Atomic five-plus-one aggregate checks for R14."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

import src.core.observer_synthesis_v2_pipeline as pipeline
from src.core.observer_synthesis_v2_receipt_worker_types import (
    ISOLATED_RECEIPT_RESULT_SCHEMA,
    IsolatedObserverReceiptResultV2,
)
from src.core.observer_synthesis_v2_trial import run_locked_trials_v2
from src.core.observer_synthesis_v2_trial_worker_types import (
    ISOLATED_TRIAL_RESULT_SCHEMA,
    IsolatedObserverTrialResultV2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

pytestmark = pytest.mark.requires_linux

LIMITS_DIGEST = (
    "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb"
)
REPORT_DIGEST = (
    "07dbfe7567f86a2817bd01317ceb14e8c8650fd2ed488a7e1a6a7aad5f890f48"
)


def _complete_trial() -> IsolatedObserverTrialResultV2:
    """Build an exact terminal around the deterministic in-process report."""
    report = run_locked_trials_v2()
    return IsolatedObserverTrialResultV2(
        ISOLATED_TRIAL_RESULT_SCHEMA,
        SynthesisStatus.FOUND,
        "isolated-trial-complete",
        LIMITS_DIGEST,
        report,
        report.report_digest,
    )


def test_real_pipeline_calls_approved_five_and_one_stages_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    trial_stage = pipeline.run_isolated_locked_trials_v2
    receipt_stage = pipeline.run_isolated_receipts_v2

    def trials() -> object:
        calls.append("five-trial-children")
        return trial_stage()

    def receipt(trial: object) -> object:
        calls.append("one-receipt-child")
        return receipt_stage(trial)

    monkeypatch.setattr(pipeline, "run_isolated_locked_trials_v2", trials)
    monkeypatch.setattr(pipeline, "run_isolated_receipts_v2", receipt)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert calls == ["five-trial-children", "one-receipt-child"]
    assert result.status is SynthesisStatus.FOUND
    assert result.evidence is not None
    assert result.evidence.subjects == 5
    assert result.evidence.cases == 10
    assert result.evidence.receipt_rows == 10
    assert result.evidence.receipt_bundle_bytes == 27_857
    assert len(result.evidence.receipt_bundle_sha256) == 64


def test_trial_failure_is_atomic_and_never_starts_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial = IsolatedObserverTrialResultV2(
        ISOLATED_TRIAL_RESULT_SCHEMA,
        SynthesisStatus.INCOMPLETE,
        "trial-worker-wall",
        LIMITS_DIGEST,
        None,
        None,
    )
    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        lambda: trial,
    )

    def forbidden(_: object) -> object:
        raise AssertionError("receipt child must not start")

    monkeypatch.setattr(pipeline, "run_isolated_receipts_v2", forbidden)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.evidence is None


def test_receipt_failure_discards_all_partial_trial_pins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        _complete_trial,
    )
    failed = IsolatedObserverReceiptResultV2(
        ISOLATED_RECEIPT_RESULT_SCHEMA,
        SynthesisStatus.INCOMPLETE,
        "receipt-worker-wall",
        LIMITS_DIGEST,
        REPORT_DIGEST,
        None,
        None,
        None,
    )
    monkeypatch.setattr(
        pipeline,
        "run_isolated_receipts_v2",
        lambda _: failed,
    )
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.evidence is None


def test_forged_terminal_types_and_receipt_bytes_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        _complete_trial,
    )
    forged = IsolatedObserverReceiptResultV2(
        ISOLATED_RECEIPT_RESULT_SCHEMA,
        SynthesisStatus.FOUND,
        "receipt-complete",
        LIMITS_DIGEST,
        REPORT_DIGEST,
        b"x" * 27_857,
        sha256(b"x" * 27_857).hexdigest(),
        "740f55aa23a8372d01db506e1019cbab2bdb5990796c6c3b158ec048286b0895",
    )
    monkeypatch.setattr(
        pipeline,
        "run_isolated_receipts_v2",
        lambda _: forged,
    )
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None

    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        lambda: object(),
    )
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None


def test_malformed_exact_report_shape_fails_before_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal = _complete_trial()
    assert terminal.report is not None
    malformed = replace(
        terminal,
        report=replace(terminal.report, subjects=(object(),)),
    )
    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        lambda: malformed,
    )

    def forbidden(_: object) -> object:
        raise AssertionError("receipt child must not start")

    monkeypatch.setattr(pipeline, "run_isolated_receipts_v2", forbidden)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None


def test_aggregate_nonclaims_and_taxonomy_are_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial_stage = pipeline.run_isolated_locked_trials_v2
    receipt_stage = pipeline.run_isolated_receipts_v2
    trial = trial_stage()
    receipt = receipt_stage(trial)
    monkeypatch.setattr(
        pipeline,
        "run_isolated_locked_trials_v2",
        lambda: trial,
    )
    monkeypatch.setattr(
        pipeline,
        "run_isolated_receipts_v2",
        lambda _: receipt,
    )
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.evidence is not None
    evidence = result.evidence
    assert evidence.taxonomy_counts == (2, 4, 25, 5)
    assert evidence.layers == 36
    assert (
        evidence.general_completeness,
        evidence.general_minimality,
        evidence.novelty,
        evidence.superiority,
        evidence.evidence_accepted,
        evidence.promotion_ready,
        evidence.taxonomy_changed,
        evidence.proof_complete,
    ) == (False,) * 8
    assert "not a theorem" in evidence.boundary
    assert "R8 evidence" in evidence.boundary


class _EqualityBomb:
    def __eq__(self, _: object) -> bool:
        raise AssertionError("hostile equality must not run")


def test_trial_hostile_and_deleted_slots_fail_closed_before_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial = _complete_trial()
    assert trial.report is not None
    object.__setattr__(trial.report.guarantee, "train_matched", _EqualityBomb())
    monkeypatch.setattr(pipeline, "run_isolated_locked_trials_v2", lambda: trial)
    monkeypatch.setattr(
        pipeline,
        "run_isolated_receipts_v2",
        lambda _: pytest.fail("receipt child must not start"),
    )
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None
    deleted = _complete_trial()
    object.__delattr__(deleted, "status")
    monkeypatch.setattr(pipeline, "run_isolated_locked_trials_v2", lambda: deleted)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None


def test_pipeline_never_rereads_mutated_trial_after_receipt_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial = _complete_trial()
    assert trial.report is not None
    receipt = pipeline.run_isolated_receipts_v2(trial)
    monkeypatch.setattr(pipeline, "run_isolated_locked_trials_v2", lambda: trial)

    def mutate_then_return(_: object) -> object:
        assert trial.report is not None
        object.__setattr__(trial.report.guarantee, "all_required_matched", 7)
        return receipt

    monkeypatch.setattr(pipeline, "run_isolated_receipts_v2", mutate_then_return)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.FOUND
    assert result.evidence is not None
    assert result.evidence.required_matched == 8


def test_receipt_deleted_status_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trial = _complete_trial()
    receipt = pipeline.run_isolated_receipts_v2(trial)
    object.__delattr__(receipt, "status")
    monkeypatch.setattr(pipeline, "run_isolated_locked_trials_v2", lambda: trial)
    monkeypatch.setattr(pipeline, "run_isolated_receipts_v2", lambda _: receipt)
    result = pipeline.run_observer_synthesis_v2_pipeline()
    assert result.status is SynthesisStatus.INVALID
    assert result.evidence is None
