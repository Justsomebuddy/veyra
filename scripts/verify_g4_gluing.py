#!/usr/bin/env python3
"""Exhaustively verify the finite G4 bridge with optional real Sage."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from veyra_sage.observer_patch_gluing import VeyraObserverPatchGluingLab  # noqa: E402

logger = logging.getLogger("veyra.verify_g4_gluing")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse bounded exhaustive-oracle arguments."""
    logger.debug("parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-nodes", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--require-sage", action="store_true")
    result = parser.parse_args(argv)
    logger.debug("parse_args exit max=%d sage=%s", result.max_nodes, result.require_sage)
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the independent oracle and print visible progress and exact totals."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    started = time.monotonic()
    print(f"[1/3] Preparing bounded oracle max_nodes={args.max_nodes} require_sage={args.require_sage}")
    lab = VeyraObserverPatchGluingLab()
    print("[2/3] Enumerating cover shapes, local partitions, and global witnesses")
    try:
        summary = lab.exhaustive_summary(args.max_nodes, require_sage=args.require_sage)
    except (RuntimeError, ValueError) as exc:
        logger.error("main verification failed error=%s", exc)
        elapsed = time.monotonic() - started
        print(f"[done] errors=1 elapsed={elapsed:.3f}s error={exc}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - started
    assignments = int(summary["assignments"])
    speed = assignments / elapsed if elapsed else float("inf")
    print(
        f"[3/3] Checking pinned counts and quotient classification processed={assignments}/{assignments} remaining=0 elapsed={elapsed:.3f}s eta=0s speed={speed:.1f}/s"
    )
    print(f"summary={summary}")
    ok = bool(summary["classification_passed"])
    print(f"[done] errors={0 if ok else 1} elapsed={elapsed:.3f}s assignments={assignments}")
    logger.debug("main exit ok=%s", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
