#!/usr/bin/env python3
"""Compile experimental research Lean sources against the pinned 48-file tree.

The 48-file proofs/lean inventory is immutable (checked separately by
scripts/check_lean_sources.py). Research proofs live in
experimental/research_lean/ and may import any base module. This harness
builds the base modules once into a persistent olean cache under the ignored
data/tmp/ tree, then compiles the research files in dependency order and
emits structured METRIC lines for the autoresearch loop.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
LEAN_ROOT = ROOT / "proofs" / "lean"
RESEARCH_ROOT = ROOT / "experimental" / "research_lean"
OLEAN_ROOT = ROOT / "data" / "tmp" / "research-olean"
TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
EXPECTED_VERSION = "4.30.0-rc2"
IMPORT_PATTERN = re.compile(r"^import\s+(.+?)\s*$", re.MULTILINE)
THEOREM_PATTERN = re.compile(r"^\s*(theorem|lemma)\s+(\w+)", re.MULTILINE)
FORBIDDEN_PATTERN = re.compile(r"\b(sorry|admit|axiom)\b")


def lean_command() -> list[str]:
    elan = shutil.which("elan")
    if elan is None:
        raise RuntimeError("elan-not-found")
    command = [elan, "run", TOOLCHAIN, "lean"]
    result = subprocess.run([*command, "--version"], capture_output=True, text=True, check=False, timeout=30)
    if result.returncode or f"version {EXPECTED_VERSION}" not in (result.stdout or result.stderr):
        raise RuntimeError("pinned-lean-toolchain-unavailable")
    return command


def sources(root: Path) -> list[Path]:
    return sorted(root.glob("*.lean"), key=lambda path: path.name)


def graph(files: list[Path], by_stem: dict[str, Path]) -> dict[Path, tuple[Path, ...]]:
    result: dict[Path, tuple[Path, ...]] = {}
    for source in files:
        text = source.read_text(encoding="utf-8")
        imports = tuple(
            by_stem[name] for row in IMPORT_PATTERN.findall(text) for name in row.split() if name in by_stem
        )
        result[source] = imports
    return result


def layers(graph: dict[Path, tuple[Path, ...]]) -> list[tuple[Path, ...]]:
    remaining = set(graph)
    completed: set[Path] = set()
    out: list[tuple[Path, ...]] = []
    while remaining:
        layer = tuple(sorted((s for s in remaining if set(graph[s]) <= completed), key=lambda p: p.name))
        if not layer:
            raise RuntimeError("lean-import-cycle")
        out.append(layer)
        completed.update(layer)
        remaining.difference_update(layer)
    return out


def compile_one(command: list[str], source: Path, env: dict[str, str]) -> tuple[Path, int, str, float]:
    output = OLEAN_ROOT / f"{source.stem}.olean"
    started = time.perf_counter()
    process = subprocess.run(
        [*command, "-DwarningAsError=true", "-o", str(output), str(source)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    return source, process.returncode, (process.stdout + process.stderr)[-16_384:], time.perf_counter() - started


def main() -> int:
    command = lean_command()
    base_files = sources(LEAN_ROOT)
    research_files = sources(RESEARCH_ROOT) if RESEARCH_ROOT.exists() else []
    OLEAN_ROOT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["LEAN_PATH"] = os.pathsep.join((str(OLEAN_ROOT), str(LEAN_ROOT), str(RESEARCH_ROOT)))

    started = time.perf_counter()
    # Base modules: build once; sources are immutable during the campaign.
    missing = [f for f in base_files if not (OLEAN_ROOT / f"{f.stem}.olean").exists()]
    by_stem = {p.stem: p for p in base_files + research_files}
    base_graph = graph(base_files, by_stem)
    failed = False
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as executor:
        pending = set(missing)
        done: set[Path] = set(f for f in base_files if f not in pending)
        futures = {}
        while pending or futures:
            ready = [f for f in pending if set(base_graph[f]) <= done]
            for f in ready:
                futures[executor.submit(compile_one, command, f, env)] = f
                pending.discard(f)
            for future in list(as_completed(futures)):
                source = futures.pop(future)
                _src, rc, text, _el = future.result()
                done.add(source)
                if rc:
                    failed = True
                    print(f"[fail] {source.name}\n{text}", file=sys.stderr)
            if ready:
                continue
    base_elapsed = time.perf_counter() - started
    if failed:
        print("[fail] base modules did not compile", file=sys.stderr)
        return 1
    if missing:
        print(f"[ok] built {len(missing)} base modules in {base_elapsed:.2f}s")

    # Research modules: full recompile every run (incremental by content).
    research_elapsed = 0.0
    checked = 0
    total = 0
    if research_files:
        started = time.perf_counter()
        # Research files may import base modules (prebuilt above); only
        # research-local imports participate in the research layer ordering.
        research_graph = {
            source: tuple(dep for dep in deps if dep in set(research_files))
            for source, deps in graph(research_files, by_stem).items()
        }
        for layer in layers(research_graph):
            with ThreadPoolExecutor(max_workers=min(4, len(layer))) as executor:
                futures = {executor.submit(compile_one, command, f, env): f for f in layer}
                for future in as_completed(futures):
                    source, rc, text, _el = future.result()
                    if rc:
                        failed = True
                        print(f"[fail] {source.name}\n{text}", file=sys.stderr)
                    else:
                        content = source.read_text(encoding="utf-8")
                        if FORBIDDEN_PATTERN.search(content):
                            failed = True
                            print(f"[fail] {source.name} contains sorry/admit/axiom", file=sys.stderr)
                        else:
                            theorems = THEOREM_PATTERN.findall(content)
                            checked += len(theorems)
                            total += len(theorems)
        research_elapsed = time.perf_counter() - started
    else:
        print("[info] no research sources yet (baseline)")

    print(f"METRIC new_checked_proofs={checked}")
    print(f"METRIC research_theorems_total={total}")
    print(f"METRIC base_build_s={base_elapsed:.2f}")
    print(f"METRIC research_compile_s={research_elapsed:.2f}")
    print(f"[done] checked={checked} failed={'yes' if failed else 'no'} "
          f"base={len(base_files)} research={len(research_files)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
