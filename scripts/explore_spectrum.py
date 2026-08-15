#!/usr/bin/env python3
"""Explore Veyra resonance spectra with progress."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.modes import Mode  # noqa: E402
from src.core.spectrum import candidate_parts, resonance_spectrum  # noqa: E402

logger = logging.getLogger("veyra.explore_spectrum")


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
    parser = argparse.ArgumentParser(description="Explore resonance spectrum for a whole mode.")
    parser.add_argument("--whole", default="abac", help="whole mode word, default: abac")
    parser.add_argument("--alphabet", default="abc", help="candidate alphabet, default: abc")
    parser.add_argument("--max-part-len", type=int, default=2, help="max candidate part length, default: 2")
    parser.add_argument("--min-part-len", type=int, default=1, help="min candidate part length, default: 1")
    parser.add_argument("--max-defects", type=int, default=1, help="defect budget, default: 1")
    parser.add_argument("--limit", type=int, default=20, help="row limit, default: 20")
    parser.add_argument("--include-nonresonant", action="store_true", help="include non-resonating candidates")
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
        stage(1, 3, "Enumerating candidate parts")
        whole = Mode.from_word(args.whole)
        alphabet = parse_alphabet(args.alphabet)
        candidates = candidate_parts(alphabet, args.max_part_len, args.min_part_len)
        print(f"whole={whole.word} candidates={len(candidates)} max_defects={args.max_defects}")

        stage(2, 3, "Ranking resonance spectrum")
        spectrum = resonance_spectrum(whole, candidates, args.max_defects, include_nonresonant=args.include_nonresonant)
        for entry in spectrum[: args.limit]:
            best = entry.profile.best
            offset = None if best is None else best.offset
            defect_detail = () if best is None else tuple((d.index, d.expected, d.actual) for d in best.defects)
            print(
                f"part={entry.part.word} resonates={entry.profile.resonates} exact={entry.exact} "
                f"defects={entry.defect_count} offset={offset} obstruction={entry.profile.obstruction} "
                f"detail={defect_detail}"
            )

        stage(3, 3, "Done")
        print(f"[done] processed={len(candidates)} shown={min(len(spectrum), args.limit)} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] processed=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
