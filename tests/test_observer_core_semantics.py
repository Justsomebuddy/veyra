"""Exhaustive small-model tests for R11 partial observer semantics."""

from __future__ import annotations

import os
import pytest

import src.core.observer_core_bridge_report as bridge_report
from src.core.observer_core_bridge_report import read_exact_regular_source
from src.core.observer_core_semantics import ObserverCoreError, echo, infer_observer_kind, observe, validate_closed_recurrence
from src.core.observer_core_types import (
    Apply, Blocked, DomainBlocked, Echo, Input, LeafKind, Mark, MarkValue,
    Mismatch, ObstructionCode, ObserverObstruction, Pair, PairKind, PairValue,
    PathStep, PrimitiveId, Ready, RecurrenceValue,
)
from src.core.observer_core_support import (
    MAX_OBSTRUCTIONS, MAX_OBSTRUCTION_PATH_STEPS, obstruction_data, outcome_data, paths_data, response_data, support_closure,
)
from src.core.observer_core_proof_types import ObserverLawId, ObserverRuleId
from src.core.proof_core_types import Bound, Pulse, Silence


def _recurrences(limit: int = 5):
    rows = [Silence()]
    for _ in range(limit):
        rows.append(Pulse(rows[-1]))
    return tuple(rows)


def _observers(depth: int = 2):
    rows: list[tuple[object, object]] = [(Input(), LeafKind.RECURRENCE)]
    frontier = rows[:]
    for _ in range(depth):
        prior = rows[:]
        added: list[tuple[object, object]] = []
        for observer, kind in frontier:
            if kind is LeafKind.RECURRENCE:
                added.extend(
                    (
                        (Apply(PrimitiveId.TAIL, observer), LeafKind.RECURRENCE),
                        (Apply(PrimitiveId.CREST, observer), LeafKind.MARK),
                    )
                )
        for left, left_kind in prior:
            for right, right_kind in frontier:
                added.append((Pair(left, right), PairKind(left_kind, right_kind)))
        rows.extend(added)
        frontier = added
    return tuple(rows)


def _prefix(step, blocked):
    return Blocked(tuple(ObserverObstruction(item.code, (step,) + item.path) for item in blocked.obstructions))


def _reference(observer, recurrence):
    if type(observer) is Input:
        return Ready(RecurrenceValue(recurrence))
    if type(observer) is Apply:
        child = _reference(observer.child, recurrence)
        step = PathStep.APPLY_TAIL if observer.primitive is PrimitiveId.TAIL else PathStep.APPLY_CREST
        if type(child) is Blocked:
            return _prefix(step, child)
        value = child.value.recurrence
        if observer.primitive is PrimitiveId.TAIL:
            if type(value) is Silence:
                return Blocked((ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (step,)),))
            return Ready(RecurrenceValue(value.tail))
        return Ready(MarkValue(Mark.SILENT if type(value) is Silence else Mark.PULSE))
    left, right = _reference(observer.left, recurrence), _reference(observer.right, recurrence)
    if type(left) is Ready and type(right) is Ready:
        return Ready(PairValue(left.value, right.value))
    left_obs = () if type(left) is Ready else _prefix(PathStep.PAIR_LEFT, left).obstructions
    right_obs = () if type(right) is Ready else _prefix(PathStep.PAIR_RIGHT, right).obstructions
    return Blocked(left_obs + right_obs)


def _reference_echo(observer, left, right):
    lval, rval = _reference(observer, left), _reference(observer, right)
    if type(lval) is Blocked or type(rval) is Blocked:
        return DomainBlocked(
            lval.obstructions if type(lval) is Blocked else (), rval.obstructions if type(rval) is Blocked else ()
        )
    return Echo(lval.value) if lval.value == rval.value else Mismatch(lval.value, rval.value)


def test_kind_inference_and_exhaustive_small_observation_parity():
    observers = _observers()
    assert len(observers) == 18
    for observer, expected_kind in observers:
        assert infer_observer_kind(observer) == expected_kind
        for recurrence in _recurrences():
            assert observe(observer, recurrence) == _reference(observer, recurrence)


def test_exhaustive_small_echo_parity_with_independent_reference():
    for observer, _ in _observers(1):
        for left in _recurrences(4):
            for right in _recurrences(4):
                assert echo(observer, left, right) == _reference_echo(observer, left, right)


def test_mismatch_domain_blockage_and_noncollapse_are_distinct():
    crest = Apply(PrimitiveId.CREST, Input())
    tail = Apply(PrimitiveId.TAIL, Input())
    assert type(echo(crest, Silence(), Pulse(Silence()))) is Mismatch
    blocked = echo(tail, Silence(), Pulse(Silence()))
    assert type(blocked) is DomainBlocked
    assert blocked.left_obstructions and not blocked.right_obstructions
    noncollapse = echo(crest, Pulse(Silence()), Pulse(Pulse(Silence())))
    assert noncollapse == Echo(MarkValue(Mark.PULSE))


def test_mark_response_is_branded_non_scalar_with_stable_serialization():
    value = MarkValue(Mark.PULSE)
    scalar_types = (str, bytes, int, float, bool)
    assert not isinstance(Mark.PULSE, scalar_types)
    assert not isinstance(value, scalar_types)
    assert response_data(value) == {"tag": "mark", "mark": "pulse"}


def test_pair_evaluates_both_branches_and_preserves_ordered_paths():
    tail = Apply(PrimitiveId.TAIL, Input())
    observer = Pair(tail, Pair(Apply(PrimitiveId.CREST, Input()), tail))
    result = observe(observer, Silence())
    assert result == Blocked(
        (
            ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (PathStep.PAIR_LEFT, PathStep.APPLY_TAIL)),
            ObserverObstruction(
                ObstructionCode.TAIL_OF_SILENCE, (PathStep.PAIR_RIGHT, PathStep.PAIR_RIGHT, PathStep.APPLY_TAIL)
            ),
        )
    )


def test_nested_partial_application_and_exact_tail_obstruction():
    observer = Apply(PrimitiveId.TAIL, Apply(PrimitiveId.TAIL, Input()))
    first = observe(observer, Silence())
    second = observe(observer, Pulse(Silence()))
    assert first == Blocked(
        (
            ObserverObstruction(
                ObstructionCode.TAIL_OF_SILENCE,
                (PathStep.APPLY_TAIL, PathStep.APPLY_TAIL),
            ),
        )
    )
    assert second == Blocked(
        (
            ObserverObstruction(
                ObstructionCode.TAIL_OF_SILENCE,
                (PathStep.APPLY_TAIL,),
            ),
        )
    )


def test_invalid_types_open_terms_cycles_and_limits_are_rejected():
    with pytest.raises(ObserverCoreError, match="invalid-primitive-application"):
        infer_observer_kind(Apply(PrimitiveId.CREST, Apply(PrimitiveId.CREST, Input())))
    with pytest.raises(ObserverCoreError, match="non-value-recurrence"):
        validate_closed_recurrence(Bound(0))
    cyclic = Pulse(Silence())
    object.__setattr__(cyclic, "tail", cyclic)
    with pytest.raises(ObserverCoreError, match="circular-recurrence"):
        observe(Input(), cyclic)
    deep = Silence()
    for _ in range(130):
        deep = Pulse(deep)
    with pytest.raises(ObserverCoreError, match="recurrence-resource-limit"):
        observe(Input(), deep)


def test_response_serializer_rejects_cycles_depth_and_open_recurrences():
    cyclic = PairValue(MarkValue(Mark.PULSE), MarkValue(Mark.SILENT))
    object.__setattr__(cyclic, "left", cyclic)
    with pytest.raises(ValueError, match="circular-response-value"):
        response_data(cyclic)
    with pytest.raises(ValueError, match="circular-response-value"):
        outcome_data(Echo(cyclic))
    deep = MarkValue(Mark.PULSE)
    for _ in range(130):
        deep = PairValue(deep, MarkValue(Mark.SILENT))
    with pytest.raises(ValueError, match="response-resource-limit"):
        response_data(deep)
    with pytest.raises(ObserverCoreError, match="non-value-recurrence"):
        response_data(RecurrenceValue(Bound(0)))


def test_support_serializers_reject_protocol_and_attribute_traps_before_access():
    class ProtocolTrap:
        def __len__(self):
            raise AssertionError("len trap")

        def __iter__(self):
            raise AssertionError("iter trap")

        def __repr__(self):
            raise AssertionError("repr trap")

    class AttributeTrap:
        def __getattribute__(self, _name):
            raise AssertionError("attribute trap")

    class TupleTrap(tuple):
        def __iter__(self):
            raise AssertionError("tuple iter trap")

    trap = ProtocolTrap()
    for hostile in (trap, [], iter(()), TupleTrap()):
        with pytest.raises(ValueError, match="invalid-obstruction-paths"):
            paths_data(hostile)
        blocked = Blocked(())
        object.__setattr__(blocked, "obstructions", hostile)
        with pytest.raises(ValueError, match="invalid-blocked-obstructions"):
            outcome_data(blocked)
    domain = DomainBlocked((), ())
    object.__setattr__(domain, "left_obstructions", trap)
    with pytest.raises(ValueError, match="invalid-left-obstructions"):
        outcome_data(domain)
    obstruction = ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (PathStep.APPLY_TAIL,))
    object.__setattr__(obstruction, "path", trap)
    with pytest.raises(ValueError, match="invalid-obstruction"):
        obstruction_data(obstruction)
    with pytest.raises(ValueError, match="invalid-observer-outcome"):
        outcome_data(AttributeTrap())
    for forged in (Ready(trap), Echo(trap), Mismatch(MarkValue(Mark.PULSE), trap)):
        with pytest.raises(ValueError, match="invalid-response-value"):
            outcome_data(forged)
    with pytest.raises(ValueError, match="invalid-support-input"):
        support_closure(trap, ())


def test_support_obstruction_containers_and_paths_are_resource_bounded():
    item = ObserverObstruction(ObstructionCode.TAIL_OF_SILENCE, (PathStep.APPLY_TAIL,))
    with pytest.raises(ValueError, match="invalid-blocked-obstructions"):
        outcome_data(Blocked((item,) * (MAX_OBSTRUCTIONS + 1)))
    unique = tuple(
        ObserverObstruction(item.code, tuple(tuple(PathStep)[i >> (2 * j) & 3] for j in range(6)) + item.path)
        for i in range(MAX_OBSTRUCTIONS + 1)
    )
    with pytest.raises(ValueError, match="invalid-domain-obstructions"):
        outcome_data(DomainBlocked(unique[: MAX_OBSTRUCTIONS // 2], unique[MAX_OBSTRUCTIONS // 2 :]))
    for path in (item.path * (MAX_OBSTRUCTION_PATH_STEPS + 1), (PathStep.PAIR_LEFT,), (PathStep.APPLY_CREST,)):
        with pytest.raises(ValueError, match="invalid-obstruction"):
            obstruction_data(ObserverObstruction(item.code, path))
        with pytest.raises(ValueError, match="invalid-obstruction-paths"):
            paths_data((path,))
    with pytest.raises(ValueError, match="invalid-obstruction-paths"):
        paths_data((item.path,) * (MAX_OBSTRUCTIONS + 1))
    with pytest.raises(ValueError, match="invalid-blocked-obstructions"):
        outcome_data(Blocked((item, item)))
    with pytest.raises(ValueError, match="invalid-obstruction-paths"):
        paths_data((item.path, item.path))
    with pytest.raises(ValueError, match="invalid-blocked-obstructions"):
        outcome_data(Blocked((object(),)))
    with pytest.raises(ValueError, match="invalid-obstruction-paths"):
        paths_data(((object(),),))
    with pytest.raises(ValueError, match="invalid-blocked-obstructions"):
        outcome_data(Blocked(()))
    with pytest.raises(ValueError, match="invalid-domain-obstructions"):
        outcome_data(DomainBlocked((), ()))
    assert paths_data((item.path, (PathStep.PAIR_LEFT, PathStep.APPLY_TAIL))) == [["apply-tail"], ["pair-left", "apply-tail"]]
    assert support_closure((ObserverRuleId.EMBED_R7,), ()) and support_closure((), (ObserverLawId.CREST_PULSE_ECHO,))


def test_exact_source_reader_rejects_symlink_fifo_hardlink_and_path_race(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
):
    payload = b"reviewed-source"
    source = tmp_path / "source.py"
    source.write_bytes(payload)
    assert read_exact_regular_source(source) == payload
    symlink = tmp_path / "symlink.py"
    symlink.symlink_to(source)
    with pytest.raises(ValueError, match="r11-source-file-shape-invalid"):
        read_exact_regular_source(symlink)
    fifo = tmp_path / "source.fifo"
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match="r11-source-file-shape-invalid"):
        read_exact_regular_source(fifo)
    hardlink = tmp_path / "hardlink.py"
    os.link(source, hardlink)
    with pytest.raises(ValueError, match="r11-source-file-shape-invalid"):
        read_exact_regular_source(source)
    hardlink.unlink()
    original_read, replaced = bridge_report.os.read, False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        data = original_read(descriptor, size)
        if not replaced:
            replaced = True
            source.rename(tmp_path / "opened.py")
            source.write_bytes(payload)
        return data

    monkeypatch.setattr(bridge_report.os, "read", racing_read)
    with pytest.raises(ValueError, match="r11-source-file-raced"):
        read_exact_regular_source(source)
