from src.core.break_locus import (
    achieved_floor_check,
    break_locus,
    first_slice,
    forced_pairs,
    forcing_report,
    formula_agreement_sweep,
    locus_formula,
    pair_projection,
    refutation_witness,
)

AB = ("a", "b")
ABC = ("a", "b", "c")


def test_first_slice_basics():
    assert first_slice(tuple("aabbcc"), ABC, 2) == tuple("abc")
    assert first_slice(tuple("aaabbb"), AB, 3) == tuple("ab")
    assert first_slice(tuple("abab"), AB, 2) == tuple("ab")


def test_achieved_floor_on_known_cells():
    for word, alphabet, exponent in (
        (tuple("aabb"), AB, 2),
        (tuple("aabbcc"), ABC, 2),
        (tuple("aaabbb"), AB, 3),
        (tuple("aabbab" * 2), AB, 2),
        (tuple("aabbab" * 2), AB, 3),
    ):
        row = achieved_floor_check(word, alphabet, exponent)
        assert row.status == "witnessed", (word, exponent, row.obstruction)
        assert row.attained
    blocked = achieved_floor_check(tuple("aab"), AB, 2)
    assert blocked.status == "blocked"
    assert blocked.obstruction == "invalid-exponent"


def test_refutation_witness_is_nonprincipal():
    word, alphabet = refutation_witness()
    assert "".join(word) == "aaccabbbaccaaccbbb"
    assert tuple(word.count(letter) for letter in alphabet) == (6, 6, 6)
    assert pair_projection(word, "a", "b") == tuple("aaabbbaaabbb")
    assert pair_projection(word, "a", "c") == tuple("aaccaaccaacc")
    assert forced_pairs(word, alphabet, 2) == (("a", "c"), ("b", "c"))
    assert forced_pairs(word, alphabet, 3) == (("a", "b"), ("b", "c"))
    locus = break_locus(word, alphabet)
    assert locus.status == "witnessed"
    assert not locus.principal
    assert locus.minimal_deltas == (
        (("a", "b"), ("b", "c")),
        (("a", "c"), ("b", "c")),
    )
    assert locus_formula(word, alphabet) == locus.minimal_deltas
    report = forcing_report(word, alphabet)
    assert report.lemma_a_respected
    for exponent in (2, 3):
        assert achieved_floor_check(word, alphabet, exponent).attained


def test_formula_agreement_small_shapes():
    for alphabet, counts, checked in (
        (AB, (3, 3), 20),
        (AB, (4, 2), 15),
        (ABC, (2, 2, 2), 90),
    ):
        report = formula_agreement_sweep(alphabet, counts)
        assert report.status == "witnessed"
        assert report.words_checked == checked
        assert report.formula_mismatches == ()
        assert report.unachieved_floors == ()


def test_formula_matches_on_two_prime_samples():
    from src.core.break_locus import two_prime_probe

    probe = two_prime_probe(ABC, (6, 6, 6), samples=60)
    assert probe.status == "witnessed"
    word, alphabet = refutation_witness()
    assert locus_formula(word, alphabet) == break_locus(word, alphabet).minimal_deltas
