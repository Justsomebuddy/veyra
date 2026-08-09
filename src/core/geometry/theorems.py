"""Executable theorem cards for Veyra geometry."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging
from math import isqrt

from ..geometry import EventPoint, TremorCorridor, event_from_ints, event_shadow, squared_separation, vector_between
from .relations import PlaneRelabel, relabel_event, triangle_congruence
from ..shadows.ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TheoremCard:
    """Small executable theorem certificate with string evidence."""

    name: str
    status: str
    relation: str
    obstruction: str
    evidence: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class IntersectionCard:
    """Line/corridor against constant-separation shell certificate."""

    status: str
    relation: str
    parameters: tuple[RatioMode, ...]
    obstruction: str


def ratio_text(value: RatioMode) -> str:
    """Return compact exact ratio-shadow text."""
    logger.debug("ratio_text entry value=%s", value.word)
    result = str(ratio_shadow(value))
    logger.debug("ratio_text exit result=%s", result)
    return result


def dot_vectors(left: tuple[RatioMode, ...], right: tuple[RatioMode, ...]) -> RatioMode:
    """Return exact dot echo of two equal-dimensional displacement vectors."""
    logger.debug("dot_vectors entry dims=%d/%d", len(left), len(right))
    if len(left) != len(right):
        logger.error("dot_vectors dimension mismatch")
        raise ValueError("vectors must share dimension")
    total = ratio_from_ints(0)
    for a, b in zip(left, right, strict=True):
        total = add_ratios(total, multiply_ratios(a, b))
    logger.debug("dot_vectors exit result=%s", total.word)
    return total


def dot_echo(anchor: EventPoint, first: EventPoint, second: EventPoint) -> RatioMode:
    """Return dot echo of corridors anchor->first and anchor->second."""
    logger.debug("dot_echo entry anchor=%s first=%s second=%s", anchor.label, first.label, second.label)
    result = dot_vectors(vector_between(anchor, first), vector_between(anchor, second))
    logger.debug("dot_echo exit result=%s", result.word)
    return result


def pythagorean_card(apex: EventPoint, leg_one: EventPoint, leg_two: EventPoint) -> TheoremCard:
    """Certify Pythagorean separation decomposition at a right apex."""
    logger.debug("pythagorean_card entry apex=%s", apex.label)
    dot = dot_echo(apex, leg_one, leg_two)
    left = squared_separation(leg_one, leg_two)
    right = add_ratios(squared_separation(apex, leg_one), squared_separation(apex, leg_two))
    is_right = ratio_shadow(dot) == 0
    relation = "proven" if is_right and ratio_shadow(left) == ratio_shadow(right) else "blocked"
    obstruction = "none" if relation == "proven" else "non-right-apex" if not is_right else "decomposition-mismatch"
    result = TheoremCard("pythagorean-separation", "exact", relation, obstruction, (("dot", ratio_text(dot)), ("hyp_echo", ratio_text(left)), ("leg_sum", ratio_text(right))))
    logger.debug("pythagorean_card exit relation=%s", relation)
    return result


def sss_card(left: tuple[EventPoint, EventPoint, EventPoint], right: tuple[EventPoint, EventPoint, EventPoint], preserve_turn: bool = True) -> TheoremCard:
    """Certify SSS triangle congruence using existing triangle signature."""
    logger.debug("sss_card entry preserve_turn=%s", preserve_turn)
    cert = triangle_congruence(left, right, preserve_turn)
    result = TheoremCard("sss-triangle", cert.status, cert.relation, cert.obstruction, (("left_max_side", ratio_text(cert.left_measure)), ("right_max_side", ratio_text(cert.right_measure))))
    logger.debug("sss_card exit relation=%s", result.relation)
    return result


def sas_card(left: tuple[EventPoint, EventPoint, EventPoint], right: tuple[EventPoint, EventPoint, EventPoint], preserve_turn: bool = True) -> TheoremCard:
    """Certify SAS-like congruence by two side echoes and included dot echo."""
    logger.debug("sas_card entry preserve_turn=%s", preserve_turn)
    la, lb, lc = left
    ra, rb, rc = right
    measures = (
        squared_separation(la, lb), squared_separation(la, lc), dot_echo(la, lb, lc),
        squared_separation(ra, rb), squared_separation(ra, rc), dot_echo(ra, rb, rc),
    )
    same = tuple(map(ratio_shadow, measures[:3])) == tuple(map(ratio_shadow, measures[3:]))
    turn_ok = True if not preserve_turn else triangle_congruence(left, right).obstruction != "turn-mismatch"
    relation = "congruent" if same and turn_ok else "different"
    obstruction = "none" if relation == "congruent" else "turn-mismatch" if same else "side-dot-mismatch"
    result = TheoremCard("sas-triangle", "exact", relation, obstruction, (("left_side_a", ratio_text(measures[0])), ("left_side_b", ratio_text(measures[1])), ("left_dot", ratio_text(measures[2]))))
    logger.debug("sas_card exit relation=%s obstruction=%s", relation, obstruction)
    return result


def exact_sqrt_fraction(value: Fraction) -> Fraction | None:
    """Return exact rational square root when it exists."""
    logger.debug("exact_sqrt_fraction entry value=%s", value)
    if value < 0:
        return None
    n = isqrt(value.numerator)
    d = isqrt(value.denominator)
    result = Fraction(n, d) if n * n == value.numerator and d * d == value.denominator else None
    logger.debug("exact_sqrt_fraction exit result=%s", result)
    return result


def line_shell_intersections(corridor: TremorCorridor, center: EventPoint, radius_squared: RatioMode) -> IntersectionCard:
    """Solve corridor intersection with constant-separation shell using exact rational roots."""
    logger.debug("line_shell_intersections entry corridor=%s center=%s", corridor.label, center.label)
    d = tuple(ratio_shadow(x) for x in vector_between(corridor.start, corridor.end))
    f = tuple(ratio_shadow(x) for x in vector_between(center, corridor.start))
    a = sum(x * x for x in d)
    b = 2 * sum(x * y for x, y in zip(d, f, strict=True))
    c = sum(x * x for x in f) - ratio_shadow(radius_squared)
    if a == 0:
        relation = "degenerate-on" if c == 0 else "none"
        params = (ratio_from_ints(0),) if c == 0 else ()
        return IntersectionCard("exact", relation, params, "none" if c == 0 else "degenerate-off")
    disc = b * b - 4 * a * c
    root = exact_sqrt_fraction(disc)
    if root is None:
        obstruction = "no-real-crossing" if disc < 0 else "irrational-parameters"
        relation = "none" if disc < 0 else "completion-needed"
        return IntersectionCard("exact", relation, (), obstruction)
    roots = {(-b - root) / (2 * a), (-b + root) / (2 * a)}
    inside = tuple(ratio_from_fraction(x) for x in sorted(roots) if Fraction(0) <= x <= Fraction(1))
    relation = "none" if not inside else "tangent" if len(inside) == 1 else "two"
    result = IntersectionCard("exact", relation, inside, "none" if inside else "outside-segment")
    logger.debug("line_shell_intersections exit relation=%s count=%d", relation, len(inside))
    return result


def identity_relabel() -> PlaneRelabel:
    """Return identity plane relabeling."""
    logger.debug("identity_relabel entry")
    one = ratio_from_ints(1)
    zero = ratio_from_ints(0)
    result = PlaneRelabel(((one, zero), (zero, one)), event_from_ints((0, 0), "offset"), "identity")
    logger.debug("identity_relabel exit")
    return result


def compose_relabels(outer: PlaneRelabel, inner: PlaneRelabel, label: str = "compose") -> PlaneRelabel:
    """Compose plane relabels as outer(inner(event))."""
    logger.debug("compose_relabels entry outer=%s inner=%s", outer.label, inner.label)
    rows = []
    for row in outer.matrix:
        rows.append(tuple(add_ratios(multiply_ratios(row[0], inner.matrix[0][col]), multiply_ratios(row[1], inner.matrix[1][col])) for col in range(2)))
    shifted = relabel_event(outer, inner.offset)
    result = PlaneRelabel((rows[0], rows[1]), shifted, label)
    logger.debug("compose_relabels exit label=%s", label)
    return result


def relabel_composition_card(outer: PlaneRelabel, inner: PlaneRelabel, sample: EventPoint) -> TheoremCard:
    """Certify that composed relabel equals sequential relabel on a sample event."""
    logger.debug("relabel_composition_card entry sample=%s", sample.label)
    composed = relabel_event(compose_relabels(outer, inner), sample)
    sequential = relabel_event(outer, relabel_event(inner, sample))
    same = event_shadow(composed) == event_shadow(sequential)
    result = TheoremCard("plane-relabel-composition", "exact", "proven" if same else "blocked", "none" if same else "shadow-mismatch", (("composed", str(event_shadow(composed))), ("sequential", str(event_shadow(sequential)))))
    logger.debug("relabel_composition_card exit relation=%s", result.relation)
    return result
