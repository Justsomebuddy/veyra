"""Captured Lean continuity and hard-first formal replay tests for P3-A1b."""

import logging

import pytest

from src.core.prime_power_productive_bridge import (
    BridgeResourceLimit, FailedBound, ProductiveBridgeValidationError,
    establish_productive_family_bridge, project_residue, refute_offset_program,
    validate_offset_refutation_result, validate_projection_result,
)
from src.core.prime_power_productive_bridge_formal import (
    capture_pressure_sources, capture_sources, compile_pressure_sources, compile_sources,
)
from src.core.prime_power_productive_bridge_package import preflight_charge
from src.core.prime_power_productive_bridge_pressure import PRESSURE_AXIOM_ROWS
from src.core.prime_power_productive_bridge_sources import AXIOM_ROWS
from prime_power_productive_bridge_fixture import exact_a1b_package, exact_offset_pressure

pytestmark = pytest.mark.requires_lean


def test_private_four_phase_lean_replay_and_axiom_rows():
    package = exact_a1b_package()
    outcome = compile_sources(capture_sources(package), 120, 1024 * 1024)
    assert outcome.kind is None
    assert outcome.theorem_axiom_rows == AXIOM_ROWS
    assert len(outcome.phase_receipts) == 6


def test_capture_binds_pomega2_n1_bridge_and_exact_instance():
    captured = capture_sources(exact_a1b_package(p=3, z=-77))
    assert len(captured) == 4
    assert b"p3a1bPrime : VeyraPrimeWitness 3" in captured[3]
    assert b"p3a1bInteger : Int := (-77 : Int)" in captured[3]


def test_hard_first_charge_includes_every_captured_byte():
    package = exact_a1b_package()
    captured = capture_sources(package)
    charge = preflight_charge(package, captured, 9)
    assert charge.captured_bytes == sum(map(len, captured))
    assert charge.requested_depth == 9


def test_valid_low_source_cap_is_typed_resource_not_open_or_refuted():
    value = establish_productive_family_bridge(exact_a1b_package(max_captured_bytes=1))
    assert type(value) is BridgeResourceLimit


def test_nested_oversize_utf8_source_is_rejected_before_compile(monkeypatch):
    package = exact_a1b_package()
    from src.core import prime_power_productive_bridge_formal as formal
    original = formal._read
    def bomb(path):
        if path.name == "VeyraPrimePowerProductiveBridge.lean":
            return b"\xff" + b"x" * 32
        return original(path)
    monkeypatch.setattr(formal, "_read", bomb)
    with pytest.raises(ProductiveBridgeValidationError):
        capture_sources(package)


def test_bool_policy_and_depth_are_rejected_without_cast():
    with pytest.raises(ProductiveBridgeValidationError):
        exact_a1b_package(max_depth=True)


def test_private_pressure_proofs_are_total_and_coherent():
    package = exact_a1b_package()
    captured = capture_pressure_sources(package, exact_offset_pressure(package))
    outcome = compile_pressure_sources(captured, 120, 1024 * 1024)
    assert outcome.kind is None
    assert outcome.theorem_axiom_rows == PRESSURE_AXIOM_ROWS
    assert len(outcome.phase_receipts) == 7


def test_pressure_hard_first_depth_refusal_precedes_pow():
    package = exact_a1b_package(max_depth=1, max_output_bytes=1)
    result = refute_offset_program(package, exact_offset_pressure(package), 4097)
    assert type(result) is BridgeResourceLimit


def test_pressure_depth_7000_has_typed_outcome_without_decimal_conversion():
    package = exact_a1b_package(max_depth=10_000)
    result = refute_offset_program(package, exact_offset_pressure(package), 7000)
    from src.core.prime_power_productive_bridge import BridgeRefutation
    assert type(result) is BridgeRefutation


def test_huge_exact_depth_is_typed_resource_in_both_runtime_lanes():
    package = exact_a1b_package(max_depth=1)
    pressure = exact_offset_pressure(package)
    depth = 1 << 256
    projection = project_residue(package, depth)
    refutation = refute_offset_program(package, pressure, depth)
    for value in (projection, refutation):
        assert type(value) is BridgeResourceLimit
        assert value.failed_bound is FailedBound.REQUESTED_DEPTH
        assert value.required_value == depth
    assert validate_projection_result(package, depth, projection) == projection
    assert validate_offset_refutation_result(package, pressure, depth, refutation) == refutation


def test_hostile_depth_repr_callback_is_never_invoked(caplog):
    class BombInt(int):
        calls = 0

        def __repr__(self):
            type(self).calls += 1
            raise AssertionError("hostile repr")

    caplog.set_level(logging.DEBUG)
    package = exact_a1b_package(max_depth=1)
    pressure = exact_offset_pressure(package)
    for operation in (
        lambda: project_residue(package, BombInt(2)),
        lambda: refute_offset_program(package, pressure, BombInt(2)),
    ):
        with pytest.raises(ProductiveBridgeValidationError):
            operation()
    assert BombInt.calls == 0


def test_unexpected_continuity_runtime_error_propagates(monkeypatch):
    from src.core import prime_power_productive_bridge_formal as formal

    def unexpected(_package):
        raise RuntimeError("unexpected-continuity-probe")

    monkeypatch.setattr(formal, "capture_sources", unexpected)
    with pytest.raises(RuntimeError, match="unexpected-continuity-probe"):
        establish_productive_family_bridge(exact_a1b_package())
