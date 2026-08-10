from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.core.observer_discovery_v3.dsl import closed_rows_digest, observer_program_digest
from src.core.observer_discovery_v3.dsl.types import (
    ClosedObserverGrammar,
    ClosedObserverTerm,
    ClosedWorkerConfig,
)
from src.core.observer_discovery_v3.ledger import (
    OneShotLedgerError,
    OneShotLedgerState,
    OneShotOutcome,
    OneShotReservation,
    reserve_one_shot,
)
from src.core.observer_discovery_v3.schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
)
from src.core.observer_discovery_v3.service import (
    GOVERNED_EVALUATION_BLOCKED,
    GOVERNED_EVALUATION_READY,
    execute_one_shot_closed_evaluation,
    validate_governed_evaluation_result,
)


def digest(symbol: str) -> str:
    return symbol * 64


def grammar() -> ClosedObserverGrammar:
    return ClosedObserverGrammar("governed-grammar", 2, (0,), ("column",), 1, 0, 1)


def terms() -> tuple[ClosedObserverTerm, ...]:
    return (ClosedObserverTerm("column", (0,)),)


def presentation() -> CanonicalPresentation:
    schema = RepresentationSchema(
        "governed-schema",
        (
            RepresentationField("bit", "binary", (0, 1)),
            RepresentationField("kind", "categorical", ("a", "b")),
        ),
        ("no", "yes"),
    )
    rows = tuple(
        RepresentationRow(f"r{i}", f"s{i}", f"c{i}", f"g{i}", values, target)
        for i, (values, target) in enumerate((((0, "a"), "no"), ((1, "b"), "yes"), ((0, "b"), "no"), ((1, "a"), "yes")))
    )
    return canonical_presentation(schema, rows)


def secure_directory(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def reservation(data: CanonicalPresentation, *, program_root: str | None = None) -> OneShotReservation:
    return OneShotReservation(
        "governed-evaluation",
        "burn before closed observer evaluation",
        digest("a"),
        data.payload_digest,
        data.schema_digest,
        closed_rows_digest(tuple(tuple(row.values) for row in data.rows)),
        program_root or observer_program_digest(grammar(), terms()),
        digest("e"),
    )


def test_successful_evaluation_burns_before_worker_and_links_terminal_receipts(tmp_path: Path) -> None:
    data = presentation()
    directory = secure_directory(tmp_path / "ledger")
    capability = b"c" * 32
    reserve_one_shot(directory, reservation(data), capability)

    result = execute_one_shot_closed_evaluation(
        directory,
        "governed-evaluation",
        capability,
        "attempt-1",
        data,
        grammar(),
        terms(),
    )

    assert result.status == GOVERNED_EVALUATION_READY
    assert result.claimed_ledger.state is OneShotLedgerState.CLAIMED
    assert result.terminal_ledger.state is OneShotLedgerState.CONSUMED
    assert result.terminal_ledger.outcome is OneShotOutcome.EVALUATION_COMPLETED
    assert result.worker_receipt is not None
    assert result.worker_receipt.outputs == ((0, 1, 0, 1),)
    assert result.terminal_ledger.outcome_digest == result.worker_receipt.result_digest
    assert validate_governed_evaluation_result(result)


@pytest.mark.parametrize("fault", ("schema", "test", "program"))
def test_root_mismatch_is_detected_only_after_irreversible_claim(tmp_path: Path, fault: str) -> None:
    data = presentation()
    directory = secure_directory(tmp_path / fault)
    capability = b"m" * 32
    request = reservation(data)
    if fault == "schema":
        request = replace(request, schema_digest=digest("1"))
    elif fault == "test":
        request = replace(request, test_commitment=digest("2"))
    else:
        request = replace(request, observer_program_digest=digest("3"))
    reserve_one_shot(directory, request, capability)

    result = execute_one_shot_closed_evaluation(
        directory,
        request.reservation_id,
        capability,
        "attempt-1",
        data,
        grammar(),
        terms(),
    )

    assert result.status == GOVERNED_EVALUATION_BLOCKED
    assert result.worker_receipt is None
    assert result.terminal_ledger.state is OneShotLedgerState.FAILED
    assert result.terminal_ledger.outcome is OneShotOutcome.CONFIRMATION_BLOCKED
    assert validate_governed_evaluation_result(result)
    with pytest.raises(OneShotLedgerError, match="already-claimed"):
        execute_one_shot_closed_evaluation(
            directory,
            request.reservation_id,
            capability,
            "attempt-2",
            data,
            grammar(),
            terms(),
        )


def test_unavailable_strict_worker_is_terminal_failure_after_burn(tmp_path: Path) -> None:
    data = presentation()
    directory = secure_directory(tmp_path / "ledger")
    capability = b"s" * 32
    reserve_one_shot(directory, reservation(data), capability)

    result = execute_one_shot_closed_evaluation(
        directory,
        "governed-evaluation",
        capability,
        "attempt-1",
        data,
        grammar(),
        terms(),
        replace(ClosedWorkerConfig(), isolation_profile="strict"),
    )

    assert result.status == GOVERNED_EVALUATION_BLOCKED
    assert result.worker_receipt is not None
    assert result.worker_receipt.obstruction == "strict-isolation-unavailable"
    assert result.terminal_ledger.outcome is OneShotOutcome.WORKER_BLOCKED
    assert result.terminal_ledger.state is OneShotLedgerState.FAILED
    assert validate_governed_evaluation_result(result)


def test_program_mutation_between_service_preflight_and_worker_is_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.core.observer_discovery_v3.service.governed as governed

    data = presentation()
    directory = secure_directory(tmp_path / "ledger")
    capability = b"t" * 32
    caller_term = ClosedObserverTerm("column", (0,))
    caller_terms = (caller_term,)
    request = replace(
        reservation(data),
        observer_program_digest=observer_program_digest(grammar(), caller_terms),
    )
    reserve_one_shot(directory, request, capability)
    original_worker = governed.run_closed_observers_isolated

    def mutate_then_run(*args: object, **kwargs: object):
        object.__setattr__(caller_term, "indices", (1,))
        return original_worker(*args, **kwargs)

    monkeypatch.setattr(governed, "run_closed_observers_isolated", mutate_then_run)
    result = execute_one_shot_closed_evaluation(
        directory,
        request.reservation_id,
        capability,
        "attempt-1",
        data,
        grammar(),
        caller_terms,
    )

    assert result.status == GOVERNED_EVALUATION_BLOCKED
    assert result.worker_receipt is not None
    assert result.worker_receipt.obstruction == "expected-program-mismatch"
    assert result.worker_receipt.outputs == ()
    assert result.terminal_ledger.outcome is OneShotOutcome.WORKER_BLOCKED
    assert validate_governed_evaluation_result(result)


def test_validator_rejects_worker_or_ledger_transplant(tmp_path: Path) -> None:
    data = presentation()
    directory = secure_directory(tmp_path / "ledger")
    capability = b"f" * 32
    reserve_one_shot(directory, reservation(data), capability)
    result = execute_one_shot_closed_evaluation(
        directory,
        "governed-evaluation",
        capability,
        "attempt-1",
        data,
        grammar(),
        terms(),
    )
    assert result.worker_receipt is not None

    assert not validate_governed_evaluation_result(
        replace(result, worker_receipt=replace(result.worker_receipt, result_digest=digest("0")))
    )
    assert not validate_governed_evaluation_result(
        replace(result, terminal_ledger=replace(result.terminal_ledger, previous_receipt=digest("0")))
    )
    assert not validate_governed_evaluation_result(replace(result, obstruction="x" * 1_000_000))
    assert not validate_governed_evaluation_result(replace(result, obstruction="\ud800"))
