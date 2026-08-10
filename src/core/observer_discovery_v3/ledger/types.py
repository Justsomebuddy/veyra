"""Immutable records for the cooperating-process one-shot test ledger."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OneShotLedgerState(str, Enum):
    """Irreversible local states for one reserved test capability."""

    RESERVED = "RESERVED"
    CLAIMED = "CLAIMED"
    CONSUMED = "CONSUMED"
    FAILED = "FAILED"


class OneShotOutcome(str, Enum):
    """Exact terminal outcome classes accepted by the ledger."""

    REPLICATED = "CONFIRMATION_REPLICATED"
    NOT_REPLICATED = "CONFIRMATION_NOT_REPLICATED"
    EVALUATION_COMPLETED = "EVALUATION_COMPLETED"
    CONFIRMATION_BLOCKED = "CONFIRMATION_BLOCKED"
    WORKER_BLOCKED = "WORKER_BLOCKED"


ONE_SHOT_LEDGER_BOUNDARY = (
    "atomic one-shot only for cooperating processes sharing one protected local store; "
    "no trusted time, remote witness, operator non-bypass, or historical label-secrecy claim"
)


@dataclass(frozen=True, slots=True)
class OneShotReservation:
    """Pre-evaluation commitments that must be fixed before claiming a test."""

    reservation_id: str
    purpose: str
    parent_result: str
    test_commitment: str
    schema_digest: str
    evaluation_rows_digest: str
    observer_program_digest: str
    confirmation_policy_digest: str


@dataclass(frozen=True, slots=True)
class OneShotLedgerReceipt:
    """One hash-chained local state transition; raw capability is never stored."""

    reservation: OneShotReservation
    state: OneShotLedgerState
    capability_digest: str
    attempt_digest: str
    outcome: OneShotOutcome | None
    outcome_digest: str
    revision: int
    previous_receipt: str
    boundary: str
    receipt_digest: str
