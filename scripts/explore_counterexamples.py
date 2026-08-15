#!/usr/bin/env python3
"""Explore first multi-tact Veyra counterexamples with progress output."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.counterexamples import (  # noqa: E402
    find_echo_splits,
    find_stitch_commutators,
    find_weave_incompatibilities,
)
from src.core.modes import Mode, TEST_FAMILIES, enumerate_modes  # noqa: E402

logger = logging.getLogger("veyra.explore_counterexamples")


def stage(message: str, index: int, total: int) -> None:
    """Print a visible stage marker."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_mapping(raw: str) -> dict[str, Mode]:
    """Parse substitution mapping like a:x,b:yy."""
    logger.debug("parse_mapping entry raw=%r", raw)
    mapping: dict[str, Mode] = {}
    if not raw.strip():
        logger.error("parse_mapping empty raw=%r", raw)
        raise ValueError("mapping must not be empty")
    for chunk in raw.split(","):
        key, sep, value = chunk.partition(":")
        if sep != ":" or not key:
            logger.error("parse_mapping bad chunk=%r", chunk)
            raise ValueError(f"bad mapping chunk: {chunk!r}")
        mapping[key] = Mode.from_word(value)
    logger.debug("parse_mapping exit keys=%r", sorted(mapping))
    return mapping


def parse_alphabet(raw: str) -> tuple[str, ...]:
    """Parse an alphabet string into unique tact symbols preserving order."""
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


def render_results(title: str, rows: list[object]) -> None:
    """Render dataclass counterexample rows."""
    logger.debug("render_results entry title=%s rows=%d", title, len(rows))
    print(f"\n## {title}")
    if not rows:
        print("none")
        logger.debug("render_results exit empty")
        return
    for item in rows:
        print(item)
    logger.debug("render_results exit")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Explore Veyra multi-tact counterexamples.")
    parser.add_argument("--alphabet", default="ab", help="driver tact alphabet, default: ab")
    parser.add_argument("--max-len", type=int, default=3, help="maximum driver length, default: 3")
    parser.add_argument("--limit", type=int, default=6, help="rows per category, default: 6")
    parser.add_argument("--mapping", default="a:x,b:yy", help="substitution map, e.g. a:x,b:yy")
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
        stage("Enumerating modes", 1, 4)
        alphabet = parse_alphabet(args.alphabet)
        modes = enumerate_modes(alphabet, args.max_len, include_silent=False)
        print(f"processed={len(modes)} alphabet={alphabet} max_len={args.max_len}")

        stage("Finding echo splits", 2, 4)
        splits = []
        for coarse, fine in [("length", "bag"), ("bag", "ordered"), ("cycle", "ordered")]:
            if coarse in TEST_FAMILIES and fine in TEST_FAMILIES:
                splits.extend(find_echo_splits(modes, coarse, fine, args.limit))
        render_results("echo splits", splits[: args.limit])

        stage("Finding stitch commutators", 3, 4)
        commutators = find_stitch_commutators(modes, "ordered", args.limit)
        render_results("ordered stitch commutators", commutators)

        stage("Finding weave incompatibilities", 4, 4)
        mapping = parse_mapping(args.mapping)
        incompat = find_weave_incompatibilities(modes, "length", "length", mapping, args.limit)
        render_results("length-driver weave incompatibilities", incompat)
        print(f"\n[done] processed={len(modes)} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] processed=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
