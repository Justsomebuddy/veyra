"""Structural division and product-plus-one recurrence proofs."""
from __future__ import annotations

import logging

from .intrinsic_arithmetic_types import (
    DivisionStep, EscapeWitness, ProductPlusOneObstructionProof,
    StructuralDivisionProof,
)
from .native_runtime import Breath, Mode, NativeObstruction, Nod, Tact, silent_breath, mode

logger = logging.getLogger(__name__)



def _primitives():
    logger.debug("_primitives entry")
    from . import intrinsic_arithmetic as api
    result = (api._default_anchor, api._validate, api.zero, api.one, api.stitch, api.successor, api.weave)
    logger.debug("_primitives exit")
    return result


def _default_anchor():
    logger.debug("division._default_anchor entry")
    result = _primitives()[0]()
    logger.debug("division._default_anchor exit result=%r", result)
    return result

def _validate(value, stage):
    logger.debug("division._validate entry stage=%s", stage)
    result = _primitives()[1](value, stage)
    logger.debug("division._validate exit result=%r", result)
    return result

def zero(anchor=None):
    logger.debug("division.zero entry anchor=%r", anchor)
    result = _primitives()[2](anchor)
    logger.debug("division.zero exit result=%r", result)
    return result

def one(anchor=None):
    logger.debug("division.one entry anchor=%r", anchor)
    result = _primitives()[3](anchor)
    logger.debug("division.one exit result=%r", result)
    return result

def stitch(left, right):
    logger.debug("division.stitch entry")
    result = _primitives()[4](left, right)
    logger.debug("division.stitch exit result=%r", result)
    return result

def successor(value):
    logger.debug("division.successor entry")
    result = _primitives()[5](value)
    logger.debug("division.successor exit result=%r", result)
    return result

def weave(left, right):
    logger.debug("division.weave entry")
    result = _primitives()[6](left, right)
    logger.debug("division.weave exit result=%r", result)
    return result


def _drop_prefix(candidate: tuple[Tact, ...], pattern: tuple[Tact, ...]) -> tuple[Tact, ...] | None:
    logger.debug("_drop_prefix entry candidate={!r} pattern={!r}".format(candidate, pattern))
    if not pattern:
        logger.debug("_drop_prefix exit result={!r}".format(candidate))
        return candidate
    if not candidate or candidate[0] != pattern[0]:
        logger.debug("_drop_prefix exit result=None")
        return None
    result = _drop_prefix(candidate[1:], pattern[1:])
    logger.debug("_drop_prefix exit result={!r}".format(result))
    return result


def _divide_steps(
    remaining: tuple[Tact, ...],
    divisor: tuple[Tact, ...],
    quotient: Mode,
    steps: tuple[DivisionStep, ...],
) -> tuple[Mode, tuple[Tact, ...], tuple[DivisionStep, ...]] | NativeObstruction:
    logger.debug(
        "_divide_steps entry remaining={!r} divisor={!r} quotient={!r} steps={!r}".format(
            remaining, divisor, quotient, steps
        )
    )
    suffix = _drop_prefix(remaining, divisor)
    if suffix is None:
        result = (quotient, remaining, steps)
        logger.debug("_divide_steps exit result={!r}".format(result))
        return result
    advanced = successor(quotient)
    if isinstance(advanced, NativeObstruction):
        logger.error("_divide_steps blocked result={!r}".format(advanced))
        return advanced
    step = DivisionStep(remaining, suffix)
    result = _divide_steps(suffix, divisor, advanced, steps + (step,))
    logger.debug("_divide_steps exit result={!r}".format(result))
    return result


def _residual_mode(items: tuple[Tact, ...], anchor: Nod) -> Mode | NativeObstruction:
    logger.debug("_residual_mode entry items={!r} anchor={!r}".format(items, anchor))
    source = Breath(items) if items else silent_breath(anchor)
    result = mode(source)
    logger.debug("_residual_mode exit result={!r}".format(result))
    return result


def structural_divide(dividend: Mode, divisor: Mode) -> StructuralDivisionProof:
    """Derive quotient and residue by repeated structural prefix removal."""
    logger.debug("structural_divide entry dividend={!r} divisor={!r}".format(dividend, divisor))
    dividend_anchor = _validate(dividend, "structural-division")
    divisor_anchor = _validate(divisor, "structural-division")
    fallback_anchor = dividend_anchor if isinstance(dividend_anchor, Nod) else _default_anchor()
    silent = zero(fallback_anchor)
    if isinstance(dividend_anchor, NativeObstruction):
        result = StructuralDivisionProof(
            dividend, divisor, silent, dividend, dividend_anchor, (), "blocked", False, dividend_anchor
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    if isinstance(divisor_anchor, NativeObstruction):
        result = StructuralDivisionProof(
            dividend, divisor, silent, dividend, divisor_anchor, (), "blocked", False, divisor_anchor
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    if dividend_anchor != divisor_anchor:
        obstruction = NativeObstruction(
            "structural-division", "anchor-mismatch", (dividend_anchor.mark, divisor_anchor.mark)
        )
        result = StructuralDivisionProof(
            dividend, divisor, silent, dividend, obstruction, (), "blocked", False, obstruction
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    if not divisor.breath.tacts:
        obstruction = NativeObstruction("structural-division", "zero-divisor", (divisor_anchor.mark,))
        result = StructuralDivisionProof(
            dividend, divisor, silent, dividend, obstruction, (), "blocked", False, obstruction
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    divided = _divide_steps(dividend.breath.tacts, divisor.breath.tacts, silent, ())
    if isinstance(divided, NativeObstruction):
        result = StructuralDivisionProof(
            dividend, divisor, silent, dividend, divided, (), "blocked", False, divided
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    quotient, residual_items, steps = divided
    residual = _residual_mode(residual_items, dividend_anchor)
    if isinstance(residual, NativeObstruction):
        result = StructuralDivisionProof(
            dividend, divisor, quotient, dividend, residual, steps, "blocked", False, residual
        )
        logger.error("structural_divide blocked result={!r}".format(result))
        return result
    woven = weave(divisor, quotient)
    reconstructed = woven if isinstance(woven, NativeObstruction) else stitch(woven, residual)
    reconstructs = isinstance(reconstructed, Mode) and reconstructed.breath == dividend.breath
    status = "exact" if not residual.breath.tacts else "residual"
    result = StructuralDivisionProof(
        dividend,
        divisor,
        quotient,
        residual,
        reconstructed,
        steps,
        status,
        reconstructs,
    )
    logger.debug("structural_divide exit result={!r}".format(result))
    return result


def _product_steps(factors: tuple[Mode, ...], accumulator: Mode) -> Mode | NativeObstruction:
    logger.debug("_product_steps entry factors={!r} accumulator={!r}".format(factors, accumulator))
    if not factors:
        logger.debug("_product_steps exit result={!r}".format(accumulator))
        return accumulator
    advanced = weave(accumulator, factors[0])
    if isinstance(advanced, NativeObstruction):
        logger.error("_product_steps blocked result={!r}".format(advanced))
        return advanced
    result = _product_steps(factors[1:], advanced)
    logger.debug("_product_steps exit result={!r}".format(result))
    return result


def _escape_witnesses(
    candidate: Mode,
    factors: tuple[Mode, ...],
    unit: Mode,
) -> tuple[EscapeWitness, ...]:
    logger.debug("_escape_witnesses entry candidate={!r} factors={!r} unit={!r}".format(candidate, factors, unit))
    if not factors:
        logger.debug("_escape_witnesses exit result=()")
        return ()
    division = structural_divide(candidate, factors[0])
    unit_residual = division.residual.breath == unit.breath
    witness = EscapeWitness(
        factors[0],
        division,
        unit_residual,
        division.status == "residual" and division.reconstructs and unit_residual,
    )
    result = (witness,) + _escape_witnesses(candidate, factors[1:], unit)
    logger.debug("_escape_witnesses exit result={!r}".format(result))
    return result


def _all_escape(witnesses: tuple[EscapeWitness, ...]) -> bool:
    logger.debug("_all_escape entry witnesses={!r}".format(witnesses))
    if not witnesses:
        logger.debug("_all_escape exit result=True")
        return True
    result = witnesses[0].blocks_resonance and _all_escape(witnesses[1:])
    logger.debug("_all_escape exit result={}".format(result))
    return result


def product_plus_one_obstruction(*factors: Mode) -> ProductPlusOneObstructionProof:
    """Prove structurally that a product successor escapes every non-unit factor."""
    logger.debug("product_plus_one_obstruction entry factors={!r}".format(factors))
    anchor_result = _validate(factors[0], "product-plus-one") if factors else _default_anchor()
    anchor = anchor_result if isinstance(anchor_result, Nod) else _default_anchor()
    unit = one(anchor)
    if not factors:
        candidate = successor(unit)
        if isinstance(candidate, NativeObstruction):
            raise RuntimeError(candidate.reason)
        obstruction = NativeObstruction("product-plus-one", "missing-factors", ())
        result = ProductPlusOneObstructionProof((), unit, candidate, (), False, "blocked", obstruction)
        logger.error("product_plus_one_obstruction blocked result={!r}".format(result))
        return result
    product = _product_steps(factors, unit)
    if isinstance(product, NativeObstruction):
        obstruction = product
        result = ProductPlusOneObstructionProof(
            factors, unit, unit, (), False, "blocked", obstruction
        )
        logger.error("product_plus_one_obstruction blocked result={!r}".format(result))
        return result
    candidate = successor(product)
    if isinstance(candidate, NativeObstruction):
        result = ProductPlusOneObstructionProof(
            factors, product, product, (), False, "blocked", candidate
        )
        logger.error("product_plus_one_obstruction blocked result={!r}".format(result))
        return result
    witnesses = _escape_witnesses(candidate, factors, unit)
    escaped = _all_escape(witnesses)
    obstruction = None if escaped else NativeObstruction(
        "product-plus-one", "factor-does-not-yield-unit-residue", ()
    )
    result = ProductPlusOneObstructionProof(
        factors,
        product,
        candidate,
        witnesses,
        escaped,
        "witnessed" if escaped else "blocked",
        obstruction,
    )
    logger.debug("product_plus_one_obstruction exit result={!r}".format(result))
    return result
