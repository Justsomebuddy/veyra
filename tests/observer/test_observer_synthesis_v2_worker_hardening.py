"""Adversarial trust and bootstrap regressions for the R14.2b worker."""
from __future__ import annotations

from dataclasses import replace
import logging
import os
from pathlib import Path
import signal
import subprocess
from typing import Any

import pytest

from src.core import observer_synthesis_v2_worker as worker_module
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS
from src.core.observer_synthesis_v2_corpus import EXPECTED_DEFAULT_CORPUS_DIGEST
from src.core.observer_synthesis_v2_grammar import EXPECTED_DEFAULT_CATALOG_DIGEST
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.observer_synthesis_v2_worker import run_observer_cegis_worker_v2
from src.core.observer_synthesis_v2_worker_codec import result_payload_v2
from src.core.observer_synthesis_v2_worker_types import (
    WORKER_REQUEST_SCHEMA,
    ObserverWorkerRequestV2,
)
from src.core.observer_synthesis_v2_worker_validation import (
    EXPECTED_TRAIN_DIGESTS,
    EXPECTED_TRAIN_IDS,
    parse_result_payload_v2,
    validate_complete_result_data_v2,
    validate_worker_request_v2,
)
from src.core.proof_core_codec import load_canonical
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)
FAULT_ENTRY = PROJECT_ROOT / "tests" / "fixtures" / "observer_worker_fault.py"


@pytest.fixture
def worker_request() -> ObserverWorkerRequestV2:
    logger.debug("hardening worker request fixture entry")
    result = ObserverWorkerRequestV2(
        WORKER_REQUEST_SCHEMA,
        EXPECTED_DEFAULT_CATALOG_DIGEST,
        EXPECTED_DEFAULT_CORPUS_DIGEST,
        EXPECTED_TRAIN_IDS,
        EXPECTED_TRAIN_DIGESTS,
        DEFAULT_BUDGET_LIMITS,
    )
    logger.debug("hardening worker request fixture exit")
    return result


def _install_fault_child(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> list[subprocess.Popen[bytes]]:
    logger.debug("_install_fault_child entry mode=%s", mode)
    original = worker_module.subprocess.Popen
    captured: list[subprocess.Popen[bytes]] = []

    def fault_spawn(args: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        child_args = list(args)
        child_args[4] = str(FAULT_ENTRY)
        env = dict(kwargs["env"])
        env["VEYRA_WORKER_FAULT_MODE"] = mode
        kwargs["env"] = env
        proc = original(child_args, **kwargs)
        captured.append(proc)
        return proc

    monkeypatch.setattr(worker_module.subprocess, "Popen", fault_spawn)
    logger.debug("_install_fault_child exit")
    return captured


def test_request_tuple_items_are_shape_gated_before_equality(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b request equality-hook regression entry")

    class EqualId:
        def __eq__(self, other: object) -> bool:
            raise AssertionError(f"hostile equality reached: {other!r}")

    forged = replace(worker_request, train_case_ids=(EqualId(), 102))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid-worker-request-binding"):
        validate_worker_request_v2(forged)
    logger.info("R14.2b request equality-hook regression exit")


def test_bool_winner_and_impossible_exhaustion_are_rejected(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b complete result strict-shape regression entry")
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.report_canonical is not None
    report = load_canonical(result.report_canonical.decode())
    bool_winner = dict(report)
    bool_winner["winner"] = dict(report["winner"], ordinal=True)
    with pytest.raises(ValueError, match="invalid-worker-winner"):
        validate_complete_result_data_v2(bool_winner, worker_request)
    extra_winner = dict(report)
    extra_winner["winner"] = dict(report["winner"], extra="forged")
    with pytest.raises(ValueError, match="invalid-worker-winner"):
        validate_complete_result_data_v2(extra_winner, worker_request)
    exhausted = dict(report, status="EXHAUSTED", winner=None, traversed_candidates=1565)
    with pytest.raises(ValueError, match="worker-report-not-complete"):
        validate_complete_result_data_v2(exhausted, worker_request)
    logger.info("R14.2b complete result strict-shape regression exit")


def test_child_noncomplete_status_reason_matrix_is_closed(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b child status matrix regression entry")
    for status, detail in (
        (SynthesisStatus.INCOMPLETE, "invented-cutoff"),
        (SynthesisStatus.INVALID, "invalid-worker-request"),
        (SynthesisStatus.EXHAUSTED, "invented-exhaustion"),
    ):
        payload = result_payload_v2(status, detail, None)
        with pytest.raises(ValueError):
            parse_result_payload_v2(payload, worker_request)
    nested = b"[" * 1_000 + b"0" + b"]" * 1_000
    with pytest.raises(ValueError, match="invalid-worker-result-shape"):
        parse_result_payload_v2(nested, worker_request)
    logger.info("R14.2b child status matrix regression exit")


def test_lower_complete_budget_has_request_specific_valid_trace(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b lowered complete budget regression entry")
    limited = replace(
        worker_request,
        limits=replace(DEFAULT_BUDGET_LIMITS, candidate_limit=1565),
    )
    result = run_observer_cegis_worker_v2(limited)
    assert result.status is SynthesisStatus.FOUND
    assert result.report_canonical is not None
    logger.info("R14.2b lowered complete budget regression exit")


@pytest.mark.parametrize("failure_call", (1, 2))
def test_pipe_bootstrap_failures_are_incomplete_and_close_fds(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
    failure_call: int,
) -> None:
    logger.info("R14.2b pipe bootstrap regression entry call=%d", failure_call)
    original = worker_module.os.pipe
    allocated: list[int] = []
    calls = 0

    def failing_pipe() -> tuple[int, int]:
        nonlocal calls
        calls += 1
        if calls == failure_call:
            raise OSError("injected-pipe-failure")
        pair = original()
        allocated.extend(pair)
        return pair

    monkeypatch.setattr(worker_module.os, "pipe", failing_pipe)
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-runtime"
    for fd in allocated:
        with pytest.raises(OSError):
            os.fstat(fd)
    logger.info("R14.2b pipe bootstrap regression exit call=%d", failure_call)


def test_production_child_disables_site_bootstrap(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2b no-site bootstrap regression entry")
    original = worker_module.subprocess.Popen
    observed: list[str] = []

    def checked_spawn(args: list[str], **kwargs: Any) -> object:
        observed.extend(args)
        return original(args, **kwargs)

    monkeypatch.setattr(worker_module.subprocess, "Popen", checked_spawn)
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.status is SynthesisStatus.FOUND
    assert "-E" in observed and "-s" in observed and "-S" in observed
    logger.info("R14.2b no-site bootstrap regression exit")


@pytest.mark.parametrize("mode", ("as-check", "allocation", "signal"))
def test_real_limited_child_faults_are_incomplete(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    logger.info("R14.2b limited fault child entry mode=%s", mode)
    captured = _install_fault_child(monkeypatch, mode)
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-child"
    assert len(captured) == 1 and captured[0].poll() is not None
    expected_code = 73 if mode == "allocation" else -signal.SIGKILL
    assert captured[0].returncode == expected_code
    logger.info("R14.2b limited fault child exit mode=%s", mode)


def test_wall_hang_kills_and_reaps_process_group(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2b hanging group regression entry")
    captured = _install_fault_child(monkeypatch, "hang-group")
    limited = replace(
        worker_request,
        limits=replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1),
    )
    result = run_observer_cegis_worker_v2(limited)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-wall"
    assert len(captured) == 1 and captured[0].poll() is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[0].pid, 0)
    logger.info("R14.2b hanging group regression exit")


@pytest.mark.parametrize("mode", ("partial", "multiple"))
def test_fault_child_partial_or_multiple_frame_never_completes(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    logger.info("R14.2b framed fault regression entry mode=%s", mode)
    captured = _install_fault_child(monkeypatch, mode)
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.report_canonical is None
    proc = captured[0]
    assert proc.poll() is not None
    assert proc.stdin is not None and proc.stdin.closed
    assert proc.stdout is not None and proc.stdout.closed
    assert proc.stderr is not None and proc.stderr.closed
    logger.info("R14.2b framed fault regression exit mode=%s", mode)
