"""Burn-before-evaluation orchestration for the strict observer worker."""

from __future__ import annotations

from dataclasses import replace
import logging
from pathlib import Path

from ..dsl.runtime import ClosedDslError, closed_rows_digest, observer_program_digest
from ..dsl.types import (
    ClosedObserverGrammar,
    ClosedObserverTerm,
    ClosedWorkerConfig,
)
from ..ledger.store import (
    claim_one_shot,
    finalize_one_shot,
    validate_one_shot_receipt,
)
from ..ledger.types import OneShotLedgerState, OneShotOutcome
from ..schema.canonical import canonical_presentation
from ..schema.types import CanonicalPresentation
from ..worker.runtime import (
    BLOCKED,
    READY,
    run_closed_observers_isolated,
    validate_closed_receipt,
)
from ...proof_core_codec import digest_data
from .types import (
    GOVERNED_EVALUATION_BLOCKED,
    GOVERNED_EVALUATION_BOUNDARY,
    GOVERNED_EVALUATION_READY,
    GovernedEvaluationResult,
)

logger = logging.getLogger(__name__)
_HEX = frozenset("0123456789abcdef")


class GovernedEvaluationError(ValueError):
    """Stable post-burn input or root-link failure."""

    def __init__(self, reason: str) -> None:
        logger.error("GovernedEvaluationError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def execute_one_shot_closed_evaluation(
    directory: Path,
    reservation_id: str,
    capability: bytes,
    attempt_id: str,
    presentation: CanonicalPresentation,
    grammar: ClosedObserverGrammar,
    terms: tuple[ClosedObserverTerm, ...],
    worker_config: ClosedWorkerConfig = ClosedWorkerConfig(),
) -> GovernedEvaluationResult:
    """Burn first, then validate roots and execute the fixed closed worker once."""
    logger.debug("execute_one_shot_closed_evaluation entry")
    claimed = claim_one_shot(directory, reservation_id, capability, attempt_id)
    worker_receipt = None
    program_root = ""
    obstruction = ""
    try:
        if type(presentation) is not CanonicalPresentation:
            raise GovernedEvaluationError("invalid-presentation")
        presentation_snapshot = canonical_presentation(presentation.schema, presentation.rows)
        if presentation_snapshot != presentation:
            raise GovernedEvaluationError("invalid-presentation")
        presentation = presentation_snapshot
        program_root = observer_program_digest(grammar, terms)
        reservation = claimed.reservation
        if reservation.schema_digest != presentation.schema_digest:
            raise GovernedEvaluationError("schema-root-mismatch")
        if reservation.test_commitment != presentation.payload_digest:
            raise GovernedEvaluationError("test-commitment-mismatch")
        rows = tuple(tuple(row.values) for row in presentation.rows)
        if reservation.evaluation_rows_digest != closed_rows_digest(rows):
            raise GovernedEvaluationError("evaluation-rows-mismatch")
        if reservation.observer_program_digest != program_root:
            raise GovernedEvaluationError("observer-program-mismatch")
        worker_receipt = run_closed_observers_isolated(
            grammar,
            terms,
            rows,
            worker_config,
            expected_program_digest=reservation.observer_program_digest,
        )
        if not validate_closed_receipt(worker_receipt):
            raise GovernedEvaluationError("invalid-worker-receipt")
        if worker_receipt.status == READY:
            if not validate_closed_receipt(
                worker_receipt,
                expected_rows_digest=reservation.evaluation_rows_digest,
            ):
                raise GovernedEvaluationError("worker-rows-drift")
            if _worker_program_digest(worker_receipt) != program_root:
                raise GovernedEvaluationError("worker-program-drift")
            outcome = OneShotOutcome.EVALUATION_COMPLETED
            outcome_root = worker_receipt.result_digest
            status = GOVERNED_EVALUATION_READY
        elif worker_receipt.status == BLOCKED:
            outcome = OneShotOutcome.WORKER_BLOCKED
            outcome_root = worker_receipt.result_digest
            status = GOVERNED_EVALUATION_BLOCKED
            obstruction = worker_receipt.obstruction
        else:
            raise GovernedEvaluationError("worker-status")
    except (ClosedDslError, GovernedEvaluationError, AttributeError, TypeError, ValueError) as exc:
        obstruction = exc.reason if isinstance(exc, (ClosedDslError, GovernedEvaluationError)) else type(exc).__name__
        outcome = OneShotOutcome.CONFIRMATION_BLOCKED
        outcome_root = _failure_digest(claimed.receipt_digest, obstruction)
        status = GOVERNED_EVALUATION_BLOCKED
        worker_receipt = None
        logger.error("execute_one_shot_closed_evaluation state=BLOCKED reason=%s", obstruction)
    terminal = finalize_one_shot(
        directory,
        reservation_id,
        capability,
        claimed.receipt_digest,
        outcome,
        outcome_root,
    )
    draft = GovernedEvaluationResult(
        status,
        claimed,
        terminal,
        worker_receipt,
        program_root,
        obstruction,
        "",
        GOVERNED_EVALUATION_BOUNDARY,
    )
    result = _bind_result(draft)
    logger.info("execute_one_shot_closed_evaluation state=%s", status)
    logger.debug("execute_one_shot_closed_evaluation exit")
    return result


def validate_governed_evaluation_result(result: object) -> bool:
    """Validate receipt shapes, irreversible transition linkage, and result root."""
    logger.debug("validate_governed_evaluation_result entry type=%s", type(result).__name__)
    try:
        if type(result) is not GovernedEvaluationResult:
            return False
        claimed = result.claimed_ledger
        terminal = result.terminal_ledger
        common = (
            validate_one_shot_receipt(claimed)
            and validate_one_shot_receipt(terminal)
            and claimed.state is OneShotLedgerState.CLAIMED
            and terminal.state in {OneShotLedgerState.CONSUMED, OneShotLedgerState.FAILED}
            and claimed.reservation == terminal.reservation
            and terminal.previous_receipt == claimed.receipt_digest
            and result.boundary == GOVERNED_EVALUATION_BOUNDARY
            and (not result.observer_program_digest or _is_digest(result.observer_program_digest))
            and type(result.obstruction) is str
            and len(result.obstruction) <= 256
            and len(result.obstruction.encode("utf-8")) <= 256
            and _is_digest(result.result_digest)
        )
        if not common:
            return False
        if result.status == GOVERNED_EVALUATION_READY:
            worker = result.worker_receipt
            state_valid = (
                worker is not None
                and validate_closed_receipt(worker)
                and worker.status == READY
                and terminal.state is OneShotLedgerState.CONSUMED
                and terminal.outcome is OneShotOutcome.EVALUATION_COMPLETED
                and terminal.outcome_digest == worker.result_digest
                and result.observer_program_digest == terminal.reservation.observer_program_digest
                and _worker_program_digest(worker) == result.observer_program_digest
                and worker.rows_digest == terminal.reservation.evaluation_rows_digest
                and not result.obstruction
            )
        elif result.status == GOVERNED_EVALUATION_BLOCKED:
            worker = result.worker_receipt
            if worker is None:
                state_valid = (
                    terminal.outcome is OneShotOutcome.CONFIRMATION_BLOCKED
                    and terminal.state is OneShotLedgerState.FAILED
                    and bool(result.obstruction)
                    and terminal.outcome_digest == _failure_digest(claimed.receipt_digest, result.obstruction)
                )
            else:
                state_valid = (
                    validate_closed_receipt(worker)
                    and worker.status == BLOCKED
                    and terminal.outcome is OneShotOutcome.WORKER_BLOCKED
                    and terminal.state is OneShotLedgerState.FAILED
                    and terminal.outcome_digest == worker.result_digest
                    and result.obstruction == worker.obstruction
                    and result.observer_program_digest == terminal.reservation.observer_program_digest
                    and (not worker.rows_digest or worker.rows_digest == terminal.reservation.evaluation_rows_digest)
                )
        else:
            state_valid = False
        valid = state_valid and _bind_result(replace(result, result_digest="")) == result
    except (AttributeError, TypeError, ValueError):
        logger.error("validate_governed_evaluation_result malformed")
        return False
    logger.debug("validate_governed_evaluation_result exit valid=%s", valid)
    return valid


def _failure_digest(claimed_receipt: str, obstruction: str) -> str:
    logger.debug("_failure_digest entry")
    result = digest_data(
        {"claimed_ledger": claimed_receipt, "obstruction": obstruction},
        "veyra.observer-discovery.v3.governed-failure.v1",
    )
    logger.debug("_failure_digest exit")
    return result


def _worker_program_digest(worker_receipt: object) -> str:
    logger.debug("_worker_program_digest entry type=%s", type(worker_receipt).__name__)
    grammar_root = getattr(worker_receipt, "grammar_digest", "")
    terms_root = getattr(worker_receipt, "terms_digest", "")
    if not _is_digest(grammar_root) or not _is_digest(terms_root):
        raise GovernedEvaluationError("worker-program-roots")
    result = digest_data(
        {"grammar_digest": grammar_root, "terms_digest": terms_root},
        "veyra.closed-observer.program-suite.v1",
    )
    logger.debug("_worker_program_digest exit digest=%s", result[:12])
    return result


def _bind_result(result: GovernedEvaluationResult) -> GovernedEvaluationResult:
    logger.debug("_bind_result entry status=%s", result.status)
    digest = digest_data(
        {
            "status": result.status,
            "claimed_ledger": result.claimed_ledger.receipt_digest,
            "terminal_ledger": result.terminal_ledger.receipt_digest,
            "worker_receipt": None if result.worker_receipt is None else result.worker_receipt.result_digest,
            "observer_program": result.observer_program_digest,
            "obstruction": result.obstruction,
            "boundary": result.boundary,
        },
        "veyra.observer-discovery.v3.governed-result.v1",
    )
    bound = replace(result, result_digest=digest)
    logger.debug("_bind_result exit digest=%s", digest[:12])
    return bound


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    valid = type(value) is str and len(value) == 64 and all(character in _HEX for character in value)
    logger.debug("_is_digest exit valid=%s", valid)
    return valid
