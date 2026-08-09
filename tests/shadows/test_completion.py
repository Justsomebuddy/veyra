from src.core.completion import interval_refines, interval_within, square_refinement, tail_limit_certificate
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_square_refinement_for_sqrt_two_is_nested():
    early = square_refinement(ratio_from_ints(2), 4)
    later = square_refinement(ratio_from_ints(2), 8)
    assert interval_refines(early, later)
    low = ratio_shadow(later.lower)
    high = ratio_shadow(later.upper)
    assert low * low <= 2 < high * high
    assert later.width < early.width


def test_square_refinement_exact_root_becomes_tight():
    interval = square_refinement(ratio_from_ints(4), 10)
    assert ratio_shadow(interval.lower) <= 2 <= ratio_shadow(interval.upper)
    assert interval_within(interval, ratio_from_ints(1, 100))


def test_tail_limit_certificate_stable_and_jump():
    samples = tuple(ratio_from_ints(1, n) for n in range(5, 11))
    stable = tail_limit_certificate(samples, ratio_from_ints(0), ratio_from_ints(1, 5), 4)
    assert stable.status == "stable"
    jump = tail_limit_certificate(samples, ratio_from_ints(0), ratio_from_ints(1, 20), 4)
    assert jump.status == "none"
    assert jump.obstruction == "tail-jump"
