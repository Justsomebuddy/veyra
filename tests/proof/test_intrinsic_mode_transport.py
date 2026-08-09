import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.intrinsic_mode_laws import (
    recurrence_stitch, recurrence_weave, stitch_transport, successor_transport,
    transport_law_rows, weave_transport, zero_transport,
)
from src.core.intrinsic_mode_transport import (
    OBSERVER_NAME, ORIGIN_NAME, SUCCESSOR_MARK, IntrinsicMode, decode_mode,
    encode_recurrence, recurrence_equal, verify_intrinsic_mode,
)
from src.core.native_runtime import Breath, Mode, NativeObstruction, Nod, Rez, Tact
from src.core.proof_core_types import Bound, Pulse, Silence, Stitch, Weave
from src.core.paths import PROJECT_ROOT


def _pulse_chain(depth):
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    return result


@pytest.mark.parametrize("depth", [0, 1, 2, 7, 31])
def test_exact_both_round_trips_over_canonical_image(depth):
    recurrence = _pulse_chain(depth)
    encoded = encode_recurrence(recurrence)
    decoded = decode_mode(encoded.native)
    assert type(decoded) is IntrinsicMode
    assert recurrence_equal(decoded.recurrence, recurrence)
    assert encode_recurrence(decoded.recurrence).native == encoded.native
    assert verify_intrinsic_mode(encoded)


def test_encoder_is_stack_safe_beyond_python_recursion_limit():
    recurrence = _pulse_chain(2500)
    encoded = encode_recurrence(recurrence)
    decoded = decode_mode(encoded.native)
    assert type(decoded) is IntrinsicMode
    assert recurrence_equal(recurrence, decoded.recurrence)


def test_native_operation_transport_is_stack_safe_beyond_recursion_limit():
    deep = _pulse_chain(1100)
    assert stitch_transport(deep, Silence()).holds
    assert weave_transport(Pulse(Silence()), deep).holds
    assert successor_transport(deep).holds


@pytest.mark.parametrize("term", [
    Bound(0), Stitch(Silence(), Silence()), Weave(Silence(), Silence()), Pulse(Bound(0)),
])
def test_non_value_proof_syntax_is_rejected(term):
    with pytest.raises(ValueError, match="noncanonical-recurrence-value"):
        encode_recurrence(term)


def test_circular_pulse_value_is_rejected_even_when_compared_to_silence():
    circular = Pulse(Silence())
    object.__setattr__(circular, "tail", circular)
    with pytest.raises(ValueError, match="cyclic-recurrence-value"):
        encode_recurrence(circular)
    with pytest.raises(ValueError, match="cyclic-recurrence-value"):
        recurrence_equal(circular, Silence())


def test_direct_wrapper_forgery_is_rejected_at_construction():
    valid = encode_recurrence(Silence())
    with pytest.raises(ValueError, match="forged-intrinsic-mode-wrapper"):
        replace(valid, digest="0" * 64)


def _anchor(name=ORIGIN_NAME, mark=ORIGIN_NAME):
    return Nod(Rez(name), mark)


@pytest.mark.parametrize("value,reason", [
    (object(), "foreign-mode-type"),
    (Mode(Breath((), None), OBSERVER_NAME), "zero-anchor-mismatch"),
    (Mode(Breath((), _anchor("foreign", "foreign")), OBSERVER_NAME), "zero-anchor-mismatch"),
    (Mode(Breath((), _anchor()), "forged-observer"), "observer-mismatch"),
    (Mode(Breath([Tact(_anchor(), _anchor(), SUCCESSOR_MARK)], None), OBSERVER_NAME), "noncanonical-tact-container"),
    (Mode(Breath((Tact(_anchor(), _anchor(), "touch"),), None), OBSERVER_NAME), "foreign-recurrence-tact"),
    (Mode(Breath((Tact(_anchor(), _anchor("other", "other"), SUCCESSOR_MARK),), None), OBSERVER_NAME), "foreign-recurrence-tact"),
    (Mode(Breath((Tact(_anchor(), _anchor(), SUCCESSOR_MARK),), _anchor()), OBSERVER_NAME), "nonzero-anchor-present"),
])
def test_hostile_native_modes_fail_closed_with_exact_reason(value, reason):
    result = decode_mode(value)
    assert type(result) is NativeObstruction
    assert result.reason == reason


def test_generic_two_node_closed_cycle_is_not_the_intrinsic_image():
    first, second = _anchor("a", "a"), _anchor("b", "b")
    generic = Mode(Breath((Tact(first, second), Tact(second, first))), OBSERVER_NAME)
    result = decode_mode(generic)
    assert type(result) is NativeObstruction
    assert result.reason == "foreign-recurrence-tact"


@pytest.mark.parametrize(
    "left_depth,right_depth", [(left, right) for left in range(7) for right in range(7)],
)
def test_structural_stitch_and_weave_rows(left_depth, right_depth):
    left, right = _pulse_chain(left_depth), _pulse_chain(right_depth)
    assert recurrence_equal(
        decode_mode(encode_recurrence(recurrence_stitch(left, right)).native).recurrence,
        recurrence_stitch(left, right),
    )
    assert recurrence_equal(
        decode_mode(encode_recurrence(recurrence_weave(left, right)).native).recurrence,
        recurrence_weave(left, right),
    )
    assert stitch_transport(left, right).holds
    assert weave_transport(left, right).holds
    assert successor_transport(left).holds


def test_all_executable_transport_rows_hold_with_honest_boundary():
    rows = transport_law_rows()
    assert {row.law_id for row in rows} == {
        "R9-LAW-ZERO", "R9-LAW-SUCCESSOR", "THM-R9-005", "THM-R9-006", "THM-R9-008",
    }
    assert all(row.holds and row.expected_digest == row.native_digest for row in rows)
    assert all("cyclic phase" in row.boundary for row in rows)


def test_zero_and_successor_transport_are_explicit_not_inferred_from_weave():
    assert zero_transport().holds
    assert all(successor_transport(_pulse_chain(depth)).holds for depth in range(12))


def test_transport_nucleus_ast_has_no_school_arithmetic_shortcuts():
    blocked_calls = {"len", "int", "range", "sum", "pow", "gcd"}
    blocked_ops = (ast.Mod, ast.Pow, ast.FloorDiv)
    for name in ("intrinsic_mode_transport.py", "intrinsic_mode_laws.py"):
        source = (PROJECT_ROOT / "src/core" / name).read_text()
        tree = ast.parse(source)
        calls = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not calls & blocked_calls
        assert not any(isinstance(node, blocked_ops) for node in ast.walk(tree))
