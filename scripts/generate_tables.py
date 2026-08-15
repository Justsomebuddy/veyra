#!/usr/bin/env python3
"""Generate reproducible Veyra processed tables with progress."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import _project_bootstrap  # noqa: F401
from src.core.compression import CompressionWeights  # noqa: E402
from src.core.modes import Mode  # noqa: E402
from src.core.tables import (  # noqa: E402
    approx_resonance_rows,
    compression_rows,
    counterexample_data,
    cyclic_weave_rows,
    language_coverage_rows,
    phase_resonance_rows,
    prime_variant_rows,
    spectrum_rows,
    span_diagnostic_rows,
    weighted_resonance_rows,
    write_csv,
    write_json,
    write_manifest,
)
from src.core.tact_similarity import aura_cost_map, tact_aura_cost_rows  # noqa: E402
from src.core.weighted_resonance import CostMap  # noqa: E402

logger = logging.getLogger("veyra.generate_tables")


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


def parse_costs(raw: str) -> CostMap:
    """Parse directed weighted costs like b>c:0.25,a>c:2."""
    logger.debug("parse_costs entry raw=%r", raw)
    costs: CostMap = {}
    if not raw.strip():
        logger.debug("parse_costs exit empty")
        return costs
    for chunk in raw.split(","):
        pair, sep, value = chunk.partition(":")
        left, arrow, right = pair.partition(">")
        if sep != ":" or arrow != ">" or not left or not right:
            logger.error("parse_costs bad chunk=%r", chunk)
            raise ValueError(f"bad cost chunk: {chunk!r}")
        costs[(left, right)] = float(value)
    logger.debug("parse_costs exit costs=%r", costs)
    return costs


def resolve_weighted_costs(
    raw: str, whole: Mode, alphabet: tuple[str, ...], radius: int, min_mismatch_cost: float, default_cost: float
) -> tuple[CostMap, str]:
    """Use manual weighted costs or derive them from tact auras."""
    logger.debug("resolve_weighted_costs entry raw=%r whole=%s", raw, whole.word)
    manual = parse_costs(raw)
    if manual:
        logger.debug("resolve_weighted_costs exit source=manual count=%d", len(manual))
        return manual, "manual"
    result = aura_cost_map([whole], alphabet, radius, min_mismatch_cost, default_cost)
    logger.debug("resolve_weighted_costs exit source=aura count=%d", len(result))
    return result, "aura"


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    logger.debug("build_parser entry")
    parser = argparse.ArgumentParser(description="Generate Veyra processed tables.")
    parser.add_argument("--out-dir", default="data/processed", help="output directory")
    parser.add_argument("--whole", default="abac", help="whole mode word")
    parser.add_argument("--alphabet", default="abc", help="alphabet for candidates")
    parser.add_argument("--max-part-len", type=int, default=2, help="max candidate part length")
    parser.add_argument("--min-part-len", type=int, default=1, help="min candidate part length")
    parser.add_argument("--max-mode-len", type=int, default=4, help="max mode length for prime/counterexample tables")
    parser.add_argument("--max-defects", type=int, default=1, help="defect budget")
    parser.add_argument("--defect-weight", type=float, default=2.0, help="defect cost")
    parser.add_argument("--phase-weight", type=float, default=0.25, help="phase cost")
    parser.add_argument("--weighted-budget", type=float, default=0.5, help="weighted resonance budget")
    parser.add_argument(
        "--weighted-costs", default="", help="manual directed costs; empty derives costs from tact auras"
    )
    parser.add_argument("--default-cost", type=float, default=1.0, help="default weighted mismatch cost")
    parser.add_argument("--aura-radius", type=int, default=1, help="radius for derived tact auras")
    parser.add_argument("--min-mismatch-cost", type=float, default=0.25, help="minimum nonzero derived mismatch cost")
    parser.add_argument("--limit", type=int, default=20, help="counterexample limit")
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
        out_dir = Path(args.out_dir)
        alphabet = parse_alphabet(args.alphabet)
        whole = Mode.from_word(args.whole)
        weights = CompressionWeights(args.defect_weight, args.phase_weight)
        costs, cost_source = resolve_weighted_costs(
            args.weighted_costs, whole, alphabet, args.aura_radius, args.min_mismatch_cost, args.default_cost
        )
        artifacts = []

        stage(1, 12, "Writing spectrum table")
        rows = spectrum_rows(whole, alphabet, args.max_part_len, args.min_part_len, args.max_defects)
        artifacts.append(
            write_csv(
                out_dir / f"spectrum_{whole.word}.csv",
                rows,
                ["part", "resonates", "exact", "defects", "offset", "obstruction"],
            )
        )

        stage(2, 12, "Writing compression table")
        rows = compression_rows(whole, alphabet, args.max_part_len, args.min_part_len, args.max_defects, weights)
        artifacts.append(
            write_csv(
                out_dir / f"compression_{whole.word}.csv",
                rows,
                ["part", "cost", "saving", "ratio", "defects", "offset", "obstruction"],
            )
        )

        stage(3, 12, "Writing prime variant table")
        rows = prime_variant_rows(alphabet, args.max_mode_len, tact=alphabet[0])
        artifacts.append(
            write_csv(
                out_dir / f"prime_variants_len{args.max_mode_len}.csv",
                rows,
                ["mode", "length", "numeric_prime", "ordered_primitive", "cyclic_primitive", "ordered_resonance_prime"],
            )
        )

        stage(4, 12, "Writing phase resonance table")
        part = Mode.from_word(alphabet[0] + alphabet[1] if len(alphabet) > 1 else alphabet[0])
        rows = phase_resonance_rows(part, alphabet, args.max_mode_len)
        artifacts.append(
            write_csv(
                out_dir / f"phase_resonance_{part.word}_len{args.max_mode_len}.csv",
                rows,
                ["part", "whole", "ordered", "cyclic", "offsets", "obstruction"],
            )
        )

        stage(5, 12, "Writing approximate resonance table")
        rows = approx_resonance_rows(part, alphabet, args.max_mode_len, args.max_defects)
        artifacts.append(
            write_csv(
                out_dir / f"approx_resonance_{part.word}_len{args.max_mode_len}.csv",
                rows,
                ["part", "whole", "resonates", "obstruction", "best_offset", "defects", "defect_detail"],
            )
        )

        stage(6, 12, "Writing tact aura cost table")
        rows = tact_aura_cost_rows([whole], alphabet, args.aura_radius, args.min_mismatch_cost, args.default_cost)
        artifacts.append(
            write_csv(
                out_dir / f"tact_aura_costs_{whole.word}.csv",
                rows,
                ["expected", "actual", "similarity", "cost", "expected_aura", "actual_aura"],
            )
        )

        stage(7, 12, "Writing weighted resonance table")
        rows = weighted_resonance_rows(
            part, alphabet, args.max_mode_len, args.weighted_budget, costs, args.default_cost
        )
        artifacts.append(
            write_csv(
                out_dir / f"weighted_resonance_{part.word}_len{args.max_mode_len}.csv",
                rows,
                ["part", "whole", "resonates", "obstruction", "best_offset", "total_cost", "defects", "defect_detail"],
            )
        )

        stage(8, 12, "Writing cyclic weave table")
        mapping = {alphabet[0]: Mode.from_word("x")}
        if len(alphabet) > 1:
            mapping[alphabet[1]] = Mode.from_word("yy")
        rows = cyclic_weave_rows(alphabet, args.max_mode_len, mapping)
        artifacts.append(
            write_csv(
                out_dir / f"cyclic_weave_len{args.max_mode_len}.csv",
                rows,
                ["driver", "cyclic_driver", "ordered_output", "cyclic_output", "same_word"],
            )
        )

        stage(9, 12, "Writing Core Language coverage table")
        rows = language_coverage_rows()
        artifacts.append(
            write_csv(
                out_dir / "core_language_coverage_matrix.csv",
                rows,
                ["family", "cases", "blocked", "unknown", "ready", "unexpected", "covered"],
            )
        )

        stage(10, 12, "Writing Core Language span diagnostic table")
        rows = span_diagnostic_rows()
        artifacts.append(
            write_csv(
                out_dir / "core_language_span_diagnostics.csv",
                rows,
                ["name", "source", "ok", "expected", "found", "message", "line", "column", "has_excerpt", "multiline"],
            )
        )

        stage(11, 12, "Writing counterexample JSON")
        data = counterexample_data(alphabet, args.max_mode_len, args.limit)
        row_count = sum(len(value) for value in data.values())
        artifacts.append(write_json(out_dir / f"counterexamples_len{args.max_mode_len}.json", data, row_count))

        stage(12, 12, "Writing manifest")
        params = vars(args) | {"alphabet": "".join(alphabet), "weighted_cost_source": cost_source}
        artifacts.append(write_manifest(out_dir / "manifest.json", params, artifacts))
        for artifact in artifacts:
            print(f"artifact={artifact.path} rows={artifact.rows}")
        print(f"[done] artifacts={len(artifacts)} errors=0")
        logger.debug("main exit code=0")
        return 0
    except Exception as exc:
        logger.exception("main error: %s", exc)
        print(f"[done] artifacts=0 errors=1 error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
