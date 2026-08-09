from veyra_sage.all import VeyraCategoryLab, build_category_like_notebook, category_like_lab_summary


EXPECTED = {"objects": 4, "morphisms": 4, "closed": 4, "invariants": 2, "broken": 1, "universal": 3, "blocked": 1, "checklist": 4}


def test_category_like_lab_summary_closes_x3():
    assert category_like_lab_summary() == EXPECTED


def test_category_like_lab_rows_are_json_ready():
    lab = VeyraCategoryLab()
    assert lab.object_rows()[0]["shadows"] == ["0", "1", "2"]
    assert lab.morphism_rows()[1]["status"] == "closed"
    assert lab.invariant_rows()[1]["status"] == "broken"
    assert lab.universal_rows()[-1]["obstruction"] == "object-shadow-mismatch"


def test_category_like_notebook_is_executable_contract():
    notebook = build_category_like_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert "universal claims stay bounded" in notebook.to_markdown()
