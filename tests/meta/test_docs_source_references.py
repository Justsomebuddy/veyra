"""Every repository path cited in documentation must exist.

Documentation carries the evidence trail for claim discipline, so a stale
source reference is a provenance error rather than a cosmetic one.
"""
from __future__ import annotations

import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

CITED = re.compile(
    r"(?<![\w/.])((?:src|proofs|scripts|tests|vam|veyra_sage|experimental|data|notebooks)"
    r"/[A-Za-z0-9_./-]+\.(?:py|lean|md|json|toml|rs|yml|cff))"
)
GENERATED_PREFIXES = ("data/processed/", "data/tmp/", "notebooks/generated/", "vam/native/target/")
# release history records the tree as it was; it is not rewritten to match today
HISTORICAL = ("releases/",)


def _citations(docs: Path, repo_root: Path) -> dict[str, set[str]]:
    logger.debug("_citations entry docs=%s", docs)
    found: dict[str, set[str]] = {}
    for document in sorted(docs.rglob("*.md")):
        if document.relative_to(docs).as_posix().startswith(HISTORICAL):
            continue
        for cited in CITED.findall(document.read_text(encoding="utf-8")):
            if cited.startswith(GENERATED_PREFIXES):
                continue
            found.setdefault(cited, set()).add(str(document.relative_to(repo_root)))
    logger.debug("_citations exit paths=%d", len(found))
    return found


# a link target, as opposed to inline mathematical notation, is path-like
MARKDOWN_LINK = re.compile(
    r"\[[^\]]*\]\((?!https?://|mailto:)([^)\s#]*[/.][^)\s#]*)(?:#[^)\s]*)?\)"
)
LINKABLE_SUFFIXES = {".md", ".py", ".lean", ".json", ".toml", ".cff", ".rs", ".yml", ".ipynb"}


def test_documentation_markdown_links_resolve(repo_root: Path) -> None:
    """Reject relative markdown links that point at nothing."""
    logger.debug("test_documentation_markdown_links_resolve entry")
    broken: list[str] = []
    checked = 0
    docs = repo_root / "docs"
    for document in sorted(docs.rglob("*.md")):
        if document.relative_to(docs).as_posix().startswith(HISTORICAL):
            continue
        for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            if Path(target).suffix not in LINKABLE_SUFFIXES:
                continue
            checked += 1
            if not (document.parent / target).resolve().exists():
                broken.append(f"{document.relative_to(repo_root)} -> {target}")
    assert checked, "expected documentation to contain relative links"
    assert not broken, "documentation has broken links:\n" + "\n".join(broken)
    logger.debug("test_documentation_markdown_links_resolve exit links=%d", checked)


def test_documentation_cites_only_existing_repository_paths(repo_root: Path) -> None:
    """Reject documentation references to files the repository does not hold."""
    logger.debug("test_documentation_cites_only_existing_repository_paths entry")
    citations = _citations(repo_root / "docs", repo_root)
    assert citations, "expected documentation to cite repository paths"
    missing = sorted(
        f"{path} <- {', '.join(sorted(sources))}"
        for path, sources in citations.items()
        if not (repo_root / path).exists()
    )
    assert not missing, "documentation cites missing paths:\n" + "\n".join(missing)
    logger.debug(
        "test_documentation_cites_only_existing_repository_paths exit paths=%d",
        len(citations),
    )
