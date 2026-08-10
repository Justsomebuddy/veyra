#!/usr/bin/env python3
"""Battle-style local VAM timing harness.

This is a local timing diagnostic, not a speedup or superiority claim.  It keeps
Python as the semantic oracle and measures current execution/encoding/native CLI
surfaces on synthetic but semantics-valid VAM programs.
"""
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import logging
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vam.src import decode_dense, decode_vmbc, encode_dense, encode_vmbc, execute, optimize
from vam.src.model import Instruction

NATIVE = ROOT / "vam" / "native"
DEFAULT_NATIVE_BIN = NATIVE / "target" / "debug" / (
    "vam0-inspect.exe" if sys.platform == "win32" else "vam0-inspect"
)
BOUNDARY = "local-timing-diagnostic-not-speedup-claim"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BenchRow:
    workload: str
    blocks: int
    instructions: int
    metric: str
    repeats: int
    median_s: float
    min_s: float
    max_s: float
    units_per_s: float
    detail: str
    boundary: str = BOUNDARY


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local VAM battle timing diagnostics without speedup claims.")
    parser.add_argument("--blocks", default="16,128,512", help="Comma-separated block counts. Default: 16,128,512")
    parser.add_argument("--repeats", type=int, default=5, help="Repeats per metric. Default: 5")
    parser.add_argument("--native-bin", default=str(DEFAULT_NATIVE_BIN), help="Path to vam0-inspect binary")
    parser.add_argument("--json-out", help="Optional path for JSON result payload")
    parser.add_argument("--skip-native", action="store_true", help="Skip native CLI timing")
    return parser.parse_args(argv)


def workload_echo_cert(blocks: int) -> tuple[Instruction, ...]:
    rows: list[Instruction] = [Instruction("OBSERVER", ("%r1", "length"))]
    reg = 2
    for index in range(blocks):
        rez, left, right, tact, breath, mode, echo, cert = [f"%r{reg + off}" for off in range(8)]
        rows.extend(
            [
                Instruction("REZ", (rez, f"seed-{index}")),
                Instruction("NOD", (left, rez, f"left-{index}")),
                Instruction("NOD", (right, rez, f"right-{index}")),
                Instruction("TACT", (tact, left, right, f"tact-{index}")),
                Instruction("BREATH", (breath, tact)),
                Instruction("MODE", (mode, breath)),
                Instruction("ECHO", (echo, mode, mode, "%r1")),
                Instruction("CERT", (cert, f"claim-{index}", echo, "battle")),
            ]
        )
        reg += 8
    return tuple(rows)


def workload_optimizer_pressure(blocks: int) -> tuple[Instruction, ...]:
    rows: list[Instruction] = []
    reg = 1
    for index in range(blocks):
        rez, obs_a, obs_b, comp_a, comp_b, echo = [f"%r{reg + off}" for off in range(6)]
        rows.extend(
            [
                Instruction("REZ", (rez, f"phase-{index}")),
                Instruction("OBSERVER", (obs_a, "kind")),
                Instruction("OBSERVER", (obs_b, "kind")),
                Instruction("COMPRESS", (comp_a, rez, obs_a)),
                Instruction("COMPRESS", (comp_b, rez, obs_b)),
                Instruction("ECHO", (echo, comp_a, comp_b, obs_a)),
            ]
        )
        reg += 6
    return tuple(rows)


def workload_obstruction_boundary(blocks: int) -> tuple[Instruction, ...]:
    rows: list[Instruction] = []
    reg = 1
    for index in range(blocks):
        rez, obs, comp_a, comp_b, obs_row = [f"%r{reg + off}" for off in range(5)]
        rows.extend(
            [
                Instruction("REZ", (rez, f"phase-{index}")),
                Instruction("OBSERVER", (obs, "kind")),
                Instruction("COMPRESS", (comp_a, rez, obs)),
                Instruction("COMPRESS", (comp_b, comp_a, obs)),
                Instruction("OBSTRUCT", (obs_row, f"boundary-{index}", comp_b)),
            ]
        )
        reg += 5
    return tuple(rows)


def time_call(fn: Callable[[], object], repeats: int) -> tuple[list[float], object]:
    durations: list[float] = []
    result: object = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = fn()
        durations.append(time.perf_counter() - start)
    return durations, result


def row(workload: str, blocks: int, program: tuple[Instruction, ...], metric: str, repeats: int, durations: list[float], detail: str) -> BenchRow:
    median = statistics.median(durations)
    units = len(program) / median if median > 0 else 0.0
    return BenchRow(workload, blocks, len(program), metric, repeats, median, min(durations), max(durations), units, detail)


def native_runner(path: str) -> tuple[str, ...] | None:
    logger.debug("native_runner entry")
    candidate = Path(path).expanduser()
    if candidate.exists():
        result = (str(candidate),)
    else:
        cargo = shutil.which("cargo")
        result = (
            (cargo, "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--")
            if cargo
            else None
        )
    logger.debug("native_runner exit available=%s", result is not None)
    return result


def public_runner_label(prefix: tuple[str, ...]) -> str:
    """Return a stable runner label without publishing a host-local path."""
    logger.debug("public_runner_label entry fields=%d", len(prefix))
    if not prefix:
        raise ValueError("empty native runner")
    if len(prefix) > 1 and "run" in prefix:
        result = f"{Path(prefix[0]).name} run"
    elif Path(prefix[0]) == DEFAULT_NATIVE_BIN:
        result = "vam/native/target/debug/vam0-inspect"
    else:
        result = Path(prefix[0]).name
    logger.debug("public_runner_label exit label=%s", result)
    return result


def run_native(prefix: tuple[str, ...], frame: Path) -> dict[str, object]:
    proc = subprocess.run([*prefix, str(frame)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    payload = json.loads(proc.stdout)
    if not payload.get("ok"):
        raise RuntimeError(str(payload))
    return payload


def benchmark_program(name: str, blocks: int, program: tuple[Instruction, ...], repeats: int, native: tuple[str, ...] | None, temp_dir: Path) -> list[BenchRow]:
    logger.debug("benchmark_program entry workload=%s blocks=%d", name, blocks)
    result: list[BenchRow] = []
    durations, state = time_call(lambda: execute(program), repeats)
    result.append(row(name, blocks, program, "python_execute", repeats, durations, f"trace={len(state.trace)}"))
    durations, report = time_call(lambda: optimize(program), repeats)
    detail = f"accepted={len(report.accepted_rows)} rejected={len(report.rejected_rows)} opt_instr={len(report.optimized)}"
    result.append(row(name, blocks, program, "python_optimize", repeats, durations, detail))
    durations, vmbc = time_call(lambda: encode_vmbc(program), repeats)
    result.append(row(name, blocks, program, "vam0_encode", repeats, durations, f"bytes={len(vmbc)}"))
    durations, dense = time_call(lambda: encode_dense(program), repeats)
    result.append(row(name, blocks, program, "vamd_encode", repeats, durations, f"bytes={len(dense)}"))
    durations, decoded0 = time_call(lambda: decode_vmbc(vmbc), repeats)
    result.append(row(name, blocks, program, "vam0_decode", repeats, durations, f"decoded={len(decoded0)}"))
    durations, decoded_dense = time_call(lambda: decode_dense(dense), repeats)
    result.append(row(name, blocks, program, "vamd_decode", repeats, durations, f"decoded={len(decoded_dense)}"))
    if native:
        vam0_path, vamd_path = temp_dir / f"{name}-{blocks}.vam0", temp_dir / f"{name}-{blocks}.vamd"
        vam0_path.write_bytes(vmbc)
        vamd_path.write_bytes(dense)
        durations, _ = time_call(lambda: run_native(native, vam0_path), repeats)
        label = public_runner_label(native)
        result.append(row(name, blocks, program, "native_cli_vam0", repeats, durations, f"runner={label}"))
        durations, _ = time_call(lambda: run_native(native, vamd_path), repeats)
        result.append(row(name, blocks, program, "native_cli_vamd", repeats, durations, f"runner={label}"))
    logger.debug("benchmark_program exit rows=%d", len(result))
    return result


def print_progress(done: int, total: int, label: str, start: float) -> None:
    elapsed = time.perf_counter() - start
    rate = done / elapsed if elapsed > 0 else 0.0
    eta = (total - done) / rate if rate > 0 else 0.0
    print(f"[{done}/{total}] {label} elapsed={elapsed:.2f}s eta={eta:.2f}s", flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(argv if argv is not None else sys.argv[1:]))
    blocks = tuple(int(item) for item in args.blocks.split(",") if item.strip())
    workloads = (
        ("echo_cert", workload_echo_cert),
        ("optimizer_pressure", workload_optimizer_pressure),
        ("obstruction_boundary", workload_obstruction_boundary),
    )
    native = None if args.skip_native else native_runner(args.native_bin)
    total = len(blocks) * len(workloads)
    rows: list[BenchRow] = []
    start = time.perf_counter()
    temp_root = ROOT / "data" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    print(f"[1/3] VAM battle benchmark boundary={BOUNDARY}", flush=True)
    print(f"[2/3] workloads={len(workloads)} blocks={blocks} repeats={args.repeats} native={bool(native)}", flush=True)
    with tempfile.TemporaryDirectory(prefix="vam-battle-", dir=temp_root) as temp_name:
        temp_dir = Path(temp_name)
        for done, (name, factory, block_count) in enumerate(((n, f, b) for b in blocks for n, f in workloads), start=1):
            print_progress(done, total, f"{name}:{block_count}", start)
            rows.extend(benchmark_program(name, block_count, factory(block_count), args.repeats, native, temp_dir))
    payload = {"boundary": BOUNDARY, "rows": [asdict(item) for item in rows]}
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
            newline="\n",
        )
    print("[3/3] summary", flush=True)
    for item in rows:
        print(f"{item.workload:20s} blocks={item.blocks:4d} instr={item.instructions:5d} {item.metric:16s} median={item.median_s:.6f}s ips={item.units_per_s:,.0f} {item.detail}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
