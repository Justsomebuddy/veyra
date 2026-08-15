"""Adversarial source-distribution extraction checks."""

from __future__ import annotations

from io import BytesIO
import logging
from pathlib import Path
import tarfile

import pytest

import scripts.package_smoke as package_smoke

logger = logging.getLogger(__name__)


def _write_sdist(path: Path, rows: tuple[tuple[str, bytes, str], ...]) -> None:
    """Write a small synthetic gzip tar with explicit member kinds."""
    logger.debug("test_package_smoke_archive._write_sdist entry path=%s rows=%d", path, len(rows))
    with tarfile.open(path, "w:gz") as archive:
        for name, payload, kind in rows:
            member = tarfile.TarInfo(name)
            if kind == "file":
                member.size = len(payload)
                archive.addfile(member, BytesIO(payload))
            elif kind == "dir":
                member.type = tarfile.DIRTYPE
                archive.addfile(member)
            elif kind == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "target"
                archive.addfile(member)
            else:  # pragma: no cover - test helper misuse guard
                logger.error("test archive helper rejected member kind=%r", kind)
                raise AssertionError(f"unknown archive member kind: {kind}")
    logger.debug("test_package_smoke_archive._write_sdist exit path=%s", path)


def _extractall_spy(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Record extraction attempts while retaining the real implementation."""
    logger.debug("test_package_smoke_archive._extractall_spy entry")
    calls: list[Path] = []
    original = tarfile.TarFile.extractall

    def recording_extractall(self, path=".", members=None, *, numeric_owner=False, filter=None):
        logger.debug("test package archive extractall call path=%s", path)
        calls.append(Path(path))
        result = original(
            self,
            path,
            members=members,
            numeric_owner=numeric_owner,
            filter=filter,
        )
        logger.debug("test package archive extractall return path=%s", path)
        return result

    monkeypatch.setattr(tarfile.TarFile, "extractall", recording_extractall)
    logger.debug("test_package_smoke_archive._extractall_spy exit")
    return calls


def test_extract_sdist_accepts_a_bounded_regular_archive(tmp_path: Path) -> None:
    """A normal single-root sdist extracts after validation."""
    logger.debug("test normal sdist extraction entry")
    sdist = tmp_path / "normal.tar.gz"
    _write_sdist(
        sdist,
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/src/module.py", b"VALUE = 1\n", "file"),
        ),
    )
    root = package_smoke.extract_sdist(sdist, tmp_path / "destination")
    assert root == tmp_path / "destination" / "veyra-1"
    assert (root / "src/module.py").read_bytes() == b"VALUE = 1\n"
    logger.debug("test normal sdist extraction exit root=%s", root)


@pytest.mark.parametrize(
    ("limit_name", "limit", "expected"),
    (
        ("MAX_SDIST_MEMBERS", 1, "sdist-member-limit-exceeded"),
        ("MAX_SDIST_UNCOMPRESSED_BYTES", 15, "sdist-uncompressed-size-limit-exceeded"),
    ),
)
def test_extract_sdist_rejects_resource_overflow_before_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    limit: int,
    expected: str,
) -> None:
    """Member-count and expanded-byte limits fail before filesystem writes."""
    logger.debug("test sdist resource overflow entry limit=%s", limit_name)
    sdist = tmp_path / "overflow.tar.gz"
    _write_sdist(
        sdist,
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/src/module.py", b"VALUE = 1\n", "file"),
        ),
    )
    monkeypatch.setattr(package_smoke, limit_name, limit)
    calls = _extractall_spy(monkeypatch)
    destination = tmp_path / "destination"
    with pytest.raises(RuntimeError, match=expected):
        package_smoke.extract_sdist(sdist, destination)
    assert calls == []
    assert tuple(destination.iterdir()) == ()
    logger.debug("test sdist resource overflow exit limit=%s", limit_name)


def test_extract_sdist_validates_all_members_before_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A late unsafe member cannot leave an earlier regular file behind."""
    logger.debug("test complete sdist validation entry")
    sdist = tmp_path / "unsafe.tar.gz"
    _write_sdist(
        sdist,
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/link", b"", "symlink"),
        ),
    )
    calls = _extractall_spy(monkeypatch)
    destination = tmp_path / "destination"
    with pytest.raises(RuntimeError, match="sdist-unsafe-member"):
        package_smoke.extract_sdist(sdist, destination)
    assert calls == []
    assert tuple(destination.iterdir()) == ()
    logger.debug("test complete sdist validation exit")


def test_extract_sdist_validates_root_before_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A structurally invalid root cannot produce partial output."""
    logger.debug("test sdist root validation entry")
    sdist = tmp_path / "wrong-root.tar.gz"
    _write_sdist(
        sdist,
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("second-root/module.py", b"VALUE = 1\n", "file"),
        ),
    )
    calls = _extractall_spy(monkeypatch)
    destination = tmp_path / "destination"
    with pytest.raises(RuntimeError, match="sdist-root-mismatch"):
        package_smoke.extract_sdist(sdist, destination)
    assert calls == []
    assert tuple(destination.iterdir()) == ()
    logger.debug("test sdist root validation exit")


@pytest.mark.parametrize(
    "rows",
    (
        (
            ("veyra-1", b"root-file", "file"),
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
        ),
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/./pyproject.toml", b"replacement\n", "file"),
        ),
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1", b"", "dir"),
        ),
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/Module.py", b"VALUE = 1\n", "file"),
            ("veyra-1/module.py", b"VALUE = 2\n", "file"),
        ),
        (
            ("veyra-1/pyproject.toml", b"[build-system]\n", "file"),
            ("veyra-1/dir/module.py", b"VALUE = 1\n", "file"),
            ("veyra-1/dir\\module.py", b"VALUE = 2\n", "file"),
        ),
    ),
)
def test_extract_sdist_rejects_portable_path_conflicts_before_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rows: tuple[tuple[str, bytes, str], ...],
) -> None:
    """Aliases and file/directory hierarchy conflicts cannot write output."""
    logger.debug("test portable sdist conflict entry rows=%d", len(rows))
    sdist = tmp_path / "portable-conflict.tar.gz"
    _write_sdist(sdist, rows)
    calls = _extractall_spy(monkeypatch)
    destination = tmp_path / "destination"
    with pytest.raises(RuntimeError, match="sdist-unsafe-member"):
        package_smoke.extract_sdist(sdist, destination)
    assert calls == []
    assert tuple(destination.iterdir()) == ()
    logger.debug("test portable sdist conflict exit")
