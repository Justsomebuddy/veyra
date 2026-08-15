"""Fail-closed exact-result invariants for level-1 certificate producers."""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable

import pytest

import src.core.certify_observer_genesis as observer_certificate
import src.core.certify_productivity as productivity_certificate
from src.core.observer_genesis_types import GenesisJudgment, GenesisResourceLimit
from src.core.productivity_types import (
    ConstructionArtifact,
    ResourceLimitResult,
    RestrictionArtifact,
)

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
LEAK_SENTINEL = "certificate-invariant-leak-sentinel"
CALLBACKS: list[str] = []


class _TrapMeta(type):
    def __instancecheck__(cls, instance: object) -> bool:
        CALLBACKS.append("instancecheck")
        raise AssertionError(LEAK_SENTINEL)

    def __subclasscheck__(cls, subclass: type[object]) -> bool:
        CALLBACKS.append("subclasscheck")
        raise AssertionError(LEAK_SENTINEL)


class _HostileCallbacks:
    def __getattribute__(self, name: str) -> object:
        CALLBACKS.append("getattribute")
        raise AssertionError(LEAK_SENTINEL)

    def __repr__(self) -> str:
        CALLBACKS.append("repr")
        raise AssertionError(LEAK_SENTINEL)

    def __str__(self) -> str:
        CALLBACKS.append("str")
        raise AssertionError(LEAK_SENTINEL)


class _HostileGenesisJudgment(_HostileCallbacks, GenesisJudgment, metaclass=_TrapMeta):
    pass


class _HostileGenesisResourceLimit(_HostileCallbacks, GenesisResourceLimit, metaclass=_TrapMeta):
    pass


class _HostileConstructionArtifact(_HostileCallbacks, ConstructionArtifact, metaclass=_TrapMeta):
    pass


class _HostileRestrictionArtifact(_HostileCallbacks, RestrictionArtifact, metaclass=_TrapMeta):
    pass


class _HostileResourceLimitResult(_HostileCallbacks, ResourceLimitResult, metaclass=_TrapMeta):
    pass


HOSTILE_CLASSES: dict[type[Any], type[Any]] = {
    GenesisJudgment: _HostileGenesisJudgment,
    GenesisResourceLimit: _HostileGenesisResourceLimit,
    ConstructionArtifact: _HostileConstructionArtifact,
    RestrictionArtifact: _HostileRestrictionArtifact,
    ResourceLimitResult: _HostileResourceLimitResult,
}


def _hostile_uninitialized(base: type[Any]) -> object:
    """Build an uninitialized subclass whose observable hooks must stay untouched."""
    logger.debug("hostile certificate result construction entry")
    result = object.__new__(HOSTILE_CLASSES[base])
    logger.debug("hostile certificate result construction exit")
    return result


def _replace_nth_call(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    producer_name: str,
    ordinal: int,
    replacement: object,
) -> None:
    """Replace exactly one producer result while preserving preceding calls."""
    logger.debug("replace certificate producer call entry ordinal=%d", ordinal)
    original: Callable[..., object] = getattr(module, producer_name)
    calls = 0

    def wrapped(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        logger.debug("certificate producer wrapper call ordinal=%d", calls)
        if calls == ordinal:
            logger.debug("certificate producer wrapper injected result")
            return replacement
        return original(*args, **kwargs)

    monkeypatch.setattr(module, producer_name, wrapped)
    logger.debug("replace certificate producer call exit")


OBSERVER_CASES = (
    (1, GenesisJudgment, "observer-genesis certificate positive result type invariant failed"),
    (2, GenesisJudgment, "observer-genesis certificate withheld result type invariant failed"),
    (3, GenesisJudgment, "observer-genesis certificate reset result type invariant failed"),
    (4, GenesisResourceLimit, "observer-genesis certificate limited result type invariant failed"),
)


@pytest.mark.parametrize(
    ("ordinal", "base", "reason"),
    OBSERVER_CASES,
    ids=("positive", "withheld", "reset", "limited"),
)
def test_observer_certificate_rejects_each_hostile_result_before_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    ordinal: int,
    base: type[Any],
    reason: str,
) -> None:
    logger.debug("observer certificate result invariant test entry")
    CALLBACKS.clear()
    caplog.set_level(logging.ERROR, logger=observer_certificate.__name__)
    _replace_nth_call(
        monkeypatch,
        observer_certificate,
        "observer_genesis_judgment",
        ordinal,
        _hostile_uninitialized(base),
    )
    with pytest.raises(RuntimeError, match=f"^{reason}$") as caught:
        observer_certificate.certify_observer_genesis_p1e1()
    assert str(caught.value) == reason
    assert [record.getMessage() for record in caplog.records] == [reason]
    assert CALLBACKS == []
    assert LEAK_SENTINEL not in caplog.text
    logger.debug("observer certificate result invariant test exit")


PRODUCTIVITY_CASES = (
    ("construct_at_depth", 1, ConstructionArtifact, "first"),
    ("construct_at_depth", 2, ConstructionArtifact, "repeated"),
    ("construct_at_depth", 3, ConstructionArtifact, "cross-policy"),
    ("restriction_judgment", 1, RestrictionArtifact, "identity"),
    ("restriction_judgment", 2, RestrictionArtifact, "lower-mid"),
    ("restriction_judgment", 3, RestrictionArtifact, "mid-upper"),
    ("restriction_judgment", 4, RestrictionArtifact, "lower-upper"),
    ("construct_at_depth", 4, ResourceLimitResult, "refusal"),
)


@pytest.mark.parametrize(
    ("producer_name", "ordinal", "base", "label"),
    PRODUCTIVITY_CASES,
    ids=tuple(case[3] for case in PRODUCTIVITY_CASES),
)
def test_productivity_certificate_rejects_each_hostile_result_before_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    producer_name: str,
    ordinal: int,
    base: type[Any],
    label: str,
) -> None:
    logger.debug("productivity certificate result invariant test entry")
    CALLBACKS.clear()
    caplog.set_level(logging.ERROR, logger=productivity_certificate.__name__)
    _replace_nth_call(
        monkeypatch,
        productivity_certificate,
        producer_name,
        ordinal,
        _hostile_uninitialized(base),
    )
    reason = f"productivity certificate {label} result type invariant failed"
    with pytest.raises(RuntimeError, match=f"^{reason}$") as caught:
        productivity_certificate.certify_productivity_p1d1()
    assert str(caught.value) == reason
    assert [record.getMessage() for record in caplog.records] == [reason]
    assert CALLBACKS == []
    assert LEAK_SENTINEL not in caplog.text
    logger.debug("productivity certificate result invariant test exit")


@pytest.mark.parametrize(
    ("module_name", "producer_name", "certificate_name", "reason"),
    (
        (
            "src.core.certify_observer_genesis",
            "observer_genesis_judgment",
            "certify_observer_genesis_p1e1",
            "observer-genesis certificate positive result type invariant failed",
        ),
        (
            "src.core.certify_productivity",
            "construct_at_depth",
            "certify_productivity_p1d1",
            "productivity certificate first result type invariant failed",
        ),
    ),
    ids=("observer-genesis", "productivity"),
)
def test_certificate_result_guards_survive_optimized_python(
    module_name: str,
    producer_name: str,
    certificate_name: str,
    reason: str,
) -> None:
    logger.debug("optimized certificate result invariant test entry")
    program = f"""
import importlib
module = importlib.import_module({module_name!r})
setattr(module, {producer_name!r}, lambda *args, **kwargs: object())
try:
    getattr(module, {certificate_name!r})()
except RuntimeError as exc:
    if str(exc) != {reason!r}:
        raise RuntimeError("unstable optimized certificate error") from exc
else:
    raise RuntimeError("optimized certificate result guard was skipped")
print("optimized-certificate-guard-pass")
"""
    completed = subprocess.run(
        [sys.executable, "-O", "-c", program],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "optimized-certificate-guard-pass\n"
    assert LEAK_SENTINEL not in completed.stdout + completed.stderr
    logger.debug("optimized certificate result invariant test exit")
