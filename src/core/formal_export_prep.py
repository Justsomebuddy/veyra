"""X7 formal export preparation without claiming completed formalization."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .formal_bridge import check_lean_echo_export, lean_echo_export_path
from .proof_discipline import stable_formal_export_rows

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class FormalExportPrepRow:
    """One formal-export preparation row with explicit non-claim boundary."""
    theorem_id: str
    title: str
    source: str
    backend: str
    dependencies: tuple[str, ...]
    source_status: str
    export_status: str
    formalized: bool
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready export preparation row."""
        logger.debug("FormalExportPrepRow.as_dict entry theorem=%s", self.theorem_id)
        result = {
            "theorem_id": self.theorem_id,
            "title": self.title,
            "source": self.source,
            "backend": self.backend,
            "dependencies": self.dependencies,
            "source_status": self.source_status,
            "export_status": self.export_status,
            "formalized": self.formalized,
            "boundary": self.boundary,
        }
        logger.debug("FormalExportPrepRow.as_dict exit result=%r", result)
        return result

def checked_bridge_rows() -> tuple[FormalExportPrepRow, ...]:
    """Return already checked tiny bridge rows; these are not new broad claims."""
    logger.debug("checked_bridge_rows entry")
    path = lean_echo_export_path()
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    lean_status = check_lean_echo_export(path).status
    rows = []
    for theorem_id, title, marker in (
        ("THM-F001", "echo reflexivity", "THM_F001_echo_reflexive"),
        ("THM-F002", "product-plus-one modular escape", "THM_F002_euclid_escape_mod"),
    ):
        checked = marker in text and lean_status == "checked"
        rows.append(FormalExportPrepRow(
            theorem_id, title, str(path), "Lean", (), "bridge-file", "checked" if checked else "blocked", checked,
            "tiny bridge theorem only; does not formalize the wider Veyra layer",
        ))
    result = tuple(rows)
    logger.debug("checked_bridge_rows exit count=%d", len(result))
    return result

def stable_card_export_prep_rows() -> tuple[FormalExportPrepRow, ...]:
    """Select only stable theorem cards for future Lean/Coq-style export."""
    logger.debug("stable_card_export_prep_rows entry")
    rows = []
    for row in stable_formal_export_rows():
        backend = "Lean-prep" if row.hook.startswith(("geometry", "algebra", "analysis")) else "Coq-prep"
        rows.append(FormalExportPrepRow(
            row.theorem_id, row.title, row.hook, backend, row.dependencies,
            row.export_status, "prep-ready", False,
            "stable card selected for export preparation; no formal proof generated yet",
        ))
    result = tuple(rows)
    logger.debug("stable_card_export_prep_rows exit count=%d", len(result))
    return result

def formal_export_prep_rows() -> tuple[FormalExportPrepRow, ...]:
    """Return checked bridges plus selected stable-card export-prep rows."""
    logger.debug("formal_export_prep_rows entry")
    result = checked_bridge_rows() + stable_card_export_prep_rows()
    logger.debug("formal_export_prep_rows exit count=%d", len(result))
    return result

def formal_export_prep_summary() -> dict[str, int | bool]:
    """Return compact X7 formal-export preparation counters."""
    logger.debug("formal_export_prep_summary entry")
    bridges = checked_bridge_rows()
    candidates = stable_card_export_prep_rows()
    result: dict[str, int | bool] = {
        "checked_bridges": sum(row.export_status == "checked" and row.formalized for row in bridges),
        "candidate_rows": len(candidates),
        "prep_ready": sum(row.export_status == "prep-ready" for row in candidates),
        "candidate_formalized": sum(row.formalized for row in candidates),
        "stable_sources": sum(row.source_status == "stable-card-only" for row in candidates),
        "no_completed_claims": all(row.export_status != "completed" for row in candidates),
    }
    logger.debug("formal_export_prep_summary exit result=%r", result)
    return result

def formal_export_prep_checklist() -> tuple[str, ...]:
    """Return X7 acceptance checklist."""
    logger.debug("formal_export_prep_checklist entry")
    result = (
        "checked bridges stay separate from new prep candidates",
        "only stable-card rows become export-prep candidates",
        "candidate rows are prep-ready, not completed",
        "formalized flag remains false for every unexported candidate",
    )
    logger.debug("formal_export_prep_checklist exit count=%d", len(result))
    return result
