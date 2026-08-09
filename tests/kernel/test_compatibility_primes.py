from src.core.compatibility import (
    binary_compatibility_failures,
    unary_compatibility_failures,
    unary_respects,
)
from src.core.modes import Mode, enumerate_modes, substitute_mode
from src.core.primes import (
    cyclic_root,
    is_cyclic_primitive,
    is_one_tact_numeric_prime,
    is_ordered_resonance_prime,
    is_prime_int,
    prime_profile,
)


def test_unary_compatibility_detects_bad_length_substitution():
    modes = [Mode.from_word("a"), Mode.from_word("b")]
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    schema = lambda mode: substitute_mode(mode, mapping)
    failures = unary_compatibility_failures(modes, schema, "length", "length", "substitute", limit=1)
    assert failures
    assert not unary_respects(modes, schema, "length", "length", "substitute")


def test_unary_compatibility_accepts_uniform_length_substitution():
    modes = enumerate_modes(("a", "b"), 2, include_silent=False)
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("y")}
    schema = lambda mode: substitute_mode(mode, mapping)
    assert unary_respects(modes, schema, "length", "length", "uniform_substitute")


def test_binary_stitch_compatible_with_ordered_identity():
    modes = enumerate_modes(("a", "b"), 2, include_silent=False)
    failures = binary_compatibility_failures(modes, lambda left, right: left.stitch(right), "ordered", "ordered", "ordered", limit=1)
    assert not failures


def test_numeric_prime_shadow():
    assert is_prime_int(2)
    assert is_prime_int(13)
    assert not is_prime_int(1)
    assert not is_prime_int(12)
    assert is_one_tact_numeric_prime(Mode.from_word("aaa"), tact="a")
    assert is_one_tact_numeric_prime(Mode.from_word("aa"), tact="a")
    assert not is_one_tact_numeric_prime(Mode.from_word("aaaa"), tact="a")
    assert not is_one_tact_numeric_prime(Mode.from_word("ab"), tact="a")


def test_cyclic_and_resonance_prime_variants():
    root, exponent = cyclic_root(Mode.from_word("baba"))
    assert root == Mode.from_word("ab")
    assert exponent == 2
    assert is_cyclic_primitive(Mode.from_word("aba"))
    assert not is_cyclic_primitive(Mode.from_word("abab"))
    assert is_ordered_resonance_prime(Mode.from_word("ab"))
    assert not is_ordered_resonance_prime(Mode.from_word("abab"))


def test_prime_profile_records_divergence():
    profile = prime_profile(Mode.from_word("ab"), tact="a")
    assert not profile.numeric_prime
    assert profile.ordered_primitive
    assert profile.cyclic_primitive
    assert profile.ordered_resonance_prime
