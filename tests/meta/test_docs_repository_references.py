"""Static integrity checks for documentation links and source references."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit

from src.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

REPOSITORY_SOURCE_REFERENCE = re.compile(
    r"(?<![\w/.])((?:data|docs|experimental|notebooks|proofs|scripts|src|tests|vam|veyra_sage)"
    r"/[A-Za-z0-9_./-]+\.(?:cff|ipynb|json|lean|md|py|pyi|rs|sh|toml|yaml|yml))"
)
RELATIVE_MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(((?![A-Za-z][A-Za-z0-9+.-]*:)[^)\s#]*[/.][^)\s#]*)(?:#[^)\s]*)?\)"
)
GENERATED_REPOSITORY_ROOTS = (
    "data/processed",
    "data/tmp",
    "notebooks/generated",
    "vam/native/target",
)
TOP_LEVEL_PUBLIC_DOCUMENTS = (
    "README.md",
    "CONTRIBUTING.md",
    "THEOREMS.md",
    "NOTATION.md",
    "SECURITY.md",
    "CHANGELOG.md",
)
HISTORICAL_DOC_PREFIXES = ("docs/releases/",)
# Changelog prose is an immutable record of the tree at that release.  Keep
# any vanished historical identity explicit rather than exempting the file.
HISTORICAL_SOURCE_REFERENCE_EXCEPTIONS = frozenset(
    {("CHANGELOG.md", "src/core/MODULE_LOG.md")}
)


def _public_repository_candidates(root: Path) -> frozenset[str]:
    """Return tracked and non-ignored untracked paths eligible for publication."""
    logger.debug("meta public repository candidate inventory entry root=%s", root)
    try:
        result = subprocess.run(
            [
                "git", "-C", str(root), "ls-files", "--cached", "--others",
                "--exclude-standard", "-z",
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.error("meta public repository candidate inventory failed error=%s", type(exc).__name__)
        raise
    candidates = frozenset(os.fsdecode(item) for item in result.stdout.split(b"\0") if item)
    logger.debug("meta public repository candidate inventory exit count=%d", len(candidates))
    return candidates


def _is_public_candidate(identity: str, candidates: frozenset[str]) -> bool:
    """Accept one publishable file or a directory containing publishable files."""
    logger.debug("meta public repository candidate check entry identity=%s", identity)
    prefix = f"{identity.rstrip('/')}/"
    result = identity in candidates or any(path.startswith(prefix) for path in candidates)
    logger.debug("meta public repository candidate check exit public=%s", result)
    return result


def _documentation_files(root: Path) -> tuple[Path, ...]:
    """Return public Markdown while excluding only immutable release snapshots."""
    logger.debug("meta documentation inventory entry root=%s", root)
    candidates = [root / identity for identity in TOP_LEVEL_PUBLIC_DOCUMENTS]
    candidates.extend(sorted((root / "docs").rglob("*.md")))
    result = tuple(
        path
        for path in candidates
        if not path.relative_to(root).as_posix().startswith(HISTORICAL_DOC_PREFIXES)
    )
    logger.debug("meta documentation inventory exit files=%d", len(result))
    return result


def _is_generated_reference(identity: str) -> bool:
    """Return whether a reference names an explicitly generated tree."""
    logger.debug("meta generated documentation reference entry identity=%s", identity)
    result = any(identity == root or identity.startswith(f"{root}/") for root in GENERATED_REPOSITORY_ROOTS)
    logger.debug("meta generated documentation reference exit generated=%s", result)
    return result


def _repository_source_references(documents: tuple[Path, ...], root: Path) -> dict[str, set[str]]:
    """Collect repository-root-relative source citations and their documents."""
    logger.debug("meta repository source reference scan entry documents=%d", len(documents))
    found: dict[str, set[str]] = {}
    for document in documents:
        document_identity = document.relative_to(root).as_posix()
        for identity in REPOSITORY_SOURCE_REFERENCE.findall(document.read_text(encoding="utf-8")):
            if _is_generated_reference(identity):
                continue
            if (document_identity, identity) in HISTORICAL_SOURCE_REFERENCE_EXCEPTIONS:
                continue
            found.setdefault(identity, set()).add(document_identity)
    logger.debug("meta repository source reference scan exit identities=%d", len(found))
    return found


def test_documentation_relative_markdown_links_resolve() -> None:
    """Reject path-shaped relative Markdown links that escape or do not exist."""
    logger.debug("test documentation relative Markdown links entry")
    root = PROJECT_ROOT.resolve()
    documents = _documentation_files(root)
    candidates = _public_repository_candidates(root)
    violations: list[str] = []
    checked = 0

    for document in documents:
        for encoded_target in RELATIVE_MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            target = unquote(urlsplit(encoded_target).path)
            checked += 1
            resolved = (document.parent / target).resolve(strict=False)
            location = f"{document.relative_to(root).as_posix()} -> {encoded_target}"
            if not resolved.is_relative_to(root):
                violations.append(f"escapes repository: {location}")
            elif not resolved.exists():
                violations.append(f"missing: {location}")
            else:
                identity = resolved.relative_to(root).as_posix()
                if not _is_public_candidate(identity, candidates):
                    violations.append(f"not a public candidate: {location}")

    if not checked:
        logger.error("test documentation relative Markdown links found no path links")
    if violations:
        logger.error("test documentation relative Markdown links violations=%d", len(violations))
    assert checked, "expected documentation to contain relative path links"
    assert not violations, "broken relative Markdown links:\n" + "\n".join(violations)
    logger.debug("test documentation relative Markdown links exit checked=%d", checked)


def test_documentation_repository_source_references_exist() -> None:
    """Reject current documentation citations to missing repository sources."""
    logger.debug("test documentation repository source references entry")
    root = PROJECT_ROOT.resolve()
    references = _repository_source_references(_documentation_files(root), root)
    candidates = _public_repository_candidates(root)
    missing: list[str] = []
    for identity, sources in sorted(references.items()):
        normalized = PurePosixPath(identity)
        target = root.joinpath(*normalized.parts).resolve(strict=False)
        if (
            not target.is_relative_to(root)
            or not target.exists()
            or not _is_public_candidate(identity, candidates)
        ):
            missing.append(f"{identity} <- {', '.join(sorted(sources))}")

    if not references:
        logger.error("test documentation repository source references found no citations")
    if missing:
        logger.error("test documentation repository source references missing=%d", len(missing))
    assert references, "expected documentation to cite repository sources"
    assert not missing, "documentation cites missing repository sources:\n" + "\n".join(missing)
    logger.debug("test documentation repository source references exit checked=%d", len(references))
