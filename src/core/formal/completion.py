"""X8 checked formal-export completion for stable theorem-card candidates."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import logging
from pathlib import Path

from .catalog import (
    BINOMIAL_SYMMETRY_ID, BINOMIAL_SYMMETRY_SYMBOL,
    CYCLIC_PERIOD_ID, CYCLIC_PERIOD_SYMBOL,
    LINEAR_EQUATION_ID, LINEAR_EQUATION_SYMBOL,
    LINE_SHELL_INTERSECTION_ID, LINE_SHELL_INTERSECTION_SYMBOL,
    PLANE_RELABEL_COMPOSITION_ID, PLANE_RELABEL_COMPOSITION_SYMBOL,
    POLYNOMIAL_EVALUATION_ID, POLYNOMIAL_EVALUATION_SYMBOL,
    POLYNOMIAL_IDENTITY_ID, POLYNOMIAL_IDENTITY_SYMBOL,
    PROBABILITY_COMPLEMENT_ID, PROBABILITY_COMPLEMENT_SYMBOL,
    PROBABILITY_INDEPENDENCE_ID, PROBABILITY_INDEPENDENCE_SYMBOL,
    PROBABILITY_UNION_ID, PROBABILITY_UNION_SYMBOL,
    PYTHAGOREAN_SEPARATION_ID, PYTHAGOREAN_SEPARATION_SYMBOL,
    SAS_TRIANGLE_ID, SAS_TRIANGLE_SYMBOL,
    SSS_TRIANGLE_ID, SSS_TRIANGLE_SYMBOL,
    VARIANCE_SHIFT_ID, VARIANCE_SHIFT_SYMBOL,
    FormalExportSpec,
    check_captured_lean_artifact,
    formal_export_specs,
    lean_algebra_export_path,
    lean_combinatorics_export_path,
    lean_cyclic_period_export_path,
    lean_probability_export_path,
    lean_pythagorean_export_path,
    lean_statistics_export_path,
)
from .evaluator import evaluate_completion_row
from .prep import FormalExportPrepRow, stable_card_export_prep_rows

logger = logging.getLogger(__name__)
_ROW_DICT_KEYS = tuple("theorem_id title source_hook backend proof_path lean_symbol artifact_sha256 artifact_digest_status dependencies export_status lean_status formalized boundary".split())

__all__ = (
    "BINOMIAL_SYMMETRY_ID", "BINOMIAL_SYMMETRY_SYMBOL",
    "CYCLIC_PERIOD_ID", "CYCLIC_PERIOD_SYMBOL",
    "FormalExportCompletionRow",
    "LINEAR_EQUATION_ID", "LINEAR_EQUATION_SYMBOL",
    "LINE_SHELL_INTERSECTION_ID", "LINE_SHELL_INTERSECTION_SYMBOL",
    "PLANE_RELABEL_COMPOSITION_ID", "PLANE_RELABEL_COMPOSITION_SYMBOL",
    "POLYNOMIAL_EVALUATION_ID", "POLYNOMIAL_EVALUATION_SYMBOL",
    "POLYNOMIAL_IDENTITY_ID", "POLYNOMIAL_IDENTITY_SYMBOL",
    "PROBABILITY_COMPLEMENT_ID", "PROBABILITY_COMPLEMENT_SYMBOL",
    "PROBABILITY_INDEPENDENCE_ID", "PROBABILITY_INDEPENDENCE_SYMBOL",
    "PROBABILITY_UNION_ID", "PROBABILITY_UNION_SYMBOL",
    "PYTHAGOREAN_SEPARATION_ID", "PYTHAGOREAN_SEPARATION_SYMBOL",
    "SAS_TRIANGLE_ID", "SAS_TRIANGLE_SYMBOL",
    "SSS_TRIANGLE_ID", "SSS_TRIANGLE_SYMBOL",
    "VARIANCE_SHIFT_ID", "VARIANCE_SHIFT_SYMBOL",
    "completed_formal_export_rows",
    "binomial_symmetry_completion_row",
    "cyclic_period_completion_row",
    "formal_export_completion_checklist",
    "formal_export_completion_summary",
    "lean_algebra_export_path",
    "lean_combinatorics_export_path",
    "lean_cyclic_period_export_path",
    "lean_probability_export_path",
    "lean_pythagorean_export_path",
    "lean_statistics_export_path",
    "linear_equation_completion_row",
    "line_shell_intersection_completion_row",
    "mean_balance_completion_row",
    "polynomial_evaluation_completion_row",
    "polynomial_identity_completion_row",
    "probability_complement_completion_row",
    "probability_independence_completion_row",
    "probability_union_completion_row",
    "pythagorean_separation_completion_row",
    "plane_relabel_composition_completion_row",
    "sas_triangle_completion_row",
    "sss_triangle_completion_row",
    "variance_shift_completion_row",
)


@dataclass(frozen=True)
class FormalExportCompletionRow:
    """One prep-ready theorem-card candidate promoted to a checked proof artifact."""

    theorem_id: str
    title: str
    source_hook: str
    backend: str
    proof_path: str
    lean_symbol: str
    dependencies: tuple[str, ...]
    export_status: str
    lean_status: str
    formalized: bool
    boundary: str
    artifact_sha256: str = ""
    artifact_digest_status: str = "unbound"

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready completion row."""
        logger.debug("FormalExportCompletionRow.as_dict entry theorem=%s", self.theorem_id)
        values = asdict(self)
        result: dict[str, object] = {key: values[key] for key in _ROW_DICT_KEYS}
        logger.debug("FormalExportCompletionRow.as_dict exit result=%r", result)
        return result


def cyclic_period_completion_row() -> FormalExportCompletionRow:
    """Return the checked completion row for `cyclic-period`."""
    logger.debug("cyclic_period_completion_row entry")
    result = _named_completion_row("cyclic-period")
    logger.debug("cyclic_period_completion_row exit status=%s", result.export_status)
    return result


def binomial_symmetry_completion_row() -> FormalExportCompletionRow:
    """Return the fixed `choose 6 2 = choose 6 4 = 15` completion row."""
    logger.debug("binomial_symmetry_completion_row entry")
    result = _named_completion_row(BINOMIAL_SYMMETRY_ID)
    logger.debug("binomial_symmetry_completion_row exit status=%s", result.export_status)
    return result


def pythagorean_separation_completion_row() -> FormalExportCompletionRow:
    """Return the checked finite `pythagorean-separation` completion row."""
    logger.debug("pythagorean_separation_completion_row entry")
    result = _named_completion_row("pythagorean-separation")
    logger.debug("pythagorean_separation_completion_row exit status=%s", result.export_status)
    return result


def sss_triangle_completion_row() -> FormalExportCompletionRow:
    """Return the fixed base/+10 side-square-triples completion row."""
    logger.debug("sss_triangle_completion_row entry")
    result = _named_completion_row(SSS_TRIANGLE_ID)
    logger.debug("sss_triangle_completion_row exit status=%s", result.export_status)
    return result


def sas_triangle_completion_row() -> FormalExportCompletionRow:
    """Return the fixed base/+10 SAS-anchor-measures completion row."""
    logger.debug("sas_triangle_completion_row entry")
    result = _named_completion_row(SAS_TRIANGLE_ID)
    logger.debug("sas_triangle_completion_row exit status=%s", result.export_status)
    return result


def line_shell_intersection_completion_row() -> FormalExportCompletionRow:
    """Return the fixed diameter-shell scaled-roots completion row."""
    logger.debug("line_shell_intersection_completion_row entry")
    result = _named_completion_row(LINE_SHELL_INTERSECTION_ID)
    logger.debug("line_shell_intersection_completion_row exit status=%s", result.export_status)
    return result


def plane_relabel_composition_completion_row() -> FormalExportCompletionRow:
    """Return the fixed translation-then-quarter-turn completion row."""
    logger.debug("plane_relabel_composition_completion_row entry")
    result = _named_completion_row(PLANE_RELABEL_COMPOSITION_ID)
    logger.debug("plane_relabel_composition_completion_row exit status=%s", result.export_status)
    return result


def polynomial_identity_completion_row() -> FormalExportCompletionRow:
    """Return the checked finite `polynomial-identity` completion row."""
    logger.debug("polynomial_identity_completion_row entry")
    result = _named_completion_row("polynomial-identity")
    logger.debug("polynomial_identity_completion_row exit status=%s", result.export_status)
    return result


def polynomial_evaluation_completion_row() -> FormalExportCompletionRow:
    """Return the checked finite `polynomial-evaluation` completion row."""
    logger.debug("polynomial_evaluation_completion_row entry")
    result = _named_completion_row("polynomial-evaluation")
    logger.debug("polynomial_evaluation_completion_row exit status=%s", result.export_status)
    return result


def linear_equation_completion_row() -> FormalExportCompletionRow:
    """Return the checked finite `linear-equation-solution` completion row."""
    logger.debug("linear_equation_completion_row entry")
    result = _named_completion_row("linear-equation-solution")
    logger.debug("linear_equation_completion_row exit status=%s", result.export_status)
    return result


def probability_complement_completion_row() -> FormalExportCompletionRow:
    """Return the checked finite `probability-complement` completion row."""
    logger.debug("probability_complement_completion_row entry")
    result = _named_completion_row("probability-complement")
    logger.debug("probability_complement_completion_row exit status=%s", result.export_status)
    return result


def probability_independence_completion_row() -> FormalExportCompletionRow:
    """Return the canonical four-outcome `probability-independence` completion row."""
    logger.debug("probability_independence_completion_row entry")
    result = _named_completion_row(PROBABILITY_INDEPENDENCE_ID)
    logger.debug("probability_independence_completion_row exit status=%s", result.export_status)
    return result


def probability_union_completion_row() -> FormalExportCompletionRow:
    """Return the canonical four-outcome `probability-union` completion row."""
    logger.debug("probability_union_completion_row entry")
    result = _named_completion_row(PROBABILITY_UNION_ID)
    logger.debug("probability_union_completion_row exit status=%s", result.export_status)
    return result


def mean_balance_completion_row() -> FormalExportCompletionRow:
    """Return the fixed-sample `(1,3,5)` mean-balance completion row."""
    logger.debug("mean_balance_completion_row entry")
    result = _named_completion_row("mean-balance")
    logger.debug("mean_balance_completion_row exit status=%s", result.export_status)
    return result


def variance_shift_completion_row() -> FormalExportCompletionRow:
    """Return the fixed `(1,3,5)` to `(11,13,15)` variance-numerator row."""
    logger.debug("variance_shift_completion_row entry")
    result = _named_completion_row(VARIANCE_SHIFT_ID)
    logger.debug("variance_shift_completion_row exit status=%s", result.export_status)
    return result


def completed_formal_export_rows() -> tuple[FormalExportCompletionRow, ...]:
    """Return the nineteen completed finite theorem-card formal exports."""
    logger.debug("completed_formal_export_rows entry")
    result = tuple(_completion_row(spec) for spec in formal_export_specs())
    logger.debug("completed_formal_export_rows exit count=%d", len(result))
    return result


def formal_export_completion_summary() -> dict[str, int]:
    """Return compact X8 formal-export completion counters."""
    logger.debug("formal_export_completion_summary entry")
    prep_rows: tuple[FormalExportPrepRow, ...] = stable_card_export_prep_rows()
    rows = completed_formal_export_rows()
    completed = sum(row.export_status == "completed" for row in rows)
    overclaims = sum("only" not in row.boundary or "no claim" not in row.boundary for row in rows)
    result = {
        "candidate_total": len(prep_rows),
        "completed_candidates": completed,
        "checked_lean_files": len({row.proof_path for row in rows if row.lean_status == "checked"}),
        "formalized_candidates": sum(row.formalized for row in rows),
        "remaining_prep_ready": len(prep_rows) - completed,
        "overclaims": overclaims,
    }
    logger.debug("formal_export_completion_summary exit result=%r", result)
    return result


def formal_export_completion_checklist() -> tuple[str, ...]:
    """Return X8 acceptance checklist."""
    logger.debug("formal_export_completion_checklist entry")
    result = (
        "each completed row must come from an X7 stable-card candidate",
        "each Lean proof file must check with the pinned local toolchain",
        "each completion row scope must name exactly one theorem-card candidate",
        "boundary must reject full-domain formalization claims",
    )
    logger.debug("formal_export_completion_checklist exit count=%d", len(result))
    return result


def _named_completion_row(theorem_id: str) -> FormalExportCompletionRow:
    logger.debug("_named_completion_row entry theorem=%s", theorem_id)
    result = _completion_row(_find_spec(theorem_id))
    logger.debug("_named_completion_row exit theorem=%s status=%s", theorem_id, result.export_status)
    return result


def _mean_balance_completion_row_at(proof_path: Path) -> FormalExportCompletionRow:
    """Exercise fail-closed mean-balance artifact checks at an adversarial path."""
    logger.debug("_mean_balance_completion_row_at entry path=%s", proof_path)
    result = _completion_row(replace(_find_spec("mean-balance"), proof_path=proof_path))
    logger.debug("_mean_balance_completion_row_at exit status=%s", result.export_status)
    return result


def _completion_row(spec: FormalExportSpec) -> FormalExportCompletionRow:
    logger.debug("_completion_row entry theorem=%s path=%s", spec.theorem_id, spec.proof_path)
    result = evaluate_completion_row(spec, check_captured_lean_artifact, FormalExportCompletionRow)
    logger.debug("_completion_row exit theorem=%s status=%s", spec.theorem_id, result.export_status)
    return result


def _find_spec(theorem_id: str) -> FormalExportSpec:
    logger.debug("_find_spec entry theorem=%s", theorem_id)
    for spec in formal_export_specs():
        if spec.theorem_id == theorem_id:
            logger.debug("_find_spec exit found=%s", theorem_id)
            return spec
    logger.error("_find_spec missing theorem=%s", theorem_id)
    logger.debug("_find_spec exit found=None")
    raise KeyError(theorem_id)
