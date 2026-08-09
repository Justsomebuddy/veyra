from src.core.modes import Mode
from src.core.surprise import (
    best_surprise_for_mode,
    find_surprise_witnesses,
    surprise_checklist,
)


def test_best_surprise_for_mode_finds_hidden_edit_lift():
    witness = best_surprise_for_mode(
        Mode.from_word("abababa"), ("a", "b"), max_part_len=3, max_edits=1
    )
    assert witness is not None
    assert witness.part.word == "ab"
    assert witness.surface_observer == "exact-cycle"
    assert witness.hidden_observer == "edit-lift"
    assert witness.surface_saving == 0.0
    assert witness.hidden_saving > 0.0
    assert witness.score > 0.0
    assert witness.as_dict()["obstruction"] == "edit-drift"


def test_find_surprise_witnesses_prefers_multitact_hidden_rhythm():
    witnesses = find_surprise_witnesses(
        ("a", "b"), max_len=7, max_part_len=3, max_edits=1, limit=5
    )
    assert witnesses
    assert all(len(set(item.part.tacts)) > 1 for item in witnesses)
    assert any(item.mode.word == "abababa" for item in witnesses)


def test_no_surprise_when_surface_observer_already_compresses():
    assert (
        best_surprise_for_mode(
            Mode.from_word("ababab"), ("a", "b"), max_part_len=3, max_edits=1
        )
        is None
    )


def test_surprise_checklist_contract():
    assert surprise_checklist() == (
        "surface-observer",
        "hidden-observer",
        "observer-gap-score",
        "edit-lift-witness",
        "negative-if-no-gap",
    )
