from veyra_sage.all import VeyraLinearAlgebraLab, build_linear_algebra_seed_notebook, linear_algebra_seed_lab_summary


def test_linear_algebra_seed_lab_summary_ready():
    assert linear_algebra_seed_lab_summary() == {"checklist": 4, "cards": 2, "action_ready": True, "determinant_ready": True}


def test_linear_algebra_seed_rows_are_json_ready():
    lab = VeyraLinearAlgebraLab()
    action = lab.action_row()
    cards = lab.card_rows()
    assert action["image"] == ["2", "6"]
    assert action["det"] == "6"
    assert action["trace"] == "5"
    assert cards[0]["relation"] == "coherent"
    assert cards[1]["relation"] == "eigen-shadow"


def test_linear_algebra_seed_notebook_shape():
    assert build_linear_algebra_seed_notebook().summary() == {"cells": 5, "markdown": 2, "code": 3}
