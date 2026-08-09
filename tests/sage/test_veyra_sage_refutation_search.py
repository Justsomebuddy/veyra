from veyra_sage.all import VeyraSearchReport, build_all_refutation_search_notebooks, build_refutation_search_notebook, refutation_search, refutation_search_summary, run_search_candidate


def test_refutation_search_summary_and_reports():
    reports = refutation_search()
    assert refutation_search_summary() == {"domains": 7, "tried": 10, "blocked": 7}
    assert all(isinstance(item, VeyraSearchReport) for item in reports)
    assert {item.domain for item in reports} == {"algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig"}


def test_run_search_candidate_positive_and_blocked_cases():
    assert run_search_candidate("geo-right").status == "ready"
    blocked = run_search_candidate("geo-non-right")
    assert blocked.status == "blocked"
    assert blocked.obstruction == "non-right-apex"


def test_refutation_search_filter_by_domain():
    geometry = refutation_search("geometry")
    assert len(geometry) == 1
    assert geometry[0].tried == 2
    assert len(geometry[0].blocked) == 1
    assert geometry[0].blocked[0].as_dict()["parameters"]["point"] == "1,1"


def test_refutation_search_notebook_shape():
    notebook = build_refutation_search_notebook("geometry")
    assert notebook.summary() == {"cells": 6, "markdown": 3, "code": 3}
    text = notebook.to_markdown()
    assert "refutation search" in text
    assert "geo-non-right" in text


def test_all_refutation_search_notebooks():
    notebooks = build_all_refutation_search_notebooks()
    assert set(notebooks) == {"algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig"}
    assert sum(item.summary()["cells"] for item in notebooks.values()) == 42
    assert "dependent-events" in notebooks["probability"].to_markdown()


def test_unknown_search_candidate_and_domain_fail():
    for func in (run_search_candidate, refutation_search, build_refutation_search_notebook):
        try:
            func("unknown")
        except KeyError as exc:
            assert "unknown" in str(exc)
        else:
            raise AssertionError("unknown search item must fail")
