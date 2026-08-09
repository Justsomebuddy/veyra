"""Topic-level school replacement rows after Core Language v0.8."""

from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchoolTopicCoverage:
    """One topic row with native/shadow/example/counterexample coverage."""

    topic_id: str
    domain: str
    native_definition: str
    school_shadow: str
    example: str
    counterexample: str
    test_path: str
    sage_row: str
    status: str
    required_primitives: tuple[str, ...]


def school_topic_coverage_rows() -> tuple[SchoolTopicCoverage, ...]:
    """Return topic-level native/shadow/example/counterexample coverage rows."""
    logger.debug("school_topic_coverage_rows entry")
    result = (
        SchoolTopicCoverage(
            "arithmetic-ratios", "arithmetic",
            "balances and ratio modes with integer/rational shadows",
            "integer arithmetic, fractions, and proportional reasoning",
            "ratio_from_ints(1, 2) + ratio_from_ints(1, 3)",
            "zero denominator or unmatched balance scale is rejected",
            "tests/shadows/test_balance_ratio.py", "facade:VeyraRatios", "covered",
            ("balance", "ratio", "shadow"),
        ),
        SchoolTopicCoverage(
            "linear-equations", "algebra", "linear obstruction solver over ratio shadows",
            "one-variable school linear equations", "2x + 3 = 11 gives x = 4",
            "zero coefficient with inconsistent constant blocks the card",
            "tests/shadows/test_equation.py", "algebra.linear_solution", "covered",
            ("ratio", "linear-form", "obstruction"),
        ),
        SchoolTopicCoverage(
            "polynomials", "algebra", "polynomial ratio forms and native factor hits",
            "identities, evaluation, roots, and factors", "(x - 1)(x + 1) evaluates as x^2 - 1",
            "a claimed root with nonzero residual is blocked", "tests/shadows/test_polynomial.py",
            "algebra.polynomial_identity", "covered", ("polynomial", "ratio", "factor-hit"),
        ),
        SchoolTopicCoverage(
            "combinatorics", "combinatorics", "finite choice echoes and binomial symmetry",
            "factorials, combinations, and symmetric counting", "choose_echo(5, 2) equals choose_echo(5, 3)",
            "negative or overlarge choice indices are invalid", "tests/registry/test_depth_packs.py",
            "combinatorics.binomial_symmetry", "covered", ("finite-choice", "factorial-echo"),
        ),
        SchoolTopicCoverage(
            "functions", "functions", "mode transformers with typed Core Language shadows",
            "function input/output tables and composition", "compose_transformers(f, g) acts on a mode",
            "domain/kind mismatch blocks inference", "tests/shadows/test_transformer.py",
            "facade:VeyraLanguageLab", "covered", ("mode", "transformer", "kind"),
        ),
        SchoolTopicCoverage(
            "analysis-seeds", "analysis", "sampled continuity, drift quotient, and finite area certificate",
            "limits, continuity, derivatives, and area seeds", "area_additivity_card splits a finite interval",
            "jump discontinuity blocks sampled-continuity witness", "tests/shadows/test_change.py",
            "analysis.sampled_continuity", "covered", ("completion", "drift", "area"),
        ),
        SchoolTopicCoverage(
            "geometry-events", "geometry", "events, corridors, shells, congruence, and relabels",
            "distance, triangles, congruence, lines, and planes", "pythagorean_card checks squared separation",
            "nonmatching triangle signature blocks congruence", "tests/geometry/test_geometry_theorems.py",
            "geometry.pythagorean", "covered", ("event", "corridor", "shell", "relabel"),
        ),
        SchoolTopicCoverage(
            "proof-registry", "proof", "theorem cards with dependency and Sage-hook gates",
            "school theorem statements with explicit prerequisites", "registry_summary reports 19 Sage-ready cards",
            "missing dependency prevents stable export", "tests/registry/test_theorem_registry.py",
            "facade:VeyraProofGraph", "covered", ("theorem-card", "dependency-edge", "proof-check"),
        ),
        SchoolTopicCoverage(
            "trigonometry", "geometry", "cyclic phase and chord symmetry over shell geometry",
            "unit-circle periods and chord symmetry", "phase_period_card verifies cyclic period",
            "noncyclic phase witness blocks period claim", "tests/numbers/test_cyclic_probability_stats.py",
            "trig.cyclic_period", "covered", ("cyclic-phase", "shell", "chord"),
        ),
        SchoolTopicCoverage(
            "probability", "probability", "finite weighted observers and event coverage laws",
            "finite probability, complement, union, independence",
            "probability_union_card checks inclusion/exclusion", "dependent events block independence claim",
            "tests/registry/test_depth_packs.py", "probability.union", "covered",
            ("finite-distribution", "weighted-outcome", "observer"),
        ),
        SchoolTopicCoverage(
            "statistics", "statistics", "sample echoes, mean balance, and variance shift",
            "mean, variance, distributions, and first inference shadows",
            "variance_shift_card is invariant under translation", "empty sample blocks mean/variance rows",
            "tests/registry/test_depth_packs.py", "statistics.variance_shift", "covered",
            ("sample-echo", "mean-balance", "variance"),
        ),
        SchoolTopicCoverage(
            "trigonometry-identities", "geometry", "cyclic shell algebra for angle-composition identities",
            "sin/cos identities, inverse trig, and equation solving",
            "rational unit phase plus sum/double/inverse identity cards are executable",
            "transcendental sine/cosine evaluation remains outside this rational seed",
            "tests/shadows/test_trigonometry_identities.py", "trig.identity_seed", "seeded",
            ("angle-composition", "inverse-phase", "identity-normal-form"),
        ),
        SchoolTopicCoverage(
            "calculus-depth", "analysis", "local/global observer coherence for derivative and integral laws",
            "derivative rules, integral rules, and fundamental theorem shadows",
            "local-linearization plus product/chain/integral cards are executable",
            "full transcendental calculus remains outside this polynomial shadow pack",
            "tests/shadows/test_calculus_depth.py", "analysis.calculus_depth", "seeded",
            ("limit-algebra", "local-linearization", "integral-coherence"),
        ),
        SchoolTopicCoverage(
            "statistics-inference", "statistics",
            "distribution-family observer with sampling uncertainty certificates",
            "confidence intervals, hypothesis tests, and likelihood shadows",
            "mean interval plus hypothesis and uncertainty cards are executable",
            "concentration bounds and likelihood geometry remain future work",
            "tests/shadows/test_statistics_inference.py", "statistics.inference_seed", "seeded",
            ("distribution-family", "sampling-law", "uncertainty-certificate"),
        ),
        SchoolTopicCoverage(
            "vectors-matrices", "linear-algebra",
            "mode arrays with linear-transform and determinant/eigen shadows",
            "vectors, matrices, systems, determinants, and eigenvectors",
            "matrix-vector action plus determinant/eigen cards are executable",
            "higher-dimensional spectral theory remains outside this 2x2 seed",
            "tests/shadows/test_linear_algebra_seed.py", "linear_algebra.matrix_seed", "seeded",
            ("vector-mode", "matrix-transformer", "determinant-shadow"),
        ),
    )
    logger.debug("school_topic_coverage_rows exit count=%d", len(result))
    return result


def school_topic_gap_rows(rows: tuple[SchoolTopicCoverage, ...] | None = None) -> tuple[SchoolTopicCoverage, ...]:
    """Return seeded/gap topic rows that still need deeper school replacement."""
    logger.debug("school_topic_gap_rows entry")
    actual_rows = rows or school_topic_coverage_rows()
    result = tuple(row for row in actual_rows if row.status != "covered")
    logger.debug("school_topic_gap_rows exit count=%d", len(result))
    return result
