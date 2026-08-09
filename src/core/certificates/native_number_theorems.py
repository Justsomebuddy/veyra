"""Certificate for native number-theorem pressure."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..numbers.native_number_theorems import native_euclid_mode_rows, native_euclid_rows, native_fermat_obstruction_rows, native_fermat_phase_rows, native_number_theorem_gaps, native_number_theorem_summary

logger = logging.getLogger(__name__)

def certify_native_number_theorem_n1() -> Certificate:
    """Certify the first Euclid-style native number-theorem shadow."""
    logger.debug("certify_native_number_theorem_n1 entry")
    rows = native_euclid_rows()
    native_rows = native_euclid_mode_rows()
    summary = native_number_theorem_summary()
    shadow_ok = all(all(r == 1 % p for r, p in zip(row.remainders, row.primes, strict=True)) for row in rows)
    native_ok = all(row.mode_lengths == row.periods and row.status == "derived" for row in native_rows)
    passed = (
        summary["rows"] == 3 and summary["certified"] == 3 and summary["native_rows"] == 3
        and summary["native_derived"] == 3 and summary["open_gaps"] >= 3 and summary["lean_f002"]
        and shadow_ok and native_ok and len(native_number_theorem_gaps()) == 3
    )
    detail = f"rows={summary['rows']} native={summary['native_derived']}/{summary['native_rows']} lean_f002={summary['lean_f002']} gaps={summary['open_gaps']}"
    result = Certificate(
        "native_number_theorem_n1",
        "Euclid-style product-plus-one theorem with native Mode-length derivation and Lean bridge",
        passed, detail, 1,
    )
    logger.debug("certify_native_number_theorem_n1 exit result=%r", result)
    return result

def certify_native_fermat_phase_n2() -> Certificate:
    """Certify finite prime-period Fermat phase rows from native observers."""
    logger.debug("certify_native_fermat_phase_n2 entry")
    rows = native_fermat_phase_rows()
    blocked = native_fermat_obstruction_rows()
    summary = native_number_theorem_summary()
    residues_ok = all(row.residues == tuple(1 for _ in row.unit_lengths) for row in rows)
    coverage_ok = all(row.coverage == row.unit_lengths for row in rows)
    passed = (
        summary["fermat_rows"] == 4 and summary["fermat_derived"] == 4
        and summary["fermat_units"] == 13 and summary["fermat_blocked"] == 3
        and residues_ok and coverage_ok and all(row.status == "blocked" for row in blocked)
    )
    detail = f"periods={summary['fermat_rows']} units={summary['fermat_units']} blocked={summary['fermat_blocked']}"
    result = Certificate(
        "native_fermat_phase_n2",
        "finite prime-period Fermat phase rows from native Mode/Breath length observers",
        passed, detail, 1,
    )
    logger.debug("certify_native_fermat_phase_n2 exit result=%r", result)
    return result
