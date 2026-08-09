"""Tests for the non-promotional Sage intrinsic-VAM presentation."""

from __future__ import annotations

import json

import pytest

from src.core.certify_types import Certificate
from veyra_sage import intrinsic_vam
from veyra_sage.all import VeyraIntrinsicVamLab


def _certificate(*, passed: bool = True) -> Certificate:
    return Certificate(
        "intrinsic_vam_r12",
        "R12.1-R12.5 replay",
        passed,
        "theorems=9 lanes=4 vami_frames=4",
        2,
    )


def test_lab_constructor_runs_one_core_certificate(monkeypatch):
    calls = 0

    def fake_certificate() -> Certificate:
        nonlocal calls
        calls += 1
        return _certificate()

    monkeypatch.setattr(
        intrinsic_vam,
        "certify_intrinsic_vam_r12",
        fake_certificate,
    )
    lab = VeyraIntrinsicVamLab()
    assert calls == 1
    assert lab.summary()["passed"] is True
    assert calls == 1


def test_presentation_is_json_ready_and_keeps_exact_nonclaims(monkeypatch):
    monkeypatch.setattr(
        intrinsic_vam,
        "certify_intrinsic_vam_r12",
        _certificate,
    )
    row = VeyraIntrinsicVamLab().certificate_row()
    assert row["schema"] == intrinsic_vam.SAGE_INTRINSIC_VAM_SCHEMA
    assert row["certificate"] == "intrinsic_vam_r12"
    assert (row["theorems"], row["lanes"], row["vami_frames"]) == (9, 4, 4)
    assert row["capability"] == "preserves"
    assert row["evidence"] == "formal-bridge"
    assert row["scope"] == "general"
    assert row["presentation_only"] is True
    assert row["evidence_accepted"] is False
    assert row["promotion_ready"] is False
    assert row["taxonomy_changed"] is False
    assert row["proof_complete"] is False
    assert row["boundary"] == (
        "presentation of core certificate, not independent evidence "
        "or promotion contract"
    )
    assert json.loads(json.dumps(row, sort_keys=True)) == row


def test_presentation_returns_fresh_rows(monkeypatch):
    monkeypatch.setattr(
        intrinsic_vam,
        "certify_intrinsic_vam_r12",
        _certificate,
    )
    lab = VeyraIntrinsicVamLab()
    first = lab.certificate_row()
    first["promotion_ready"] = True
    assert lab.summary()["promotion_ready"] is False


def test_private_presentation_rejects_wrong_or_subclassed_certificates():
    class HostileCertificate(Certificate):
        pass

    with pytest.raises(TypeError):
        intrinsic_vam._intrinsic_vam_presentation(
            HostileCertificate(*_certificate().__dict__.values())
        )
    with pytest.raises(ValueError):
        intrinsic_vam._intrinsic_vam_presentation(
            Certificate("other", "method", True, "detail", 2)
        )
    with pytest.raises(ValueError):
        intrinsic_vam._intrinsic_vam_presentation(
            Certificate("intrinsic_vam_r12", "method", 1, "detail", 2)
        )


def test_failed_core_certificate_stays_failed_presentation():
    row = intrinsic_vam._intrinsic_vam_presentation(
        _certificate(passed=False)
    )
    assert row["passed"] is False
    assert row["evidence_accepted"] is False
    assert row["promotion_ready"] is False
