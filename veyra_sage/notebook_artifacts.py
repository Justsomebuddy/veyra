"""Disk artifact bundle for generated Veyra Sage notebooks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
import logging
from pathlib import Path

from .calculus import build_calculus_depth_notebook
from .category_like import build_category_like_notebook
from .linear_algebra import build_linear_algebra_seed_notebook
from .card_examples import build_all_executable_card_notebooks
from .essence import build_essence_core_notebook
from .geometry_cards import build_geometry_theorem_card_notebook
from .language import build_language_lab_notebook
from .likelihood_geometry import build_likelihood_geometry_notebook
from .notebooks import VeyraNotebook, build_all_domain_notebooks, build_school_proof_notebook
from .number_theory import build_number_theory_notebook
from .proof_discipline import build_proof_discipline_notebook
from .refutation_search import build_all_refutation_search_notebooks
from .refutations import build_all_refutation_notebooks
from .statistics_inference import build_statistics_inference_notebook
from .topology_echo import build_topology_echo_notebook
from .trigonometry import build_trigonometry_identity_notebook

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[int, int, "VeyraNotebookArtifact"], None]


@dataclass(frozen=True)
class VeyraNotebookArtifact:
    """One named notebook ready to be written to disk."""

    family: str
    name: str
    notebook: VeyraNotebook

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraNotebookArtifact({self.family}/{self.name})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, object]:
        """Return manifest-ready artifact summary."""
        logger.debug("VeyraNotebookArtifact.as_dict entry family=%s name=%s", self.family, self.name)
        summary = self.notebook.summary()
        result = {"family": self.family, "name": self.name, "title": self.notebook.title, **summary}
        logger.debug("VeyraNotebookArtifact.as_dict exit result=%r", result)
        return result


def _domain_artifacts(family: str, notebooks: dict[str, VeyraNotebook]) -> tuple[VeyraNotebookArtifact, ...]:
    """Convert domain notebook mapping into sorted artifacts."""
    logger.debug("_domain_artifacts entry family=%s count=%d", family, len(notebooks))
    result = tuple(VeyraNotebookArtifact(family, domain, notebooks[domain]) for domain in sorted(notebooks))
    logger.debug("_domain_artifacts exit count=%d", len(result))
    return result


def current_notebook_artifacts() -> tuple[VeyraNotebookArtifact, ...]:
    """Return every current generated notebook as disk-ready artifacts."""
    logger.debug("current_notebook_artifacts entry")
    global_artifacts = (
        VeyraNotebookArtifact("global", "school_proof", build_school_proof_notebook()),
        VeyraNotebookArtifact("global", "core_language", build_language_lab_notebook()),
        VeyraNotebookArtifact("global", "calculus_depth", build_calculus_depth_notebook()),
        VeyraNotebookArtifact("global", "trigonometry_identities", build_trigonometry_identity_notebook()),
        VeyraNotebookArtifact("global", "linear_algebra_seed", build_linear_algebra_seed_notebook()),
        VeyraNotebookArtifact("global", "statistics_inference", build_statistics_inference_notebook()),
        VeyraNotebookArtifact("global", "geometry_theorem_cards", build_geometry_theorem_card_notebook()),
        VeyraNotebookArtifact("global", "essence_core", build_essence_core_notebook()),
        VeyraNotebookArtifact("global", "proof_discipline", build_proof_discipline_notebook()),
        VeyraNotebookArtifact("global", "number_theory", build_number_theory_notebook()),
        VeyraNotebookArtifact("global", "category_like", build_category_like_notebook()),
        VeyraNotebookArtifact("global", "topology_echo", build_topology_echo_notebook()),
        VeyraNotebookArtifact("global", "likelihood_geometry", build_likelihood_geometry_notebook()),
    )
    result = global_artifacts + _domain_artifacts("domain_theorems", build_all_domain_notebooks()) + _domain_artifacts("executable_cards", build_all_executable_card_notebooks()) + _domain_artifacts("refutations", build_all_refutation_notebooks()) + _domain_artifacts("refutation_search", build_all_refutation_search_notebooks())
    logger.debug("current_notebook_artifacts exit count=%d", len(result))
    return result


def notebook_artifact_summary(artifacts: tuple[VeyraNotebookArtifact, ...] | None = None) -> dict[str, int]:
    """Return compact summary for a notebook artifact set."""
    logger.debug("notebook_artifact_summary entry has_artifacts=%s", artifacts is not None)
    items = current_notebook_artifacts() if artifacts is None else artifacts
    summaries = tuple(item.notebook.summary() for item in items)
    result = {"notebooks": len(items), "families": len({item.family for item in items}), "cells": sum(item["cells"] for item in summaries), "markdown": sum(item["markdown"] for item in summaries), "code": sum(item["code"] for item in summaries)}
    logger.debug("notebook_artifact_summary exit result=%r", result)
    return result


def write_current_notebook_artifacts(output_dir: str | Path = "notebooks/generated", include_markdown: bool = True, progress: ProgressCallback | None = None) -> dict[str, object]:
    """Write all current notebook artifacts plus a compact manifest."""
    logger.debug("write_current_notebook_artifacts entry output_dir=%s include_markdown=%s", output_dir, include_markdown)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    artifacts = current_notebook_artifacts()
    rows: list[dict[str, object]] = []
    for index, artifact in enumerate(artifacts, 1):
        family_dir = target / artifact.family
        family_dir.mkdir(parents=True, exist_ok=True)
        ipynb_path = artifact.notebook.write_ipynb(family_dir / f"{artifact.name}.ipynb")
        markdown_path = artifact.notebook.write_markdown(family_dir / f"{artifact.name}.md") if include_markdown else None
        row = artifact.as_dict() | {
            "ipynb": ipynb_path.as_posix(),
            "markdown": None if markdown_path is None else markdown_path.as_posix(),
        }
        rows.append(row)
        if progress is not None:
            progress(index, len(artifacts), artifact)
    summary = notebook_artifact_summary(artifacts)
    manifest = {
        "format": "veyra-notebook-artifacts-v1",
        "output_dir": target.as_posix(),
        "include_markdown": include_markdown,
        **summary,
        "artifacts": rows,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    logger.debug("write_current_notebook_artifacts exit manifest=%s count=%d", manifest_path, len(rows))
    return manifest
