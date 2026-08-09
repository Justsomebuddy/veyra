import json

from veyra_sage.all import VeyraDomainNotebookSpec, VeyraNotebook, VeyraNotebookCell, available_notebook_domains, build_all_domain_notebooks, build_domain_theorem_notebook, build_school_proof_notebook, domain_notebook_spec


def test_school_proof_notebook_summary_and_markdown():
    notebook = build_school_proof_notebook()
    assert isinstance(notebook, VeyraNotebook)
    assert notebook.summary() == {"cells": 8, "markdown": 4, "code": 4}
    markdown = notebook.to_markdown()
    assert "Veyra School Proof Graph Lab" in markdown
    assert "arithmetic-ratios → combinatorics → probability → statistics" in markdown


def test_school_proof_notebook_ipynb_shape():
    notebook = build_school_proof_notebook()
    ipynb = notebook.to_ipynb_dict()
    assert ipynb["nbformat"] == 4
    assert len(ipynb["cells"]) == 8
    assert ipynb["cells"][0]["cell_type"] == "markdown"
    assert ipynb["cells"][2]["cell_type"] == "code"
    assert ipynb["metadata"]["veyra"]["title"] == notebook.title


def test_school_proof_notebook_writes_artifacts(tmp_path):
    notebook = build_school_proof_notebook()
    md = notebook.write_markdown(tmp_path / "veyra_lab.md")
    ipynb = notebook.write_ipynb(tmp_path / "veyra_lab.ipynb")
    assert md.read_text().startswith("# Veyra")
    loaded = json.loads(ipynb.read_text())
    assert loaded["nbformat_minor"] == 5
    assert len(loaded["cells"]) == 8


def test_notebook_cell_rejects_invalid_kind():
    cell = VeyraNotebookCell("bad", "x")
    try:
        cell.as_ipynb_cell()
    except ValueError as exc:
        assert "kind" in str(exc)
    else:
        raise AssertionError("invalid cell kind must fail")


def test_available_domain_notebook_specs():
    domains = available_notebook_domains()
    assert domains == ("algebra", "analysis", "combinatorics", "geometry", "probability", "statistics", "trig")
    spec = domain_notebook_spec("geometry")
    assert isinstance(spec, VeyraDomainNotebookSpec)
    assert "pythagorean-separation" in spec.theorem_ids
    assert spec.as_dict()["cells"] == 8


def test_domain_theorem_notebook_geometry_shape():
    notebook = build_domain_theorem_notebook("geometry")
    assert notebook.summary() == {"cells": 8, "markdown": 4, "code": 4}
    markdown = notebook.to_markdown()
    assert "Veyra geometry theorem lab" in markdown
    assert "pythagorean-separation" in markdown
    assert "DEF-088" in markdown


def test_domain_theorem_notebook_rejects_unknown_domain():
    try:
        build_domain_theorem_notebook("unknown")
    except KeyError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("unknown domain must fail")


def test_build_all_domain_notebooks():
    notebooks = build_all_domain_notebooks()
    assert set(notebooks) == set(available_notebook_domains())
    assert notebooks["probability"].summary()["cells"] == 8
    assert "probability-union" in notebooks["probability"].to_markdown()
