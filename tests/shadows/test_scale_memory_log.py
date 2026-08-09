from subprocess import run
import sys

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.scale_memory_log import finite_field_log_fixture, recover_cyclic_depth, recover_transition_depth, scale_memory_log_checklist, scale_memory_obstruction_card, transition_depth_rows


def test_exact_transition_depth_recovery():
    cert = recover_transition_depth("doubling-exact", ratio_from_ints(2), ratio_from_ints(32), 10)
    assert cert.status == "exact"
    assert cert.obstruction == "none"
    assert cert.candidate.depth == 5
    assert ratio_shadow(cert.candidate.residual) == 0


def test_residual_transition_depth_recovery():
    cert = recover_transition_depth("doubling-residual", ratio_from_ints(2), ratio_from_ints(20), 6, ratio_from_ints(4))
    assert cert.status == "approximate"
    assert cert.candidate.depth == 4
    assert ratio_shadow(cert.candidate.value) == 16
    assert ratio_shadow(cert.candidate.residual) == 4


def test_blocked_transition_depth_reports_residual_gap():
    cert = recover_transition_depth("outside-band", ratio_from_ints(3), ratio_from_ints(11), 3, ratio_from_ints(1))
    assert cert.status == "blocked"
    assert cert.obstruction == "residual-gap"


def test_cyclic_unwrap_fixture_recovers_depth():
    cert = finite_field_log_fixture()
    assert cert.status == "exact"
    assert cert.candidate_depth == 17
    assert cert.candidate_value == 83


def test_cyclic_obstruction_card_reports_cycle_collapse():
    cert = scale_memory_obstruction_card()
    assert cert.status == "blocked"
    assert cert.obstruction == "cycle-collapse"
    assert cert.cycle_length == 1


def test_invalid_inputs_are_rejected():
    try:
        transition_depth_rows("", ratio_from_ints(2), ratio_from_ints(4), 3)
    except ValueError as exc:
        assert "label" in str(exc)
    else:
        raise AssertionError("empty labels must be rejected")
    try:
        recover_cyclic_depth("bad", 2, 1, 1, 3)
    except ValueError as exc:
        assert "modulus" in str(exc)
    else:
        raise AssertionError("invalid modulus must be rejected")


def test_scale_memory_log_checklist_and_demo_script():
    assert len(scale_memory_log_checklist()) == 4
    proc = run([sys.executable, "scripts/scale_memory_log_demo.py"], check=True, capture_output=True, text=True)
    assert "[1/5]" in proc.stdout
    assert '"candidate_depth": 17' in proc.stdout
    assert "[done] errors=0" in proc.stdout
