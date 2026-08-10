#!/usr/bin/env python3
"""Run repository line-limit and cache-ignore hygiene portably."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
from types import MappingProxyType

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
TARGET_LINE_LIMIT = 1000
HARD_LINE_LIMIT = 2000
# Every exception is path-bound, reviewable, and must explain why a cohesive
# split would reduce readability. Keep this empty unless such a case exists.
LINE_LIMIT_EXCEPTIONS: Mapping[str, tuple[int, str]] = MappingProxyType({})


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


def _valid_line_limit_identity(identity: object) -> bool:
    """Return whether an exception key is normalized repository-relative POSIX."""
    logger.debug("project_hygiene._valid_line_limit_identity entry type=%s", type(identity).__name__)
    if not isinstance(identity, str):
        logger.debug("project_hygiene._valid_line_limit_identity exit valid=false")
        return False
    normalized = PurePosixPath(identity)
    result = not (
        identity in {"", "."}
        or "\\" in identity
        or identity != normalized.as_posix()
        or normalized.is_absolute()
        or any(part in {"", ".", ".."} for part in normalized.parts)
    )
    logger.debug("project_hygiene._valid_line_limit_identity exit valid=%s", result)
    return result


def line_limit(relative: Path) -> int:
    """Return the target limit or one explicitly justified bounded exception."""
    identity = relative.as_posix()
    logger.debug("project_hygiene.line_limit entry path=%s", identity)
    if not _valid_line_limit_identity(identity):
        logger.error("project_hygiene invalid line identity path=%r", identity)
        raise RuntimeError(f"invalid-line-limit-identity:{identity}")
    exception = LINE_LIMIT_EXCEPTIONS.get(identity)
    if exception is None:
        logger.debug(
            "project_hygiene.line_limit exit path=%s limit=%d exception=false",
            identity,
            TARGET_LINE_LIMIT,
        )
        return TARGET_LINE_LIMIT
    if (
        not isinstance(exception, tuple)
        or len(exception) != 2
        or type(exception[0]) is not int
        or not isinstance(exception[1], str)
    ):
        logger.error("project_hygiene invalid line exception shape path=%s", identity)
        raise RuntimeError(f"invalid-line-limit-exception:{identity}")
    limit, justification = exception
    if not justification.strip() or not TARGET_LINE_LIMIT < limit <= HARD_LINE_LIMIT:
        logger.error(
            "project_hygiene invalid line exception path=%s limit=%d justification=%s",
            identity,
            limit,
            bool(justification.strip()),
        )
        raise RuntimeError(f"invalid-line-limit-exception:{identity}")
    logger.debug(
        "project_hygiene.line_limit exit path=%s limit=%d exception=true",
        identity,
        limit,
    )
    return limit


def line_limit_exception_errors(files: tuple[Path, ...]) -> tuple[str, ...]:
    """Reject stale or malformed exception keys before checking file sizes."""
    logger.debug(
        "project_hygiene.line_limit_exception_errors entry files=%d exceptions=%d",
        len(files),
        len(LINE_LIMIT_EXCEPTIONS),
    )
    maintained = {path.relative_to(ROOT).as_posix(): path for path in files}
    errors: list[str] = []
    for identity in LINE_LIMIT_EXCEPTIONS:
        if not _valid_line_limit_identity(identity):
            errors.append(f"invalid-line-limit-identity:{identity}")
            continue
        try:
            line_limit(Path(identity))
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        path = maintained.get(identity)
        if path is None:
            errors.append(f"stale-line-limit-exception:{identity}")
            continue
        if line_count(path)[1] <= TARGET_LINE_LIMIT:
            errors.append(f"unneeded-line-limit-exception:{identity}")
    result = tuple(errors)
    logger.debug(
        "project_hygiene.line_limit_exception_errors exit errors=%d",
        len(result),
    )
    return result


def line_violations(files: tuple[Path, ...], jobs: int) -> tuple[tuple[Path, int, int], ...]:
    """Check the target and explicitly justified hard-bounded exceptions."""
    logger.debug("project_hygiene.line_violations entry files=%d jobs=%d", len(files), jobs)
    violations: list[tuple[Path, int, int]] = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        rows = executor.map(line_count, files)
        for path, count in tqdm(rows, total=len(files), desc="Line hygiene", unit="file"):
            relative = path.relative_to(ROOT)
            limit = line_limit(relative)
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
    print("[1/4] Enumerating stable and experimental text files", flush=True)
    files = tracked_text_files()
    print("[2/4] Validating path-bound line-limit exceptions", flush=True)
    exception_errors = line_limit_exception_errors(files)
    print(f"[3/4] Checking {len(files)} line-count limits", flush=True)
    violations = line_violations(files, args.jobs)
    print("[4/4] Checking generated-cache ignore rules", flush=True)
    missing = cache_ignore_check()
    for error in exception_errors:
        print(f"[fail] {error}", file=sys.stderr)
    for path, count, limit in violations:
        print(f"[fail] {path.as_posix()}: {count} > {limit}", file=sys.stderr)
    for probe in missing:
        print(f"[fail] cache path is not ignored: {probe}", file=sys.stderr)
    elapsed = time.perf_counter() - started
    errors = len(exception_errors) + len(violations) + len(missing)
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
