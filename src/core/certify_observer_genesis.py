"""Executable level-1 certificate for doctrine-relative P1-E1 genesis."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_genesis import (
    ADAPTER_ID,
    derive_fixed_machine,
    genesis_resource_policy,
    observer_genesis_doctrine,
    observer_genesis_judgment,
    observer_genesis_source,
    oep_admission_record,
    origin_mode_spec,
    recurrence_witness,
    validate_genesis_result,
    witness_scope,
)
from .observer_genesis_types import (
    GenesisJudgment,
    GenesisResourceLimit,
    HistoricalTargetIndependence,
    MachineState,
    OEPAdmission,
    ObserverRole,
    PhysicalInstantiation,
    PremiseStatus,
)

logger = logging.getLogger(__name__)


def _fixture(policy):
    logger.debug("_fixture entry")
    doctrine = observer_genesis_doctrine(policy)
    genealogy = origin_mode_spec()
    machine = derive_fixed_machine(genealogy)
    source = observer_genesis_source(doctrine, genealogy, ADAPTER_ID, machine)
    witness = witness_scope(
        source,
        MachineState("base", "zero"),
        "left",
        "right",
        ("tick",),
        1,
        1,
    )
    recurrence = recurrence_witness(
        source,
        witness,
        ("left", "tick", "reset"),
        ("right", "tick", "reset"),
    )
    result = doctrine, machine, source, witness, recurrence
    logger.debug("_fixture exit")
    return result


def certify_observer_genesis_p1e1() -> Certificate:
    """Certify one finite OEP role without physical, mental, or R11 promotion."""
    logger.debug("certify_observer_genesis_p1e1 entry")
    doctrine, machine, source, witness, recurrence = _fixture(
        genesis_resource_policy(),
    )
    admitted = oep_admission_record(doctrine, OEPAdmission.ADMITTED)
    not_admitted = oep_admission_record(doctrine, OEPAdmission.NOT_ADMITTED)
    positive = observer_genesis_judgment(
        doctrine,
        source,
        witness,
        recurrence,
        admitted,
    )
    if type(positive) is not GenesisJudgment:
        reason = "observer-genesis certificate positive result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    withheld = observer_genesis_judgment(
        doctrine,
        source,
        witness,
        recurrence,
        not_admitted,
    )
    if type(withheld) is not GenesisJudgment:
        reason = "observer-genesis certificate withheld result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    reset_witness = witness_scope(
        source,
        MachineState("base", "zero"),
        "left",
        "right",
        ("reset",),
        1,
        1,
    )
    reset_recurrence = recurrence_witness(
        source,
        reset_witness,
        ("left", "reset"),
        ("right", "reset"),
    )
    reset_case = observer_genesis_judgment(
        doctrine,
        source,
        reset_witness,
        reset_recurrence,
        admitted,
    )
    if type(reset_case) is not GenesisJudgment:
        reason = "observer-genesis certificate reset result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    limited_doctrine, _, limited_source, limited_witness, limited_recurrence = _fixture(
        genesis_resource_policy(max_transition_rows=23),
    )
    limited = observer_genesis_judgment(
        limited_doctrine,
        limited_source,
        limited_witness,
        limited_recurrence,
        oep_admission_record(limited_doctrine, OEPAdmission.ADMITTED),
    )
    if type(limited) is not GenesisResourceLimit:
        reason = "observer-genesis certificate limited result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    fresh = validate_genesis_result(
        doctrine,
        source,
        witness,
        recurrence,
        admitted,
        positive,
    )
    passed = (
        len(machine.rows) == 24
        and all(item.status is PremiseStatus.ESTABLISHED for item in positive.premises)
        and positive.observer_role_relative_to_scope is ObserverRole.ESTABLISHED
        and withheld.observer_role_relative_to_scope is ObserverRole.OPEN
        and reset_case.bounded_persistence is PremiseStatus.REFUTED
        and reset_case.residue_efficacy is PremiseStatus.REFUTED
        and reset_case.observer_role_relative_to_scope is ObserverRole.OPEN
        and not hasattr(limited, "premises")
        and not hasattr(limited, "trace")
        and fresh == positive
        and fresh is not positive
        and fresh.premises is not positive.premises
        and positive.historical_target_independence is HistoricalTargetIndependence.NOT_ESTABLISHED
        and positive.physical_instantiation is PhysicalInstantiation.NOT_ESTABLISHED
    )
    method = (
        "strict primitive AST/native replay plus Mode-only exact 24-row adapter, "
        "bounded BFS, path-relevant recurrence, scoped persistence and exact-index "
        "residue efficacy under explicitly ADMITTED OEP; no E2/R11 shadow, consciousness, "
        "experience, agency, human observer, physical instantiation, target-independent "
        "history, view from nowhere, observer-free truth, absolute existence, universal "
        "self-knowledge, regress closure, novelty, R8, layer, or Sage promotion"
    )
    detail = (
        "fresh whole-table/raw-source replay; six ordered premises; NOT_ADMITTED, "
        "unavailable evidence, or semantic failure leaves the observer role OPEN; "
        "typed preflight refusal has no partial artifact"
    )
    result = Certificate("observer_genesis_p1e1", method, passed, detail, 1)
    logger.debug("certify_observer_genesis_p1e1 exit result=%r", result)
    return result
