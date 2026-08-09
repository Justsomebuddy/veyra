from veyra_sage.all import VeyraTopologyLab, build_topology_echo_notebook, topology_echo_lab_summary

EXPECTED = {"shapes": 4, "invariants": 4, "invariant_hits": 4, "obstructions": 2, "blocked": 2, "checklist": 4}


def test_topology_echo_lab_summary_closes_x4():
    assert topology_echo_lab_summary() == EXPECTED


def test_topology_echo_lab_rows_are_json_ready():
    lab = VeyraTopologyLab()
    assert lab.shape_rows()[0]["component_count"] == 1
    assert all(row["status"] == "invariant" for row in lab.invariant_rows())
    assert lab.obstruction_rows()[-1]["obstruction"] == "cycle-collapse"


def test_topology_echo_notebook_is_executable_contract():
    notebook = build_topology_echo_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert "deformation-invariant" in notebook.to_markdown()
