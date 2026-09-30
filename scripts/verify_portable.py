#!/usr/bin/env python3
"""Run the supported OS-neutral source-checkout verification lane."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Step:
    """One deterministic portable verification stage."""

    name: str
    command: tuple[str, ...]
    timeout_seconds: int


#: The hosted portable lane collects the whole public test tree. A module is kept
#: out only through a declared capability marker (attached centrally by
#: ``tests/conftest.py``), so a new test file cannot be left out by omission.
PORTABLE_TEST_ROOT = "tests"
#: Local-only archive of unpublished work; never part of the public suite.
LOCAL_ONLY_TEST_DIRS = ("tests/uncommitted",)
#: Every external capability marker declared in ``pyproject.toml``.
PORTABLE_MARKER_EXCLUSIONS = (
    "requires_posix_file_locks",
    "requires_symlinks",
    "requires_linux_hardening",
    "requires_lean_candidate",
    "requires_pinned_lean",
    "requires_real_sage",
    "requires_native_rust",
    "requires_posix_host",
)


def portable_marker_expression() -> str:
    """Return the pytest marker filter that deselects every external capability."""
    logger.debug("verify_portable.portable_marker_expression entry")
    result = " and ".join(f"not {marker}" for marker in PORTABLE_MARKER_EXCLUSIONS)
    logger.debug("verify_portable.portable_marker_expression exit markers=%d", len(PORTABLE_MARKER_EXCLUSIONS))
    return result


def steps() -> tuple[Step, ...]:
    """Build the cross-platform gate without shell-specific syntax."""
    logger.debug("verify_portable.steps entry")
    python = sys.executable
    result = (
        Step(
            "Ruff",
            (python, "-m", "ruff", "check", "src", "veyra_sage", "vam", "scripts", "tests"),
            300,
        ),
        Step(
            "Portable pytest",
            (
                python,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "-m",
                portable_marker_expression(),
                *(f"--ignore={directory}" for directory in LOCAL_ONLY_TEST_DIRS),
                PORTABLE_TEST_ROOT,
            ),
            2400,
        ),
        Step("Package build/install smoke", (python, "scripts/package_smoke.py"), 900),
        Step("Repository hygiene", (python, "scripts/project_hygiene.py"), 300),
    )
    logger.debug("verify_portable.steps exit count=%d", len(result))
    return result


def run() -> int:
    """Run every stage serially and report exact pass/fail/skip counts."""
    logger.debug("verify_portable.run entry")
    planned = steps()
    passed = failed = 0
    started = time.perf_counter()
    for index, step in enumerate(planned, 1):
        print(f"[{index}/{len(planned)}] {step.name}", flush=True)
        stage_started = time.perf_counter()
        logger.debug(
            "portable stage entry name=%s timeout_seconds=%d",
            step.name,
            step.timeout_seconds,
        )
        environment = os.environ.copy()
        if step.name == "Portable pytest":
            environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        try:
            process = subprocess.run(
                step.command,
                cwd=ROOT,
                env=environment,
                check=False,
                timeout=step.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            stage_elapsed = time.perf_counter() - stage_started
            failed += 1
            logger.error(
                "portable stage blocked name=%s timeout_seconds=%d error=%s",
                step.name,
                step.timeout_seconds,
                exc,
            )
            print(
                f"[fail] {step.name} error={exc} elapsed={stage_elapsed:.2f}s",
                flush=True,
            )
            break
        stage_elapsed = time.perf_counter() - stage_started
        if process.returncode:
            failed += 1
            logger.error("portable stage failed name=%s rc=%d", step.name, process.returncode)
            print(f"[fail] {step.name} rc={process.returncode} elapsed={stage_elapsed:.2f}s")
            break
        passed += 1
        logger.debug("portable stage exit name=%s rc=0", step.name)
        print(f"[pass] {step.name} elapsed={stage_elapsed:.2f}s", flush=True)
    skipped = len(planned) - passed - failed
    elapsed = time.perf_counter() - started
    print(
        f"[done] passed={passed} failed={failed} skipped={skipped} elapsed={elapsed:.2f}s",
        flush=True,
    )
    result = 1 if failed else 0
    logger.debug("verify_portable.run exit rc=%d", result)
    return result


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.debug("verify_portable.main entry")
    result = run()
    logger.debug("verify_portable.main exit rc=%d", result)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
