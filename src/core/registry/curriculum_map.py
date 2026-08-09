"""School-core curriculum map for Veyra theorem-card coverage."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .theorem_registry import TheoremSpec, all_theorem_specs

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurriculumNode:
    """A school concept bucket with Veyra coverage metadata."""

    concept_id: str
    title: str
    domain: str
    grade_band: str
    definitions: tuple[str, ...]
    theorem_ids: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class CurriculumEdge:
    """Directed curriculum dependency edge between concept buckets."""

    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class CurriculumGap:
    """Missing or partially covered curriculum concept."""

    concept_id: str
    reason: str
    missing_theorems: tuple[str, ...]


@dataclass(frozen=True)
class DomainCoverage:
    """Coverage count for one curriculum domain."""

    domain: str
    covered: int
    total: int


@dataclass(frozen=True)
class CurriculumSummary:
    """Compact curriculum-map health summary."""

    concepts: int
    edges: int
    covered: int
    missing: int
    sage_rows: int


def school_curriculum_nodes() -> tuple[CurriculumNode, ...]:
    """Return current school-core concept coverage nodes."""
    logger.debug("school_curriculum_nodes entry")
    result = (
        CurriculumNode("arithmetic-ratios", "Arithmetic and rational shadows", "arithmetic", "1-7", ("DEF-047", "DEF-049", "DEF-050"), (), "covered"),
        CurriculumNode("linear-equations", "Linear equations", "algebra", "6-9", ("DEF-055", "DEF-056", "DEF-057"), ("linear-equation-solution",), "covered"),
        CurriculumNode("polynomials", "Polynomial forms", "algebra", "7-11", ("DEF-058",), ("polynomial-identity", "polynomial-evaluation"), "covered"),
        CurriculumNode("combinatorics", "Finite counting and binomial choices", "combinatorics", "5-11", ("DEF-116", "DEF-117"), ("binomial-symmetry",), "covered"),
        CurriculumNode("functions", "Mode transformers", "functions", "7-11", ("DEF-059", "DEF-063"), (), "covered"),
        CurriculumNode("analysis-seeds", "Continuity, drift, and area", "analysis", "10-11", ("DEF-072", "DEF-075"), ("sampled-continuity", "drift-stability", "area-additivity"), "covered"),
        CurriculumNode("geometry-events", "Event/corridor geometry", "geometry", "5-11", ("DEF-076", "DEF-085"), ("pythagorean-separation", "sss-triangle", "sas-triangle", "line-shell-intersection", "plane-relabel-composition"), "covered"),
        CurriculumNode("proof-registry", "Theorem-card registry", "proof", "8-11", ("DEF-086", "DEF-095"), (), "covered"),
        CurriculumNode("trigonometry", "Trigonometric shells and cyclic angle measures", "geometry", "8-11", ("DEF-106", "DEF-108"), ("cyclic-period", "chord-symmetry"), "covered"),
        CurriculumNode("probability", "Probability and random observers", "probability", "7-11", ("DEF-109", "DEF-111", "DEF-118", "DEF-119"), ("probability-complement", "probability-union", "probability-independence"), "covered"),
        CurriculumNode("statistics", "Statistics, distributions, and inference", "statistics", "7-11", ("DEF-112", "DEF-114", "DEF-120"), ("mean-balance", "variance-shift"), "covered"),
    )
    logger.debug("school_curriculum_nodes exit count=%d", len(result))
    return result


def curriculum_edges() -> tuple[CurriculumEdge, ...]:
    """Return current school-core dependency edges."""
    logger.debug("curriculum_edges entry")
    result = (
        CurriculumEdge("arithmetic-ratios", "linear-equations", "enables"),
        CurriculumEdge("arithmetic-ratios", "polynomials", "enables"),
        CurriculumEdge("arithmetic-ratios", "combinatorics", "counts"),
        CurriculumEdge("polynomials", "functions", "models"),
        CurriculumEdge("functions", "analysis-seeds", "refines"),
        CurriculumEdge("arithmetic-ratios", "geometry-events", "coordinates"),
        CurriculumEdge("geometry-events", "trigonometry", "cyclic-extension"),
        CurriculumEdge("linear-equations", "proof-registry", "certifies"),
        CurriculumEdge("geometry-events", "proof-registry", "certifies"),
        CurriculumEdge("analysis-seeds", "proof-registry", "certifies"),
        CurriculumEdge("combinatorics", "probability", "finite-sample-space"),
        CurriculumEdge("probability", "statistics", "observer-foundation"),
    )
    logger.debug("curriculum_edges exit count=%d", len(result))
    return result


def missing_curriculum_concepts(nodes: tuple[CurriculumNode, ...], specs: dict[str, TheoremSpec]) -> tuple[CurriculumGap, ...]:
    """Return missing concepts or nodes with absent theorem specs."""
    logger.debug("missing_curriculum_concepts entry nodes=%d specs=%d", len(nodes), len(specs))
    gaps = []
    for node in nodes:
        missing_ids = tuple(theorem_id for theorem_id in node.theorem_ids if theorem_id not in specs)
        if node.status != "covered" or missing_ids:
            reason = node.status if node.status != "covered" else "missing-theorem-spec"
            gaps.append(CurriculumGap(node.concept_id, reason, missing_ids))
    result = tuple(gaps)
    logger.debug("missing_curriculum_concepts exit count=%d", len(result))
    return result


def domain_coverage(nodes: tuple[CurriculumNode, ...]) -> tuple[DomainCoverage, ...]:
    """Return coverage counts by domain."""
    logger.debug("domain_coverage entry nodes=%d", len(nodes))
    domains = sorted({node.domain for node in nodes})
    rows = []
    for domain in domains:
        subset = [node for node in nodes if node.domain == domain]
        rows.append(DomainCoverage(domain, sum(1 for node in subset if node.status == "covered"), len(subset)))
    result = tuple(rows)
    logger.debug("domain_coverage exit domains=%d", len(result))
    return result


def sage_export_rows(nodes: tuple[CurriculumNode, ...], specs: dict[str, TheoremSpec]) -> tuple[tuple[str, str, str, str], ...]:
    """Return rows `(concept, domain, theorem_id, sage_hook)` for Sage export."""
    logger.debug("sage_export_rows entry nodes=%d", len(nodes))
    rows = []
    for node in nodes:
        for theorem_id in node.theorem_ids:
            if theorem_id in specs:
                rows.append((node.concept_id, node.domain, theorem_id, specs[theorem_id].sage_hook))
    result = tuple(rows)
    logger.debug("sage_export_rows exit rows=%d", len(result))
    return result


def curriculum_summary(nodes: tuple[CurriculumNode, ...] | None = None, specs: dict[str, TheoremSpec] | None = None) -> CurriculumSummary:
    """Return compact curriculum coverage summary."""
    logger.debug("curriculum_summary entry")
    actual_nodes = nodes or school_curriculum_nodes()
    actual_specs = specs or all_theorem_specs()
    gaps = missing_curriculum_concepts(actual_nodes, actual_specs)
    rows = sage_export_rows(actual_nodes, actual_specs)
    result = CurriculumSummary(len(actual_nodes), len(curriculum_edges()), sum(1 for node in actual_nodes if node.status == "covered"), len(gaps), len(rows))
    logger.debug("curriculum_summary exit concepts=%d missing=%d", result.concepts, result.missing)
    return result
