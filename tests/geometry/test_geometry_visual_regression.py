from src.core.geometry_visual_regression import (
    EXPECTED_VISUAL_DIGESTS,
    GEOMETRY_VISUAL_VERSION,
    canonical_visual_payload,
    geometry_visual_regression_checklist,
    geometry_visual_regression_summary,
    geometry_visual_scene_rows,
    geometry_visual_snapshots,
    render_visual_scene,
    visual_digest,
)


def test_geometry_visual_scene_rows_are_canonical_and_indexed():
    rows = geometry_visual_scene_rows()
    assert [row["scene"] for row in rows] == [
        "pythagorean-right-triangle",
        "line-shell-tangent",
        "plane-relabel-composition",
    ]
    assert {row["card"] for row in rows} == {
        "pythagorean-separation",
        "line-shell-intersection",
        "plane-relabel-composition",
    }


def test_geometry_visual_render_digest_is_stable():
    first = geometry_visual_scene_rows()[0]
    render = render_visual_scene(first)
    assert render.startswith(GEOMETRY_VISUAL_VERSION)
    assert canonical_visual_payload(first) in render
    assert visual_digest(render) == EXPECTED_VISUAL_DIGESTS["pythagorean-right-triangle"]


def test_geometry_visual_snapshots_match_expected_digests():
    rows = geometry_visual_snapshots()
    assert len(rows) == 3
    assert all(row.status == "matched" for row in rows)
    assert rows[-1].as_dict()["digest"] == EXPECTED_VISUAL_DIGESTS["plane-relabel-composition"]


def test_geometry_visual_regression_summary_is_non_claim():
    summary = geometry_visual_regression_summary()
    assert summary == {"scenes": 3, "snapshots": 3, "matched": 3, "changed": 0, "indexed": True, "reproducible": True}
    assert "no theorem claim" in geometry_visual_regression_checklist()[-1]
