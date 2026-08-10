"""Processed table generation for Veyra experiments."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .compression import CompressionWeights, compression_scores
from .counterexamples import find_echo_splits, find_stitch_commutators, find_weave_incompatibilities
from .language_coverage import language_coverage_matrix
from .language_span_coverage import run_span_diagnostic_coverage, span_diagnostic_cases
from .modes import Mode, enumerate_modes
from .approx_resonance import approximate_resonance_profile
from .primes import prime_profile
from .resonance import resonance_profile
from .spectrum import candidate_parts, resonance_spectrum
from .weave import cyclic_representative, cyclic_weave, ordered_weave
from .weighted_resonance import CostMap, weighted_resonance_profile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableArtifact:
    """Generated table artifact metadata."""

    kind: str
    path: Path
    rows: int


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> TableArtifact:
    """Write rows to CSV and return artifact metadata."""
    logger.debug("write_csv entry path=%s rows=%d", path, len(rows))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    result = TableArtifact(path.stem, path, len(rows))
    logger.debug("write_csv exit result=%r", result)
    return result


def write_json(path: Path, data: Any, rows: int) -> TableArtifact:
    """Write JSON data and return artifact metadata."""
    logger.debug("write_json entry path=%s rows=%d", path, rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    result = TableArtifact(path.stem, path, rows)
    logger.debug("write_json exit result=%r", result)
    return result


def spectrum_rows(whole: Mode, alphabet: Iterable[str], max_part_len: int, min_part_len: int, max_defects: int) -> list[dict[str, Any]]:
    """Build resonance spectrum table rows."""
    logger.debug("spectrum_rows entry whole=%s", whole.word)
    candidates = candidate_parts(alphabet, max_part_len, min_part_len)
    rows: list[dict[str, Any]] = []
    for entry in resonance_spectrum(whole, candidates, max_defects, include_nonresonant=True):
        best = entry.profile.best
        rows.append({
            "part": entry.part.word,
            "resonates": entry.profile.resonates,
            "exact": entry.exact,
            "defects": entry.defect_count,
            "offset": None if best is None else best.offset,
            "obstruction": entry.profile.obstruction,
        })
    logger.debug("spectrum_rows exit rows=%d", len(rows))
    return rows


def compression_rows(whole: Mode, alphabet: Iterable[str], max_part_len: int, min_part_len: int, max_defects: int, weights: CompressionWeights) -> list[dict[str, Any]]:
    """Build compression score table rows."""
    logger.debug("compression_rows entry whole=%s weights=%r", whole.word, weights)
    candidates = candidate_parts(alphabet, max_part_len, min_part_len)
    rows = [{
        "part": item.part.word,
        "cost": item.cost,
        "saving": item.saving,
        "ratio": item.ratio,
        "defects": item.spectrum_entry.defect_count,
        "offset": item.spectrum_entry.best_offset,
        "obstruction": item.spectrum_entry.profile.obstruction,
    } for item in compression_scores(whole, candidates, max_defects, weights)]
    logger.debug("compression_rows exit rows=%d", len(rows))
    return rows


def prime_variant_rows(alphabet: Iterable[str], max_len: int, tact: str) -> list[dict[str, Any]]:
    """Build prime variant table rows."""
    logger.debug("prime_variant_rows entry max_len=%d tact=%r", max_len, tact)
    rows: list[dict[str, Any]] = []
    for mode in enumerate_modes(alphabet, max_len, include_silent=False):
        profile = prime_profile(mode, tact=tact)
        rows.append({
            "mode": mode.word,
            "length": mode.length,
            "numeric_prime": profile.numeric_prime,
            "ordered_primitive": profile.ordered_primitive,
            "cyclic_primitive": profile.cyclic_primitive,
            "ordered_resonance_prime": profile.ordered_resonance_prime,
        })
    logger.debug("prime_variant_rows exit rows=%d", len(rows))
    return rows


def phase_resonance_rows(part: Mode, alphabet: Iterable[str], max_len: int) -> list[dict[str, Any]]:
    """Build exact ordered/cyclic phase resonance rows."""
    logger.debug("phase_resonance_rows entry part=%s max_len=%d", part.word, max_len)
    rows: list[dict[str, Any]] = []
    for whole in enumerate_modes(alphabet, max_len, include_silent=False):
        profile = resonance_profile(part, whole)
        rows.append({
            "part": part.word,
            "whole": whole.word,
            "ordered": profile.ordered,
            "cyclic": profile.cyclic,
            "offsets": "|".join(map(str, profile.phase_offsets)),
            "obstruction": profile.obstruction,
        })
    logger.debug("phase_resonance_rows exit rows=%d", len(rows))
    return rows


def approx_resonance_rows(part: Mode, alphabet: Iterable[str], max_len: int, max_defects: int) -> list[dict[str, Any]]:
    """Build bounded-defect approximate resonance rows."""
    logger.debug("approx_resonance_rows entry part=%s max_len=%d max_defects=%d", part.word, max_len, max_defects)
    rows: list[dict[str, Any]] = []
    for whole in enumerate_modes(alphabet, max_len, include_silent=False):
        profile = approximate_resonance_profile(part, whole, max_defects)
        best = profile.best
        details = "" if best is None else "|".join(f"{d.index}:{d.expected}>{d.actual}" for d in best.defects)
        rows.append({
            "part": part.word,
            "whole": whole.word,
            "resonates": profile.resonates,
            "obstruction": profile.obstruction,
            "best_offset": None if best is None else best.offset,
            "defects": None if best is None else best.defect_count,
            "defect_detail": details,
        })
    logger.debug("approx_resonance_rows exit rows=%d", len(rows))
    return rows


def weighted_resonance_rows(part: Mode, alphabet: Iterable[str], max_len: int, budget: float, costs: CostMap, default_cost: float) -> list[dict[str, Any]]:
    """Build weighted-defect resonance rows."""
    logger.debug("weighted_resonance_rows entry part=%s max_len=%d budget=%s", part.word, max_len, budget)
    rows: list[dict[str, Any]] = []
    for whole in enumerate_modes(alphabet, max_len, include_silent=False):
        profile = weighted_resonance_profile(part, whole, budget, costs, default_cost)
        best = profile.best
        details = "" if best is None else "|".join(f"{d.index}:{d.expected}>{d.actual}:{d.cost:g}" for d in best.defects)
        rows.append({
            "part": part.word,
            "whole": whole.word,
            "resonates": profile.resonates,
            "obstruction": profile.obstruction,
            "best_offset": None if best is None else best.offset,
            "total_cost": None if best is None else best.total_cost,
            "defects": None if best is None else best.defect_count,
            "defect_detail": details,
        })
    logger.debug("weighted_resonance_rows exit rows=%d", len(rows))
    return rows


def cyclic_weave_rows(alphabet: Iterable[str], max_len: int, mapping: dict[str, Mode]) -> list[dict[str, Any]]:
    """Build ordered/cyclic weave comparison rows."""
    logger.debug("cyclic_weave_rows entry max_len=%d keys=%r", max_len, sorted(mapping))
    rows: list[dict[str, Any]] = []
    for driver in enumerate_modes(alphabet, max_len, include_silent=False):
        if not all(tact in mapping for tact in driver.tacts):
            continue
        ordered = ordered_weave(driver, mapping)
        cyclic = cyclic_weave(driver, mapping)
        rows.append({
            "driver": driver.word,
            "cyclic_driver": cyclic_representative(driver).word,
            "ordered_output": ordered.word,
            "cyclic_output": cyclic.word,
            "same_word": ordered == cyclic,
        })
    logger.debug("cyclic_weave_rows exit rows=%d", len(rows))
    return rows


def language_coverage_rows() -> list[dict[str, Any]]:
    """Build Core Language coverage-matrix table rows."""
    logger.debug("language_coverage_rows entry")
    rows = [{
        "family": cell.family,
        "cases": cell.cases,
        "blocked": cell.blocked,
        "unknown": cell.unknown,
        "ready": cell.ready,
        "unexpected": cell.unexpected,
        "covered": cell.cases > 0,
    } for cell in language_coverage_matrix()]
    logger.debug("language_coverage_rows exit rows=%d", len(rows))
    return rows


def span_diagnostic_rows() -> list[dict[str, Any]]:
    """Build Core Language source-span diagnostic table rows."""
    logger.debug("span_diagnostic_rows entry")
    cases = {case.name: case for case in span_diagnostic_cases()}
    rows: list[dict[str, Any]] = []
    for result in run_span_diagnostic_coverage():
        case = cases[result.name]
        rows.append({
            "name": result.name,
            "source": case.source.replace("\n", "\\n"),
            "ok": result.ok,
            "expected": result.expected,
            "found": result.found,
            "message": result.message,
            "line": result.line,
            "column": result.column,
            "has_excerpt": result.has_excerpt,
            "multiline": "\n" in case.source,
        })
    logger.debug("span_diagnostic_rows exit rows=%d", len(rows))
    return rows


def counterexample_data(alphabet: Iterable[str], max_len: int, limit: int) -> dict[str, Any]:
    """Build counterexample JSON-serializable data."""
    logger.debug("counterexample_data entry max_len=%d limit=%d", max_len, limit)
    modes = enumerate_modes(alphabet, max_len, include_silent=False)
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    data = {
        "echo_splits": [item.__dict__ | {"left": item.left.word, "right": item.right.word} for item in find_echo_splits(modes, "length", "bag", limit)],
        "stitch_commutators": [
            {"left": item.left.word, "right": item.right.word, "left_then_right": item.left_then_right.word, "right_then_left": item.right_then_left.word, "test_name": item.test_name}
            for item in find_stitch_commutators(modes, "ordered", limit)
        ],
        "weave_incompatibilities": [
            {"driver_left": item.driver_left.word, "driver_right": item.driver_right.word, "output_left": item.output_left.word, "output_right": item.output_right.word, "driver_test": item.driver_test, "output_test": item.output_test}
            for item in find_weave_incompatibilities(modes, "length", "length", mapping, limit)
        ],
    }
    logger.debug("counterexample_data exit sections=%r", list(data))
    return data


def write_manifest(path: Path, params: dict[str, Any], artifacts: list[TableArtifact]) -> TableArtifact:
    """Write generation manifest."""
    logger.debug("write_manifest entry path=%s artifacts=%d", path, len(artifacts))
    data = {
        "params": params,
        "artifacts": [
            {"kind": artifact.kind, "path": artifact.path.as_posix(), "rows": artifact.rows}
            for artifact in artifacts
        ],
    }
    result = write_json(path, data, len(artifacts))
    logger.debug("write_manifest exit result=%r", result)
    return result
