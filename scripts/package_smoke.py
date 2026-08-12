#!/usr/bin/env python3
"""Build wheel/sdist offline and validate the installed public payload."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "data" / "tmp"
REQUIRED_SDIST_PREFIXES = (
    ".github/workflows/",
    "docs/",
    "proofs/lean/",
    "requirements/",
    "scripts/",
    "src/core/",
    "tests/",
    "vam/native/",
    "veyra_sage/",
)


def expected_source_only_payload() -> frozenset[str]:
    """Return exact maintained Lean, native, and differential-vector payload."""
    logger.debug("package_smoke.expected_source_only_payload entry")
    lean = tuple(sorted((ROOT / "proofs" / "lean").glob("*.lean")))
    if len(lean) != 44:
        raise RuntimeError("lean-source-inventory-mismatch")
    native_root = ROOT / "vam" / "native"
    native = tuple(sorted((native_root / "src").rglob("*.rs"))) + tuple(
        native_root / name
        for name in ("Cargo.toml", "Cargo.lock", "rust-toolchain.toml", "README.md")
    )
    differential = ROOT / "tests/fixtures/observer_synthesis_python_rust_v1.json"
    files = (*lean, *native, differential)
    if any(not path.is_file() or path.is_symlink() for path in files):
        raise RuntimeError("source-only-payload-invalid")
    result = frozenset(path.relative_to(ROOT).as_posix() for path in files)
    logger.debug("package_smoke.expected_source_only_payload exit files=%d", len(result))
    return result


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one bounded packaging command with captured diagnostics."""
    logger.debug("package_smoke.run_command entry command=%r cwd=%s", command, cwd)
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=300,
    )
    if result.returncode:
        logger.error("package command failed rc=%d command=%r", result.returncode, command)
        print(result.stdout[-8_192:], file=sys.stderr)
        print(result.stderr[-8_192:], file=sys.stderr)
    logger.debug("package_smoke.run_command exit rc=%d", result.returncode)
    return result


def inspect_archives(dist: Path) -> tuple[Path, Path]:
    """Check wheel package data and source-distribution coverage."""
    logger.debug("package_smoke.inspect_archives entry dist=%s", dist)
    wheels = tuple(dist.glob("*.whl"))
    sdists = tuple(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("package-artifact-count-mismatch")
    wheel, sdist = wheels[0], sdists[0]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    required_wheel = (
        "src/core/",
        "veyra_sage/",
        "vam/src/",
        "vam/examples/minimal_echo.vmasm",
    )
    if any(not any(name.startswith(prefix) for name in names) for prefix in required_wheel):
        raise RuntimeError("wheel-required-payload-missing")
    if any(name.startswith(("vam/docs/", "vam/native/", "tests/")) for name in names):
        raise RuntimeError("wheel-source-only-payload-present")
    with tarfile.open(sdist, "r:gz") as archive:
        members = tuple(member.name.split("/", 1)[1] for member in archive if "/" in member.name)
    member_names = set(members)
    if any("vam/native/target/" in name or "__pycache__/" in name or ".pytest_cache/" in name for name in members):
        raise RuntimeError("sdist-generated-artifact-present")
    missing = tuple(
        prefix for prefix in REQUIRED_SDIST_PREFIXES if not any(name.startswith(prefix) for name in members)
    )
    if missing:
        raise RuntimeError(f"sdist-public-surface-missing:{','.join(missing)}")
    missing_sources = expected_source_only_payload() - member_names
    if missing_sources:
        raise RuntimeError("sdist-source-payload-missing:" + ",".join(sorted(missing_sources)))
    logger.debug("package_smoke.inspect_archives exit wheel=%s sdist=%s", wheel.name, sdist.name)
    return wheel, sdist


def installed_import_smoke(wheel: Path, scratch: Path, label: str) -> None:
    """Install without dependencies and import strictly from the wheel payload."""
    logger.debug("package_smoke.installed_import_smoke entry wheel=%s label=%s", wheel, label)
    target = scratch / f"installed-{label}"
    target.mkdir()
    install = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-index",
            "--target",
            str(target),
            str(wheel),
        ],
        cwd=scratch,
    )
    if install.returncode:
        raise RuntimeError("wheel-install-failed")
    script = "\n".join(
        (
            "import sys",
            f"sys.path.insert(0, {str(target)!r})",
            "from importlib.resources import files",
            "import src.core",
            "import src.core.claim_composition",
            "import src.core.observer_provenance",
            "import veyra_sage.all",
            "import vam.src",
            "from pathlib import Path",
            "root = Path(sys.path[0]).resolve()",
            "for module in (src.core, src.core.claim_composition, src.core.observer_provenance, veyra_sage.all, vam.src):",
            "    assert Path(module.__file__).resolve().is_relative_to(root)",
            "example = files('vam').joinpath('examples/minimal_echo.vmasm')",
            "assert example.is_file()",
            "assert 'CERT' in example.read_text(encoding='utf-8')",
            "print('wheel-import-ok')",
        )
    )
    smoke = run_command([sys.executable, "-I", "-S", "-c", script], cwd=scratch)
    if smoke.returncode or "wheel-import-ok" not in smoke.stdout:
        raise RuntimeError("wheel-installed-import-failed")
    logger.debug("package_smoke.installed_import_smoke exit label=%s", label)


def extract_sdist(sdist: Path, destination: Path) -> Path:
    """Extract one validated regular-file sdist and return its single root."""
    logger.debug("package_smoke.extract_sdist entry sdist=%s", sdist)
    destination.mkdir()
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            pure = Path(member.name)
            if pure.is_absolute() or ".." in pure.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError("sdist-unsafe-member")
        archive.extractall(destination, members=members)
    roots = tuple(path for path in destination.iterdir() if path.is_dir())
    if len(roots) != 1 or not (roots[0] / "pyproject.toml").is_file():
        raise RuntimeError("sdist-root-mismatch")
    logger.debug("package_smoke.extract_sdist exit root=%s members=%d", roots[0], len(members))
    return roots[0]


def build_wheel_from_sdist(sdist: Path, scratch: Path) -> Path:
    """Prove the source archive can independently produce an installable wheel."""
    logger.debug("package_smoke.build_wheel_from_sdist entry sdist=%s", sdist)
    source = extract_sdist(sdist, scratch / "sdist-source")
    output = scratch / "sdist-wheel"
    result = run_command(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--outdir",
            str(output),
        ],
        cwd=source,
    )
    wheels = tuple(output.glob("*.whl"))
    if result.returncode or len(wheels) != 1:
        raise RuntimeError("sdist-wheel-build-failed")
    logger.debug("package_smoke.build_wheel_from_sdist exit wheel=%s", wheels[0].name)
    return wheels[0]


def copy_source_checkout(destination: Path) -> Path:
    """Copy the active tree without writing build metadata beside proof inputs."""
    logger.debug("package_smoke.copy_source_checkout entry destination=%s", destination)
    source = destination / "source"
    process = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode:
        raise RuntimeError("package-source-inventory-failed")
    relative_paths = tuple(Path(os.fsdecode(raw)) for raw in process.stdout.split(b"\0") if raw)
    source.mkdir()
    for relative in relative_paths:
        origin = ROOT / relative
        if origin.is_symlink():
            raise RuntimeError(f"package-source-symlink:{relative.as_posix()}")
        if not origin.is_file():
            continue
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    logger.debug(
        "package_smoke.copy_source_checkout exit source=%s files=%d",
        source,
        len(relative_paths),
    )
    return source


def run() -> int:
    """Build and validate both Python distribution formats."""
    logger.debug("package_smoke.run entry")
    started = time.perf_counter()
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="package-smoke-", dir=TMP_ROOT) as directory:
        scratch = Path(directory)
        dist = scratch / "dist"
        print("[1/7] Copying the active source tree into an isolated build root", flush=True)
        source = copy_source_checkout(scratch)
        print("[2/7] Building wheel and sdist without build isolation", flush=True)
        build = run_command(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(dist)],
            cwd=source,
        )
        if build.returncode:
            raise RuntimeError("checkout-package-build-failed")
        print("[3/7] Inspecting package payloads", flush=True)
        wheel, sdist = inspect_archives(dist)
        print("[4/7] Installing checkout-built wheel into an isolated target", flush=True)
        installed_import_smoke(wheel, scratch, "checkout")
        print("[5/7] Rebuilding a wheel from the extracted source distribution", flush=True)
        sdist_wheel = build_wheel_from_sdist(sdist, scratch)
        print("[6/7] Installing the source-distribution wheel", flush=True)
        installed_import_smoke(sdist_wheel, scratch, "sdist")
        print("[7/7] Packaging summary", flush=True)
    elapsed = time.perf_counter() - started
    print(
        f"[done] artifacts=3 installs=2 imports=6 resources=2 errors=0 elapsed={elapsed:.2f}s",
        flush=True,
    )
    logger.debug("package_smoke.run exit rc=0")
    return 0


def main() -> None:
    """CLI entry point with a stable failure summary."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.debug("package_smoke.main entry")
    try:
        result = run()
    except (
        OSError,
        RuntimeError,
        subprocess.TimeoutExpired,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as exc:
        logger.exception("package smoke failed error=%s", exc)
        print(f"[done] artifacts=0 imports=0 errors=1 error={exc}", file=sys.stderr)
        result = 1
    logger.debug("package_smoke.main exit rc=%d", result)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
