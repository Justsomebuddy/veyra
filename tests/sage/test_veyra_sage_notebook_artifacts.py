import json

from veyra_sage.all import current_notebook_artifacts, notebook_artifact_summary, write_current_notebook_artifacts


def test_current_notebook_artifact_inventory():
    artifacts = current_notebook_artifacts()
    assert len(artifacts) == 41
    assert artifacts[0].family == "global"
    assert artifacts[0].name == "school_proof"
    assert notebook_artifact_summary(artifacts) == {"notebooks": 41, "families": 5, "cells": 280, "markdown": 133, "code": 147}


def test_write_current_notebook_artifacts(tmp_path):
    manifest = write_current_notebook_artifacts(tmp_path)
    assert manifest["format"] == "veyra-notebook-artifacts-v1"
    assert manifest["notebooks"] == 41
    assert len(list(tmp_path.glob("**/*.ipynb"))) == 41
    assert len(list(tmp_path.glob("**/*.md"))) == 41

    loaded_manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert loaded_manifest["cells"] == 280
    school = json.loads((tmp_path / "global" / "school_proof.ipynb").read_text())
    assert school["nbformat"] == 4
    assert school["metadata"]["veyra"]["title"] == "Veyra School Proof Graph Lab"


def test_write_current_notebook_artifacts_without_markdown(tmp_path):
    manifest = write_current_notebook_artifacts(tmp_path, include_markdown=False)
    assert manifest["include_markdown"] is False
    assert len(list(tmp_path.glob("**/*.ipynb"))) == 41
    assert len(list(tmp_path.glob("**/*.md"))) == 0
    assert manifest["artifacts"][0]["markdown"] is None
