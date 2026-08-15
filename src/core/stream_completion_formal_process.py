"""Live bounded process-group capture for PΩ1 formal execution."""

from __future__ import annotations

from hashlib import sha256
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time

from .stream_completion_types import FormalExecutionFailureKind

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FormalPhaseReceipt:
    phase: str
    return_code: int
    output_bytes: int
    output_digest: str
    failure_kind: FormalExecutionFailureKind | None


@dataclass(frozen=True)
class CapturedPhase:
    kind: FormalExecutionFailureKind | None
    return_code: int
    output: bytes
    receipt: FormalPhaseReceipt


def file_sha(path: Path) -> str:
    """Hash a tool binary with bounded-memory streaming."""
    logger.debug("file_sha entry file=%s", path.name)
    value = sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                value.update(chunk)
    except OSError as exc:
        logger.error("file_sha failed error=%s", exc)
        return ""
    result = value.hexdigest()
    logger.debug("file_sha exit")
    return result


def kill_group(process: subprocess.Popen[bytes]) -> None:
    """Kill and reap an entire isolated compiler process group."""
    logger.debug("kill_group entry pid=%d", process.pid)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        logger.debug("kill_group already exited pid=%d", process.pid)
    process.wait()
    logger.debug("kill_group exit pid=%d", process.pid)


def capture_command(
    command: list[str], cwd: Path | None, deadline: float, cap: int,
    env: dict[str, str] | None = None,
) -> tuple[FormalExecutionFailureKind | None, int, bytes]:
    """Stream output live; kill the whole group immediately on cap or deadline."""
    logger.debug("capture_command entry stage=spawn argc=%d cap=%d", len(command), cap)
    if cap < 1:
        logger.error("capture_command exhausted output budget")
        return FormalExecutionFailureKind.OUTPUT_LIMIT, -1, b""
    try:
        process = subprocess.Popen(
            command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            env=env, start_new_session=True,
        )
    except OSError:
        logger.error(
            "capture_command start failed stage=spawn argc=%d cap=%d",
            len(command), cap,
        )
        return FormalExecutionFailureKind.COMPILE_ERROR, -1, b""
    if process.stdout is None:
        logger.error("capture_command blocked stage=stdout argc=%d cap=%d", len(command), cap)
        kill_group(process)
        return FormalExecutionFailureKind.COMPILE_ERROR, -1, b""
    os.set_blocking(process.stdout.fileno(), False)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    output = bytearray()
    while True:
        if time.monotonic() >= deadline:
            kill_group(process)
            logger.error(
                "capture_command timeout stage=running argc=%d cap=%d bytes=%d",
                len(command), cap, len(output),
            )
            return FormalExecutionFailureKind.TIMEOUT, -1, bytes(output)
        events = selector.select(min(0.05, max(0.0, deadline - time.monotonic())))
        for key, _ in events:
            try:
                chunk = os.read(key.fd, min(65536, cap - len(output) + 1))
            except BlockingIOError:
                chunk = b""
            if chunk:
                output.extend(chunk)
                if len(output) > cap:
                    kill_group(process)
                    logger.error(
                        "capture_command output limit stage=running argc=%d cap=%d bytes=%d",
                        len(command), cap, cap,
                    )
                    return FormalExecutionFailureKind.OUTPUT_LIMIT, -1, bytes(output[:cap])
            else:
                try:
                    selector.unregister(key.fileobj)
                except KeyError:
                    pass
        if process.poll() is not None and not selector.get_map():
            break
    code = process.wait()
    payload = bytes(output)
    if code != 0:
        logger.error(
            "capture_command nonzero exit stage=complete argc=%d cap=%d rc=%d bytes=%d",
            len(command), cap, code, len(payload),
        )
        return FormalExecutionFailureKind.COMPILE_ERROR, code, payload
    logger.debug(
        "capture_command exit stage=complete argc=%d cap=%d rc=%d bytes=%d",
        len(command), cap, code, len(payload),
    )
    return None, code, payload


def capture_phase(
    phase: str, command: list[str], cwd: Path | None, deadline: float, cap: int,
    env: dict[str, str] | None = None,
) -> CapturedPhase:
    """Capture one named phase and retain exact bounded provenance."""
    logger.debug("capture_phase entry phase=%s", phase)
    kind, code, output = capture_command(command, cwd, deadline, cap, env)
    receipt = FormalPhaseReceipt(phase, code, len(output), sha256(output).hexdigest(), kind)
    result = CapturedPhase(kind, code, output, receipt)
    logger.debug("capture_phase exit phase=%s kind=%s", phase, None if kind is None else kind.value)
    return result
