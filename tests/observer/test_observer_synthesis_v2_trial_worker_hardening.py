"""Adversarial R14.4b child payload and lifecycle regressions."""
from __future__ import annotations

from dataclasses import replace
import logging
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest

from src.core import observer_synthesis_v2_trial_worker as isolated_module
from src.core.observer_synthesis_v2_trial import run_locked_trials_v2
from src.core.observer_synthesis_v2_trial_worker import (
    build_trial_subject_requests_v2,
    run_isolated_locked_trials_v2,
)
from src.core.observer_synthesis_v2_budget import DEFAULT_BUDGET_LIMITS, BudgetLimits
from src.core.observer_synthesis_v2_trial_worker_codec import (
    full_subject_data_v2,
    trial_subject_request_digest_v2,
    trial_subject_result_payload_v2,
)
from src.core.observer_synthesis_v2_trial_worker_types import (
    TrialSubjectWorkerRequestV2,
)
from src.core.observer_synthesis_v2_trial_worker_validation import (
    parse_trial_subject_result_payload_v2,
    validate_trial_subject_request_v2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.observer_synthesis_v2_worker_runtime import run_fixed_child_v2
from src.core.proof_core_codec import canonical_json, load_canonical
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_linux

logger = logging.getLogger(__name__)
FAULT_ENTRY = PROJECT_ROOT / "tests" / "fixtures" / "observer_worker_fault.py"


def _valid_payload(index: int = 0) -> tuple[bytes, TrialSubjectWorkerRequestV2]:
    logger.debug("_valid_payload entry index=%d", index)
    request = build_trial_subject_requests_v2()[index]
    subject = run_locked_trials_v2().subjects[index]
    payload = trial_subject_result_payload_v2(
        SynthesisStatus.FOUND,
        "trial-subject-complete",
        trial_subject_request_digest_v2(request),
        request.limits_digest,
        subject,
    )
    logger.debug("_valid_payload exit bytes=%d", len(payload))
    return payload, request


def test_valid_full_payload_is_freshly_rebuilt() -> None:
    logger.info("R14.4b full payload validation test entry")
    payload, request = _valid_payload()
    parsed = parse_trial_subject_result_payload_v2(payload, request)
    expected = run_locked_trials_v2().subjects[0]
    assert parsed.status is SynthesisStatus.FOUND
    assert parsed.subject == expected
    assert parsed.subject is not expected
    assert parsed.subject is not None and parsed.subject.cases is not expected.cases
    logger.info("R14.4b full payload validation test exit")


@pytest.mark.parametrize("mutation", ("bool", "order", "outcome", "accounting"))
def test_mutated_complete_subject_is_invalid(mutation: str) -> None:
    logger.info("R14.4b mutated payload test entry mutation=%s", mutation)
    payload, request = _valid_payload()
    envelope = load_canonical(payload.decode())
    subject = dict(envelope["subject"])
    if mutation == "bool":
        subject["required_total"] = True
    elif mutation == "order":
        subject["cases"] = list(reversed(subject["cases"]))
    elif mutation == "outcome":
        rows = [dict(row) for row in subject["cases"]]
        rows[0]["outcome_digest"] = "0" * 64
        subject["cases"] = rows
    else:
        subject["accounting"] = dict(subject["accounting"], evaluations=9)
    envelope["subject"] = subject
    forged = canonical_json(envelope).encode()
    with pytest.raises(ValueError):
        parse_trial_subject_result_payload_v2(forged, request)
    logger.info("R14.4b mutated payload test exit mutation=%s", mutation)


def test_cross_subject_and_limits_transplants_are_invalid() -> None:
    logger.info("R14.4b transplant test entry")
    payload, first = _valid_payload(0)
    second = build_trial_subject_requests_v2()[1]
    with pytest.raises(ValueError):
        parse_trial_subject_result_payload_v2(payload, second)
    envelope = load_canonical(payload.decode())
    envelope["limits_digest"] = "0" * 64
    with pytest.raises(ValueError):
        parse_trial_subject_result_payload_v2(canonical_json(envelope).encode(), first)
    logger.info("R14.4b transplant test exit")


def test_request_shape_gates_hostile_items_before_equality() -> None:
    logger.info("R14.4b equality hook test entry")

    class EqualId:
        def __eq__(self, other: object) -> bool:
            raise AssertionError(f"hostile equality reached: {other!r}")

    request = build_trial_subject_requests_v2()[0]
    forged = replace(
        request,
        case_ids=(EqualId(),) + request.case_ids[1:],  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="invalid-trial-subject-request-items"):
        validate_trial_subject_request_v2(forged)
    logger.info("R14.4b equality hook test exit")


def test_deleted_request_and_limit_slots_map_to_invalid() -> None:
    logger.info("R14.4b deleted request slot test entry")
    for field in ("subject_id", "case_ids", "limits"):
        request = replace(build_trial_subject_requests_v2()[0])
        object.__delattr__(request, field)
        with pytest.raises(ValueError, match="invalid-trial-subject-request"):
            validate_trial_subject_request_v2(request)
    request = build_trial_subject_requests_v2()[0]
    limits = BudgetLimits()
    object.__delattr__(limits, "candidate_limit")
    with pytest.raises(ValueError, match="invalid-trial-subject-request-limits"):
        validate_trial_subject_request_v2(replace(request, limits=limits))
    logger.info("R14.4b deleted request slot test exit")


def test_result_parser_resnapshots_deleted_request_slots() -> None:
    logger.info("R14.4b parser request snapshot test entry")
    request = build_trial_subject_requests_v2()[0]
    payload = trial_subject_result_payload_v2(
        SynthesisStatus.INCOMPLETE,
        "evaluation-limit",
        trial_subject_request_digest_v2(request),
        request.limits_digest,
        None,
    )
    for field in ("subject_id", "case_ids", "limits", "limits_digest"):
        malformed = replace(request)
        object.__delattr__(malformed, field)
        with pytest.raises(ValueError, match="invalid-trial-subject-request"):
            parse_trial_subject_result_payload_v2(payload, malformed)
    logger.info("R14.4b parser request snapshot test exit")


def test_result_parser_maps_hostile_nesting_to_typed_invalid() -> None:
    logger.info("R14.4b parser hostile nesting test entry")
    request = build_trial_subject_requests_v2()[0]
    payload = b"[" * 1_000 + b"0" + b"]" * 1_000
    with pytest.raises(ValueError, match="invalid-trial-subject-result-shape"):
        parse_trial_subject_result_payload_v2(payload, request)
    logger.info("R14.4b parser hostile nesting test exit")


def test_closed_child_status_matrix_rejects_exhausted_and_invented() -> None:
    logger.info("R14.4b child status matrix test entry")
    request = build_trial_subject_requests_v2()[0]
    for status, detail in (
        (SynthesisStatus.EXHAUSTED, "invented"),
        (SynthesisStatus.INCOMPLETE, "invented"),
    ):
        payload = trial_subject_result_payload_v2(
            status,
            detail,
            trial_subject_request_digest_v2(request),
            request.limits_digest,
            None,
        )
        with pytest.raises(ValueError):
            parse_trial_subject_result_payload_v2(payload, request)
    logger.info("R14.4b child status matrix test exit")


def test_prlimit_mismatch_never_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4b prlimit mismatch test entry")
    monkeypatch.setattr(isolated_module, "_apply_limits", lambda _pid, _limit: False)
    result = run_isolated_locked_trials_v2()
    assert result.status is SynthesisStatus.INCOMPLETE
    assert result.detail == "trial-worker-limit-bootstrap"
    assert result.report is None
    logger.info("R14.4b prlimit mismatch test exit")


def test_generic_runtime_kills_residual_groups_on_success_and_wall(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.4b residual group test entry")
    original = isolated_module.subprocess.Popen
    captured: list[subprocess.Popen[bytes]] = []
    mode = "success-fork"

    def fault_spawn(args: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        child_args = list(args)
        child_args[4] = str(FAULT_ENTRY)
        kwargs["env"] = dict(kwargs["env"], VEYRA_WORKER_FAULT_MODE=mode)
        proc = original(child_args, **kwargs)
        captured.append(proc)
        return proc

    monkeypatch.setattr(isolated_module.subprocess, "Popen", fault_spawn)
    first = run_isolated_locked_trials_v2()
    assert first.detail == "invalid-trial-worker-result"
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[-1].pid, 0)
    mode = "ignore-term-group"
    limited = replace(DEFAULT_BUDGET_LIMITS, wall_seconds=1)
    second = run_isolated_locked_trials_v2(limits=limited)
    assert second.detail == "trial-worker-wall"
    with pytest.raises(ProcessLookupError):
        os.killpg(captured[-1].pid, 0)
    logger.info("R14.4b residual group test exit")


def test_generic_runtime_rejects_forged_entry_kind_before_spawn() -> None:
    logger.info("R14.4b fixed entry kind test entry")

    class ForgedKind:
        value = "observer_synthesis_v2_receipts.py"

    with pytest.raises(ValueError, match="invalid-fixed-worker-kind"):
        run_fixed_child_v2(
            ForgedKind(),  # type: ignore[arg-type]
            b"unused",
            DEFAULT_BUDGET_LIMITS,
            clock=lambda: 0,
        )
    logger.info("R14.4b fixed entry kind test exit")


def test_full_subject_codec_has_exact_complete_shape() -> None:
    logger.info("R14.4b full subject codec test entry")
    subject = run_locked_trials_v2().subjects[0]
    data = full_subject_data_v2(subject)
    assert isinstance(data["cases"], list) and len(data["cases"]) == 10
    assert isinstance(data["splits"], list) and len(data["splits"]) == 4
    assert data["subject_id"] == "synthesized-winner"
    logger.info("R14.4b full subject codec test exit")
