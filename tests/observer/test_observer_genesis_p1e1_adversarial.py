"""Hostile exactness, transplant, mutation, and preflight pressure for P1-E1."""

from dataclasses import replace
import inspect

import pytest

import src.core.observer_genesis_adapter as adapter
import src.core.observer_genesis_evidence as evidence
import src.core.observer_genesis_result_validation as result_validation
import src.core.observer_genesis_validation as source_validation
from src.core.certify_types import Certificate
from src.core.native_runtime import breath, mode, nod, rez, tact
from src.core.observer_genesis import (
    ADAPTER_ID, BreathSpec, NodSpec, RezSpec, TactSpec, derive_fixed_machine,
    genesis_resource_policy, mode_genealogy, observer_genesis_doctrine,
    observer_genesis_judgment, observer_genesis_source, oep_admission_record,
    origin_mode_spec, recurrence_witness, validate_genesis_result, witness_scope,
)
from src.core.observer_genesis_digest import evidence_digest, machine_digest
from src.core.observer_genesis_native import ObserverGenesisValidationError
from src.core.observer_genesis_types import (
    GenesisJudgment, GenesisResourceBound, GenesisResourceLimit, MachineState,
    ModeSpec, OEPAdmission, PremiseName, PremiseStatus, TransitionRow,
)


def setup(*, policy=None):
    policy = genesis_resource_policy() if policy is None else policy
    doctrine = observer_genesis_doctrine(policy)
    genealogy = origin_mode_spec()
    machine = derive_fixed_machine(genealogy)
    source = observer_genesis_source(doctrine, genealogy, ADAPTER_ID, machine)
    witness = witness_scope(
        source, MachineState("base", "zero"), "left", "right", ("tick",), 1, 1,
    )
    recurrence = recurrence_witness(
        source, witness, ("left", "tick", "reset"),
        ("right", "tick", "reset"),
    )
    oep = oep_admission_record(doctrine, OEPAdmission.ADMITTED)
    return doctrine, genealogy, machine, source, witness, recurrence, oep


def redigest(machine, **changes):
    provisional = replace(machine, **changes, machine_digest="0" * 64)
    return replace(provisional, machine_digest=machine_digest(provisional))


class ModeSpecSubclass(ModeSpec):
    pass


class DuckGenealogy:
    breath = ()


def test_native_dto_subclass_duck_callable_and_raw_target_are_not_source_evidence():
    doctrine, genealogy, machine, _, _, _, _ = setup()
    native_rez = rez("origin")
    native_nod = nod(native_rez, "origin")
    native_breath = breath(tact(native_nod, native_nod, "cycle"))
    native_mode = mode(native_breath, None)
    aliens = (
        native_rez, native_nod, native_breath, native_mode,
        DuckGenealogy(), lambda: genealogy, ("target",),
    )
    for alien in aliens:
        with pytest.raises(ObserverGenesisValidationError):
            derive_fixed_machine(alien)  # type: ignore[arg-type]
    subclass = ModeSpecSubclass(
        genealogy.version, genealogy.breath, genealogy.genealogy_digest,
    )
    with pytest.raises(ObserverGenesisValidationError, match="mode-spec-must-be-exact"):
        observer_genesis_source(doctrine, subclass, ADAPTER_ID, machine)
    with pytest.raises(ObserverGenesisValidationError, match="adapter"):
        observer_genesis_source(doctrine, genealogy, lambda: ADAPTER_ID, machine)  # type: ignore[arg-type]


def test_empty_surrogate_noncontiguous_open_and_cyclic_genealogy_reject():
    def one(start, end):
        return BreathSpec((TactSpec(start, end, "cycle"),))

    good = NodSpec(RezSpec("origin"), "origin")
    for bad in (NodSpec(RezSpec(""), "origin"), NodSpec(RezSpec("\ud800"), "origin")):
        with pytest.raises(ObserverGenesisValidationError):
            mode_genealogy(one(bad, bad))
    other = NodSpec(RezSpec("other"), "other")
    with pytest.raises(ObserverGenesisValidationError, match="strictly-closed"):
        mode_genealogy(one(good, other))
    broken = BreathSpec((
        TactSpec(good, other, "out"), TactSpec(good, good, "back"),
    ))
    with pytest.raises(ObserverGenesisValidationError, match="noncontiguous"):
        mode_genealogy(broken)
    cyclic = origin_mode_spec()
    object.__setattr__(cyclic, "breath", cyclic)
    with pytest.raises(ObserverGenesisValidationError, match="breath-spec-must-be-exact"):
        derive_fixed_machine(cyclic)


def test_missing_reordered_duplicate_and_foreign_machine_semantics_reject():
    doctrine, genealogy, machine, _, _, _, _ = setup()
    variants = (
        redigest(machine, rows=machine.rows[:-1]),
        redigest(machine, rows=tuple(reversed(machine.rows))),
        redigest(machine, control_states=("base", "base")),
        redigest(
            machine,
            rows=(replace(machine.rows[0], next_control="foreign"),) + machine.rows[1:],
        ),
        replace(machine, machine_digest="0" * 64),
    )
    for variant in variants:
        with pytest.raises(ObserverGenesisValidationError):
            observer_genesis_source(doctrine, genealogy, ADAPTER_ID, variant)


def test_full_but_decorative_constant_machine_is_rejected_by_semantic_adapter_compare():
    doctrine, genealogy, machine, _, _, _, _ = setup()
    rows = tuple(TransitionRow(
        row.control, row.residue, row.coupling, row.control, row.residue, "idle",
    ) for row in machine.rows)
    decorative = redigest(machine, rows=rows)
    with pytest.raises(ObserverGenesisValidationError, match="whole-table-adapter-output"):
        observer_genesis_source(doctrine, genealogy, ADAPTER_ID, decorative)


def test_doctrine_source_witness_recurrence_and_oep_transplants_reject():
    first = setup()
    second = setup(policy=genesis_resource_policy(max_encoded_bytes=16_383))
    d1, _, _, s1, w1, r1, o1 = first
    d2, _, _, s2, w2, _, o2 = second
    with pytest.raises(ObserverGenesisValidationError, match="source.*transplant"):
        observer_genesis_judgment(d2, s1, w1, r1, o2)
    with pytest.raises(ObserverGenesisValidationError, match="witness-scope-drift-or-transplant"):
        observer_genesis_judgment(d2, s2, w1, r1, o2)
    with pytest.raises(ObserverGenesisValidationError, match="recurrence-witness-drift-or-transplant"):
        observer_genesis_judgment(d2, s2, w2, r1, o2)
    with pytest.raises(ObserverGenesisValidationError, match="oep-record-drift-or-transplant"):
        observer_genesis_judgment(d1, s1, w1, r1, o2)
    assert o1.oep_digest != o2.oep_digest


def test_invalid_scope_indices_continuations_and_return_words_reject():
    _, _, _, source, witness, _, _ = setup()
    invalid_witnesses = (
        ("left", "left", ("tick",), 1, 1),
        ("left", "right", (), 0, 1),
        ("left", "right", ("tick",), True, 1),
        ("left", "right", ("tick",), 1, 0),
        ("left", "right", ("foreign",), 1, 1),
    )
    for left, right, continuation, horizon, index in invalid_witnesses:
        with pytest.raises(ObserverGenesisValidationError):
            witness_scope(
                source, MachineState("base", "zero"), left, right,
                continuation, horizon, index,
            )
    invalid_words = (
        ((), ("right", "tick")),
        (("tick",), ("right", "tick")),
        (("left", "reset"), ("right", "tick")),
        (("left", "tick", "foreign"), ("right", "tick")),
    )
    for left, right in invalid_words:
        with pytest.raises(ObserverGenesisValidationError):
            recurrence_witness(source, witness, left, right)


def test_valid_but_unreachable_witness_state_is_rejected_by_fresh_bfs():
    doctrine, _, _, source, _, _, oep = setup()
    witness = witness_scope(
        source, MachineState("marked", "zero"), "left", "right", ("tick",), 1, 1,
    )
    recurrence = recurrence_witness(
        source, witness, ("left", "tick", "reset"),
        ("right", "tick", "reset"),
    )
    with pytest.raises(
        ObserverGenesisValidationError, match="witness-evidence-state-unreachable",
    ):
        observer_genesis_judgment(doctrine, source, witness, recurrence, oep)


def test_result_outer_and_nested_mutation_reject_before_unbounded_row_walk(monkeypatch):
    doctrine, _, _, source, witness, recurrence, oep = setup()
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("deep row walk before exact outer length binding")

    monkeypatch.setattr(result_validation, "_row", forbidden)
    huge = replace(result.premises[3], rows=result.premises[3].rows * 50_000)
    forged = replace(result, premises=result.premises[:3] + (huge,) + result.premises[4:])
    with pytest.raises(ObserverGenesisValidationError, match="outer-precheck"):
        validate_genesis_result(doctrine, source, witness, recurrence, oep, forged)
    with pytest.raises(ObserverGenesisValidationError, match="outer-precheck"):
        validate_genesis_result(
            doctrine, source, witness, recurrence, oep,
            replace(result, judgment_digest="0" * 64),
        )
    assert calls == []


def test_resource_astronomical_forgery_is_expected_bound_before_any_hash():
    policy = genesis_resource_policy(max_transition_rows=23)
    doctrine, _, _, source, witness, recurrence, oep = setup(policy=policy)
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisResourceLimit)
    forged = replace(result, required_value=10**100_000)
    with pytest.raises(ObserverGenesisValidationError, match="outer-precheck"):
        validate_genesis_result(doctrine, source, witness, recurrence, oep, forged)
    assert not hasattr(result_validation, "refusal_digest")


@pytest.mark.parametrize(("caps", "bound"), (
    ({"max_transition_rows": 23}, GenesisResourceBound.TRANSITION_ROWS),
    ({"max_reachability_checks": 23}, GenesisResourceBound.REACHABILITY_CHECKS),
    ({"max_continuation_steps": 1}, GenesisResourceBound.CONTINUATION_STEPS),
    ({"max_return_word_steps": 5}, GenesisResourceBound.RETURN_WORD_STEPS),
    ({"max_response_checks": 3}, GenesisResourceBound.RESPONSE_CHECKS),
    ({"max_encoded_bytes": 0}, GenesisResourceBound.ENCODED_BYTES),
))
def test_each_early_refusal_precedes_adapter_table_bfs_and_step(monkeypatch, caps, bound):
    doctrine, _, _, source, witness, recurrence, oep = setup(
        policy=genesis_resource_policy(**caps),
    )
    calls = []

    def forbidden(*args):
        calls.append(args)
        raise AssertionError("semantic source/evidence replay before resource preflight")

    monkeypatch.setattr(source_validation, "_derive_machine", forbidden)
    monkeypatch.setattr(source_validation, "snapshot_machine", forbidden)
    monkeypatch.setattr(adapter, "_row", forbidden)
    monkeypatch.setattr(evidence, "_table", forbidden)
    monkeypatch.setattr(evidence, "_step", forbidden)
    monkeypatch.setattr(evidence, "reachable_states", forbidden)
    result = observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    assert isinstance(result, GenesisResourceLimit)
    assert result.failed_bound is bound
    assert calls == []


def test_target_selection_never_promotes_history_and_api_has_no_target_channel():
    target = "left"
    doctrine, _, _, source, witness, recurrence, oep = setup()
    chosen = source if target == "left" else None
    result = observer_genesis_judgment(doctrine, chosen, witness, recurrence, oep)
    assert isinstance(result, GenesisJudgment)
    assert result.historical_target_independence.value == "not-established"
    assert result.physical_instantiation.value == "not-established"
    assert "target" not in inspect.signature(observer_genesis_judgment).parameters


def test_unexpected_step_exception_propagates_and_prior_results_are_not_evidence(monkeypatch):
    doctrine, _, _, source, witness, recurrence, oep = setup()

    def explode(*args):
        raise RuntimeError("unexpected-step")

    monkeypatch.setattr(evidence, "_step", explode)
    with pytest.raises(RuntimeError, match="unexpected-step"):
        observer_genesis_judgment(doctrine, source, witness, recurrence, oep)
    prior = Certificate("prior", "not raw evidence", True, "", 1)
    with pytest.raises(ObserverGenesisValidationError):
        observer_genesis_judgment(doctrine, source, witness, prior, oep)  # type: ignore[arg-type]


def test_evidence_digest_frames_ambiguous_component_boundaries():
    first = TransitionRow("a", "bc", "c", "q", "r", "idle")
    second = TransitionRow("ab", "c", "c", "q", "r", "idle")
    left = evidence_digest(
        PremiseName.STRUCTURAL_CLOSURE, PremiseStatus.ESTABLISHED, (first,), (),
    )
    right = evidence_digest(
        PremiseName.STRUCTURAL_CLOSURE, PremiseStatus.ESTABLISHED, (second,), (),
    )
    assert left != right
