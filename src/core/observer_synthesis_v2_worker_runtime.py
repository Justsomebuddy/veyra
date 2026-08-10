"""Shared fixed-entry subprocess lifecycle for bounded R14 workers."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
from typing import IO, Callable

from src.platform_capabilities import CapabilityUnavailableError

from .observer_synthesis_v2_budget import BudgetLimits
from .platform_posix import apply_process_limits
from .observer_synthesis_v2_worker_transport import send_go_and_request_v2

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

READ_CHUNK_MAX = 64 * 1024
TERM_GRACE_SECONDS = 0.2
GROUP_REAP_GRACE_SECONDS = 1.0


class FixedWorkerKindV2(str, Enum):
    """Closed child entries; requests can never supply executable paths."""

    CEGIS = "observer_synthesis_v2_worker_entry.py"
    TRIAL_SUBJECT = "observer_synthesis_v2_trial_worker_entry.py"
    RECEIPT = "observer_synthesis_v2_receipt_worker_entry.py"


@dataclass(frozen=True, slots=True)
class FixedChildOutcomeV2:
    """Process/framing-independent terminal state returned to an adapter."""

    state: str
    framed_result: bytes


def close_fd_v2(fd: int | None) -> None:
    """Close an owned descriptor idempotently."""
    logger.debug("close_fd_v2 entry fd=%r", fd)
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            logger.debug("close_fd_v2 already closed fd=%d", fd)
    logger.debug("close_fd_v2 exit")


def close_stream_v2(stream: IO[bytes] | None) -> None:
    """Close an owned subprocess stream idempotently."""
    logger.debug("close_stream_v2 entry type=%s", type(stream).__name__)
    if stream is not None:
        try:
            stream.close()
        except OSError:
            logger.debug("close_stream_v2 already closed")
    logger.debug("close_stream_v2 exit")


def terminate_process_group_v2(proc: subprocess.Popen[bytes]) -> None:
    """TERM/KILL the owned group before reaping its reserved leader PID."""
    logger.debug("terminate_process_group_v2 entry pid=%d", proc.pid)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        delivered = True
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            delivered = False
            logger.debug("terminate_process_group_v2 group gone sig=%d", sig)
        if sig is signal.SIGTERM and delivered:
            time.sleep(TERM_GRACE_SECONDS)
    try:
        proc.wait(timeout=TERM_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        logger.error("terminate_process_group_v2 leader survived SIGKILL")
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait()
    reap_deadline = time.monotonic() + GROUP_REAP_GRACE_SECONDS
    while True:
        try:
            os.killpg(proc.pid, 0)
        except ProcessLookupError:
            break
        if time.monotonic() >= reap_deadline:
            logger.warning("terminate_process_group_v2 residual zombie group")
            break
        time.sleep(0.005)
    logger.debug("terminate_process_group_v2 exit returncode=%r", proc.returncode)


def apply_verified_limits_v2(pid: int, address_space: int) -> bool:
    """Apply and independently read back exact pre-GO AS/core limits."""
    logger.debug("apply_verified_limits_v2 entry pid=%d as=%d", pid, address_space)
    try:
        actual_as, actual_core = apply_process_limits(pid, address_space)
        result = actual_as == (address_space, address_space) and actual_core == (0, 0)
    except (CapabilityUnavailableError, OSError, ValueError):
        logger.error("apply_verified_limits_v2 failed", exc_info=True)
        result = False
    logger.debug("apply_verified_limits_v2 exit result=%s", result)
    return result


def drain_fixed_child_v2(
    proc: subprocess.Popen[bytes],
    result_fd: int,
    deadline_ns: int,
    output_limit: int,
    clock: Callable[[], int],
) -> FixedChildOutcomeV2:
    """Drain stdout, stderr, and result under one wall/output boundary."""
    logger.debug("drain_fixed_child_v2 entry pid=%d limit=%d", proc.pid, output_limit)
    selector = selectors.DefaultSelector()
    if proc.stdout is None or proc.stderr is None:
        logger.error("drain_fixed_child_v2 missing stdio pipes")
        return FixedChildOutcomeV2("child", b"")
    streams = {
        proc.stdout.fileno(): "stdout",
        proc.stderr.fileno(): "stderr",
        result_fd: "result",
    }
    buffers = {name: bytearray() for name in streams.values()}
    for fd, name in streams.items():
        os.set_blocking(fd, False)
        selector.register(fd, selectors.EVENT_READ, name)
    total = 0
    try:
        while selector.get_map():
            remaining_ns = deadline_ns - clock()
            if remaining_ns <= 0:
                logger.warning("drain_fixed_child_v2 cutoff=wall")
                return FixedChildOutcomeV2("wall", b"")
            events = selector.select(remaining_ns / 1_000_000_000)
            if not events:
                return FixedChildOutcomeV2("wall", b"")
            for key, _mask in events:
                allowance = output_limit - total
                chunk = os.read(key.fd, min(READ_CHUNK_MAX, allowance + 1))
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                total += len(chunk)
                if total > output_limit:
                    logger.warning("drain_fixed_child_v2 cutoff=output")
                    return FixedChildOutcomeV2("output", b"")
                buffers[key.data].extend(chunk)
        info = None
        while info is None:
            remaining_ns = deadline_ns - clock()
            if remaining_ns <= 0:
                return FixedChildOutcomeV2("wall", b"")
            info = os.waitid(
                os.P_PID,
                proc.pid,
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
            if info is None:
                time.sleep(min(0.005, remaining_ns / 1_000_000_000))
        if info.si_code != os.CLD_EXITED or info.si_status != 0:
            logger.warning(
                "drain_fixed_child_v2 child failure code=%r status=%r",
                info.si_code,
                info.si_status,
            )
            logger.debug(
                "drain_fixed_child_v2 child output stdout=%d stderr=%d",
                len(buffers["stdout"]),
                len(buffers["stderr"]),
            )
            return FixedChildOutcomeV2("child", b"")
        result = FixedChildOutcomeV2("ok", bytes(buffers["result"]))
    finally:
        selector.close()
    logger.debug("drain_fixed_child_v2 exit result_bytes=%d", len(result.framed_result))
    return result


def unframe_exact_result_v2(raw: bytes, frame_bytes: int, maximum: int) -> bytes:
    """Accept exactly one nonempty bounded frame."""
    logger.debug("unframe_exact_result_v2 entry bytes=%d", len(raw))
    if len(raw) < frame_bytes:
        raise EOFError("partial-worker-result")
    size = int.from_bytes(raw[:frame_bytes], "big")
    if size <= 0 or size > maximum:
        raise ValueError("invalid-worker-result-size")
    if len(raw) != frame_bytes + size:
        raise EOFError("partial-or-multiple-worker-result")
    result = raw[frame_bytes:]
    logger.debug("unframe_exact_result_v2 exit bytes=%d", len(result))
    return result


def run_fixed_child_v2(
    kind: FixedWorkerKindV2,
    request_frame: bytes,
    limits: BudgetLimits,
    *,
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    pipe: Callable[[], tuple[int, int]] = os.pipe,
    write: Callable[[int, bytes], int] = os.write,
    clock: Callable[[], int],
    apply_limits: Callable[[int, int], bool] = apply_verified_limits_v2,
) -> FixedChildOutcomeV2:
    """Run one closed child after exact limits and before a fresh deadline."""
    if type(kind) is not FixedWorkerKindV2:
        logger.error("run_fixed_child_v2 invalid fixed kind")
        raise ValueError("invalid-fixed-worker-kind")
    logger.debug("run_fixed_child_v2 entry kind=%s", kind.value)
    started_ns = clock()
    deadline_ns = started_ns + limits.wall_seconds * 1_000_000_000
    control_r = control_w = result_r = result_w = -1
    proc: subprocess.Popen[bytes] | None = None
    try:
        control_r, control_w = pipe()
        result_r, result_w = pipe()
        project_root = str(PROJECT_ROOT)
        entry_path = str(Path(__file__).resolve().with_name(kind.value))
        env = {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH": project_root,
        }
        proc = popen(
            [sys.executable, "-E", "-s", "-S", entry_path, str(control_r), str(result_w)],
            cwd=project_root,
            env=env,
            shell=False,
            close_fds=True,
            start_new_session=True,
            pass_fds=(control_r, result_w),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        close_fd_v2(control_r)
        control_r = -1
        close_fd_v2(result_w)
        result_w = -1
        if not apply_limits(proc.pid, limits.process_as_bytes_limit):
            terminate_process_group_v2(proc)
            return FixedChildOutcomeV2("limit-bootstrap", b"")
        if proc.stdin is None or proc.stdout is None or proc.stderr is None:
            terminate_process_group_v2(proc)
            return FixedChildOutcomeV2("pipe-bootstrap", b"")
        transport_state = send_go_and_request_v2(
            proc,
            control_w,
            request_frame,
            deadline_ns,
            clock,
            write,
        )
        close_fd_v2(control_w)
        control_w = -1
        if transport_state != "ok":
            terminate_process_group_v2(proc)
            return FixedChildOutcomeV2(transport_state, b"")
        outcome = drain_fixed_child_v2(
            proc,
            result_r,
            deadline_ns,
            limits.transcript_output_bytes_limit,
            clock,
        )
        terminate_process_group_v2(proc)
        logger.debug("run_fixed_child_v2 exit state=%s", outcome.state)
        return outcome
    except KeyboardInterrupt:
        if proc is not None:
            terminate_process_group_v2(proc)
        return FixedChildOutcomeV2("cancelled", b"")
    except (OSError, subprocess.SubprocessError):
        if proc is not None:
            terminate_process_group_v2(proc)
        return FixedChildOutcomeV2("runtime", b"")
    except (TypeError, UnicodeError, ValueError):
        if proc is not None:
            terminate_process_group_v2(proc)
        return FixedChildOutcomeV2("invalid", b"")
    finally:
        if proc is not None:
            close_stream_v2(proc.stdin)
            close_stream_v2(proc.stdout)
            close_stream_v2(proc.stderr)
        close_fd_v2(control_r if control_r >= 0 else None)
        close_fd_v2(control_w if control_w >= 0 else None)
        close_fd_v2(result_r if result_r >= 0 else None)
        close_fd_v2(result_w if result_w >= 0 else None)
