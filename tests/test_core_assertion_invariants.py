"""Optimized-Python-stable invariants for the bounded core assertion wave."""

from __future__ import annotations

import ast
from dataclasses import replace
import logging
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest

import src.core.intrinsic_observer_echo_source as r13_module
import src.core.observer_provenance as provenance_module
import src.core.stream_completion_formal_process as process_module
from src.core.confluence import (
    diagram_edge,
    diagram_path,
    direct_echo_transport,
    finite_diagram_source,
    fork_confluence_judgment,
    fork_join_plan,
)
from src.core.confluence_runtime import _transport_cell
from src.core.confluence_preflight import ConfluenceValidationError
from src.core.confluence_types import AlignmentPoint, ConfluenceStatus
from src.core.intrinsic_observer_echo_source import (
    IntrinsicObserverEchoSourceArtifact,
    verify_intrinsic_observer_echo_source_artifact,
)
from src.core.observer_provenance import ProvenanceDiagnosticError
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence
from src.core.stream_completion_types import FormalExecutionFailureKind
from src.core.translated_confluence_cell import _side_ids
from src.core.translated_confluence_preflight import snapshot_translated_request
from src.core.translated_confluence_validation import TranslatedConfluenceValidationError
from translated_confluence_fixture import translated_fixture

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
TARGETS = "confluence_runtime intrinsic_observer_echo_source observer_provenance ".split()
TARGETS += "stream_completion_formal_process translated_confluence_cell".split()


def _direct_fixture() -> tuple[Any, Any, Any, Any]:
    logger.debug("_direct_fixture entry")
    doctrine = p0_observer_doctrine()
    stages = tuple(ontology_stage(name, Pulse(Silence()), doctrine, 1) for name in ("fork", "left", "right", "join"))
    edges = (
        diagram_edge("fl", "fork", "left", ("crest",)),
        diagram_edge("fr", "fork", "right", ("crest",)),
        diagram_edge("lj", "left", "join", ("crest",)),
        diagram_edge("rj", "right", "join", ("crest",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "fork", "left"),
        diagram_path("rb", ("fr",), "fork", "right"),
        diagram_path("ljp", ("lj",), "left", "join"),
        diagram_path("rjp", ("rj",), "right", "join"),
    )
    source = finite_diagram_source(doctrine, "invariant-diagram", stages, edges, paths)
    transport = direct_echo_transport(doctrine, ("crest",))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan = fork_join_plan(
        doctrine,
        source,
        "invariant-plan",
        "lb",
        "rb",
        "ljp",
        "rjp",
        alignment,
        transport,
    )
    logger.debug("_direct_fixture exit")
    return doctrine, source, transport, plan


def test_public_missing_join_is_total_open_while_private_cell_fails_stably() -> None:
    logger.debug("test public/private C1 invariant entry")
    doctrine, source, transport, plan = _direct_fixture()
    incomplete = fork_join_plan(
        doctrine,
        source,
        "incomplete-plan",
        "lb",
        "rb",
        None,
        None,
        (),
        transport,
    )
    result = fork_confluence_judgment(doctrine, source, incomplete, transport)
    assert result.status is ConfluenceStatus.OPEN
    assert result.transport_cell is None
    assert result.first_obstruction is not None
    assert result.first_obstruction.outcome == "missing-required-joins"

    for left_join, right_join in ((None, "rjp"), ("ljp", None)):
        with pytest.raises(ConfluenceValidationError, match="^partial-join-plan$"):
            fork_join_plan(
                doctrine,
                source,
                "partial-plan",
                "lb",
                "rb",
                left_join,
                right_join,
                (),
                transport,
            )
        forged = replace(
            plan,
            left_join_path_id=left_join,
            right_join_path_id=right_join,
        )
        with pytest.raises(RuntimeError, match="^transport-cell-requires-complete-separate-joins$"):
            _transport_cell(doctrine, source, forged, transport)
    logger.debug("test public/private C1 invariant exit")


def test_r13_type_gate_precedes_hostile_shape_helper_and_verifier_never_throws(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test R13 hostile helper entry")

    def hostile_shape(_artifact: object) -> tuple[str, ...]:
        raise RuntimeError("hostile-shape-callback")

    artifact = object.__new__(IntrinsicObserverEchoSourceArtifact)
    caplog.set_level(logging.DEBUG, logger=r13_module.__name__)
    monkeypatch.setattr(r13_module, "_shape_errors", hostile_shape)
    wrong = verify_intrinsic_observer_echo_source_artifact(object())
    assert wrong.errors == ("invalid-r13-source-artifact-type",)
    hostile = verify_intrinsic_observer_echo_source_artifact(artifact)
    assert hostile.errors == ("invalid-r13-source-artifact-shape",)
    monkeypatch.setattr(r13_module, "_shape_errors", lambda _artifact: ())

    def hostile_pin(_artifact: object) -> tuple[str, ...]:
        raise RuntimeError("hostile-pin-callback")

    monkeypatch.setattr(r13_module, "_pin_errors", hostile_pin)
    hostile = verify_intrinsic_observer_echo_source_artifact(artifact)
    assert hostile.errors == ("invalid-r13-source-artifact-shape",)
    assert "hostile-shape-callback" not in caplog.text
    assert "hostile-pin-callback" not in caplog.text
    logger.debug("test R13 hostile helper exit")


def test_provenance_exact_string_gate_precedes_digest_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.debug("test provenance string gate entry")

    def hostile_digest(_value: object) -> bool:
        raise RuntimeError("digest-helper-reached")

    monkeypatch.setattr(provenance_module, "_is_digest", hostile_digest)
    with pytest.raises(ProvenanceDiagnosticError, match="^node-digest$"):
        provenance_module._exact_digest(object(), "node-digest")
    logger.debug("test provenance string gate exit")


def test_missing_stdout_kills_group_and_reaps_once_without_command_disclosure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test missing stdout cleanup entry")

    class FakeProcess:
        stdout = None

        def __init__(self) -> None:
            self.waits = 0

        def wait(self) -> int:
            self.waits += 1
            return -9

    fake = FakeProcess()
    cleanup_calls: list[FakeProcess] = []
    selector_bomb = Mock(side_effect=AssertionError("selector-constructed"))

    def fake_cleanup(process: FakeProcess) -> None:
        cleanup_calls.append(process)
        process.wait()

    monkeypatch.setattr(process_module.subprocess, "Popen", lambda *args, **kwargs: fake)
    monkeypatch.setattr(process_module, "kill_group", fake_cleanup)
    monkeypatch.setattr(process_module.selectors, "DefaultSelector", selector_bomb)
    caplog.set_level(logging.DEBUG, logger=process_module.__name__)
    sensitive_value = "raw-command-private-value"
    kind, code, output = process_module.capture_command(
        ["compiler", sensitive_value], None, process_module.time.monotonic() + 10, 64
    )
    assert (kind, code, output) == (FormalExecutionFailureKind.COMPILE_ERROR, -1, b"")
    assert cleanup_calls == [fake]
    assert fake.waits == 1
    selector_bomb.assert_not_called()
    assert sensitive_value not in caplog.text
    logger.debug("test missing stdout cleanup exit")


def test_spawn_error_log_omits_command_and_exception_payload(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test spawn privacy entry")
    sensitive_value = "raw-command-private-value"

    def blocked_spawn(*_args: object, **_kwargs: object) -> None:
        raise OSError(sensitive_value)

    monkeypatch.setattr(process_module.subprocess, "Popen", blocked_spawn)
    caplog.set_level(logging.DEBUG, logger=process_module.__name__)
    result = process_module.capture_command(["compiler", sensitive_value], None, 1.0, 64)
    assert result == (FormalExecutionFailureKind.COMPILE_ERROR, -1, b"")
    assert sensitive_value not in caplog.text
    assert "stage=spawn argc=2 cap=64" in caplog.text
    logger.debug("test spawn privacy exit")


def test_translated_side_resolution_returns_narrowed_join_ids_and_stable_error() -> None:
    logger.debug("test translated join narrowing entry")
    fixture = translated_fixture()
    request = snapshot_translated_request(*fixture[:9])
    left, right, left_join_id, right_join_id = _side_ids(request)
    assert left and right
    assert (left_join_id, right_join_id) == (
        request.plan.left_join_path_id,
        request.plan.right_join_path_id,
    )

    for left_join, right_join in ((None, right_join_id), (left_join_id, None)):
        malformed = SimpleNamespace(
            plan=replace(
                request.plan,
                left_join_path_id=left_join,
                right_join_path_id=right_join,
            ),
            diagram=request.diagram,
        )
        with pytest.raises(
            TranslatedConfluenceValidationError,
            match="^translated-cell-requires-complete-separate-joins$",
        ):
            _side_ids(malformed)  # type: ignore[arg-type]
    logger.debug("test translated join narrowing exit")


def test_target_sources_contain_no_assert_nodes() -> None:
    logger.debug("test target AST assert inventory entry")
    for name in TARGETS:
        path = ROOT / "src/core" / f"{name}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), name
    logger.debug("test target AST assert inventory exit files=%d", len(TARGETS))


def test_representative_explicit_guards_survive_optimized_python() -> None:
    logger.debug("test optimized Python core invariants entry")
    probe = """
import src.core.intrinsic_observer_echo_source as r13
import src.core.observer_provenance as provenance
r13._shape_errors = lambda _artifact: ()
check = r13.verify_intrinsic_observer_echo_source_artifact(object())
failures = 0
if check.errors != (\"invalid-r13-source-artifact-type\",):
    failures += 1
provenance._is_digest = lambda _value: True
try:
    provenance._exact_digest(object(), \"optimized-digest\")
except provenance.ProvenanceDiagnosticError as exc:
    if str(exc) != \"optimized-digest\":
        failures += 1
else:
    failures += 1
if failures:
    raise SystemExit(10 + failures)
print(\"optimized-core-invariants-ok\")
"""
    completed = subprocess.run(
        [sys.executable, "-O", "-c", probe],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "optimized-core-invariants-ok\n"
    logger.debug("test optimized Python core invariants exit")
