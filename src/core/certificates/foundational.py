"""Certificate for F1-F3 foundational repair artifacts."""
from __future__ import annotations
import logging
from ..kernel.axiom_kernel import axiom_kernel_checklist, axiom_kernel_report
from ..certify_types import Certificate
from ..formal.bridge import check_lean_echo_export, echo_reflexive_certificate, formal_bridge_checklist
from ..formal.native_bridge import intrinsic_arithmetic_lean_status, native_formal_bridge_report
from ..registry.theorem_language import check_theorem_statement, default_theorem_environments, parse_theorem_statement, theorem_language_checklist, theorem_obligation_rows
logger = logging.getLogger(__name__)

def certify_foundational_repair_f1_f3() -> Certificate:
    """Certify unified axioms, theorem statements, obligations, and Lean bridge."""
    logger.debug("certify_foundational_repair_f1_f3 entry")
    kernel = axiom_kernel_report()
    statement = parse_theorem_statement("theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))")
    theorem = check_theorem_statement(statement, default_theorem_environments()[:2])
    blocked_rows = [row for row in theorem_obligation_rows() if row.status == "blocked"]
    internal = echo_reflexive_certificate()
    lean = check_lean_echo_export()
    native_lean = native_formal_bridge_report()
    arithmetic_lean = intrinsic_arithmetic_lean_status()
    passed = kernel.ready and theorem.status == "ready" and blocked_rows and internal.status == "checked" and lean.status == "checked" and native_lean.status == "checked" and arithmetic_lean == "checked" and len(native_lean.theorem_ids) == 7 and len(axiom_kernel_checklist()) == 6 and len(theorem_language_checklist()) == 7 and len(formal_bridge_checklist()) == 5
    detail = f"axioms={len(kernel.axioms)} layers={len(kernel.layers)} obligations={len(theorem.obligations)} lean={lean.status} native_lean={native_lean.status} arithmetic_lean={arithmetic_lean}"
    result = Certificate("foundational_repair_f1_f3", "receipt-derived witness axiom kernel, theorem obligations, checked Lean bridge, and checked native Lean semantics", passed, detail, 1)
    logger.debug("certify_foundational_repair_f1_f3 exit result=%r", result)
    return result
