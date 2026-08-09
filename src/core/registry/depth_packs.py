"""Depth packs and Sage export adapters for Veyra school-core coverage."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from math import comb, factorial

from ..numbers.cyclic_probability_stats import FiniteDistribution, SampleEcho, probability_of, sample_variance
from ..geometry.theorems import TheoremCard
from ..shadows.ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow, subtract_ratios
from .theorem_registry import TheoremSpec

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SageExportRow:
    """JSON-ready row for future Sage theorem/curriculum export."""

    row_type: str
    name: str
    domain: str
    hook: str
    payload: tuple[tuple[str, str], ...]


def factorial_echo(n: int) -> RatioMode:
    """Return exact factorial count echo."""
    logger.debug("factorial_echo entry n=%d", n)
    if n < 0:
        logger.error("factorial_echo negative n=%d", n)
        raise ValueError("n must be nonnegative")
    result = ratio_from_ints(factorial(n))
    logger.debug("factorial_echo exit result=%s", result.word)
    return result


def choose_echo(n: int, k: int) -> RatioMode:
    """Return exact binomial count echo."""
    logger.debug("choose_echo entry n=%d k=%d", n, k)
    if n < 0 or k < 0 or k > n:
        logger.error("choose_echo invalid n=%d k=%d", n, k)
        raise ValueError("require 0 <= k <= n")
    result = ratio_from_ints(comb(n, k))
    logger.debug("choose_echo exit result=%s", result.word)
    return result


def binomial_symmetry_card(n: int, k: int) -> TheoremCard:
    """Card proving `C(n,k)=C(n,n-k)`."""
    logger.debug("binomial_symmetry_card entry n=%d k=%d", n, k)
    left = choose_echo(n, k)
    right = choose_echo(n, n - k)
    relation = "symmetric" if ratio_shadow(left) == ratio_shadow(right) else "broken"
    result = TheoremCard("binomial-symmetry", "exact", relation, "none" if relation == "symmetric" else "count-mismatch", (("left", str(ratio_shadow(left))), ("right", str(ratio_shadow(right)))))
    logger.debug("binomial_symmetry_card exit relation=%s", relation)
    return result


def probability_union_card(distribution: FiniteDistribution, left: frozenset[str], right: frozenset[str]) -> TheoremCard:
    """Card proving finite union probability additivity with intersection subtraction."""
    logger.debug("probability_union_card entry")
    union = probability_of(distribution, left | right)
    p_left = probability_of(distribution, left)
    p_right = probability_of(distribution, right)
    p_intersection = probability_of(distribution, left & right)
    rhs = subtract_ratios(add_ratios(p_left, p_right), p_intersection)
    relation = "additive" if ratio_shadow(union) == ratio_shadow(rhs) else "broken"
    result = TheoremCard("probability-union", "exact", relation, "none" if relation == "additive" else "union-gap", (("union", str(ratio_shadow(union))), ("rhs", str(ratio_shadow(rhs)))))
    logger.debug("probability_union_card exit relation=%s", relation)
    return result


def independence_card(distribution: FiniteDistribution, left: frozenset[str], right: frozenset[str]) -> TheoremCard:
    """Card classifying finite events by `P(A∩B)=P(A)P(B)`."""
    logger.debug("independence_card entry")
    p_intersection = probability_of(distribution, left & right)
    product = multiply_ratios(probability_of(distribution, left), probability_of(distribution, right))
    relation = "independent" if ratio_shadow(p_intersection) == ratio_shadow(product) else "dependent"
    result = TheoremCard("probability-independence", "exact", relation, "none" if relation == "independent" else "product-gap", (("intersection", str(ratio_shadow(p_intersection))), ("product", str(ratio_shadow(product)))))
    logger.debug("independence_card exit relation=%s", relation)
    return result


def shifted_sample(sample: SampleEcho, shift: RatioMode) -> SampleEcho:
    """Return sample shifted by a constant ratio echo."""
    logger.debug("shifted_sample entry count=%d shift=%s", len(sample.values), shift.word)
    result = SampleEcho(tuple(add_ratios(value, shift) for value in sample.values))
    logger.debug("shifted_sample exit")
    return result


def variance_shift_card(sample: SampleEcho, shift: RatioMode) -> TheoremCard:
    """Card proving variance is invariant under constant shifts."""
    logger.debug("variance_shift_card entry")
    base = sample_variance(sample)
    shifted = sample_variance(shifted_sample(sample, shift))
    relation = "invariant" if ratio_shadow(base) == ratio_shadow(shifted) else "broken"
    result = TheoremCard("variance-shift", "exact", relation, "none" if relation == "invariant" else "variance-gap", (("base", str(ratio_shadow(base))), ("shifted", str(ratio_shadow(shifted)))))
    logger.debug("variance_shift_card exit relation=%s", relation)
    return result


def theorem_sage_export_rows(specs: dict[str, TheoremSpec]) -> tuple[SageExportRow, ...]:
    """Export theorem specs into Sage-facing rows."""
    logger.debug("theorem_sage_export_rows entry count=%d", len(specs))
    rows = []
    for spec in sorted(specs.values(), key=lambda item: item.theorem_id):
        domain = spec.sage_hook.split(".", 1)[0] if "." in spec.sage_hook else "pending"
        rows.append(SageExportRow("theorem", spec.theorem_id, domain, spec.sage_hook, (("deps", ",".join(spec.dependencies)), ("success", ",".join(spec.success_relations)))))
    result = tuple(rows)
    logger.debug("theorem_sage_export_rows exit rows=%d", len(result))
    return result


def curriculum_sage_export_rows(rows: tuple[tuple[str, str, str, str], ...]) -> tuple[SageExportRow, ...]:
    """Wrap curriculum export tuples into Sage rows."""
    logger.debug("curriculum_sage_export_rows entry rows=%d", len(rows))
    result = tuple(SageExportRow("curriculum", concept, domain, hook, (("theorem", theorem),)) for concept, domain, theorem, hook in rows)
    logger.debug("curriculum_sage_export_rows exit rows=%d", len(result))
    return result
