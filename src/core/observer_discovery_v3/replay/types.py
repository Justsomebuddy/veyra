"""Immutable records for the authenticated observer replay package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReplayAuthentication(str, Enum):
    """Supported authentication profiles for canonical replay roots."""

    HMAC_SHA256 = "HMAC-SHA256-v1"
    ED25519 = "Ed25519-v1"


class ReplayPackageKind(str, Enum):
    """Current disclosure level; v1 ships roots rather than test objects."""

    AUDIT_RECEIPT = "AUDIT_RECEIPT"


AUTHENTICATED_REPLAY_BOUNDARY = (
    "root-only audit receipt, not independently executable full replay; authentication may use shared-key HMAC "
    "or optional Ed25519, while public-key identity and trust remain external; no trusted time or claim-truth proof"
)


@dataclass(frozen=True, slots=True)
class ReplayEvidenceRoots:
    """Exact evidence identities carried by one replay package."""

    parent_result: str
    confirmation_result: str
    test_commitment: str
    test_data: str
    schema_digest: str
    evaluation_rows_digest: str
    observer_program_digest: str
    confirmation_policy_digest: str
    worker_receipt_digest: str
    ledger_receipt_digest: str
    transport_receipt_digests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayEnvironment:
    """Caller-declared normalized replay environment identity."""

    implementation: str
    runtime_version: str
    platform: str
    worker_profile: str
    source_tree_digest: str


@dataclass(frozen=True, slots=True)
class AuthenticatedReplayPackage:
    """Canonical evidence envelope with an HMAC tag or Ed25519 signature."""

    schema_version: str
    package_kind: ReplayPackageKind
    evidence: ReplayEvidenceRoots
    environment: ReplayEnvironment
    signer_id: str
    authentication: ReplayAuthentication
    payload_digest: str
    authentication_tag: str
    boundary: str
