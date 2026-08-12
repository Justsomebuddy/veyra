"""Structural predicate-separation ledger kept distinct from bridge status."""

from __future__ import annotations

from collections import Counter
import logging

from .comparative_ledger_types import (
    ComparativeEvidenceRef,
    StructuralSeparationRow,
    StructuralSeparationStatus,
)
from .certify_observer_patch_atlas import observer_patch_atlas_lean_evidence
from .observer_patch_gluing_classification import disjoint_singleton_nonuniqueness

logger = logging.getLogger(__name__)

STRUCTURAL_SEPARATION_SCHEMA = "veyra.structural-separation-ledger.v1"
_EVIDENCE_KINDS = frozenset({"executable", "lean", "counterexample", "document"})


def structural_separation_rows() -> tuple[StructuralSeparationRow, ...]:
    """Return exact finite predicate separations without expressivity claims."""
    logger.debug("structural_separation_rows entry")
    lean = observer_patch_atlas_lean_evidence()
    witness = disjoint_singleton_nonuniqueness()
    checked = (
        witness.classification.criterion.exact_gluing_exists
        and witness.classification.direct_exact_gluing_count == 2
        and witness.classification.classification_holds
        and witness.classification.uniqueness_iff_conflict_complete
        and witness.both_exact
        and witness.distinct
        and lean.digest_status == "matched"
        and lean.lean_status == "checked"
        and lean.helpers_exact
    )
    rows = (
        StructuralSeparationRow(
            STRUCTURAL_SEPARATION_SCHEMA,
            "SEP-G4-001",
            "there exists an exact global equivalence-relation gluing",
            "there exists a unique exact global equivalence-relation gluing",
            StructuralSeparationStatus.STRICTLY_SEPARATED if checked else StructuralSeparationStatus.OPEN,
            "finite declared cover with extensional equality of relations",
            "two disjoint singleton patches admit both identity and universal exact gluings",
            (
                ComparativeEvidenceRef("G4-NONUNIQUE", "counterexample", "src/core/observer_patch_gluing_classification.py", checked),
                ComparativeEvidenceRef("G4-LEAN-HELPER", "lean", "proofs/lean/VeyraObserverPatchAtlas.lean", True),
            ),
            "separates two predicates only; it does not establish Veyra superiority, nonexpressibility, or novelty",
        ),
    )
    result = tuple(validate_structural_separation_row(row) for row in rows)
    logger.debug("structural_separation_rows exit count=%d", len(result))
    return result


def validate_structural_separation_row(value: object) -> StructuralSeparationRow:
    """Validate one exact separation row and its witness obligations."""
    logger.debug("validate_structural_separation_row entry")
    if type(value) is not StructuralSeparationRow:
        logger.error("validate_structural_separation_row exact type rejected")
        raise ValueError("structural-separation-row-must-be-exact")
    strings = (
        value.schema,
        value.separation_id,
        value.left_predicate,
        value.right_predicate,
        value.scope,
        value.witness,
        value.boundary,
    )
    valid = (
        value.schema == STRUCTURAL_SEPARATION_SCHEMA
        and all(_bounded_text(item) for item in strings)
        and type(value.status) is StructuralSeparationStatus
        and type(value.evidence) is tuple
        and 1 <= len(value.evidence) <= 8
        and all(
            type(item) is ComparativeEvidenceRef
            and _bounded_text(item.evidence_id)
            and item.kind in _EVIDENCE_KINDS
            and _bounded_text(item.location)
            and not item.location.startswith("/")
            and type(item.checked) is bool
            for item in value.evidence
        )
    )
    if not valid:
        logger.error("validate_structural_separation_row shape rejected")
        raise ValueError("invalid-structural-separation-row")
    if value.status is StructuralSeparationStatus.STRICTLY_SEPARATED and not all(
        item.checked for item in value.evidence
    ):
        logger.error("validate_structural_separation_row unsupported strict status")
        raise ValueError("strict-separation-without-evidence")
    logger.debug("validate_structural_separation_row exit id=%s", value.separation_id)
    return value


def structural_separation_summary(rows: tuple[StructuralSeparationRow, ...] | None = None) -> dict[str, int | bool]:
    """Return exact status counts for the separation ledger."""
    logger.debug("structural_separation_summary entry supplied=%s", rows is not None)
    captured = structural_separation_rows() if rows is None else tuple(validate_structural_separation_row(row) for row in rows)
    counts = Counter(row.status.value for row in captured)
    result: dict[str, int | bool] = {
        "rows": len(captured),
        "candidate_separation": counts[StructuralSeparationStatus.CANDIDATE_SEPARATION.value],
        "strictly_separated": counts[StructuralSeparationStatus.STRICTLY_SEPARATED.value],
        "open": counts[StructuralSeparationStatus.OPEN.value],
        "unique_ids": len({row.separation_id for row in captured}) == len(captured),
        "all_strict_checked": all(row.status is not StructuralSeparationStatus.STRICTLY_SEPARATED or all(item.checked for item in row.evidence) for row in captured),
    }
    logger.debug("structural_separation_summary exit result=%r", result)
    return result


def structural_separation_checklist() -> tuple[str, ...]:
    """Return fixed acceptance rules for structural separation rows."""
    logger.debug("structural_separation_checklist entry")
    result = (
        "STRICTLY_SEPARATED requires a checked counterexample or theorem",
        "the separated predicates and equality notion are explicit",
        "bridge reduction does not imply strict separation",
        "finite predicate separation does not imply nonexpressibility",
        "no row implies novelty or superiority",
    )
    logger.debug("structural_separation_checklist exit count=%d", len(result))
    return result


def _bounded_text(value: object) -> bool:
    """Return whether one field is nonempty bounded UTF-8 text."""
    logger.debug("separation _bounded_text entry type=%s", type(value).__name__)
    if type(value) is not str or not value:
        logger.debug("separation _bounded_text exit result=False")
        return False
    try:
        result = len(value.encode("utf-8")) <= 2_048
    except UnicodeError:
        logger.error("separation _bounded_text encoding rejected")
        return False
    logger.debug("separation _bounded_text exit result=%s", result)
    return result
