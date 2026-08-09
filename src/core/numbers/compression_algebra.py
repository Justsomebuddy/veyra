"""Compression algebra: edit drift, trees, roots, and cost comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging
from typing import Iterable

from .compression import CompressionWeights, best_compression
from .modes import Mode, enumerate_modes, repeat_mode
from ..shadows.polynomial import Polynomial, eval_polynomial, normalize_polynomial
from ..shadows.ratio import RatioMode, ratio_from_fraction, ratio_from_ints, ratio_shadow
from .resonance import rotate_mode
from .tact_similarity import aura_cost_map
from .weighted_resonance import CostMap, WeightedResonanceProfile, weighted_resonance_profile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EditResonanceProfile:
    """Best insert/delete/substitution drift resonance profile."""

    part: Mode
    whole: Mode
    max_edits: int
    exponent: int
    offset: int
    expected: Mode
    rotated: Mode
    distance: int
    resonates: bool
    obstruction: str


def edit_distance(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    """Return Levenshtein distance with unit insert/delete/substitute costs."""
    logger.debug("edit_distance entry left=%d right=%d", len(left), len(right))
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, start=1):
        current = [i]
        for j, b in enumerate(right, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a != b)))
        previous = current
    result = previous[-1]
    logger.debug("edit_distance exit result=%d", result)
    return result


def edit_resonance_profile(part: Mode, whole: Mode, max_edits: int) -> EditResonanceProfile:
    """Return best cyclic edit-drift resonance profile."""
    logger.debug("edit_resonance_profile entry part=%s whole=%s max_edits=%d", part.word, whole.word, max_edits)
    if max_edits < 0:
        logger.error("edit_resonance_profile invalid max_edits=%d", max_edits)
        raise ValueError("max_edits must be non-negative")
    if part.length == 0:
        return EditResonanceProfile(part, whole, max_edits, 0, 0, part, whole, whole.length, False, "silent-part")
    lo = max(1, (max(0, whole.length - max_edits) + part.length - 1) // part.length)
    hi = max(lo, (whole.length + max_edits) // part.length + 1)
    matches: list[tuple[int, int, int, Mode, Mode]] = []
    for exponent in range(lo, hi + 1):
        expected = repeat_mode(part, exponent)
        for offset in range(whole.length if whole.length else 1):
            rotated = rotate_mode(whole, offset)
            matches.append((edit_distance(expected.tacts, rotated.tacts), exponent, offset, expected, rotated))
    distance, exponent, offset, expected, rotated = min(matches, key=lambda item: (item[0], abs(item[3].length - whole.length), item[1], item[2]))
    obstruction = "none" if distance == 0 else "edit-drift" if distance <= max_edits else "over-budget"
    result = EditResonanceProfile(part, whole, max_edits, exponent, offset, expected, rotated, distance, distance <= max_edits, obstruction)
    logger.debug("edit_resonance_profile exit result=%r", result)
    return result


@dataclass(frozen=True)
class CompressionTree:
    """Hierarchical compression explanation tree."""

    mode: Mode
    part: Mode | None
    saving: float
    repeats: int
    children: tuple["CompressionTree", ...]
    status: str


def hierarchical_compression_tree(mode: Mode, max_depth: int, max_defects: int, weights: CompressionWeights = CompressionWeights()) -> CompressionTree:
    """Build a recursive positive-saving compression tree."""
    logger.debug("hierarchical_compression_tree entry mode=%s depth=%d", mode.word, max_depth)
    if max_depth <= 0 or mode.length <= 1:
        return CompressionTree(mode, None, 0.0, 1, (), "leaf")
    alphabet = tuple(sorted(set(mode.tacts)))
    candidates = [item for item in enumerate_modes(alphabet, max(1, mode.length - 1), include_silent=False) if item.length < mode.length]
    best = best_compression(mode, candidates, max_defects, weights)
    if best is None or best.saving <= 0:
        return CompressionTree(mode, None, 0.0, 1, (), "leaf")
    repeats = mode.length // best.part.length if best.part.length else 0
    child = hierarchical_compression_tree(best.part, max_depth - 1, max_defects, weights)
    result = CompressionTree(mode, best.part, best.saving, repeats, (child,), "split")
    logger.debug("hierarchical_compression_tree exit result=%r", result)
    return result


@dataclass(frozen=True)
class PolynomialFactorHit:
    """Native polynomial root/factor search hit."""

    root: RatioMode
    factor: Polynomial
    quotient: Polynomial
    residual: RatioMode


def divide_by_linear_root(poly: Polynomial, root: RatioMode) -> Polynomial:
    """Synthetic divide a polynomial by x-root in rational shadow terms."""
    logger.debug("divide_by_linear_root entry degree=%d root=%s", poly.degree, root.word)
    if poly.degree < 1:
        logger.error("divide_by_linear_root constant polynomial")
        raise ValueError("polynomial degree must be at least one")
    r = ratio_shadow(root)
    coeffs = [ratio_shadow(item) for item in poly.coefficients]
    acc = coeffs[-1]
    out = [acc]
    for coeff in reversed(coeffs[1:-1]):
        acc = coeff + r * acc
        out.append(acc)
    result = normalize_polynomial(Polynomial(tuple(ratio_from_fraction(item) for item in reversed(out))))
    logger.debug("divide_by_linear_root exit degree=%d", result.degree)
    return result


def polynomial_factor_search(poly: Polynomial, candidates: Iterable[int | Fraction]) -> tuple[PolynomialFactorHit, ...]:
    """Search exact rational roots and return linear factor hits."""
    logger.debug("polynomial_factor_search entry degree=%d", poly.degree)
    hits: list[PolynomialFactorHit] = []
    for candidate in candidates:
        root = ratio_from_fraction(Fraction(candidate))
        residual = eval_polynomial(poly, root)
        if ratio_shadow(residual) == 0:
            factor = normalize_polynomial(Polynomial((ratio_from_fraction(-ratio_shadow(root)), ratio_from_ints(1))))
            hits.append(PolynomialFactorHit(root, factor, divide_by_linear_root(poly, root), residual))
    result = tuple(hits)
    logger.debug("polynomial_factor_search exit hits=%d", len(result))
    return result


@dataclass(frozen=True)
class CostComparisonRow:
    """Weighted resonance result under one mismatch-cost strategy."""

    strategy: str
    profile: WeightedResonanceProfile
    best_cost: float | None


def compare_cost_strategies(part: Mode, whole: Mode, budget: float, context: Iterable[Mode], alphabet: Iterable[str], manual: CostMap) -> tuple[CostComparisonRow, ...]:
    """Compare uniform, manual, and aura-derived weighted resonance costs."""
    logger.debug("compare_cost_strategies entry part=%s whole=%s", part.word, whole.word)
    strategies = (("uniform", {}), ("manual", manual), ("aura", aura_cost_map(context, alphabet)))
    rows = []
    for name, costs in strategies:
        profile = weighted_resonance_profile(part, whole, budget, costs)
        rows.append(CostComparisonRow(name, profile, None if profile.best is None else profile.best.total_cost))
    result = tuple(rows)
    logger.debug("compare_cost_strategies exit rows=%d", len(result))
    return result


def compression_algebra_checklist() -> tuple[str, ...]:
    """Return Sprint B compression-algebra checklist."""
    logger.debug("compression_algebra_checklist entry")
    result = ("edit insert/delete drift", "hierarchical compression tree", "native polynomial root/factor hit", "aura/manual/uniform cost comparison")
    logger.debug("compression_algebra_checklist exit count=%d", len(result))
    return result
