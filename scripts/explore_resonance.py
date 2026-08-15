#!/usr/bin/env python3
"""Explore ordered vs cyclic/phase resonance with progress."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.modes import Mode, enumerate_modes  # noqa: E402
from src.core.resonance import resonance_profile  # noqa: E402

logger = logging.getLogger("veyra.explore_resonance")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_alphabet(raw: str) -> tuple[str, ...]:
    """Parse unique alphabet preserving order."""
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


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Explore Veyra phase resonance.")
    parser.add_argument("--alphabet", default="ab", help="mode alphabet, default: ab")
    parser.add_argument("--part", default="ab", help="part mode, default: ab")
    parser.add_argument("--max-len", type=int, default=4, help="maximum whole length, default: 4")
    parser.add_argument("--limit", type=int, default=20, help="row limit, default: 20")
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
        stage(1, 3, "Enumerating candidate wholes")
        alphabet = parse_alphabet(args.alphabet)
        part = Mode.from_word(args.part)
        wholes = enumerate_modes(alphabet, args.max_len, include_silent=False)
        print(f"part={part.word} candidates={len(wholes)} alphabet={alphabet} max_len={args.max_len}")

        stage(2, 3, "Profiling resonance")
        shown = 0
        for whole in wholes:
            profile = resonance_profile(part, whole)
            if profile.cyclic or profile.ordered or profile.obstruction != "length-obstruction":
                print(
                    f"whole={whole.word} ordered={profile.ordered} cyclic={profile.cyclic} "
                    f"offsets={profile.phase_offsets} obstruction={profile.obstruction}"
                )
                shown += 1
                if shown >= args.limit:
                    break

        stage(3, 3, "Done")
        print(f"[done] processed={len(wholes)} shown={shown} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] processed=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
