from src.core.break_locus import (
    break_locus,
    locus_formula,
    tightness_witness,
    type_matrix,
    type_spectrum_sweep,
    verify_tightness,
)


def test_tightness_witness_rejects_invalid_primes():
    assert tightness_witness((4,)) == ("invalid-primes",)
    assert tightness_witness((2, 2)) == ("invalid-primes",)
    assert tightness_witness(()) == ("invalid-primes",)


def test_tightness_r1_is_principal():
    report = verify_tightness((2,))
    assert report.status == "witnessed"
    assert report.locus_size == 1
    assert report.length == 4


def test_tightness_r2_two_minimal_floors():
    report = verify_tightness((2, 3))
    assert report.status == "witnessed"
    assert report.locus_size == 2
    assert report.special_pattern_ok
    assert report.pairwise_incomparable
    assert report.length == 18
    assert report.word == "aaabbzzbbzaaazbbzz"
    word, alphabet = tightness_witness((2, 3))
    from src.core.break_locus import forced_pairs

    assert forced_pairs(word, alphabet, 2) == (("a", "b"), ("b", "z"))
    assert forced_pairs(word, alphabet, 3) == (("a", "b"), ("a", "z"))
    assert locus_formula(word, alphabet) == (
        (("a", "b"), ("a", "z")),
        (("a", "b"), ("b", "z")),
    )
    assert locus_formula(word, alphabet) == break_locus(word, alphabet).minimal_deltas


def test_tightness_r3_three_minimal_floors():
    report = verify_tightness((2, 3, 5))
    assert report.status == "witnessed"
    assert report.locus_size == 3
    assert report.special_pattern_ok
    assert report.pairwise_incomparable
    assert report.length == 120


def test_type_matrix_on_refutation_witness():
    from src.core.break_locus import refutation_witness

    word, alphabet = refutation_witness()
    matrix = dict(type_matrix(word, alphabet))
    assert matrix[("a", "b")] == ((2, True), (3, False))
    assert matrix[("a", "c")] == ((2, False), (3, True))
    assert matrix[("b", "c")] == ((2, False), (3, False))


def test_type_spectrum_structure_abc222():
    report = type_spectrum_sweep(("a", "b", "c"), (2, 2, 2), 2)
    assert report.status == "witnessed"
    assert report.words_scanned == 90
    assert len(report.realized_vectors) == 8
    assert report.realized_vectors == tuple(
        sorted((a, b, c) for a in (False, True) for b in (False, True) for c in (False, True))
    )


def test_type_spectrum_refuses_oversize():
    report = type_spectrum_sweep(("a", "b", "c"), (4, 4, 4), 2, word_cap=100)
    assert report.status == "refused"
