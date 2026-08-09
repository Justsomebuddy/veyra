"""Veyra geometry from anchored events and tremor corridors."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from ..shadows.change import ratio_divide, ratio_midpoint
from ..shadows.ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventPoint:
    """Anchored observation event with ratio-coordinate shadows."""

    coordinates: tuple[RatioMode, ...]
    label: str = "event"

    @property
    def dimension(self) -> int:
        """Return event dimension."""
        logger.debug("EventPoint.dimension entry label=%s", self.label)
        result = len(self.coordinates)
        logger.debug("EventPoint.dimension exit result=%d", result)
        return result


@dataclass(frozen=True)
class TremorCorridor:
    """Bounded corridor between two observation events."""

    start: EventPoint
    end: EventPoint
    label: str = "corridor"

    def __post_init__(self) -> None:
        """Validate matching dimensions."""
        logger.debug("TremorCorridor.__post_init__ entry label=%s", self.label)
        if self.start.dimension != self.end.dimension:
            logger.error("TremorCorridor dimension mismatch")
            raise ValueError("corridor endpoints must share dimension")
        logger.debug("TremorCorridor.__post_init__ exit")

    @property
    def dimension(self) -> int:
        """Return corridor dimension."""
        logger.debug("TremorCorridor.dimension entry label=%s", self.label)
        result = self.start.dimension
        logger.debug("TremorCorridor.dimension exit result=%d", result)
        return result


@dataclass(frozen=True)
class TurnCertificate:
    """Two-dimensional turn/area orientation certificate."""

    status: str
    orientation: str
    value: RatioMode
    obstruction: str


def event_from_ints(values: tuple[int, ...], label: str = "event") -> EventPoint:
    """Create an event point from integer coordinate shadows."""
    logger.debug("event_from_ints entry values=%r label=%s", values, label)
    if not values:
        logger.error("event_from_ints empty values")
        raise ValueError("event must have at least one coordinate")
    result = EventPoint(tuple(ratio_from_ints(value) for value in values), label)
    logger.debug("event_from_ints exit dimension=%d", result.dimension)
    return result


def event_shadow(point: EventPoint) -> tuple[Fraction, ...]:
    """Return exact rational coordinate shadow of an event."""
    logger.debug("event_shadow entry label=%s", point.label)
    result = tuple(ratio_shadow(item) for item in point.coordinates)
    logger.debug("event_shadow exit dimension=%d", len(result))
    return result


def vector_between(start: EventPoint, end: EventPoint) -> tuple[RatioMode, ...]:
    """Return displacement ratios from start to end."""
    logger.debug("vector_between entry start=%s end=%s", start.label, end.label)
    if start.dimension != end.dimension:
        logger.error("vector_between dimension mismatch")
        raise ValueError("points must share dimension")
    result = tuple(subtract_ratios(b, a) for a, b in zip(start.coordinates, end.coordinates, strict=True))
    logger.debug("vector_between exit dimension=%d", len(result))
    return result


def squared_separation(left: EventPoint, right: EventPoint) -> RatioMode:
    """Return squared separation shadow between two events."""
    logger.debug("squared_separation entry left=%s right=%s", left.label, right.label)
    total = ratio_from_ints(0)
    for delta in vector_between(left, right):
        total = add_ratios(total, multiply_ratios(delta, delta))
    logger.debug("squared_separation exit result=%s", total.word)
    return total


def corridor_midpoint(corridor: TremorCorridor) -> EventPoint:
    """Return event halfway through a corridor."""
    logger.debug("corridor_midpoint entry label=%s", corridor.label)
    coords = tuple(ratio_midpoint(a, b) for a, b in zip(corridor.start.coordinates, corridor.end.coordinates, strict=True))
    result = EventPoint(coords, f"mid({corridor.label})")
    logger.debug("corridor_midpoint exit shadow=%r", event_shadow(result))
    return result


def corridor_interpolate(corridor: TremorCorridor, parameter: RatioMode) -> EventPoint:
    """Return event at start + parameter*(end-start)."""
    logger.debug("corridor_interpolate entry label=%s parameter=%s", corridor.label, parameter.word)
    coords = tuple(add_ratios(a, multiply_ratios(parameter, d)) for a, d in zip(corridor.start.coordinates, vector_between(corridor.start, corridor.end), strict=True))
    result = EventPoint(coords, f"{corridor.label}@{parameter.word}")
    logger.debug("corridor_interpolate exit shadow=%r", event_shadow(result))
    return result


def corridor_contains(corridor: TremorCorridor, point: EventPoint) -> bool:
    """Return True iff point lies on the finite corridor shadow."""
    logger.debug("corridor_contains entry corridor=%s point=%s", corridor.label, point.label)
    if corridor.dimension != point.dimension:
        logger.debug("corridor_contains exit mismatch")
        return False
    deltas = vector_between(corridor.start, corridor.end)
    offsets = vector_between(corridor.start, point)
    parameter: Fraction | None = None
    for delta, offset in zip(deltas, offsets, strict=True):
        d = ratio_shadow(delta)
        o = ratio_shadow(offset)
        if d == 0:
            if o != 0:
                logger.debug("corridor_contains exit fixed-axis miss")
                return False
            continue
        candidate = o / d
        if parameter is None:
            parameter = candidate
        elif parameter != candidate:
            logger.debug("corridor_contains exit parameter mismatch")
            return False
    result = parameter is None or Fraction(0) <= parameter <= Fraction(1)
    logger.debug("corridor_contains exit result=%s", result)
    return result


def turn_2d(first: EventPoint, second: EventPoint, third: EventPoint) -> TurnCertificate:
    """Return exact 2D orientation determinant certificate."""
    logger.debug("turn_2d entry labels=%s,%s,%s", first.label, second.label, third.label)
    if first.dimension != 2 or second.dimension != 2 or third.dimension != 2:
        logger.error("turn_2d requires plane events")
        raise ValueError("turn_2d requires three 2D events")
    ab = vector_between(first, second)
    ac = vector_between(first, third)
    det = subtract_ratios(multiply_ratios(ab[0], ac[1]), multiply_ratios(ab[1], ac[0]))
    value = ratio_shadow(det)
    orientation = "flat" if value == 0 else "left" if value > 0 else "right"
    result = TurnCertificate("exact", orientation, det, "none")
    logger.debug("turn_2d exit orientation=%s value=%s", orientation, value)
    return result


def triangle_area(first: EventPoint, second: EventPoint, third: EventPoint) -> RatioMode:
    """Return absolute triangle area shadow from a turn certificate."""
    logger.debug("triangle_area entry")
    turn = turn_2d(first, second, third)
    value = abs(ratio_shadow(turn.value)) / 2
    result = ratio_from_fraction(value)
    logger.debug("triangle_area exit result=%s", result.word)
    return result


def corridor_parameter(corridor: TremorCorridor, point: EventPoint) -> RatioMode:
    """Return exact corridor parameter for a contained nondegenerate point."""
    logger.debug("corridor_parameter entry corridor=%s point=%s", corridor.label, point.label)
    if not corridor_contains(corridor, point):
        logger.error("corridor_parameter point outside corridor")
        raise ValueError("point is not inside corridor")
    for delta, offset in zip(vector_between(corridor.start, corridor.end), vector_between(corridor.start, point), strict=True):
        if ratio_shadow(delta) != 0:
            result = ratio_divide(offset, delta)
            logger.debug("corridor_parameter exit result=%s", result.word)
            return result
    result = ratio_from_ints(0)
    logger.debug("corridor_parameter exit degenerate")
    return result
