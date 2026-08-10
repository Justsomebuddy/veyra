"""Canonical HMAC-authenticated or Ed25519-signed replay receipts."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import hmac
import json
import logging
from typing import NoReturn

from ..ledger.store import validate_one_shot_receipt
from ..ledger.types import (
    OneShotLedgerReceipt,
    OneShotLedgerState,
    OneShotOutcome,
)
from .types import (
    AUTHENTICATED_REPLAY_BOUNDARY,
    AuthenticatedReplayPackage,
    ReplayAuthentication,
    ReplayEnvironment,
    ReplayEvidenceRoots,
    ReplayPackageKind,
)
from ...proof_core_codec import canonical_json, digest_data, load_canonical

logger = logging.getLogger(__name__)

_PACKAGE_SCHEMA = "veyra.observer-confirmation.authenticated-replay.v1"
_PAYLOAD_DOMAIN = "veyra.observer-confirmation.replay-payload.v1"
_AUTH_DOMAIN = b"veyra.observer-confirmation.replay-authentication.v1\0"
_SIGNATURE_DOMAIN = b"veyra.observer-confirmation.replay-signature.v1\0"
_MAX_PACKAGE_BYTES = 1_000_000
_MAX_TEXT_BYTES = 512
_MAX_TRANSPORT_RECEIPTS = 64
_MIN_KEY_BYTES = 32
_MAX_KEY_BYTES = 4096
_HEX = frozenset("0123456789abcdef")


class AuthenticatedReplayError(ValueError):
    """Stable replay construction/decoding failure without key disclosure."""

    def __init__(self, reason: str) -> None:
        logger.error("AuthenticatedReplayError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def build_authenticated_replay(
    evidence: ReplayEvidenceRoots,
    environment: ReplayEnvironment,
    signer_id: str,
    key: bytes,
    ledger_receipt: OneShotLedgerReceipt,
) -> AuthenticatedReplayPackage:
    """Build one canonical shared-key authenticated package from terminal roots."""
    logger.debug("build_authenticated_replay entry")
    _validate_evidence(evidence)
    _validate_environment(environment)
    _bounded_text(signer_id, "signer-id")
    _validate_key(key)
    _link_terminal_ledger(evidence, ledger_receipt)
    draft = AuthenticatedReplayPackage(
        _PACKAGE_SCHEMA,
        ReplayPackageKind.AUDIT_RECEIPT,
        evidence,
        environment,
        signer_id,
        ReplayAuthentication.HMAC_SHA256,
        "",
        "",
        AUTHENTICATED_REPLAY_BOUNDARY,
    )
    payload_digest = digest_data(_payload_data(draft), _PAYLOAD_DOMAIN)
    tag = _authentication_tag(payload_digest, key)
    result = replace(draft, payload_digest=payload_digest, authentication_tag=tag)
    logger.info("build_authenticated_replay state=AUTHENTICATED")
    logger.debug("build_authenticated_replay exit")
    return result


def build_signed_replay(
    evidence: ReplayEvidenceRoots,
    environment: ReplayEnvironment,
    signer_id: str,
    private_key: bytes,
    ledger_receipt: OneShotLedgerReceipt,
) -> AuthenticatedReplayPackage:
    """Build one canonical Ed25519-signed root-only replay receipt."""
    logger.debug("build_signed_replay entry")
    _validate_evidence(evidence)
    _validate_environment(environment)
    _bounded_text(signer_id, "signer-id")
    _validate_ed25519_key(private_key, "private-key")
    _link_terminal_ledger(evidence, ledger_receipt)
    draft = AuthenticatedReplayPackage(
        _PACKAGE_SCHEMA,
        ReplayPackageKind.AUDIT_RECEIPT,
        evidence,
        environment,
        signer_id,
        ReplayAuthentication.ED25519,
        "",
        "",
        AUTHENTICATED_REPLAY_BOUNDARY,
    )
    payload_digest = digest_data(_payload_data(draft), _PAYLOAD_DOMAIN)
    signature = _ed25519_sign(payload_digest, private_key)
    result = replace(draft, payload_digest=payload_digest, authentication_tag=signature)
    logger.info("build_signed_replay state=SIGNED")
    logger.debug("build_signed_replay exit")
    return result


def validate_authenticated_replay(
    package: object,
    key: bytes,
    *,
    ledger_receipt: OneShotLedgerReceipt | None = None,
) -> bool:
    """Verify exact shape, payload identity, HMAC, and optional terminal ledger link."""
    logger.debug("validate_authenticated_replay entry type=%s", type(package).__name__)
    try:
        _validate_key(key)
        if type(package) is not AuthenticatedReplayPackage:
            return False
        _validate_package_shape(package)
        if package.authentication is not ReplayAuthentication.HMAC_SHA256:
            return False
        expected_payload = digest_data(_payload_data(package), _PAYLOAD_DOMAIN)
        expected_tag = _authentication_tag(expected_payload, key)
        valid = hmac.compare_digest(package.payload_digest, expected_payload) and hmac.compare_digest(
            package.authentication_tag,
            expected_tag,
        )
        if valid and ledger_receipt is not None:
            _link_terminal_ledger(package.evidence, ledger_receipt)
    except (AttributeError, AuthenticatedReplayError, TypeError, ValueError):
        logger.error("validate_authenticated_replay rejected package")
        return False
    logger.debug("validate_authenticated_replay exit valid=%s", valid)
    return valid


def validate_signed_replay(
    package: object,
    public_key: bytes,
    *,
    ledger_receipt: OneShotLedgerReceipt | None = None,
) -> bool:
    """Verify canonical payload identity, Ed25519 signature, and optional ledger link."""
    logger.debug("validate_signed_replay entry type=%s", type(package).__name__)
    try:
        _validate_ed25519_key(public_key, "public-key")
        if type(package) is not AuthenticatedReplayPackage:
            return False
        _validate_package_shape(package)
        if package.authentication is not ReplayAuthentication.ED25519:
            return False
        expected_payload = digest_data(_payload_data(package), _PAYLOAD_DOMAIN)
        valid = hmac.compare_digest(package.payload_digest, expected_payload) and _ed25519_verify(
            expected_payload,
            package.authentication_tag,
            public_key,
        )
        if valid and ledger_receipt is not None:
            _link_terminal_ledger(package.evidence, ledger_receipt)
    except (AttributeError, AuthenticatedReplayError, TypeError, ValueError):
        logger.error("validate_signed_replay rejected package")
        return False
    logger.debug("validate_signed_replay exit valid=%s", valid)
    return valid


def authenticated_replay_json(package: AuthenticatedReplayPackage) -> str:
    """Serialize one already valid-shaped package into canonical portable JSON."""
    logger.debug("authenticated_replay_json entry")
    _validate_package_shape(package)
    result = canonical_json(_package_data(package))
    if len(result.encode("utf-8")) > _MAX_PACKAGE_BYTES:
        _reject("package-size")
    logger.debug("authenticated_replay_json exit bytes=%d", len(result.encode("utf-8")))
    return result


def authenticated_replay_from_json(text: str) -> AuthenticatedReplayPackage:
    """Decode only exact canonical v1 JSON under the hard package-size cap."""
    logger.debug("authenticated_replay_from_json entry type=%s", type(text).__name__)
    if type(text) is not str or len(text) > _MAX_PACKAGE_BYTES:
        _reject("package-size")
    try:
        encoded = text.encode("utf-8")
    except UnicodeError as exc:
        raise AuthenticatedReplayError("package-format") from exc
    if len(encoded) > _MAX_PACKAGE_BYTES:
        _reject("package-size")
    try:
        data = load_canonical(text)
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("authenticated_replay_from_json invalid encoding type=%s", type(exc).__name__)
        raise AuthenticatedReplayError("package-format") from exc
    package = _package_from_data(data)
    _validate_package_shape(package)
    logger.debug("authenticated_replay_from_json exit")
    return package


def _link_terminal_ledger(
    evidence: ReplayEvidenceRoots,
    receipt: OneShotLedgerReceipt,
) -> None:
    logger.debug("_link_terminal_ledger entry")
    common_link = (
        not validate_one_shot_receipt(receipt)
        or receipt.state not in {OneShotLedgerState.CONSUMED, OneShotLedgerState.FAILED}
        or receipt.reservation.parent_result != evidence.parent_result
        or receipt.reservation.test_commitment != evidence.test_commitment
        or receipt.reservation.schema_digest != evidence.schema_digest
        or receipt.reservation.evaluation_rows_digest != evidence.evaluation_rows_digest
        or receipt.reservation.observer_program_digest != evidence.observer_program_digest
        or receipt.reservation.confirmation_policy_digest != evidence.confirmation_policy_digest
        or receipt.receipt_digest != evidence.ledger_receipt_digest
    )
    worker_outcome = receipt.outcome in {
        OneShotOutcome.EVALUATION_COMPLETED,
        OneShotOutcome.WORKER_BLOCKED,
    }
    linked_outcome = evidence.worker_receipt_digest if worker_outcome else evidence.confirmation_result
    if common_link or receipt.outcome_digest != linked_outcome:
        _reject("ledger-link")
    logger.debug("_link_terminal_ledger exit")


def _validate_package_shape(package: AuthenticatedReplayPackage) -> None:
    logger.debug("_validate_package_shape entry")
    if (
        type(package) is not AuthenticatedReplayPackage
        or package.schema_version != _PACKAGE_SCHEMA
        or package.package_kind is not ReplayPackageKind.AUDIT_RECEIPT
        or type(package.authentication) is not ReplayAuthentication
        or not _text_valid(package.signer_id)
        or not _is_digest(package.payload_digest)
        or not _authentication_shape_valid(package.authentication, package.authentication_tag)
        or package.boundary != AUTHENTICATED_REPLAY_BOUNDARY
    ):
        _reject("package-shape")
    _validate_evidence(package.evidence)
    _validate_environment(package.environment)
    logger.debug("_validate_package_shape exit")


def _validate_evidence(evidence: ReplayEvidenceRoots) -> None:
    logger.debug("_validate_evidence entry type=%s", type(evidence).__name__)
    if type(evidence) is not ReplayEvidenceRoots:
        _reject("evidence-type")
    roots = (
        evidence.parent_result,
        evidence.confirmation_result,
        evidence.test_commitment,
        evidence.test_data,
        evidence.schema_digest,
        evidence.evaluation_rows_digest,
        evidence.observer_program_digest,
        evidence.confirmation_policy_digest,
        evidence.worker_receipt_digest,
        evidence.ledger_receipt_digest,
    )
    if (
        any(not _is_digest(value) for value in roots)
        or type(evidence.transport_receipt_digests) is not tuple
        or not 1 <= len(evidence.transport_receipt_digests) <= _MAX_TRANSPORT_RECEIPTS
        or any(not _is_digest(value) for value in evidence.transport_receipt_digests)
    ):
        _reject("evidence-shape")
    logger.debug("_validate_evidence exit")


def _validate_environment(environment: ReplayEnvironment) -> None:
    logger.debug("_validate_environment entry type=%s", type(environment).__name__)
    if (
        type(environment) is not ReplayEnvironment
        or not _text_valid(environment.implementation)
        or not _text_valid(environment.runtime_version)
        or not _text_valid(environment.platform)
        or not _text_valid(environment.worker_profile)
        or not _is_digest(environment.source_tree_digest)
    ):
        _reject("environment-shape")
    logger.debug("_validate_environment exit")


def _validate_key(key: bytes) -> None:
    logger.debug("_validate_key entry type=%s", type(key).__name__)
    if type(key) is not bytes or not _MIN_KEY_BYTES <= len(key) <= _MAX_KEY_BYTES:
        _reject("key-shape")
    logger.debug("_validate_key exit")


def _authentication_tag(payload_digest: str, key: bytes) -> str:
    logger.debug("_authentication_tag entry")
    result = hmac.new(key, _AUTH_DOMAIN + payload_digest.encode("ascii"), sha256).hexdigest()
    logger.debug("_authentication_tag exit")
    return result


def _validate_ed25519_key(key: bytes, reason: str) -> None:
    logger.debug("_validate_ed25519_key entry reason=%s type=%s", reason, type(key).__name__)
    if type(key) is not bytes or len(key) != 32:
        _reject(reason)
    logger.debug("_validate_ed25519_key exit reason=%s", reason)


def _ed25519_sign(payload_digest: str, private_key: bytes) -> str:
    logger.debug("_ed25519_sign entry")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        signer = Ed25519PrivateKey.from_private_bytes(private_key)
        signature = signer.sign(_SIGNATURE_DOMAIN + payload_digest.encode("ascii")).hex()
    except ImportError as exc:
        raise AuthenticatedReplayError("signing-backend-unavailable") from exc
    except (TypeError, ValueError) as exc:
        raise AuthenticatedReplayError("private-key") from exc
    logger.debug("_ed25519_sign exit")
    return signature


def _ed25519_verify(payload_digest: str, signature_hex: str, public_key: bytes) -> bool:
    logger.debug("_ed25519_verify entry")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        verifier = Ed25519PublicKey.from_public_bytes(public_key)
        verifier.verify(bytes.fromhex(signature_hex), _SIGNATURE_DOMAIN + payload_digest.encode("ascii"))
    except ImportError as exc:
        raise AuthenticatedReplayError("signing-backend-unavailable") from exc
    except (InvalidSignature, TypeError, ValueError):
        logger.error("_ed25519_verify invalid signature")
        return False
    logger.debug("_ed25519_verify exit valid=True")
    return True


def _authentication_shape_valid(authentication: ReplayAuthentication, tag: object) -> bool:
    logger.debug("_authentication_shape_valid entry authentication=%s", authentication.value)
    if authentication is ReplayAuthentication.HMAC_SHA256:
        valid = _is_digest(tag)
    elif authentication is ReplayAuthentication.ED25519:
        valid = type(tag) is str and len(tag) == 128 and all(character in _HEX for character in tag)
    else:
        valid = False
    logger.debug("_authentication_shape_valid exit valid=%s", valid)
    return valid


def _payload_data(package: AuthenticatedReplayPackage) -> dict[str, object]:
    logger.debug("_payload_data entry")
    result = {
        "schema_version": package.schema_version,
        "package_kind": package.package_kind.value,
        "evidence": _evidence_data(package.evidence),
        "environment": _environment_data(package.environment),
        "signer_id": package.signer_id,
        "authentication": package.authentication.value,
        "boundary": package.boundary,
    }
    logger.debug("_payload_data exit")
    return result


def _package_data(package: AuthenticatedReplayPackage) -> dict[str, object]:
    logger.debug("_package_data entry")
    result = {
        **_payload_data(package),
        "payload_digest": package.payload_digest,
        "authentication_tag": package.authentication_tag,
    }
    logger.debug("_package_data exit")
    return result


def _evidence_data(evidence: ReplayEvidenceRoots) -> dict[str, object]:
    logger.debug("_evidence_data entry")
    result = {
        "parent_result": evidence.parent_result,
        "confirmation_result": evidence.confirmation_result,
        "test_commitment": evidence.test_commitment,
        "test_data": evidence.test_data,
        "schema_digest": evidence.schema_digest,
        "evaluation_rows_digest": evidence.evaluation_rows_digest,
        "observer_program_digest": evidence.observer_program_digest,
        "confirmation_policy_digest": evidence.confirmation_policy_digest,
        "worker_receipt_digest": evidence.worker_receipt_digest,
        "ledger_receipt_digest": evidence.ledger_receipt_digest,
        "transport_receipt_digests": list(evidence.transport_receipt_digests),
    }
    logger.debug("_evidence_data exit")
    return result


def _environment_data(environment: ReplayEnvironment) -> dict[str, object]:
    logger.debug("_environment_data entry")
    result = {
        "implementation": environment.implementation,
        "runtime_version": environment.runtime_version,
        "platform": environment.platform,
        "worker_profile": environment.worker_profile,
        "source_tree_digest": environment.source_tree_digest,
    }
    logger.debug("_environment_data exit")
    return result


def _package_from_data(data: object) -> AuthenticatedReplayPackage:
    logger.debug("_package_from_data entry")
    expected = {
        "schema_version",
        "package_kind",
        "evidence",
        "environment",
        "signer_id",
        "authentication",
        "payload_digest",
        "authentication_tag",
        "boundary",
    }
    if type(data) is not dict or set(data) != expected:
        _reject("package-shape")
    evidence_data = data["evidence"]
    environment_data = data["environment"]
    evidence_keys = {
        "parent_result",
        "confirmation_result",
        "test_commitment",
        "test_data",
        "schema_digest",
        "evaluation_rows_digest",
        "observer_program_digest",
        "confirmation_policy_digest",
        "worker_receipt_digest",
        "ledger_receipt_digest",
        "transport_receipt_digests",
    }
    environment_keys = {
        "implementation",
        "runtime_version",
        "platform",
        "worker_profile",
        "source_tree_digest",
    }
    if (
        type(evidence_data) is not dict
        or set(evidence_data) != evidence_keys
        or type(environment_data) is not dict
        or set(environment_data) != environment_keys
        or type(evidence_data["transport_receipt_digests"]) is not list
    ):
        _reject("package-shape")
    try:
        evidence = ReplayEvidenceRoots(
            evidence_data["parent_result"],
            evidence_data["confirmation_result"],
            evidence_data["test_commitment"],
            evidence_data["test_data"],
            evidence_data["schema_digest"],
            evidence_data["evaluation_rows_digest"],
            evidence_data["observer_program_digest"],
            evidence_data["confirmation_policy_digest"],
            evidence_data["worker_receipt_digest"],
            evidence_data["ledger_receipt_digest"],
            tuple(evidence_data["transport_receipt_digests"]),
        )
        environment = ReplayEnvironment(**environment_data)
        result = AuthenticatedReplayPackage(
            data["schema_version"],
            ReplayPackageKind(data["package_kind"]),
            evidence,
            environment,
            data["signer_id"],
            ReplayAuthentication(data["authentication"]),
            data["payload_digest"],
            data["authentication_tag"],
            data["boundary"],
        )
    except (TypeError, ValueError) as exc:
        raise AuthenticatedReplayError("package-shape") from exc
    logger.debug("_package_from_data exit")
    return result


def _bounded_text(value: object, reason: str) -> None:
    logger.debug("_bounded_text entry reason=%s", reason)
    if not _text_valid(value):
        _reject(reason)
    logger.debug("_bounded_text exit reason=%s", reason)


def _text_valid(value: object) -> bool:
    logger.debug("_text_valid entry type=%s", type(value).__name__)
    try:
        result = (
            type(value) is str
            and bool(value)
            and len(value) <= _MAX_TEXT_BYTES
            and len(value.encode("utf-8")) <= _MAX_TEXT_BYTES
        )
    except UnicodeError:
        result = False
    logger.debug("_text_valid exit valid=%s", result)
    return result


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in _HEX for character in value)
    logger.debug("_is_digest exit valid=%s", result)
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("observer_discovery_replay rejected reason=%s", reason)
    raise AuthenticatedReplayError(reason)
