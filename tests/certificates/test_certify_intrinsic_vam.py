"""R12.6 integration-certificate tests and non-promotion boundaries."""

from __future__ import annotations

import logging
import pytest

import src.core.certify_intrinsic_vam as certificate_module
from src.core.certify_intrinsic_vam import (
    _formal_replay,
    _transport_replay,
    certify_intrinsic_vam_r12,
)
from src.core.intrinsic_vam_formal_effects import intrinsic_vam_formal_effect_digest
from src.core.intrinsic_vam_formal_lean_render import THEOREM_IDS
from src.core.intrinsic_vam_formal_manifest import (
    BRIDGE_ID,
    EXPECTED_BINDING_DIGEST,
    EXPECTED_R11_BINDING,
    EXPECTED_R12_5_TCB_DIGESTS,
    EXPECTED_SNAPSHOT_DIGEST,
    EXPECTED_TOOLCHAIN_IDENTITY,
    MANIFEST_BOUNDARY,
)
from src.core.intrinsic_vam_formal_objects import EXPECTED_R12_5_OBJECTS
from src.core.intrinsic_vam_formal_report import IntrinsicVamFormalBridgeReport
from src.core.shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from src.core.shadow_effects import shadow_effect_registry_digest

pytestmark = pytest.mark.requires_lean

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def intrinsic_certificate():
    """Run the expensive public R12.6 certificate only once in this module."""
    LOGGER.info("R12.6 certificate fixture start")
    result = certify_intrinsic_vam_r12()
    LOGGER.info("R12.6 certificate fixture exit passed=%s", result.passed)
    return result


def _checked_stub() -> IntrinsicVamFormalBridgeReport:
    """Build an exact-shape report for call-count isolation without Lean replay."""
    LOGGER.debug("R12.6 checked report stub entry")
    result = IntrinsicVamFormalBridgeReport(
        "checked",
        BRIDGE_ID,
        THEOREM_IDS,
        EXPECTED_R11_BINDING,
        tuple(EXPECTED_R12_5_TCB_DIGESTS.items()),
        tuple(EXPECTED_R12_5_OBJECTS.items()),
        EXPECTED_SNAPSHOT_DIGEST,
        shadow_effect_registry_digest(),
        intrinsic_vam_formal_effect_digest(),
        BridgeCapability.PRESERVES,
        EvidenceClass.FORMAL_BRIDGE,
        EvidenceScope.GENERAL,
        EXPECTED_BINDING_DIGEST,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        EXPECTED_TOOLCHAIN_IDENTITY,
        "compiled 9/9 theorem checks",
        MANIFEST_BOUNDARY,
    )
    LOGGER.debug("R12.6 checked report stub exit")
    return result


def test_intrinsic_certificate_is_level_two_integration_not_promotion(
    intrinsic_certificate,
) -> None:
    LOGGER.info("R12.6 positive certificate audit start")
    assert intrinsic_certificate.name == "intrinsic_vam_r12"
    assert intrinsic_certificate.level == 2
    assert intrinsic_certificate.passed is True
    assert "four-lane intrinsic IR/VAMI replay" in intrinsic_certificate.method
    assert "Lean preservation" in intrinsic_certificate.method
    assert "lanes=4/4" in intrinsic_certificate.detail
    assert "vami=4/4" in intrinsic_certificate.detail
    assert "theorems=9/9" in intrinsic_certificate.detail
    assert "sources=28/28" in intrinsic_certificate.detail
    assert "objects=9/9" in intrinsic_certificate.detail
    LOGGER.info("R12.6 positive certificate audit complete")


def test_four_transport_lanes_replay_through_four_vami_frames() -> None:
    LOGGER.info("R12.6 bounded transport replay start")
    passed, transports, frames = _transport_replay()
    assert passed is True
    assert len(transports) == len(frames) == 4
    assert all(type(frame) is bytes and frame.startswith(b"VAMI") for frame in frames)
    LOGGER.info("R12.6 bounded transport replay complete")


def test_formal_replay_calls_public_self_verifying_report_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    LOGGER.info("R12.6 single formal report call audit start")
    calls = 0
    report = _checked_stub()

    def one_report() -> IntrinsicVamFormalBridgeReport:
        nonlocal calls
        LOGGER.debug("R12.6 one-report stub entry")
        calls += 1
        LOGGER.debug("R12.6 one-report stub exit calls=%d", calls)
        return report

    monkeypatch.setattr(
        certificate_module,
        "intrinsic_vam_formal_bridge_report",
        one_report,
    )
    passed, data = _formal_replay()
    assert passed is True
    assert calls == 1
    assert data["promotion_ready"] is False
    assert data["taxonomy_changed"] is False
    LOGGER.info("R12.6 single formal report call audit complete")


def test_certificate_fails_closed_when_formal_replay_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    LOGGER.info("R12.6 blocked formal report audit start")
    monkeypatch.setattr(certificate_module, "_formal_replay", lambda: (False, {}))
    result = certify_intrinsic_vam_r12()
    assert result.passed is False
    assert result.name == "intrinsic_vam_r12"
    assert result.level == 2
    LOGGER.info("R12.6 blocked formal report audit complete")
