"""Independent real-Sage oracle for the number-theory lanes.

Every row here re-derives a claim of the N8 / N2 / TR-2 / PΩ2 / primitive-root
layers with SageMath primitives that share no code with the production
implementation (`LyndonWords`, `moebius`, `Word.primitive`, `Zp` valuations,
`Mod.multiplicative_order`, `primitive_root`, `power_mod`) and compares the
two sides exactly. Real Sage is mandatory: without it every entry point fails
closed with `real-sage-required-for-number-theory-oracle`; nothing is faked.
Agreement is finite cross-check evidence (`EXECUTABLE_EVIDENCE`), not a proof,
and promotes nothing; the general statements live in
`proofs/lean/VeyraNecklaceOrbit.lean`, `VeyraPrimitiveRoot.lean` and
`VeyraPadicDomain.lean` (see `docs/188_general_number_theory_lean.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations, product
import logging
from math import gcd
import random

from src.core import break_locus
from src.core.modes import Mode, primitive_root as python_primitive_root
from src.core.native_number_theorems import native_fermat_phase_row
from src.core.necklace_congruence import fermat_orbit_witness, gauss_congruence_witness

logger = logging.getLogger(__name__)

SAGE_REQUIRED_REASON = "real-sage-required-for-number-theory-oracle"
DEFAULT_SEED = 20260904
ORACLE_ALPHABET = ("a", "b", "c", "d", "e")
COMPOSITE_PERIODS = ((4, 2, 0), (6, 2, 2), (9, 2, 4), (561, 3, 375))
LOCUS_SHAPES = (
    (("a", "b", "c"), (2, 2, 2)),
    (("a", "b"), (3, 3)),
    (("a", "b"), (4, 2)),
    (("a", "b"), (4, 4)),
    (("a", "b", "c"), (2, 2, 4)),
)


@dataclass(frozen=True, slots=True)
class NumberTheoryOracleRow:
    """One lane cross-checked against real Sage: exact counts, zero-mismatch verdict."""

    lane: str
    checked: int
    mismatches: int
    detail: str
    sage_crosscheck_passed: bool

    def as_dict(self) -> dict[str, object]:
        """Return one JSON-ready row."""
        logger.debug("NumberTheoryOracleRow.as_dict entry lane=%s", self.lane)
        result: dict[str, object] = {
            "lane": self.lane,
            "checked": self.checked,
            "mismatches": self.mismatches,
            "detail": self.detail,
            "sage_crosscheck_passed": self.sage_crosscheck_passed,
        }
        logger.debug("NumberTheoryOracleRow.as_dict exit lane=%s", self.lane)
        return result


def _sage():
    """Import the Sage namespace or fail closed."""
    logger.debug("number_theory_oracle._sage entry")
    try:
        import sage.all as sage_all  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised when Sage is absent
        logger.error("number_theory_oracle real Sage unavailable")
        raise RuntimeError(SAGE_REQUIRED_REASON) from exc
    logger.debug("number_theory_oracle._sage exit")
    return sage_all


def sage_available() -> bool:
    """Return whether real Sage can be imported in this interpreter."""
    logger.debug("number_theory_oracle.sage_available entry")
    try:
        _sage()
    except RuntimeError:
        logger.debug("number_theory_oracle.sage_available exit result=False")
        return False
    logger.debug("number_theory_oracle.sage_available exit result=True")
    return True


def _row(lane: str, checked: int, mismatches: int, detail: str) -> NumberTheoryOracleRow:
    logger.debug("number_theory_oracle._row entry lane=%s checked=%d mismatches=%d", lane, checked, mismatches)
    result = NumberTheoryOracleRow(lane, checked, mismatches, detail, checked > 0 and mismatches == 0)
    logger.debug("number_theory_oracle._row exit lane=%s passed=%s", lane, result.sage_crosscheck_passed)
    return result


def fermat_lyndon_oracle(max_prime: int = 13, max_alphabet: int = 5) -> NumberTheoryOracleRow:
    """Check `k^p - k = p · #Lyndon(k, p)` in Sage and tie the N8 orbit witnesses to it."""
    logger.debug("fermat_lyndon_oracle entry max_prime=%d max_alphabet=%d", max_prime, max_alphabet)
    sage = _sage()
    checked = mismatches = 0
    for prime in sage.primes(2, max_prime + 1):
        for size in range(2, max_alphabet + 1):
            checked += 1
            lyndon = int(sage.LyndonWords(size, prime).cardinality())
            if size**int(prime) - size != int(prime) * lyndon:
                mismatches += 1
            if int(prime) in (2, 3, 5, 7) and size in (2, 3):
                checked += 1
                witness = fermat_orbit_witness(ORACLE_ALPHABET[:size], int(prime))
                if witness.status != "witnessed" or witness.full_orbit_count != lyndon or witness.nonconstant_count != size**int(prime) - size:
                    mismatches += 1
    detail = f"primes<= {max_prime}, alphabets 2..{max_alphabet}: k^p-k == p*LyndonWords(k,p); N8 full-orbit counts tied for p in 2,3,5,7 and k in 2,3"
    result = _row("fermat-lyndon", checked, mismatches, detail)
    logger.debug("fermat_lyndon_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def gauss_mobius_oracle(max_length: int = 12, max_alphabet: int = 4) -> NumberTheoryOracleRow:
    """Check `Σ μ(d) k^(n/d) = n · #Lyndon(k, n)` in Sage and tie the N8 Gauss witnesses to it."""
    logger.debug("gauss_mobius_oracle entry max_length=%d max_alphabet=%d", max_length, max_alphabet)
    sage = _sage()
    checked = mismatches = 0
    for length in range(1, max_length + 1):
        for size in range(2, max_alphabet + 1):
            checked += 1
            mobius_count = int(sum(sage.moebius(d) * size ** (length // int(d)) for d in sage.divisors(length)))
            lyndon = int(sage.LyndonWords(size, length).cardinality())
            if mobius_count != length * lyndon or mobius_count % length:
                mismatches += 1
            if length <= 10 and size in (2, 3):
                checked += 1
                witness = gauss_congruence_witness(ORACLE_ALPHABET[:size], length)
                if witness.status != "witnessed" or witness.primitive_count != mobius_count or not witness.shadow_match:
                    mismatches += 1
    detail = f"lengths 1..{max_length}, alphabets 2..{max_alphabet}: Möbius primitive count == n*LyndonWords(k,n) and n | count; N8 Gauss witnesses tied for n<=10, k in 2,3"
    result = _row("gauss-mobius", checked, mismatches, detail)
    logger.debug("gauss_mobius_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def primitive_root_oracle(max_length: int = 7, alphabet: tuple[str, ...] = ("a", "b", "c")) -> NumberTheoryOracleRow:
    """Compare `modes.primitive_root` with Sage `Word.primitive`/`primitive_length` on every word."""
    logger.debug("primitive_root_oracle entry max_length=%d alphabet=%r", max_length, alphabet)
    sage = _sage()
    checked = mismatches = 0
    for length in range(1, max_length + 1):
        for word in product(alphabet, repeat=length):
            checked += 1
            root, exponent = python_primitive_root(Mode(word))
            sage_word = sage.Word(list(word))
            if root.tacts != tuple(sage_word.primitive()) or exponent != length // int(sage_word.primitive_length()):
                mismatches += 1
    detail = f"all words of length 1..{max_length} over {len(alphabet)} letters: primitive root and exponent agree with Sage Word.primitive/primitive_length"
    result = _row("primitive-root", checked, mismatches, detail)
    logger.debug("primitive_root_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def commutation_oracle(max_length: int = 5, alphabet: tuple[str, ...] = ("a", "b")) -> NumberTheoryOracleRow:
    """Enumerative Lyndon–Schützenberger: `uv = vu` iff `u`, `v` share a primitive root (Sage side)."""
    logger.debug("commutation_oracle entry max_length=%d alphabet=%r", max_length, alphabet)
    sage = _sage()
    words = [tuple(item) for length in range(0, max_length + 1) for item in product(alphabet, repeat=length)]
    roots = {word: (list(sage.Word(list(word)).primitive()) if word else None) for word in words}
    checked = mismatches = 0
    for left in words:
        for right in words:
            checked += 1
            commute = left + right == right + left
            predicted = not left or not right or roots[left] == roots[right]
            if commute != predicted:
                mismatches += 1
    detail = f"all ordered pairs of words of length 0..{max_length} over {len(alphabet)} letters: uv == vu iff empty or equal Sage primitive roots"
    result = _row("commutation", checked, mismatches, detail)
    logger.debug("commutation_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def padic_domain_oracle(primes: tuple[int, ...] = (2, 3, 5, 7, 11), trials: int = 200, seed: int = DEFAULT_SEED) -> NumberTheoryOracleRow:
    """Check the coordinate integral-domain law of `THM_PD_001` against Sage `Zp` valuations.

    For random depths `n, m` and residues `X, Y` below `p^(n+m+1)` that are nonzero
    modulo `p^(n+1)` and `p^(m+1)`, the product must be nonzero modulo `p^(n+m+1)`,
    and Sage valuations must satisfy `v(X) <= n`, `v(Y) <= m`, `v(XY) = v(X)+v(Y)`.
    One extra cell records that the law fails for the composite base 6.
    """
    logger.debug("padic_domain_oracle entry primes=%r trials=%d seed=%d", primes, trials, seed)
    sage = _sage()
    generator = random.Random(seed)
    checked = mismatches = 0
    for prime in primes:
        field = sage.Zp(prime, prec=30)
        for _ in range(trials):
            depth_n, depth_m = generator.randint(0, 5), generator.randint(0, 5)
            modulus = prime ** (depth_n + depth_m + 1)
            left, right = generator.randrange(modulus), generator.randrange(modulus)
            if left % prime ** (depth_n + 1) == 0 or right % prime ** (depth_m + 1) == 0:
                continue
            checked += 1
            if (left * right) % modulus == 0:
                mismatches += 1
            x_val, y_val = int(field(left).valuation()), int(field(right).valuation())
            if x_val > depth_n or y_val > depth_m or int((field(left) * field(right)).valuation()) != x_val + y_val:
                mismatches += 1
    checked += 1
    if (2 * 3) % 6 != 0:
        mismatches += 1
    detail = f"primes {primes}, {trials} seeded trials each: coordinate law and Sage Zp valuation additivity; base 6 counter-cell 2*3 == 0 mod 6 confirms primality is necessary"
    result = _row("padic-domain", checked, mismatches, detail)
    logger.debug("padic_domain_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def fermat_phase_oracle(primes: tuple[int, ...] = (2, 3, 5, 7, 11, 13), composites: tuple[tuple[int, int, int], ...] = COMPOSITE_PERIODS) -> NumberTheoryOracleRow:
    """Tie N2 orbit lengths to Sage multiplicative orders, primitive roots, and composite failures."""
    logger.debug("fermat_phase_oracle entry primes=%r composites=%r", primes, composites)
    sage = _sage()
    checked = mismatches = 0
    for prime in primes:
        checked += 1
        row = native_fermat_phase_row(prime)
        orders = tuple(int(sage.Mod(unit, prime).multiplicative_order()) for unit in range(1, prime))
        generator_order = int(sage.Mod(sage.primitive_root(prime), prime).multiplicative_order())
        if row.status != "derived" or row.orbit_lengths != orders or any((prime - 1) % order for order in orders) or generator_order != prime - 1:
            mismatches += 1
    for period, unit, residue in composites:
        checked += 1
        row = native_fermat_phase_row(period)
        if sage.is_prime(period) or int(sage.power_mod(unit, period - 1, period)) != residue or row.status != "blocked" or row.residues[unit - 1] != residue:
            mismatches += 1
    detail = f"primes {primes}: orbit lengths == Sage multiplicative orders, Lagrange and generator; composite periods {tuple(item[0] for item in composites)}: Sage power_mod confirms the exhibited failing unit"
    result = _row("fermat-phase", checked, mismatches, detail)
    logger.debug("fermat_phase_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def _gcd_form_locus(sage, word: tuple[str, ...], alphabet: tuple[str, ...]) -> tuple[tuple[tuple[str, str], ...], ...]:
    """Break locus in gcd form with projection exponents taken from Sage `primitive_length`."""
    logger.debug("number_theory_oracle._gcd_form_locus entry word=%s", "".join(word))
    letters = tuple(sorted(alphabet))
    count_gcd = 0
    for letter in letters:
        count_gcd = gcd(count_gcd, word.count(letter))
    floors: list[set[tuple[str, str]]] = []
    for divisor in sage.divisors(count_gcd) if count_gcd else ():
        if not sage.is_prime(divisor):
            continue
        floor: set[tuple[str, str]] = set()
        for left, right in combinations(letters, 2):
            projection = [item for item in word if item in (left, right)]
            exponent = len(projection) // int(sage.Word(projection).primitive_length()) if projection else 0
            if exponent % int(divisor):
                floor.add((left, right))
        floors.append(floor)
    minimal = sorted({tuple(sorted(item)) for item in floors if not any(other < item for other in floors)})
    result = tuple(minimal)
    logger.debug("number_theory_oracle._gcd_form_locus exit size=%d", len(result))
    return result


def break_locus_gcd_oracle(shapes: tuple[tuple[tuple[str, ...], tuple[int, ...]], ...] = LOCUS_SHAPES) -> NumberTheoryOracleRow:
    """Compare `break_locus.locus_formula` with the gcd-form locus computed from Sage exponents."""
    logger.debug("break_locus_gcd_oracle entry shapes=%d", len(shapes))
    sage = _sage()
    checked = mismatches = 0
    for alphabet, counts in shapes:
        base = tuple(letter for letter, count in zip(alphabet, counts, strict=True) for _ in range(count))
        for word in set(permutations(base)):
            checked += 1
            expected = _gcd_form_locus(sage, word, alphabet)
            actual = tuple(tuple(pair) for pair in break_locus.locus_formula(word, alphabet))
            if expected != actual:
                mismatches += 1
    checked += 1
    witness, alphabet = break_locus.refutation_witness()
    expected = _gcd_form_locus(sage, tuple(witness), tuple(alphabet))
    if expected != ((("a", "b"), ("b", "c")), (("a", "c"), ("b", "c"))) or expected != tuple(tuple(pair) for pair in break_locus.locus_formula(tuple(witness), tuple(alphabet))):
        mismatches += 1
    detail = f"{len(shapes)} exhaustive shapes plus the refutation witness: min-antichain of Sage-exponent prime floors == locus_formula"
    result = _row("break-locus-gcd", checked, mismatches, detail)
    logger.debug("break_locus_gcd_oracle exit checked=%d mismatches=%d", checked, mismatches)
    return result


def number_theory_oracle_rows() -> tuple[NumberTheoryOracleRow, ...]:
    """Run every real-Sage cross-check lane with the canonical bounds."""
    logger.debug("number_theory_oracle_rows entry")
    result = (
        fermat_lyndon_oracle(),
        gauss_mobius_oracle(),
        primitive_root_oracle(),
        commutation_oracle(),
        padic_domain_oracle(),
        fermat_phase_oracle(),
        break_locus_gcd_oracle(),
    )
    logger.debug("number_theory_oracle_rows exit rows=%d", len(result))
    return result


class VeyraNumberTheoryOracleLab:
    """JSON-ready facade for the real-Sage number-theory oracle."""

    def rows(self) -> list[dict[str, object]]:
        """Return every lane row (requires real Sage)."""
        logger.debug("VeyraNumberTheoryOracleLab.rows entry")
        result = [row.as_dict() for row in number_theory_oracle_rows()]
        logger.debug("VeyraNumberTheoryOracleLab.rows exit rows=%d", len(result))
        return result

    def summary(self) -> dict[str, object]:
        """Return the oracle verdict, or a typed unavailable record without Sage."""
        logger.debug("VeyraNumberTheoryOracleLab.summary entry")
        if not sage_available():
            result: dict[str, object] = {"backend": "unavailable", "status": "unavailable", "reason": SAGE_REQUIRED_REASON, "rows": [], "lanes": 0, "checked": 0, "mismatches": 0}
            logger.error("VeyraNumberTheoryOracleLab.summary unavailable reason=%s", SAGE_REQUIRED_REASON)
            return result
        lane_rows = number_theory_oracle_rows()
        checked = sum(row.checked for row in lane_rows)
        mismatches = sum(row.mismatches for row in lane_rows)
        passed = bool(lane_rows) and all(row.sage_crosscheck_passed for row in lane_rows)
        result = {
            "backend": "python+real-sage",
            "status": "witnessed" if passed else "blocked",
            "reason": "none" if passed else "sage-crosscheck-mismatch",
            "rows": [row.as_dict() for row in lane_rows],
            "lanes": len(lane_rows),
            "checked": checked,
            "mismatches": mismatches,
            "evidence_level": "EXECUTABLE_EVIDENCE",
            "nonclaims": (
                "finite cross-check only; the general statements are the Lean theorems, not these rows",
                "agreement with Sage promotes no registry status",
                "no native Veyra quantifier; every count is host arithmetic",
            ),
        }
        logger.debug("VeyraNumberTheoryOracleLab.summary exit status=%s", result["status"])
        return result


def number_theory_oracle_summary() -> dict[str, object]:
    """Return the lab summary."""
    logger.debug("number_theory_oracle_summary entry")
    result = VeyraNumberTheoryOracleLab().summary()
    logger.debug("number_theory_oracle_summary exit status=%s", result["status"])
    return result
