#!/usr/bin/env python3
"""Optional VAM semantic parity harness for Python oracle vs native CLI.

This script is intentionally a parity/diagnostic harness, not a speed claim.
It compares semantic reports for golden fixtures encoded as VAM0 and/or VAMD.
"""
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vam.src import canonical_report, decode_dense, decode_vmbc, encode_dense, encode_vmbc, execute
from vam.src.fixtures import iter_valid_vam0_fixture_report_programs
from vam.src.model import Instruction

NATIVE = ROOT / "vam" / "native"
DEFAULT_NATIVE_BIN = NATIVE / "target" / "debug" / (
    "vam0-inspect.exe" if sys.platform == "win32" else "vam0-inspect"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Fixture:
    """One benchmark/parity fixture."""

    name: str
    program: tuple[Instruction, ...]


@dataclass(frozen=True)
class NativeRunner:
    """Resolved native CLI invocation mode."""

    prefix: tuple[str, ...]
    label: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare VAM Python oracle semantics with native CLI reports. No speedup claims.",
    )
    parser.add_argument(
        "--format",
        choices=("both", "vam0", "vamd"),
        default="both",
        help="Frame format(s) to compare. Default: both.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional fixture limit for smoke runs.")
    parser.add_argument("--fixture", action="append", help="Run only matching fixture name; repeatable.")
    parser.add_argument("--native-bin", help="Path to a prebuilt vam0-inspect binary.")
    parser.add_argument(
        "--cargo",
        action="store_true",
        help="Use cargo run instead of a prebuilt binary. This may update Cargo target artifacts.",
    )
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary encoded frame files.")
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args(argv)


def load_fixtures(limit: int, filters: Sequence[str] | None) -> list[Fixture]:
    fixtures = [Fixture(name, tuple(program)) for name, program in iter_valid_vam0_fixture_report_programs()]
    if filters:
        needles = tuple(filters)
        fixtures = [case for case in fixtures if any(needle in case.name for needle in needles)]
    if limit > 0:
        fixtures = fixtures[:limit]
    return fixtures


def selected_formats(kind: str) -> tuple[str, ...]:
    if kind == "both":
        return ("vam0", "vamd")
    return (kind,)


def resolve_runner(args: argparse.Namespace) -> NativeRunner:
    logger.debug("resolve_runner entry")
    if args.native_bin:
        path = Path(args.native_bin).expanduser()
        if not path.exists():
            logger.error("resolve_runner native binary missing")
            raise SystemExit("native binary not found")
        result = NativeRunner((str(path),), f"bin:{path.name}")
        logger.debug("resolve_runner exit mode=explicit")
        return result
    if args.cargo:
        cargo = shutil.which("cargo") or str(Path.home() / ".cargo" / "bin" / "cargo")
        if not cargo or not Path(cargo).exists():
            raise SystemExit("cargo not found; pass --native-bin or build vam/native first")
        return NativeRunner(
            (cargo, "run", "--quiet", "--manifest-path", str(NATIVE / "Cargo.toml"), "--"),
            "cargo-run",
        )
    if DEFAULT_NATIVE_BIN.exists():
        result = NativeRunner(
            (str(DEFAULT_NATIVE_BIN),),
            "bin:vam/native/target/debug/vam0-inspect",
        )
        logger.debug("resolve_runner exit mode=default")
        return result
    logger.debug("resolve_runner state=fallback-cargo")
    result = resolve_runner(argparse.Namespace(native_bin=None, cargo=True))
    logger.debug("resolve_runner exit mode=fallback-cargo")
    return result


def encode_frame(fmt: str, program: Iterable[Instruction]) -> bytes:
    program = tuple(program)
    if fmt == "vam0":
        return encode_vmbc(program)
    if fmt == "vamd":
        return encode_dense(program)
    raise ValueError(f"unsupported format: {fmt}")


def python_semantics(fmt: str, blob: bytes) -> dict[str, Any]:
    program = decode_vmbc(blob) if fmt == "vam0" else decode_dense(blob)
    report = canonical_report(program, execute(program))
    return {
        "ok": True,
        "profile": report["profile"],
        "instruction_count": len(program),
        "pc": report["final_pc"],
        "trace": report["trace"],
        "registers": report["registers"],
        "certs": report["certs"],
        "obstructions": report["obstructions"],
    }


def native_semantics(runner: NativeRunner, frame_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [*runner.prefix, str(frame_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"native emitted non-json stdout: {exc}", "stderr": result.stderr}
    if result.returncode != 0:
        return {"ok": False, "error": payload.get("error", payload), "stderr": result.stderr}
    return {
        "ok": payload.get("ok"),
        "profile": payload.get("profile"),
        "instruction_count": payload.get("instruction_count"),
        "pc": payload.get("pc"),
        "trace": payload.get("trace"),
        "registers": payload.get("registers"),
        "certs": payload.get("certs"),
        "obstructions": payload.get("obstructions"),
    }


def first_difference(left: dict[str, Any], right: dict[str, Any]) -> str:
    for key in ("ok", "profile", "instruction_count", "pc", "trace", "registers", "certs", "obstructions"):
        if left.get(key) != right.get(key):
            return f"{key}: python={compact(left.get(key))} native={compact(right.get(key))}"
    return "unknown difference"


def compact(value: Any, limit: int = 240) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return data if len(data) <= limit else data[: limit - 3] + "..."


def parity_cases(args: argparse.Namespace) -> int:
    fixtures = load_fixtures(args.limit, args.fixture)
    formats = selected_formats(args.format)
    if not fixtures:
        raise SystemExit("no fixtures selected")
    runner = resolve_runner(args)
    total = len(fixtures) * len(formats)
    start = time.perf_counter()
    mismatches = 0
    processed = 0
    temp_cm = tempfile.TemporaryDirectory(prefix="vam-semantic-parity-")
    with temp_cm as temp_name:
        temp_dir = Path(temp_name)
        if args.keep_temp:
            temp_dir = Path(tempfile.mkdtemp(prefix="vam-semantic-parity-keep-"))
        print_header(total, fixtures, formats, runner, temp_dir, args.quiet)
        for fixture in fixtures:
            for fmt in formats:
                processed += 1
                elapsed = time.perf_counter() - start
                remaining = total - processed
                label = f"{fixture.name}:{fmt}"
                if not args.quiet:
                    print(f"[{processed}/{total}] {label} remaining={remaining} elapsed={elapsed:.2f}s", flush=True)
                ok = compare_one(fixture, fmt, runner, temp_dir)
                if not ok:
                    mismatches += 1
        elapsed = time.perf_counter() - start
        print(
            "summary: "
            f"fixtures={len(fixtures)} formats={','.join(formats)} comparisons={total} "
            f"mismatches={mismatches} elapsed={elapsed:.2f}s claim=speed-neutral",
            flush=True,
        )
    return 0 if mismatches == 0 else 1


def print_header(
    total: int,
    fixtures: Sequence[Fixture],
    formats: Sequence[str],
    runner: NativeRunner,
    temp_dir: Path,
    quiet: bool,
) -> None:
    if quiet:
        return
    print("[1/3] preparing VAM semantic parity harness", flush=True)
    print(f"[2/3] selected fixtures={len(fixtures)} formats={','.join(formats)} total={total}", flush=True)
    print(f"[3/3] native runner={runner.label} temp=isolated", flush=True)
    print("note: elapsed time is operational only; this script makes no speedup claim", flush=True)


def compare_one(fixture: Fixture, fmt: str, runner: NativeRunner, temp_dir: Path) -> bool:
    blob = encode_frame(fmt, fixture.program)
    suffix = ".vam0" if fmt == "vam0" else ".vamd"
    frame_path = temp_dir / f"{fixture.name}{suffix}"
    frame_path.write_bytes(blob)
    left = python_semantics(fmt, blob)
    right = native_semantics(runner, frame_path)
    if left == right:
        return True
    print(f"MISMATCH {fixture.name}:{fmt} {first_difference(left, right)}", flush=True)
    return False


def main(argv: Sequence[str] | None = None) -> int:
    return parity_cases(parse_args(tuple(argv if argv is not None else sys.argv[1:])))


if __name__ == "__main__":
    raise SystemExit(main())
