from veyra_sage.all import VeyraRefutationExample, build_all_refutation_notebooks, build_refutation_notebook, refutation_examples, refutation_summary, run_refutation_example


def test_refutation_examples_cover_key_domains():
    rows = refutation_examples()
    assert len(rows) == 7
    assert refutation_summary() == {"examples": 7, "blocked": 7, "domains": 7, "mutations": 3}
    assert all(isinstance(row, VeyraRefutationExample) for row in rows)
    assert {row.domain for row in rows} == {"algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig"}


def test_run_refutation_example_blocks_geometry():
    check = run_refutation_example("pythagorean-non-right")
    assert check.status == "blocked"
    assert check.obstruction == "non-right-apex"


def test_refutation_examples_filter_by_domain():
    probability = refutation_examples("probability")
    assert len(probability) == 1
    assert probability[0].refutation_id == "dependent-events"
    assert run_refutation_example("dependent-events").obstruction == "product-gap"


def test_refutation_notebook_shape():
    notebook = build_refutation_notebook("geometry")
    assert notebook.summary() == {"cells": 8, "markdown": 4, "code": 4}
    text = notebook.to_markdown()
    assert "refutation lab" in text
    assert "pythagorean-non-right" in text


def test_all_refutation_notebooks():
    notebooks = build_all_refutation_notebooks()
    assert set(notebooks) == {"algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig"}
    assert sum(item.summary()["cells"] for item in notebooks.values()) == 56
    assert "variance-mutated-shift" in notebooks["statistics"].to_markdown()


def test_unknown_refutation_and_notebook_fail():
    for func in (run_refutation_example, build_refutation_notebook):
        try:
            func("unknown")
        except KeyError as exc:
            assert "unknown" in str(exc)
        else:
            raise AssertionError("unknown refutation/domain must fail")
