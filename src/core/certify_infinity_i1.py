"""Digest-bound certificate for bounded I1 prefix and residue evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import logging
from pathlib import Path
import re

from .certify_types import Certificate
from .formal_export_catalog import _strip_lean_comments, check_captured_lean_artifact
from .infinity_prefix import (
    first_prefix_obstruction,
    periodic_prefix_window,
    prefix_alphabet,
    prefix_coherence_report,
    prefix_tower_window,
)
from .infinity_prefix_types import PrefixRestrictionObstruction
from .padic_residue_tower import (
    add_padic_windows,
    first_padic_obstruction,
    integer_padic_window,
    multiply_padic_windows,
    padic_coherence_report,
    padic_residue_window,
    prime_base,
)
from .padic_residue_types import PadicCompatibilityObstruction
from .paths import repository_path

logger = logging.getLogger(__name__)

I1_LEAN_SHA256 = "7be8b425c0cefb243706d71d4774fa886df5ddb75c611cf6e2fb848930a75975"
I1_LEAN_SYMBOLS = (
    "THM_I1_001_prefix_tower_recovers_stream",
    "THM_I1_002_prefix_observers_determine_stream",
    "THM_I1_003_prefix_conflict_blocks_global_stream",
    "THM_I1_004_modular_addition_preserves_refinement",
)


@dataclass(frozen=True)
class ObserverInfinityLeanEvidence:
    """Digest, symbols, captured compile, and reread continuity for I1 Lean."""

    proof_path: str
    expected_sha256: str
    actual_sha256: str
    digest_status: str
    lean_status: str
    symbols: tuple[str, ...]
    symbols_exact: bool
    continuous: bool


def lean_coherent_towers_path() -> Path:
    """Return the canonical project-relative I1 Lean artifact path."""
    logger.debug("lean_coherent_towers_path entry")
    result = Path("proofs/lean/VeyraCoherentTowers.lean")
    logger.debug("lean_coherent_towers_path exit result=%s", result)
    return result


def observer_infinity_lean_evidence() -> ObserverInfinityLeanEvidence:
    """Check the digest-bound all-depth Lean schema without Python promotion."""
    logger.debug("observer_infinity_lean_evidence entry")
    result = _observer_infinity_lean_evidence_at(lean_coherent_towers_path())
    logger.debug("observer_infinity_lean_evidence exit status=%s", result.lean_status)
    return result


def certify_observer_infinity_i1() -> Certificate:
    """Certify finite windows plus the separately hypothesized Lean schema."""
    logger.debug("certify_observer_infinity_i1 entry")
    alphabet = prefix_alphabet(("a", "b"))
    periodic = periodic_prefix_window(alphabet, ("a", "b"), 6)
    broken_prefix = prefix_tower_window(
        alphabet, ((), ("a",), ("a", "b"), ("b", "b", "a"))
    )
    base = prime_base(5)
    coherent = padic_residue_window(base, (2, 7, 57, 307))
    broken_residue = padic_residue_window(base, (2, 8, 57))
    left = integer_padic_window(base, 307, 4)
    right = integer_padic_window(base, 18, 4)
    added = add_padic_windows(left, right)
    multiplied = multiply_padic_windows(left, right)
    lean = observer_infinity_lean_evidence()
    prefix_obstruction = first_prefix_obstruction(broken_prefix)
    residue_obstruction = first_padic_obstruction(broken_residue)
    prefix_report = prefix_coherence_report(periodic)
    residue_report = padic_coherence_report(coherent)
    passed = (
        prefix_report.coherent
        and prefix_report.scope == "finite-window"
        and prefix_report.checked_links == 6
        and prefix_obstruction == PrefixRestrictionObstruction(2, 3, 0, "a", "b")
        and residue_report.coherent
        and residue_report.scope == "finite-prime-power-window"
        and residue_report.checked_links == 3
        and residue_obstruction == PadicCompatibilityObstruction(0, 1, 2, 3)
        and tuple(stage.residue for stage in added.stages) == (0, 0, 75, 325)
        and tuple(stage.residue for stage in multiplied.stages) == (1, 1, 26, 526)
        and lean.digest_status == "matched"
        and lean.lean_status == "checked"
        and lean.symbols == I1_LEAN_SYMBOLS
        and lean.symbols_exact
        and lean.continuous
    )
    detail = (
        f"prefix_depth={len(periodic.stages) - 1} p5_levels={len(coherent.stages)} "
        f"obstructions=2 lean={len(lean.symbols) if lean.symbols_exact else 0}/4"
    )
    result = Certificate(
        "observer_infinity_i1",
        "finite prefix coherence and classical p-adic residue shadows with an all-depth Lean hypothesis",
        passed,
        detail,
        1,
    )
    logger.debug("certify_observer_infinity_i1 exit result=%r", result)
    return result


def _observer_infinity_lean_evidence_at(
    proof_path: Path, expected_sha256: str = I1_LEAN_SHA256
) -> ObserverInfinityLeanEvidence:
    logger.debug("_observer_infinity_lean_evidence_at entry path=%s", proof_path)
    target = proof_path if proof_path.is_absolute() else repository_path(proof_path.as_posix())
    try:
        payload = target.read_bytes()
    except OSError as exc:
        logger.error("_observer_infinity_lean_evidence_at read failed error=%s", exc)
        return _blocked_evidence(proof_path, expected_sha256)
    actual = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256):
        logger.error("_observer_infinity_lean_evidence_at digest mismatch actual=%s", actual)
        return _blocked_evidence(proof_path, expected_sha256, actual, "mismatch")
    text = payload.decode(errors="replace")
    declared_symbols = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_I1_[A-Za-z0-9_]+)(?=[ \t:(])",
        _strip_lean_comments(text),
    ))
    symbols_exact = declared_symbols == I1_LEAN_SYMBOLS
    if not symbols_exact:
        logger.error("_observer_infinity_lean_evidence_at symbol set missing")
        return _blocked_evidence(proof_path, expected_sha256, actual, "matched")
    compiled = check_captured_lean_artifact(payload, expected_sha256)
    try:
        after = target.read_bytes()
    except OSError as exc:
        logger.error("_observer_infinity_lean_evidence_at reread failed error=%s", exc)
        after = b""
    continuous = payload == after and hmac.compare_digest(
        hashlib.sha256(after).hexdigest(), expected_sha256
    )
    result = ObserverInfinityLeanEvidence(
        str(proof_path), expected_sha256, actual, "matched",
        "checked" if compiled == "checked" and continuous else "blocked",
        I1_LEAN_SYMBOLS, symbols_exact, continuous,
    )
    logger.debug("_observer_infinity_lean_evidence_at exit status=%s", result.lean_status)
    return result


def _blocked_evidence(
    path: Path, expected: str, actual: str = "", digest_status: str = "missing"
) -> ObserverInfinityLeanEvidence:
    logger.debug("_blocked_evidence entry path=%s digest_status=%s", path, digest_status)
    result = ObserverInfinityLeanEvidence(
        str(path), expected, actual, digest_status, "blocked", I1_LEAN_SYMBOLS, False, False
    )
    logger.debug("_blocked_evidence exit status=%s", result.lean_status)
    return result
