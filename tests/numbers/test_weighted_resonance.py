import pytest

from src.core.modes import Mode
from src.core.weighted_resonance import (
    tact_cost,
    weighted_cyclic_resonates,
    weighted_defects,
    weighted_phase_matches,
    weighted_resonance_profile,
)


def test_tact_cost_uses_exact_directed_and_default():
    costs = {("b", "c"): 0.25}
    assert tact_cost("b", "b", costs) == 0.0
    assert tact_cost("b", "c", costs) == 0.25
    assert tact_cost("c", "b", costs) == 1.0
    with pytest.raises(ValueError):
        tact_cost("a", "b", {}, default_cost=-1)


def test_weighted_defects_record_costs():
    defects = weighted_defects(Mode.from_word("abab"), Mode.from_word("abac"), {("b", "c"): 0.25})
    assert len(defects) == 1
    assert defects[0].index == 3
    assert defects[0].cost == 0.25


def test_weighted_phase_match_prefers_low_cost_shift():
    matches = weighted_phase_matches(Mode.from_word("ab"), Mode.from_word("abac"), {("b", "c"): 0.25})
    assert matches[0].offset == 0
    assert matches[0].total_cost == 0.25


def test_weighted_profile_accepts_cheap_defect():
    profile = weighted_resonance_profile(Mode.from_word("ab"), Mode.from_word("abac"), 0.5, {("b", "c"): 0.25})
    assert profile.resonates
    assert profile.obstruction == "weighted-defect"
    assert profile.best is not None
    assert profile.best.total_cost == 0.25


def test_weighted_profile_rejects_expensive_default():
    profile = weighted_resonance_profile(Mode.from_word("ab"), Mode.from_word("abac"), 0.5, {})
    assert not profile.resonates
    assert profile.obstruction == "over-budget"
    assert profile.best is not None
    assert profile.best.total_cost == 1.0


def test_weighted_exact_and_obstructions():
    assert weighted_resonance_profile(Mode.from_word("ab"), Mode.from_word("baba"), 0.0, {}).obstruction == "none"
    assert weighted_resonance_profile(Mode.from_word(""), Mode.from_word("ab"), 1.0, {}).obstruction == "silent-part"
    assert weighted_resonance_profile(Mode.from_word("ab"), Mode.from_word("aba"), 1.0, {}).obstruction == "length-obstruction"
    assert weighted_cyclic_resonates(Mode.from_word("ab"), Mode.from_word("abac"), 0.5, {("b", "c"): 0.25})
