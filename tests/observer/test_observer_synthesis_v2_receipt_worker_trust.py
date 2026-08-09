"""TOCTOU and precharge-order regressions for isolated R14.5b receipts."""
from __future__ import annotations

from dataclasses import replace
import fcntl
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Any

import pytest

from src.core import observer_synthesis_v2_receipt_worker as worker_module
from src.core import observer_synthesis_v2_receipt_worker_validation as validation_module
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetLimitExceeded,
)
from src.core.observer_synthesis_v2_receipt_worker import (
    build_receipt_request_v2,
    run_isolated_receipts_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
)
from src.core.observer_synthesis_v2_receipt_worker_execution import (
    build_precharged_receipt_bytes_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_validation import (
    validate_receipt_request_v2,
)
from src.core.observer_synthesis_v2_trial_worker import run_isolated_locked_trials_v2
from src.core.observer_synthesis_v2_trial_worker_types import (
    IsolatedObserverTrialResultV2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)
FAULT_ENTRY = PROJECT_ROOT / "tests" / "fixtures" / "observer_worker_fault.py"


@pytest.fixture(scope="module")
def isolated_trial() -> IsolatedObserverTrialResultV2:
    logger.info("R14.5b trust trial fixture entry")
    result = run_isolated_locked_trials_v2()
    assert result.status is SynthesisStatus.FOUND
    logger.info("R14.5b trust trial fixture exit")
    return result


def test_hostile_isolated_terminal_never_reaches_equality(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b hostile terminal equality test entry")

    class Hostile:
        def __eq__(self, other: object) -> bool:
            raise AssertionError(f"hostile terminal equality reached: {other!r}")

    monkeypatch.setattr(
        worker_module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("spawned hostile terminal"),
    )
    for field in ("schema", "detail", "report_digest"):
        forged = replace(isolated_trial, **{field: Hostile()})
        result = run_isolated_receipts_v2(forged)
        assert result.status is SynthesisStatus.INVALID
        assert result.detail == "invalid-isolated-receipt-request"
    logger.info("R14.5b hostile terminal equality test exit")


def test_nondefault_upstream_trial_limits_never_spawn(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b upstream limits binding test entry")
    monkeypatch.setattr(
        worker_module.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("spawned nondefault upstream limits"),
    )
    for digest in ("", "junk", "0" * 64):
        forged = replace(isolated_trial, limits_digest=digest)
        result = run_isolated_receipts_v2(forged)
        assert result.status is SynthesisStatus.INVALID
        assert result.detail == "invalid-isolated-receipt-request"
    logger.info("R14.5b upstream limits binding test exit")


def test_request_snapshot_blocks_midparse_payload_mutation(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b request TOCTOU test entry")
    request = build_receipt_request_v2(isolated_trial)
    original = request.trial_payload
    mutated = b"x" * len(original)
    parser = validation_module.trial_report_from_payload_v2

    def mutating_parser(payload: object) -> object:
        object.__setattr__(request, "trial_payload", mutated)
        return parser(payload)

    monkeypatch.setattr(
        validation_module,
        "trial_report_from_payload_v2",
        mutating_parser,
    )
    validated = validate_receipt_request_v2(request)
    assert validated.request.trial_payload == original
    assert validated.request.trial_payload != request.trial_payload
    with pytest.raises(ValueError, match="invalid-receipt-request-payload-digest"):
        validate_receipt_request_v2(request)
    logger.info("R14.5b request TOCTOU test exit")


def test_low_output_precharge_never_invokes_receipt_builder(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b output precharge ordering test entry")
    assert isolated_trial.report is not None

    def forbidden(_trial: object) -> object:
        raise AssertionError("builder-ran-before-output-precharge")

    limits = replace(
        DEFAULT_BUDGET_LIMITS,
        transcript_output_bytes_limit=EXPECTED_BUNDLE_BYTES - 1,
    )
    with pytest.raises(BudgetLimitExceeded) as exc_info:
        build_precharged_receipt_bytes_v2(
            isolated_trial.report,
            limits,
            forbidden,  # type: ignore[arg-type]
        )
    assert exc_info.value.reason.value == "transcript-output-bytes-limit"
    logger.info("R14.5b output precharge ordering test exit")


def test_nonreader_small_pipe_hits_wall_and_reaps_group(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b nonreader small-pipe test entry")
    original = worker_module.subprocess.Popen
    captured: list[subprocess.Popen[bytes]] = []

    def nonreader_spawn(
        args: list[str],
        **kwargs: Any,
    ) -> subprocess.Popen[bytes]:
        child_args = list(args)
        child_args[4] = str(FAULT_ENTRY)
        kwargs["env"] = dict(kwargs["env"], VEYRA_WORKER_FAULT_MODE="hang-group")
        proc = original(child_args, **kwargs)
        assert proc.stdin is not None
        fcntl.fcntl(proc.stdin.fileno(), fcntl.F_SETPIPE_SZ, 4096)
        captured.append(proc)
        return proc

    monkeypatch.setattr(worker_module.subprocess, "Popen", nonreader_spawn)
    started = time.monotonic()
    result = run_isolated_receipts_v2(
        isolated_trial,
        replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1),
    )
    elapsed = time.monotonic() - started
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "receipt-worker-wall"
    assert elapsed < 3.0
    assert len(captured) == 1 and captured[0].poll() is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[0].pid, 0)
    logger.info("R14.5b nonreader small-pipe test exit elapsed=%.3f", elapsed)
