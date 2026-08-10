"""Declarative X8 theorem-card identifiers and pinned Lean artifact paths."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import logging
from pathlib import Path
import re
import tempfile

from .formal_bridge import check_lean_echo_export
from .formal_export_geometry_data import (
    GEOMETRY_ARTIFACT_SHA256,
    GEOMETRY_FORMAL_EXPORT_ROWS,
    LINE_SHELL_INTERSECTION_ID,
    LINE_SHELL_INTERSECTION_SYMBOL,
    PLANE_RELABEL_COMPOSITION_ID,
    PLANE_RELABEL_COMPOSITION_SYMBOL,
    SAS_TRIANGLE_ID,
    SAS_TRIANGLE_SYMBOL,
    SSS_TRIANGLE_ID,
    SSS_TRIANGLE_SYMBOL,
)
from .formal_export_remaining_data import (
    ANALYSIS_ARTIFACT_SHA256, CYCLIC_ARTIFACT_SHA256,
    REMAINING_FORMAL_EXPORT_ROWS,
)

from .paths import TMP_DIR, repository_path

logger = logging.getLogger(__name__)
_GEOMETRY_REEXPORTS = (
    SSS_TRIANGLE_ID, SSS_TRIANGLE_SYMBOL,
    SAS_TRIANGLE_ID, SAS_TRIANGLE_SYMBOL,
    LINE_SHELL_INTERSECTION_ID, LINE_SHELL_INTERSECTION_SYMBOL,
    PLANE_RELABEL_COMPOSITION_ID, PLANE_RELABEL_COMPOSITION_SYMBOL,
)

BINOMIAL_SYMMETRY_ID = "binomial-symmetry"
BINOMIAL_SYMMETRY_SYMBOL = "THM_B001_binomial_symmetry_6_2"
CYCLIC_PERIOD_ID = "cyclic-period"
CYCLIC_PERIOD_SYMBOL = "THM_C001_cyclic_period"
PYTHAGOREAN_SEPARATION_ID = "pythagorean-separation"
PYTHAGOREAN_SEPARATION_SYMBOL = "THM_G001_pythagorean_3_4_5"
POLYNOMIAL_IDENTITY_ID = "polynomial-identity"
POLYNOMIAL_IDENTITY_SYMBOL = "THM_A001_polynomial_identity_coeffs"
POLYNOMIAL_EVALUATION_ID = "polynomial-evaluation"
POLYNOMIAL_EVALUATION_SYMBOL = "THM_A002_polynomial_eval_at_3"
LINEAR_EQUATION_ID = "linear-equation-solution"
LINEAR_EQUATION_SYMBOL = "THM_A003_linear_equation_unique_solution"
PROBABILITY_COMPLEMENT_ID = "probability-complement"
PROBABILITY_COMPLEMENT_SYMBOL = "THM_P001_probability_complement_counts"
PROBABILITY_UNION_ID = "probability-union"
PROBABILITY_UNION_SYMBOL = "THM_P002_probability_union_counts"
PROBABILITY_INDEPENDENCE_ID = "probability-independence"
PROBABILITY_INDEPENDENCE_SYMBOL = "THM_P003_probability_independence_counts"
MEAN_BALANCE_ID = "mean-balance"
MEAN_BALANCE_SYMBOL = "THM_S001_mean_balance_1_3_5"
VARIANCE_SHIFT_ID = "variance-shift"
VARIANCE_SHIFT_SYMBOL = "THM_S002_variance_shift_1_3_5_plus_10"


@dataclass(frozen=True)
class FormalExportSpec:
    """One exact X7 candidate-to-Lean-artifact binding."""

    theorem_id: str
    fallback_title: str
    fallback_source: str
    proof_path: Path
    lean_symbol: str
    artifact_sha256: str
    boundary: str


def lean_cyclic_period_export_path() -> Path:
    """Return the pinned cyclic-period Lean artifact path."""
    logger.debug("lean_cyclic_period_export_path entry")
    result = Path("proofs/lean/VeyraCyclic.lean")
    logger.debug("lean_cyclic_period_export_path exit result=%s", result)
    return result


def lean_pythagorean_export_path() -> Path:
    """Return the pinned finite-geometry Lean artifact path."""
    logger.debug("lean_pythagorean_export_path entry")
    result = Path("proofs/lean/VeyraGeometry.lean")
    logger.debug("lean_pythagorean_export_path exit result=%s", result)
    return result


def lean_algebra_export_path() -> Path:
    """Return the pinned finite-algebra Lean artifact path."""
    logger.debug("lean_algebra_export_path entry")
    result = Path("proofs/lean/VeyraAlgebra.lean")
    logger.debug("lean_algebra_export_path exit result=%s", result)
    return result


def lean_probability_export_path() -> Path:
    """Return the pinned finite-probability Lean artifact path."""
    logger.debug("lean_probability_export_path entry")
    result = Path("proofs/lean/VeyraProbability.lean")
    logger.debug("lean_probability_export_path exit result=%s", result)
    return result


def lean_statistics_export_path() -> Path:
    """Return the pinned canonical-sample mean-balance Lean artifact path."""
    logger.debug("lean_statistics_export_path entry")
    result = Path("proofs/lean/VeyraStatistics.lean")
    logger.debug("lean_statistics_export_path exit result=%s", result)
    return result


def lean_combinatorics_export_path() -> Path:
    """Return the pinned fixed-binomial Lean artifact path."""
    logger.debug("lean_combinatorics_export_path entry")
    result = Path("proofs/lean/VeyraCombinatorics.lean")
    logger.debug("lean_combinatorics_export_path exit result=%s", result)
    return result


def formal_export_specs() -> tuple[FormalExportSpec, ...]:
    """Return the nineteen exact X8 completion bindings in catalog order."""
    logger.debug("formal_export_specs entry")
    rows = (
        FormalExportSpec(
            CYCLIC_PERIOD_ID, "Cyclic period", "trig.cyclic_period",
            lean_cyclic_period_export_path(), CYCLIC_PERIOD_SYMBOL,
            CYCLIC_ARTIFACT_SHA256,
            "formalizes only the Nat modulo cyclic-period card; no claim about full trigonometry or all Veyra cyclic theory",
        ),
        FormalExportSpec(
            PYTHAGOREAN_SEPARATION_ID, "Pythagorean separation", "geometry.pythagorean",
            lean_pythagorean_export_path(), PYTHAGOREAN_SEPARATION_SYMBOL,
            GEOMETRY_ARTIFACT_SHA256,
            "formalizes only the finite 3-4-5 Nat separation card; no claim about full Euclidean geometry or all Veyra geometry",
        ),
        FormalExportSpec(
            POLYNOMIAL_IDENTITY_ID, "Polynomial identity", "algebra.polynomial_identity",
            lean_algebra_export_path(), POLYNOMIAL_IDENTITY_SYMBOL,
            ANALYSIS_ARTIFACT_SHA256,
            "formalizes only one finite coefficient-shadow identity card; no claim about full polynomial algebra",
        ),
        FormalExportSpec(
            POLYNOMIAL_EVALUATION_ID, "Polynomial evaluation", "algebra.polynomial_eval",
            lean_algebra_export_path(), POLYNOMIAL_EVALUATION_SYMBOL,
            ANALYSIS_ARTIFACT_SHA256,
            "formalizes only one finite polynomial-evaluation card; no claim about all polynomial evaluation or algebra",
        ),
        FormalExportSpec(
            LINEAR_EQUATION_ID, "Linear equation solution", "algebra.linear_solution",
            lean_algebra_export_path(), LINEAR_EQUATION_SYMBOL,
            ANALYSIS_ARTIFACT_SHA256,
            "formalizes only one finite integer unique-solution card; no claim about the full linear-equation solver or all algebra",
        ),
        FormalExportSpec(
            PROBABILITY_COMPLEMENT_ID, "Probability complement", "probability.complement",
            lean_probability_export_path(), PROBABILITY_COMPLEMENT_SYMBOL,
            "b41611ae5d42575211526fd3e9c7fa97b97eb9ab6c47e9b3f2b2dbc8b5f03542",
            "formalizes only one finite counting complement card; no claim about full probability theory",
        ),
        FormalExportSpec(
            PROBABILITY_UNION_ID, "Probability union", "probability.union",
            lean_probability_export_path(), PROBABILITY_UNION_SYMBOL,
            "b41611ae5d42575211526fd3e9c7fa97b97eb9ab6c47e9b3f2b2dbc8b5f03542",
            "formalizes only the canonical four-outcome inclusion-exclusion count card; no claim about general probability or measure theory",
        ),
        FormalExportSpec(
            PROBABILITY_INDEPENDENCE_ID, "Probability independence", "probability.independence",
            lean_probability_export_path(), PROBABILITY_INDEPENDENCE_SYMBOL,
            "b41611ae5d42575211526fd3e9c7fa97b97eb9ab6c47e9b3f2b2dbc8b5f03542",
            "formalizes only the canonical four-outcome independence count-product card; no claim about general independence, probability, or measure theory",
        ),
        FormalExportSpec(
            MEAN_BALANCE_ID, "Mean balance", "statistics.mean_balance",
            lean_statistics_export_path(), MEAN_BALANCE_SYMBOL,
            "4e39dea022ec7b268e1a6bb52bda34acc0a7b40d02d730a73570cf60bba006f0",
            "formalizes only the fixed finite sample (1,3,5) mean-balance card; no claim about general statistics",
        ),
        FormalExportSpec(
            BINOMIAL_SYMMETRY_ID, "Binomial symmetry", "combinatorics.binomial_symmetry",
            lean_combinatorics_export_path(), BINOMIAL_SYMMETRY_SYMBOL,
            "1b61326de0dab1522f18441211e00d6b978e699c38898ffdbd880dd96df16b8d",
            "formalizes only choose 6 2 = choose 6 4 = 15 by the displayed finite recurrence; no claim about general binomial symmetry or combinatorics",
        ),
        FormalExportSpec(
            VARIANCE_SHIFT_ID, "Variance shift", "statistics.variance_shift",
            lean_statistics_export_path(), VARIANCE_SHIFT_SYMBOL,
            "4e39dea022ec7b268e1a6bb52bda34acc0a7b40d02d730a73570cf60bba006f0",
            "formalizes only variance numerators 8 for fixed samples (1,3,5) and (11,13,15); no claim about arbitrary shifts or general statistics",
        ),
        *(
            FormalExportSpec(
                theorem_id, title, source, lean_pythagorean_export_path(), symbol,
                GEOMETRY_ARTIFACT_SHA256, boundary,
            )
            for theorem_id, title, source, symbol, boundary in GEOMETRY_FORMAL_EXPORT_ROWS
        ),
        *(
            FormalExportSpec(theorem_id, title, source, Path(path), symbol, digest, boundary)
            for theorem_id, title, source, _dependencies, path, symbol, digest, boundary
            in REMAINING_FORMAL_EXPORT_ROWS
        ),
    )
    logger.debug("formal_export_specs exit count=%d", len(rows))
    return rows


def read_bound_lean_artifact(spec: FormalExportSpec) -> tuple[bytes | None, bool]:
    """Read a Lean artifact and bind its entire byte content to the catalog digest."""
    logger.debug("read_bound_lean_artifact entry theorem=%s path=%s", spec.theorem_id, spec.proof_path)
    target = spec.proof_path if spec.proof_path.is_absolute() else repository_path(spec.proof_path.as_posix())
    try:
        payload = target.read_bytes()
    except OSError as exc:
        logger.error("read_bound_lean_artifact failed theorem=%s error=%s", spec.theorem_id, exc)
        logger.debug("read_bound_lean_artifact exit bytes=0 matched=False")
        return None, False
    actual = hashlib.sha256(payload).hexdigest()
    matched = hmac.compare_digest(actual, spec.artifact_sha256)
    if not matched:
        logger.warning("read_bound_lean_artifact digest mismatch theorem=%s actual=%s", spec.theorem_id, actual)
    logger.debug("read_bound_lean_artifact exit bytes=%d matched=%s", len(payload), matched)
    return payload, matched


def check_captured_lean_artifact(payload: bytes, digest: str) -> str:
    """Compile exact captured bytes from a private content-addressed temporary path."""
    logger.debug("check_captured_lean_artifact entry bytes=%d digest=%s", len(payload), digest)
    temp_root = TMP_DIR
    actual_digest = hashlib.sha256(payload).hexdigest()
    try:
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="x8-lean-", dir=temp_root) as directory:
            capture = Path(directory) / f"{actual_digest}.lean"
            capture.write_bytes(payload)
            capture.chmod(0o600)
            status = check_lean_echo_export(capture).status
    except OSError as exc:
        logger.error("check_captured_lean_artifact failed digest=%s error=%s", digest, exc)
        status = "blocked"
    logger.debug("check_captured_lean_artifact exit status=%s", status)
    return status


def declares_lean_theorem(text: str, symbol: str) -> bool:
    """Recognize one exact declaration marker outside Lean comments."""
    logger.debug("declares_lean_theorem entry symbol=%s", symbol)
    pattern = rf"(?m)^[ \t]*(?:theorem|lemma)[ \t]+{re.escape(symbol)}(?=[ \t:(])"
    result = re.search(pattern, _strip_lean_comments(text)) is not None
    logger.debug("declares_lean_theorem exit result=%s", result)
    return result


def _strip_lean_comments(text: str) -> str:
    logger.debug("_strip_lean_comments entry chars=%d", len(text))
    output: list[str] = []
    index = 0
    block_depth = 0
    while index < len(text):
        pair = text[index:index + 2]
        if block_depth == 0 and pair == "--":
            newline = text.find("\n", index + 2)
            if newline < 0:
                break
            output.append("\n")
            index = newline + 1
            continue
        if pair == "/-":
            block_depth += 1
            index += 2
            continue
        if block_depth > 0 and pair == "-/":
            block_depth -= 1
            index += 2
            continue
        if block_depth == 0:
            output.append(text[index])
        elif text[index] == "\n":
            output.append("\n")
        index += 1
    if block_depth:
        logger.warning("_strip_lean_comments unclosed block depth=%d", block_depth)
    result = "".join(output)
    logger.debug("_strip_lean_comments exit chars=%d", len(result))
    return result
