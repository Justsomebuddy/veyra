from src.core.language_coverage import (
    EXPECTED_COVERAGE_FAMILIES,
    coverage_language_checklist,
    language_coverage_matrix,
    language_coverage_report,
    missed_language_coverage_rules,
)


def test_language_coverage_matrix_has_expected_family_order():
    matrix = language_coverage_matrix()
    assert tuple(cell.family for cell in matrix) == EXPECTED_COVERAGE_FAMILIES
    assert len(matrix) == 11


def test_language_coverage_matrix_counts_all_mutation_layers():
    matrix = language_coverage_matrix()
    by_family = {cell.family: cell for cell in matrix}
    assert by_family["grammar"].cases == 4
    assert by_family["typing"].cases == 4
    assert by_family["inference"].cases == 2
    assert by_family["arity"].cases == 8
    assert by_family["constructor"].cases == 4
    assert by_family["observer"].cases == 4
    assert by_family["label"].cases == 4
    assert by_family["property-observer"].cases == 6


def test_language_coverage_matrix_status_totals():
    matrix = language_coverage_matrix()
    assert sum(cell.cases for cell in matrix) == 54
    assert sum(cell.blocked for cell in matrix) == 48
    assert sum(cell.unknown for cell in matrix) == 6
    assert sum(cell.ready for cell in matrix) == 0
    assert sum(cell.unexpected for cell in matrix) == 0


def test_language_coverage_report_contract():
    report = language_coverage_report()
    assert report.families == 11
    assert report.cases == 54
    assert report.blocked == 48
    assert report.unknown == 6
    assert report.ready == 0
    assert report.unexpected == 0
    assert report.missed == 0
    assert report.shrink_witnesses == 24


def test_missed_language_coverage_rules_empty_when_all_families_hit():
    assert missed_language_coverage_rules() == ()


def test_coverage_language_checklist_v07():
    assert coverage_language_checklist() == (
        "fixed-catalog",
        "generated-families",
        "property-fuzz-families",
        "coverage-matrix",
        "missed-rule-report",
        "shrink-witness-count",
    )
