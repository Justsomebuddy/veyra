"""Source-span diagnostic coverage for the Veyra Core Language parser."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .span import diagnostic_excerpt, parse_veyra_spanned
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class VeyraSpanDiagnosticCase:
    """One parser diagnostic coverage case."""
    name: str
    source: str
    expected: str
    found: str
    message: str
    line: int
    column: int
@dataclass(frozen=True)
class VeyraSpanDiagnosticResult:
    """Result of checking one span diagnostic."""
    name: str
    ok: bool
    expected: str
    found: str
    message: str
    line: int
    column: int
    has_excerpt: bool
@dataclass(frozen=True)
class VeyraSpanCoverageReport:
    """Aggregate source-span diagnostic coverage report."""
    cases: int
    diagnostics: int
    excerpts: int
    multiline: int
    unexpected: int
    missed: int

def span_diagnostic_cases() -> tuple[VeyraSpanDiagnosticCase, ...]:
    """Return deterministic source-span diagnostic coverage cases."""
    logger.debug("span_diagnostic_cases entry")
    result = (
        VeyraSpanDiagnosticCase("missing-close", "echo(nod:a,nod:b,observer:length", "')'", "EOF", "unexpected token", 1, 33),
        VeyraSpanDiagnosticCase("trailing-source", "nod:a nod:b", "EOF", "NAME", "trailing source", 1, 7),
        VeyraSpanDiagnosticCase("empty-label", "nod:", "atom label", "EOF", "unexpected token", 1, 5),
        VeyraSpanDiagnosticCase("bad-label-char", "nod:!", "atom label", "!", "unexpected token", 1, 5),
        VeyraSpanDiagnosticCase("missing-name", "!", "constructor name", "!", "unexpected token", 1, 1),
        VeyraSpanDiagnosticCase("newline-close", "echo(\n  nod:a,nod:b", "')'", "EOF", "unexpected token", 2, 14),
        VeyraSpanDiagnosticCase("comma-hole", "echo(nod:a,)", "constructor name", "RPAREN", "unexpected token", 1, 12),
    )
    logger.debug("span_diagnostic_cases exit count=%d", len(result))
    return result

def run_span_diagnostic_case(case: VeyraSpanDiagnosticCase) -> VeyraSpanDiagnosticResult:
    """Run one diagnostic case and compare exact source-span fields."""
    logger.debug("run_span_diagnostic_case entry case=%r", case)
    parsed = parse_veyra_spanned(case.source)
    diagnostic = parsed.diagnostic
    excerpt = diagnostic_excerpt(case.source, diagnostic) if diagnostic else ""
    ok = diagnostic is not None and not parsed.ok and diagnostic.expected == case.expected and diagnostic.found == case.found and diagnostic.message == case.message and diagnostic.span.line == case.line and diagnostic.span.column == case.column and "^" in excerpt
    result = VeyraSpanDiagnosticResult(case.name, ok, diagnostic.expected if diagnostic else "", diagnostic.found if diagnostic else "", diagnostic.message if diagnostic else "", diagnostic.span.line if diagnostic else 0, diagnostic.span.column if diagnostic else 0, "^" in excerpt)
    logger.debug("run_span_diagnostic_case exit result=%r", result)
    return result

def run_span_diagnostic_coverage() -> tuple[VeyraSpanDiagnosticResult, ...]:
    """Run all source-span diagnostic coverage cases."""
    logger.debug("run_span_diagnostic_coverage entry")
    result = tuple(run_span_diagnostic_case(case) for case in span_diagnostic_cases())
    logger.debug("run_span_diagnostic_coverage exit count=%d unexpected=%d", len(result), sum(not item.ok for item in result))
    return result

def missed_span_diagnostic_rules() -> tuple[str, ...]:
    """Return diagnostic cases whose expected fields were missed."""
    logger.debug("missed_span_diagnostic_rules entry")
    result = tuple(item.name for item in run_span_diagnostic_coverage() if not item.ok)
    logger.debug("missed_span_diagnostic_rules exit missed=%r", result)
    return result

def span_diagnostic_coverage_report() -> VeyraSpanCoverageReport:
    """Return aggregate source-span diagnostic coverage counts."""
    logger.debug("span_diagnostic_coverage_report entry")
    cases = span_diagnostic_cases()
    results = run_span_diagnostic_coverage()
    report = VeyraSpanCoverageReport(len(cases), sum(item.message != "" for item in results), sum(item.has_excerpt for item in results), sum("\n" in case.source for case in cases), sum(not item.ok for item in results), len(missed_span_diagnostic_rules()))
    logger.debug("span_diagnostic_coverage_report exit report=%r", report)
    return report

def span_diagnostic_coverage_checklist() -> tuple[str, ...]:
    """Return v0.8 source-span diagnostic coverage capabilities."""
    logger.debug("span_diagnostic_coverage_checklist entry")
    result = ("missing-close", "trailing-source", "atom-label", "constructor-name", "multiline-span", "diagnostic-excerpt")
    logger.debug("span_diagnostic_coverage_checklist exit count=%d", len(result))
    return result
