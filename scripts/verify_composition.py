#!/usr/bin/env python3
"""Independently replay a canonical Veyra composition package and optional authentication."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.claim_composition import (  # noqa: E402
    ClaimCompositionError,
    CompositionAuthentication,
    authenticated_composition_export_from_json,
    composition_replay_package_from_json,
    validate_authenticated_composition_export,
    validate_signed_composition_export,
)

logger = logging.getLogger(__name__)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse bounded file inputs without accepting inline secret material."""
    logger.debug("verify_composition.parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="canonical composition replay-package JSON")
    parser.add_argument("--auth", type=Path, help="optional authenticated-envelope JSON")
    keys = parser.add_mutually_exclusive_group()
    keys.add_argument("--hmac-key-file", type=Path, help="raw HMAC key file (never printed)")
    keys.add_argument("--ed25519-public-key-file", type=Path, help="raw 32-byte public key file")
    result = parser.parse_args(argv)
    logger.debug("verify_composition.parse_args exit auth=%s", result.auth is not None)
    return result


def _read_bounded(path: Path, maximum: int, label: str) -> bytes:
    """Read one regular bounded artifact without following a late size surprise."""
    logger.debug("_read_bounded entry label=%s", label)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum:
            raise ClaimCompositionError(f"verifier-{label}-size")
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ClaimCompositionError(f"verifier-{label}-size")
    logger.debug("_read_bounded exit label=%s bytes=%d", label, len(data))
    return data


def _failure_reason(exc: Exception) -> str:
    """Expose only stable protocol reasons, never attacker-controlled OS/parser detail."""
    logger.debug("_failure_reason entry type=%s", type(exc).__name__)
    if type(exc) is ClaimCompositionError and exc.args and type(exc.args[0]) is str:
        reason = exc.args[0]
        if reason and len(reason) <= 96 and all(char.isalnum() or char in "-_" for char in reason):
            logger.debug("_failure_reason exit stable=True")
            return reason
    logger.debug("_failure_reason exit stable=False")
    return "invalid-input"


def run(argv: list[str]) -> int:
    """Replay package semantics first, then verify the explicitly selected auth profile."""
    logger.debug("verify_composition.run entry")
    args = parse_args(argv)
    started = time.perf_counter()
    planned = 4 if args.auth is not None else 3
    try:
        if args.auth is None and (args.hmac_key_file is not None or args.ed25519_public_key_file is not None):
            raise ClaimCompositionError("verifier-auth-envelope-required")
        print(f"[1/{planned}] Reading bounded replay package", flush=True)
        package_text = _read_bounded(args.package, 1_500_000, "package").decode("utf-8")
        print(f"[2/{planned}] Replaying local receipts and exact composition", flush=True)
        package = composition_replay_package_from_json(package_text)
        if args.auth is not None:
            print(f"[3/{planned}] Reading canonical authentication envelope", flush=True)
            envelope_text = _read_bounded(args.auth, 32_768, "auth").decode("utf-8")
            envelope = authenticated_composition_export_from_json(envelope_text)
            print(f"[4/{planned}] Verifying selected authentication profile", flush=True)
            if envelope.authentication is CompositionAuthentication.HMAC_SHA256:
                if args.hmac_key_file is None:
                    raise ClaimCompositionError("verifier-hmac-key-required")
                key = _read_bounded(args.hmac_key_file, 4096, "hmac-key")
                valid = validate_authenticated_composition_export(envelope, package.export, package.sources, key)
            else:
                if args.ed25519_public_key_file is None:
                    raise ClaimCompositionError("verifier-public-key-required")
                key = _read_bounded(args.ed25519_public_key_file, 32, "public-key")
                valid = validate_signed_composition_export(envelope, package.export, package.sources, key)
            if not valid:
                raise ClaimCompositionError("verifier-authentication-failed")
        else:
            print(f"[3/{planned}] Authentication NOT_CHECKED (no envelope supplied)", flush=True)
    except (ClaimCompositionError, OSError, UnicodeError, ValueError) as exc:
        elapsed = time.perf_counter() - started
        logger.error("verify_composition.run rejected type=%s", type(exc).__name__)
        print(
            f"[done] status=FAIL processed=0 errors=1 reason={_failure_reason(exc)} elapsed={elapsed:.3f}s",
            file=sys.stderr,
        )
        return 1
    elapsed = time.perf_counter() - started
    auth_status = "VERIFIED" if args.auth is not None else "NOT_CHECKED"
    print(
        f"[done] status=PASS processed=1 errors=0 auth={auth_status} elapsed={elapsed:.3f}s",
        flush=True,
    )
    logger.debug("verify_composition.run exit rc=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
