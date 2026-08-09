from src.core.modes import (
    TEST_FAMILIES,
    Mode,
    cyclic_observer,
    echo_equivalent,
    enumerate_modes,
    is_ordered_primitive,
    natural_mode,
    natural_shadow,
    ordered_resonates_inside,
    primitive_root,
    repeat_mode,
    substitute_mode,
    weave_by_length,
)


def test_enumerate_two_tact_modes_count():
    modes = enumerate_modes(("a", "b"), 2)
    assert len(modes) == 7
    assert Mode.from_word("") in modes
    assert Mode.from_word("ab") in modes


def test_echo_test_families_split_identity():
    ab = Mode.from_word("ab")
    ba = Mode.from_word("ba")
    aa = Mode.from_word("aa")
    assert echo_equivalent(ab, ba, TEST_FAMILIES["length"])
    assert echo_equivalent(ab, ba, TEST_FAMILIES["bag"])
    assert not echo_equivalent(ab, aa, TEST_FAMILIES["bag"])
    assert not echo_equivalent(ab, ba, TEST_FAMILIES["ordered"])
    assert echo_equivalent(ab, ba, TEST_FAMILIES["cycle"])


def test_cyclic_observer_canonicalizes_rotation():
    assert cyclic_observer(Mode.from_word("aba")) == cyclic_observer(Mode.from_word("baa"))


def test_primitive_root_and_ordered_primitivity():
    root, exponent = primitive_root(Mode.from_word("abab"))
    assert root == Mode.from_word("ab")
    assert exponent == 2
    assert is_ordered_primitive(Mode.from_word("ab"))
    assert not is_ordered_primitive(Mode.from_word("aaaa"))
    assert not is_ordered_primitive(Mode.from_word(""))


def test_ordered_resonance():
    assert ordered_resonates_inside(Mode.from_word("ab"), Mode.from_word("ababab"))
    assert not ordered_resonates_inside(Mode.from_word("ab"), Mode.from_word("aba"))


def test_weave_schema_and_substitution():
    assert repeat_mode(Mode.from_word("ab"), 3) == Mode.from_word("ababab")
    assert substitute_mode(
        Mode.from_word("abba"),
        {"a": Mode.from_word("x"), "b": Mode.from_word("yz")},
    ) == Mode.from_word("xyzyzx")
    assert weave_by_length(Mode.from_word("ab"), Mode.from_word("xyz")) == Mode.from_word("ababab")


def test_one_tact_natural_shadow_operations():
    three = natural_mode(3)
    two = natural_mode(2)
    assert natural_shadow(three.stitch(two)) == 5
    assert natural_shadow(weave_by_length(three, two)) == 6
