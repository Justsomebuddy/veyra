"""Exact level-3 certificate checks for the finite R14 aggregate."""
from __future__ import annotations

from pathlib import Path

import pytest

import src.core.certify_observer_synthesis_v2 as cert_module
from src.core.certify_observer_synthesis_v2 import (
    R14_CERTIFICATE_DETAIL,
    R14_CERTIFICATE_METHOD,
    certify_observer_synthesis_v2_r14,
)
from src.core.observer_synthesis_v2_pipeline_types import (
    OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
    ObserverSynthesisEvidenceV2,
    ObserverSynthesisPipelineResultV2,
)
from src.core.observer_synthesis_v2_pipeline import PIPELINE_BOUNDARY
from src.core.observer_synthesis_v2_types import SynthesisStatus
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_lean


def _success() -> ObserverSynthesisPipelineResultV2:
    """Build the exact aggregate DTO without replaying its six children."""
    evidence = ObserverSynthesisEvidenceV2(
        "07dbfe7567f86a2817bd01317ceb14e8c8650fd2ed488a7e1a6a7aad5f890f48",
        "4de40e8fdc41475c7e2f39d4370aecb0447e1b73b0254d723d17b1dc49221317",
        "56287ca10c7de90bb04bb4794ad6fb455511675304357031370b76866531dba9",
        "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb",
        "7a9511755e8d00c5e91de1bc137b7e310876d06cf8ce8ea08164a588264b07cb",
        27_857,
        "0afbd94886cef42dc5dda3a3b923f7766948bc53a32fca7481a1b861a3b54720",
        "740f55aa23a8372d01db506e1019cbab2bdb5990796c6c3b158ec048286b0895",
        5,
        10,
        8,
        8,
        0,
        2,
        10,
        (2, 4, 25, 5),
        36,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        PIPELINE_BOUNDARY,
    )
    return ObserverSynthesisPipelineResultV2(
        OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
        SynthesisStatus.FOUND,
        "observer-synthesis-v2-aggregate-complete",
        evidence,
    )


def test_certificate_runs_aggregate_once_and_is_explicitly_finite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def once() -> ObserverSynthesisPipelineResultV2:
        nonlocal calls
        calls += 1
        return _success()

    monkeypatch.setattr(
        cert_module,
        "run_observer_synthesis_v2_pipeline",
        once,
    )
    certificate = certify_observer_synthesis_v2_r14()
    assert calls == 1
    assert certificate.name == "observer_synthesis_v2_r14"
    assert certificate.method == R14_CERTIFICATE_METHOD
    assert certificate.detail == R14_CERTIFICATE_DETAIL
    assert certificate.level == 3
    assert certificate.passed is True
    assert "finite executable" in certificate.method
    assert "not a theorem" in certificate.method
    assert "formal proof" in certificate.method
    assert "R8 evidence" in certificate.method


def test_certificate_fails_closed_on_incomplete_or_wrong_aggregate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incomplete = ObserverSynthesisPipelineResultV2(
        OBSERVER_SYNTHESIS_V2_PIPELINE_SCHEMA,
        SynthesisStatus.INCOMPLETE,
        "aggregate-receipt-incomplete",
        None,
    )
    monkeypatch.setattr(
        cert_module,
        "run_observer_synthesis_v2_pipeline",
        lambda: incomplete,
    )
    assert certify_observer_synthesis_v2_r14().passed is False
    monkeypatch.setattr(
        cert_module,
        "run_observer_synthesis_v2_pipeline",
        lambda: object(),
    )
    blocked = certify_observer_synthesis_v2_r14()
    assert blocked.passed is False
    assert blocked.detail.startswith("blocked=TypeError:")


def test_certificate_is_registered_exactly_once() -> None:
    text = (PROJECT_ROOT / "src/core/certify.py").read_text()
    assert text.count("certify_observer_synthesis_v2_r14,") == 1
    assert text.count(
        "from .certify_observer_synthesis_v2 import "
        "certify_observer_synthesis_v2_r14"
    ) == 1


class _EqualityBomb:
    def __eq__(self, _: object) -> bool:
        raise AssertionError("hostile equality must not run")


def test_certificate_rejects_hostile_deleted_numeric_and_boundary_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hostile = _success()
    assert hostile.evidence is not None
    object.__setattr__(hostile.evidence, "trial_report_digest", _EqualityBomb())
    monkeypatch.setattr(cert_module, "run_observer_synthesis_v2_pipeline", lambda: hostile)
    assert certify_observer_synthesis_v2_r14().passed is False
    numeric = _success()
    assert numeric.evidence is not None
    object.__setattr__(numeric.evidence, "subjects", 5.0)
    monkeypatch.setattr(cert_module, "run_observer_synthesis_v2_pipeline", lambda: numeric)
    assert certify_observer_synthesis_v2_r14().passed is False
    boundary = _success()
    assert boundary.evidence is not None
    object.__setattr__(boundary.evidence, "boundary", "not a theorem; formal proof; R8 evidence")
    monkeypatch.setattr(cert_module, "run_observer_synthesis_v2_pipeline", lambda: boundary)
    assert certify_observer_synthesis_v2_r14().passed is False
    deleted = _success()
    object.__delattr__(deleted, "status")
    monkeypatch.setattr(cert_module, "run_observer_synthesis_v2_pipeline", lambda: deleted)
    assert certify_observer_synthesis_v2_r14().passed is False
