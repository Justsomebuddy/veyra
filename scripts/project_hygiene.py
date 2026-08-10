#!/usr/bin/env python3
"""Run repository line-limit and cache-ignore hygiene portably."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

from tqdm import tqdm

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".cff",
    ".cu",
    ".cuh",
    ".ini",
    ".lean",
    ".lock",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {"LICENSE", "Makefile"}
SKIP_PARTS = {".git", ".venv", "node_modules", "__pycache__"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse hygiene controls."""
    logger.debug("project_hygiene.parse_args entry argc=%d", len(argv))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=min(32, os.cpu_count() or 1))
    result = parser.parse_args(argv)
    logger.debug("project_hygiene.parse_args exit jobs=%d", result.jobs)
    return result


def tracked_text_files() -> tuple[Path, ...]:
    """Enumerate checked text files without following external symlinks."""
    logger.debug("project_hygiene.tracked_text_files entry")
    process = subprocess.run(
        [
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode:
        raise RuntimeError("hygiene-source-inventory-failed")
    candidates = (ROOT / os.fsdecode(raw) for raw in process.stdout.split(b"\0") if raw)
    result = tuple(
        sorted(
            (
                path
                for path in candidates
                if path.is_file()
                and not path.is_symlink()
                and (path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES)
                and not SKIP_PARTS.intersection(path.relative_to(ROOT).parts)
            ),
            key=lambda path: path.relative_to(ROOT).as_posix(),
        )
    )
    logger.debug("project_hygiene.tracked_text_files exit count=%d", len(result))
    return result


def line_count(path: Path) -> tuple[Path, int]:
    """Count physical lines using an explicit portable encoding."""
    logger.debug("project_hygiene.line_count entry path=%s", path)
    count = len(path.read_text(encoding="utf-8").splitlines())
    logger.debug("project_hygiene.line_count exit path=%s lines=%d", path, count)
    return path, count


def line_violations(files: tuple[Path, ...], jobs: int) -> tuple[tuple[Path, int, int], ...]:
    """Check stable and experimental limits with bounded parallel I/O."""
    logger.debug("project_hygiene.line_violations entry files=%d jobs=%d", len(files), jobs)
    violations: list[tuple[Path, int, int]] = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = executor.map(line_count, files)
        for path, count in tqdm(rows, total=len(files), desc="Line hygiene", unit="file"):
            relative = path.relative_to(ROOT)
            limit = 1000 if relative.parts and relative.parts[0] == "experimental" else 300
            if count > limit:
                violations.append((relative, count, limit))
    result = tuple(violations)
    logger.debug("project_hygiene.line_violations exit violations=%d", len(result))
    return result


def cache_ignore_check() -> tuple[str, ...]:
    """Verify representative generated-cache paths remain ignored by Git."""
    logger.debug("project_hygiene.cache_ignore_check entry")
    probes = (".pytest_cache/", "src/core/__pycache__/", "vam/native/target/")
    missing: list[str] = []
    for probe in probes:
        result = subprocess.run(
            ["git", "check-ignore", "-q", probe],
            cwd=ROOT,
            check=False,
            timeout=10,
        )
        if result.returncode:
            missing.append(probe)
    outcome = tuple(missing)
    logger.debug("project_hygiene.cache_ignore_check exit missing=%d", len(outcome))
    return outcome


def run(argv: list[str]) -> int:
    """Run all portable hygiene stages and print one count summary."""
    logger.debug("project_hygiene.run entry argc=%d", len(argv))
    args = parse_args(argv)
    if not 1 <= args.jobs <= 32:
        raise SystemExit("--jobs must be between 1 and 32")
    started = time.perf_counter()
    print("[1/3] Enumerating stable and experimental text files", flush=True)
    files = tracked_text_files()
    print(f"[2/3] Checking {len(files)} line-count limits", flush=True)
    violations = line_violations(files, args.jobs)
    print("[3/3] Checking generated-cache ignore rules", flush=True)
    missing = cache_ignore_check()
    for path, count, limit in violations:
        print(f"[fail] {path.as_posix()}: {count} > {limit}", file=sys.stderr)
    for probe in missing:
        print(f"[fail] cache path is not ignored: {probe}", file=sys.stderr)
    elapsed = time.perf_counter() - started
    errors = len(violations) + len(missing)
    print(
        f"[done] processed={len(files)} errors={errors} elapsed={elapsed:.2f}s "
        f"speed={len(files) / elapsed if elapsed else 0:.2f} file/s",
        flush=True,
    )
    result = 1 if errors else 0
    logger.debug("project_hygiene.run exit rc=%d", result)
    return result


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.debug("project_hygiene.main entry")
    try:
        result = run(sys.argv[1:])
    except (OSError, RuntimeError, UnicodeError, subprocess.TimeoutExpired) as exc:
        logger.error("project hygiene blocked error=%s", exc)
        print(f"[done] processed=0 errors=1 error={exc}", file=sys.stderr)
        result = 2
    logger.debug("project_hygiene.main exit rc=%d", result)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
