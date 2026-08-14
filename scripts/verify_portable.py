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


PORTABLE_TESTS = (
    "tests/test_balance_ratio.py",
    "tests/test_modes.py",
    "tests/test_core_language.py",
    "tests/test_core_native_semantics.py",
    "tests/test_observer_realization.py",
    "tests/test_claim_composition.py",
    "tests/test_claim_composition_adversarial.py",
    "tests/test_claim_composition_export.py",
    "tests/test_claim_composition_p2.py",
    "tests/test_claim_composition_properties.py",
    "tests/test_claim_composition_replay.py",
    "tests/test_observer_provenance.py",
    "tests/test_observer_synthesis_python_rust_vector.py",
    "tests/test_finite_builder_package_compat.py",
    "tests/test_finite_builder_types_package_compat.py",
    "tests/test_platform_imports.py",
    "tests/test_project_paths.py",
    "tests/test_package_metadata.py",
    "tests/test_check_lean_sources.py",
    "tests/test_check_research_lean.py",
    "tests/test_vam_reference.py",
    "tests/test_vam_highlevel.py",
    "tests/test_vam_highlevel_v1.py",
    "tests/test_veyra_sage.py::test_veyra_modes_parent_constructs_elements",
    "tests/test_veyra_sage.py::test_veyra_mode_resonance_methods",
    "tests/test_veyra_sage.py::test_veyra_balance_parent_signed_arithmetic",
    "tests/test_veyra_sage.py::test_veyra_ratio_parent_arithmetic_and_raw_forms",
    "tests/test_veyra_sage.py::test_veyra_polynomial_parent_algebra_and_derivative",
    "tests/test_veyra_sage.py::test_veyra_sage_examples_doctest",
    "tests/test_veyra_sage_api_index.py",
    "tests/test_veyra_sage_notebooks.py",
    "tests/test_veyra_sage_notebook_artifacts.py",
)


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
                "not requires_posix_file_locks and not requires_symlinks and not requires_linux_hardening and not requires_lean_candidate and not requires_pinned_lean and not requires_real_sage and not requires_native_rust",
                *PORTABLE_TESTS,
            ),
            900,
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
