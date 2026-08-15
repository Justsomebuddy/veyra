#!/usr/bin/env python3
"""Explore Veyra balance and ratio arithmetic with progress."""

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
from src.core.balance import balance_from_int, canonical_length_balance, stitch_balance, subtract_balance  # noqa: E402
from src.core.order import RatioInterval, compare_balances, compare_ratios, interval_contains  # noqa: E402
from src.core.ratio import (
    add_ratios,
    inverse_ratio,
    multiply_ratios,
    ratio_from_fraction,
    ratio_shadow,
    subtract_ratios,
)  # noqa: E402

logger = logging.getLogger("veyra.explore_arithmetic")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_fraction(raw: str) -> Fraction:
    """Parse an integer or fraction string."""
    logger.debug("parse_fraction entry raw=%r", raw)
    result = Fraction(raw)
    logger.debug("parse_fraction exit result=%s", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Explore Veyra arithmetic shadows.")
    parser.add_argument("--left", type=int, default=3, help="left balance integer")
    parser.add_argument("--right", type=int, default=-2, help="right balance integer")
    parser.add_argument("--ratio-left", default="1/2", help="left ratio")
    parser.add_argument("--ratio-right", default="1/3", help="right ratio")
    parser.add_argument("--verbose", action="store_true", help="enable debug logs")
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
        stage(1, 4, "Building balance modes")
        left = balance_from_int(args.left)
        right = balance_from_int(args.right)
        print(f"left={left.word} net={left.net_length}")
        print(f"right={right.word} net={right.net_length}")
        print(f"sum={canonical_length_balance(stitch_balance(left, right)).word}")
        print(f"diff={canonical_length_balance(subtract_balance(left, right)).word}")

        stage(2, 4, "Building ratio modes")
        ratio_left = ratio_from_fraction(parse_fraction(args.ratio_left))
        ratio_right = ratio_from_fraction(parse_fraction(args.ratio_right))
        print(f"ratio_left={ratio_left.word} shadow={ratio_shadow(ratio_left)}")
        print(f"ratio_right={ratio_right.word} shadow={ratio_shadow(ratio_right)}")
        print(f"ratio_sum={ratio_shadow(add_ratios(ratio_left, ratio_right))}")
        print(f"ratio_diff={ratio_shadow(subtract_ratios(ratio_left, ratio_right))}")
        print(f"ratio_product={ratio_shadow(multiply_ratios(ratio_left, ratio_right))}")
        print(f"ratio_inverse_left={ratio_shadow(inverse_ratio(ratio_left))}")

        stage(3, 4, "Comparing arithmetic shadows")
        print(f"balance_compare={compare_balances(left, right).relation}")
        print(f"ratio_compare={compare_ratios(ratio_left, ratio_right).relation}")
        interval = RatioInterval(ratio_right, ratio_left)
        print(f"ratio_right_in_[right,left]={interval_contains(interval, ratio_right)}")

        stage(4, 4, "Done")
        print("[done] errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
