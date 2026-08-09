"""Congruence, shells, and relabel transforms for Veyra geometry."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..geometry import EventPoint, TremorCorridor, event_from_ints, event_shadow, squared_separation, turn_2d, vector_between
from ..shadows.ratio import RatioMode, add_ratios, multiply_ratios, ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CongruenceCertificate:
    """Exact certificate for equal separation echoes."""

    status: str
    relation: str
    left_measure: RatioMode
    right_measure: RatioMode
    obstruction: str


@dataclass(frozen=True)
class TriangleSignature:
    """Triangle signature by sorted side echoes and turn orientation."""

    side_echoes: tuple[RatioMode, RatioMode, RatioMode]
    orientation: str


@dataclass(frozen=True)
class ShellCertificate:
    """Constant-separation shell membership certificate."""

    status: str
    relation: str
    separation: RatioMode
    shell: RatioMode
    obstruction: str


@dataclass(frozen=True)
class ParallelCertificate:
    """Two-dimensional corridor parallelism certificate."""

    status: str
    relation: str
    determinant: RatioMode
    obstruction: str


@dataclass(frozen=True)
class PlaneRelabel:
    """Two-dimensional affine relabeling of event shadows."""

    matrix: tuple[tuple[RatioMode, RatioMode], tuple[RatioMode, RatioMode]]
    offset: EventPoint
    label: str = "relabel"

    def __post_init__(self) -> None:
        """Validate plane offset."""
        logger.debug("PlaneRelabel.__post_init__ entry label=%s", self.label)
        if self.offset.dimension != 2:
            logger.error("PlaneRelabel invalid offset dimension=%d", self.offset.dimension)
            raise ValueError("plane relabel offset must be two-dimensional")
        logger.debug("PlaneRelabel.__post_init__ exit")


def corridor_congruence(left: TremorCorridor, right: TremorCorridor) -> CongruenceCertificate:
    """Compare two corridors by squared separation echo."""
    logger.debug("corridor_congruence entry left=%s right=%s", left.label, right.label)
    a = squared_separation(left.start, left.end)
    b = squared_separation(right.start, right.end)
    relation = "congruent" if ratio_shadow(a) == ratio_shadow(b) else "different"
    result = CongruenceCertificate("exact", relation, a, b, "none" if relation == "congruent" else "separation-mismatch")
    logger.debug("corridor_congruence exit relation=%s", relation)
    return result


def sorted_side_echoes(first: EventPoint, second: EventPoint, third: EventPoint) -> tuple[RatioMode, RatioMode, RatioMode]:
    """Return triangle side echoes sorted by exact rational shadow."""
    logger.debug("sorted_side_echoes entry")
    echoes = (squared_separation(first, second), squared_separation(second, third), squared_separation(third, first))
    result = tuple(sorted(echoes, key=ratio_shadow))  # type: ignore[return-value]
    logger.debug("sorted_side_echoes exit shadows=%r", tuple(ratio_shadow(x) for x in result))
    return result


def triangle_signature(first: EventPoint, second: EventPoint, third: EventPoint) -> TriangleSignature:
    """Return side+turn signature for a triangle event family."""
    logger.debug("triangle_signature entry")
    result = TriangleSignature(sorted_side_echoes(first, second, third), turn_2d(first, second, third).orientation)
    logger.debug("triangle_signature exit orientation=%s", result.orientation)
    return result


def triangle_congruence(left: tuple[EventPoint, EventPoint, EventPoint], right: tuple[EventPoint, EventPoint, EventPoint], preserve_turn: bool = True) -> CongruenceCertificate:
    """Compare triangles by side echoes and optional turn orientation."""
    logger.debug("triangle_congruence entry preserve_turn=%s", preserve_turn)
    a = triangle_signature(*left)
    b = triangle_signature(*right)
    same_sides = tuple(map(ratio_shadow, a.side_echoes)) == tuple(map(ratio_shadow, b.side_echoes))
    same_turn = a.orientation == b.orientation or not preserve_turn
    relation = "congruent" if same_sides and same_turn else "different"
    obstruction = "none" if relation == "congruent" else "turn-mismatch" if same_sides else "side-mismatch"
    result = CongruenceCertificate("exact", relation, a.side_echoes[-1], b.side_echoes[-1], obstruction)
    logger.debug("triangle_congruence exit relation=%s obstruction=%s", relation, obstruction)
    return result


def circle_shell(center: EventPoint, radius_squared: RatioMode, point: EventPoint) -> ShellCertificate:
    """Classify point against constant squared-separation shell."""
    logger.debug("circle_shell entry center=%s point=%s", center.label, point.label)
    sep = squared_separation(center, point)
    left = ratio_shadow(sep)
    right = ratio_shadow(radius_squared)
    relation = "on" if left == right else "inside" if left < right else "outside"
    result = ShellCertificate("exact", relation, sep, radius_squared, "none" if relation == "on" else relation)
    logger.debug("circle_shell exit relation=%s", relation)
    return result


def parallel_corridors_2d(left: TremorCorridor, right: TremorCorridor) -> ParallelCertificate:
    """Return exact 2D parallelism certificate for two corridors."""
    logger.debug("parallel_corridors_2d entry left=%s right=%s", left.label, right.label)
    if left.dimension != 2 or right.dimension != 2:
        logger.error("parallel_corridors_2d invalid dimension")
        raise ValueError("parallel check requires two-dimensional corridors")
    a = vector_between(left.start, left.end)
    b = vector_between(right.start, right.end)
    det = add_ratios(multiply_ratios(a[0], b[1]), multiply_ratios(multiply_ratios(a[1], b[0]), ratio_from_ints(-1)))
    relation = "parallel" if ratio_shadow(det) == 0 else "turning"
    result = ParallelCertificate("exact", relation, det, "none" if relation == "parallel" else "nonzero-turn")
    logger.debug("parallel_corridors_2d exit relation=%s", relation)
    return result


def relabel_event(relabel: PlaneRelabel, event: EventPoint) -> EventPoint:
    """Apply an affine plane relabeling to an event."""
    logger.debug("relabel_event entry relabel=%s event=%s", relabel.label, event.label)
    if event.dimension != 2:
        logger.error("relabel_event invalid dimension=%d", event.dimension)
        raise ValueError("plane relabel requires two-dimensional event")
    x, y = event.coordinates
    rows = relabel.matrix
    first = add_ratios(add_ratios(multiply_ratios(rows[0][0], x), multiply_ratios(rows[0][1], y)), relabel.offset.coordinates[0])
    second = add_ratios(add_ratios(multiply_ratios(rows[1][0], x), multiply_ratios(rows[1][1], y)), relabel.offset.coordinates[1])
    result = EventPoint((first, second), f"{relabel.label}({event.label})")
    logger.debug("relabel_event exit shadow=%r", event_shadow(result))
    return result


def translation_relabel(dx: int, dy: int) -> PlaneRelabel:
    """Return plane translation relabeling."""
    logger.debug("translation_relabel entry dx=%d dy=%d", dx, dy)
    one = ratio_from_ints(1)
    zero = ratio_from_ints(0)
    result = PlaneRelabel(((one, zero), (zero, one)), event_from_ints((dx, dy), "offset"), "translate")
    logger.debug("translation_relabel exit")
    return result


def scale_relabel(factor: int) -> PlaneRelabel:
    """Return uniform integer scale relabeling."""
    logger.debug("scale_relabel entry factor=%d", factor)
    s = ratio_from_ints(factor)
    zero = ratio_from_ints(0)
    result = PlaneRelabel(((s, zero), (zero, s)), event_from_ints((0, 0), "offset"), "scale")
    logger.debug("scale_relabel exit")
    return result


def quarter_turn_relabel() -> PlaneRelabel:
    """Return quarter-turn relabeling `(x,y)->(-y,x)`."""
    logger.debug("quarter_turn_relabel entry")
    one = ratio_from_ints(1)
    zero = ratio_from_ints(0)
    neg = ratio_from_ints(-1)
    result = PlaneRelabel(((zero, neg), (one, zero)), event_from_ints((0, 0), "offset"), "quarter_turn")
    logger.debug("quarter_turn_relabel exit")
    return result
