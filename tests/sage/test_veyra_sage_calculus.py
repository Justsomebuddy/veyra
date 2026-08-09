from veyra_sage.all import VeyraCalculusLab, build_calculus_depth_notebook, calculus_depth_lab_summary


def test_calculus_lab_summary_is_ready():
    summary = calculus_depth_lab_summary()
    assert summary == {"checklist": 4, "cards": 3, "linearization_ready": True, "integral_ready": True}


def test_calculus_lab_rows_are_json_ready():
    lab = VeyraCalculusLab()
    linear = lab.linearization_row()
    cards = lab.card_rows()
    assert linear["slope"] == "6"
    assert linear["error"] == "1"
    assert [card["relation"] for card in cards] == ["coherent", "coherent", "coherent"]
    assert len(lab.checklist()) == 4


def test_calculus_depth_notebook_shape():
    notebook = build_calculus_depth_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert notebook.to_ipynb_dict()["nbformat"] == 4
