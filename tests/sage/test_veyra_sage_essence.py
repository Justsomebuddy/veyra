from veyra_sage.all import VeyraEssenceLab, build_essence_core_notebook, essence_lab_summary
import pytest

pytestmark = pytest.mark.requires_lean


def test_essence_lab_summary_is_core_ready():
    summary = essence_lab_summary()
    assert summary["core_ready"] is True
    assert summary["axioms"] == 9
    assert summary["layers"] == 36
    assert summary["theorem_derived"] == 2
    assert summary["shadow"] == 25
    assert summary["proof_complete"] is False


def test_essence_lab_rows_are_json_ready():
    lab = VeyraEssenceLab()
    axioms = lab.axiom_rows()
    layers = lab.layer_rows()
    assert axioms[0]["name"] == "no-primitive-equality"
    assert layers[-1]["name"] == "deduction-chain"
    assert any(row["name"] == "native-runtime" for row in layers)
    assert any(row["name"] == "classical-benchmark" for row in layers)
    assert any(row["name"] == "native-number-theorem" for row in layers)
    assert any(row["name"] == "foundational-kernel" for row in layers)
    assert any(row["name"] == "intrinsic-resonance" for row in layers)
    assert any(row["name"] == "intrinsic-observer-echo" for row in layers)
    assert any(row["name"] == "weighted-echo-measure" for row in layers)
    assert any(row["name"] == "science-domain-certificates" for row in layers)
    assert any(row["name"] == "model-diagnostics" for row in layers)
    assert any(row["name"] == "scale-memory-log" for row in layers)
    assert any(row["name"] == "trigonometry-identities" for row in layers)
    assert any(row["name"] == "linear-algebra" for row in layers)
    assert any(row["name"] == "statistics-inference" for row in layers)
    assert any(row["name"] == "transcendental-limit" for row in layers)
    assert any(row["name"] == "convergence-algebra" for row in layers)
    assert any(row["name"] == "real-analysis-structure" for row in layers)
    assert any(row["name"] == "phase-equations" for row in layers)
    assert any(row["name"] == "statistics-concentration" for row in layers)
    assert len(lab.checklist()) == 6


def test_essence_core_notebook_shape():
    notebook = build_essence_core_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert notebook.to_ipynb_dict()["nbformat"] == 4
