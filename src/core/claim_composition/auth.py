"""Authenticated root binding for a validated composition public export."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import hmac
import json
import logging
from typing import NoReturn

from ..proof_core_codec import canonical_json, digest_data, exact_keys, load_canonical
from .export import validate_composition_public_export
from .protocol import ClaimCompositionError
from .types import (
    COMPOSITION_AUTH_BOUNDARY,
    COMPOSITION_AUTH_SCHEMA,
    AuthenticatedCompositionExport,
    ClaimCompositionSource,
    CompositionAuthentication,
    CompositionPublicExport,
)

logger = logging.getLogger(__name__)

MAX_COMPOSITION_AUTH_BYTES = 32_768
_MIN_KEY_BYTES = 32
_MAX_KEY_BYTES = 4096
_MAX_SIGNER_BYTES = 512
_ENVELOPE_DOMAIN = "veyra.claim-composition.authenticated-export-payload.v1"
_AUTH_DOMAIN = b"veyra.claim-composition.authenticated-export-hmac.v1\0"
_SIGNATURE_DOMAIN = b"veyra.claim-composition.authenticated-export-ed25519.v1\0"
_HEX = frozenset("0123456789abcdef")


def build_authenticated_composition_export(
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
    signer_id: str,
    key: bytes,
) -> AuthenticatedCompositionExport:
    """Bind a freshly replayed export and all composition roots with HMAC-SHA256."""
    logger.debug("build_authenticated_composition_export entry")
    _validate_export_and_signer(export, sources, signer_id)
    _validate_hmac_key(key)
    draft = _envelope_draft(export, signer_id, CompositionAuthentication.HMAC_SHA256)
    envelope_digest = digest_data(_envelope_payload_data(draft), _ENVELOPE_DOMAIN)
    result = replace(
        draft,
        envelope_digest=envelope_digest,
        authentication_tag=hmac.new(
            key,
            _AUTH_DOMAIN + envelope_digest.encode("ascii"),
            sha256,
        ).hexdigest(),
    )
    logger.info("build_authenticated_composition_export state=AUTHENTICATED truth=False")
    logger.debug("build_authenticated_composition_export exit")
    return result


def build_signed_composition_export(
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
    signer_id: str,
    private_key: bytes,
) -> AuthenticatedCompositionExport:
    """Bind a freshly replayed export and all composition roots with Ed25519."""
    logger.debug("build_signed_composition_export entry")
    _validate_export_and_signer(export, sources, signer_id)
    _validate_ed25519_key(private_key, "private-key")
    draft = _envelope_draft(export, signer_id, CompositionAuthentication.ED25519)
    envelope_digest = digest_data(_envelope_payload_data(draft), _ENVELOPE_DOMAIN)
    result = replace(
        draft,
        envelope_digest=envelope_digest,
        authentication_tag=_ed25519_sign(envelope_digest, private_key),
    )
    logger.info("build_signed_composition_export state=SIGNED truth=False")
    logger.debug("build_signed_composition_export exit")
    return result


def validate_authenticated_composition_export(
    envelope: object,
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
    key: bytes,
) -> bool:
    """Verify source-backed export identity, exact root binding, and HMAC."""
    logger.debug("validate_authenticated_composition_export entry type=%s", type(envelope).__name__)
    try:
        _validate_hmac_key(key)
        if type(envelope) is not AuthenticatedCompositionExport:
            logger.debug("validate_authenticated_composition_export exit valid=False")
            return False
        checked = envelope
        valid = (
            checked.authentication is CompositionAuthentication.HMAC_SHA256
            and _validate_envelope_shape(checked)
            and _envelope_links_export(checked, export, sources)
        )
        if valid:
            expected_digest = digest_data(_envelope_payload_data(checked), _ENVELOPE_DOMAIN)
            expected_tag = hmac.new(
                key,
                _AUTH_DOMAIN + expected_digest.encode("ascii"),
                sha256,
            ).hexdigest()
            valid = hmac.compare_digest(checked.envelope_digest, expected_digest) and hmac.compare_digest(
                checked.authentication_tag,
                expected_tag,
            )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_authenticated_composition_export rejected")
        valid = False
    logger.debug("validate_authenticated_composition_export exit valid=%s", valid)
    return valid


def validate_signed_composition_export(
    envelope: object,
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
    public_key: bytes,
) -> bool:
    """Verify source-backed export identity, exact root binding, and Ed25519 signature."""
    logger.debug("validate_signed_composition_export entry type=%s", type(envelope).__name__)
    try:
        _validate_ed25519_key(public_key, "public-key")
        if type(envelope) is not AuthenticatedCompositionExport:
            logger.debug("validate_signed_composition_export exit valid=False")
            return False
        checked = envelope
        valid = (
            checked.authentication is CompositionAuthentication.ED25519
            and _validate_envelope_shape(checked)
            and _envelope_links_export(checked, export, sources)
        )
        if valid:
            expected_digest = digest_data(_envelope_payload_data(checked), _ENVELOPE_DOMAIN)
            valid = hmac.compare_digest(checked.envelope_digest, expected_digest) and _ed25519_verify(
                expected_digest,
                checked.authentication_tag,
                public_key,
            )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_signed_composition_export rejected")
        valid = False
    logger.debug("validate_signed_composition_export exit valid=%s", valid)
    return valid


def authenticated_composition_export_json(envelope: AuthenticatedCompositionExport) -> str:
    """Serialize one exact-shaped authentication envelope as canonical JSON."""
    logger.debug("authenticated_composition_export_json entry")
    if not _validate_envelope_shape(envelope):
        _reject("composition-auth-shape")
    result = canonical_json(_envelope_data(envelope))
    if len(result.encode("utf-8")) > MAX_COMPOSITION_AUTH_BYTES:
        _reject("composition-auth-size")
    logger.debug("authenticated_composition_export_json exit bytes=%d", len(result.encode("utf-8")))
    return result


def authenticated_composition_export_from_json(text: str) -> AuthenticatedCompositionExport:
    """Decode exact canonical envelope JSON under a hard byte cap."""
    logger.debug("authenticated_composition_export_from_json entry type=%s", type(text).__name__)
    if type(text) is not str or len(text) > MAX_COMPOSITION_AUTH_BYTES:
        _reject("composition-auth-size")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        raise ClaimCompositionError("composition-auth-format") from exc
    if len(encoded) > MAX_COMPOSITION_AUTH_BYTES:
        _reject("composition-auth-size")
    try:
        row = exact_keys(
            load_canonical(text),
            {
                "schema_version",
                "export_payload_digest",
                "composition_receipt_digest",
                "license_digest",
                "assessment_digest",
                "signer_id",
                "authentication",
                "envelope_digest",
                "authentication_tag",
                "boundary",
            },
        )
        result = AuthenticatedCompositionExport(
            row["schema_version"],
            row["export_payload_digest"],
            row["composition_receipt_digest"],
            row["license_digest"],
            row["assessment_digest"],
            row["signer_id"],
            CompositionAuthentication(row["authentication"]),
            row["envelope_digest"],
            row["authentication_tag"],
            row["boundary"],
        )
    except (json.JSONDecodeError, KeyError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("authenticated_composition_export_from_json rejected type=%s", type(exc).__name__)
        raise ClaimCompositionError("composition-auth-format") from exc
    if not _validate_envelope_shape(result):
        _reject("composition-auth-shape")
    logger.debug("authenticated_composition_export_from_json exit")
    return result


def _envelope_draft(
    export: CompositionPublicExport,
    signer_id: str,
    authentication: CompositionAuthentication,
) -> AuthenticatedCompositionExport:
    logger.debug("_envelope_draft entry authentication=%s", authentication.value)
    result = AuthenticatedCompositionExport(
        COMPOSITION_AUTH_SCHEMA,
        export.payload_digest,
        export.receipt.receipt_digest,
        export.license.license_digest,
        export.assessment.assessment_digest,
        signer_id,
        authentication,
        "",
        "",
        COMPOSITION_AUTH_BOUNDARY,
    )
    logger.debug("_envelope_draft exit")
    return result


def _validate_export_and_signer(
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
    signer_id: str,
) -> None:
    logger.debug("_validate_export_and_signer entry")
    if not validate_composition_public_export(export, sources) or not _text_valid(signer_id):
        _reject("composition-auth-input")
    logger.debug("_validate_export_and_signer exit")


def _envelope_links_export(
    envelope: AuthenticatedCompositionExport,
    export: CompositionPublicExport,
    sources: tuple[ClaimCompositionSource, ...],
) -> bool:
    logger.debug("_envelope_links_export entry")
    valid = (
        validate_composition_public_export(export, sources)
        and envelope.export_payload_digest == export.payload_digest
        and envelope.composition_receipt_digest == export.receipt.receipt_digest
        and envelope.license_digest == export.license.license_digest
        and envelope.assessment_digest == export.assessment.assessment_digest
    )
    logger.debug("_envelope_links_export exit valid=%s", valid)
    return valid


def _validate_envelope_shape(value: object) -> bool:
    logger.debug("_validate_envelope_shape entry type=%s", type(value).__name__)
    valid = (
        type(value) is AuthenticatedCompositionExport
        and value.schema_version == COMPOSITION_AUTH_SCHEMA
        and value.boundary == COMPOSITION_AUTH_BOUNDARY
        and _text_valid(value.signer_id)
        and type(value.authentication) is CompositionAuthentication
        and all(
            _is_digest(item)
            for item in (
                value.export_payload_digest,
                value.composition_receipt_digest,
                value.license_digest,
                value.assessment_digest,
                value.envelope_digest,
            )
        )
        and _authentication_tag_valid(value.authentication, value.authentication_tag)
    )
    logger.debug("_validate_envelope_shape exit valid=%s", valid)
    return valid


def _envelope_payload_data(value: AuthenticatedCompositionExport) -> dict[str, object]:
    logger.debug("_envelope_payload_data entry")
    result: dict[str, object] = {
        "schema_version": value.schema_version,
        "export_payload_digest": value.export_payload_digest,
        "composition_receipt_digest": value.composition_receipt_digest,
        "license_digest": value.license_digest,
        "assessment_digest": value.assessment_digest,
        "signer_id": value.signer_id,
        "authentication": value.authentication.value,
        "boundary": value.boundary,
    }
    logger.debug("_envelope_payload_data exit")
    return result


def _envelope_data(value: AuthenticatedCompositionExport) -> dict[str, object]:
    logger.debug("_envelope_data entry")
    result = {
        **_envelope_payload_data(value),
        "envelope_digest": value.envelope_digest,
        "authentication_tag": value.authentication_tag,
    }
    logger.debug("_envelope_data exit")
    return result


def _validate_hmac_key(key: bytes) -> None:
    logger.debug("_validate_hmac_key entry type=%s", type(key).__name__)
    if type(key) is not bytes or not _MIN_KEY_BYTES <= len(key) <= _MAX_KEY_BYTES:
        _reject("composition-auth-key")
    logger.debug("_validate_hmac_key exit")


def _validate_ed25519_key(key: bytes, reason: str) -> None:
    logger.debug("_validate_ed25519_key entry reason=%s", reason)
    if type(key) is not bytes or len(key) != 32:
        _reject(reason)
    logger.debug("_validate_ed25519_key exit")


def _ed25519_sign(payload_digest: str, private_key: bytes) -> str:
    logger.debug("_ed25519_sign entry")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        signer = Ed25519PrivateKey.from_private_bytes(private_key)
        result = signer.sign(_SIGNATURE_DOMAIN + payload_digest.encode("ascii")).hex()
    except ImportError as exc:
        raise ClaimCompositionError("signing-backend-unavailable") from exc
    except (TypeError, ValueError) as exc:
        raise ClaimCompositionError("private-key") from exc
    logger.debug("_ed25519_sign exit")
    return result


def _ed25519_verify(payload_digest: str, signature_hex: str, public_key: bytes) -> bool:
    logger.debug("_ed25519_verify entry")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        verifier = Ed25519PublicKey.from_public_bytes(public_key)
        verifier.verify(bytes.fromhex(signature_hex), _SIGNATURE_DOMAIN + payload_digest.encode("ascii"))
    except ImportError as exc:
        raise ClaimCompositionError("signing-backend-unavailable") from exc
    except (InvalidSignature, TypeError, ValueError):
        logger.error("_ed25519_verify invalid signature")
        return False
    logger.debug("_ed25519_verify exit valid=True")
    return True


def _authentication_tag_valid(authentication: CompositionAuthentication, tag: object) -> bool:
    logger.debug("_authentication_tag_valid entry")
    if authentication is CompositionAuthentication.HMAC_SHA256:
        valid = _is_digest(tag)
    elif authentication is CompositionAuthentication.ED25519:
        valid = type(tag) is str and len(tag) == 128 and all(item in _HEX for item in tag)
    else:
        valid = False
    logger.debug("_authentication_tag_valid exit valid=%s", valid)
    return valid


def _text_valid(value: object) -> bool:
    logger.debug("_text_valid entry type=%s", type(value).__name__)
    valid = (
        type(value) is str
        and bool(value)
        and "\x00" not in value
        and len(value.encode("utf-8")) <= _MAX_SIGNER_BYTES
    )
    logger.debug("_text_valid exit valid=%s", valid)
    return valid


def _is_digest(value: object) -> bool:
    logger.debug("auth._is_digest entry type=%s", type(value).__name__)
    valid = type(value) is str and len(value) == 64 and all(item in _HEX for item in value)
    logger.debug("auth._is_digest exit valid=%s", valid)
    return valid


def _reject(reason: str) -> NoReturn:
    logger.error("composition authentication rejected reason=%s", reason)
    raise ClaimCompositionError(reason)
