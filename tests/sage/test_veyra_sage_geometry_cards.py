from veyra_sage.all import VeyraGeometryTheoremLab, build_geometry_theorem_card_notebook, geometry_theorem_lab_summary


def test_geometry_theorem_lab_summary_and_rows():
    lab = VeyraGeometryTheoremLab()
    assert geometry_theorem_lab_summary() == {"cards": 5, "ready": 5, "visual_scenes": 3, "stable_exports": 5, "package_stable": False}
    assert {row["theorem_id"] for row in lab.card_rows()} == {"pythagorean-separation", "sss-triangle", "sas-triangle", "line-shell-intersection", "plane-relabel-composition"}
    assert all(row["status"] == "ready" for row in lab.card_rows())


def test_geometry_visual_rows_are_notebook_ready():
    rows = VeyraGeometryTheoremLab().visual_rows()
    assert rows[0]["scene"] == "pythagorean-right-triangle"
    assert rows[0]["points"]["e"] == [3, 0]
    assert rows[1]["card"] == "line-shell-intersection"


def test_geometry_stable_export_rows_are_filtered():
    rows = VeyraGeometryTheoremLab().stable_export_rows()
    assert len(rows) == 5
    assert all(row["export_status"] == "stable-card-only" for row in rows)
    assert all(str(row["hook"]).startswith("geometry.") for row in rows)


def test_geometry_theorem_card_notebook_shape():
    notebook = build_geometry_theorem_card_notebook()
    assert notebook.summary() == {"cells": 6, "markdown": 2, "code": 4}
    text = notebook.to_markdown()
    assert "Geometry Theorem-Card Lab" in text
    assert "Visual scene rows" in text
