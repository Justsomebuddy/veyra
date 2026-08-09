"""Publication portability checks for the R13 formal toolchain identity."""
from __future__ import annotations

import logging
from pathlib import Path

from src.core.intrinsic_observer_echo_formal_manifest import EXPECTED_TOOLCHAIN_IDENTITY

logger = logging.getLogger(__name__)


def test_toolchain_identity_is_content_bound_and_host_path_independent() -> None:
    """Require logical names plus content hashes, never host-local metadata."""
    logger.debug("test R13 portable toolchain identity entry")
    assert "toolchain=leanprover/lean4:v4.30.0-rc2" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "binary=lean" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "sha256=" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "merkle=" in EXPECTED_TOOLCHAIN_IDENTITY
    fields = {
        name: value
        for field in EXPECTED_TOOLCHAIN_IDENTITY.split("|")[1:]
        if "=" in field
        for name, value in (field.split("=", 1),)
    }
    assert {"path", "inode", "mtime"}.isdisjoint(fields)
    assert not Path(fields["binary"]).is_absolute()
    assert not Path(fields["toolchain"]).is_absolute()
    logger.debug("test R13 portable toolchain identity exit")
