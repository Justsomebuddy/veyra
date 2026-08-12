"""Portable replay and authentication controls for issue-18 composition exports."""

from __future__ import annotations

from dataclasses import replace
import json
import logging
from pathlib import Path

import pytest

from src.core.claim_composition import (
    ClaimCompositionError,
    authenticated_composition_export_from_json,
    authenticated_composition_export_json,
    build_authenticated_composition_export,
    build_composition_public_export,
    build_composition_receipt,
    build_signed_composition_export,
    composition_public_export_from_json,
    composition_public_export_json,
    validate_authenticated_composition_export,
    validate_composition_public_export,
    validate_signed_composition_export,
)
from src.core.proof_core_codec import canonical_json

from test_claim_composition import _positive_case

logger = logging.getLogger(__name__)


def _export_case(tmp_path: Path):
    logger.debug("_export_case entry")
    tmp_path.mkdir(parents=True, exist_ok=True)
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    export = build_composition_public_export(receipt, sources, target, license)
    logger.debug("_export_case exit")
    return sources, export


def test_complete_export_round_trips_only_with_original_sources(tmp_path: Path) -> None:
    """Canonical decoding replays target, license, assessment, and receipt against sources."""
    logger.debug("test_complete_export_round_trips_only_with_original_sources entry")
    sources, export = _export_case(tmp_path)
    payload = composition_public_export_json(export, sources)
    decoded = composition_public_export_from_json(payload, sources)
    assert decoded == export
    assert validate_composition_public_export(decoded, sources)
    assert decoded.receipt.p2_promotion_established is False

    other_sources = tuple(reversed(sources))
    with pytest.raises(ClaimCompositionError, match="public-export-replay"):
        composition_public_export_from_json(payload, other_sources)
    logger.debug("test_complete_export_round_trips_only_with_original_sources exit")


def test_export_rejects_noncanonical_extra_and_forged_assessment(tmp_path: Path) -> None:
    """Transport shape drift and semantic digest forgery fail before public acceptance."""
    logger.debug("test_export_rejects_noncanonical_extra_and_forged_assessment entry")
    sources, export = _export_case(tmp_path)
    payload = composition_public_export_json(export, sources)
    parsed = json.loads(payload)
    parsed["unexpected"] = True
    with pytest.raises(ClaimCompositionError, match="public-export-format"):
        composition_public_export_from_json(canonical_json(parsed), sources)
    with pytest.raises(ClaimCompositionError, match="public-export-format"):
        composition_public_export_from_json(json.dumps(json.loads(payload), indent=2), sources)

    forged = replace(
        export,
        assessment=replace(
            export.assessment,
            aggregate_claim_licensed=type(
                export.assessment.aggregate_claim_licensed
            ).NOT_ESTABLISHED,
        ),
    )
    assert not validate_composition_public_export(forged, sources)
    logger.debug("test_export_rejects_noncanonical_extra_and_forged_assessment exit")


def test_hmac_envelope_binds_every_composition_root_and_round_trips(tmp_path: Path) -> None:
    """HMAC binds exact export bytes and roots but never changes the P2 nonpromotion bit."""
    logger.debug("test_hmac_envelope_binds_every_composition_root_and_round_trips entry")
    sources, export = _export_case(tmp_path)
    key = b"k" * 32
    envelope = build_authenticated_composition_export(export, sources, "issue-18-test", key)
    payload = authenticated_composition_export_json(envelope)
    decoded = authenticated_composition_export_from_json(payload)
    assert decoded == envelope
    assert validate_authenticated_composition_export(decoded, export, sources, key)
    assert not validate_authenticated_composition_export(decoded, export, sources, b"z" * 32)
    assert not validate_authenticated_composition_export(
        replace(decoded, license_digest="0" * 64),
        export,
        sources,
        key,
    )
    assert export.receipt.p2_promotion_established is False
    logger.debug("test_hmac_envelope_binds_every_composition_root_and_round_trips exit")


def test_ed25519_envelope_binds_validated_export_when_backend_available(tmp_path: Path) -> None:
    """Ed25519 signing has the same byte-binding, non-truth semantics as HMAC."""
    logger.debug("test_ed25519_envelope_binds_validated_export_when_backend_available entry")
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    sources, export = _export_case(tmp_path)
    private = Ed25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_bytes = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    envelope = build_signed_composition_export(export, sources, "issue-18-test", private_bytes)
    assert validate_signed_composition_export(envelope, export, sources, public_bytes)
    assert not validate_signed_composition_export(envelope, export, sources, b"z" * 32)
    logger.debug("test_ed25519_envelope_binds_validated_export_when_backend_available exit")
