from veyra_sage.all import VeyraLikelihoodGeometryLab, build_likelihood_geometry_notebook, likelihood_geometry_lab_summary

EXPECTED = {"likelihood_points": 3, "segments": 2, "rising_segments": 2, "residual_certificates": 2, "fit_domains": 1, "blocked_domains": 1, "checklist": 4}


def test_likelihood_geometry_lab_summary_closes_x5():
    assert likelihood_geometry_lab_summary() == EXPECTED


def test_likelihood_geometry_lab_rows_are_json_ready():
    lab = VeyraLikelihoodGeometryLab()
    assert lab.likelihood_rows()[-1]["likelihood"] == "27/256"
    assert lab.segment_rows()[0]["slope"] == "13/64"
    assert lab.peak_row()["status"] == "unique-peak"
    assert lab.residual_rows()[-1]["status"] == "blocked"


def test_likelihood_geometry_notebook_is_executable_contract():
    notebook = build_likelihood_geometry_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert "residual-family" in notebook.to_markdown()
