from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import os
from pathlib import Path

import pytest

from src.core.observer_discovery_v3.ledger.store import (
    OneShotLedgerError,
    claim_one_shot,
    finalize_one_shot,
    read_one_shot,
    reserve_one_shot,
    validate_one_shot_receipt,
)
from src.core.observer_discovery_v3.ledger import store as ledger_store
from src.core.observer_discovery_v3.ledger.types import (
    OneShotLedgerState,
    OneShotOutcome,
    OneShotReservation,
)
from src.core.proof_core_codec import canonical_json


def digest(symbol: str) -> str:
    return symbol * 64


def reservation(name: str = "phase-iii-test") -> OneShotReservation:
    return OneShotReservation(
        name,
        "fixed-winner declared-test consumption",
        digest("a"),
        digest("b"),
        digest("c"),
        digest("d"),
        digest("e"),
        digest("f"),
    )


def secure_directory(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def test_reserve_claim_finalize_is_hash_chained_and_secret_free(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    capability = bytes(range(32))
    reserved = reserve_one_shot(directory, reservation(), capability)
    claimed = claim_one_shot(directory, reservation().reservation_id, capability, "attempt-1")
    finalized = finalize_one_shot(
        directory,
        reservation().reservation_id,
        capability,
        claimed.receipt_digest,
        OneShotOutcome.REPLICATED,
        digest("f"),
    )

    assert reserved.state is OneShotLedgerState.RESERVED
    assert claimed.state is OneShotLedgerState.CLAIMED
    assert finalized.state is OneShotLedgerState.CONSUMED
    assert claimed.previous_receipt == reserved.receipt_digest
    assert finalized.previous_receipt == claimed.receipt_digest
    assert read_one_shot(directory, reservation().reservation_id) == finalized
    assert all(validate_one_shot_receipt(row) for row in (reserved, claimed, finalized))
    assert capability not in (directory / "observer-confirmation-ledger-v1.json").read_bytes()


def test_claim_is_irreversible_and_finalize_is_exactly_once(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    capability = b"x" * 32
    reserve_one_shot(directory, reservation(), capability)
    claimed = claim_one_shot(directory, reservation().reservation_id, capability, "attempt-1")

    with pytest.raises(OneShotLedgerError, match="already-claimed"):
        claim_one_shot(directory, reservation().reservation_id, capability, "attempt-2")
    with pytest.raises(OneShotLedgerError, match="claimed-receipt-mismatch"):
        finalize_one_shot(
            directory,
            reservation().reservation_id,
            capability,
            digest("0"),
            OneShotOutcome.NOT_REPLICATED,
            digest("f"),
        )
    finalized = finalize_one_shot(
        directory,
        reservation().reservation_id,
        capability,
        claimed.receipt_digest,
        OneShotOutcome.CONFIRMATION_BLOCKED,
        digest("f"),
    )
    assert finalized.state is OneShotLedgerState.FAILED
    with pytest.raises(OneShotLedgerError, match="not-claimable-final-state"):
        finalize_one_shot(
            directory,
            reservation().reservation_id,
            capability,
            claimed.receipt_digest,
            OneShotOutcome.CONFIRMATION_BLOCKED,
            digest("f"),
        )


def test_wrong_capability_duplicate_reservation_and_forgery_fail(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    capability = b"k" * 32
    reserved = reserve_one_shot(directory, reservation(), capability)

    with pytest.raises(OneShotLedgerError, match="reservation-exists"):
        reserve_one_shot(directory, reservation(), capability)
    with pytest.raises(OneShotLedgerError, match="capability-mismatch"):
        claim_one_shot(directory, reservation().reservation_id, b"z" * 32, "attempt")
    assert not validate_one_shot_receipt(replace(reserved, reservation=replace(reserved.reservation, purpose="forged")))
    assert not validate_one_shot_receipt(replace(reserved, receipt_digest=digest("0")))


def test_capability_and_test_commitment_cannot_be_reserved_under_new_ids(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    original = reservation("original")
    capability = b"u" * 32
    reserve_one_shot(directory, original, capability)

    with pytest.raises(OneShotLedgerError, match="capability-already-reserved"):
        reserve_one_shot(
            directory,
            replace(original, reservation_id="same-capability", test_commitment=digest("1")),
            capability,
        )
    with pytest.raises(OneShotLedgerError, match="test-commitment-already-reserved"):
        reserve_one_shot(
            directory,
            replace(original, reservation_id="same-test"),
            b"v" * 32,
        )


@pytest.mark.parametrize("duplicate", ["capability", "test-commitment"])
def test_loading_canonical_state_rejects_duplicate_unique_commitments(
    tmp_path: Path,
    duplicate: str,
) -> None:
    directory = secure_directory(tmp_path / duplicate)
    first = reserve_one_shot(directory, reservation("first"), b"a" * 32)
    second = reserve_one_shot(
        directory,
        replace(reservation("second"), test_commitment=digest("1")),
        b"b" * 32,
    )
    if duplicate == "capability":
        forged = replace(second, capability_digest=first.capability_digest, receipt_digest="")
    else:
        forged = replace(
            second,
            reservation=replace(second.reservation, test_commitment=first.reservation.test_commitment),
            receipt_digest="",
        )
    forged = ledger_store._bind_receipt(forged)
    state = directory / "observer-confirmation-ledger-v1.json"
    state.write_text(
        canonical_json(
            {
                "schema": ledger_store._LEDGER_SCHEMA,
                "entries": [
                    ledger_store._receipt_data(first, include_digest=True),
                    ledger_store._receipt_data(forged, include_digest=True),
                ],
            }
        )
    )

    with pytest.raises(OneShotLedgerError, match=f"duplicate-{duplicate}"):
        read_one_shot(directory, "first")


def test_concurrent_claim_allows_exactly_one_process_cooperator(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    capability = b"r" * 32
    reserve_one_shot(directory, reservation(), capability)

    def attempt(index: int) -> str:
        try:
            claim_one_shot(directory, reservation().reservation_id, capability, f"attempt-{index}")
        except OneShotLedgerError as exc:
            return exc.reason
        return "claimed"

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes = tuple(pool.map(attempt, range(16)))
    assert outcomes.count("claimed") == 1
    assert outcomes.count("already-claimed") == 15
    assert read_one_shot(directory, reservation().reservation_id).state is OneShotLedgerState.CLAIMED


def test_insecure_directory_symlink_state_and_malformed_state_fail(tmp_path: Path) -> None:
    insecure = tmp_path / "insecure"
    insecure.mkdir(mode=0o755)
    insecure.chmod(0o755)
    with pytest.raises(OneShotLedgerError, match="insecure-directory"):
        reserve_one_shot(insecure, reservation(), b"a" * 32)

    directory = secure_directory(tmp_path / "ledger")
    external = tmp_path / "external"
    external.write_text("{}")
    (directory / "observer-confirmation-ledger-v1.json").symlink_to(external)
    with pytest.raises(OneShotLedgerError, match="ledger-io"):
        reserve_one_shot(directory, reservation(), b"a" * 32)

    os.unlink(directory / "observer-confirmation-ledger-v1.json")
    state = directory / "observer-confirmation-ledger-v1.json"
    state.write_text("{}")
    state.chmod(0o600)
    with pytest.raises(OneShotLedgerError, match="ledger-schema"):
        reserve_one_shot(directory, reservation(), b"a" * 32)


def test_caps_and_exact_types_fail_before_persistence(tmp_path: Path) -> None:
    directory = secure_directory(tmp_path / "ledger")
    with pytest.raises(OneShotLedgerError, match="capability-shape"):
        reserve_one_shot(directory, reservation(), b"short")
    with pytest.raises(OneShotLedgerError, match="reservation-shape"):
        reserve_one_shot(
            directory,
            replace(reservation(), purpose="x" * 513),
            b"a" * 32,
        )
    with pytest.raises(OneShotLedgerError, match="reservation-shape"):
        reserve_one_shot(
            directory,
            replace(reservation(), purpose="\ud800"),
            b"a" * 32,
        )
    assert not (directory / "observer-confirmation-ledger-v1.json").exists()
