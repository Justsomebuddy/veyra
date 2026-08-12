"""Certificate and digest-bound Lean evidence for finite G4 atlas gluing."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import logging
from pathlib import Path

from .certify_types import Certificate
from .formal_export_catalog import check_captured_lean_artifact, declares_lean_theorem
from .observer_patch_atlas import (
    exact_gluing_criterion,
    exact_gluing_relation,
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
    triangle_counterexample,
)
from .observer_patch_gluing_classification import disjoint_singleton_nonuniqueness
from .paths import repository_path

logger = logging.getLogger(__name__)

G4_LEAN_SHA256 = "6e0b011f61c8f6093973efe61577aac82b2848564ea87675fdfdd5fe5f07038c"
G4_LEAN_SYMBOLS = (
    "THM_G4_001_exact_gluing_exists_iff_no_local_contradiction",
    "THM_G4_002_triangle_singleton_overlaps_pass",
    "THM_G4_003_triangle_exact_gluing_impossible",
)
G4_LEAN_HELPER_SYMBOLS = (
    "g4_generated_pair_coverage_unique_exact_gluing",
    "g4_disjoint_singletons_exact_gluing_not_unique",
)


@dataclass(frozen=True)
class ObserverPatchLeanEvidence:
    """Digest, symbol, captured-compile, and continuity status for G4 Lean."""

    proof_path: str
    expected_sha256: str
    actual_sha256: str
    digest_status: str
    lean_status: str
    symbols: tuple[str, ...]
    symbols_exact: bool
    helper_symbols: tuple[str, ...]
    helpers_exact: bool
    continuous: bool


def lean_observer_patch_atlas_path() -> Path:
    """Return the canonical G4 Lean artifact path."""
    logger.debug("lean_observer_patch_atlas_path entry")
    result = Path("proofs/lean/VeyraObserverPatchAtlas.lean")
    logger.debug("lean_observer_patch_atlas_path exit result=%s", result)
    return result


def observer_patch_atlas_lean_evidence() -> ObserverPatchLeanEvidence:
    """Check the canonical digest-bound G4 Lean artifact."""
    logger.debug("observer_patch_atlas_lean_evidence entry")
    result = _observer_patch_lean_evidence_at(lean_observer_patch_atlas_path())
    logger.debug("observer_patch_atlas_lean_evidence exit status=%s", result.lean_status)
    return result


def certify_observer_patch_atlas_g4() -> Certificate:
    """Certify exact, blocked, and nonunique G4 cases plus Lean evidence."""
    logger.debug("certify_observer_patch_atlas_g4 entry")
    patches = (observer_patch("AB", ("a", "b")), observer_patch("BC", ("b", "c")))
    atlas = observer_patch_atlas(("a", "b", "c"), patches)
    sections = (
        local_observer_section(atlas, "AB", (("a", "b"),)),
        local_observer_section(atlas, "BC", (("b", "c"),)),
    )
    valid_criterion = exact_gluing_criterion(atlas, sections)
    valid_witness = exact_gluing_relation(atlas, sections)
    triangle = triangle_counterexample()
    nonunique = disjoint_singleton_nonuniqueness()
    lean = observer_patch_atlas_lean_evidence()
    triangle_row = triangle.contradictions[0] if len(triangle.contradictions) == 1 else None
    passed = (
        valid_witness is not None
        and valid_criterion.no_local_contradiction
        and valid_criterion.exact_gluing_exists
        and valid_criterion.iff_holds
        and len(triangle.overlaps) == 3
        and all(len(row.overlap) == 1 and row.compatible for row in triangle.overlaps)
        and triangle_row is not None
        and triangle_row.patch_name == "CA"
        and {triangle_row.left, triangle_row.right} == {"a", "c"}
        and not triangle.criterion.exact_gluing_exists
        and triangle.criterion.iff_holds
        and lean.digest_status == "matched"
        and lean.lean_status == "checked"
        and lean.symbols == G4_LEAN_SYMBOLS
        and lean.symbols_exact
        and lean.helper_symbols == G4_LEAN_HELPER_SYMBOLS
        and lean.helpers_exact
        and lean.continuous
        and nonunique.classification.direct_exact_gluing_count == 2
        and nonunique.classification.classification_holds
        and nonunique.classification.uniqueness_iff_conflict_complete
        and nonunique.both_exact
        and nonunique.distinct
    )
    detail = (
        f"valid_gluing={valid_witness is not None} triangle_obstructions="
        f"{len(triangle.contradictions)} nonunique={nonunique.classification.direct_exact_gluing_count} "
        f"lean={len(lean.symbols) if lean.symbols_exact else 0}/3 "
        f"helpers={len(lean.helper_symbols) if lean.helpers_exact else 0}/2"
    )
    result = Certificate(
        "observer_patch_atlas_g4",
        "finite observer-patch exact gluing, triangle obstruction, and nonuniqueness",
        passed,
        detail,
        1,
    )
    logger.debug("certify_observer_patch_atlas_g4 exit result=%r", result)
    return result


def _observer_patch_lean_evidence_at(
    proof_path: Path, expected_sha256: str = G4_LEAN_SHA256
) -> ObserverPatchLeanEvidence:
    logger.debug("_observer_patch_lean_evidence_at entry path=%s", proof_path)
    target = proof_path if proof_path.is_absolute() else repository_path(proof_path.as_posix())
    try:
        payload = target.read_bytes()
    except OSError as exc:
        logger.error("_observer_patch_lean_evidence_at read failed path=%s error=%s", proof_path, exc)
        return _blocked_evidence(proof_path, expected_sha256)
    actual = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256):
        logger.error("_observer_patch_lean_evidence_at digest mismatch actual=%s", actual)
        return _blocked_evidence(proof_path, expected_sha256, actual, "mismatch")
    text = payload.decode(errors="replace")
    symbols_exact = all(declares_lean_theorem(text, symbol) for symbol in G4_LEAN_SYMBOLS)
    helpers_exact = all(declares_lean_theorem(text, symbol) for symbol in G4_LEAN_HELPER_SYMBOLS)
    if not symbols_exact or not helpers_exact:
        logger.error("_observer_patch_lean_evidence_at exact symbol set missing path=%s", proof_path)
        return _blocked_evidence(proof_path, expected_sha256, actual, "matched")
    compiled = check_captured_lean_artifact(payload, expected_sha256)
    try:
        after = target.read_bytes()
    except OSError as exc:
        logger.error("_observer_patch_lean_evidence_at reread failed path=%s error=%s", proof_path, exc)
        after = b""
    continuous = payload == after and hmac.compare_digest(
        hashlib.sha256(after).hexdigest(), expected_sha256
    )
    if not continuous:
        logger.error("_observer_patch_lean_evidence_at continuity failure path=%s", proof_path)
    result = ObserverPatchLeanEvidence(
        str(proof_path), expected_sha256, actual, "matched",
        "checked" if compiled == "checked" and continuous else "blocked",
        G4_LEAN_SYMBOLS, symbols_exact, G4_LEAN_HELPER_SYMBOLS, helpers_exact, continuous,
    )
    logger.debug("_observer_patch_lean_evidence_at exit status=%s", result.lean_status)
    return result


def _blocked_evidence(
    path: Path, expected: str, actual: str = "", digest_status: str = "missing"
) -> ObserverPatchLeanEvidence:
    logger.debug("_blocked_evidence entry path=%s digest_status=%s", path, digest_status)
    result = ObserverPatchLeanEvidence(
        str(path), expected, actual, digest_status, "blocked", G4_LEAN_SYMBOLS, False,
        G4_LEAN_HELPER_SYMBOLS, False, False,
    )
    logger.debug("_blocked_evidence exit result=%r", result)
    return result
