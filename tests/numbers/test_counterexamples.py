from src.core.counterexamples import (
    find_echo_splits,
    find_stitch_commutators,
    find_weave_incompatibilities,
)
from src.core.modes import Mode, enumerate_modes


def test_length_split_refined_by_bag():
    modes = [Mode.from_word("ab"), Mode.from_word("aa")]
    splits = find_echo_splits(modes, "length", "bag", limit=1)
    assert splits
    assert {splits[0].left.word, splits[0].right.word} == {"ab", "aa"}


def test_bag_split_refined_by_ordered():
    modes = [Mode.from_word("ab"), Mode.from_word("ba")]
    splits = find_echo_splits(modes, "bag", "ordered", limit=1)
    assert splits
    assert {splits[0].left.word, splits[0].right.word} == {"ab", "ba"}


def test_ordered_stitch_commutator_exists():
    modes = [Mode.from_word("a"), Mode.from_word("b")]
    commutators = find_stitch_commutators(modes, "ordered", limit=1)
    assert commutators
    assert commutators[0].left_then_right.word != commutators[0].right_then_left.word


def test_weave_incompatibility_over_length_echo():
    modes = [Mode.from_word("ab"), Mode.from_word("aa")]
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    found = find_weave_incompatibilities(modes, "length", "length", mapping, limit=1)
    assert found
    assert found[0].output_left.length != found[0].output_right.length


def test_counterexample_search_on_small_space():
    modes = enumerate_modes(("a", "b"), 2, include_silent=False)
    assert find_echo_splits(modes, "length", "ordered", limit=3)
    assert find_stitch_commutators(modes, "ordered", limit=3)
