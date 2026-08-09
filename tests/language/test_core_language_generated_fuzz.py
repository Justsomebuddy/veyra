from src.core.language_fuzz import (
    generated_language_mutation_cases,
    generated_language_mutation_report,
    generated_mutation_language_checklist,
    run_generated_language_mutations,
)


def test_generated_mutation_catalog_has_four_families():
    cases = generated_language_mutation_cases()
    assert len(cases) == 20
    assert {case.category for case in cases} == {"arity", "constructor", "observer", "label"}


def test_generated_mutations_all_match_expected_status():
    results = run_generated_language_mutations()
    assert all(result.ok for result in results)
    assert {result.actual_status for result in results} == {"blocked", "unknown"}


def test_generated_arity_constructor_label_are_blocked():
    results = run_generated_language_mutations()
    blocked_families = {"arity", "constructor", "label"}
    selected = [result for result in results if result.category in blocked_families]
    assert len(selected) == 16
    assert all(result.actual_status == "blocked" for result in selected)


def test_generated_observer_family_splits_blocked_and_unknown():
    results = run_generated_language_mutations()
    statuses = {result.name: result.actual_status for result in results if result.category == "observer"}
    assert statuses == {
        "unknown-aura": "unknown",
        "unknown-phase": "unknown",
        "trace-label-block": "blocked",
        "boundary-block": "blocked",
    }


def test_generated_mutation_report_counts_family_surface():
    report = generated_language_mutation_report()
    assert report.families == 4
    assert report.cases == 20
    assert report.blocked == 18
    assert report.unknown == 2
    assert report.ready == 0
    assert report.unexpected == 0


def test_generated_mutation_language_checklist_v05():
    assert generated_mutation_language_checklist() == (
        "arity-family",
        "constructor-family",
        "observer-family",
        "label-family",
        "proof-trace-family-runner",
        "family-report",
    )
