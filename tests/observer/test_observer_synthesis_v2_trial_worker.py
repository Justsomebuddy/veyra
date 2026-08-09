"""R14.4b isolated five-child trial regressions."""
from __future__ import annotations

from dataclasses import replace
import logging
import subprocess
from typing import Any

import pytest

from src.core import observer_synthesis_v2_trial_execution as execution_module
from src.core import observer_synthesis_v2_trial_worker as isolated_module
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS
from src.core.observer_synthesis_v2_trial import (
    EXPECTED_TRIAL_REPORT_DIGEST,
    run_locked_trials_v2,
)
from src.core.observer_synthesis_v2_trial_validation import DEFAULT_LOCKED_WINNER_V2
from src.core.observer_synthesis_v2_trial_worker import (
    build_trial_subject_requests_v2,
    run_isolated_locked_trials_v2,
)
from src.core.observer_synthesis_v2_trial_worker_codec import (
    trial_subject_request_bytes_v2,
    trial_subject_request_from_bytes_v2,
)
from src.core.observer_synthesis_v2_trial_worker_types import (
    TRIAL_SUBJECT_REQUEST_SCHEMA,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)


def test_exact_five_requests_are_prebuilt_and_canonical() -> None:
    logger.info("R14.4b exact request vector test entry")
    requests = build_trial_subject_requests_v2()
    assert len(requests) == 5
    assert tuple(row.subject_index for row in requests) == tuple(range(5))
    assert all(row.schema == TRIAL_SUBJECT_REQUEST_SCHEMA for row in requests)
    assert len({row.limits_digest for row in requests}) == 1
    assert all(row.case_ids == requests[0].case_ids for row in requests)
    assert all(row.case_digests == requests[0].case_digests for row in requests)
    for request in requests:
        encoded = trial_subject_request_bytes_v2(request)
        assert trial_subject_request_from_bytes_v2(encoded) == request
    logger.info("R14.4b exact request vector test exit")


def test_five_real_children_reproduce_existing_report_byte_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4b five child identity test entry")
    original = isolated_module.subprocess.Popen
    spawns: list[subprocess.Popen[bytes]] = []
    limits_seen: list[int] = []
    original_limits = isolated_module._apply_limits

    def recording_spawn(
        args: list[str],
        **kwargs: Any,
    ) -> subprocess.Popen[bytes]:
        proc = original(args, **kwargs)
        spawns.append(proc)
        return proc

    def recording_limits(pid: int, limit: int) -> bool:
        limits_seen.append(limit)
        return original_limits(pid, limit)

    monkeypatch.setattr(isolated_module.subprocess, "Popen", recording_spawn)
    monkeypatch.setattr(isolated_module, "_apply_limits", recording_limits)
    isolated = run_isolated_locked_trials_v2()
    expected = run_locked_trials_v2()
    assert isolated.status is SynthesisStatus.FOUND
    assert isolated.report == expected
    assert isolated.report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    assert len(spawns) == 5 and all(proc.poll() is not None for proc in spawns)
    assert limits_seen == [DEFAULT_BUDGET_LIMITS.process_as_bytes_limit] * 5
    logger.info("R14.4b five child identity test exit")


def test_parent_never_calls_inprocess_subject_evaluator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4b no parent evaluation test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("parent-evaluated-subject")

    monkeypatch.setattr(execution_module, "evaluate_trial_subject_v2", forbidden)
    result = run_isolated_locked_trials_v2()
    assert result.status is SynthesisStatus.FOUND
    assert result.report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    logger.info("R14.4b no parent evaluation test exit")


def test_repeated_isolated_runs_are_deterministic() -> None:
    logger.info("R14.4b deterministic isolated test entry")
    first = run_isolated_locked_trials_v2()
    second = run_isolated_locked_trials_v2()
    assert first == second
    assert first.report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    logger.info("R14.4b deterministic isolated test exit")


def test_child_budget_cutoff_is_incomplete_without_report() -> None:
    logger.info("R14.4b child cutoff test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=9)
    result = run_isolated_locked_trials_v2(limits=limits)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "evaluation-limit"
    assert result.report is None and result.report_digest is None
    logger.info("R14.4b child cutoff test exit")


def test_combined_child_output_cutoff_is_incomplete() -> None:
    logger.info("R14.4b combined output cutoff test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=1)
    result = run_isolated_locked_trials_v2(limits=limits)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "trial-worker-output"
    assert result.report is None
    logger.info("R14.4b combined output cutoff test exit")


def test_lower_uniform_completing_limits_preserve_report() -> None:
    logger.info("R14.4b lower complete limits test entry")
    limits = replace(
        DEFAULT_BUDGET_LIMITS,
        candidate_limit=1,
        canonical_bytes_limit=108,
        evaluation_limit=10,
    )
    result = run_isolated_locked_trials_v2(limits=limits)
    assert result.status is SynthesisStatus.FOUND
    assert result.report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    logger.info("R14.4b lower complete limits test exit")


def test_invalid_parent_input_never_spawns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4b invalid pre-spawn test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("spawned-invalid-trial")

    monkeypatch.setattr(isolated_module.subprocess, "Popen", forbidden)
    forged = replace(DEFAULT_LOCKED_WINNER_V2, ordinal=0)
    result = run_isolated_locked_trials_v2(winner=forged)
    assert result.status is SynthesisStatus.INVALID
    assert result.detail == "invalid-isolated-trial-request"
    logger.info("R14.4b invalid pre-spawn test exit")
