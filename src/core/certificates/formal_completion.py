"""Certificate for X8 checked formal-export completion."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..formal.completion import (
    completed_formal_export_rows,
    formal_export_completion_checklist,
    formal_export_completion_summary,
)

logger = logging.getLogger(__name__)

def certify_formal_export_completion_x8() -> Certificate:
    """Certify prep-ready stable theorem cards have checked Lean artifacts."""
    logger.debug("certify_formal_export_completion_x8 entry")
    rows = completed_formal_export_rows()
    by_id = {row.theorem_id: row for row in rows}
    summary = formal_export_completion_summary()
    cyclic = by_id.get("cyclic-period")
    pythagorean = by_id.get("pythagorean-separation")
    poly_identity = by_id.get("polynomial-identity")
    poly_eval = by_id.get("polynomial-evaluation")
    linear = by_id.get("linear-equation-solution")
    probability = by_id.get("probability-complement")
    probability_union = by_id.get("probability-union")
    probability_independence = by_id.get("probability-independence")
    mean_balance = by_id.get("mean-balance")
    binomial = by_id.get("binomial-symmetry")
    variance = by_id.get("variance-shift")
    sss = by_id.get("sss-triangle")
    sas = by_id.get("sas-triangle")
    shell = by_id.get("line-shell-intersection")
    relabel = by_id.get("plane-relabel-composition")
    final_rows = tuple(by_id.get(theorem_id) for theorem_id in (
        "sampled-continuity", "drift-stability", "area-additivity", "chord-symmetry",
    ))
    final_symbols = (
        "THM_A004_sampled_continuity_double_0_five_points",
        "THM_A005_square_symmetric_drift_3_steps_1_2_3",
        "THM_A006_identity_midpoint_area_4_4_8",
        "THM_C002_chord_symmetry_12_0_3_9",
    )
    passed = (
        cyclic is not None and cyclic.backend == "Lean"
        and cyclic.export_status == "completed" and cyclic.lean_status == "checked" and cyclic.formalized
        and pythagorean is not None and pythagorean.backend == "Lean"
        and pythagorean.export_status == "completed" and pythagorean.lean_status == "checked" and pythagorean.formalized
        and poly_identity is not None and poly_identity.backend == "Lean"
        and poly_identity.export_status == "completed" and poly_identity.lean_status == "checked"
        and poly_identity.formalized
        and poly_eval is not None and poly_eval.backend == "Lean"
        and poly_eval.export_status == "completed" and poly_eval.lean_status == "checked" and poly_eval.formalized
        and linear is not None and linear.backend == "Lean"
        and linear.export_status == "completed" and linear.lean_status == "checked" and linear.formalized
        and probability is not None and probability.backend == "Lean"
        and probability.export_status == "completed" and probability.lean_status == "checked"
        and probability.formalized
        and probability_union is not None and probability_union.backend == "Lean"
        and probability_union.export_status == "completed" and probability_union.lean_status == "checked"
        and probability_union.formalized and probability_union.lean_symbol == "THM_P002_probability_union_counts"
        and probability_independence is not None and probability_independence.backend == "Lean"
        and probability_independence.export_status == "completed" and probability_independence.lean_status == "checked"
        and probability_independence.formalized
        and probability_independence.lean_symbol == "THM_P003_probability_independence_counts"
        and mean_balance is not None and mean_balance.backend == "Lean"
        and mean_balance.export_status == "completed" and mean_balance.lean_status == "checked"
        and mean_balance.formalized and mean_balance.lean_symbol == "THM_S001_mean_balance_1_3_5"
        and binomial is not None and binomial.backend == "Lean"
        and binomial.export_status == "completed" and binomial.lean_status == "checked"
        and binomial.formalized and binomial.lean_symbol == "THM_B001_binomial_symmetry_6_2"
        and variance is not None and variance.backend == "Lean"
        and variance.export_status == "completed" and variance.lean_status == "checked"
        and variance.formalized and variance.lean_symbol == "THM_S002_variance_shift_1_3_5_plus_10"
        and all(row is not None and row.backend == "Lean" for row in (sss, sas, shell, relabel))
        and sss is not None and sss.export_status == "completed" and sss.lean_status == "checked"
        and sss.formalized and sss.lean_symbol == "THM_G002_sss_side_squares_shift_10"
        and sas is not None and sas.export_status == "completed" and sas.lean_status == "checked"
        and sas.formalized and sas.lean_symbol == "THM_G003_sas_anchor_3_4_dot_0"
        and shell is not None and shell.export_status == "completed" and shell.lean_status == "checked"
        and shell.formalized and shell.lean_symbol == "THM_G004_diameter_shell_scaled_roots"
        and relabel is not None and relabel.export_status == "completed" and relabel.lean_status == "checked"
        and relabel.formalized and relabel.lean_symbol == "THM_G005_quarter_turn_after_translation"
        and all(
            row is not None and row.backend == "Lean" and row.export_status == "completed"
            and row.lean_status == "checked" and row.formalized and row.lean_symbol == symbol
            for row, symbol in zip(final_rows, final_symbols, strict=True)
        )
        and all(row.artifact_digest_status == "matched" for row in rows)
        and summary["candidate_total"] == 19 and summary["completed_candidates"] == 19
        and summary["checked_lean_files"] == 6 and summary["formalized_candidates"] == 19
        and summary["remaining_prep_ready"] == 0 and summary["overclaims"] == 0
        and len(formal_export_completion_checklist()) == 4
    )
    detail = (
        f"completed={summary['completed_candidates']} remaining={summary['remaining_prep_ready']} "
        f"lean={summary['checked_lean_files']}"
    )
    result = Certificate(
        "formal_export_completion_x8",
        "checked Lean proof artifacts for prep-ready theorem-card candidates",
        passed,
        detail,
        1,
    )
    logger.debug("certify_formal_export_completion_x8 exit result=%r", result)
    return result
