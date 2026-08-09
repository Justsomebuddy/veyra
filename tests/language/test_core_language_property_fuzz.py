from src.core.language_fuzz import (
    property_fuzz_language_checklist,
    property_language_fuzz_report,
    property_language_mutation_cases,
    run_language_mutation_case,
    run_property_language_fuzz,
    shrink_language_mutation_case,
)


def test_property_fuzz_catalog_is_seeded_and_balanced():
    first = property_language_mutation_cases()
    second = property_language_mutation_cases()
    assert first == second
    assert len(first) == 24
    assert {case.category for case in first} == {
        "property-arity",
        "property-constructor",
        "property-observer",
        "property-label",
    }


def test_property_fuzz_results_match_expected_statuses():
    results = run_property_language_fuzz()
    assert all(result.ok for result in results)
    assert {result.actual_status for result in results} == {"blocked", "unknown"}


def test_property_observer_family_has_unknown_and_blocked_cases():
    results = run_property_language_fuzz()
    observer = [result.actual_status for result in results if result.category == "property-observer"]
    assert observer.count("unknown") == 3
    assert observer.count("blocked") == 3


def test_property_shrinker_preserves_expected_status():
    cases = property_language_mutation_cases()
    shrunk = [shrink_language_mutation_case(case) for case in cases]
    results = [run_language_mutation_case(case) for case in shrunk]
    assert all(result.ok for result in results)
    assert all(len(s.source) <= len(c.source) or s.expected_status == "unknown" for c, s in zip(cases, shrunk))


def test_property_fuzz_report_contract():
    report = property_language_fuzz_report()
    assert report.seed == 613
    assert report.families == 4
    assert report.cases == 24
    assert report.blocked == 21
    assert report.unknown == 3
    assert report.ready == 0
    assert report.unexpected == 0
    assert report.shrunk == 24


def test_property_fuzz_language_checklist_v06():
    assert property_fuzz_language_checklist() == (
        "seeded-generator",
        "four-property-families",
        "expected-status-oracle",
        "proof-trace-property-runner",
        "deterministic-shrinker",
        "property-fuzz-report",
    )
