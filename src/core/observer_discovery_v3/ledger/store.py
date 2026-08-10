"""Atomic local one-shot consumption ledger for governed confirmation.

The ledger is intentionally narrower than a remote transparency service.  It
serializes cooperating processes through one protected directory, burns a
capability at CLAIMED, and never permits a second attempt after a crash.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import hmac
import json
import logging
import os
from pathlib import Path
import secrets
import stat
from typing import Iterator, NoReturn

from src.platform_capabilities import Capability, require_capability

from .types import (
    ONE_SHOT_LEDGER_BOUNDARY,
    OneShotLedgerReceipt,
    OneShotLedgerState,
    OneShotOutcome,
    OneShotReservation,
)
from ...platform_posix import exclusive_file_lock
from ...proof_core_codec import canonical_json, digest_data, load_canonical

logger = logging.getLogger(__name__)

_LEDGER_SCHEMA = "veyra.observer-confirmation.one-shot-ledger.v1"
_STATE_NAME = "observer-confirmation-ledger-v1.json"
_LOCK_NAME = ".observer-confirmation-ledger-v1.lock"
_MAX_LEDGER_BYTES = 1_000_000
_MAX_ENTRIES = 10_000
_MAX_TEXT_BYTES = 512
_MAX_PATH_BYTES = 4096
_CAPABILITY_MIN_BYTES = 32
_CAPABILITY_MAX_BYTES = 4096
_HEX = frozenset("0123456789abcdef")


class OneShotLedgerError(RuntimeError):
    """Stable fail-closed ledger rejection without sensitive payloads."""

    def __init__(self, reason: str) -> None:
        logger.error("OneShotLedgerError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def reserve_one_shot(
    directory: Path,
    reservation: OneShotReservation,
    capability: bytes,
) -> OneShotLedgerReceipt:
    """Create exactly one RESERVED commitment under an existing secure directory."""
    logger.debug("reserve_one_shot entry")
    _validate_reservation(reservation)
    capability_digest = _capability_digest(capability)
    with _locked_directory(directory) as directory_fd:
        entries = _load_entries(directory_fd)
        if any(row.reservation.reservation_id == reservation.reservation_id for row in entries):
            _reject("reservation-exists")
        if any(row.capability_digest == capability_digest for row in entries):
            _reject("capability-already-reserved")
        if any(row.reservation.test_commitment == reservation.test_commitment for row in entries):
            _reject("test-commitment-already-reserved")
        if len(entries) >= _MAX_ENTRIES:
            _reject("entry-cap")
        draft = OneShotLedgerReceipt(
            reservation,
            OneShotLedgerState.RESERVED,
            capability_digest,
            "",
            None,
            "",
            0,
            "",
            ONE_SHOT_LEDGER_BOUNDARY,
            "",
        )
        receipt = _bind_receipt(draft)
        _write_entries(directory_fd, (*entries, receipt))
    logger.info("reserve_one_shot state=RESERVED")
    logger.debug("reserve_one_shot exit")
    return receipt


def claim_one_shot(
    directory: Path,
    reservation_id: str,
    capability: bytes,
    attempt_id: str,
) -> OneShotLedgerReceipt:
    """Atomically burn one RESERVED capability before any test evaluation."""
    logger.debug("claim_one_shot entry")
    _bounded_text(reservation_id, "reservation-id")
    _bounded_text(attempt_id, "attempt-id")
    capability_digest = _capability_digest(capability)
    with _locked_directory(directory) as directory_fd:
        entries = _load_entries(directory_fd)
        index, current = _find_entry(entries, reservation_id)
        _authenticate(current, capability_digest)
        if current.state is not OneShotLedgerState.RESERVED:
            _reject("already-claimed")
        attempt_digest = digest_data(
            {"reservation_receipt": current.receipt_digest, "attempt_id": attempt_id},
            "veyra.observer-confirmation.one-shot-attempt.v1",
        )
        claimed = _bind_receipt(
            replace(
                current,
                state=OneShotLedgerState.CLAIMED,
                attempt_digest=attempt_digest,
                revision=1,
                previous_receipt=current.receipt_digest,
                receipt_digest="",
            )
        )
        _write_entries(directory_fd, _replace_entry(entries, index, claimed))
    logger.info("claim_one_shot state=CLAIMED")
    logger.debug("claim_one_shot exit")
    return claimed


def finalize_one_shot(
    directory: Path,
    reservation_id: str,
    capability: bytes,
    claimed_receipt_digest: str,
    outcome: OneShotOutcome,
    outcome_digest: str,
) -> OneShotLedgerReceipt:
    """Finalize the one burned attempt exactly once as CONSUMED or FAILED."""
    logger.debug("finalize_one_shot entry")
    _bounded_text(reservation_id, "reservation-id")
    _require_digest(claimed_receipt_digest, "claimed-receipt")
    _require_digest(outcome_digest, "outcome")
    if type(outcome) is not OneShotOutcome:
        _reject("outcome-type")
    capability_digest = _capability_digest(capability)
    terminal = (
        OneShotLedgerState.CONSUMED
        if outcome
        in {
            OneShotOutcome.REPLICATED,
            OneShotOutcome.NOT_REPLICATED,
            OneShotOutcome.EVALUATION_COMPLETED,
        }
        else OneShotLedgerState.FAILED
    )
    with _locked_directory(directory) as directory_fd:
        entries = _load_entries(directory_fd)
        index, current = _find_entry(entries, reservation_id)
        _authenticate(current, capability_digest)
        if current.state is not OneShotLedgerState.CLAIMED:
            _reject("not-claimable-final-state")
        if not hmac.compare_digest(current.receipt_digest, claimed_receipt_digest):
            _reject("claimed-receipt-mismatch")
        finalized = _bind_receipt(
            replace(
                current,
                state=terminal,
                outcome=outcome,
                outcome_digest=outcome_digest,
                revision=2,
                previous_receipt=current.receipt_digest,
                receipt_digest="",
            )
        )
        _write_entries(directory_fd, _replace_entry(entries, index, finalized))
    logger.info("finalize_one_shot state=%s", terminal.value)
    logger.debug("finalize_one_shot exit")
    return finalized


def read_one_shot(directory: Path, reservation_id: str) -> OneShotLedgerReceipt:
    """Read one exact receipt while holding the same producer lock."""
    logger.debug("read_one_shot entry")
    _bounded_text(reservation_id, "reservation-id")
    with _locked_directory(directory) as directory_fd:
        _index, receipt = _find_entry(_load_entries(directory_fd), reservation_id)
    logger.debug("read_one_shot exit state=%s", receipt.state.value)
    return receipt


def validate_one_shot_receipt(receipt: object) -> bool:
    """Validate one local transition receipt without accessing the ledger file."""
    logger.debug("validate_one_shot_receipt entry type=%s", type(receipt).__name__)
    try:
        valid = _validate_receipt_shape(receipt) and _bind_receipt(replace(receipt, receipt_digest="")) == receipt
    except (AttributeError, TypeError, ValueError):
        logger.error("validate_one_shot_receipt malformed")
        return False
    logger.debug("validate_one_shot_receipt exit valid=%s", valid)
    return valid


@contextmanager
def _locked_directory(directory: Path) -> Iterator[int]:
    logger.debug("_locked_directory entry")
    directory_fd = _open_directory(directory)
    lock_fd = -1
    try:
        lock_fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        _validate_owned_regular_fd(lock_fd, "lock-file")
        exclusive_file_lock(lock_fd)
        yield directory_fd
    except OneShotLedgerError:
        raise
    except (OSError, ValueError) as exc:
        logger.error("_locked_directory runtime failure type=%s", type(exc).__name__)
        raise OneShotLedgerError("ledger-io") from exc
    finally:
        if lock_fd >= 0:
            os.close(lock_fd)
        os.close(directory_fd)
        logger.debug("_locked_directory exit")


def _open_directory(directory: Path) -> int:
    logger.debug("_open_directory entry type=%s", type(directory).__name__)
    require_capability(Capability.POSIX_FILE_LOCKS)
    if not isinstance(directory, Path):
        _reject("directory-type")
    raw = os.fsencode(directory)
    if not raw or len(raw) > _MAX_PATH_BYTES or not hasattr(os, "O_NOFOLLOW"):
        _reject("directory-path")
    metadata = os.lstat(directory)
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
        _reject("insecure-directory")
    descriptor = os.open(
        directory,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    opened = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
        os.close(descriptor)
        _reject("directory-race")
    logger.debug("_open_directory exit")
    return descriptor


def _load_entries(directory_fd: int) -> tuple[OneShotLedgerReceipt, ...]:
    logger.debug("_load_entries entry")
    try:
        state_fd = os.open(
            _STATE_NAME,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        logger.debug("_load_entries exit count=0")
        return ()
    try:
        metadata = _validate_owned_regular_fd(state_fd, "state-file")
        if metadata.st_size > _MAX_LEDGER_BYTES:
            _reject("ledger-size")
        payload = bytearray()
        while len(payload) <= metadata.st_size:
            chunk = os.read(state_fd, min(65_536, metadata.st_size + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) != metadata.st_size:
            _reject("ledger-read")
    finally:
        os.close(state_fd)
    try:
        text = payload.decode("utf-8")
        data = load_canonical(text)
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("_load_entries invalid encoding type=%s", type(exc).__name__)
        raise OneShotLedgerError("ledger-format") from exc
    if type(data) is not dict or set(data) != {"schema", "entries"} or data["schema"] != _LEDGER_SCHEMA:
        _reject("ledger-schema")
    rows = data["entries"]
    if type(rows) is not list or len(rows) > _MAX_ENTRIES:
        _reject("entry-cap")
    entries = tuple(_receipt_from_data(row) for row in rows)
    if len({row.reservation.reservation_id for row in entries}) != len(entries):
        _reject("duplicate-reservation")
    if len({row.capability_digest for row in entries}) != len(entries):
        _reject("duplicate-capability")
    if len({row.reservation.test_commitment for row in entries}) != len(entries):
        _reject("duplicate-test-commitment")
    logger.debug("_load_entries exit count=%d", len(entries))
    return entries


def _write_entries(directory_fd: int, entries: tuple[OneShotLedgerReceipt, ...]) -> None:
    logger.debug("_write_entries entry count=%d", len(entries))
    payload = canonical_json(
        {"schema": _LEDGER_SCHEMA, "entries": [_receipt_data(row, include_digest=True) for row in entries]}
    ).encode("utf-8")
    if len(payload) > _MAX_LEDGER_BYTES:
        _reject("ledger-size")
    temporary = f".observer-ledger-{os.getpid()}-{secrets.token_hex(8)}.tmp"
    temp_fd = -1
    try:
        temp_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        _write_all(temp_fd, payload)
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = -1
        os.replace(temporary, _STATE_NAME, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
    logger.debug("_write_entries exit bytes=%d", len(payload))


def _write_all(descriptor: int, payload: bytes) -> None:
    logger.debug("_write_all entry bytes=%d", len(payload))
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            _reject("ledger-write")
        view = view[written:]
    logger.debug("_write_all exit")


def _validate_owned_regular_fd(descriptor: int, reason: str) -> os.stat_result:
    logger.debug("_validate_owned_regular_fd entry reason=%s", reason)
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
        or metadata.st_mode & 0o077
    ):
        _reject(reason)
    logger.debug("_validate_owned_regular_fd exit reason=%s", reason)
    return metadata


def _find_entry(
    entries: tuple[OneShotLedgerReceipt, ...],
    reservation_id: str,
) -> tuple[int, OneShotLedgerReceipt]:
    logger.debug("_find_entry entry count=%d", len(entries))
    matches = tuple(
        (index, row) for index, row in enumerate(entries) if row.reservation.reservation_id == reservation_id
    )
    if len(matches) != 1:
        _reject("reservation-not-found")
    logger.debug("_find_entry exit")
    return matches[0]


def _replace_entry(
    entries: tuple[OneShotLedgerReceipt, ...],
    index: int,
    replacement: OneShotLedgerReceipt,
) -> tuple[OneShotLedgerReceipt, ...]:
    logger.debug("_replace_entry entry count=%d", len(entries))
    result = (*entries[:index], replacement, *entries[index + 1 :])
    logger.debug("_replace_entry exit")
    return result


def _authenticate(receipt: OneShotLedgerReceipt, capability_digest: str) -> None:
    logger.debug("_authenticate entry")
    if not hmac.compare_digest(receipt.capability_digest, capability_digest):
        _reject("capability-mismatch")
    logger.debug("_authenticate exit")


def _capability_digest(capability: bytes) -> str:
    logger.debug("_capability_digest entry type=%s", type(capability).__name__)
    if type(capability) is not bytes or not _CAPABILITY_MIN_BYTES <= len(capability) <= _CAPABILITY_MAX_BYTES:
        _reject("capability-shape")
    result = sha256(b"veyra.observer-confirmation.capability.v1\0" + capability).hexdigest()
    logger.debug("_capability_digest exit")
    return result


def _bind_receipt(receipt: OneShotLedgerReceipt) -> OneShotLedgerReceipt:
    logger.debug("_bind_receipt entry state=%s", receipt.state.value)
    digest = digest_data(_receipt_data(receipt, include_digest=False), "veyra.observer-confirmation.ledger-receipt.v1")
    result = replace(receipt, receipt_digest=digest)
    logger.debug("_bind_receipt exit")
    return result


def _validate_receipt_shape(receipt: object) -> bool:
    logger.debug("_validate_receipt_shape entry")
    if type(receipt) is not OneShotLedgerReceipt or not _valid_reservation(receipt.reservation):
        return False
    common = (
        type(receipt.state) is OneShotLedgerState
        and _is_digest(receipt.capability_digest)
        and type(receipt.revision) is int
        and 0 <= receipt.revision <= 2
        and receipt.boundary == ONE_SHOT_LEDGER_BOUNDARY
        and _is_digest(receipt.receipt_digest)
        and (not receipt.previous_receipt or _is_digest(receipt.previous_receipt))
        and (not receipt.attempt_digest or _is_digest(receipt.attempt_digest))
        and (not receipt.outcome_digest or _is_digest(receipt.outcome_digest))
        and (receipt.outcome is None or type(receipt.outcome) is OneShotOutcome)
    )
    if receipt.state is OneShotLedgerState.RESERVED:
        state_valid = (
            receipt.revision == 0
            and not receipt.attempt_digest
            and receipt.outcome is None
            and not receipt.outcome_digest
            and not receipt.previous_receipt
        )
    elif receipt.state is OneShotLedgerState.CLAIMED:
        state_valid = (
            receipt.revision == 1
            and _is_digest(receipt.attempt_digest)
            and receipt.outcome is None
            and not receipt.outcome_digest
            and _is_digest(receipt.previous_receipt)
        )
    else:
        expected_state = (
            OneShotLedgerState.CONSUMED
            if receipt.outcome
            in {
                OneShotOutcome.REPLICATED,
                OneShotOutcome.NOT_REPLICATED,
                OneShotOutcome.EVALUATION_COMPLETED,
            }
            else OneShotLedgerState.FAILED
        )
        state_valid = (
            receipt.revision == 2
            and receipt.state is expected_state
            and _is_digest(receipt.attempt_digest)
            and type(receipt.outcome) is OneShotOutcome
            and _is_digest(receipt.outcome_digest)
            and _is_digest(receipt.previous_receipt)
        )
    result = common and state_valid
    logger.debug("_validate_receipt_shape exit valid=%s", result)
    return result


def _validate_reservation(reservation: OneShotReservation) -> None:
    logger.debug("_validate_reservation entry")
    if not _valid_reservation(reservation):
        _reject("reservation-shape")
    logger.debug("_validate_reservation exit")


def _valid_reservation(reservation: object) -> bool:
    logger.debug("_valid_reservation entry type=%s", type(reservation).__name__)
    try:
        result = (
            type(reservation) is OneShotReservation
            and _text_valid(reservation.reservation_id)
            and _text_valid(reservation.purpose)
            and all(
                _is_digest(value)
                for value in (
                    reservation.parent_result,
                    reservation.test_commitment,
                    reservation.schema_digest,
                    reservation.evaluation_rows_digest,
                    reservation.observer_program_digest,
                    reservation.confirmation_policy_digest,
                )
            )
        )
    except AttributeError:
        result = False
    logger.debug("_valid_reservation exit valid=%s", result)
    return result


def _receipt_data(receipt: OneShotLedgerReceipt, *, include_digest: bool) -> dict[str, object]:
    logger.debug("_receipt_data entry state=%s", receipt.state.value)
    data = {
        "reservation": {
            "reservation_id": receipt.reservation.reservation_id,
            "purpose": receipt.reservation.purpose,
            "parent_result": receipt.reservation.parent_result,
            "test_commitment": receipt.reservation.test_commitment,
            "schema_digest": receipt.reservation.schema_digest,
            "evaluation_rows_digest": receipt.reservation.evaluation_rows_digest,
            "observer_program_digest": receipt.reservation.observer_program_digest,
            "confirmation_policy_digest": receipt.reservation.confirmation_policy_digest,
        },
        "state": receipt.state.value,
        "capability_digest": receipt.capability_digest,
        "attempt_digest": receipt.attempt_digest,
        "outcome": None if receipt.outcome is None else receipt.outcome.value,
        "outcome_digest": receipt.outcome_digest,
        "revision": receipt.revision,
        "previous_receipt": receipt.previous_receipt,
        "boundary": receipt.boundary,
    }
    if include_digest:
        data["receipt_digest"] = receipt.receipt_digest
    logger.debug("_receipt_data exit")
    return data


def _receipt_from_data(data: object) -> OneShotLedgerReceipt:
    logger.debug("_receipt_from_data entry")
    expected = {
        "reservation",
        "state",
        "capability_digest",
        "attempt_digest",
        "outcome",
        "outcome_digest",
        "revision",
        "previous_receipt",
        "boundary",
        "receipt_digest",
    }
    if type(data) is not dict or set(data) != expected or type(data["reservation"]) is not dict:
        _reject("receipt-shape")
    row = data["reservation"]
    reservation_keys = {
        "reservation_id",
        "purpose",
        "parent_result",
        "test_commitment",
        "schema_digest",
        "evaluation_rows_digest",
        "observer_program_digest",
        "confirmation_policy_digest",
    }
    if set(row) != reservation_keys:
        _reject("reservation-shape")
    try:
        receipt = OneShotLedgerReceipt(
            OneShotReservation(**row),
            OneShotLedgerState(data["state"]),
            data["capability_digest"],
            data["attempt_digest"],
            None if data["outcome"] is None else OneShotOutcome(data["outcome"]),
            data["outcome_digest"],
            data["revision"],
            data["previous_receipt"],
            data["boundary"],
            data["receipt_digest"],
        )
    except (TypeError, ValueError) as exc:
        raise OneShotLedgerError("receipt-shape") from exc
    if not validate_one_shot_receipt(receipt):
        _reject("receipt-invalid")
    logger.debug("_receipt_from_data exit state=%s", receipt.state.value)
    return receipt


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


def _require_digest(value: object, reason: str) -> None:
    logger.debug("_require_digest entry reason=%s", reason)
    if not _is_digest(value):
        _reject(reason)
    logger.debug("_require_digest exit reason=%s", reason)


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = type(value) is str and len(value) == 64 and all(character in _HEX for character in value)
    logger.debug("_is_digest exit valid=%s", result)
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("observer_discovery_ledger rejected reason=%s", reason)
    raise OneShotLedgerError(reason)
