"""Native geometry derivation pressure for finite right-corner theorem rows."""
from __future__ import annotations
from dataclasses import dataclass
from math import isqrt
import logging
from ..native_runtime import Breath, NativeObstruction, breath, nod, observe_native, rez, tact

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class NativeRightCornerRow:
    """One finite right-corner row derived from native Breath lengths."""
    theorem_id: str
    leg_lengths: tuple[int, int]
    hypotenuse: int
    leg_square_sum: int
    hyp_square: int
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready native geometry row."""
        logger.debug("NativeRightCornerRow.as_dict entry theorem=%s", self.theorem_id)
        result = self.__dict__.copy()
        logger.debug("NativeRightCornerRow.as_dict exit result=%r", result)
        return result

def native_axis_breath(axis: str, length: int) -> Breath | NativeObstruction:
    """Build a native open Breath with `length` steps along one axis residue family."""
    logger.debug("native_axis_breath entry axis=%s length=%d", axis, length)
    if length <= 0:
        result = NativeObstruction("axis-breath", "nonpositive-length", (axis, str(length)))
        logger.debug("native_axis_breath exit obstruction=%r", result)
        return result
    nodes = tuple(nod(rez(f"{axis}:{idx}"), str(idx)) for idx in range(length + 1))
    contacts = tuple(tact(nodes[idx], nodes[idx + 1], f"{axis}-step") for idx in range(length))
    result = breath(*contacts)
    logger.debug("native_axis_breath exit result=%r", result)
    return result

def native_right_corner_row(leg_a: int, leg_b: int) -> NativeRightCornerRow:
    """Derive a finite right-corner Pythagorean row from two native leg breaths."""
    logger.debug("native_right_corner_row entry leg_a=%d leg_b=%d", leg_a, leg_b)
    first, second = native_axis_breath("x", int(leg_a)), native_axis_breath("y", int(leg_b))
    if not isinstance(first, Breath) or not isinstance(second, Breath):
        result = NativeRightCornerRow("THM-G001", (int(leg_a), int(leg_b)), 0, 0, 0, "blocked", "requires positive native Breath legs")
        logger.debug("native_right_corner_row exit blocked result=%r", result)
        return result
    lengths = (int(observe_native(first, "length")), int(observe_native(second, "length")))
    square_sum = lengths[0] * lengths[0] + lengths[1] * lengths[1]
    root = isqrt(square_sum)
    status = "derived" if root * root == square_sum else "blocked"
    boundary = "finite native Breath-length right-corner row; not a full geometry theorem"
    result = NativeRightCornerRow("THM-G001", lengths, root if status == "derived" else 0, square_sum, root * root, status, boundary)
    logger.debug("native_right_corner_row exit result=%r", result)
    return result

def native_geometry_derivation_rows() -> tuple[NativeRightCornerRow, ...]:
    """Return canonical finite native geometry derivation rows."""
    logger.debug("native_geometry_derivation_rows entry")
    result = (native_right_corner_row(3, 4), native_right_corner_row(5, 12), native_right_corner_row(8, 15))
    logger.debug("native_geometry_derivation_rows exit count=%d", len(result))
    return result

def native_geometry_derivation_summary() -> dict[str, int | bool]:
    """Return compact native geometry derivation counters."""
    logger.debug("native_geometry_derivation_summary entry")
    rows = native_geometry_derivation_rows()
    result: dict[str, int | bool] = {
        "rows": len(rows),
        "derived": sum(row.status == "derived" for row in rows),
        "finite_only": True,
    }
    logger.debug("native_geometry_derivation_summary exit result=%r", result)
    return result
