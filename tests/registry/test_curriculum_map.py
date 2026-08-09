from src.core.curriculum_map import curriculum_edges, curriculum_summary, domain_coverage, missing_curriculum_concepts, sage_export_rows, school_curriculum_nodes
from src.core.curriculum_topics import SchoolTopicCoverage, school_topic_coverage_rows, school_topic_gap_rows
from src.core.theorem_registry import all_theorem_specs


def test_curriculum_summary_counts_current_school_core():
    summary = curriculum_summary()
    assert summary.concepts == 11
    assert summary.covered == 11
    assert summary.missing == 0
    assert summary.sage_rows == 19


def test_curriculum_edges_include_cross_domain_path():
    edges = curriculum_edges()
    assert ("arithmetic-ratios", "linear-equations", "enables") in tuple((e.source, e.target, e.relation) for e in edges)
    assert ("functions", "analysis-seeds", "refines") in tuple((e.source, e.target, e.relation) for e in edges)


def test_missing_curriculum_detector_is_empty_after_gap_closure():
    gaps = missing_curriculum_concepts(school_curriculum_nodes(), all_theorem_specs())
    assert gaps == ()


def test_domain_coverage_and_sage_export_rows():
    nodes = school_curriculum_nodes()
    coverage = {row.domain: (row.covered, row.total) for row in domain_coverage(nodes)}
    assert coverage["algebra"] == (2, 2)
    assert coverage["combinatorics"] == (1, 1)
    assert coverage["geometry"] == (2, 2)
    assert coverage["probability"] == (1, 1)
    assert coverage["statistics"] == (1, 1)
    rows = sage_export_rows(nodes, all_theorem_specs())
    assert ("linear-equations", "algebra", "linear-equation-solution", "algebra.linear_solution") in rows
    assert ("geometry-events", "geometry", "pythagorean-separation", "geometry.pythagorean") in rows
    assert ("probability", "probability", "probability-complement", "probability.complement") in rows
    assert ("statistics", "statistics", "mean-balance", "statistics.mean_balance") in rows
    assert ("combinatorics", "combinatorics", "binomial-symmetry", "combinatorics.binomial_symmetry") in rows
    assert ("probability", "probability", "probability-union", "probability.union") in rows
    assert ("statistics", "statistics", "variance-shift", "statistics.variance_shift") in rows


def test_school_topic_coverage_rows_record_v08_native_shadow_contract():
    rows = school_topic_coverage_rows()
    by_id = {row.topic_id: row for row in rows}
    assert isinstance(rows[0], SchoolTopicCoverage)
    assert len(rows) == 15
    assert by_id["functions"].sage_row == "facade:VeyraLanguageLab"
    assert by_id["proof-registry"].status == "covered"
    for row in rows:
        assert row.native_definition
        assert row.school_shadow
        assert row.example
        assert row.counterexample
        assert row.test_path
        assert row.sage_row
        assert row.required_primitives


def test_school_topic_gap_rows_mark_remaining_school_to_11_work():
    gaps = school_topic_gap_rows()
    by_id = {row.topic_id: row for row in gaps}
    assert set(by_id) == {"trigonometry-identities", "calculus-depth", "statistics-inference", "vectors-matrices"}
    assert by_id["calculus-depth"].status == "seeded"
    assert by_id["calculus-depth"].test_path == "tests/shadows/test_calculus_depth.py"
    assert by_id["trigonometry-identities"].test_path == "tests/shadows/test_trigonometry_identities.py"
    assert by_id["vectors-matrices"].status == "seeded"
    assert by_id["vectors-matrices"].test_path == "tests/shadows/test_linear_algebra_seed.py"
    assert by_id["vectors-matrices"].required_primitives == ("vector-mode", "matrix-transformer", "determinant-shadow")
    assert by_id["statistics-inference"].status == "seeded"
    assert by_id["statistics-inference"].test_path == "tests/shadows/test_statistics_inference.py"
