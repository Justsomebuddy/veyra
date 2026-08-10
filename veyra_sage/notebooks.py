"""Notebook/export generator for the Veyra Sage laboratory."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path

from .proofs import VeyraProofGraph
from .school import VeyraSchoolCore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraNotebookCell:
    """One markdown or code notebook cell."""

    kind: str
    source: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraNotebookCell({self.kind})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_ipynb_cell(self) -> dict[str, object]:
        """Return nbformat-compatible cell dictionary."""
        logger.debug("VeyraNotebookCell.as_ipynb_cell entry kind=%s", self.kind)
        if self.kind not in {"markdown", "code"}:
            logger.error("VeyraNotebookCell.as_ipynb_cell invalid kind=%s", self.kind)
            raise ValueError("kind must be markdown or code")
        result = {"cell_type": self.kind, "metadata": {}, "source": self.source.splitlines(keepends=True)}
        if self.kind == "code":
            result |= {"execution_count": None, "outputs": []}
        logger.debug("VeyraNotebookCell.as_ipynb_cell exit keys=%r", sorted(result))
        return result

    def as_markdown_block(self) -> str:
        """Return markdown rendering for this cell."""
        logger.debug("VeyraNotebookCell.as_markdown_block entry kind=%s", self.kind)
        if self.kind == "code":
            result = "```python\n" + self.source.rstrip() + "\n```"
        elif self.kind == "markdown":
            result = self.source.rstrip()
        else:
            logger.error("VeyraNotebookCell.as_markdown_block invalid kind=%s", self.kind)
            raise ValueError("kind must be markdown or code")
        logger.debug("VeyraNotebookCell.as_markdown_block exit chars=%d", len(result))
        return result


@dataclass(frozen=True)
class VeyraNotebook:
    """Generated Sage-lab notebook artifact."""

    title: str
    cells: tuple[VeyraNotebookCell, ...]

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraNotebook({self.title!r}, cells={len(self.cells)})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def summary(self) -> dict[str, int]:
        """Return compact notebook summary."""
        logger.debug("VeyraNotebook.summary entry title=%s", self.title)
        result = {"cells": len(self.cells), "markdown": sum(1 for cell in self.cells if cell.kind == "markdown"), "code": sum(1 for cell in self.cells if cell.kind == "code")}
        logger.debug("VeyraNotebook.summary exit result=%r", result)
        return result

    def to_markdown(self) -> str:
        """Render notebook as markdown with fenced code cells."""
        logger.debug("VeyraNotebook.to_markdown entry cells=%d", len(self.cells))
        result = "\n\n".join(cell.as_markdown_block() for cell in self.cells) + "\n"
        logger.debug("VeyraNotebook.to_markdown exit chars=%d", len(result))
        return result

    def to_ipynb_dict(self) -> dict[str, object]:
        """Render notebook as nbformat v4 dictionary."""
        logger.debug("VeyraNotebook.to_ipynb_dict entry cells=%d", len(self.cells))
        result = {"cells": [cell.as_ipynb_cell() for cell in self.cells], "metadata": {"language_info": {"name": "python"}, "veyra": {"title": self.title}}, "nbformat": 4, "nbformat_minor": 5}
        logger.debug("VeyraNotebook.to_ipynb_dict exit cells=%d", len(result["cells"]))
        return result

    def write_markdown(self, path: str | Path) -> Path:
        """Write markdown rendering and return path."""
        logger.debug("VeyraNotebook.write_markdown entry path=%s", path)
        target = Path(path)
        target.write_text(self.to_markdown(), encoding="utf-8", newline="\n")
        logger.debug("VeyraNotebook.write_markdown exit path=%s", target)
        return target

    def write_ipynb(self, path: str | Path) -> Path:
        """Write ipynb JSON rendering and return path."""
        logger.debug("VeyraNotebook.write_ipynb entry path=%s", path)
        target = Path(path)
        target.write_text(
            json.dumps(self.to_ipynb_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        logger.debug("VeyraNotebook.write_ipynb exit path=%s", target)
        return target


def build_school_proof_notebook(title: str = "Veyra School Proof Graph Lab") -> VeyraNotebook:
    """Build a Sage-lab notebook from current school/proof registries."""
    logger.debug("build_school_proof_notebook entry title=%s", title)
    school = VeyraSchoolCore()
    graph = VeyraProofGraph()
    school_summary = school.summary()
    graph_summary = graph.summary()
    path = graph.curriculum_path("arithmetic-ratios", "statistics")
    domains = graph.domain_index()
    cells = (
        VeyraNotebookCell("markdown", f"# {title}\n\nGenerated from Veyra school-core and proof graph facades."),
        VeyraNotebookCell("markdown", f"## Snapshot\n\n- theorem specs: {school_summary['theorem_specs']}\n- definition edges: {graph_summary['definition_edges']}\n- curriculum nodes: {school_summary['curriculum_nodes']}\n- curriculum edges: {graph_summary['curriculum_edges']}\n- export rows: {len(school.export_rows())}"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraSchoolCore, VeyraProofGraph\nS = VeyraSchoolCore()\nG = VeyraProofGraph()"),
        VeyraNotebookCell("code", "S.summary()\nG.summary()"),
        VeyraNotebookCell("markdown", "## Curriculum path\n\nArithmetic-to-statistics path: `" + " → ".join(path) + "`."),
        VeyraNotebookCell("code", "G.curriculum_path('arithmetic-ratios', 'statistics')"),
        VeyraNotebookCell("markdown", "## Sage-hook domains\n\n" + "\n".join(f"- `{domain}`: {len(items)} theorem(s)" for domain, items in domains.items())),
        VeyraNotebookCell("code", "G.domain_index()\nS.export_dicts()[:3]"),
    )
    result = VeyraNotebook(title, cells)
    logger.debug("build_school_proof_notebook exit cells=%d", len(cells))
    return result


@dataclass(frozen=True)
class VeyraDomainNotebookSpec:
    """Descriptor for one generated domain notebook."""

    domain: str
    theorem_ids: tuple[str, ...]
    cells: int

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraDomainNotebookSpec({self.domain}:{len(self.theorem_ids)})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready spec dictionary."""
        logger.debug("VeyraDomainNotebookSpec.as_dict entry domain=%s", self.domain)
        result = {"domain": self.domain, "theorem_ids": self.theorem_ids, "cells": self.cells}
        logger.debug("VeyraDomainNotebookSpec.as_dict exit theorems=%d", len(self.theorem_ids))
        return result


def available_notebook_domains() -> tuple[str, ...]:
    """Return domains with generated theorem notebooks."""
    logger.debug("available_notebook_domains entry")
    result = tuple(VeyraProofGraph().domain_index())
    logger.debug("available_notebook_domains exit count=%d", len(result))
    return result


def domain_notebook_spec(domain: str) -> VeyraDomainNotebookSpec:
    """Return descriptor for one domain notebook."""
    logger.debug("domain_notebook_spec entry domain=%s", domain)
    domains = VeyraProofGraph().domain_index()
    if domain not in domains:
        logger.error("domain_notebook_spec unknown domain=%s", domain)
        raise KeyError(domain)
    result = VeyraDomainNotebookSpec(domain, domains[domain], 8)
    logger.debug("domain_notebook_spec exit theorems=%d", len(result.theorem_ids))
    return result


def build_domain_theorem_notebook(domain: str) -> VeyraNotebook:
    """Build an interactive theorem notebook for one Sage-hook domain."""
    logger.debug("build_domain_theorem_notebook entry domain=%s", domain)
    spec = domain_notebook_spec(domain)
    graph = VeyraProofGraph()
    objects = graph.proof_objects(domain)
    theorem_lines = "\n".join(f"- `{obj.theorem_id}` — {obj.title}" for obj in objects)
    dep_lines = "\n".join(f"- `{obj.theorem_id}`: {', '.join(obj.dependencies)}" for obj in objects)
    ids_literal = repr(spec.theorem_ids)
    cells = (
        VeyraNotebookCell("markdown", f"# Veyra {domain} theorem lab\n\nGenerated domain notebook for `{domain}` Sage hooks."),
        VeyraNotebookCell("markdown", f"## Domain snapshot\n\n- domain: `{domain}`\n- theorem objects: {len(objects)}\n- notebook cells: {spec.cells}"),
        VeyraNotebookCell("code", f"from veyra_sage.all import VeyraProofGraph\nG = VeyraProofGraph()\ndomain = {domain!r}\ntheorem_ids = {ids_literal}"),
        VeyraNotebookCell("code", "objects = G.proof_objects(domain)\n[obj.as_dict() for obj in objects]"),
        VeyraNotebookCell("markdown", "## Theorem catalogue\n\n" + theorem_lines),
        VeyraNotebookCell("code", "{item: G.definition_dependencies(item) for item in theorem_ids}"),
        VeyraNotebookCell("markdown", "## Dependency ledger\n\n" + dep_lines),
        VeyraNotebookCell("code", "[(obj.theorem_id, obj.success_relations, obj.obstruction_catalog) for obj in objects]"),
    )
    result = VeyraNotebook(f"Veyra {domain} theorem lab", cells)
    logger.debug("build_domain_theorem_notebook exit cells=%d", len(cells))
    return result


def build_all_domain_notebooks() -> dict[str, VeyraNotebook]:
    """Build notebooks for every current Sage-hook domain."""
    logger.debug("build_all_domain_notebooks entry")
    result = {domain: build_domain_theorem_notebook(domain) for domain in available_notebook_domains()}
    logger.debug("build_all_domain_notebooks exit count=%d", len(result))
    return result
