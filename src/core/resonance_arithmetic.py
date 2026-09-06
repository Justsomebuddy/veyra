"""Resonance arithmetic: native number theory over intrinsic recurrences.

This module makes the docs/02 vocabulary executable on the native runtime:
divisibility is resonance (`resonates`), a prime is an indecomposable rhythm
(`resonance_prime_witness`), congruence is the phase obstruction left after
maximal extraction of the modulus (`phase_residual`, `phase_congruent`), gcd is
the strongest shared echo (`shared_echo`) and lcm the smallest shared closure
(`shared_closure`). Every decision is a native structural operation on
`native_runtime.Mode` recurrences — `structural_divide` (prefix removal),
`stitch`, `weave` — and the only observer consulted is the length observer.
No host `%`, `//`, `pow`, `gcd` or `is_prime_int` appears on a decision path;
`tests/test_resonance_decision_paths.py` enforces this by AST for every
number-theory lane. Host integers enter only through the declared transport
`unary` (int → recurrence) and leave through `length` (recurrence → int), the
docs/06 §3 shadow license; both are listed in `SHADOW_LICENSED`.

Formal counterpart: `proofs/lean/VeyraResonanceArithmetic.lean`
(`THM_RA_001`–`014`), which proves the weave laws, the uniqueness of structural
division, the phase-congruence characterization and laws, Fermat and Euclid in
this vocabulary, and the gcd/lcm universal properties over the native
`Recurrence` type. Statuses are `witnessed`/`blocked`, never `proved`.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .intrinsic_arithmetic import one, stitch, successor, weave, zero
from .intrinsic_arithmetic_division import structural_divide
from .native_runtime import Mode, NativeObstruction, Nod, nod, rez

logger = logging.getLogger(__name__)

SHADOW_LICENSED = ("unary", "length")
DEFAULT_NATIVE_LIMIT = 31


@dataclass(frozen=True)
class ResonancePrimeWitness:
    """Native primality: every candidate divisor length leaves a residual."""

    length: int
    divisor_rows: tuple[tuple[int, str], ...]
    prime: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class FermatPhaseWitness:
    """Native Fermat phase return for one prime period."""

    period: int
    unit_lengths: tuple[int, ...]
    residue_lengths: tuple[int, ...]
    orbit_lengths: tuple[int, ...]
    returns: bool
    lagrange: bool
    cyclic: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class EscapeWitness:
    """Native Euclid escape: product-plus-one leaves the unit phase under every factor."""

    factor_lengths: tuple[int, ...]
    escape_length: int
    residual_lengths: tuple[int, ...]
    new_prime_length: int
    status: str
    obstruction: str


def default_anchor() -> Nod:
    """Return the anchor nod used by the canonical resonance rows."""
    logger.debug("resonance_arithmetic.default_anchor entry")
    result = nod(rez("resonance"), "ra")
    logger.debug("resonance_arithmetic.default_anchor exit")
    return result


def unary(anchor: Nod, count: int) -> Mode:
    """Transport a host integer into its unary recurrence (declared shadow license)."""
    logger.debug("resonance_arithmetic.unary entry count=%d", count)
    if count < 0:
        logger.error("resonance_arithmetic.unary negative count=%d", count)
        raise ValueError("unary-count-negative")
    value: Mode | NativeObstruction = zero(anchor)
    for _ in range(count):
        value = successor(value)
        if isinstance(value, NativeObstruction):
            logger.error("resonance_arithmetic.unary blocked %r", value)
            raise ValueError(value.reason)
    logger.debug("resonance_arithmetic.unary exit")
    return value


def length(mode: Mode) -> int:
    """Read a recurrence through the length observer (declared shadow license)."""
    logger.debug("resonance_arithmetic.length entry")
    result = len(mode.breath.tacts)
    logger.debug("resonance_arithmetic.length exit result=%d", result)
    return result


def is_silent(mode: Mode) -> bool:
    """Return whether a recurrence carries no tact."""
    logger.debug("resonance_arithmetic.is_silent entry")
    result = not mode.breath.tacts
    logger.debug("resonance_arithmetic.is_silent exit result=%s", result)
    return result


def _require(value: Mode | NativeObstruction, stage: str) -> Mode:
    logger.debug("resonance_arithmetic._require entry stage=%s", stage)
    if isinstance(value, NativeObstruction):
        logger.error("resonance_arithmetic._require blocked stage=%s reason=%s", stage, value.reason)
        raise ValueError(f"{stage}:{value.reason}")
    logger.debug("resonance_arithmetic._require exit stage=%s", stage)
    return value


def phase_residual(modulus: Mode, value: Mode) -> Mode:
    """Return the residual left after maximal structural extraction of `modulus`."""
    logger.debug("resonance_arithmetic.phase_residual entry")
    if is_silent(modulus):
        logger.error("resonance_arithmetic.phase_residual silent modulus")
        raise ValueError("phase-residual-silent-modulus")
    proof = structural_divide(value, modulus)
    if proof.status not in ("exact", "residual") or not proof.reconstructs:
        logger.error("resonance_arithmetic.phase_residual division blocked status=%s", proof.status)
        raise ValueError(f"phase-residual-division-{proof.status}")
    logger.debug("resonance_arithmetic.phase_residual exit")
    return proof.residual


def phase_congruent(modulus: Mode, left: Mode, right: Mode) -> bool:
    """Return whether two recurrences leave the same phase obstruction modulo `modulus`."""
    logger.debug("resonance_arithmetic.phase_congruent entry")
    result = phase_residual(modulus, left).breath == phase_residual(modulus, right).breath
    logger.debug("resonance_arithmetic.phase_congruent exit result=%s", result)
    return result


def resonates(factor: Mode, carrier: Mode) -> bool:
    """Return whether `factor` resonates inside `carrier` (weaves it exactly)."""
    logger.debug("resonance_arithmetic.resonates entry")
    if is_silent(factor):
        result = is_silent(carrier)
        logger.debug("resonance_arithmetic.resonates exit silent factor result=%s", result)
        return result
    proof = structural_divide(carrier, factor)
    result = proof.status == "exact" and proof.reconstructs
    logger.debug("resonance_arithmetic.resonates exit result=%s", result)
    return result


def shared_echo(left: Mode, right: Mode) -> Mode:
    """Return the strongest shared echo (gcd) by native structural Euclid."""
    logger.debug("resonance_arithmetic.shared_echo entry")
    first, second = left, right
    while not is_silent(second):
        first, second = second, phase_residual(second, first)
    logger.debug("resonance_arithmetic.shared_echo exit")
    return first


def shared_closure(left: Mode, right: Mode) -> Mode:
    """Return the smallest shared closure (lcm) as `left` woven by `right / echo`."""
    logger.debug("resonance_arithmetic.shared_closure entry")
    if is_silent(left):
        logger.debug("resonance_arithmetic.shared_closure exit silent left")
        return left
    if is_silent(right):
        logger.debug("resonance_arithmetic.shared_closure exit silent right")
        return right
    echo = shared_echo(left, right)
    proof = structural_divide(right, echo)
    if proof.status != "exact":
        logger.error("resonance_arithmetic.shared_closure echo does not divide")
        raise ValueError("shared-closure-echo-inexact")
    result = _require(weave(left, proof.quotient), "shared-closure-weave")
    logger.debug("resonance_arithmetic.shared_closure exit")
    return result


def resonance_prime_witness(anchor: Nod, candidate: Mode) -> ResonancePrimeWitness:
    """Witness primality only for an intrinsic recurrence on the supplied anchor."""
    logger.debug("resonance_arithmetic.resonance_prime_witness entry")
    size = length(candidate)
    if size < 2:
        result = ResonancePrimeWitness(size, (), False, "blocked", "length-too-short")
        logger.error("resonance_arithmetic.resonance_prime_witness blocked %r", result)
        return result
    admitted = stitch(zero(anchor), candidate)
    if isinstance(admitted, NativeObstruction):
        result = ResonancePrimeWitness(size, (), False, "blocked", admitted.reason)
        logger.error("resonance_arithmetic.resonance_prime_witness blocked reason=%s", admitted.reason)
        return result
    rows: list[tuple[int, str]] = []
    divisor = unary(anchor, 2)
    while length(divisor) < size:
        proof = structural_divide(candidate, divisor)
        rows.append((length(divisor), proof.status))
        if proof.status == "exact":
            result = ResonancePrimeWitness(size, tuple(rows), False, "blocked", "composite-rhythm")
            logger.error("resonance_arithmetic.resonance_prime_witness composite divisor=%d", length(divisor))
            return result
        if proof.status != "residual":
            result = ResonancePrimeWitness(size, tuple(rows), False, "blocked", proof.status)
            logger.error("resonance_arithmetic.resonance_prime_witness blocked %r", result)
            return result
        divisor = _require(successor(divisor), "prime-witness-successor")
    result = ResonancePrimeWitness(size, tuple(rows), True, "witnessed", "none")
    logger.debug("resonance_arithmetic.resonance_prime_witness exit prime rows=%d", len(rows))
    return result


def phase_power(base: Mode, exponent: Mode, modulus: Mode) -> Mode:
    """Weave `base` with itself once per tact of `exponent`, reducing the phase after each weave."""
    logger.debug("resonance_arithmetic.phase_power entry")
    anchor = modulus.breath.anchor if modulus.breath.anchor is not None else modulus.breath.tacts[0].start
    value = phase_residual(modulus, one(anchor))
    for _ in exponent.breath.tacts:
        value = phase_residual(modulus, _require(weave(value, base), "phase-power-weave"))
    logger.debug("resonance_arithmetic.phase_power exit")
    return value


def phase_orbit_length(unit: Mode, modulus: Mode) -> int:
    """Return the multiplicative phase-orbit length of `unit` modulo `modulus` (first return to the unit phase)."""
    logger.debug("resonance_arithmetic.phase_orbit_length entry")
    anchor = modulus.breath.anchor if modulus.breath.anchor is not None else modulus.breath.tacts[0].start
    unit_phase = phase_residual(modulus, one(anchor))
    value = phase_residual(modulus, unit)
    steps = 1
    bound = length(modulus)
    while value.breath != unit_phase.breath:
        if steps > bound:
            logger.error("resonance_arithmetic.phase_orbit_length no return within modulus")
            return 0
        value = phase_residual(modulus, _require(weave(value, unit), "phase-orbit-weave"))
        steps += 1
    logger.debug("resonance_arithmetic.phase_orbit_length exit steps=%d", steps)
    return steps


def fermat_phase_witness(anchor: Nod, period: int) -> FermatPhaseWitness:
    """Witness Fermat's phase return natively for one period built from `period` pulses."""
    logger.debug("resonance_arithmetic.fermat_phase_witness entry period=%d", period)
    if period < 2:
        result = FermatPhaseWitness(period, (), (), (), False, False, False, "blocked", "period-too-short")
        logger.error("resonance_arithmetic.fermat_phase_witness blocked %r", result)
        return result
    modulus = unary(anchor, period)
    exponent = unary(anchor, period - 1)
    unit_phase = phase_residual(modulus, one(anchor))
    units: list[int] = []
    residues: list[int] = []
    orbits: list[int] = []
    unit = one(anchor)
    while length(unit) < period:
        units.append(length(unit))
        residues.append(length(phase_power(unit, exponent, modulus)))
        orbits.append(phase_orbit_length(unit, modulus))
        unit = _require(successor(unit), "fermat-unit-successor")
    returns = all(length(phase_residual(modulus, unary(anchor, residue))) == length(unit_phase) and residue == length(unit_phase) for residue in residues)
    lagrange = all(orbit > 0 and resonates(unary(anchor, orbit), exponent) for orbit in orbits)
    cyclic = any(orbit == length(exponent) for orbit in orbits)
    primality = resonance_prime_witness(anchor, modulus)
    if not primality.prime:
        obstruction = "composite-period" if primality.obstruction == "composite-rhythm" else primality.obstruction
        result = FermatPhaseWitness(period, tuple(units), tuple(residues), tuple(orbits), returns, lagrange, cyclic, "blocked", obstruction)
        logger.error("resonance_arithmetic.fermat_phase_witness blocked %r", result.obstruction)
        return result
    if not (returns and lagrange and cyclic):
        obstruction = "phase-return-failure" if not returns else "lagrange-failure" if not lagrange else "no-generator"
        result = FermatPhaseWitness(period, tuple(units), tuple(residues), tuple(orbits), returns, lagrange, cyclic, "blocked", obstruction)
        logger.error("resonance_arithmetic.fermat_phase_witness blocked %r", result.obstruction)
        return result
    result = FermatPhaseWitness(period, tuple(units), tuple(residues), tuple(orbits), True, True, True, "witnessed", "none")
    logger.debug("resonance_arithmetic.fermat_phase_witness exit witnessed period=%d", period)
    return result


def euclid_escape_witness(anchor: Nod, factor_lengths: tuple[int, ...]) -> EscapeWitness:
    """Witness natively that the escape of listed rhythms carries a new resonance prime."""
    logger.debug("resonance_arithmetic.euclid_escape_witness entry factors=%r", factor_lengths)
    factors = tuple(unary(anchor, item) for item in factor_lengths)
    if not factors or any(length(item) < 2 for item in factors):
        result = EscapeWitness(factor_lengths, 0, (), 0, "blocked", "requires-nonempty-factors-of-two-or-more-pulses")
        logger.error("resonance_arithmetic.euclid_escape_witness blocked %r", result.obstruction)
        return result
    for item in factors:
        if not resonance_prime_witness(anchor, item).prime:
            result = EscapeWitness(factor_lengths, 0, (), 0, "blocked", "factor-not-resonance-prime")
            logger.error("resonance_arithmetic.euclid_escape_witness blocked %r", result.obstruction)
            return result
    woven = one(anchor)
    for item in factors:
        woven = _require(weave(woven, item), "escape-weave")
    escape = _require(successor(woven), "escape-successor")
    residuals = tuple(length(phase_residual(item, escape)) for item in factors)
    if any(residue != 1 for residue in residuals):
        result = EscapeWitness(factor_lengths, length(escape), residuals, 0, "blocked", "escape-residual-not-unit")
        logger.error("resonance_arithmetic.euclid_escape_witness blocked %r", result.obstruction)
        return result
    divisor = unary(anchor, 2)
    new_prime = escape
    # Search divisors only while divisor woven with itself does not exceed the escape:
    # a composite escape has a resonator no longer than that bound.
    while length(_require(weave(divisor, divisor), "escape-square-weave")) <= length(escape):
        if resonates(divisor, escape):
            new_prime = divisor
            break
        divisor = _require(successor(divisor), "escape-divisor-successor")
    if not resonance_prime_witness(anchor, new_prime).prime or any(new_prime.breath == item.breath for item in factors):
        result = EscapeWitness(factor_lengths, length(escape), residuals, length(new_prime), "blocked", "escape-factor-not-new-prime")
        logger.error("resonance_arithmetic.euclid_escape_witness blocked %r", result.obstruction)
        return result
    result = EscapeWitness(factor_lengths, length(escape), residuals, length(new_prime), "witnessed", "none")
    logger.debug("resonance_arithmetic.euclid_escape_witness exit witnessed escape=%d new_prime=%d", length(escape), length(new_prime))
    return result


def resonance_arithmetic_checklist() -> tuple[str, ...]:
    """Return the acceptance checklist of the resonance-arithmetic lane."""
    logger.debug("resonance_arithmetic_checklist entry")
    result = (
        "divisibility is resonance: structural_divide status exact, no host remainder",
        "congruence is the phase obstruction after maximal extraction of the modulus",
        "primes are indecomposable rhythms witnessed by native trial division",
        "gcd is the strongest shared echo and lcm the smallest shared closure, by structural Euclid",
        "Fermat and Euclid rows are native phase computations; THM_RA_010/012 are the formal counterparts",
        "host integers only enter through unary and leave through length; statuses never say proved",
    )
    logger.debug("resonance_arithmetic_checklist exit count=%d", len(result))
    return result
