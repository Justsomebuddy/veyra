"""Necklace congruence probes: arithmetic from counting rotation orbits.

Boundary: the counting side is native — orbits are collected through
`native_number.cycle_echo` rotation orbits over concrete mode presentations,
and every divisibility fact is witnessed by an exact orbit partition, not by
`%` on opaque totals. The Möbius column is a declared school shadow
(docs/06 §3 license) used only as an external cross-check of the native
counts; it decides nothing. Witness statuses use `witnessed`/`blocked`,
never `proved` (CONTRIBUTING claim rules). General statements remain
EXECUTABLE_EVIDENCE for the exact bounded rows; see
`docs/179_necklace_congruence_n8.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

from .modes import Mode, enumerate_modes, is_ordered_primitive
from .native_number import CycleEcho, cycle_echo
from .primes import is_prime_int

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrbitRow:
    """One rotation orbit: display representative, exact size, constancy."""

    representative: str
    orbit_size: int
    constant: bool


@dataclass(frozen=True)
class OrbitDichotomyWitness:
    """Prime-length orbit dichotomy: every orbit has size 1 or the length."""

    length: int
    alphabet_size: int
    total_words: int
    constant_count: int
    nonconstant_count: int
    orbit_sizes: tuple[int, ...]
    dichotomy: bool
    counterexample: str
    status: str
    obstruction: str


@dataclass(frozen=True)
class FermatOrbitWitness:
    """Fermat count from orbits: nonconstant words split into full orbits."""

    prime: int
    alphabet_size: int
    nonconstant_count: int
    full_orbit_count: int
    partition_exact: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class GaussCongruenceWitness:
    """Gauss congruence: primitive words split into full orbits; Möbius shadow."""

    length: int
    alphabet_size: int
    primitive_count: int
    all_orbits_full: bool
    divisibility: bool
    mobius_shadow: int
    shadow_match: bool
    status: str
    obstruction: str


def _exact_length_modes(alphabet: tuple[str, ...], length: int) -> list[Mode]:
    logger.debug("_exact_length_modes entry alphabet=%r length=%d", alphabet, length)
    result = [item for item in enumerate_modes(alphabet, length, include_silent=False) if item.length == length]
    logger.debug("_exact_length_modes exit count=%d", len(result))
    return result


def _is_constant(mode: Mode) -> bool:
    logger.debug("_is_constant entry mode=%s", mode.word)
    result = mode.length > 0 and all(item == mode.tacts[0] for item in mode.tacts)
    logger.debug("_is_constant exit result=%s", result)
    return result


def rotation_orbit_rows(alphabet: Iterable[str], length: int) -> tuple[OrbitRow, ...]:
    """Group all words of exact length into native rotation orbits."""
    logger.debug("rotation_orbit_rows entry length=%d", length)
    symbols = tuple(alphabet)
    if length <= 0:
        logger.error("rotation_orbit_rows invalid length=%d", length)
        raise ValueError("length must be positive")
    orbits: dict[CycleEcho, Mode] = {}
    for mode in _exact_length_modes(symbols, length):
        echo = cycle_echo(mode)
        if echo not in orbits:
            orbits[echo] = mode
    rows = tuple(
        sorted(
            (OrbitRow(echo.words[0], echo.orbit_size, _is_constant(member)) for echo, member in orbits.items()),
            key=lambda row: row.representative,
        )
    )
    logger.debug("rotation_orbit_rows exit orbits=%d", len(rows))
    return rows


def orbit_dichotomy_witness(alphabet: Iterable[str], length: int) -> OrbitDichotomyWitness:
    """Witness that every orbit at a prime length has size 1 or the length."""
    logger.debug("orbit_dichotomy_witness entry length=%d", length)
    symbols = tuple(alphabet)
    rows = rotation_orbit_rows(symbols, length)
    total = len(symbols) ** length
    constant = sum(1 for row in rows if row.constant)
    nonconstant = total - constant
    sizes = tuple(sorted({row.orbit_size for row in rows}))
    offending = next((row.representative for row in rows if row.orbit_size not in (1, length)), "")
    dichotomy = offending == "" and all(row.orbit_size == (1 if row.constant else length) for row in rows)
    if not is_prime_int(length):
        result = OrbitDichotomyWitness(length, len(symbols), total, constant, nonconstant, sizes, dichotomy, offending, "blocked", "nonprime-length")
        logger.error("orbit_dichotomy_witness blocked result=%r", result)
        return result
    if not dichotomy:
        result = OrbitDichotomyWitness(length, len(symbols), total, constant, nonconstant, sizes, dichotomy, offending, "blocked", "dichotomy-failure")
        logger.error("orbit_dichotomy_witness blocked result=%r", result)
        return result
    result = OrbitDichotomyWitness(length, len(symbols), total, constant, nonconstant, sizes, True, "", "witnessed", "none")
    logger.debug("orbit_dichotomy_witness exit result=%r", result)
    return result


def fermat_orbit_witness(alphabet: Iterable[str], prime_length: int) -> FermatOrbitWitness:
    """Witness k^p - k as an exact partition into full orbits of size p."""
    logger.debug("fermat_orbit_witness entry prime_length=%d", prime_length)
    symbols = tuple(alphabet)
    dichotomy = orbit_dichotomy_witness(symbols, prime_length)
    if dichotomy.status != "witnessed":
        result = FermatOrbitWitness(prime_length, len(symbols), dichotomy.nonconstant_count, 0, False, "blocked", dichotomy.obstruction)
        logger.error("fermat_orbit_witness blocked result=%r", result)
        return result
    rows = rotation_orbit_rows(symbols, prime_length)
    full_orbits = [row for row in rows if not row.constant]
    partition_exact = (
        all(row.orbit_size == prime_length for row in full_orbits)
        and sum(row.orbit_size for row in full_orbits) == dichotomy.nonconstant_count
    )
    if not partition_exact:
        result = FermatOrbitWitness(prime_length, len(symbols), dichotomy.nonconstant_count, len(full_orbits), False, "blocked", "partition-mismatch")
        logger.error("fermat_orbit_witness blocked result=%r", result)
        return result
    result = FermatOrbitWitness(prime_length, len(symbols), dichotomy.nonconstant_count, len(full_orbits), True, "witnessed", "none")
    logger.debug("fermat_orbit_witness exit result=%r", result)
    return result


def mobius_shadow_value(value: int) -> int:
    """Return the Möbius function as a declared school shadow (docs/06 §3)."""
    logger.debug("mobius_shadow_value entry value=%d", value)
    if value < 1:
        logger.error("mobius_shadow_value invalid value=%d", value)
        raise ValueError("value must be positive")
    remaining, distinct = value, 0
    factor = 2
    while factor * factor <= remaining:
        if remaining % factor == 0:
            remaining //= factor
            distinct += 1
            if remaining % factor == 0:
                logger.debug("mobius_shadow_value exit result=0 square factor=%d", factor)
                return 0
        else:
            factor += 1
    if remaining > 1:
        distinct += 1
    result = -1 if distinct % 2 else 1
    logger.debug("mobius_shadow_value exit result=%d", result)
    return result


def _mobius_primitive_shadow(length: int, alphabet_size: int) -> int:
    logger.debug("_mobius_primitive_shadow entry length=%d k=%d", length, alphabet_size)
    result = sum(
        mobius_shadow_value(divisor) * alphabet_size ** (length // divisor)
        for divisor in range(1, length + 1)
        if length % divisor == 0
    )
    logger.debug("_mobius_primitive_shadow exit result=%d", result)
    return result


def gauss_congruence_witness(alphabet: Iterable[str], length: int) -> GaussCongruenceWitness:
    """Witness length | #primitive words via full orbits, with Möbius shadow."""
    logger.debug("gauss_congruence_witness entry length=%d", length)
    symbols = tuple(alphabet)
    if length <= 0:
        result = GaussCongruenceWitness(length, len(symbols), 0, False, False, 0, False, "blocked", "silent-length")
        logger.error("gauss_congruence_witness blocked result=%r", result)
        return result
    primitive = [mode for mode in _exact_length_modes(symbols, length) if is_ordered_primitive(mode)]
    echoes = [cycle_echo(mode) for mode in primitive]
    all_full = all(echo.orbit_size == length for echo in echoes)
    count = len(primitive)
    orbit_count = len(set(echoes))
    divisibility = all_full and count == orbit_count * length
    shadow = _mobius_primitive_shadow(length, len(symbols))
    match = shadow == count
    if not (all_full and divisibility and match):
        obstruction = "orbit-not-full" if not all_full else "divisibility-failure" if not divisibility else "shadow-mismatch"
        result = GaussCongruenceWitness(length, len(symbols), count, all_full, divisibility, shadow, match, "blocked", obstruction)
        logger.error("gauss_congruence_witness blocked result=%r", result)
        return result
    result = GaussCongruenceWitness(length, len(symbols), count, True, True, shadow, True, "witnessed", "none")
    logger.debug("gauss_congruence_witness exit result=%r", result)
    return result


def necklace_congruence_checklist() -> tuple[str, ...]:
    """Return the N8 lane acceptance checklist."""
    logger.debug("necklace_congruence_checklist entry")
    result = (
        "orbits are collected natively through cycle_echo, never through a canonical cut",
        "prime-length dichotomy is witnessed orbit-by-orbit with an explicit counterexample slot",
        "the Fermat count is an exact partition into full orbits, not a remainder check",
        "the Gauss divisibility is carried by full primitive orbits; the Möbius column is a labeled school shadow",
        "witness statuses are witnessed/blocked; nothing here is proved",
    )
    logger.debug("necklace_congruence_checklist exit count=%d", len(result))
    return result
