#!/usr/bin/env python3
"""Explore Veyra polynomial ratio forms with progress."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.polynomial import derivative_polynomial, eval_polynomial, multiply_polynomials, polynomial_from_ints  # noqa: E402
from src.core.ratio import ratio_from_ints, ratio_shadow  # noqa: E402

logger = logging.getLogger("veyra.explore_polynomials")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_coeffs(raw: str) -> list[int]:
    """Parse comma-separated integer coefficients."""
    logger.debug("parse_coeffs entry raw=%r", raw)
    result = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not result:
        logger.error("parse_coeffs empty raw=%r", raw)
        raise ValueError("at least one coefficient is required")
    logger.debug("parse_coeffs exit result=%r", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Explore polynomial ratio forms.")
    parser.add_argument("--left", default="1,1", help="left coefficients low-degree first")
    parser.add_argument("--right", default="-1,1", help="right coefficients low-degree first")
    parser.add_argument("--x", type=int, default=3, help="evaluation point")
    parser.add_argument("--verbose", action="store_true", help="debug logs")
    logger.debug("build_parser exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s:%(name)s:%(message)s"
    )
    logger.debug("main entry args=%r", args)
    try:
        stage(1, 3, "Building polynomials")
        left = polynomial_from_ints(parse_coeffs(args.left))
        right = polynomial_from_ints(parse_coeffs(args.right))
        print(f"left_degree={left.degree} right_degree={right.degree}")

        stage(2, 3, "Multiplying and differentiating")
        product = multiply_polynomials(left, right)
        derivative = derivative_polynomial(product)
        x = ratio_from_ints(args.x)
        print(f"product_coeffs={[str(ratio_shadow(c)) for c in product.coefficients]}")
        print(f"product({args.x})={ratio_shadow(eval_polynomial(product, x))}")
        print(f"derivative({args.x})={ratio_shadow(eval_polynomial(derivative, x))}")

        stage(3, 3, "Done")
        print("[done] errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
