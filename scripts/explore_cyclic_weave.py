#!/usr/bin/env python3
"""Compare ordered and cyclic Veyra weave schemas with progress."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.compatibility import unary_compatibility_failures, unary_respects  # noqa: E402
from src.core.modes import Mode, enumerate_modes  # noqa: E402
from src.core.weave import cyclic_weave, ordered_weave  # noqa: E402

logger = logging.getLogger("veyra.explore_cyclic_weave")


def stage(index: int, total: int, message: str) -> None:
    """Print a visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def parse_alphabet(raw: str) -> tuple[str, ...]:
    """Parse unique alphabet symbols preserving order."""
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


def parse_mapping(raw: str) -> dict[str, Mode]:
    """Parse mapping like a:x,b:yy."""
    logger.debug("parse_mapping entry raw=%r", raw)
    mapping: dict[str, Mode] = {}
    for chunk in raw.split(","):
        key, sep, value = chunk.partition(":")
        if sep != ":" or not key:
            logger.error("parse_mapping bad chunk=%r", chunk)
            raise ValueError(f"bad mapping chunk: {chunk!r}")
        mapping[key] = Mode.from_word(value)
    logger.debug("parse_mapping exit keys=%r", sorted(mapping))
    return mapping


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Explore ordered vs cyclic weave.")
    parser.add_argument("--alphabet", default="ab", help="driver alphabet, default: ab")
    parser.add_argument("--max-len", type=int, default=3, help="maximum mode length, default: 3")
    parser.add_argument("--mapping", default="a:x,b:yy", help="substitution map, default: a:x,b:yy")
    parser.add_argument("--limit", type=int, default=10, help="row limit, default: 10")
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
        stage(1, 4, "Enumerating closed word shadows")
        alphabet = parse_alphabet(args.alphabet)
        modes = enumerate_modes(alphabet, args.max_len, include_silent=False)
        mapping = parse_mapping(args.mapping)
        print(f"processed={len(modes)} alphabet={alphabet} max_len={args.max_len}")

        stage(2, 4, "Comparing ordered and cyclic weave outputs")
        for mode in modes[: args.limit]:
            ordered = ordered_weave(mode, mapping)
            cyclic = cyclic_weave(mode, mapping)
            print(f"{mode.word}: ordered={ordered.word} cyclic={cyclic.word}")

        stage(3, 4, "Checking compatibility claims")
        ordered_schema = lambda mode: ordered_weave(mode, mapping)
        cyclic_schema = lambda mode: cyclic_weave(mode, mapping)
        print(
            "ordered respects (T_cycle,T_cycle):",
            unary_respects(modes, ordered_schema, "cycle", "cycle", "ordered_weave"),
        )
        print(
            "ordered respects (T_cycle,T_word):",
            unary_respects(modes, ordered_schema, "cycle", "ordered", "ordered_weave"),
        )
        print(
            "cyclic respects (T_cycle,T_word):",
            unary_respects(modes, cyclic_schema, "cycle", "ordered", "cyclic_weave"),
        )
        failures = unary_compatibility_failures(modes, ordered_schema, "cycle", "ordered", "ordered_weave", args.limit)
        for failure in failures:
            print("ordered failure:", failure)

        stage(4, 4, "Done")
        print(f"[done] processed={len(modes)} ordered_failures={len(failures)} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] processed=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
