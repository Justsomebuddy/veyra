"""Focused trust, mutation, continuity, and compilation tests for R13.2."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

import src.core.intrinsic_observer_echo_formal_bridge as bridge
import src.core.intrinsic_observer_echo_formal_bridge_core as core
from src.core.intrinsic_observer_echo_effects import (
    EXPECTED_REGISTRY_DIGEST,
    intrinsic_observer_echo_effect_digest,
)
from src.core.intrinsic_observer_echo_evidence import EXPECTED_EVIDENCE_DIGEST
from src.core.intrinsic_observer_echo_formal_bridge import (
    intrinsic_observer_echo_contract_bridge_report,
    intrinsic_observer_echo_formal_bridge_data,
    is_trusted_intrinsic_observer_echo_contract_report,
    verify_intrinsic_observer_echo_formal_bridge_report,
)
from src.core.intrinsic_observer_echo_formal_bridge_core import (
    SOURCE_PATHS,
    _read_sources,
    _validate_sources,
    _verified_r12,
    check_intrinsic_observer_echo_formal_bridge,
)
from src.core.intrinsic_observer_echo_formal_lean_render import (
    THEOREM_IDS,
    canonical_intrinsic_observer_echo_formal_lean,
)
from src.core.intrinsic_observer_echo_formal_manifest import (
    BRIDGE_ID,
    EXPECTED_BINDING_DIGEST,
    EXPECTED_PHASE_ARTIFACT,
    EXPECTED_R11_BINDING,
    EXPECTED_R12_BINDING,
    EXPECTED_R13_TCB_DIGESTS,
    EXPECTED_SNAPSHOT_DIGEST,
    EXPECTED_SOURCE_ELABORATION_BINDING,
)
from src.core.intrinsic_observer_echo_formal_objects import EXPECTED_R13_OBJECTS
from src.core.intrinsic_observer_echo_formal_report import (
    IntrinsicObserverEchoFormalBridgeReport,
    valid_digest_manifest,
    valid_intrinsic_observer_echo_formal_report_shape,
    valid_object_manifest,
    valid_source_origins,
)
from src.core.intrinsic_observer_echo_formal_snapshot import (
    SNAPSHOT_NAMES,
    _SNAPSHOT_NAME_ROWS,
    valid_snapshot_names,
)
from src.core.layer_theorem_contracts import theorem_contract_registry
from src.core.shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope

pytestmark = pytest.mark.requires_lean

SOURCE_NAMES = (*tuple(SOURCE_PATHS), "lean_export")
OBJECT_NAMES = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])


@pytest.fixture(scope="module")
def checked_report():
    """Build the full guarded report once for focused positive/mutation tests."""
    report = check_intrinsic_observer_echo_formal_bridge()
    assert report.status == "checked", report.diagnostics
    return report


def _canonical_sources() -> tuple[bytes, dict[str, bytes]]:
    """Build the exact generated stage and source-byte map without compiling."""
    generated = canonical_intrinsic_observer_echo_formal_lean(
        EXPECTED_PHASE_ARTIFACT,
        EXPECTED_SOURCE_ELABORATION_BINDING,
        EXPECTED_R11_BINDING,
        EXPECTED_R12_BINDING,
        EXPECTED_EVIDENCE_DIGEST,
        EXPECTED_REGISTRY_DIGEST,
        intrinsic_observer_echo_effect_digest(),
    )
    return generated, _read_sources(SOURCE_PATHS, generated)


def test_checked_report_binds_every_origin_and_is_not_promotion(
    checked_report,
) -> None:
    data = intrinsic_observer_echo_formal_bridge_data(checked_report)
    assert checked_report.bridge_id == BRIDGE_ID
    assert checked_report.theorem_ids == THEOREM_IDS
    assert checked_report.phase_artifact_digest == EXPECTED_PHASE_ARTIFACT
    assert checked_report.source_elaboration_binding_digest == EXPECTED_SOURCE_ELABORATION_BINDING
    assert checked_report.r11_binding_digest == EXPECTED_R11_BINDING
    assert checked_report.r12_binding_digest == EXPECTED_R12_BINDING
    assert checked_report.executable_evidence_digest == EXPECTED_EVIDENCE_DIGEST
    assert checked_report.source_digests == tuple(EXPECTED_R13_TCB_DIGESTS.items())
    assert checked_report.object_records == tuple(EXPECTED_R13_OBJECTS.items())
    assert checked_report.snapshot_digest == EXPECTED_SNAPSHOT_DIGEST
    assert checked_report.binding_digest == EXPECTED_BINDING_DIGEST
    assert checked_report.capability is BridgeCapability.PRESERVES
    assert checked_report.evidence_class is EvidenceClass.FORMAL_BRIDGE
    assert checked_report.evidence_scope is EvidenceScope.GENERAL
    assert verify_intrinsic_observer_echo_formal_bridge_report(checked_report)
    assert data["promotion_ready"] is False and data["taxonomy_changed"] is False
    assert data["checks"] == {
        "phase": True, "r12": True, "manifest": True, "sources": True,
        "objects": True, "snapshot": True, "lean": True,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("status", "blocked"),
        ("bridge_id", "transplanted"),
        ("phase_artifact_digest", "0" * 64),
        ("source_elaboration_binding_digest", "0" * 64),
        ("r11_binding_digest", "0" * 64),
        ("r12_binding_digest", "0" * 64),
        ("executable_evidence_digest", "0" * 64),
        ("effect_registry_digest", "0" * 64),
        ("effect_digest", "0" * 64),
        ("snapshot_digest", "0" * 64),
        ("binding_digest", "0" * 64),
        ("capability", BridgeCapability.REFLECTS),
        ("evidence_class", EvidenceClass.KERNEL_PROOF),
        ("evidence_scope", EvidenceScope.FINITE),
        ("phase_checked", False),
        ("r12_checked", False),
        ("manifest_checked", False),
        ("source_bound", False),
        ("object_bound", False),
        ("snapshot_checked", False),
        ("lean_checked", False),
        ("promotion_ready", True),
        ("taxonomy_changed", True),
        ("toolchain", "forged"),
        ("diagnostics", "forged"),
        ("boundary", "broader"),
        ("theorem_ids", tuple(reversed(THEOREM_IDS))),
    ),
)
def test_every_report_binding_and_flag_mutation_fails_closed(
    checked_report,
    field: str,
    value: object,
) -> None:
    assert not verify_intrinsic_observer_echo_formal_bridge_report(
        replace(checked_report, **{field: value}),
    )


def test_source_export_origin_and_manifest_transplants_fail_closed(tmp_path: Path) -> None:
    generated, sources = _canonical_sources()
    changed = dict(sources)
    changed["lean_export"] = generated + b"\n"
    with pytest.raises(ValueError, match="r13.2-generated-lean-source-drift"):
        _validate_sources(changed, generated)
    changed = dict(sources)
    changed["evidence"] += b"\n"
    with pytest.raises(ValueError, match="r13.2-reviewed-tcb-drift"):
        _validate_sources(changed, generated)
    assert valid_digest_manifest(EXPECTED_R13_TCB_DIGESTS, SOURCE_NAMES)
    assert valid_object_manifest(EXPECTED_R13_OBJECTS, OBJECT_NAMES)
    assert valid_snapshot_names(SNAPSHOT_NAMES)
    assert valid_source_origins(dict(SOURCE_PATHS), SOURCE_PATHS)
    copied = tmp_path / SOURCE_PATHS["evidence"].name
    copied.write_bytes(SOURCE_PATHS["evidence"].read_bytes())
    transplanted = dict(SOURCE_PATHS)
    transplanted["evidence"] = copied
    assert not valid_source_origins(transplanted, SOURCE_PATHS)
    with pytest.raises(ValueError, match="r13.2-source-path-set-invalid"):
        _read_sources(transplanted, generated)


def test_local_corrupt_roots_reject_before_parent_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden_parent() -> object:
        nonlocal calls
        calls += 1
        raise AssertionError("parent must not run")

    monkeypatch.setattr(core, "_verified_r12", forbidden_parent)
    monkeypatch.setattr(core, "EXPECTED_R13_TCB_DIGESTS", MappingProxyType({}))
    report = check_intrinsic_observer_echo_formal_bridge()
    assert report.status == "blocked"
    assert report.diagnostics == "r13.2-source-manifest-shape-mismatch"
    assert calls == 0


def test_hostile_r12_parent_is_rejected_before_attribute_dereference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Hostile:
        def __getattribute__(self, name: str) -> object:
            raise RuntimeError(name)

    monkeypatch.setattr(core, "intrinsic_vam_formal_bridge_report", Hostile)
    with pytest.raises(ValueError, match="r13.2-r12-continuity-rejected"):
        _verified_r12()


def test_report_subclass_and_tuple_transplants_fail_closed(checked_report) -> None:
    class ReportSubclass(type(checked_report)):
        pass

    hostile = ReportSubclass(
        *(getattr(checked_report, name) for name in checked_report.__dataclass_fields__),
    )
    assert not valid_intrinsic_observer_echo_formal_report_shape(hostile)
    assert not verify_intrinsic_observer_echo_formal_bridge_report(
        replace(checked_report, source_digests=tuple(reversed(checked_report.source_digests))),
    )
    assert not verify_intrinsic_observer_echo_formal_bridge_report(
        replace(checked_report, object_records=tuple(reversed(checked_report.object_records))),
    )


def test_uninitialized_exact_report_fails_closed_without_dereference() -> None:
    hostile = object.__new__(IntrinsicObserverEchoFormalBridgeReport)
    assert not valid_intrinsic_observer_echo_formal_report_shape(hostile)
    assert not verify_intrinsic_observer_echo_formal_bridge_report(hostile)
    with pytest.raises(ValueError, match="report-shape-invalid"):
        intrinsic_observer_echo_formal_bridge_data(hostile)


def test_contract_provider_checks_once_and_identity_blocks_copy(
    checked_report,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def once() -> IntrinsicObserverEchoFormalBridgeReport:
        nonlocal calls
        calls += 1
        return checked_report

    monkeypatch.setattr(bridge, "check_intrinsic_observer_echo_formal_bridge", once)
    monkeypatch.setattr(bridge, "_matches_reviewed_envelope", lambda _report: True)
    bridge._TRUSTED_CONTRACT_REPORT.set(None)
    report = intrinsic_observer_echo_contract_bridge_report()
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    artifact = contract.artifact_digest
    assert calls == 1
    assert not contract.bridge_verifier(contract, report, "0" * 64)
    assert not contract.bridge_verifier(contract, report, artifact)
    report = intrinsic_observer_echo_contract_bridge_report()
    assert contract.bridge_verifier(contract, report, artifact)
    assert not is_trusted_intrinsic_observer_echo_contract_report(report)
    report = intrinsic_observer_echo_contract_bridge_report()
    assert not is_trusted_intrinsic_observer_echo_contract_report(replace(report))
    assert not contract.bridge_verifier(contract, report, artifact)


def test_failed_contract_provider_clears_prior_token(
    checked_report,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reports = iter((checked_report, core._blocked("forced-failure")))
    monkeypatch.setattr(
        bridge,
        "check_intrinsic_observer_echo_formal_bridge",
        lambda: next(reports),
    )
    monkeypatch.setattr(bridge, "_matches_reviewed_envelope", lambda _report: True)
    contract = theorem_contract_registry()["intrinsic-observer-echo"]
    original = intrinsic_observer_echo_contract_bridge_report()
    assert intrinsic_observer_echo_contract_bridge_report().status == "blocked"
    assert not contract.bridge_verifier(contract, original, contract.artifact_digest)


def test_contract_report_slots_are_concurrent_and_one_shot(
    checked_report,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bridge,
        "check_intrinsic_observer_echo_formal_bridge",
        lambda: checked_report,
    )
    monkeypatch.setattr(bridge, "_matches_reviewed_envelope", lambda _report: True)
    contract = theorem_contract_registry()["intrinsic-observer-echo"]

    def resolve_once(_index: int) -> bool:
        report = intrinsic_observer_echo_contract_bridge_report()
        return contract.bridge_verifier(
            contract,
            report,
            contract.artifact_digest,
        )

    with ThreadPoolExecutor(max_workers=16) as workers:
        assert all(workers.map(resolve_once, range(32)))
