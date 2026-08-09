"""Repository-anchored locations for artifacts the core reads and writes.

Anchoring on ``__file__`` rather than the process working directory keeps these
roots correct however the code is invoked: from a subdirectory, from a build
sandbox, or through an entry point that never enters the checkout.

Repository-relative *strings* hashed into proof ledgers (``ARTIFACT_PATH`` and
friends) are identities rather than locations; they stay relative and are not
derived from these values.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
TMP_DIR = PROJECT_ROOT / "data" / "tmp"


def lean_artifact(name: str) -> Path:
    """Resolve one checked Lean source by file name."""
    logger.debug("paths.lean_artifact entry name=%s", name)
    if not name or "/" in name or not name.endswith(".lean"):
        raise ValueError("invalid-lean-artifact-name")
    return LEAN_DIR / name
