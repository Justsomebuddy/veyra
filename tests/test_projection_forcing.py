from src.core.break_locus import (
    forced_law_sweep,
    forced_pairs,
    forcing_report,
    is_k_power,
    prime_valid_exponents,
    two_prime_probe,
)

AB = ("a", "b")
ABC = ("a", "b", "c")


def test_is_k_power_basics():
    assert is_k_power(tuple("abab"), 2)
    assert not is_k_power(tuple("aabb"), 2)
    assert is_k_power(tuple("bcbcbcbcbcbc"), 2)
    assert is_k_power(tuple("bcbcbcbcbcbc"), 3)
    assert is_k_power(tuple("aaccaaccaacc"), 3)
    assert not is_k_power(tuple("aaccaaccaacc"), 2)
    assert not is_k_power(tuple("abc"), 2)


def test_forced_pairs_known_cells_match_loci():
    assert forced_pairs(tuple("aabb"), AB, 2) == (("a", "b"),)
    assert forced_pairs(tuple("abab"), AB, 2) == ()
    assert forced_pairs(tuple("aabbcc"), ABC, 2) == (("a", "b"), ("a", "c"), ("b", "c"))


def test_prime_valid_exponents():
    assert prime_valid_exponents(tuple("aabb"), AB) == (2,)
    assert prime_valid_exponents(tuple("aaabbb"), AB) == (3,)
    assert prime_valid_exponents(tuple("aaaabbbb"), AB) == (2,)
    assert prime_valid_exponents(tuple("aab"), AB) == ()
    assert prime_valid_exponents(tuple("a" * 6 + "b" * 6), AB) == (2, 3)


def test_forcing_report_single_prime_cells():
    report = forcing_report(tuple("aabbcc"), ABC)
    assert report.status == "witnessed"
    assert report.lemma_a_respected
    assert report.single_prime
    assert report.forced_locus_law is True

    literal = forcing_report(tuple("abab"), AB)
    assert literal.status == "witnessed"
    assert literal.forced_locus_law is None


def test_two_prime_forcing_floors_are_incomparable_in_principle():
    word = tuple("aabbab" * 2) + tuple()  # ab-projection square, 12 letters a6b6
    report = forcing_report(word, AB)
    assert report.prime_exponents == (2, 3)
    floors = dict(report.forced_by_prime)
    assert floors[2] == ()
    assert floors[3] == (("a", "b"),)
    assert report.lemma_a_respected


def test_checklist_untouched_and_law_sweep_small_shape():
    sweep = forced_law_sweep(AB, (3, 3))
    assert sweep.status == "witnessed"
    assert sweep.lemma_a_violations == ()
    assert sweep.law_mismatches == ()
    assert sweep.words_checked == 20


def test_forced_locus_law_pinned_on_all_scanned_shapes():
    """Pinned AFTER observation: B(w) == {F_q} on every single-prime word."""
    expected = (
        (AB, (3, 3), 20), (AB, (4, 2), 15), (AB, (4, 4), 70),
        (ABC, (2, 2, 2), 90), (ABC, (2, 2, 4), 420),
        (ABC, (4, 4, 2), 3150), (("a", "b", "c", "d"), (2, 2, 2, 2), 2520),
    )
    for alphabet, counts, checked in expected:
        sweep = forced_law_sweep(alphabet, counts)
        assert sweep.status == "witnessed"
        assert sweep.words_checked == checked
        assert sweep.lemma_a_violations == ()
        assert sweep.law_mismatches == ()


def test_two_prime_probe_pinned_1200():
    """Pinned AFTER observation: the conjecture survives first two-prime contact."""
    probe = two_prime_probe(ABC, (6, 6, 6), samples=1200)
    assert probe.status == "witnessed"
    assert probe.samples == 1200
    assert probe.literal_powers == 0
    assert probe.principal == 1200
    assert probe.nonprincipal_words == ()
    assert probe.max_locus_size == 1
    assert probe.forced_floor_respected


def test_two_prime_probe_is_deterministic():
    first = two_prime_probe(ABC, (6, 6, 6), samples=40)
    second = two_prime_probe(ABC, (6, 6, 6), samples=40)
    assert first == second
    assert first.status == "witnessed"
    assert first.samples == 40
    assert first.forced_floor_respected
