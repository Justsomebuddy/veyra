"""Theorem registry and dependency graph for Veyra proof cards."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class CardLike(Protocol):
    """Minimal shape shared by theorem and intersection cards."""

    status: str
    relation: str
    obstruction: str


@dataclass(frozen=True)
class TheoremSpec:
    """Registry specification for a Veyra theorem/check card."""

    theorem_id: str
    title: str
    claim: str
    dependencies: tuple[str, ...]
    success_relations: tuple[str, ...]
    obstruction_catalog: tuple[str, ...]
    sage_hook: str = "pending"


@dataclass(frozen=True)
class RegistryCheck:
    """Result of checking a theorem card against its spec and dependencies."""

    theorem_id: str
    status: str
    relation: str
    obstruction: str
    missing_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class RegistrySummary:
    """Small summary of theorem registry health."""

    total: int
    dependency_edges: int
    sage_ready: int


GEOMETRY_KNOWN_DEFS = frozenset(f"DEF-{i:03d}" for i in range(76, 91))
SCHOOL_KNOWN_DEFS = frozenset(f"DEF-{i:03d}" for i in range(55, 122))


def geometry_theorem_specs() -> dict[str, TheoremSpec]:
    """Return built-in geometry theorem-card registry specs."""
    logger.debug("geometry_theorem_specs entry")
    specs = {
        "pythagorean-separation": TheoremSpec(
            "pythagorean-separation", "Pythagorean separation", "right-apex dot zero implies separation decomposition",
            ("DEF-076", "DEF-078", "DEF-086", "DEF-087", "DEF-088"), ("proven",), ("none", "non-right-apex", "decomposition-mismatch"), "geometry.pythagorean",
        ),
        "sss-triangle": TheoremSpec(
            "sss-triangle", "SSS triangle card", "matching side echoes imply triangle congruence under chosen turn observer",
            ("DEF-076", "DEF-079", "DEF-082", "DEF-086"), ("congruent",), ("none", "side-mismatch", "turn-mismatch"), "geometry.sss",
        ),
        "sas-triangle": TheoremSpec(
            "sas-triangle", "SAS triangle card", "two side echoes plus included dot echo certify triangle congruence",
            ("DEF-076", "DEF-078", "DEF-079", "DEF-086", "DEF-087"), ("congruent",), ("none", "side-dot-mismatch", "turn-mismatch"), "geometry.sas",
        ),
        "line-shell-intersection": TheoremSpec(
            "line-shell-intersection", "Corridor-shell intersection", "solve corridor crossing of constant-separation shell by parameter certificate",
            ("DEF-077", "DEF-083", "DEF-086", "DEF-089"), ("two", "tangent", "degenerate-on"), ("none", "outside-segment", "no-real-crossing", "irrational-parameters", "completion-needed"), "geometry.line_shell",
        ),
        "plane-relabel-composition": TheoremSpec(
            "plane-relabel-composition", "Plane relabel composition", "composed plane relabel equals sequential relabel on event shadows",
            ("DEF-076", "DEF-085", "DEF-086", "DEF-090"), ("proven",), ("none", "shadow-mismatch"), "geometry.relabel_compose",
        ),
    }
    logger.debug("geometry_theorem_specs exit count=%d", len(specs))
    return specs


def algebra_analysis_theorem_specs() -> dict[str, TheoremSpec]:
    """Return algebra and analysis theorem-card registry specs."""
    logger.debug("algebra_analysis_theorem_specs entry")
    specs = {
        "linear-equation-solution": TheoremSpec(
            "linear-equation-solution", "Linear equation solution", "linear constraint yields unique, identity, or obstruction card",
            ("DEF-055", "DEF-056", "DEF-057", "DEF-086"), ("unique", "identity"), ("none", "parallel-obstruction", "residual-nonzero"), "algebra.linear_solution",
        ),
        "polynomial-identity": TheoremSpec(
            "polynomial-identity", "Polynomial identity", "coefficient echoes certify exact polynomial identity",
            ("DEF-058", "DEF-086"), ("identity",), ("none", "coefficient-mismatch"), "algebra.polynomial_identity",
        ),
        "polynomial-evaluation": TheoremSpec(
            "polynomial-evaluation", "Polynomial evaluation", "polynomial value at a ratio shadow matches expected echo",
            ("DEF-058", "DEF-086"), ("matches",), ("none", "value-mismatch"), "algebra.polynomial_eval",
        ),
        "sampled-continuity": TheoremSpec(
            "sampled-continuity", "Sampled continuity", "finite input tremor produces no output jump",
            ("DEF-072", "DEF-073", "DEF-086"), ("stable",), ("none", "echo-jump"), "analysis.sampled_continuity",
        ),
        "drift-stability": TheoremSpec(
            "drift-stability", "Drift stability", "drift quotients remain within tolerance across refinements",
            ("DEF-074", "DEF-086"), ("stable",), ("none", "drift-jump"), "analysis.drift_stability",
        ),
        "area-additivity": TheoremSpec(
            "area-additivity", "Area additivity", "finite area braid over adjacent intervals equals whole interval braid",
            ("DEF-075", "DEF-086"), ("additive",), ("none", "area-gap", "missing-area-value"), "analysis.area_additivity",
        ),
    }
    logger.debug("algebra_analysis_theorem_specs exit count=%d", len(specs))
    return specs


def cyclic_probability_statistics_theorem_specs() -> dict[str, TheoremSpec]:
    """Return cyclic/probability/statistics theorem-card registry specs."""
    logger.debug("cyclic_probability_statistics_theorem_specs entry")
    specs = {
        "cyclic-period": TheoremSpec(
            "cyclic-period", "Cyclic period", "advancing a phase by its modulus returns the same phase",
            ("DEF-106", "DEF-107", "DEF-086"), ("periodic",), ("none", "phase-mismatch"), "trig.cyclic_period",
        ),
        "chord-symmetry": TheoremSpec(
            "chord-symmetry", "Chord symmetry", "cyclic chord echo is symmetric around an anchor phase",
            ("DEF-106", "DEF-108", "DEF-086"), ("symmetric",), ("none", "chord-mismatch"), "trig.chord_symmetry",
        ),
        "probability-complement": TheoremSpec(
            "probability-complement", "Probability complement", "event and complement probabilities sum to one",
            ("DEF-109", "DEF-110", "DEF-111", "DEF-086"), ("complete",), ("none", "mass-gap"), "probability.complement",
        ),
        "mean-balance": TheoremSpec(
            "mean-balance", "Mean balance", "sample deviations from mean sum to zero",
            ("DEF-112", "DEF-113", "DEF-114", "DEF-086"), ("balanced",), ("none", "deviation-gap"), "statistics.mean_balance",
        ),
    }
    logger.debug("cyclic_probability_statistics_theorem_specs exit count=%d", len(specs))
    return specs


def depth_pack_theorem_specs() -> dict[str, TheoremSpec]:
    """Return depth-pack theorem-card registry specs."""
    logger.debug("depth_pack_theorem_specs entry")
    specs = {
        "binomial-symmetry": TheoremSpec(
            "binomial-symmetry", "Binomial symmetry", "choosing k equals choosing n-k",
            ("DEF-086", "DEF-116", "DEF-117"), ("symmetric",), ("none", "count-mismatch"), "combinatorics.binomial_symmetry",
        ),
        "probability-union": TheoremSpec(
            "probability-union", "Probability union", "finite union probability equals sum minus intersection",
            ("DEF-086", "DEF-109", "DEF-110", "DEF-118"), ("additive",), ("none", "union-gap"), "probability.union",
        ),
        "probability-independence": TheoremSpec(
            "probability-independence", "Probability independence", "finite events are independent when intersection probability equals product",
            ("DEF-086", "DEF-109", "DEF-110", "DEF-119"), ("independent",), ("none", "product-gap"), "probability.independence",
        ),
        "variance-shift": TheoremSpec(
            "variance-shift", "Variance shift", "sample variance is invariant under constant shifts",
            ("DEF-086", "DEF-112", "DEF-114", "DEF-120"), ("invariant",), ("none", "variance-gap"), "statistics.variance_shift",
        ),
    }
    logger.debug("depth_pack_theorem_specs exit count=%d", len(specs))
    return specs


def all_theorem_specs() -> dict[str, TheoremSpec]:
    """Return combined school-core theorem registry specs."""
    logger.debug("all_theorem_specs entry")
    result = geometry_theorem_specs() | algebra_analysis_theorem_specs() | cyclic_probability_statistics_theorem_specs() | depth_pack_theorem_specs()
    logger.debug("all_theorem_specs exit count=%d", len(result))
    return result


def dependency_edges(specs: dict[str, TheoremSpec]) -> tuple[tuple[str, str], ...]:
    """Return theorem-to-definition dependency edges."""
    logger.debug("dependency_edges entry count=%d", len(specs))
    result = tuple((spec.theorem_id, dep) for spec in specs.values() for dep in spec.dependencies)
    logger.debug("dependency_edges exit count=%d", len(result))
    return result


def missing_dependencies(spec: TheoremSpec, known_defs: frozenset[str] = SCHOOL_KNOWN_DEFS) -> tuple[str, ...]:
    """Return dependencies absent from the current definition registry."""
    logger.debug("missing_dependencies entry theorem=%s", spec.theorem_id)
    result = tuple(dep for dep in spec.dependencies if dep not in known_defs)
    logger.debug("missing_dependencies exit count=%d", len(result))
    return result


def check_card(spec: TheoremSpec, card: CardLike, known_defs: frozenset[str] = SCHOOL_KNOWN_DEFS) -> RegistryCheck:
    """Check a produced card against registry dependencies and success relations."""
    logger.debug("check_card entry theorem=%s relation=%s", spec.theorem_id, card.relation)
    missing = missing_dependencies(spec, known_defs)
    if missing:
        result = RegistryCheck(spec.theorem_id, "blocked", card.relation, "missing-dependencies", missing)
        logger.debug("check_card exit missing=%d", len(missing))
        return result
    ok = card.relation in spec.success_relations and card.obstruction in {"none", "completion-needed"}
    obstruction = "none" if ok else card.obstruction or "relation-mismatch"
    result = RegistryCheck(spec.theorem_id, "ready" if ok else "blocked", card.relation, obstruction, ())
    logger.debug("check_card exit status=%s obstruction=%s", result.status, result.obstruction)
    return result


def registry_summary(specs: dict[str, TheoremSpec]) -> RegistrySummary:
    """Return registry size/dependency/Sage readiness summary."""
    logger.debug("registry_summary entry count=%d", len(specs))
    hooks = sum(1 for spec in specs.values() if spec.sage_hook != "pending")
    result = RegistrySummary(len(specs), len(dependency_edges(specs)), hooks)
    logger.debug("registry_summary exit total=%d edges=%d", result.total, result.dependency_edges)
    return result


def spec_by_card_name(card_name: str, specs: dict[str, TheoremSpec] | None = None) -> TheoremSpec:
    """Return spec by executable card name."""
    logger.debug("spec_by_card_name entry card_name=%s", card_name)
    table = specs or all_theorem_specs()
    key = "line-shell-intersection" if card_name == "intersection" else card_name
    if key not in table:
        logger.error("spec_by_card_name unknown=%s", key)
        raise KeyError(key)
    result = table[key]
    logger.debug("spec_by_card_name exit theorem=%s", result.theorem_id)
    return result
