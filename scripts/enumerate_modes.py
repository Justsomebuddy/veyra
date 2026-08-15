#!/usr/bin/env python3
"""Enumerate tiny Veyra mode shadows with visible progress."""

from __future__ import annotations

import argparse
from collections import defaultdict
import logging
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.modes import (  # noqa: E402
    TEST_FAMILIES,
    Mode,
    echo_key,
    enumerate_modes,
    is_ordered_primitive,
    primitive_root,
)

logger = logging.getLogger("veyra.enumerate_modes")


def progress(iterable: Iterable[Mode], total: int, enabled: bool) -> Iterable[Mode]:
    """Wrap iterable in tqdm when enabled, with a simple fallback."""
    logger.debug("progress entry total=%d enabled=%s", total, enabled)
    if not enabled:
        logger.debug("progress exit passthrough")
        return iterable
    try:
        from tqdm import tqdm

        wrapped = tqdm(iterable, total=total, desc="[1/1] Classifying modes", unit="mode")
        logger.debug("progress exit tqdm")
        return wrapped
    except Exception:
        logger.exception("progress fallback because tqdm is unavailable")

        def fallback() -> Iterable[Mode]:
            done = 0
            for item in iterable:
                done += 1
                print(f"\r[1/1] Classifying modes {done}/{total}", end="", file=sys.stderr)
                yield item
            print(file=sys.stderr)

        logger.debug("progress exit fallback")
        return fallback()


def parse_alphabet(raw: str) -> tuple[str, ...]:
    """Parse alphabet string into unique tact symbols preserving order."""
    logger.debug("parse_alphabet entry raw=%r", raw)
    seen: list[str] = []
    for char in raw:
        if char not in seen:
            seen.append(char)
    if not seen:
        logger.error("parse_alphabet empty raw=%r", raw)
        raise ValueError("alphabet must contain at least one symbol")
    result = tuple(seen)
    logger.debug("parse_alphabet exit result=%r", result)
    return result


def classify_modes(modes: list[Mode], test_name: str, show_progress: bool) -> dict[tuple[object, ...], list[Mode]]:
    """Group modes by echo key under a named test family."""
    logger.debug("classify_modes entry count=%d test=%s show_progress=%s", len(modes), test_name, show_progress)
    tests = TEST_FAMILIES[test_name]
    groups: dict[tuple[object, ...], list[Mode]] = defaultdict(list)
    for mode in progress(modes, len(modes), show_progress):
        groups[echo_key(mode, tests)].append(mode)
    logger.debug("classify_modes exit groups=%d", len(groups))
    return dict(groups)


def render_summary(groups: dict[tuple[object, ...], list[Mode]], limit: int) -> str:
    """Render echo groups and primitive-root data as a compact table."""
    logger.debug("render_summary entry groups=%d limit=%d", len(groups), limit)
    lines = ["echo_key | modes | primitive_info"]
    for index, (key, members) in enumerate(sorted(groups.items(), key=lambda item: str(item[0]))):
        if index >= limit:
            lines.append(f"... {len(groups) - limit} more groups")
            break
        primitive_bits: list[str] = []
        for mode in members[:6]:
            if mode.length == 0:
                primitive_bits.append("ε:silent")
                continue
            root, exponent = primitive_root(mode)
            tag = "primitive" if is_ordered_primitive(mode) else f"{root.word}^{exponent}"
            primitive_bits.append(f"{mode.word}:{tag}")
        if len(members) > 6:
            primitive_bits.append("...")
        words = ", ".join(mode.word for mode in members[:8])
        if len(members) > 8:
            words += ", ..."
        lines.append(f"{key!r} | {words} | {', '.join(primitive_bits)}")
    result = "\n".join(lines)
    logger.debug("render_summary exit chars=%d", len(result))
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Enumerate Veyra mode shadows.")
    parser.add_argument("--alphabet", default="ab", help="tact alphabet as compact string, default: ab")
    parser.add_argument("--max-len", type=int, default=4, help="maximum tact-word length, default: 4")
    parser.add_argument("--test", choices=sorted(TEST_FAMILIES), default="ordered", help="echo test family")
    parser.add_argument("--limit", type=int, default=40, help="maximum echo groups to print")
    parser.add_argument("--no-progress", action="store_true", help="disable progress bar")
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
        alphabet = parse_alphabet(args.alphabet)
        modes = enumerate_modes(alphabet, args.max_len, include_silent=True)
        print(f"[setup] alphabet={alphabet} max_len={args.max_len} modes={len(modes)} test={args.test}")
        groups = classify_modes(modes, args.test, not args.no_progress)
        print(render_summary(groups, args.limit))
        print(f"[done] processed={len(modes)} groups={len(groups)} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] processed=0 groups=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
