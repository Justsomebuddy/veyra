"""Non-authoritative P3-N6 E parser with bounded source-integrity checks."""

from __future__ import annotations

import hashlib
import logging
import os
import stat
from typing import cast

from .padic.completion.common import PadicCompletionValidationError
from .padic.completion.package import snapshot_package as snapshot_pomega2
from .padic.family_introduction.common import PadicFamilyIntroductionValidationError
from .padic.family_introduction.package import snapshot_package as snapshot_n1
from .prime_power_unbounded_common import digest, exact_digest, exact_shape, reject
from .prime_power_unbounded_capture import _open_project_root
from .prime_power_unbounded_preflight import preflight_e_request
from .prime_power_unbounded_sources import (
    policy, snapshot_policy, snapshot_theorem_source, theorem_source,
)
from .prime_power_unbounded_types import (
    N6ERawRequestV1, N6ERequestV1, N6Lane, N6PolicyV1,
    N6TheoremSourceV1, N6_E_RAW_REQUEST_LAYOUT,
)

logger = logging.getLogger(__name__)


def _signature(fd: int) -> tuple[int, ...]:
    logger.debug("_signature entry")
    try:
        metadata = os.fstat(fd)
    except OSError:
        logger.error("_signature fstat failed")
        reject("n6-source-fstat-failed")
    result = (
        metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns,
    )
    logger.debug("_signature exit size=%d", metadata.st_size)
    return result


def _hash_fd(fd: int, size: int) -> str:
    logger.debug("_hash_fd entry size=%d", size)
    hasher, offset = hashlib.sha256(), 0
    try:
        while offset < size:
            chunk = os.pread(fd, min(131072, size - offset), offset)
            if not chunk:
                reject("n6-source-fd-byte-continuity-drift")
            hasher.update(chunk)
            offset += len(chunk)
        if os.pread(fd, 1, size):
            reject("n6-source-fd-byte-continuity-drift")
    except OSError:
        logger.error("_hash_fd read failed")
        reject("n6-source-fd-read-failed")
    result = hasher.hexdigest()
    logger.debug("_hash_fd exit bytes=%d", offset)
    return result


def _open_component(parent_fd: int, component: str, directory: bool) -> int:
    logger.debug("_open_component entry directory=%s", directory)
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    try:
        result = os.open(component, flags, dir_fd=parent_fd)
    except OSError:
        logger.error("_open_component unavailable-or-symlinked directory=%s", directory)
        reject("n6-fixed-source-unavailable-or-symlinked")
    logger.debug("_open_component exit directory=%s", directory)
    return result


def _capture_source(
    root_fd: int, source_id: str, path_text: str, expected_sha: str
) -> tuple[str, tuple[int, ...], str]:
    """Acquire, verify and close one source before returning immutable metadata."""
    logger.debug("_capture_source entry source_id=%s", source_id)
    parts = path_text.split("/")
    if path_text.startswith("/") or not parts or any(p in ("", ".", "..") for p in parts):
        reject("n6-fixed-source-path-invalid")
    opened: list[int] = []
    final_fd: int | None = None
    try:
        current = root_fd
        for component in parts[:-1]:
            directory_fd = _open_component(current, component, True)
            opened.append(directory_fd)
            current = directory_fd
        final_fd = _open_component(current, parts[-1], False)
        before = _signature(final_fd)
        if not stat.S_ISREG(before[2]) or not 0 <= before[3] <= 3 * 1024 * 1024:
            reject("n6-fixed-source-type-or-size-invalid")
        content_sha = _hash_fd(final_fd, before[3])
        after = _signature(final_fd)
        if before != after:
            reject("n6-source-handle-continuity-drift")
        if content_sha != expected_sha:
            reject("n6-fixed-source-byte-digest-mismatch")
        result = source_id, before, content_sha
    finally:
        if final_fd is not None:
            try:
                os.close(final_fd)
            except OSError:
                logger.error("P3-N6 final source fd close failed")
        for directory_fd in reversed(opened):
            try:
                os.close(directory_fd)
            except OSError:
                logger.error("P3-N6 source directory fd close failed")
    logger.debug("_capture_source exit source_id=%s", source_id)
    return result


def _capture_all(root_fd: int) -> tuple[tuple[str, tuple[int, ...], str], ...]:
    """Capture the exact owned sources without consulting mutable module data."""
    logger.debug("_capture_all entry")
    specs = (
        ("n6", "proofs/lean/VeyraPrimePowerUnbounded.lean",
         "d35ead8dca26e0a07842ad830a143dab36b94b6ff201e79fd16dce9a81305b1c"),
        ("n1", "proofs/lean/VeyraPadicFamilyIntroduction.lean",
         "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48"),
        ("pomega2", "proofs/lean/VeyraPadicCompletion.lean",
         "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f"),
    )
    result = tuple(_capture_source(root_fd, *spec) for spec in specs)
    logger.debug("_capture_all exit sources=%d", len(result))
    return result


def dispatch_e_request(raw_request: N6ERawRequestV1) -> N6ERequestV1:
    """Parse/replay E input; this Python function grants no positive authority."""
    logger.debug("dispatch_e_request entry state=non-authoritative-parser")
    charge = preflight_e_request(raw_request)
    raw = exact_shape(raw_request, N6_E_RAW_REQUEST_LAYOUT, "n6-dispatch-e-raw-request")
    root_fd: int | None = None
    try:
        root_fd, _ = _open_project_root()
        if not stat.S_ISDIR(_signature(root_fd)[2]):
            reject("n6-project-root-not-directory")
        before = _capture_all(root_fd)
        source_bytes = sum(item[1][3] for item in before)
        if charge.captured_bytes + source_bytes > 3 * 1024 * 1024:
            reject("n6-preflight-captured-hard-cap")
        if charge.static_cost + source_bytes > 8 * 1024 * 1024:
            reject("n6-preflight-static-hard-cap")
        try:
            n1 = snapshot_n1(raw["n1_zero"])
            p2 = snapshot_pomega2(raw["pomega2"])
            source = (
                theorem_source(N6Lane.E_POWER_INJECTION)
                if raw["theorem"] is None
                else snapshot_theorem_source(
                    cast(N6TheoremSourceV1, raw["theorem"]),
                    N6Lane.E_POWER_INJECTION,
                )
            )
            selected_policy = (
                policy()
                if raw["policy"] is None
                else snapshot_policy(cast(N6PolicyV1, raw["policy"]))
            )
        except (PadicCompletionValidationError, PadicFamilyIntroductionValidationError):
            reject("n6-e-request-nested-validation-failed")
        if type(n1.integer.z) is not int or n1.integer.z != 0:
            reject("n6-e-request-n1-zero-required")
        if (
            n1.prime != p2.prime
            or n1.doctrine != p2.doctrine
            or n1.theorem_source.pomega2_artifact_path_id
            != p2.theorem_source.artifact_path_id
            or n1.theorem_source.pomega2_artifact_sha256
            != p2.theorem_source.artifact_sha256
        ):
            reject("n6-e-request-prime-doctrine-or-theorem-endpoint-mismatch")
        request_digest = digest("veyra.p3n6.e-request.v1", (
            ("n1-zero-package", n1.package_digest.encode()),
            ("pomega2-package", p2.package_digest.encode()),
            ("theorem-source", source.source_digest.encode()),
            ("policy", selected_policy.policy_digest.encode()),
        ))
        supplied = raw["supplied_request_digest"]
        if supplied is not None:
            exact_digest(supplied, "n6-e-request-supplied-digest")
            if supplied != request_digest:
                reject("n6-e-request-drift")
        after = _capture_all(root_fd)
        if before != after:
            reject("n6-source-reopen-continuity-drift")
        result = N6ERequestV1(n1, p2, source, selected_policy, request_digest)
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                logger.error("P3-N6 project root fd close failed")
    logger.debug("dispatch_e_request exit state=parsed-no-authority")
    return result
