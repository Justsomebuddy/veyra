from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.core.observer_discovery_v3.ledger.store import (
    claim_one_shot,
    finalize_one_shot,
    reserve_one_shot,
)
from src.core.observer_discovery_v3.ledger.types import (
    OneShotOutcome,
    OneShotReservation,
)
from src.core.observer_discovery_v3.replay.package import (
    AuthenticatedReplayError,
    authenticated_replay_from_json,
    authenticated_replay_json,
    build_authenticated_replay,
    build_signed_replay,
    validate_authenticated_replay,
    validate_signed_replay,
)
from src.core.observer_discovery_v3.replay.types import (
    ReplayEnvironment,
    ReplayEvidenceRoots,
    ReplayPackageKind,
)


def digest(symbol: str) -> str:
    return symbol * 64


def terminal_receipt(
    directory: Path,
    outcome: OneShotOutcome = OneShotOutcome.REPLICATED,
    outcome_digest: str = digest("f"),
):
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    capability = bytes(range(32))
    reservation = OneShotReservation(
        "replay-test",
        "authenticated audit receipt",
        digest("a"),
        digest("b"),
        digest("c"),
        digest("6"),
        digest("d"),
        digest("e"),
    )
    reserve_one_shot(directory, reservation, capability)
    claimed = claim_one_shot(directory, reservation.reservation_id, capability, "attempt-1")
    return finalize_one_shot(
        directory,
        reservation.reservation_id,
        capability,
        claimed.receipt_digest,
        outcome,
        outcome_digest,
    )


def evidence(ledger_digest: str) -> ReplayEvidenceRoots:
    return ReplayEvidenceRoots(
        digest("a"),
        digest("f"),
        digest("b"),
        digest("8"),
        digest("c"),
        digest("6"),
        digest("d"),
        digest("e"),
        digest("7"),
        ledger_digest,
        (digest("9"), digest("0")),
    )


def environment() -> ReplayEnvironment:
    return ReplayEnvironment(
        "CPython",
        "3.11.14",
        "linux-x86_64",
        "logical-fixed-child-v1",
        digest("1"),
    )


def test_authenticated_audit_receipt_roundtrips_and_links_terminal_ledger(tmp_path: Path) -> None:
    receipt = terminal_receipt(tmp_path / "ledger")
    key = b"shared-replay-authentication-key!"
    package = build_authenticated_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "lab-key-1",
        key,
        receipt,
    )
    encoded = authenticated_replay_json(package)
    decoded = authenticated_replay_from_json(encoded)

    assert package.package_kind is ReplayPackageKind.AUDIT_RECEIPT
    assert decoded == package
    assert validate_authenticated_replay(decoded, key, ledger_receipt=receipt)
    assert key not in encoded.encode()
    assert "not independently executable full replay" in package.boundary


def test_wrong_key_payload_substitution_and_ledger_substitution_fail(tmp_path: Path) -> None:
    receipt = terminal_receipt(tmp_path / "ledger")
    key = b"shared-replay-authentication-key!"
    package = build_authenticated_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "lab-key-1",
        key,
        receipt,
    )

    assert not validate_authenticated_replay(package, b"different-replay-authentication!!")
    assert not validate_authenticated_replay(
        replace(package, evidence=replace(package.evidence, test_data=digest("2"))),
        key,
    )
    assert not validate_authenticated_replay(
        package,
        key,
        ledger_receipt=replace(receipt, outcome_digest=digest("2")),
    )


def test_worker_terminal_outcome_links_worker_receipt_not_unrelated_confirmation(tmp_path: Path) -> None:
    receipt = terminal_receipt(
        tmp_path / "ledger",
        OneShotOutcome.EVALUATION_COMPLETED,
        digest("7"),
    )
    key = b"shared-replay-authentication-key!"
    package = build_authenticated_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "lab-key-1",
        key,
        receipt,
    )

    assert validate_authenticated_replay(package, key, ledger_receipt=receipt)
    with pytest.raises(AuthenticatedReplayError, match="ledger-link"):
        build_authenticated_replay(
            replace(package.evidence, worker_receipt_digest=digest("2")),
            environment(),
            "lab-key-1",
            key,
            receipt,
        )


def test_builder_rejects_nonterminal_or_mismatched_ledger_and_weak_key(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    capability = b"x" * 32
    request = OneShotReservation(
        "replay-test",
        "authenticated audit receipt",
        digest("a"),
        digest("b"),
        digest("c"),
        digest("6"),
        digest("d"),
        digest("e"),
    )
    reserved = reserve_one_shot(directory, request, capability)

    with pytest.raises(AuthenticatedReplayError, match="ledger-link"):
        build_authenticated_replay(
            evidence(reserved.receipt_digest),
            environment(),
            "lab-key-1",
            b"k" * 32,
            reserved,
        )
    with pytest.raises(AuthenticatedReplayError, match="key-shape"):
        build_authenticated_replay(
            evidence(reserved.receipt_digest),
            environment(),
            "lab-key-1",
            b"short",
            reserved,
        )


def test_canonical_decoder_rejects_noncanonical_extra_and_oversized_json(tmp_path: Path) -> None:
    receipt = terminal_receipt(tmp_path / "ledger")
    key = b"shared-replay-authentication-key!"
    package = build_authenticated_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "lab-key-1",
        key,
        receipt,
    )
    encoded = authenticated_replay_json(package)
    noncanonical = json.dumps(json.loads(encoded), indent=2)
    extra = json.loads(encoded)
    extra["unexpected"] = True

    with pytest.raises(AuthenticatedReplayError, match="package-format"):
        authenticated_replay_from_json(noncanonical)
    with pytest.raises(AuthenticatedReplayError, match="package-shape"):
        authenticated_replay_from_json(json.dumps(extra, sort_keys=True, separators=(",", ":")))
    with pytest.raises(AuthenticatedReplayError, match="package-size"):
        authenticated_replay_from_json("x" * 1_000_001)
    with pytest.raises(AuthenticatedReplayError, match="package-format"):
        authenticated_replay_from_json("\ud800")


def test_transport_suite_and_environment_are_mandatory(tmp_path: Path) -> None:
    receipt = terminal_receipt(tmp_path / "ledger")
    base = evidence(receipt.receipt_digest)

    with pytest.raises(AuthenticatedReplayError, match="evidence-shape"):
        build_authenticated_replay(
            replace(base, transport_receipt_digests=()),
            environment(),
            "lab-key-1",
            b"k" * 32,
            receipt,
        )
    with pytest.raises(AuthenticatedReplayError, match="environment-shape"):
        build_authenticated_replay(
            base,
            replace(environment(), worker_profile=""),
            "lab-key-1",
            b"k" * 32,
            receipt,
        )


def test_ed25519_signed_receipt_is_publicly_verifiable_and_canonical(tmp_path: Path) -> None:
    pytest.importorskip("cryptography.hazmat.primitives.asymmetric.ed25519")
    receipt = terminal_receipt(tmp_path / "ledger")
    # Public RFC 8032 test-vector keypair; never production key material.
    private_key = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    public_key = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")

    first = build_signed_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "ed25519-lab-key-1",
        private_key,
        receipt,
    )
    second = build_signed_replay(
        evidence(receipt.receipt_digest),
        environment(),
        "ed25519-lab-key-1",
        private_key,
        receipt,
    )
    decoded = authenticated_replay_from_json(authenticated_replay_json(first))

    assert first == second == decoded
    assert first.authentication.value == "Ed25519-v1"
    assert len(first.authentication_tag) == 128
    assert validate_signed_replay(first, public_key, ledger_receipt=receipt)
    assert not validate_signed_replay(first, b"x" * 32)
    assert not validate_signed_replay(
        replace(first, evidence=replace(first.evidence, test_data=digest("2"))),
        public_key,
    )
    assert not validate_authenticated_replay(first, b"k" * 32)
    encoded = authenticated_replay_json(first).encode()
    assert private_key not in encoded
