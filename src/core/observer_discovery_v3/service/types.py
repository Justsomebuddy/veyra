"""Immutable records for burn-before-evaluation observer execution."""

from __future__ import annotations

from dataclasses import dataclass

from ..dsl.types import ClosedEvaluationReceipt
from ..ledger.types import OneShotLedgerReceipt

GOVERNED_EVALUATION_READY = "READY"
GOVERNED_EVALUATION_BLOCKED = "BLOCKED"
GOVERNED_EVALUATION_BOUNDARY = (
    "the local one-shot capability is atomically burned before validation or closed-worker evaluation; "
    "this coordinates cooperating same-user processes but is not remote custody, anti-rollback storage, "
    "a syscall sandbox, historical label-secrecy proof, or a statistical confirmation verdict"
)


@dataclass(frozen=True, slots=True)
class GovernedEvaluationResult:
    """Terminal ledger and worker linkage for one burned evaluation attempt."""

    status: str
    claimed_ledger: OneShotLedgerReceipt
    terminal_ledger: OneShotLedgerReceipt
    worker_receipt: ClosedEvaluationReceipt | None
    observer_program_digest: str
    obstruction: str
    result_digest: str
    boundary: str = GOVERNED_EVALUATION_BOUNDARY
