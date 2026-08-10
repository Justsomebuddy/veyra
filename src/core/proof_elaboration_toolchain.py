"""Deterministic Merkle binding for the pinned Lean runtime closure."""
from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path
import stat

from .platform_posix import user_home

logger = logging.getLogger(__name__)
TOOLCHAIN_ROOT = (
    user_home() / ".elan/toolchains"
    / "leanprover--lean4---v4.30.0-rc2"
)
LEAN_BINARY = TOOLCHAIN_ROOT / "bin/lean"
RUNTIME_DOMAIN = b"veyra-r10-lean-runtime-v1\0"
GUARDED_INPUT_DOMAIN = b"veyra-r10-guarded-input-v1\0"
_FIXED_RUNTIME = (
    "bin/lean",
    "lib/lean/libInit_shared.so",
    "lib/lean/libleanshared.so",
    "lib/lean/libleanshared_1.so",
    "lib/lean/libleanshared_2.so",
)


def runtime_closure_paths() -> tuple[Path, ...]:
    """Enumerate launcher, native libraries, and every observed Init olean/IR input."""
    logger.debug("runtime_closure_paths entry root=%s", TOOLCHAIN_ROOT)
    paths = [TOOLCHAIN_ROOT / name for name in _FIXED_RUNTIME]
    lean_lib = TOOLCHAIN_ROOT / "lib/lean"
    paths.extend(lean_lib.glob("Init.olean*"))
    paths.extend(lean_lib.glob("Init.ir"))
    paths.extend((lean_lib / "Init").rglob("*.olean*"))
    paths.extend((lean_lib / "Init").rglob("*.ir"))
    result = tuple(sorted(set(paths), key=lambda path: path.relative_to(TOOLCHAIN_ROOT).as_posix()))
    logger.debug("runtime_closure_paths exit count=%d", len(result))
    return result


def _file_digest(path: Path) -> tuple[int, bytes]:
    logger.debug("proof_elaboration_toolchain._file_digest entry path=%s", path)
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("r10-lean-runtime-file-not-regular")
        digest = sha256()
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            identity = (metadata.st_dev, metadata.st_ino, metadata.st_size)
            if identity != (opened.st_dev, opened.st_ino, opened.st_size):
                raise ValueError("r10-lean-runtime-file-raced")
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
            finished = os.fstat(stream.fileno())
        if (opened.st_size, opened.st_mtime_ns) != (finished.st_size, finished.st_mtime_ns):
            raise ValueError("r10-lean-runtime-file-raced")
    except OSError as exc:
        logger.error("proof_elaboration_toolchain runtime unreadable path=%s", path)
        raise ValueError("r10-lean-runtime-unreadable") from exc
    result = metadata.st_size, digest.digest()
    logger.debug("proof_elaboration_toolchain._file_digest exit bytes=%d", result[0])
    return result


def records_digest(
    records: tuple[tuple[Path, int, bytes], ...], root: Path, domain: bytes,
) -> tuple[str, int, int]:
    """Merkle-bind reviewed path, size, and SHA-256 records under one root."""
    logger.debug("records_digest entry records=%d root=%s", len(records), root)
    if not domain or any(size < 0 or len(content) != 32 for _, size, content in records):
        raise ValueError("r10-digest-record-invalid")
    ordered = tuple(sorted(records, key=lambda row: row[0].relative_to(root).as_posix()))
    if len({path for path, _, _ in ordered}) != len(ordered):
        raise ValueError("r10-digest-record-duplicate")
    digest = sha256(domain)
    total = 0
    for path, size, content_digest in ordered:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(size.to_bytes(8, "big"))
        digest.update(content_digest)
        total += size
    result = digest.hexdigest(), len(ordered), total
    logger.debug("records_digest exit digest=%s files=%d bytes=%d", *result)
    return result


def paths_digest(
    paths: tuple[Path, ...], root: Path, domain: bytes,
) -> tuple[str, int, int]:
    """Read and Merkle-bind one explicitly enumerated regular-file closure."""
    logger.debug("paths_digest entry paths=%d root=%s", len(paths), root)
    ordered = tuple(sorted(set(paths), key=lambda path: path.relative_to(root).as_posix()))
    records = tuple((path, *_file_digest(path)) for path in ordered)
    result = records_digest(records, root, domain)
    logger.debug("paths_digest exit digest=%s files=%d bytes=%d", *result)
    return result


def runtime_paths_digest(
    paths: tuple[Path, ...], root: Path,
) -> tuple[str, int, int]:
    """Merkle-bind one runtime closure using its fixed domain."""
    logger.debug("runtime_paths_digest entry paths=%d root=%s", len(paths), root)
    result = paths_digest(paths, root, RUNTIME_DOMAIN)
    logger.debug("runtime_paths_digest exit digest=%s files=%d bytes=%d", *result)
    return result


def lean_runtime_digest() -> tuple[str, int, int]:
    """Hash path, size, and content of the complete reviewed runtime closure."""
    logger.debug("lean_runtime_digest entry")
    paths = runtime_closure_paths()
    if len(paths) < 1000:
        logger.error("lean_runtime_digest incomplete closure count=%d", len(paths))
        raise ValueError("r10-lean-runtime-closure-incomplete")
    result = runtime_paths_digest(paths, TOOLCHAIN_ROOT)
    logger.debug("lean_runtime_digest exit digest=%s files=%d bytes=%d", *result)
    return result
