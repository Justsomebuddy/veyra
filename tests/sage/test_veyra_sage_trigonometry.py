from veyra_sage.all import VeyraTrigonometryIdentityLab, build_trigonometry_identity_notebook, trigonometry_identity_lab_summary


def test_trigonometry_identity_lab_summary_ready():
    assert trigonometry_identity_lab_summary() == {"checklist": 4, "cards": 4, "all_coherent": True, "unit_ready": True}


def test_trigonometry_identity_rows_are_json_ready():
    lab = VeyraTrigonometryIdentityLab()
    phases = lab.phase_rows()
    cards = lab.card_rows()
    assert phases[0]["cos"] == "3/5"
    assert phases[0]["sin"] == "4/5"
    assert all(row["relation"] == "coherent" for row in cards)
    assert cards[-1]["evidence"][-1] == ("sin", "0")


def test_trigonometry_identity_notebook_shape():
    assert build_trigonometry_identity_notebook().summary() == {"cells": 5, "markdown": 2, "code": 3}
