from veyra_sage.all import VeyraProofDisciplineLab, build_proof_discipline_notebook, proof_discipline_lab_summary


def test_proof_discipline_lab_summary_matches_core():
    assert proof_discipline_lab_summary() == {"rules": 7, "steps": 28, "blocked_rules": 3, "domains": 7, "domain_certs": 7, "models": 10, "exports": 19}


def test_proof_discipline_lab_rows_are_json_ready():
    lab = VeyraProofDisciplineLab()
    assert lab.rule_coverage_rows()[0]["rule"] == "grammar.parse"
    assert len(lab.semantic_domain_rows()) == 7
    assert all(row["certificate"] == "declared-shadow" for row in lab.semantic_domain_rows())
    assert len(lab.primitive_model_rows()) == 10
    assert len(lab.stable_export_rows()) == 19
    assert len(lab.checklist()) == 4


def test_proof_discipline_notebook_shape():
    notebook = build_proof_discipline_notebook()
    assert notebook.summary() == {"cells": 5, "markdown": 2, "code": 3}
    assert notebook.to_ipynb_dict()["nbformat"] == 4
