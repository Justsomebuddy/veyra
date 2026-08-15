#!/usr/bin/env python3
"""Explore Veyra linear equation constraints with progress."""

from __future__ import annotations

import argparse
from fractions import Fraction
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.equation import LinearEquation, LinearForm, equation_residual, solve_linear  # noqa: E402
from src.core.ratio import ratio_from_fraction, ratio_shadow  # noqa: E402

logger = logging.getLogger("veyra.explore_equations")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_ratio(raw: str):
    """Parse ratio text into RatioMode."""
    logger.debug("parse_ratio entry raw=%r", raw)
    result = ratio_from_fraction(Fraction(raw))
    logger.debug("parse_ratio exit result=%s", result.word)
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Solve left_a*x+left_b = right_a*x+right_b.")
    parser.add_argument("--left-a", default="2", help="left coefficient")
    parser.add_argument("--left-b", default="3", help="left offset")
    parser.add_argument("--right-a", default="0", help="right coefficient")
    parser.add_argument("--right-b", default="7", help="right offset")
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
        stage(1, 3, "Building linear equation")
        equation = LinearEquation(
            LinearForm(parse_ratio(args.left_a), parse_ratio(args.left_b)),
            LinearForm(parse_ratio(args.right_a), parse_ratio(args.right_b)),
        )
        print(f"equation=({args.left_a})x+({args.left_b}) = ({args.right_a})x+({args.right_b})")

        stage(2, 3, "Solving")
        solution = solve_linear(equation)
        print(f"status={solution.status} obstruction={solution.obstruction}")
        if solution.value is not None:
            residual = equation_residual(equation, solution.value)
            print(f"x={ratio_shadow(solution.value)} residual={ratio_shadow(residual)}")

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
