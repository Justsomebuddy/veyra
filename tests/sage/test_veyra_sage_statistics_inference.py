from veyra_sage.all import VeyraStatisticsInferenceLab, build_statistics_inference_notebook, statistics_inference_lab_summary


def test_statistics_inference_lab_summary_ready():
    assert statistics_inference_lab_summary() == {"checklist": 4, "hypothesis_cards": 2, "family_ready": True, "interval_ready": True, "uncertainty": "3/64"}


def test_statistics_inference_rows_are_json_ready():
    lab = VeyraStatisticsInferenceLab()
    family = lab.family_row()
    interval = lab.interval_row()
    hypotheses = lab.hypothesis_rows()
    assert family["p"] == "3/4"
    assert family["variance"] == "3/16"
    assert interval["center"] == "2"
    assert interval["lower"] == "3/2"
    assert interval["upper"] == "5/2"
    assert interval["contains_center"] is True
    assert hypotheses[0]["relation"] == "accepted"
    assert hypotheses[1]["relation"] == "rejected"


def test_statistics_inference_notebook_shape():
    assert build_statistics_inference_notebook().summary() == {"cells": 5, "markdown": 2, "code": 3}
