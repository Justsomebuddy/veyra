"""Strict repository-path resolution for source-checkout operations.

Logical artifact identifiers remain repository-relative POSIX strings.  This
module resolves those identifiers only at filesystem boundaries so callers do
not depend on their current working directory and reports never publish a local
absolute path.
"""

from __future__ import annotations

from importlib.util import find_spec
import logging
import os
from pathlib import Path, PurePosixPath

logger = logging.getLogger(__name__)
PROJECT_ROOT_ENV = "VEYRA_PROJECT_ROOT"


def _installed_root() -> Path:
    """Return the directory containing the installed top-level packages."""
    logger.debug("paths._installed_root entry")
    spec = find_spec("src")
    locations = () if spec is None or spec.submodule_search_locations is None else tuple(spec.submodule_search_locations)
    if len(locations) != 1:
        logger.error("paths package root unavailable locations=%d", len(locations))
        raise RuntimeError("veyra-package-root-unavailable")
    result = Path(locations[0]).resolve().parent
    logger.debug("paths._installed_root exit root=%s", result)
    return result


def _validate_override(value: str) -> Path:
    """Validate one explicit source-checkout root without guessing."""
    logger.debug("paths._validate_override entry chars=%d", len(value))
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        logger.error("paths override is not absolute")
        raise ValueError("veyra-project-root-not-absolute")
    result = candidate.resolve()
    if not (result / "pyproject.toml").is_file() or not (result / "src" / "core").is_dir():
        logger.error("paths override is not a Veyra source root path=%s", result)
        raise ValueError("veyra-project-root-invalid")
    logger.debug("paths._validate_override exit root=%s", result)
    return result


def project_root() -> Path:
    """Return the explicit source root or the package installation root."""
    logger.debug("paths.project_root entry")
    override = os.environ.get(PROJECT_ROOT_ENV)
    result = _validate_override(override) if override else _installed_root()
    logger.debug("paths.project_root exit override=%s root=%s", override is not None, result)
    return result


def repository_path(identity: str | PurePosixPath) -> Path:
    """Resolve one validated repository-relative POSIX identity."""
    logger.debug("paths.repository_path entry identity=%s", identity)
    raw = str(identity)
    relative = PurePosixPath(raw)
    if (
        raw in {"", "."}
        or "\\" in raw
        or raw != relative.as_posix()
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        logger.error("paths invalid repository identity=%r", raw)
        raise ValueError("invalid-repository-path-identity")
    root = PROJECT_ROOT.resolve()
    result = root.joinpath(*relative.parts).resolve(strict=False)
    if not result.is_relative_to(root):
        logger.error("paths repository identity escapes root identity=%r", raw)
        raise ValueError("repository-path-escapes-root")
    logger.debug("paths.repository_path exit path=%s", result)
    return result


def lean_artifact(name: str) -> Path:
    """Resolve one checked Lean source filename under ``proofs/lean``."""
    logger.debug("paths.lean_artifact entry name=%s", name)
    if not name or PurePosixPath(name).name != name or not name.endswith(".lean"):
        logger.error("paths invalid Lean artifact name=%r", name)
        raise ValueError("invalid-lean-artifact-name")
    result = repository_path(f"proofs/lean/{name}")
    logger.debug("paths.lean_artifact exit path=%s", result)
    return result


PROJECT_ROOT = project_root()
LEAN_DIR = repository_path("proofs/lean")
TMP_DIR = repository_path("data/tmp")
