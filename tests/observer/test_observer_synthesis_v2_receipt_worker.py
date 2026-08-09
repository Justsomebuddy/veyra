"""Functional exact-vector tests for one isolated R14.5 receipt child."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import logging
import subprocess
from typing import Any

import pytest

from src.core import observer_synthesis_v2_receipt_worker as worker_module
from src.core import observer_synthesis_v2_receipts as receipts_module
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS
from src.core.observer_synthesis_v2_cegis_codec import limits_digest_v2
from src.core.observer_synthesis_v2_receipt_codec import receipt_bundle_bytes_v2
from src.core.observer_synthesis_v2_receipt_worker import (
    build_receipt_request_v2,
    run_isolated_receipts_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_codec import (
    EXPECTED_BUNDLE_BYTES,
    EXPECTED_BUNDLE_DIGEST,
    EXPECTED_BUNDLE_SHA256,
    receipt_request_bytes_v2,
    receipt_request_from_bytes_v2,
)
from src.core.observer_synthesis_v2_receipt_worker_trial import (
    TRIAL_PAYLOAD_BYTES,
    TRIAL_PAYLOAD_SHA256,
)
from src.core.observer_synthesis_v2_receipts import (
    build_observer_synthesis_receipts_v2,
    build_receipts_from_validated_trial_v2,
)
from src.core.observer_synthesis_v2_trial_worker import (
    run_isolated_locked_trials_v2,
)
from src.core.observer_synthesis_v2_trial_worker_types import (
    IsolatedObserverTrialResultV2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def isolated_trial() -> IsolatedObserverTrialResultV2:
    logger.info("R14.5b isolated trial fixture entry")
    result = run_isolated_locked_trials_v2()
    assert result.status is SynthesisStatus.FOUND
    logger.info("R14.5b isolated trial fixture exit")
    return result


def test_exact_request_is_canonical_and_bound(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b exact request test entry")
    request = build_receipt_request_v2(isolated_trial)
    encoded = receipt_request_bytes_v2(request)
    assert receipt_request_from_bytes_v2(encoded) == request
    assert len(request.trial_payload) == TRIAL_PAYLOAD_BYTES
    assert sha256(request.trial_payload).hexdigest() == TRIAL_PAYLOAD_SHA256
    assert request.limits_digest == limits_digest_v2(DEFAULT_BUDGET_LIMITS)
    assert request.limits_digest == (
        "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb"
    )
    logger.info("R14.5b exact request test exit")


def test_one_real_child_returns_exact_opaque_bundle(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b real child test entry")
    original = worker_module.subprocess.Popen
    spawns: list[subprocess.Popen[bytes]] = []
    limits_seen: list[int] = []
    original_limits = worker_module._apply_limits

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

    monkeypatch.setattr(worker_module.subprocess, "Popen", recording_spawn)
    monkeypatch.setattr(worker_module, "_apply_limits", recording_limits)
    result = run_isolated_receipts_v2(isolated_trial)
    assert result.status is SynthesisStatus.FOUND
    assert result.detail == "receipt-complete"
    assert len(spawns) == 1 and spawns[0].poll() is not None
    assert limits_seen == [DEFAULT_BUDGET_LIMITS.process_as_bytes_limit]
    assert result.bundle_bytes is not None
    assert len(result.bundle_bytes) == EXPECTED_BUNDLE_BYTES
    assert result.bundle_sha256 == EXPECTED_BUNDLE_SHA256
    assert result.bundle_digest == EXPECTED_BUNDLE_DIGEST
    logger.info("R14.5b real child test exit")


def test_pure_builder_does_not_call_trial_execution(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b pure builder test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("pure-builder-ran-trial")

    monkeypatch.setattr(receipts_module, "run_locked_trials_v2", forbidden)
    assert isolated_trial.report is not None
    bundle = build_receipts_from_validated_trial_v2(isolated_trial.report)
    assert len(receipt_bundle_bytes_v2(bundle)) == EXPECTED_BUNDLE_BYTES
    logger.info("R14.5b pure builder test exit")


def test_parent_never_rebuilds_receipt_semantics(
    isolated_trial: IsolatedObserverTrialResultV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.5b no parent semantics test entry")

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("parent-rebuilt-receipts")

    monkeypatch.setattr(
        receipts_module,
        "build_receipts_from_validated_trial_v2",
        forbidden,
    )
    result = run_isolated_receipts_v2(isolated_trial)
    assert result.status is SynthesisStatus.FOUND
    assert result.bundle_digest == EXPECTED_BUNDLE_DIGEST
    logger.info("R14.5b no parent semantics test exit")


def test_isolated_and_preserved_inprocess_api_are_byte_identical(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b preserved API identity test entry")
    isolated = run_isolated_receipts_v2(isolated_trial)
    expected = receipt_bundle_bytes_v2(build_observer_synthesis_receipts_v2())
    assert isolated.bundle_bytes == expected
    logger.info("R14.5b preserved API identity test exit")


def test_outer_output_cutoff_is_incomplete(
    isolated_trial: IsolatedObserverTrialResultV2,
) -> None:
    logger.info("R14.5b output cutoff test entry")
    limits = replace(DEFAULT_BUDGET_LIMITS, transcript_output_bytes_limit=1)
    result = run_isolated_receipts_v2(isolated_trial, limits)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "receipt-worker-output"
    assert result.bundle_bytes is None
    logger.info("R14.5b output cutoff test exit")


@pytest.mark.parametrize(
    ("limits", "detail"),
    (
        (
            replace(
                DEFAULT_BUDGET_LIMITS,
                canonical_bytes_limit=TRIAL_PAYLOAD_BYTES + EXPECTED_BUNDLE_BYTES - 1,
            ),
            "canonical-bytes-limit",
        ),
        (
            replace(DEFAULT_BUDGET_LIMITS, evaluation_limit=9),
            "evaluation-limit",
        ),
    ),
)
def test_lower_replay_work_limits_cannot_return_found(
    isolated_trial: IsolatedObserverTrialResultV2,
    limits: object,
    detail: str,
) -> None:
    logger.info("R14.5b replay precharge test entry detail=%s", detail)
    result = run_isolated_receipts_v2(isolated_trial, limits)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == detail
    assert result.bundle_bytes is None
    logger.info("R14.5b replay precharge test exit detail=%s", detail)
