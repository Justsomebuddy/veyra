"""Proof discipline coverage for Veyra rule/span/domain/model/export readiness."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from collections.abc import Iterable
from ..language import interpret_veyra
from ..language.proof import trace_veyra_proof
from .theorem_registry import all_theorem_specs, missing_dependencies
logger = logging.getLogger(__name__)
DEFAULT_PROOF_SOURCES = (
    "echo(nod:a,nod:b,observer:kind)",
    "echo(nod:a,nod:b,observer:trace)",
    "echo(nod:a,nod:b,observer:alien)",
    "shell(echo(nod:a,nod:b,observer:kind),echo(nod:a,nod:b,observer:trace))",
    "echo(nod:a,nod:b,observer:kind",
)
@dataclass(frozen=True)
class RuleCoverageCell:
    """Coverage row for one proof rule over chosen source expressions."""
    rule: str
    count: int
    ready: int
    blocked: int
    unknown: int
    spans: int
@dataclass(frozen=True)
class SemanticDomainRow:
    """One explicit human-domain shadow certificate covered by the core interpreter."""
    domain: str
    source: str
    status: str
    keys: tuple[str, ...]
    required_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    counter_source: str
    counter_status: str
    certificate: str
@dataclass(frozen=True)
class PrimitiveModelNote:
    """Small consistency/model note for one primitive family."""
    name: str
    primitive: str
    model: str
    consistency: str
    witness: str
    status: str
@dataclass(frozen=True)
class StableExportRow:
    """Formal-prover export candidate gated to stable theorem cards only."""
    theorem_id: str
    title: str
    hook: str
    dependencies: tuple[str, ...]
    export_status: str

def proof_rule_coverage(sources: Iterable[str] = DEFAULT_PROOF_SOURCES) -> tuple[RuleCoverageCell, ...]:
    """Aggregate proof-step status and source-span coverage by rule name."""
    logger.debug("proof_rule_coverage entry")
    table: dict[str, list[int]] = {}
    for source in sources:
        trace = trace_veyra_proof(source)
        for step in trace.steps:
            row = table.setdefault(step.rule, [0, 0, 0, 0, 0])
            row[0] += 1; row[1] += step.output_status == "ready"; row[2] += step.output_status == "blocked"
            row[3] += step.output_status == "unknown"; row[4] += step.span.end > step.span.start
    result = tuple(RuleCoverageCell(rule, *counts) for rule, counts in sorted(table.items()))
    logger.debug("proof_rule_coverage exit count=%d", len(result))
    return result

def proof_rule_coverage_summary(sources: Iterable[str] = DEFAULT_PROOF_SOURCES) -> dict[str, int]:
    """Return compact rule/span coverage counters."""
    logger.debug("proof_rule_coverage_summary entry")
    rows = proof_rule_coverage(sources)
    result = {"rules": len(rows), "steps": sum(r.count for r in rows), "ready": sum(r.ready for r in rows), "blocked": sum(r.blocked for r in rows), "unknown": sum(r.unknown for r in rows), "spans": sum(r.spans for r in rows), "blocked_rules": sum(r.blocked > 0 for r in rows)}
    logger.debug("proof_rule_coverage_summary exit result=%r", result)
    return result

def semantic_domain_coverage() -> tuple[SemanticDomainRow, ...]:
    """Cover declared semantic shadows with required keys and counterexamples."""
    logger.debug("semantic_domain_coverage entry")
    mode = "mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))"; bad = f"echo({mode},mode(breath(tact(nod:c,nod:b),tact(nod:b,nod:c))),observer:trace)"
    specs = (("arithmetic", mode, ("length",)), ("geometry", mode, ("boundary",)), ("logic", "echo(nod:a,nod:b,observer:kind)", ("status",)), ("analysis", mode, ("length", "variation")), ("topology", mode, ("component_count", "deformation_class")), ("probability", mode, ("sample_space", "sample_size")), ("statistics", mode, ("sample_size", "support_size")))
    rows = []
    for domain, source, required in specs:
        interp = interpret_veyra(source, domain); counter = interpret_veyra(bad, domain); keys = tuple(sorted(interp.semantic)); missing = tuple(k for k in required if k not in keys)
        cert = "declared-shadow" if interp.check.status == "ready" and counter.check.status == "blocked" and not missing else "hold"
        rows.append(SemanticDomainRow(domain, source, interp.check.status, keys, required, missing, bad, counter.check.status, cert))
    result = tuple(rows)
    logger.debug("semantic_domain_coverage exit count=%d", len(result))
    return result

def primitive_model_notes() -> tuple[PrimitiveModelNote, ...]:
    """Return model/consistency notes for stable Veyra primitive families."""
    logger.debug("primitive_model_notes entry")
    rows = (
        ("rez", "residue", "null/distinction residue token", "accepted only by atom/type rules", "expr_kind(rez:x)", "model-noted"),
        ("nod", "event node", "residue-labelled event point", "tact requires exactly two nods", "tact(nod:a,nod:b)", "model-noted"),
        ("tact", "directed contact", "ordered two-nod transfer", "breath accepts only tact rows", "breath(tact(...))", "model-noted"),
        ("breath/mode", "finite flow", "closed list of contacts then modal wrapper", "mode has one breath child", "mode(breath(...))", "model-noted"),
        ("echo", "observer sameness", "relation over two objects and observer", "status is ready/blocked/unknown", "infer.echo", "model-noted"),
        ("obstruction", "negative proof object", "blocked outcome is first-class", "parse/type/infer failures are retained", "grammar.parse", "model-noted"),
        ("shadow", "domain projection", "external math enters by named shadow", "domain keys are explicit", "semantic_shadow", "model-noted"),
        ("cycle-echo", "native number", "cyclic primitive count surface", "periodic equivalence is executable", "cycle_echo", "model-noted"),
        ("balance/ratio", "signed scale", "arising/fading over denominator scale", "raw shadows match Fraction tests", "ratio_shadow", "model-noted"),
        ("compression", "structural cost", "edit/tree/factor strategy comparison", "cost rows are tested by certificate", "compression_algebra", "model-noted"),
    )
    result = tuple(PrimitiveModelNote(*row) for row in rows)
    logger.debug("primitive_model_notes exit count=%d", len(result))
    return result

def stable_formal_export_rows() -> tuple[StableExportRow, ...]:
    """Return only stable theorem cards eligible for later formal-prover export."""
    logger.debug("stable_formal_export_rows entry")
    rows = []
    for spec in all_theorem_specs().values():
        missing = missing_dependencies(spec)
        status = "stable-card-only" if spec.sage_hook != "pending" and not missing else "hold"
        if status == "stable-card-only":
            rows.append(StableExportRow(spec.theorem_id, spec.title, spec.sage_hook, spec.dependencies, status))
    result = tuple(rows)
    logger.debug("stable_formal_export_rows exit count=%d", len(result))
    return result

def proof_discipline_summary() -> dict[str, int]:
    """Return the proof-discipline readiness summary."""
    logger.debug("proof_discipline_summary entry")
    rules = proof_rule_coverage_summary(); domains = semantic_domain_coverage(); models = primitive_model_notes(); exports = stable_formal_export_rows()
    result = {"rules": rules["rules"], "steps": rules["steps"], "blocked_rules": rules["blocked_rules"], "domains": len(domains), "domain_certs": sum(r.certificate == "declared-shadow" for r in domains), "models": len(models), "exports": len(exports)}
    logger.debug("proof_discipline_summary exit result=%r", result)
    return result

def proof_discipline_checklist() -> tuple[str, ...]:
    """Return Sprint F proof-discipline closure checklist."""
    logger.debug("proof_discipline_checklist entry")
    result = ("rule/source-span coverage", "semantic shadow certificates", "primitive model/consistency notes", "stable-card formal-export gate")
    logger.debug("proof_discipline_checklist exit count=%d", len(result))
    return result
