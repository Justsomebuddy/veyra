from src.core.compatibility import unary_respects
from src.core.modes import Mode, TEST_FAMILIES, echo_equivalent, enumerate_modes
from src.core.weave import cyclic_representative, cyclic_weave, ordered_weave


def test_cyclic_representative_normalizes_rotations():
    assert cyclic_representative(Mode.from_word("ba")) == Mode.from_word("ab")
    assert cyclic_representative(Mode.from_word("baba")) == Mode.from_word("abab")


def test_ordered_weave_differs_by_cut_but_cycle_echoes():
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    ab = ordered_weave(Mode.from_word("ab"), mapping)
    ba = ordered_weave(Mode.from_word("ba"), mapping)
    assert ab == Mode.from_word("xyy")
    assert ba == Mode.from_word("yyx")
    assert not echo_equivalent(ab, ba, TEST_FAMILIES["ordered"])
    assert echo_equivalent(ab, ba, TEST_FAMILIES["cycle"])


def test_cyclic_weave_picks_same_word_for_rotations():
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    assert cyclic_weave(Mode.from_word("ab"), mapping) == cyclic_weave(Mode.from_word("ba"), mapping)


def test_cyclic_weave_compatibility_claims():
    modes = enumerate_modes(("a", "b"), 3, include_silent=False)
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    ordered_schema = lambda mode: ordered_weave(mode, mapping)
    cyclic_schema = lambda mode: cyclic_weave(mode, mapping)
    assert unary_respects(modes, ordered_schema, "cycle", "cycle", "ordered_weave")
    assert not unary_respects(modes, ordered_schema, "cycle", "ordered", "ordered_weave")
    assert unary_respects(modes, cyclic_schema, "cycle", "ordered", "cyclic_weave")
