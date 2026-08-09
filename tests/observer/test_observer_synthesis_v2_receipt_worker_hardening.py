"""Adversarial validation and lifecycle tests for R14.5b receipts."""
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
from src.core.observer_synthesis_v2_budget import (
    DEFAULT_BUDGET_LIMITS,
    BudgetLimits,
)
from src.core.observer_synthesis_v2_receipt_codec import receipt_bundle_bytes_v2
from src.core.observer_synthesis_v2_receipt_worker import (
    build_receipt_request_v2,
    run_isolated_receipts_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_codec import (
    receipt_request_digest_v2,
    receipt_request_from_bytes_v2,
    receipt_result_payload_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_validation import (
    parse_receipt_result_payload_v2,
    validate_receipt_request_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_types import ReceiptWorkerRequestV2
from src.core.observer_synthesis_v2_receipts import (
    build_observer_synthesis_receipts_v2,
)
from src.core.observer_synthesis_v2_trial_worker import (
    run_isolated_locked_trials_v2,
)
from src.core.observer_synthesis_v2_trial_worker_types import (
    IsolatedObserverTrialResultV2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.observer_synthesis_v2_worker_codec import frame_bytes_v2
from src.core.observer_synthesis_v2_worker_runtime import FixedChildOutcomeV2
from src.core.proof_core_codec import canonical_json, load_canonical
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)
FAULT_ENTRY = PROJECT_ROOT / "tests" / "fixtures" / "observer_worker_fault.py"


@pytest.fixture(scope="module")
def isolated_trial() -> IsolatedObserverTrialResultV2:
    logger.info("R14.5b hardening trial fixture entry")
    result = run_isolated_locked_trials_v2()
    assert result.status is SynthesisStatus.FOUND
    logger.info("R14.5b hardening trial fixture exit")
    return result


def _valid_payload(
    trial: IsolatedObserverTrialResultV2,
) -> tuple[bytes, ReceiptWorkerRequestV2]:
    logger.debug("_valid_payload entry")
    request = build_receipt_request_v2(trial)
    bundle = receipt_bundle_bytes_v2(build_observer_synthesis_receipts_v2())
    payload = receipt_result_payload_v2(
        SynthesisStatus.FOUND,
        "receipt-complete",
        receipt_request_digest_v2(request),
        request.limits_digest,
        bundle,
    )
    logger.debug("_valid_payload exit bytes=%d", len(payload))
    return payload, request


def test_trial_result_transplants_are_rejected_before_spawn(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b trial transplant test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("spawned-transplanted-trial")

    monkeypatch.setattr(worker_module.subprocess, "Popen", forbidden)
    for forged in (
        replace(isolated_trial, report_digest="0" * 64),
        replace(isolated_trial, status=SynthesisStatus.INCOMPLETE),
        replace(isolated_trial, detail="invented"),
    ):
        result = run_isolated_receipts_v2(forged)
        assert result.status is SynthesisStatus.INVALID
        assert result.detail == "invalid-isolated-receipt-request"
    deleted = replace(isolated_trial)
    object.__delattr__(deleted, "report")
    result = run_isolated_receipts_v2(deleted)
    assert result.status is SynthesisStatus.INVALID
    assert result.detail == "invalid-isolated-receipt-request"
    logger.info("R14.5b trial transplant test exit")


def test_deleted_request_and_nested_limit_slots_are_invalid(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b deleted request test entry")
    request = build_receipt_request_v2(isolated_trial)
    for field in ("trial_payload", "manifest_digest", "limits", "limits_digest"):
        malformed = replace(request)
        object.__delattr__(malformed, field)
        with pytest.raises(ValueError, match="invalid-receipt-request"):
            validate_receipt_request_v2(malformed)
    limits = BudgetLimits()
    object.__delattr__(limits, "candidate_limit")
    with pytest.raises(ValueError, match="invalid-receipt-request-shape"):
        validate_receipt_request_v2(replace(request, limits=limits))
    logger.info("R14.5b deleted request test exit")


def test_hostile_request_field_never_reaches_equality(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b hostile equality test entry")

    class Hostile:
        def __eq__(self, other: object) -> bool:
            raise AssertionError(f"hostile equality reached: {other!r}")

    request = build_receipt_request_v2(isolated_trial)
    forged = replace(request, trial_report_digest=Hostile())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid-receipt-request-fields"):
        validate_receipt_request_v2(forged)
    logger.info("R14.5b hostile equality test exit")


def test_request_and_result_hostile_nesting_is_typed_invalid(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b hostile nesting test entry")
    nested = b"[" * 1_000 + b"0" + b"]" * 1_000
    with pytest.raises(ValueError, match="invalid-receipt-request-canonical"):
        receipt_request_from_bytes_v2(nested)
    request = build_receipt_request_v2(isolated_trial)
    with pytest.raises(ValueError, match="invalid-receipt-result-canonical"):
        parse_receipt_result_payload_v2(nested, request)
    logger.info("R14.5b hostile nesting test exit")


def test_result_parser_resnapshots_request_and_rejects_bundle_mutation(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b parser resnapshot test entry")
    payload, request = _valid_payload(isolated_trial)
    malformed = replace(request)
    object.__delattr__(malformed, "trial_payload")
    with pytest.raises(ValueError, match="invalid-receipt-request"):
        parse_receipt_result_payload_v2(payload, malformed)
    envelope = load_canonical(payload.decode())
    bundle = envelope["bundle"]
    envelope["bundle"] = ("x" if bundle[0] != "x" else "y") + bundle[1:]
    with pytest.raises(ValueError, match="invalid-receipt-bundle-pins"):
        parse_receipt_result_payload_v2(canonical_json(envelope).encode(), request)
    transplanted = build_receipt_request_v2(
        isolated_trial,
        replace(DEFAULT_BUDGET_LIMITS, candidate_limit=1),
    )
    with pytest.raises(ValueError, match="invalid-receipt-result-binding"):
        parse_receipt_result_payload_v2(payload, transplanted)
    logger.info("R14.5b parser resnapshot test exit")


def test_closed_terminal_matrix_rejects_exhausted_and_invented(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b terminal matrix test entry")
    request = build_receipt_request_v2(isolated_trial)
    for status, detail in (
        (SynthesisStatus.EXHAUSTED, "invented"),
        (SynthesisStatus.INCOMPLETE, "invented"),
        (SynthesisStatus.INVALID, "invented"),
    ):
        payload = receipt_result_payload_v2(
            status,
            detail,
            receipt_request_digest_v2(request),
            request.limits_digest,
            None,
        )
        with pytest.raises(ValueError):
            parse_receipt_result_payload_v2(payload, request)
    logger.info("R14.5b terminal matrix test exit")


def test_parent_maps_malformed_framed_result_to_invalid(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b malformed child result test entry")
    nested = b"[" * 1_000 + b"0" + b"]" * 1_000
    monkeypatch.setattr(
        worker_module,
        "run_fixed_child_v2",
        lambda *_args, **_kwargs: FixedChildOutcomeV2("ok", frame_bytes_v2(nested)),
    )
    result = run_isolated_receipts_v2(isolated_trial)
    assert result.status is SynthesisStatus.INVALID
    assert result.detail == "invalid-receipt-worker-result"
    assert result.bundle_bytes is None
    logger.info("R14.5b malformed child result test exit")


def test_receipt_child_groups_are_reaped_on_success_and_wall(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b residual group test entry")
    original = worker_module.subprocess.Popen
    captured: list[subprocess.Popen[bytes]] = []
    mode = "success-fork"

    def fault_spawn(args: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        child_args = list(args)
        child_args[4] = str(FAULT_ENTRY)
        kwargs["env"] = dict(kwargs["env"], VEYRA_WORKER_FAULT_MODE=mode)
        proc = original(child_args, **kwargs)
        captured.append(proc)
        return proc

    monkeypatch.setattr(worker_module.subprocess, "Popen", fault_spawn)
    first = run_isolated_receipts_v2(isolated_trial)
    assert first.detail == "invalid-receipt-worker-result"
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[-1].pid, 0)
    mode = "ignore-term-group"
    limited = replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1)
    second = run_isolated_receipts_v2(isolated_trial, limited)
    assert second.detail == "receipt-worker-wall"
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[-1].pid, 0)
    logger.info("R14.5b residual group test exit")


def test_reduced_stdin_pipe_is_deadline_bounded_and_reaped(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b reduced stdin pipe test entry")
    original = worker_module.subprocess.Popen
    captured: list[subprocess.Popen[bytes]] = []

    def reduced_pipe_spawn(
        args: list[str],
        **kwargs: Any,
    ) -> subprocess.Popen[bytes]:
        proc = original(args, **kwargs)
        assert proc.stdin is not None
        fcntl.fcntl(proc.stdin.fileno(), fcntl.F_SETPIPE_SZ, 4096)
        captured.append(proc)
        return proc

    monkeypatch.setattr(worker_module.subprocess, "Popen", reduced_pipe_spawn)
    started = time.monotonic()
    result = run_isolated_receipts_v2(
        isolated_trial,
        replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1),
    )
    elapsed = time.monotonic() - started
    assert result.status is SynthesisStatus.FOUND
    assert elapsed < 3.0
    assert len(captured) == 1 and captured[0].poll() is not None
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[0].pid, 0)
    logger.info("R14.5b reduced stdin pipe test exit elapsed=%.3f", elapsed)
