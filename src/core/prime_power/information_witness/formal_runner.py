"""Bounded private compiler for the N6-W layer and its exact N6 ancestry."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import tempfile
import time

from ...padic.completion.formal import ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION
from .formal import (
    N6WCompileOutcomeV1,
    _axioms,
    _failure,
    _kind,
    _symbols,
    continuity_holds,
)
from .sources import snapshot_theorem_source
from .types import N6WTheoremSourceV1
from ...prime_power_unbounded_capture import project_tmp_path
from ...prime_power_unbounded_execution_continuity import (
    RuntimeFileSnapshotV1,
    continuity_set_holds,
    snapshot_runtime_file,
)
from ...prime_power_unbounded_formal import compile_e_sources, formal_run_digest
from ...prime_power_unbounded_sources import (
    snapshot_policy,
    theorem_source as n6_theorem_source,
)
from ...prime_power_unbounded_types import N6FormalFailureKind, N6Lane, N6PolicyV1
from ...construction.stream_completion.formal_attestation import ToolchainContract, attest_toolchain
from ...construction.stream_completion.formal_process import capture_phase

logger = logging.getLogger(__name__)


def _checked_captured(
    captured: tuple[bytes, bytes, bytes, bytes],
    source: N6WTheoremSourceV1,
) -> None:
    """Reject alternate containers or any byte identity before process launch."""
    logger.debug("_checked_captured entry")
    expected = (
        "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f",
        "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48",
        source.direct_import[1], source.artifact_sha256,
    )
    from ...prime_power_unbounded_common import sha

    if (
        type(captured) is not tuple
        or len(captured) != 4
        or any(type(item) is not bytes for item in captured)
        or tuple(sha(item) for item in captured) != expected
    ):
        logger.error("_checked_captured source bytes drift")
        from ...prime_power_unbounded_common import reject

        reject("n6w-formal-captured-byte-drift")
    _symbols(captured[-1])
    logger.debug("_checked_captured exit")


def _private_snapshots(
    directory: Path,
    names: tuple[str, ...],
    captured: tuple[bytes, bytes, bytes, bytes],
) -> tuple[RuntimeFileSnapshotV1, ...]:
    """Write read-only sources and capture each through shared no-follow continuity."""
    logger.debug("_private_snapshots entry files=%d", len(names))
    from ...prime_power_unbounded_common import sha

    if not isinstance(directory, Path):
        raise OSError("n6w-private-directory-type-invalid")
    snapshots: list[RuntimeFileSnapshotV1] = []
    for name, payload in zip(names, captured, strict=True):
        path = directory / name
        path.write_bytes(payload)
        path.chmod(0o400)
        snapshot = snapshot_runtime_file(path, sha(payload))
        if snapshot is None:
            raise OSError("n6w-private-source-continuity-capture-failed")
        snapshots.append(snapshot)
    result = tuple(snapshots)
    logger.debug("_private_snapshots exit files=%d", len(result))
    return result


def compile_sources(
    source: N6WTheoremSourceV1,
    base_policy: N6PolicyV1,
    captured: tuple[bytes, bytes, bytes, bytes],
) -> N6WCompileOutcomeV1:
    """Replay repaired N6-E first, then compile the exact four-source W chain."""
    logger.debug("compile_sources entry")
    checked_source = snapshot_theorem_source(source)
    checked_policy = snapshot_policy(base_policy)
    _checked_captured(captured, checked_source)
    logger.debug("compile_sources external-call=compile_e_sources state=begin")
    base = compile_e_sources(
        n6_theorem_source(N6Lane.E_POWER_INJECTION), checked_policy,
        (captured[0], captured[1], captured[2]),
    )
    logger.debug("compile_sources external-call=compile_e_sources state=end")
    base_run = formal_run_digest(base)
    output = bytearray(base.output)
    codes = list(base.return_codes)
    receipts = list(base.phase_receipts)

    def fail(kind: N6FormalFailureKind) -> N6WCompileOutcomeV1:
        logger.debug("compile_sources exit state=failure kind=%s", kind.value)
        return _failure(
            kind, bytes(output), codes, receipts, checked_source.tcb_digest, base_run,
        )

    if base.kind is not None:
        return fail(base.kind)
    elan = shutil.which("elan")
    if elan is None:
        logger.error("compile_sources elan unavailable")
        return fail(N6FormalFailureKind.COMPILE_ERROR)
    elan_snapshot = snapshot_runtime_file(Path(elan), ELAN_SHA256)
    if elan_snapshot is None:
        logger.error("compile_sources elan continuity capture failed")
        return fail(N6FormalFailureKind.CONTINUITY_DRIFT)
    deadline = time.monotonic() + checked_policy.timeout_seconds
    contract = ToolchainContract(
        checked_source.toolchain_id, ELAN_SHA256, LEAN_BINARY_SHA256,
        LEAN_VERSION.encode(), checked_source.tcb_digest,
    )
    logger.debug("compile_sources external-call=attest_toolchain state=begin")
    attested = attest_toolchain(
        elan, deadline, max(0, checked_policy.max_output_bytes - len(output)), contract,
    )
    logger.debug("compile_sources external-call=attest_toolchain state=end")
    output.extend(attested.output)
    codes.extend(attested.return_codes)
    receipts.extend(attested.phase_receipts)
    if attested.kind is not None:
        return fail(_kind(attested.kind))
    if attested.lean_path is None:
        logger.error("compile_sources attested lean path absent")
        return fail(N6FormalFailureKind.COMPILE_ERROR)
    lean_snapshot = snapshot_runtime_file(attested.lean_path, LEAN_BINARY_SHA256)
    launchers = (elan_snapshot, lean_snapshot) if lean_snapshot is not None else ()
    if not launchers or not continuity_set_holds(launchers):
        logger.error("compile_sources launcher continuity failed")
        return fail(N6FormalFailureKind.CONTINUITY_DRIFT)
    names = (
        "VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
        "VeyraPrimePowerUnbounded.lean", "VeyraPrimePowerInformation.lean",
    )
    try:
        with tempfile.TemporaryDirectory(prefix="p3n6w-", dir=project_tmp_path()) as raw:
            private = Path(raw)
            sources = _private_snapshots(private, names, captured)
            watched = launchers + sources
            env = dict(os.environ, LEAN_PATH=str(private))
            for index, name in enumerate(names):
                if not continuity_set_holds(watched):
                    return fail(N6FormalFailureKind.CONTINUITY_DRIFT)
                command = [
                    elan, "run", checked_source.toolchain_id, "lean",
                    "-DwarningAsError=true",
                ]
                if index < len(names) - 1:
                    command += ["-o", name.replace(".lean", ".olean")]
                command.append(name)
                logger.debug("compile_sources external-call=capture_phase phase=%d", index)
                phase = capture_phase(
                    f"p3n6w-compile-{index}", command, private, deadline,
                    checked_policy.max_output_bytes - len(output), env,
                )
                output.extend(phase.output)
                codes.append(phase.return_code)
                receipts.append(phase.receipt)
                if not continuity_set_holds(watched):
                    return fail(N6FormalFailureKind.CONTINUITY_DRIFT)
                if phase.kind is not None:
                    return fail(_kind(phase.kind))
    except OSError as error:
        logger.error(
            "compile_sources private filesystem failure errno=%s type=%s",
            error.errno, type(error).__name__,
        )
        return fail(N6FormalFailureKind.COMPILE_ERROR)
    rows = _axioms(bytes(output))
    if rows is None:
        return fail(N6FormalFailureKind.COMPILE_ERROR)
    if not continuity_holds(checked_source, captured):
        return fail(N6FormalFailureKind.CONTINUITY_DRIFT)
    result = N6WCompileOutcomeV1(
        None, bytes(output), tuple(codes), rows, checked_source.tcb_digest,
        tuple(receipts), base_run,
    )
    logger.debug("compile_sources exit state=success rows=%d", len(rows))
    return result
