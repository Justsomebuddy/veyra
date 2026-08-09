from src.core.language_span_coverage import (
    missed_span_diagnostic_rules,
    run_span_diagnostic_coverage,
    span_diagnostic_cases,
    span_diagnostic_coverage_checklist,
    span_diagnostic_coverage_report,
)


def test_span_diagnostic_case_catalog_contract():
    cases = span_diagnostic_cases()
    assert len(cases) == 7
    assert [case.name for case in cases] == [
        "missing-close",
        "trailing-source",
        "empty-label",
        "bad-label-char",
        "missing-name",
        "newline-close",
        "comma-hole",
    ]


def test_span_diagnostic_results_match_exact_fields():
    results = run_span_diagnostic_coverage()
    assert all(result.ok for result in results)
    assert {result.message for result in results} == {"unexpected token", "trailing source"}
    assert all(result.has_excerpt for result in results)


def test_span_diagnostic_line_and_column_coverage():
    results = {result.name: result for result in run_span_diagnostic_coverage()}
    assert results["missing-name"].line == 1
    assert results["missing-name"].column == 1
    assert results["newline-close"].line == 2
    assert results["newline-close"].column == 14


def test_span_diagnostic_report_contract():
    report = span_diagnostic_coverage_report()
    assert report.cases == 7
    assert report.diagnostics == 7
    assert report.excerpts == 7
    assert report.multiline == 1
    assert report.unexpected == 0
    assert report.missed == 0


def test_missed_span_diagnostic_rules_empty():
    assert missed_span_diagnostic_rules() == ()


def test_span_diagnostic_coverage_checklist_v08():
    assert span_diagnostic_coverage_checklist() == (
        "missing-close",
        "trailing-source",
        "atom-label",
        "constructor-name",
        "multiline-span",
        "diagnostic-excerpt",
    )
