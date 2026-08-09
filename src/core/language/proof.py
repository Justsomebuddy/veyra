"""Traceable Veyra Core Language proof objects."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from ..language import VeyraCheck, VeyraKind, expr_kind, infer_veyra, normal_text
from .span import SourceSpan, parse_veyra_spanned, span_to_plain
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class VeyraProofStep:
    """One checked inference step with source location."""
    rule: str
    span: SourceSpan
    input_kinds: tuple[str, ...]
    input_statuses: tuple[str, ...]
    output_kind: str
    output_status: str
    obstruction: str = ""
@dataclass(frozen=True)
class VeyraProofTrace:
    """Proof trace for one source expression."""
    source: str
    parse_ok: bool
    normal: str
    final_check: VeyraCheck
    steps: tuple[VeyraProofStep, ...]
    diagnostic: str = ""
@dataclass(frozen=True)
class VeyraProofSummary:
    """Compact counts for a proof trace."""
    steps: int
    ready: int
    blocked: int
    unknown: int
    final_status: str
def trace_veyra_proof(source: str) -> VeyraProofTrace:
    """Build source-spanned proof trace for a Veyra expression."""
    logger.debug("trace_veyra_proof entry source=%r", source)
    parsed = parse_veyra_spanned(source)
    if not parsed.ok or parsed.expr is None:
        diag = parsed.diagnostic
        span = diag.span if diag else SourceSpan(0, 0, 1, 1)
        msg = diag.message if diag else "parse failed"
        found = diag.found if diag else "unknown"
        step = VeyraProofStep("grammar.parse", span, (), (), "none", "blocked", f"{msg}: {found}")
        check = VeyraCheck(False, "blocked", None, step.obstruction)
        result = VeyraProofTrace(source, False, "", check, (step,), step.obstruction)
        logger.debug("trace_veyra_proof exit parse_blocked result=%r", result)
        return result
    plain = span_to_plain(parsed.expr)
    steps = tuple(_kind_steps(parsed.expr))
    final = infer_veyra(plain)
    relation_steps = tuple(_relation_steps(parsed.expr))
    result = VeyraProofTrace(source, True, normal_text(plain), final, steps + relation_steps, final.obstruction)
    logger.debug("trace_veyra_proof exit result=%r", result)
    return result
def _kind_steps(expr) -> list[VeyraProofStep]:
    """Return recursive assembly/type proof steps."""
    logger.debug("_kind_steps entry expr=%r", expr)
    steps: list[VeyraProofStep] = []
    child_checks: list[VeyraCheck] = []
    for child in expr.args:
        steps.extend(_kind_steps(child)); child_checks.append(expr_kind(span_to_plain(child)))
    check = expr_kind(span_to_plain(expr))
    step = VeyraProofStep(
        f"kind.{expr.head}", expr.span, tuple(_kind_name(c.kind) for c in child_checks),
        tuple(c.status for c in child_checks), _kind_name(check.kind), check.status, check.obstruction,
    )
    steps.append(step)
    logger.debug("_kind_steps exit count=%d last=%r", len(steps), step)
    return steps
def _relation_steps(expr) -> list[VeyraProofStep]:
    """Return recursive relation inference proof steps."""
    logger.debug("_relation_steps entry expr=%r", expr)
    steps: list[VeyraProofStep] = []
    for child in expr.args:
        steps.extend(_relation_steps(child))
    if expr.head in {"echo", "shell"}:
        child = tuple(infer_veyra(span_to_plain(arg)) for arg in expr.args)
        check = infer_veyra(span_to_plain(expr))
        steps.append(VeyraProofStep(
            f"infer.{expr.head}", expr.span, tuple(_kind_name(c.kind) for c in child),
            tuple(c.status for c in child), _kind_name(check.kind), check.status, check.obstruction,
        ))
    logger.debug("_relation_steps exit count=%d", len(steps))
    return steps
def _kind_name(kind: VeyraKind | None) -> str:
    """Render kind name for proof records."""
    logger.debug("_kind_name entry kind=%r", kind)
    result = "none" if kind is None else kind.value
    logger.debug("_kind_name exit result=%s", result)
    return result
def proof_summary(trace: VeyraProofTrace) -> VeyraProofSummary:
    """Summarize proof trace statuses."""
    logger.debug("proof_summary entry trace_steps=%d", len(trace.steps))
    statuses = [step.output_status for step in trace.steps]
    result = VeyraProofSummary(len(trace.steps), statuses.count("ready"), statuses.count("blocked"), statuses.count("unknown"), trace.final_check.status)
    logger.debug("proof_summary exit result=%r", result)
    return result
def proof_language_checklist() -> tuple[str, ...]:
    """Return v0.3 proof-object capabilities."""
    logger.debug("proof_language_checklist entry")
    result = ("rule-name", "source-span", "input-kinds", "input-statuses", "output-status", "obstruction", "trace-summary")
    logger.debug("proof_language_checklist exit count=%d", len(result))
    return result
