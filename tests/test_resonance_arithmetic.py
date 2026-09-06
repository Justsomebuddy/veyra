from math import gcd, lcm

import pytest

from src.core.native_runtime import Mode, breath, mode, nod, rez, tact
from src.core.resonance_arithmetic import (
    SHADOW_LICENSED,
    default_anchor,
    euclid_escape_witness,
    fermat_phase_witness,
    length,
    phase_congruent,
    phase_orbit_length,
    phase_power,
    phase_residual,
    resonance_arithmetic_checklist,
    resonance_prime_witness,
    resonates,
    shared_closure,
    shared_echo,
    unary,
)

ANCHOR = default_anchor()


def _u(value: int):
    return unary(ANCHOR, value)


def test_shared_echo_and_closure_match_host_gcd_lcm_on_small_range():
    for left in range(0, 13):
        for right in range(1, 13):
            assert length(shared_echo(_u(left), _u(right))) == gcd(left, right)
            if left:
                assert length(shared_closure(_u(left), _u(right))) == lcm(left, right)


def test_resonance_is_divisibility_and_silence_is_absorbing():
    for factor in range(1, 9):
        for carrier in range(0, 20):
            assert resonates(_u(factor), _u(carrier)) is (carrier % factor == 0)
    assert resonates(_u(0), _u(0))
    assert not resonates(_u(0), _u(3))
    assert resonates(_u(5), _u(0))


def test_phase_residual_and_congruence_are_the_docs02_definition():
    for modulus in range(1, 8):
        for left in range(0, 15):
            assert length(phase_residual(_u(modulus), _u(left))) == left % modulus
            for right in range(0, 15):
                assert phase_congruent(_u(modulus), _u(left), _u(right)) is (left % modulus == right % modulus)


def test_phase_power_and_orbits_match_host_modular_arithmetic():
    for modulus in (2, 3, 5, 7, 11):
        for unit in range(1, modulus):
            for exponent in range(0, 6):
                assert length(phase_power(_u(unit), _u(exponent), _u(modulus))) == pow(unit, exponent, modulus)
            orbit = phase_orbit_length(_u(unit), _u(modulus))
            assert orbit > 0 and pow(unit, orbit, modulus) == 1
            assert all(pow(unit, shorter, modulus) != 1 for shorter in range(1, orbit))


def test_resonance_primes_are_the_primes():
    witnessed = [value for value in range(0, 32) if resonance_prime_witness(ANCHOR, _u(value)).prime]
    assert witnessed == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    assert resonance_prime_witness(ANCHOR, _u(1)).obstruction == "length-too-short"
    composite = resonance_prime_witness(ANCHOR, _u(9))
    assert composite.obstruction == "composite-rhythm"
    assert composite.divisor_rows[-1] == (3, "exact")


@pytest.mark.parametrize("count", (2, 3, 4))
@pytest.mark.parametrize("outside_domain", ("foreign-recurrence", "anchor-mismatch"))
def test_resonance_prime_witness_rejects_nonintrinsic_or_foreign_anchor(count, outside_domain):
    if outside_domain == "anchor-mismatch":
        other_anchor = nod(rez("other-origin"), "other-origin")
        candidate = unary(other_anchor, count)
    else:
        candidate = mode(breath(*(tact(ANCHOR, ANCHOR, "foreign-tact") for _ in range(count))))
    assert isinstance(candidate, Mode)
    witness = resonance_prime_witness(ANCHOR, candidate)
    assert witness.status == "blocked"
    assert not witness.prime
    assert witness.obstruction == outside_domain
    assert witness.divisor_rows == ()


def test_resonance_prime_witness_accepts_equal_anchor_values():
    equal_anchor = nod(rez(ANCHOR.residue.name), ANCHOR.mark)
    witness = resonance_prime_witness(ANCHOR, unary(equal_anchor, 2))
    assert witness.status == "witnessed"
    assert witness.prime
    assert witness.divisor_rows == ()
    assert witness.obstruction == "none"


def test_fermat_phase_witness_prime_and_composite_periods():
    for period in (2, 3, 5, 7, 11, 13):
        row = fermat_phase_witness(ANCHOR, period)
        assert row.status == "witnessed"
        assert row.residue_lengths == tuple(1 for _ in row.unit_lengths)
        assert all((period - 1) % orbit == 0 for orbit in row.orbit_lengths)
        assert (period - 1) in row.orbit_lengths
    for period in (4, 6, 9):
        row = fermat_phase_witness(ANCHOR, period)
        assert row.status == "blocked"
        assert row.obstruction == "composite-period"
        assert not row.returns
    assert fermat_phase_witness(ANCHOR, 1).obstruction == "period-too-short"


def test_euclid_escape_witness_produces_new_resonance_primes():
    row = euclid_escape_witness(ANCHOR, (2, 3))
    assert (row.status, row.escape_length, row.residual_lengths, row.new_prime_length) == ("witnessed", 7, (1, 1), 7)
    row = euclid_escape_witness(ANCHOR, (2, 3, 5))
    assert (row.status, row.escape_length, row.new_prime_length) == ("witnessed", 31, 31)
    assert euclid_escape_witness(ANCHOR, (2, 4)).obstruction == "factor-not-resonance-prime"
    assert euclid_escape_witness(ANCHOR, ()).status == "blocked"


def test_shadow_license_and_checklist():
    assert SHADOW_LICENSED == ("unary", "length")
    assert len(resonance_arithmetic_checklist()) == 6
    with pytest.raises(ValueError):
        unary(ANCHOR, -1)
    with pytest.raises(ValueError):
        phase_residual(_u(0), _u(3))
