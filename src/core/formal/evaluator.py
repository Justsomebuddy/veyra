"""Internal X8 row evaluation with fail-closed captured-artifact continuity."""
from __future__ import annotations

from collections.abc import Callable
import logging
from typing import TypeVar

from .catalog import (
    FormalExportSpec,
    declares_lean_theorem,
    read_bound_lean_artifact,
)
from .prep import FormalExportPrepRow, stable_card_export_prep_rows

logger = logging.getLogger(__name__)
RowT = TypeVar("RowT")


def evaluate_completion_row(
    spec: FormalExportSpec,
    checker: Callable[[bytes, str], str],
    row_factory: Callable[..., RowT],
) -> RowT:
    """Evaluate one bound artifact using the caller-supplied captured-byte checker."""
    logger.debug("evaluate_completion_row entry theorem=%s path=%s", spec.theorem_id, spec.proof_path)
    prep = find_prep_row(spec.theorem_id)
    payload, digest_matches = read_bound_lean_artifact(spec)
    text = payload.decode(errors="replace") if payload is not None else ""
    lean_status = checker(payload, spec.artifact_sha256) if payload is not None and digest_matches else "blocked"
    after_payload, after_matches = read_bound_lean_artifact(spec)
    continuous = digest_matches and after_matches and payload == after_payload
    if digest_matches and not continuous:
        logger.error("evaluate_completion_row canonical drift theorem=%s path=%s", spec.theorem_id, spec.proof_path)
    checked = prep is not None and continuous and declares_lean_theorem(text, spec.lean_symbol) and lean_status == "checked"
    result = row_factory(
        theorem_id=prep.theorem_id if prep else spec.theorem_id,
        title=prep.title if prep else spec.fallback_title,
        source_hook=prep.source if prep else spec.fallback_source,
        backend="Lean",
        proof_path=str(spec.proof_path),
        lean_symbol=spec.lean_symbol,
        artifact_sha256=spec.artifact_sha256,
        artifact_digest_status="matched" if continuous else ("drift" if digest_matches else "mismatch"),
        dependencies=prep.dependencies if prep else (),
        export_status="completed" if checked else "blocked",
        lean_status=lean_status,
        formalized=checked,
        boundary=spec.boundary,
    )
    logger.debug("evaluate_completion_row exit theorem=%s status=%s", spec.theorem_id, getattr(result, "export_status", None))
    return result


def find_prep_row(theorem_id: str) -> FormalExportPrepRow | None:
    """Return the exact X7 prep row for one theorem-card identifier."""
    logger.debug("find_prep_row entry theorem=%s", theorem_id)
    for row in stable_card_export_prep_rows():
        if row.theorem_id == theorem_id:
            logger.debug("find_prep_row exit found=%s", row.theorem_id)
            return row
    logger.debug("find_prep_row exit found=None")
    return None
