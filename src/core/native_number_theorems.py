"""Native number-theorem pressure beyond finite tables.

Decision paths are native (docs/189): the N2 Fermat rows compute phase returns,
multiplicative orbits and primality through `resonance_arithmetic`
(`phase_power`, `phase_orbit_length`, `resonance_prime_witness`), i.e. through
`structural_divide`/`stitch`/`weave` on intrinsic recurrences, up to
`NATIVE_PERIOD_LIMIT`. Host integer arithmetic appears only in the functions
listed in `SHADOW_LICENSED` (docs/06 §3): the Euclid product-plus-one shadow
row and the `pow`-based residue shadow kept as a cross-check and as the
fallback for periods above the native limit (their rows say so).
"""
from __future__ import annotations
from dataclasses import dataclass
from math import prod
import logging
from .formal_bridge import check_lean_echo_export, lean_echo_export_path
from .native_runtime import Breath, Mode, NativeObstruction, breath, mode, nod, observe_native, rez, tact
from .resonance_arithmetic import (
    default_anchor, phase_orbit_length, phase_power, phase_residual, resonance_prime_witness, unary,
)

SHADOW_LICENSED = ("euclid_escape_row", "shadow_residues", "shadow_prime")
NATIVE_PERIOD_LIMIT = 31

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class EuclidEscapeRow:
    """One Euclid-style escape row over a finite prime observer list."""
    theorem_id: str
    primes: tuple[int, ...]
    witness: int
    remainders: tuple[int, ...]
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready theorem row."""
        logger.debug("EuclidEscapeRow.as_dict entry theorem=%s", self.theorem_id)
        result = {
            "theorem_id": self.theorem_id,
            "primes": self.primes,
            "witness": self.witness,
            "remainders": self.remainders,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("EuclidEscapeRow.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class NativeEuclidModeRow:
    """Euclid escape row whose source periods are observed from native Modes."""
    theorem_id: str
    periods: tuple[int, ...]
    mode_lengths: tuple[int, ...]
    witness: int
    remainders: tuple[int, ...]
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready native derivation row."""
        logger.debug("NativeEuclidModeRow.as_dict entry theorem=%s", self.theorem_id)
        result = {
            "theorem_id": self.theorem_id,
            "periods": self.periods,
            "mode_lengths": self.mode_lengths,
            "witness": self.witness,
            "remainders": self.remainders,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("NativeEuclidModeRow.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class NativeFermatPhaseRow:
    """Finite prime-period Fermat row derived from native Mode/Breath lengths."""
    theorem_id: str
    period: int
    mode_length: int
    unit_lengths: tuple[int, ...]
    residues: tuple[int, ...]
    orbit_lengths: tuple[int, ...]
    coverage: tuple[int, ...]
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready Fermat phase row."""
        logger.debug("NativeFermatPhaseRow.as_dict entry theorem=%s period=%d", self.theorem_id, self.period)
        result = {
            "theorem_id": self.theorem_id,
            "period": self.period,
            "mode_length": self.mode_length,
            "unit_lengths": self.unit_lengths,
            "residues": self.residues,
            "orbit_lengths": self.orbit_lengths,
            "coverage": self.coverage,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("NativeFermatPhaseRow.as_dict exit result=%r", result)
        return result

def euclid_escape_row(primes: tuple[int, ...]) -> EuclidEscapeRow:
    """Build an escape witness `prod(primes)+1` for a finite prime observer list."""
    logger.debug("euclid_escape_row entry primes=%r", primes)
    clean = tuple(int(p) for p in primes)
    if not clean or any(p <= 1 for p in clean):
        result = EuclidEscapeRow("THM-F002", clean, 0, (), "blocked", "requires nonempty finite list of integer-shadow primes")
        logger.debug("euclid_escape_row exit blocked result=%r", result)
        return result
    witness = prod(clean) + 1
    remainders = tuple(witness % p for p in clean)
    status = "certified-shadow" if all(r == 1 % p for r, p in zip(remainders, clean, strict=True)) else "blocked"
    boundary = "general product-plus-one construction over supplied list; still an integer-shadow observer, not full native prime infinitude"
    result = EuclidEscapeRow("THM-F002", clean, witness, remainders, status, boundary)
    logger.debug("euclid_escape_row exit result=%r", result)
    return result

def native_euclid_rows() -> tuple[EuclidEscapeRow, ...]:
    """Return canonical Euclid escape checks at increasing finite observer sizes."""
    logger.debug("native_euclid_rows entry")
    result = (euclid_escape_row((2, 3)), euclid_escape_row((2, 3, 5)), euclid_escape_row((3, 5, 7, 11)))
    logger.debug("native_euclid_rows exit count=%d", len(result))
    return result

def _period_mode(period: int) -> Mode | NativeObstruction:
    logger.debug("_period_mode entry period=%d", period)
    if period <= 1:
        result = NativeObstruction("mode-period", "period-too-small", (str(period),))
        logger.debug("_period_mode exit obstruction=%r", result)
        return result
    nodes = tuple(nod(rez(f"p{period}:{idx}"), str(idx)) for idx in range(period))
    contacts = tuple(tact(nodes[idx], nodes[idx + 1] if idx + 1 < period else nodes[0], "step") for idx in range(period))
    run = breath(*contacts)
    result = mode(run) if isinstance(run, Breath) else run
    logger.debug("_period_mode exit result=%r", result)
    return result

def _unit_breath(length: int) -> Breath | NativeObstruction:
    logger.debug("_unit_breath entry length=%d", length)
    if length <= 0:
        result = NativeObstruction("unit-breath", "nonpositive-length", (str(length),))
        logger.debug("_unit_breath exit obstruction=%r", result)
        return result
    nodes = tuple(nod(rez(f"u{length}:{idx}"), str(idx)) for idx in range(length + 1))
    contacts = tuple(tact(nodes[idx], nodes[idx + 1], "unit") for idx in range(length))
    result = breath(*contacts)
    logger.debug("_unit_breath exit result=%r", result)
    return result

def shadow_residues(units: tuple[int, ...], modulus: int) -> tuple[int, ...]:
    """Host pow-mod residues (declared shadow license): cross-check and above-limit fallback."""
    logger.debug("shadow_residues entry modulus=%d", modulus)
    result = tuple(pow(unit, modulus - 1, modulus) for unit in units)
    logger.debug("shadow_residues exit count=%d", len(result))
    return result

def shadow_prime(value: int) -> bool:
    """Host primality (declared shadow license): above-limit fallback only."""
    logger.debug("shadow_prime entry value=%d", value)
    from .primes import is_prime_int
    result = is_prime_int(value)
    logger.debug("shadow_prime exit result=%s", result)
    return result

def native_euclid_mode_row(periods: tuple[int, ...]) -> NativeEuclidModeRow:
    """Derive product-plus-one inputs from native Mode length observers."""
    logger.debug("native_euclid_mode_row entry periods=%r", periods)
    clean = tuple(int(period) for period in periods)
    modes = tuple(_period_mode(period) for period in clean)
    if not clean or any(not isinstance(item, Mode) for item in modes):
        result = NativeEuclidModeRow("THM-F002", clean, (), 0, (), "blocked", "requires nonempty periods that build closed native Modes")
        logger.debug("native_euclid_mode_row exit blocked result=%r", result)
        return result
    lengths = tuple(int(observe_native(item, "length")) for item in modes if isinstance(item, Mode))
    shadow = euclid_escape_row(lengths)
    status = "derived" if lengths == clean and shadow.status == "certified-shadow" else "blocked"
    boundary = "finite native Mode-length derivation; still not infinite resonance-prime theorem"
    result = NativeEuclidModeRow("THM-F002", clean, lengths, shadow.witness, shadow.remainders, status, boundary)
    logger.debug("native_euclid_mode_row exit result=%r", result)
    return result

def native_euclid_mode_rows() -> tuple[NativeEuclidModeRow, ...]:
    """Return canonical native Mode-length derivation rows."""
    logger.debug("native_euclid_mode_rows entry")
    result = (native_euclid_mode_row((2, 3)), native_euclid_mode_row((2, 3, 5)), native_euclid_mode_row((3, 5, 7, 11)))
    logger.debug("native_euclid_mode_rows exit count=%d", len(result))
    return result

def native_fermat_phase_row(period: int) -> NativeFermatPhaseRow:
    """Derive a finite Fermat phase row from a native period Mode and unit Breaths.

    Native boundary: the period and unit integers are transported into native
    Mode/Breath objects and read back through the length observer; the phase
    returns are then computed natively — `phase_power` weaves the unit with
    itself once per tact of the exponent and extracts the modulus structurally
    after every weave — and primality is the native `resonance_prime_witness`.
    ``derived`` therefore means "witnessed by native structural division on
    natively observed lengths". Pressure for prime periods is threefold and none
    of it is vacuous: every unit returns to phase 1; every multiplicative orbit
    length resonates inside ``p-1`` (a Lagrange instance); some orbit has length
    exactly ``p-1`` (a cyclicity instance). Composite periods are not
    pre-filtered: their rows are computed and blocked on the first unit whose
    phase return fails. Periods above ``NATIVE_PERIOD_LIMIT`` fall back to the
    declared host shadow and say so in their boundary text.
    """
    logger.debug("native_fermat_phase_row entry period=%d", period)
    clean = int(period)
    period_mode = _period_mode(clean)
    if not isinstance(period_mode, Mode):
        result = NativeFermatPhaseRow("THM-F003", clean, 0, (), (), (), (), "blocked", "requires a native closed Mode with period at least 2")
        logger.debug("native_fermat_phase_row exit blocked result=%r", result)
        return result
    mode_length = int(observe_native(period_mode, "length"))
    unit_breaths = tuple(_unit_breath(unit) for unit in range(1, mode_length))
    if any(not isinstance(item, Breath) for item in unit_breaths):
        result = NativeFermatPhaseRow("THM-F003", clean, mode_length, (), (), (), (), "blocked", "requires positive native unit Breaths")
        logger.debug("native_fermat_phase_row exit unit-blocked result=%r", result)
        return result
    units = tuple(int(observe_native(item, "length")) for item in unit_breaths if isinstance(item, Breath))
    native = mode_length <= NATIVE_PERIOD_LIMIT
    if native:
        anchor = default_anchor()
        modulus = unary(anchor, mode_length)
        exponent = unary(anchor, mode_length - 1)
        unit_modes = tuple(unary(anchor, unit) for unit in units)
        residues = tuple(len(phase_power(item, exponent, modulus).breath.tacts) for item in unit_modes)
        orbit_lengths = tuple(phase_orbit_length(item, modulus) for item in unit_modes)
        unit_phase_length = len(phase_residual(modulus, unary(anchor, 1)).breath.tacts)
        prime = resonance_prime_witness(anchor, modulus).prime
        lagrange = all(orbit > 0 and phase_residual(unary(anchor, orbit), exponent).breath.tacts == () for orbit in orbit_lengths)
        route = "native structural division"
    else:
        residues = shadow_residues(units, mode_length)
        orbit_lengths = tuple(_shadow_orbit_length(unit, mode_length) for unit in units)
        unit_phase_length = 1
        prime = shadow_prime(mode_length)
        lagrange = _shadow_lagrange(orbit_lengths, mode_length - 1)
        route = "host shadow (period above NATIVE_PERIOD_LIMIT)"
    coverage = tuple(sorted(set(units))) if native else units
    failing = next(((unit, residue) for unit, residue in zip(units, residues, strict=True) if residue != unit_phase_length), None)
    if failing is not None:
        boundary = f"composite or invalid period ({route}): Fermat phase return fails at unit {failing[0]} (residue {failing[1]}); native primality witness={prime}"
        result = NativeFermatPhaseRow("THM-F003", clean, mode_length, units, residues, orbit_lengths, coverage, "blocked", boundary)
        logger.debug("native_fermat_phase_row exit fermat-blocked result=%r", result)
        return result
    cyclic = (mode_length - 1) in orbit_lengths
    status = "derived" if prime and lagrange and cyclic else "blocked"
    boundary = f"finite prime-period Fermat row ({route}; orbit lengths resonate inside p-1; a generator exists); not unbounded native Fermat or reciprocity — the all-prime statement is THM_RA_010"
    result = NativeFermatPhaseRow("THM-F003", clean, mode_length, units, residues, orbit_lengths, coverage, status, boundary)
    logger.debug("native_fermat_phase_row exit result=%r", result)
    return result

def _shadow_lagrange(orbit_lengths: tuple[int, ...], order: int) -> bool:
    """Host divisibility of the group order by each orbit length (declared shadow license)."""
    logger.debug("_shadow_lagrange entry order=%d", order)
    result = all(orbit > 0 and order % orbit == 0 for orbit in orbit_lengths)
    logger.debug("_shadow_lagrange exit result=%s", result)
    return result

def _shadow_orbit_length(unit: int, modulus: int) -> int:
    """Host multiplicative-orbit length (declared shadow license): above-limit fallback only."""
    logger.debug("_shadow_orbit_length entry unit=%d modulus=%d", unit, modulus)
    value, steps = unit, 1
    while value != 1:
        if steps > modulus:
            logger.debug("_shadow_orbit_length exit no return")
            return 0
        value = (value * unit) % modulus
        steps += 1
    logger.debug("_shadow_orbit_length exit steps=%d", steps)
    return steps

def native_fermat_phase_rows() -> tuple[NativeFermatPhaseRow, ...]:
    """Return canonical finite prime-period Fermat phase rows."""
    logger.debug("native_fermat_phase_rows entry")
    result = tuple(native_fermat_phase_row(period) for period in (2, 3, 5, 7))
    logger.debug("native_fermat_phase_rows exit count=%d", len(result))
    return result

def native_fermat_obstruction_rows() -> tuple[NativeFermatPhaseRow, ...]:
    """Return canonical blocked rows for non-prime or invalid periods."""
    logger.debug("native_fermat_obstruction_rows entry")
    result = tuple(native_fermat_phase_row(period) for period in (1, 4, 6))
    logger.debug("native_fermat_obstruction_rows exit count=%d", len(result))
    return result

def native_number_theorem_gaps() -> tuple[str, ...]:
    """Return still-open native number-theory gaps."""
    logger.debug("native_number_theorem_gaps entry")
    result = ("native infinite resonance-prime theorem", "unbounded native Fermat theorem beyond finite prime-period rows", "quadratic-reciprocity analogue")
    logger.debug("native_number_theorem_gaps exit count=%d", len(result))
    return result

def lean_euclid_bridge_ready() -> bool:
    """Return whether Lean checks the bridge file containing THM-F002."""
    logger.debug("lean_euclid_bridge_ready entry")
    path = lean_echo_export_path()
    has_theorem = path.exists() and "THM_F002_euclid_escape_mod" in path.read_text(
        encoding="utf-8", errors="replace",
    )
    checked = check_lean_echo_export(path).status == "checked"
    result = bool(has_theorem and checked)
    logger.debug("lean_euclid_bridge_ready exit result=%s", result)
    return result

def native_number_theorem_summary() -> dict[str, int | bool]:
    """Return compact counters for native number-theorem pressure."""
    logger.debug("native_number_theorem_summary entry")
    rows = native_euclid_rows()
    native_rows = native_euclid_mode_rows()
    fermat_rows = native_fermat_phase_rows()
    fermat_obstructions = native_fermat_obstruction_rows()
    result: dict[str, int | bool] = {
        "rows": len(rows),
        "certified": sum(row.status == "certified-shadow" for row in rows),
        "native_rows": len(native_rows),
        "native_derived": sum(row.status == "derived" for row in native_rows),
        "fermat_rows": len(fermat_rows),
        "fermat_derived": sum(row.status == "derived" for row in fermat_rows),
        "fermat_units": sum(len(row.unit_lengths) for row in fermat_rows),
        "fermat_blocked": sum(row.status == "blocked" for row in fermat_obstructions),
        "open_gaps": len(native_number_theorem_gaps()),
        "lean_f002": lean_euclid_bridge_ready(),
    }
    logger.debug("native_number_theorem_summary exit result=%r", result)
    return result
