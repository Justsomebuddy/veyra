import pytest

from src.core.approx_resonance import (
    approximate_cyclic_resonates,
    approximate_phase_matches,
    approximate_resonance_profile,
    defect_list,
)
from src.core.modes import Mode


def test_defect_list_records_positions():
    defects = defect_list(Mode.from_word("abab"), Mode.from_word("abac"))
    assert len(defects) == 1
    assert defects[0].index == 3
    assert defects[0].expected == "b"
    assert defects[0].actual == "c"


def test_defect_list_requires_equal_length():
    with pytest.raises(ValueError):
        defect_list(Mode.from_word("ab"), Mode.from_word("aba"))


def test_approximate_phase_match_finds_best_defect():
    matches = approximate_phase_matches(Mode.from_word("ab"), Mode.from_word("abac"))
    assert matches[0].offset == 0
    assert matches[0].defect_count == 1


def test_approximate_resonance_accepts_bounded_defect():
    profile = approximate_resonance_profile(Mode.from_word("ab"), Mode.from_word("abac"), max_defects=1)
    assert profile.resonates
    assert profile.obstruction == "bounded-defect"
    assert profile.best is not None
    assert profile.best.defect_count == 1


def test_approximate_resonance_rejects_over_budget():
    profile = approximate_resonance_profile(Mode.from_word("ab"), Mode.from_word("abcc"), max_defects=1)
    assert not profile.resonates
    assert profile.obstruction == "over-budget"
    assert profile.best is not None
    assert profile.best.defect_count == 2


def test_approximate_resonance_preserves_exact_none():
    profile = approximate_resonance_profile(Mode.from_word("ab"), Mode.from_word("baba"), max_defects=1)
    assert profile.resonates
    assert profile.obstruction == "none"
    assert profile.best is not None
    assert profile.best.defect_count == 0


def test_approximate_resonance_obstructions_and_api():
    assert approximate_resonance_profile(Mode.from_word(""), Mode.from_word("ab"), 1).obstruction == "silent-part"
    assert approximate_resonance_profile(Mode.from_word("ab"), Mode.from_word("aba"), 1).obstruction == "length-obstruction"
    assert approximate_cyclic_resonates(Mode.from_word("ab"), Mode.from_word("abac"), 1)
    assert not approximate_cyclic_resonates(Mode.from_word("ab"), Mode.from_word("abac"), 0)
