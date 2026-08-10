"""Canonical authenticated and Ed25519-signed replay packages."""

from .package import (
    AuthenticatedReplayError,
    authenticated_replay_from_json,
    authenticated_replay_json,
    build_authenticated_replay,
    build_signed_replay,
    validate_authenticated_replay,
    validate_signed_replay,
)
from .types import (
    AUTHENTICATED_REPLAY_BOUNDARY,
    AuthenticatedReplayPackage,
    ReplayAuthentication,
    ReplayEnvironment,
    ReplayEvidenceRoots,
    ReplayPackageKind,
)

__all__ = (
    "AUTHENTICATED_REPLAY_BOUNDARY",
    "AuthenticatedReplayError",
    "AuthenticatedReplayPackage",
    "ReplayAuthentication",
    "ReplayEnvironment",
    "ReplayEvidenceRoots",
    "ReplayPackageKind",
    "authenticated_replay_from_json",
    "authenticated_replay_json",
    "build_authenticated_replay",
    "build_signed_replay",
    "validate_authenticated_replay",
    "validate_signed_replay",
)
