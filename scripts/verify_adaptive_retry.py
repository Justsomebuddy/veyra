#!/usr/bin/env python3
"""Verify adaptive-retry inflation with an optional independent real-Sage lane."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from veyra_sage.adaptive_research_line import VeyraAdaptiveResearchLineLab  # noqa: E402

logger = logging.getLogger("veyra.verify_adaptive_retry")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse exact bounded adaptive-retry arguments."""
    logger.debug("parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempts", type=int, default=20)
    parser.add_argument("--alpha-numerator", type=int, default=1)
    parser.add_argument("--alpha-denominator", type=int, default=20)
    parser.add_argument("--require-sage", action="store_true")
    result = parser.parse_args(argv)
    logger.debug("parse_args exit attempts=%d sage=%s", result.attempts, result.require_sage)
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the oracle with visible bounded progress and exact output."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    started = time.monotonic()
    print(
        f"[1/3] Preparing adaptive-retry oracle attempts={args.attempts} "
        f"alpha={args.alpha_numerator}/{args.alpha_denominator} require_sage={args.require_sage}"
    )
    print("[2/3] Computing exact complement and binomial-sum identities")
    try:
        summary = VeyraAdaptiveResearchLineLab().retry_summary(
            args.attempts,
            args.alpha_numerator,
            args.alpha_denominator,
            require_sage=args.require_sage,
        )
    except (RuntimeError, ValueError) as exc:
        logger.error("main verification failed error=%s", exc)
        elapsed = time.monotonic() - started
        print(f"[done] errors=1 elapsed={elapsed:.3f}s error={exc}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - started
    row = summary["row"]
    print(
        f"[3/3] Checking noncomposition boundary processed={args.attempts}/{args.attempts} "
        f"remaining=0 elapsed={elapsed:.3f}s eta=0s"
    )
    print(f"summary={summary}")
    any_numerator, any_denominator = row["any_positive"]
    alpha_numerator, alpha_denominator = row["alpha"]
    inflated = (
        any_numerator * alpha_denominator == alpha_numerator * any_denominator
        if args.attempts == 1
        else any_numerator * alpha_denominator > alpha_numerator * any_denominator
    )
    sage_ok = not args.require_sage or bool(row["sage_crosscheck_passed"])
    ok = (
        not bool(summary["local_validity_composes"])
        and summary["adaptive_validity"] == "NOT_ESTABLISHED"
        and 0 < any_numerator < any_denominator
        and inflated
        and sage_ok
    )
    print(f"[done] errors={0 if ok else 1} elapsed={elapsed:.3f}s attempts={args.attempts}")
    logger.debug("main exit ok=%s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
