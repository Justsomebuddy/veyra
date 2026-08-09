from src.core.language_fuzz import (
    language_mutation_cases,
    language_mutation_report,
    mutation_language_checklist,
    run_language_mutation_case,
    run_language_mutations,
)


def test_mutation_case_catalog_is_deterministic():
    cases = language_mutation_cases()
    assert len(cases) == 10
    assert {case.category for case in cases} == {"grammar", "typing", "inference"}
    assert cases[0].name == "missing-close"


def test_each_mutation_matches_expected_status():
    results = run_language_mutations()
    assert all(result.ok for result in results)
    assert {result.actual_status for result in results} == {"blocked", "unknown"}


def test_grammar_mutations_are_parse_blocked():
    grammar = [run_language_mutation_case(case) for case in language_mutation_cases() if case.category == "grammar"]
    assert all(not result.parse_ok for result in grammar)
    assert all(result.actual_status == "blocked" for result in grammar)


def test_typing_mutations_keep_parse_but_block_type():
    typing = [run_language_mutation_case(case) for case in language_mutation_cases() if case.category == "typing"]
    assert all(result.parse_ok for result in typing)
    assert all(result.actual_status == "blocked" for result in typing)
    assert all(result.steps >= 1 for result in typing)


def test_inference_mutations_split_blocked_and_unknown():
    inference = [run_language_mutation_case(case) for case in language_mutation_cases() if case.category == "inference"]
    statuses = {result.name: result.actual_status for result in inference}
    assert statuses == {"trace-mismatch": "blocked", "unknown-observer": "unknown"}


def test_mutation_report_counts_expected_surface():
    report = language_mutation_report()
    assert report.cases == 10
    assert report.blocked == 9
    assert report.unknown == 1
    assert report.ready == 0
    assert report.unexpected == 0


def test_mutation_language_checklist_v04():
    assert mutation_language_checklist() == (
        "grammar-mutations",
        "typing-mutations",
        "inference-mutations",
        "expected-status",
        "proof-trace-runner",
        "aggregate-report",
    )
