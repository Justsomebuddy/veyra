from veyra_sage.all import VeyraLanguageLab, build_language_lab_notebook, language_lab_summary


def test_language_lab_interpret_ready_and_blocked():
    lab = VeyraLanguageLab()
    ready = lab.interpret("echo(nod:a,nod:b,observer:kind)")
    blocked = lab.interpret("echo(nod:a,nod:b,observer:trace)")
    assert ready.status == "ready"
    assert ready.kind == "relation"
    assert blocked.status == "blocked"
    assert "echo mismatch" in blocked.obstruction


def test_language_lab_trace_is_json_ready():
    row = VeyraLanguageLab().trace("echo(nod:a,nod:b,observer:trace)")
    data = row.as_dict()
    assert data["parse_ok"] is True
    assert data["final_status"] == "blocked"
    assert data["blocked"] >= 1
    assert data["last_rule"] == "infer.echo"


def test_language_lab_mutation_summary():
    summary = VeyraLanguageLab().mutation_summary()
    assert summary == {"cases": 10, "blocked": 9, "unknown": 1, "ready": 0, "unexpected": 0}


def test_language_lab_generated_family_summary():
    summary = VeyraLanguageLab().generated_family_summary()
    assert summary == {"families": 4, "cases": 20, "blocked": 18, "unknown": 2, "ready": 0, "unexpected": 0}


def test_language_lab_property_fuzz_summary():
    summary = VeyraLanguageLab().property_fuzz_summary()
    assert summary == {"seed": 613, "families": 4, "cases": 24, "blocked": 21, "unknown": 3, "ready": 0, "unexpected": 0, "shrunk": 24}


def test_language_lab_coverage_summary():
    summary = VeyraLanguageLab().coverage_summary()
    assert summary == {"families": 11, "cases": 54, "blocked": 48, "unknown": 6, "ready": 0, "unexpected": 0, "missed": 0, "shrink_witnesses": 24}


def test_language_lab_span_diagnostic_summary():
    summary = VeyraLanguageLab().span_diagnostic_summary()
    assert summary == {"cases": 7, "diagnostics": 7, "excerpts": 7, "multiline": 1, "unexpected": 0, "missed": 0}


def test_language_lab_summary_contract():
    assert language_lab_summary() == {
        "domain": "logic",
        "ready_status": "ready",
        "blocked_status": "blocked",
        "mutation_cases": 10,
        "mutation_unexpected": 0,
        "family_cases": 20,
        "family_unexpected": 0,
        "property_cases": 24,
        "property_unexpected": 0,
        "property_shrunk": 24,
        "coverage_cases": 54,
        "coverage_missed": 0,
        "span_diag_cases": 7,
        "span_diag_missed": 0,
    }


def test_language_lab_notebook_contract():
    notebook = build_language_lab_notebook()
    assert notebook.summary() == {"cells": 6, "markdown": 2, "code": 4}
    assert "VeyraLanguageLab" in notebook.to_markdown()
