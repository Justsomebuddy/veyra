from veyra_sage.all import VeyraCardExample, build_all_executable_card_notebooks, build_executable_card_notebook, card_example_summary, card_examples, run_card_example


def test_card_examples_cover_all_theorem_specs():
    rows = card_examples()
    summary = card_example_summary()
    assert len(rows) == 19
    assert summary == {"examples": 19, "ready": 19, "domains": 7}
    assert all(isinstance(row, VeyraCardExample) for row in rows)
    assert all(row.expected_status == "ready" for row in rows)


def test_run_card_example_checks_geometry_card():
    check = run_card_example("pythagorean-separation")
    assert check.status == "ready"
    assert check.obstruction == "none"
    assert check.as_dict()["theorem_id"] == "pythagorean-separation"


def test_card_examples_filter_by_domain():
    geometry = card_examples("geometry")
    probability = card_examples("probability")
    assert len(geometry) == 5
    assert {row.theorem_id for row in probability} == {"probability-complement", "probability-union", "probability-independence"}


def test_executable_card_notebook_geometry_shape():
    notebook = build_executable_card_notebook("geometry")
    assert notebook.summary() == {"cells": 8, "markdown": 4, "code": 4}
    text = notebook.to_markdown()
    assert "executable theorem-card lab" in text
    assert "line-shell-intersection" in text


def test_all_executable_card_notebooks():
    notebooks = build_all_executable_card_notebooks()
    assert set(notebooks) == {"algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig"}
    assert sum(item.summary()["cells"] for item in notebooks.values()) == 56
    assert "variance-shift" in notebooks["statistics"].to_markdown()


def test_unknown_card_example_and_notebook_fail():
    for func in (run_card_example, build_executable_card_notebook):
        try:
            func("unknown")
        except KeyError as exc:
            assert "unknown" in str(exc)
        else:
            raise AssertionError("unknown theorem/domain must fail")
