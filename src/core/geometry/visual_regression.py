"""Reproducible visual regression rows for geometry theorem-card scenes."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging

logger = logging.getLogger(__name__)
GEOMETRY_VISUAL_VERSION = "VEYRA-GEOM-VISUAL-v1"
EXPECTED_VISUAL_DIGESTS = {
    "pythagorean-right-triangle": "1afff2f2c901296f",
    "line-shell-tangent": "fe9658a7b70673e9",
    "plane-relabel-composition": "4eeca8e45ca5ea21",
}


@dataclass(frozen=True)
class GeometryVisualSnapshot:
    """One canonical geometry visual scene with stable regression digest."""

    scene: str
    card: str
    render: str
    digest: str
    expected: str
    status: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready visual snapshot row."""
        logger.debug("GeometryVisualSnapshot.as_dict entry scene=%s", self.scene)
        result = self.__dict__.copy()
        logger.debug("GeometryVisualSnapshot.as_dict exit result=%r", result)
        return result


def geometry_visual_scene_rows() -> tuple[dict[str, object], ...]:
    """Return canonical renderer-agnostic geometry visual scene rows."""
    logger.debug("geometry_visual_scene_rows entry")
    result = (
        {"scene": "pythagorean-right-triangle", "points": {"o": [0, 0], "e": [3, 0], "n": [0, 4]}, "edges": [["o", "e"], ["o", "n"], ["e", "n"]], "card": "pythagorean-separation"},
        {"scene": "line-shell-tangent", "center": [0, 0], "radius_squared": "25", "corridor": [[5, -1], [5, 1]], "card": "line-shell-intersection"},
        {"scene": "plane-relabel-composition", "sample": [2, 3], "outer": "identity", "inner": "identity", "card": "plane-relabel-composition"},
    )
    logger.debug("geometry_visual_scene_rows exit count=%d", len(result))
    return result


def canonical_visual_payload(row: dict[str, object]) -> str:
    """Return stable JSON payload for one visual scene."""
    logger.debug("canonical_visual_payload entry scene=%s", row.get("scene"))
    result = json.dumps(row, sort_keys=True, separators=(",", ":"))
    logger.debug("canonical_visual_payload exit bytes=%d", len(result))
    return result


def render_visual_scene(row: dict[str, object]) -> str:
    """Return deterministic renderer-independent visual text."""
    logger.debug("render_visual_scene entry scene=%s", row.get("scene"))
    result = f"{GEOMETRY_VISUAL_VERSION}\n{canonical_visual_payload(row)}"
    logger.debug("render_visual_scene exit bytes=%d", len(result))
    return result


def visual_digest(render: str) -> str:
    """Return short stable digest for rendered visual text."""
    logger.debug("visual_digest entry bytes=%d", len(render))
    result = hashlib.sha256(render.encode("utf-8")).hexdigest()[:16]
    logger.debug("visual_digest exit digest=%s", result)
    return result


def geometry_visual_snapshots() -> tuple[GeometryVisualSnapshot, ...]:
    """Return visual regression snapshots for canonical geometry scenes."""
    logger.debug("geometry_visual_snapshots entry")
    rows: list[GeometryVisualSnapshot] = []
    for scene in geometry_visual_scene_rows():
        render = render_visual_scene(scene)
        digest = visual_digest(render)
        scene_name = str(scene["scene"])
        expected = EXPECTED_VISUAL_DIGESTS.get(scene_name, "")
        status = "matched" if digest == expected else "changed"
        rows.append(GeometryVisualSnapshot(scene_name, str(scene["card"]), render, digest, expected, status))
    result = tuple(rows)
    logger.debug("geometry_visual_snapshots exit count=%d", len(result))
    return result


def geometry_visual_regression_summary(rows: tuple[GeometryVisualSnapshot, ...] | None = None) -> dict[str, int | bool]:
    """Return compact X6 visual regression counters."""
    logger.debug("geometry_visual_regression_summary entry has_rows=%s", rows is not None)
    items = tuple(rows or geometry_visual_snapshots())
    scenes = geometry_visual_scene_rows()
    result: dict[str, int | bool] = {
        "scenes": len(scenes),
        "snapshots": len(items),
        "matched": sum(item.status == "matched" for item in items),
        "changed": sum(item.status != "matched" for item in items),
        "indexed": len({str(row["scene"]) for row in scenes}) == len(scenes),
        "reproducible": all(item.digest == visual_digest(item.render) for item in items),
    }
    logger.debug("geometry_visual_regression_summary exit result=%r", result)
    return result


def geometry_visual_regression_checklist() -> tuple[str, ...]:
    """Return X6 visual regression acceptance checklist."""
    logger.debug("geometry_visual_regression_checklist entry")
    result = ("canonical visual scene rows", "deterministic renderer-independent render text", "stable digest per scene", "no theorem claim from image similarity")
    logger.debug("geometry_visual_regression_checklist exit count=%d", len(result))
    return result
