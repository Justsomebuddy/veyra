"""R14.2b real child-process resource and framing regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging
import time
from typing import Any

import pytest

from src.core import observer_synthesis_v2_worker as worker_module
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS
from src.core.observer_synthesis_v2_corpus import EXPECTED_DEFAULT_CORPUS_DIGEST
from src.core.observer_synthesis_v2_grammar import EXPECTED_DEFAULT_CATALOG_DIGEST
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.observer_synthesis_v2_worker import run_observer_cegis_worker_v2
from src.core.observer_synthesis_v2_worker_codec import (
    frame_bytes_v2,
    request_bytes_v2,
    request_from_bytes_v2,
    result_payload_v2,
)
from src.core.observer_synthesis_v2_worker_types import (
    WORKER_REQUEST_SCHEMA,
    ObserverWorkerRequestV2,
)
from src.core.observer_synthesis_v2_worker_validation import (
    EXPECTED_TRAIN_DIGESTS,
    EXPECTED_TRAIN_IDS,
    parse_result_payload_v2,
)

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)


@pytest.fixture
def worker_request() -> ObserverWorkerRequestV2:
    logger.debug("worker request fixture entry")
    result = ObserverWorkerRequestV2(
        WORKER_REQUEST_SCHEMA,
        EXPECTED_DEFAULT_CATALOG_DIGEST,
        EXPECTED_DEFAULT_CORPUS_DIGEST,
        EXPECTED_TRAIN_IDS,
        EXPECTED_TRAIN_DIGESTS,
        DEFAULT_BUDGET_LIMITS,
    )
    logger.debug("worker request fixture exit")
    return result


def test_request_is_frozen_exact_and_byte_roundtrips(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b request codec test entry")
    encoded = request_bytes_v2(worker_request)
    assert request_from_bytes_v2(encoded) == worker_request
    assert frame_bytes_v2(encoded)[8:] == encoded
    with pytest.raises(FrozenInstanceError):
        worker_request.schema = "forged"  # type: ignore[misc]
    logger.info("R14.2b request codec test exit")


def test_real_worker_returns_deterministic_validated_found(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b real success test entry")
    first = run_observer_cegis_worker_v2(worker_request)
    second = run_observer_cegis_worker_v2(worker_request)
    assert first.status is second.status is SynthesisStatus.FOUND
    assert first.detail == second.detail == "first-train-satisfying-candidate"
    assert first.report_canonical == second.report_canonical
    assert first.report_digest == second.report_digest
    assert first.report_canonical is not None
    assert b"elapsed_ns" not in first.report_canonical
    assert b"pid" not in first.report_canonical
    assert b"signal" not in first.report_canonical
    logger.info("R14.2b real success test exit")


def test_malformed_request_is_invalid_without_spawning(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2b pre-spawn invalid test entry")

    def forbidden_spawn(*_args: object, **_kwargs: object) -> object:
        logger.error("forbidden_spawn called")
        raise AssertionError("spawned-malformed-request")

    monkeypatch.setattr(worker_module.subprocess, "Popen", forbidden_spawn)
    forged = replace(worker_request, catalog_digest="0" * 64)
    result = run_observer_cegis_worker_v2(forged)
    assert result.status is SynthesisStatus.INVALID
    assert result.detail == "invalid-worker-request"
    logger.info("R14.2b pre-spawn invalid test exit")


def test_candidate_cutoff_from_child_is_incomplete(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b child cutoff test entry")
    limited = replace(
        worker_request,
        limits=replace(DEFAULT_BUDGET_LIMITS, candidate_limit=1564),
    )
    result = run_observer_cegis_worker_v2(limited)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "candidate-limit"
    assert result.report_canonical is None
    logger.info("R14.2b child cutoff test exit")


def test_combined_output_overflow_kills_and_is_incomplete(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b output cutoff test entry")
    limited = replace(
        worker_request,
        limits=replace(
            DEFAULT_BUDGET_LIMITS,
            transcript_output_bytes_limit=1,
        ),
    )
    result = run_observer_cegis_worker_v2(limited)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-output"
    logger.info("R14.2b output cutoff test exit")


def test_prlimit_mismatch_never_sends_go(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2b prlimit mismatch test entry")
    monkeypatch.setattr(worker_module, "_apply_limits", lambda _pid, _limit: False)
    result = run_observer_cegis_worker_v2(worker_request)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-limit-bootstrap"
    logger.info("R14.2b prlimit mismatch test exit")


def test_wall_deadline_starts_before_spawn(
    worker_request: ObserverWorkerRequestV2,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.2b pre-spawn wall test entry")
    original = worker_module.subprocess.Popen
    original_write = worker_module.os.write
    go_writes: list[bytes] = []

    def delayed_spawn(*args: Any, **kwargs: Any) -> object:
        logger.debug("delayed_spawn entry")
        time.sleep(1.05)
        result = original(*args, **kwargs)
        logger.debug("delayed_spawn exit")
        return result

    monkeypatch.setattr(worker_module.subprocess, "Popen", delayed_spawn)

    def recording_write(fd: int, payload: bytes) -> int:
        if payload == b"G":
            go_writes.append(payload)
        return original_write(fd, payload)

    monkeypatch.setattr(worker_module.os, "write", recording_write)
    limited = replace(
        worker_request,
        limits=replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1),
    )
    result = run_observer_cegis_worker_v2(limited)
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "worker-wall"
    assert go_writes == []
    logger.info("R14.2b pre-spawn wall test exit")


@pytest.mark.parametrize("raw", (b"", b"\0" * 8, b"\0" * 7))
def test_partial_or_empty_result_is_never_accepted(raw: bytes) -> None:
    logger.info("R14.2b partial result test entry bytes=%d", len(raw))
    with pytest.raises((EOFError, ValueError)):
        worker_module._unframe_result(raw)
    logger.info("R14.2b partial result test exit")


def test_complete_status_with_malformed_report_is_invalid(
    worker_request: ObserverWorkerRequestV2,
) -> None:
    logger.info("R14.2b malformed complete result test entry")
    payload = result_payload_v2(
        SynthesisStatus.FOUND,
        "first-train-satisfying-candidate",
        None,
    )
    with pytest.raises(ValueError, match="invalid-worker-report-shape"):
        parse_result_payload_v2(payload, worker_request)
    logger.info("R14.2b malformed complete result test exit")
