"""Positive laws, scoped counterfactuals, and resource boundary for P1-E1."""

import src.core.observer_genesis_evidence as evidence
from src.core.observer_genesis import (
    ADAPTER_ID, derive_fixed_machine, genesis_resource_policy,
    observer_genesis_doctrine, observer_genesis_judgment,
    observer_genesis_source, oep_admission_record, origin_mode_spec,
    recurrence_witness, unavailable_recurrence, validate_genesis_result,
    witness_scope,
)
from src.core.observer_genesis_types import (
    GenesisJudgment, GenesisResourceBound, GenesisResourceLimit, MachineState,
    OEPAdmission, ObserverRole, PremiseName, PremiseStatus,
)


def setup(*, admission=OEPAdmission.ADMITTED, policy=None, continuation=("tick",)):
    policy = genesis_resource_policy() if policy is None else policy
    doctrine = observer_genesis_doctrine(policy)
    genealogy = origin_mode_spec()
    machine = derive_fixed_machine(genealogy)
    source = observer_genesis_source(doctrine, genealogy, ADAPTER_ID, machine)
    witness = witness_scope(
        source, MachineState("base", "zero"), "left", "right",
        continuation, len(continuation), 1,
    )
    left = ("left",) + continuation + ("reset",)
    right = ("right",) + continuation + ("reset",)
    recurrence = recurrence_witness(source, witness, left, right)
    oep = oep_admission_record(doctrine, admission)
    return doctrine, genealogy, machine, source, witness, recurrence, oep


def test_fixed_mode_only_adapter_has_exact_ordered_24_row_semantics():
    _, _, machine, _, _, _, _ = setup()
    assert machine.control_states == ("base", "marked")
    assert machine.residues == ("zero", "L", "R")
    assert machine.couplings == ("left", "right", "tick", "reset")
    assert len(machine.rows) == 2 * 3 * 4 == 24
    keys = tuple(
        (q, r, c)
        for q in machine.control_states
        for r in machine.residues
        for c in machine.couplings
    )
    assert tuple((row.control, row.residue, row.coupling) for row in machine.rows) == keys
    table = {(row.control, row.residue, row.coupling): row for row in machine.rows}
    assert table[("base", "zero", "left")].next_residue == "L"
    assert table[("base", "zero", "right")].next_residue == "R"
    assert table[("base", "L", "tick")].response == "effect-L"
    assert table[("base", "R", "tick")].response == "effect-R"
    assert all(row.response == "reset" for row in machine.rows if row.coupling == "reset")


def test_admitted_oep_establishes_exact_scoped_role_and_all_six_premises():
    doctrine, _, _, source, witness, recurrence, oep = setup()
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert tuple(item.premise for item in result.premises) == tuple(PremiseName)
    assert all(item.status is PremiseStatus.ESTABLISHED for item in result.premises)
    assert result.observer_role_relative_to_scope is ObserverRole.ESTABLISHED
    discrimination = result.premises[3]
    assert len(discrimination.rows) == 2
    assert discrimination.rows[0] is not discrimination.rows[1]
    assert discrimination.rows[0].next_control == discrimination.rows[1].next_control
    assert discrimination.rows[0].next_residue != discrimination.rows[1].next_residue
    efficacy = result.premises[5]
    assert {row.response for row in efficacy.rows} == {"effect-L", "effect-R"}


def test_not_admitted_oep_keeps_role_open_despite_complete_evidence():
    doctrine, _, _, source, witness, recurrence, oep = setup(
        admission=OEPAdmission.NOT_ADMITTED,
    )
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert all(item.status is PremiseStatus.ESTABLISHED for item in result.premises)
    assert result.observer_role_relative_to_scope is ObserverRole.OPEN


def test_actual_return_is_path_relevant_and_failure_refutes_only_recurrence():
    doctrine, _, _, source, witness, _, oep = setup()
    recurrence = recurrence_witness(
        source, witness, ("left", "tick"), ("right", "tick"),
    )
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert result.recurrent_return is PremiseStatus.REFUTED
    assert result.counterfactual_discrimination is PremiseStatus.ESTABLISHED
    assert result.observer_role_relative_to_scope is ObserverRole.OPEN


def test_explicit_unavailable_recurrence_is_open_not_refuted():
    doctrine, _, _, source, witness, _, oep = setup()
    unavailable = unavailable_recurrence(source, witness)
    result = observer_genesis_judgment(doctrine, source, witness, unavailable, oep)
    assert isinstance(result, GenesisJudgment)
    assert result.recurrent_return is PremiseStatus.OPEN
    assert all(item.status is PremiseStatus.ESTABLISHED for item in result.premises if item.premise is not PremiseName.RECURRENT_RETURN)
    assert result.observer_role_relative_to_scope is ObserverRole.OPEN


def test_transient_reset_refutes_persistence_and_efficacy_not_observer_existence():
    doctrine, _, _, source, witness, recurrence, oep = setup(continuation=("reset",))
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert result.counterfactual_discrimination is PremiseStatus.ESTABLISHED
    assert result.recurrent_return is PremiseStatus.ESTABLISHED
    assert result.bounded_persistence is PremiseStatus.REFUTED
    assert result.residue_efficacy is PremiseStatus.REFUTED
    assert result.observer_role_relative_to_scope is ObserverRole.OPEN


def test_persistent_but_inert_residue_refutes_exact_index_efficacy():
    doctrine, _, _, source, witness, _, oep = setup(continuation=("left",))
    recurrence = recurrence_witness(
        source, witness,
        ("left", "left", "reset"), ("right", "left", "reset"),
    )
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert result.bounded_persistence is PremiseStatus.ESTABLISHED
    assert result.residue_efficacy is PremiseStatus.REFUTED
    assert result.observer_role_relative_to_scope is ObserverRole.OPEN


def test_resource_refusal_precedes_step_bfs_and_has_no_partial_premises(monkeypatch):
    policy = genesis_resource_policy(max_transition_rows=23)
    doctrine, _, _, source, witness, recurrence, oep = setup(policy=policy)
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("evidence replay before preflight")

    monkeypatch.setattr(evidence, "_step", forbidden)
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisResourceLimit)
    assert result.failed_bound is GenesisResourceBound.TRANSITION_ROWS
    assert (result.required_value, result.allowed_value) == (24, 23)
    assert calls == []
    assert not hasattr(result, "premises") and not hasattr(result, "trace")
    assert not hasattr(result, "observer_role_relative_to_scope")


def test_fresh_raw_revalidation_replays_and_returns_fresh_nested_artifacts():
    doctrine, _, _, source, witness, recurrence, oep = setup()
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    fresh = validate_genesis_result(doctrine, source, witness, recurrence, oep, result)
    assert fresh == result and fresh is not result
    assert fresh.premises is not result.premises
    assert fresh.premises[3] is not result.premises[3]
    assert fresh.premises[3].rows is not result.premises[3].rows
