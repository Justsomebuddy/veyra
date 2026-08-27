"""Structural arithmetic carried only by native Veyra recurrences."""
from __future__ import annotations

import logging

from .intrinsic_arithmetic_division import product_plus_one_obstruction, structural_divide
from .intrinsic_arithmetic_types import (
    DivisionStep as DivisionStep,
    EscapeWitness as EscapeWitness,
    ProductPlusOneObstructionProof as ProductPlusOneObstructionProof,
    StructuralDivisionProof as StructuralDivisionProof,
)
from .native_runtime import (
    Breath,
    Mode,
    NativeObstruction,
    Nod,
    Tact,
    breath_boundary,
    mode,
    nod,
    rez,
    silent_breath,
    stitch as stitch_breaths,
    tact,
)


logger = logging.getLogger(__name__)

_ORIGIN_NAME = "intrinsic-origin"
_SUCCESSOR_MARK = "intrinsic-successor"


def _default_anchor() -> Nod:
    logger.debug("_default_anchor entry")
    result = nod(rez(_ORIGIN_NAME), _ORIGIN_NAME)
    logger.debug("_default_anchor exit result={!r}".format(result))
    return result


def _mode_anchor(value: Mode, stage: str) -> Nod | NativeObstruction:
    logger.debug("_mode_anchor entry value={!r} stage={}".format(value, stage))
    boundary = breath_boundary(value.breath)
    if boundary is None:
        result = NativeObstruction(stage, "unanchored-recurrence", ())
        logger.error("_mode_anchor blocked result={!r}".format(result))
        return result
    if boundary[0] != boundary[1]:
        result = NativeObstruction(stage, "open-recurrence", (boundary[0].mark, boundary[1].mark))
        logger.error("_mode_anchor blocked result={!r}".format(result))
        return result
    result = boundary[0]
    logger.debug("_mode_anchor exit result={!r}".format(result))
    return result


def _tacts_are_intrinsic(items: tuple[Tact, ...], anchor: Nod) -> bool:
    logger.debug("_tacts_are_intrinsic entry anchor={!r}".format(anchor))
    for item in items:
        if item.start != anchor or item.end != anchor or item.mark != _SUCCESSOR_MARK:
            logger.debug("_tacts_are_intrinsic exit result=False item={!r}".format(item))
            return False
    logger.debug("_tacts_are_intrinsic exit result=True")
    return True


def _validate(value: Mode, stage: str) -> Nod | NativeObstruction:
    logger.debug("_validate entry value={!r} stage={}".format(value, stage))
    anchor = _mode_anchor(value, stage)
    if isinstance(anchor, NativeObstruction):
        logger.error("_validate blocked result={!r}".format(anchor))
        return anchor
    if not _tacts_are_intrinsic(value.breath.tacts, anchor):
        result = NativeObstruction(stage, "foreign-recurrence", (anchor.mark,))
        logger.error("_validate blocked result={!r}".format(result))
        return result
    logger.debug("_validate exit anchor={!r}".format(anchor))
    return anchor


def zero(anchor: Nod | None = None) -> Mode:
    """Return an anchored silent recurrence."""
    logger.debug("zero entry anchor={!r}".format(anchor))
    origin = anchor if anchor is not None else _default_anchor()
    wrapped = mode(silent_breath(origin))
    if isinstance(wrapped, NativeObstruction):
        logger.error("zero invariant failure result={!r}".format(wrapped))
        raise RuntimeError(wrapped.reason)
    logger.debug("zero exit result={!r}".format(wrapped))
    return wrapped


def one(anchor: Nod | None = None) -> Mode:
    """Return one self-closing recurrence tact."""
    logger.debug("one entry anchor={!r}".format(anchor))
    origin = anchor if anchor is not None else _default_anchor()
    wrapped = mode(Breath((tact(origin, origin, _SUCCESSOR_MARK),)))
    if isinstance(wrapped, NativeObstruction):
        logger.error("one invariant failure result={!r}".format(wrapped))
        raise RuntimeError(wrapped.reason)
    logger.debug("one exit result={!r}".format(wrapped))
    return wrapped


def stitch(left: Mode, right: Mode) -> Mode | NativeObstruction:
    """Join two intrinsic recurrences at their common anchor."""
    logger.debug("stitch entry left={!r} right={!r}".format(left, right))
    left_anchor = _validate(left, "intrinsic-stitch")
    if isinstance(left_anchor, NativeObstruction):
        logger.error("stitch blocked result={!r}".format(left_anchor))
        return left_anchor
    right_anchor = _validate(right, "intrinsic-stitch")
    if isinstance(right_anchor, NativeObstruction):
        logger.error("stitch blocked result={!r}".format(right_anchor))
        return right_anchor
    if left_anchor != right_anchor:
        result = NativeObstruction("intrinsic-stitch", "anchor-mismatch", (left_anchor.mark, right_anchor.mark))
        logger.error("stitch blocked result={!r}".format(result))
        return result
    joined = stitch_breaths(left.breath, right.breath)
    if isinstance(joined, NativeObstruction):
        logger.error("stitch blocked result={!r}".format(joined))
        return joined
    wrapped = mode(joined)
    logger.debug("stitch exit result={!r}".format(wrapped))
    return wrapped


def successor(value: Mode) -> Mode | NativeObstruction:
    """Append one self-closing recurrence tact."""
    logger.debug("successor entry value={!r}".format(value))
    anchor = _validate(value, "intrinsic-successor")
    if isinstance(anchor, NativeObstruction):
        logger.error("successor blocked result={!r}".format(anchor))
        return anchor
    result = stitch(value, one(anchor))
    logger.debug("successor exit result={!r}".format(result))
    return result


def weave(left: Mode, right: Mode) -> Mode | NativeObstruction:
    """Repeat the left recurrence once for every tact carried by the right."""
    logger.debug("weave entry left={!r} right={!r}".format(left, right))
    left_anchor = _validate(left, "intrinsic-weave")
    if isinstance(left_anchor, NativeObstruction):
        logger.error("weave blocked result={!r}".format(left_anchor))
        return left_anchor
    right_anchor = _validate(right, "intrinsic-weave")
    if isinstance(right_anchor, NativeObstruction):
        logger.error("weave blocked result={!r}".format(right_anchor))
        return right_anchor
    if left_anchor != right_anchor:
        result = NativeObstruction("intrinsic-weave", "anchor-mismatch", (left_anchor.mark, right_anchor.mark))
        logger.error("weave blocked result={!r}".format(result))
        return result
    result_tacts: list[Tact] = []
    for _ in right.breath.tacts:
        result_tacts.extend(left.breath.tacts)
    source = Breath(tuple(result_tacts), left_anchor if not result_tacts else None)
    result = mode(source)
    if isinstance(result, NativeObstruction):
        logger.error("weave invariant failure result={!r}".format(result))
        return result
    logger.debug("weave exit result={!r}".format(result))
    return result


def mode_power(base: Mode, exponent: Mode) -> Mode | NativeObstruction:
    """Raise a recurrence by structurally iterating over the exponent recurrence."""
    logger.debug("mode_power entry base={!r} exponent={!r}".format(base, exponent))
    base_anchor = _validate(base, "intrinsic-power")
    if isinstance(base_anchor, NativeObstruction):
        logger.error("mode_power blocked result={!r}".format(base_anchor))
        return base_anchor
    exponent_anchor = _validate(exponent, "intrinsic-power")
    if isinstance(exponent_anchor, NativeObstruction):
        logger.error("mode_power blocked result={!r}".format(exponent_anchor))
        return exponent_anchor
    if base_anchor != exponent_anchor:
        result = NativeObstruction("intrinsic-power", "anchor-mismatch", (base_anchor.mark, exponent_anchor.mark))
        logger.error("mode_power blocked result={!r}".format(result))
        return result
    result: Mode | NativeObstruction = one(base_anchor)
    for _ in exponent.breath.tacts:
        result = weave(result, base)
        if isinstance(result, NativeObstruction):
            logger.error("mode_power blocked result={!r}".format(result))
            return result
    logger.debug("mode_power exit result={!r}".format(result))
    return result



def intrinsic_arithmetic_summary() -> dict[str, object]:
    """Return structural arithmetic readiness without school-number observers."""
    logger.debug("intrinsic_arithmetic_summary entry")
    unit = one()
    two = successor(unit)
    if isinstance(two, NativeObstruction):
        logger.error("intrinsic_arithmetic_summary blocked two={!r}".format(two))
        return {"status": "blocked", "division": False, "escape": False}
    three = successor(two)
    if isinstance(three, NativeObstruction):
        logger.error("intrinsic_arithmetic_summary blocked three={!r}".format(three))
        return {"status": "blocked", "division": False, "escape": False}
    product = weave(two, three)
    division = structural_divide(product, two) if isinstance(product, Mode) else None
    escape = product_plus_one_obstruction(two, three)
    result: dict[str, object] = {
        "status": "witnessed" if division and division.reconstructs and escape.escaped else "blocked",
        "division": bool(division and division.reconstructs), "escape": escape.escaped,
    }
    logger.debug("intrinsic_arithmetic_summary exit result={!r}".format(result))
    return result

zero_mode = zero
one_mode = one
stitch_modes = stitch
power = mode_power
structural_division = structural_divide
product_plus_one_escape = product_plus_one_obstruction
