"""Coverage matrix for Core Language mutation pressure."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .fuzz import property_language_fuzz_report, run_generated_language_mutations, run_language_mutations, run_property_language_fuzz
logger = logging.getLogger(__name__)
EXPECTED_COVERAGE_FAMILIES = (
    "grammar", "typing", "inference",
    "arity", "constructor", "observer", "label",
    "property-arity", "property-constructor", "property-observer", "property-label",
)
@dataclass(frozen=True)
class VeyraCoverageCell:
    """One mutation-family coverage row."""
    family: str
    cases: int
    blocked: int
    unknown: int
    ready: int
    unexpected: int
@dataclass(frozen=True)
class VeyraCoverageReport:
    """Aggregate language-coverage report."""
    families: int
    cases: int
    blocked: int
    unknown: int
    ready: int
    unexpected: int
    missed: int
    shrink_witnesses: int

def _all_language_mutation_results():
    """Return all fixed/generated/property language mutation results."""
    logger.debug("_all_language_mutation_results entry")
    result = run_language_mutations() + run_generated_language_mutations() + run_property_language_fuzz()
    logger.debug("_all_language_mutation_results exit count=%d", len(result))
    return result

def language_coverage_matrix() -> tuple[VeyraCoverageCell, ...]:
    """Return one coverage row per expected mutation family."""
    logger.debug("language_coverage_matrix entry")
    results = _all_language_mutation_results()
    cells: list[VeyraCoverageCell] = []
    for family in EXPECTED_COVERAGE_FAMILIES:
        subset = [item for item in results if item.category == family]
        statuses = [item.actual_status for item in subset]
        cells.append(VeyraCoverageCell(family, len(subset), statuses.count("blocked"), statuses.count("unknown"), statuses.count("ready"), sum(not item.ok for item in subset)))
    final = tuple(cells)
    logger.debug("language_coverage_matrix exit families=%d cases=%d", len(final), sum(cell.cases for cell in final))
    return final

def missed_language_coverage_rules() -> tuple[str, ...]:
    """Return expected families with no mutation coverage."""
    logger.debug("missed_language_coverage_rules entry")
    result = tuple(cell.family for cell in language_coverage_matrix() if cell.cases == 0)
    logger.debug("missed_language_coverage_rules exit missed=%r", result)
    return result

def language_coverage_report() -> VeyraCoverageReport:
    """Return aggregate coverage counts across all mutation layers."""
    logger.debug("language_coverage_report entry")
    cells = language_coverage_matrix()
    missed = tuple(cell for cell in cells if cell.cases == 0)
    shrink_witnesses = property_language_fuzz_report().shrunk
    report = VeyraCoverageReport(
        len(cells), sum(cell.cases for cell in cells), sum(cell.blocked for cell in cells),
        sum(cell.unknown for cell in cells), sum(cell.ready for cell in cells),
        sum(cell.unexpected for cell in cells), len(missed), shrink_witnesses,
    )
    logger.debug("language_coverage_report exit report=%r", report)
    return report

def coverage_language_checklist() -> tuple[str, ...]:
    """Return v0.7 coverage-matrix capabilities."""
    logger.debug("coverage_language_checklist entry")
    result = ("fixed-catalog", "generated-families", "property-fuzz-families", "coverage-matrix", "missed-rule-report", "shrink-witness-count")
    logger.debug("coverage_language_checklist exit count=%d", len(result))
    return result
