"""Optimizer-specific gates for the VAM reference certificate."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from vam.src import (
    check_lean_optimizer_export,
    optimizer_prepost_witness_payload,
    optimizer_prepost_witness_summary,
    optimizer_proof_payload,
    optimizer_proof_summary,
)

logger = logging.getLogger(__name__)

EXPECTED_LOCAL_LAWS = (
    "observer-alias.lookup-invariant",
    "compress-alias.same-pair-local-law",
    "compress-idempotent.same-observer-local-law",
    "compress-idempotent.visible-use-observer-local-law",
    "compress-idempotent.different-observer-reject-local-law",
    "compress-idempotent.obstruction-boundary-reject-local-law",
    "dead-shadow.unused-lookup-local-law",
)
EXPECTED_PASSES = ("observer-alias", "compress-alias", "compress-idempotent", "dead-shadow")


@dataclass(frozen=True)
class VamOptimizerGate:
    """Combined VAM optimizer proof/prepost certificate gate state."""

    proof_bridge_ok: bool
    prepost_ok: bool
    lean_status: str
    proof_docs_ok: bool
    prepost_docs_ok: bool
    checked_local_laws: tuple[str, ...]
    prepost_accepted_rows: int
    prepost_safe_equivalence_rows: int
    detail: str


def certify_vam_optimizer_gate(root: Path) -> VamOptimizerGate:
    """Check VAM optimizer proof-bridge and executable pre/post witness gates."""
    logger.debug("certify_vam_optimizer_gate entry root=%s", root)
    optimizer_lean = check_lean_optimizer_export(root / "proofs/lean/VeyraOptimizer.lean")
    optimizer_proofs = optimizer_proof_payload(optimizer_lean.status)
    proof_summary = optimizer_proof_summary(lean_status=optimizer_lean.status)
    proof_docs_ok = _optimizer_proof_docs_ok(root)
    proof_bridge_ok = _optimizer_proof_bridge_ok(
        optimizer_proofs,
        proof_summary,
        optimizer_lean.status,
        proof_docs_ok,
    )
    prepost_rows = optimizer_prepost_witness_payload()
    prepost_summary = optimizer_prepost_witness_summary()
    prepost_docs_ok = _optimizer_prepost_docs_ok(root)
    prepost_ok = _optimizer_prepost_ok(prepost_rows, prepost_summary, proof_summary.checked_local_laws, prepost_docs_ok)
    result = VamOptimizerGate(
        proof_bridge_ok=proof_bridge_ok,
        prepost_ok=prepost_ok,
        lean_status=optimizer_lean.status,
        proof_docs_ok=proof_docs_ok,
        prepost_docs_ok=prepost_docs_ok,
        checked_local_laws=proof_summary.checked_local_laws,
        prepost_accepted_rows=int(prepost_summary["accepted_rows"]),
        prepost_safe_equivalence_rows=int(prepost_summary["safe_equivalence_rows"]),
        detail=(
            f"optimizer_proof_bridge={proof_bridge_ok}/{optimizer_lean.status}/"
            f"{proof_summary.checked_local_laws}/{proof_docs_ok} "
            f"optimizer_prepost={prepost_ok}/{prepost_summary['accepted_rows']}/"
            f"{prepost_summary['safe_equivalence_rows']}"
        ),
    )
    logger.debug("certify_vam_optimizer_gate exit result=%r", result)
    return result


def _optimizer_proof_docs_ok(root: Path) -> bool:
    logger.debug("optimizer_proof_docs_ok entry root=%s", root)
    required = (
        "tests/vam/test_vam_optimizer_proofs.py",
        "tests/vam/test_vam_optimizer_formal_bridge.py",
        "vam/docs/028_vam_v2_0_optimizer_proof_semantics_first_slice.md",
        "vam/docs/029_vam_v2_1_compress_idempotent_same_observer_local_law.md",
        "vam/docs/030_vam_v2_2_compress_alias_same_pair_local_law.md",
        "vam/docs/031_vam_v2_3_dead_shadow_unused_lookup_local_law.md",
        "vam/docs/034_vam_v2_6_compress_idempotent_reject_law.md",
        "vam/docs/035_vam_v2_7_obstruction_boundary_reject_law.md",
        "vam/docs/036_vam_v2_9_visible_use_observer_law.md",
    )
    result = all((root / path).exists() for path in required)
    logger.debug("optimizer_proof_docs_ok exit ok=%s", result)
    return result


def _optimizer_prepost_docs_ok(root: Path) -> bool:
    logger.debug("optimizer_prepost_docs_ok entry root=%s", root)
    required = (
        "tests/vam/test_vam_optimizer_prepost.py",
        "vam/docs/032_vam_v2_4_optimizer_prepost_witnesses.md",
        "vam/docs/034_vam_v2_6_compress_idempotent_reject_law.md",
        "vam/docs/035_vam_v2_7_obstruction_boundary_reject_law.md",
        "vam/docs/036_vam_v2_9_visible_use_observer_law.md",
    )
    result = all((root / path).exists() for path in required)
    logger.debug("optimizer_prepost_docs_ok exit ok=%s", result)
    return result


def _optimizer_prepost_ok(
    rows: tuple[dict[str, str], ...],
    summary: dict[str, object],
    checked_local_laws: tuple[str, ...],
    docs_ok: bool,
) -> bool:
    logger.debug("optimizer_prepost_ok entry rows=%d docs=%s", len(rows), docs_ok)
    result = (
        docs_ok
        and summary["boundary"] == "optimizer-prepost-witness"
        and summary["claim"] == "executable-prepost-witness-not-proof"
        and (summary["total_rows"], summary["accepted_rows"], summary["safe_equivalence_rows"]) == (7, 5, 7)
        and summary["local_laws"] == checked_local_laws
        and all(
            row["precondition_status"] == "witnessed"
            and row["postcondition_status"] == "preserved"
            and row["equivalence_status"] == "equivalent"
            and row["boundary"] == "optimizer-prepost-witness"
            and row["claim"] == "executable-prepost-witness-not-proof"
            for row in rows
        )
    )
    logger.debug("optimizer_prepost_ok exit ok=%s", result)
    return result


def _optimizer_proof_bridge_ok(
    rows: tuple[dict[str, str], ...],
    summary,
    lean_status: str,
    docs_ok: bool,
) -> bool:
    logger.debug("optimizer_proof_bridge_ok entry rows=%d lean=%s docs=%s", len(rows), lean_status, docs_ok)
    integrated = lean_status == "checked"
    result = (
        len(rows) == 7
        and summary.boundary == "optimizer-proof-bridge"
        and summary.claim == "checked-local-laws-not-full-correctness"
        and summary.checked_local_laws == EXPECTED_LOCAL_LAWS
        and summary.obligation_only_rows == 0
        and summary.obligation_backed_passes == EXPECTED_PASSES
        and {row["pass_name"] for row in rows if row["formal_status"] == "obligation-only"} == set()
        and rows[1]["formal_status"] == "lean-checked-local-law"
        and rows[1]["lean_symbol"] == "Veyra.compressAlias_samePair_local_law"
        and "same source/observer alias law only" in rows[1]["evidence_scope"]
        and rows[2]["formal_status"] == "lean-checked-local-law"
        and rows[2]["lean_symbol"] == "Veyra.compressIdempotent_sameObserver_local_law"
        and rows[3]["formal_status"] == "lean-checked-local-law"
        and rows[3]["lean_symbol"] == "Veyra.compressIdempotent_visibleUseObserver_local_law"
        and "visible-use observer preservation law only" in rows[3]["evidence_scope"]
        and rows[4]["formal_status"] == "lean-checked-local-law"
        and rows[4]["lean_symbol"] == "Veyra.compressIdempotent_differentObserver_reject_local_law"
        and "different-observer rejection law only" in rows[4]["evidence_scope"]
        and rows[5]["formal_status"] == "lean-checked-local-law"
        and rows[5]["lean_symbol"] == "Veyra.compressIdempotent_obstructionBoundary_reject_local_law"
        and "obstruction-boundary rejection law only" in rows[5]["evidence_scope"]
        and rows[6]["formal_status"] == "lean-checked-local-law"
        and rows[6]["lean_symbol"] == "Veyra.deadShadow_unusedLookup_local_law"
        and "unused-shadow lookup/drop law only" in rows[6]["evidence_scope"]
        and "pass remains obligation-backed" in rows[1]["evidence_scope"]
        and "pass remains obligation-backed" in rows[2]["evidence_scope"]
        and "pass remains obligation-backed" in rows[3]["evidence_scope"]
        and "pass remains obligation-backed" in rows[4]["evidence_scope"]
        and "pass remains obligation-backed" in rows[5]["evidence_scope"]
        and all(row["boundary"] == "optimizer-proof-bridge" for row in rows)
        and all(row["claim"] == "checked-local-laws-not-full-correctness" for row in rows)
        and integrated
        and (not integrated or docs_ok)
    )
    logger.debug("optimizer_proof_bridge_ok exit ok=%s", result)
    return result
