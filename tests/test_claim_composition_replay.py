"""Independent replay-package and verifier CLI controls."""

from __future__ import annotations

from dataclasses import replace
import json
import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.core.claim_composition import (
    ClaimCompositionError,
    authenticated_composition_export_json,
    authenticated_composition_export_from_json,
    build_authenticated_composition_export,
    build_composition_public_export,
    build_composition_receipt,
    build_composition_replay_package,
    composition_replay_package_from_json,
    composition_replay_package_json,
    validate_composition_replay_package,
    validate_authenticated_composition_export,
)
from src.core.claim_composition.auth import MAX_COMPOSITION_AUTH_BYTES
from src.core.claim_composition.replay import MAX_COMPOSITION_REPLAY_BYTES
from src.core.proof_core_codec import canonical_json

from test_claim_composition import _positive_case

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_verify_composition_cli_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    """Nonblocking open plus regular-file validation rejects streaming special files."""
    logger.debug("test_verify_composition_cli_rejects_fifo entry")
    package_path = tmp_path / "package.fifo"
    os.mkfifo(package_path)
    result = subprocess.run(
        [sys.executable, "scripts/verify_composition.py", str(package_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert result.returncode == 1
    assert "reason=verifier-package-size" in result.stderr
    logger.debug("test_verify_composition_cli_rejects_fifo exit")


def _package_case(tmp_path: Path):
    logger.debug("_package_case entry")
    sources, target, license = _positive_case(tmp_path)
    receipt = build_composition_receipt(sources, target, license)
    export = build_composition_public_export(receipt, sources, target, license)
    result = build_composition_replay_package(export, sources)
    logger.debug("_package_case exit")
    return result


def test_replay_package_round_trips_with_detached_local_receipts(tmp_path: Path) -> None:
    """The package carries enough local-receipt data for exact composition replay."""
    logger.debug("test_replay_package_round_trips entry")
    package = _package_case(tmp_path)
    payload = composition_replay_package_json(package)
    decoded = composition_replay_package_from_json(payload)
    assert decoded == package
    assert validate_composition_replay_package(decoded)
    assert all(source.governed_result is None for source in decoded.sources)
    assert "external validator trust" in decoded.boundary
    logger.debug("test_replay_package_round_trips exit")


def test_replay_package_digest_drift_fails_fresh_validation(tmp_path: Path) -> None:
    """A changed binding cannot retain a valid package identity."""
    logger.debug("test_replay_package_digest_drift entry")
    package = _package_case(tmp_path)
    assert not validate_composition_replay_package(replace(package, payload_digest="0" * 64))
    logger.debug("test_replay_package_digest_drift exit")


@pytest.mark.parametrize(
    "mutation",
    ("extra-field", "payload-digest", "source-receipt", "source-order"),
)
def test_replay_package_json_mutations_fail_closed(tmp_path: Path, mutation: str) -> None:
    """Bounded structural mutations cannot survive strict decode plus fresh replay."""
    logger.debug("test_replay_package_json_mutations entry mutation=%s", mutation)
    package = _package_case(tmp_path)
    data = json.loads(composition_replay_package_json(package))
    if mutation == "extra-field":
        data["unexpected"] = False
    elif mutation == "payload-digest":
        data["payload_digest"] = "0" * 64
    elif mutation == "source-receipt":
        data["sources"][0]["source_receipt_root"] = "0" * 64
    else:
        assert len(data["sources"]) > 1
        data["sources"].reverse()
    with pytest.raises(ClaimCompositionError):
        composition_replay_package_from_json(canonical_json(data))
    logger.debug("test_replay_package_json_mutations exit mutation=%s", mutation)


def test_replay_and_auth_json_resource_caps_fail_before_replay() -> None:
    """Oversized attacker-controlled JSON is rejected by the declared byte caps."""
    logger.debug("test_replay_and_auth_json_resource_caps entry")
    with pytest.raises(ClaimCompositionError):
        composition_replay_package_from_json(" " * (MAX_COMPOSITION_REPLAY_BYTES + 1))
    with pytest.raises(ClaimCompositionError):
        authenticated_composition_export_from_json(" " * (MAX_COMPOSITION_AUTH_BYTES + 1))
    logger.debug("test_replay_and_auth_json_resource_caps exit")


@pytest.mark.parametrize("mutation", ("extra-field", "tag", "export-root"))
def test_authentication_json_mutations_never_validate(tmp_path: Path, mutation: str) -> None:
    """Shape, authenticator, and root mutations remain distinct fail-closed paths."""
    logger.debug("test_authentication_json_mutations entry mutation=%s", mutation)
    package = _package_case(tmp_path)
    key = b"bounded-mutation-key-material-32!!"
    envelope = build_authenticated_composition_export(
        package.export,
        package.sources,
        "bounded-mutation-test",
        key,
    )
    data = json.loads(authenticated_composition_export_json(envelope))
    if mutation == "extra-field":
        data["unexpected"] = 0
        with pytest.raises(ClaimCompositionError):
            authenticated_composition_export_from_json(canonical_json(data))
    else:
        field = "authentication_tag" if mutation == "tag" else "export_payload_digest"
        data[field] = "0" * 64
        decoded = authenticated_composition_export_from_json(canonical_json(data))
        assert not validate_authenticated_composition_export(
            decoded,
            package.export,
            package.sources,
            key,
        )
    logger.debug("test_authentication_json_mutations exit mutation=%s", mutation)


def test_verify_composition_cli_reports_replay_and_auth_boundary(tmp_path: Path) -> None:
    """The CLI verifies replay and labels omitted authentication instead of implying it."""
    logger.debug("test_verify_composition_cli entry")
    package = _package_case(tmp_path)
    package_path = tmp_path / "composition-replay.json"
    package_path.write_text(composition_replay_package_json(package), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/verify_composition.py", str(package_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "status=PASS" in result.stdout
    assert "auth=NOT_CHECKED" in result.stdout
    assert "source truth" not in result.stdout
    logger.debug("test_verify_composition_cli exit")


def test_verify_composition_cli_checks_hmac_without_echoing_key(tmp_path: Path) -> None:
    """The CLI authenticates a replayed export and never renders supplied key bytes."""
    logger.debug("test_verify_composition_cli_checks_hmac entry")
    package = _package_case(tmp_path)
    key = b"private-test-key-material-32bytes!!"
    envelope = build_authenticated_composition_export(
        package.export,
        package.sources,
        "bounded-cli-test",
        key,
    )
    package_path = tmp_path / "composition-replay.json"
    auth_path = tmp_path / "composition-auth.json"
    key_path = tmp_path / "composition-hmac.key"
    package_path.write_text(composition_replay_package_json(package), encoding="utf-8")
    auth_path.write_text(authenticated_composition_export_json(envelope), encoding="utf-8")
    key_path.write_bytes(key)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_composition.py",
            str(package_path),
            "--auth",
            str(auth_path),
            "--hmac-key-file",
            str(key_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "auth=VERIFIED" in result.stdout
    assert key.decode("ascii") not in result.stdout + result.stderr
    logger.debug("test_verify_composition_cli_checks_hmac exit")


def test_verify_composition_cli_reports_stable_failure_without_input_echo(tmp_path: Path) -> None:
    """A canonical-order failure is exact while the supplied filename remains undisclosed."""
    logger.debug("test_verify_composition_cli_reports_stable_failure entry")
    package = _package_case(tmp_path)
    data = json.loads(composition_replay_package_json(package))
    data["sources"].reverse()
    marker = "private-input-name-must-not-be-echoed.json"
    package_path = tmp_path / marker
    package_path.write_text(canonical_json(data), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "scripts/verify_composition.py", str(package_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1
    assert "reason=replay-package-source-order" in result.stderr
    assert marker not in result.stdout + result.stderr
    logger.debug("test_verify_composition_cli_reports_stable_failure exit")


def test_verify_composition_cli_rejects_oversized_file_without_full_read(tmp_path: Path) -> None:
    """The file descriptor size gate rejects oversized input before parser allocation."""
    logger.debug("test_verify_composition_cli_rejects_oversized_file entry")
    package_path = tmp_path / "oversized.json"
    with package_path.open("wb") as stream:
        stream.seek(MAX_COMPOSITION_REPLAY_BYTES)
        stream.write(b"x")
    result = subprocess.run(
        [sys.executable, "scripts/verify_composition.py", str(package_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1
    assert "reason=verifier-package-size" in result.stderr
    logger.debug("test_verify_composition_cli_rejects_oversized_file exit")


def test_verify_composition_cli_rejects_unused_key_material(tmp_path: Path) -> None:
    """Supplying verification material without an envelope cannot silently pass."""
    logger.debug("test_verify_composition_cli_rejects_unused_key_material entry")
    package = _package_case(tmp_path)
    package_path = tmp_path / "composition-replay.json"
    key_path = tmp_path / "unused.key"
    package_path.write_text(composition_replay_package_json(package), encoding="utf-8")
    key_path.write_bytes(b"x" * 32)
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_composition.py",
            str(package_path),
            "--hmac-key-file",
            str(key_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 1
    assert "reason=verifier-auth-envelope-required" in result.stderr
    logger.debug("test_verify_composition_cli_rejects_unused_key_material exit")
