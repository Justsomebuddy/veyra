#!/usr/bin/env python3
"""Compile every tracked Lean source with one pinned portable toolchain."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from tqdm import tqdm

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = ROOT / "proofs" / "lean"
TMP_ROOT = ROOT / "data" / "tmp"
DEFAULT_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
EXPECTED_VERSION = "4.30.0-rc2"
IMPORT_PATTERN = re.compile(r"^import\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CompileResult:
    """One bounded source-compilation result."""

    source: Path
    returncode: int
    output: str
    elapsed: float


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the portable whole-source gate arguments."""
    logger.debug("check_lean_sources.parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", default=DEFAULT_TOOLCHAIN)
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    result = parser.parse_args(argv)
    logger.debug("check_lean_sources.parse_args exit jobs=%d", result.jobs)
    return result


def lean_command(toolchain: str) -> list[str]:
    """Resolve elan and verify the exact requested Lean version."""
    logger.debug("check_lean_sources.lean_command entry toolchain=%s", toolchain)
    elan = shutil.which("elan")
    if elan is None:
        logger.error("check_lean_sources elan unavailable")
        raise RuntimeError("elan-not-found")
    command = [elan, "run", toolchain, "lean"]
    result = subprocess.run(
        [*command, "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    version_text = (result.stdout or result.stderr).strip()
    if result.returncode or f"version {EXPECTED_VERSION}" not in version_text:
        logger.error("check_lean_sources toolchain mismatch output=%r", version_text)
        raise RuntimeError("pinned-lean-toolchain-unavailable")
    logger.debug("check_lean_sources.lean_command exit")
    return command


def source_graph(root: Path = LEAN_ROOT) -> dict[Path, tuple[Path, ...]]:
    """Return all Lean sources and their repository-local import edges."""
    logger.debug("check_lean_sources.source_graph entry root=%s", root)
    sources = tuple(sorted(root.glob("*.lean"), key=lambda path: path.name))
    by_stem = {path.stem: path for path in sources}
    graph: dict[Path, tuple[Path, ...]] = {}
    for source in sources:
        text = source.read_text(encoding="utf-8")
        imports = tuple(
            by_stem[name] for row in IMPORT_PATTERN.findall(text) for name in row.split() if name in by_stem
        )
        graph[source] = imports
    if len(graph) != 42:
        logger.error("check_lean_sources inventory mismatch count=%d", len(graph))
        raise RuntimeError("lean-source-inventory-mismatch")
    logger.debug("check_lean_sources.source_graph exit sources=%d", len(graph))
    return graph


def topological_layers(graph: dict[Path, tuple[Path, ...]]) -> tuple[tuple[Path, ...], ...]:
    """Partition the local import DAG into deterministic parallel layers."""
    logger.debug("check_lean_sources.topological_layers entry sources=%d", len(graph))
    remaining = set(graph)
    completed: set[Path] = set()
    layers: list[tuple[Path, ...]] = []
    while remaining:
        layer = tuple(
            sorted(
                (source for source in remaining if set(graph[source]) <= completed),
                key=lambda path: path.name,
            )
        )
        if not layer:
            logger.error("check_lean_sources local import cycle")
            raise RuntimeError("lean-local-import-cycle")
        layers.append(layer)
        completed.update(layer)
        remaining.difference_update(layer)
    result = tuple(layers)
    logger.debug("check_lean_sources.topological_layers exit layers=%d", len(result))
    return result


def compile_source(
    command: list[str],
    source: Path,
    output_root: Path,
    env: dict[str, str],
) -> CompileResult:
    """Compile one source into the isolated shared object directory."""
    logger.debug("check_lean_sources.compile_source entry source=%s", source.name)
    started = time.perf_counter()
    output = output_root / f"{source.stem}.olean"
    process = subprocess.run(
        [*command, "-DwarningAsError=true", "-o", str(output), str(source)],
        cwd=LEAN_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    elapsed = time.perf_counter() - started
    result = CompileResult(
        source,
        process.returncode,
        (process.stdout + process.stderr)[-16_384:],
        elapsed,
    )
    if result.returncode:
        logger.error("check_lean_sources compile failed source=%s", source.name)
    logger.debug(
        "check_lean_sources.compile_source exit source=%s rc=%d elapsed=%.3f",
        source.name,
        result.returncode,
        elapsed,
    )
    return result


def run(argv: list[str]) -> int:
    """Run the pinned 42-source gate with dependency-aware parallelism."""
    logger.debug("check_lean_sources.run entry argc=%d", len(argv))
    args = parse_args(argv)
    if args.jobs < 1 or args.jobs > 32:
        logger.error("check_lean_sources invalid jobs=%d", args.jobs)
        raise SystemExit("--jobs must be between 1 and 32")
    print("[1/4] Resolving pinned Lean toolchain", flush=True)
    command = lean_command(args.toolchain)
    print("[2/4] Building local import graph", flush=True)
    layers = topological_layers(source_graph())
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    passed = failed = 0
    print(
        f"[3/4] Compiling 42 sources in {len(layers)} dependency layers with {args.jobs} workers",
        flush=True,
    )
    with tempfile.TemporaryDirectory(prefix="lean-all-", dir=TMP_ROOT) as directory:
        output_root = Path(directory)
        env = os.environ.copy()
        env["LEAN_PATH"] = os.pathsep.join((str(output_root), str(LEAN_ROOT)))
        with tqdm(total=42, desc="Lean sources", unit="source") as progress:
            for layer in layers:
                with ThreadPoolExecutor(max_workers=min(args.jobs, len(layer))) as executor:
                    futures = {
                        executor.submit(compile_source, command, source, output_root, env): source for source in layer
                    }
                    layer_failed = False
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                        except (OSError, subprocess.TimeoutExpired) as exc:
                            source = futures[future]
                            logger.error(
                                "check_lean_sources execution failed source=%s error=%s",
                                source.name,
                                exc,
                            )
                            print(f"\n[fail] {source.name}: {exc}", file=sys.stderr)
                            failed += 1
                            layer_failed = True
                        else:
                            if result.returncode:
                                failed += 1
                                layer_failed = True
                                print(
                                    f"\n[fail] {result.source.name}\n{result.output}",
                                    file=sys.stderr,
                                )
                            else:
                                passed += 1
                        progress.update(1)
                if layer_failed:
                    break
    elapsed = time.perf_counter() - started
    skipped = 42 - passed - failed
    print("[4/4] Whole-source Lean summary", flush=True)
    print(
        f"[done] passed={passed} failed={failed} skipped={skipped} "
        f"elapsed={elapsed:.2f}s speed={passed / elapsed if elapsed else 0:.2f} source/s",
        flush=True,
    )
    result = 0 if passed == 42 and failed == 0 else 1
    logger.debug(
        "check_lean_sources.run exit rc=%d passed=%d failed=%d skipped=%d",
        result,
        passed,
        failed,
        skipped,
    )
    return result


def main() -> None:
    """CLI entry point with deterministic logging and exit status."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.debug("check_lean_sources.main entry")
    try:
        result = run(sys.argv[1:])
    except (RuntimeError, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        logger.error("check_lean_sources blocked error=%s", exc)
        print(f"[blocked] {exc}", file=sys.stderr)
        result = 2
    logger.debug("check_lean_sources.main exit rc=%d", result)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
