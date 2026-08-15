"""Security and compatibility tests for the scripts-only Git runner."""

from __future__ import annotations

from collections.abc import Iterator
import logging
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

import scripts._trusted_git as trusted
import scripts.package_smoke as package_smoke
import scripts.project_hygiene as project_hygiene

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _test_log_boundary(request: pytest.FixtureRequest) -> Iterator[None]:
    """Give every security regression an entry/exit breadcrumb."""
    logger.debug("trusted Git regression entry test=%s", request.node.name)
    yield
    logger.debug("trusted Git regression exit test=%s", request.node.name)


def _stat(
    mode: int,
    *,
    uid: int = 0,
    attributes: int = 0,
    inode: int = 1,
) -> SimpleNamespace:
    """Build the lstat fields consumed by the admission policy."""
    logger.debug("trusted Git stat double entry")
    result = SimpleNamespace(
        st_dev=1,
        st_ino=inode,
        st_mode=mode,
        st_uid=uid,
        st_gid=0,
        st_size=100,
        st_mtime_ns=1,
        st_ctime_ns=1,
        st_file_attributes=attributes,
    )
    logger.debug("trusted Git stat double exit")
    return result


def _install_chain(
    monkeypatch: pytest.MonkeyPatch,
    executable: Path,
    executable_info: SimpleNamespace,
    ancestor_info: SimpleNamespace,
) -> None:
    """Install deterministic executable/ancestor lstat doubles."""
    logger.debug("trusted Git lstat double entry")
    parent = executable.parent
    monkeypatch.setattr(trusted, "_path_chain", lambda _path: (executable, parent))

    def fake_lstat(path: Path) -> SimpleNamespace:
        logger.debug("trusted Git fake lstat entry")
        result = executable_info if path == executable else ancestor_info
        logger.debug("trusted Git fake lstat exit")
        return result

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    logger.debug("trusted Git lstat double exit")


def test_fixed_candidate_lists_never_consult_path_or_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Platform selection is limited to the documented absolute identities."""
    monkeypatch.setattr(trusted, "_IS_WINDOWS", False)
    assert trusted._candidate_paths() == (
        Path("/usr/bin/git"),
        Path("/usr/local/bin/git"),
        Path("/opt/local/bin/git"),
    )
    monkeypatch.setattr(trusted, "_IS_WINDOWS", True)
    assert trusted._candidate_paths() == (
        Path(r"C:\Program Files\Git\bin\git.exe"),
        Path(r"C:\Program Files\Git\cmd\git.exe"),
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX installation-policy proof")
def test_live_inventory_matches_the_admitted_git_bytes() -> None:
    """The wrapper preserves the exact ls-files byte inventory on POSIX."""
    executable, _snapshot = trusted._resolve_executable()
    expected = subprocess.run(
        [
            str(executable),
            "--no-pager",
            "-C",
            str(ROOT),
            "-c",
            "core.fsmonitor=false",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        cwd=executable.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
        shell=False,
    )
    assert expected.returncode == 0
    assert trusted.git_inventory(ROOT) == tuple(item for item in expected.stdout.split(b"\0") if item)


def test_runner_uses_exact_process_boundary_and_scrubbed_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PATH, loader, and Git overrides never cross the child boundary."""
    executable = tmp_path / "trusted" / "git"
    executable.parent.mkdir()
    executable.write_bytes(b"git")
    identity = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 5, 0)
    monkeypatch.setattr(trusted, "_resolve_executable", lambda: (executable, (identity,)))
    monkeypatch.setattr(trusted, "_snapshot", lambda _path: (identity,))
    repository = tmp_path / "repo"
    repository.mkdir()
    monkeypatch.setenv("HOME", "/preserved-home")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/preserved-xdg")
    monkeypatch.setenv("PATH", "/malicious")
    monkeypatch.setenv("gIt_CONFIG_COUNT", "9")
    monkeypatch.setenv("LD_PRELOAD", "/malicious.so")
    monkeypatch.setenv("DyLd_InSeRt_LiBrArIeS", "/malicious.dylib")
    observed: dict[str, object] = {}

    def fake_run(command: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        logger.debug("trusted Git fake process entry")
        observed["command"] = command
        observed.update(kwargs)
        result = subprocess.CompletedProcess(command, 0, b"a\0b\0", b"")
        logger.debug("trusted Git fake process exit")
        return result

    monkeypatch.setattr(trusted.subprocess, "run", fake_run)
    assert trusted.git_inventory(repository) == (b"a", b"b")
    assert observed["command"] == (
        str(executable),
        "--no-pager",
        "-C",
        str(repository),
        "-c",
        "core.fsmonitor=false",
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )
    assert observed["cwd"] == executable.parent
    assert observed["stdin"] is subprocess.DEVNULL
    assert observed["stdout"] is subprocess.PIPE
    assert observed["stderr"] is subprocess.PIPE
    assert observed["check"] is False
    assert observed["shell"] is False
    assert observed["timeout"] == 30
    environment = observed["env"]
    assert isinstance(environment, dict)
    assert environment["HOME"] == "/preserved-home"
    assert environment["XDG_CONFIG_HOME"] == "/preserved-xdg"
    assert environment["GIT_OPTIONAL_LOCKS"] == "0"
    assert environment["GIT_TERMINAL_PROMPT"] == "0"
    normalized = {key.upper() for key in environment}
    assert "PATH" not in normalized
    assert "GIT_CONFIG_COUNT" not in normalized
    assert "LD_PRELOAD" not in normalized
    assert "DYLD_INSERT_LIBRARIES" not in normalized


@pytest.mark.parametrize(
    ("target", "mode", "uid"),
    (
        ("executable", stat.S_IFLNK | 0o777, 0),
        ("ancestor", stat.S_IFLNK | 0o777, 0),
        ("executable", stat.S_IFDIR | 0o755, 0),
        ("ancestor", stat.S_IFREG | 0o755, 0),
        ("executable", stat.S_IFREG | 0o644, 0),
        ("executable", stat.S_IFREG | 0o755, 1000),
        ("ancestor", stat.S_IFDIR | 0o755, 1000),
        ("executable", stat.S_IFREG | 0o775, 0),
        ("ancestor", stat.S_IFDIR | 0o757, 0),
    ),
)
def test_posix_admission_rejects_unsafe_file_and_ancestor_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    target: str,
    mode: int,
    uid: int,
) -> None:
    """Symlinks, bad types, bad ownership, writes, and no-exec all fail closed."""
    monkeypatch.setattr(trusted, "_IS_WINDOWS", False)
    executable = tmp_path / "bin" / "git"
    good_file = _stat(stat.S_IFREG | 0o755)
    good_parent = _stat(stat.S_IFDIR | 0o755)
    bad = _stat(mode, uid=uid)
    _install_chain(
        monkeypatch,
        executable,
        bad if target == "executable" else good_file,
        bad if target == "ancestor" else good_parent,
    )
    with pytest.raises(RuntimeError, match="^trusted-git-untrusted$"):
        trusted._snapshot(executable)


@pytest.mark.parametrize("target", ("executable", "ancestor"))
def test_windows_admission_rejects_every_reparse_point(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    target: str,
) -> None:
    """Windows fixed-path execution rejects reparse points at every level."""
    monkeypatch.setattr(trusted, "_IS_WINDOWS", True)
    executable = tmp_path / "Git" / "bin" / "git.exe"
    good_file = _stat(stat.S_IFREG | 0o755)
    good_parent = _stat(stat.S_IFDIR | 0o755)
    bad_file = _stat(stat.S_IFREG | 0o755, attributes=trusted._WINDOWS_REPARSE_POINT)
    bad_parent = _stat(stat.S_IFDIR | 0o755, attributes=trusted._WINDOWS_REPARSE_POINT)
    _install_chain(
        monkeypatch,
        executable,
        bad_file if target == "executable" else good_file,
        bad_parent if target == "ancestor" else good_parent,
    )
    with pytest.raises(RuntimeError, match="^trusted-git-untrusted$"):
        trusted._snapshot(executable)


def test_resolver_fails_closed_when_no_fixed_candidate_is_admitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An absent or invalid installation never falls back to PATH."""
    monkeypatch.setattr(trusted, "_candidate_paths", lambda: (Path("/fixed/a"), Path("/fixed/b")))
    monkeypatch.setattr(trusted, "_snapshot", lambda _path: (_ for _ in ()).throw(OSError()))
    with pytest.raises(RuntimeError, match="^trusted-git-unavailable$"):
        trusted.git_inventory(ROOT)


def test_missing_repository_has_fixed_value_free_failure(
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Repository normalization never leaks the rejected local identity."""
    hidden = tmp_path / "private-repository-name"
    with (
        caplog.at_level(logging.ERROR),
        pytest.raises(
            RuntimeError,
            match="^trusted-git-repository-unavailable$",
        ) as caught,
    ):
        trusted.git_inventory(hidden)
    assert caught.value.__cause__ is None
    assert str(hidden) not in str(caught.value)
    assert str(hidden) not in caplog.text
    assert "reason=repository-unavailable" in caplog.text


def test_runner_rejects_identity_drift_after_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A post-spawn executable or ancestor replacement invalidates output."""
    executable = tmp_path / "bin" / "git"
    executable.parent.mkdir()
    executable.write_bytes(b"git")
    repository = tmp_path / "repo"
    repository.mkdir()
    before = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 5, 0)
    after = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 9, 0)
    monkeypatch.setattr(trusted, "_resolve_executable", lambda: (executable, (before,)))
    snapshots = iter(((before,), (after,)))
    monkeypatch.setattr(trusted, "_snapshot", lambda _path: next(snapshots))
    monkeypatch.setattr(
        trusted.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, b"ignored\0", b""),
    )
    with pytest.raises(RuntimeError, match="^trusted-git-identity-drift$"):
        trusted.git_inventory(repository)


@pytest.mark.parametrize(
    "failure",
    (
        OSError("blocked"),
        subprocess.TimeoutExpired(cmd=("fixed",), timeout=30),
    ),
)
def test_post_attempt_identity_drift_precedes_execution_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: BaseException,
) -> None:
    """Every failed spawn rechecks identity and drift remains authoritative."""
    executable = tmp_path / "bin" / "git"
    executable.parent.mkdir()
    repository = tmp_path / "repo"
    repository.mkdir()
    before = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 5, 0)
    after = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 9, 0)
    monkeypatch.setattr(trusted, "_resolve_executable", lambda: (executable, (before,)))
    snapshots = iter(((before,), (after,)))
    monkeypatch.setattr(trusted, "_snapshot", lambda _path: next(snapshots))
    monkeypatch.setattr(trusted.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(failure))
    with pytest.raises(RuntimeError, match="^trusted-git-identity-drift$") as caught:
        trusted.git_inventory(repository)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    "failure",
    (
        OSError("blocked"),
        subprocess.TimeoutExpired(cmd=("fixed",), timeout=30),
    ),
)
def test_runner_normalizes_execution_failures_without_chaining(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: BaseException,
) -> None:
    """OS and timeout details cannot leak through the fixed error boundary."""
    executable = tmp_path / "bin" / "git"
    executable.parent.mkdir()
    repository = tmp_path / "repo"
    repository.mkdir()
    identity = trusted._PathIdentity(1, 2, stat.S_IFREG | 0o755, 0, 0, 3, 4, 5, 0)
    monkeypatch.setattr(trusted, "_resolve_executable", lambda: (executable, (identity,)))
    monkeypatch.setattr(trusted, "_snapshot", lambda _path: (identity,))
    monkeypatch.setattr(trusted.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(failure))
    with pytest.raises(RuntimeError, match="^trusted-git-execution-failed$") as caught:
        trusted.git_inventory(repository)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    ("returncode", "expected", "error"),
    (
        (0, True, None),
        (1, False, None),
        (2, None, "trusted-git-ignore-failed"),
    ),
)
def test_ignore_status_and_exact_argument_separator(
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    expected: bool | None,
    error: str | None,
) -> None:
    """Only rc 0/1 are decisions and option-like paths stay after ``--``."""
    observed: list[tuple[tuple[str, ...], int]] = []

    def fake_run(
        _root: Path,
        arguments: tuple[str, ...],
        timeout: int,
    ) -> subprocess.CompletedProcess[bytes]:
        logger.debug("trusted Git fake ignore process entry")
        observed.append((arguments, timeout))
        result = subprocess.CompletedProcess(arguments, returncode, b"", b"")
        logger.debug("trusted Git fake ignore process exit")
        return result

    monkeypatch.setattr(trusted, "_run", fake_run)
    if error is None:
        assert trusted.git_check_ignore(ROOT, "--hostile") is expected
    else:
        with pytest.raises(RuntimeError, match=f"^{error}$"):
            trusted.git_check_ignore(ROOT, "--hostile")
    assert observed == [(("check-ignore", "-q", "--", "--hostile"), 10)]


def test_inventory_status_and_nul_bytes_are_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inventory keeps undecoded bytes and rejects any nonzero Git status."""
    results = iter(
        (
            subprocess.CompletedProcess((), 0, b"alpha\0bad-\xff\0", b""),
            subprocess.CompletedProcess((), 3, b"ignored\0", b""),
        )
    )
    monkeypatch.setattr(trusted, "_run", lambda *_args, **_kwargs: next(results))
    assert trusted.git_inventory(ROOT) == (b"alpha", b"bad-\xff")
    with pytest.raises(RuntimeError, match="^trusted-git-inventory-failed$"):
        trusted.git_inventory(ROOT)


def test_consumers_delegate_to_the_private_inventory_and_ignore_seams(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Both production consumers preserve behavior without direct Git calls."""
    visible = tmp_path / "visible.py"
    visible.write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(package_smoke, "ROOT", tmp_path)
    monkeypatch.setattr(package_smoke, "git_inventory", lambda _root: (b"visible.py",))
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    copied = package_smoke.copy_source_checkout(scratch)
    assert (copied / "visible.py").read_bytes() == visible.read_bytes()

    monkeypatch.setattr(project_hygiene, "ROOT", tmp_path)
    monkeypatch.setattr(project_hygiene, "git_inventory", lambda _root: (b"visible.py",))
    assert project_hygiene.tracked_text_files() == (visible,)
    decisions = {".pytest_cache/": True, "src/core/__pycache__/": False, "vam/native/target/": True}
    monkeypatch.setattr(
        project_hygiene,
        "git_check_ignore",
        lambda _root, relative: decisions[relative],
    )
    assert project_hygiene.cache_ignore_check() == ("src/core/__pycache__/",)


def test_private_surface_and_package_metadata_are_pinned() -> None:
    """The helper ships in sdists, stays private, and enters portable Pytest."""
    assert trusted.__all__ == ("git_check_ignore", "git_inventory")
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "recursive-include scripts *.py" in manifest
    portable = (ROOT / "scripts/verify_portable.py").read_text(encoding="utf-8")
    assert '"tests/test_trusted_git.py"' in portable
    package_text = (ROOT / "scripts/package_smoke.py").read_text(encoding="utf-8")
    hygiene_text = (ROOT / "scripts/project_hygiene.py").read_text(encoding="utf-8")
    assert "from ._trusted_git import git_inventory" in package_text
    assert "from _trusted_git import git_inventory" in package_text
    assert "from ._trusted_git import git_check_ignore, git_inventory" in hygiene_text
    assert "from _trusted_git import git_check_ignore, git_inventory" in hygiene_text
