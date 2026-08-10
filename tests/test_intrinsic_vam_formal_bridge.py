"""Focused trust, effect, continuity, and mutation tests for R12.5."""
from __future__ import annotations

from dataclasses import replace
import logging
from pathlib import Path
from types import MappingProxyType

import pytest

from src.core.intrinsic_vam_formal_bridge import (
    intrinsic_vam_formal_bridge_data,
    verify_intrinsic_vam_formal_bridge_report,
)
from src.core.intrinsic_vam_formal_bridge_core import (
    SOURCE_PATHS,
    _read_sources,
    _validate_sources,
    _verified_r11,
    check_intrinsic_vam_formal_bridge,
)
from src.core.intrinsic_vam_formal_effects import (
    EFFECT_BOUNDARY,
    intrinsic_vam_formal_effect_data,
    intrinsic_vam_formal_effect_digest,
)
from src.core.intrinsic_vam_formal_lean_render import (
    THEOREM_IDS,
    canonical_intrinsic_vam_formal_lean,
)
from src.core.intrinsic_vam_formal_manifest import (
    BRIDGE_ID,
    EXPECTED_R12_5_TCB_DIGESTS,
    EXPECTED_TOOLCHAIN_IDENTITY,
)
from src.core.intrinsic_vam_formal_objects import EXPECTED_R12_5_OBJECTS
from src.core.intrinsic_vam_formal_report import (
    valid_digest_manifest,
    valid_intrinsic_vam_formal_report_shape,
    valid_object_manifest,
    valid_source_origins,
)
from src.core.intrinsic_vam_formal_snapshot import (
    SNAPSHOT_NAMES,
    _SNAPSHOT_NAME_ROWS,
    valid_snapshot_names,
)
from src.core.observer_core_bridge import _blocked as blocked_r11
from src.core.shadow_effect_types import (
    BridgeCapability,
    EvidenceClass,
    EvidenceScope,
)
from src.core.shadow_effects import shadow_effect_registry_digest


LOGGER = logging.getLogger(__name__)
R11_BINDING = "d98318066dc015ca7d0d0be36d2b07b38d50c7715f4e2a494d70ff842262c53a"
SOURCE_NAMES = (*tuple(SOURCE_PATHS), "lean_export")
OBJECT_NAMES = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])


@pytest.fixture(scope="module")
def checked_report():
    LOGGER.info("R12.5 checked bridge fixture start")
    report = check_intrinsic_vam_formal_bridge()
    assert report.status == "checked", report.diagnostics
    LOGGER.info("R12.5 checked bridge fixture complete binding=%s", report.binding_digest)
    return report


def _canonical_sources() -> tuple[bytes, dict[str, bytes]]:
    """Build the exact generated export and one source-byte snapshot."""
    LOGGER.info("R12.5 canonical source snapshot start")
    generated = canonical_intrinsic_vam_formal_lean(
        R11_BINDING,
        shadow_effect_registry_digest(),
        intrinsic_vam_formal_effect_digest(),
    )
    sources = _read_sources(SOURCE_PATHS, generated)
    LOGGER.info("R12.5 canonical source snapshot complete count=%d", len(sources))
    return generated, sources


def test_toolchain_identity_is_content_bound_and_host_path_independent() -> None:
    """The reviewed identity binds content without local path or inode metadata."""
    LOGGER.info("R12.5 portable toolchain identity audit start")
    assert "toolchain=leanprover/lean4:v4.30.0-rc2" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "binary=lean" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "sha256=" in EXPECTED_TOOLCHAIN_IDENTITY
    assert "merkle=" in EXPECTED_TOOLCHAIN_IDENTITY
    fields = {
        name: value
        for field in EXPECTED_TOOLCHAIN_IDENTITY.split("|")[1:]
        if "=" in field
        for name, value in (field.split("=", 1),)
    }
    assert "path" not in fields and "inode" not in fields and "mtime" not in fields
    assert not Path(fields["binary"]).is_absolute()
    assert not Path(fields["toolchain"]).is_absolute()
    LOGGER.info("R12.5 portable toolchain identity audit complete")


def test_checked_report_binds_r11_sources_objects_effect_and_nonpromotion(
    checked_report,
) -> None:
    LOGGER.info("R12.5 checked report audit start")
    data = intrinsic_vam_formal_bridge_data(checked_report)
    assert checked_report.bridge_id == BRIDGE_ID
    assert checked_report.theorem_ids == THEOREM_IDS
    assert checked_report.r11_binding_digest == R11_BINDING
    assert checked_report.source_digests == tuple(EXPECTED_R12_5_TCB_DIGESTS.items())
    assert checked_report.object_records == tuple(EXPECTED_R12_5_OBJECTS.items())
    assert checked_report.capability is BridgeCapability.PRESERVES
    assert checked_report.evidence_class is EvidenceClass.FORMAL_BRIDGE
    assert checked_report.evidence_scope is EvidenceScope.GENERAL
    assert checked_report.r11_checked and checked_report.lean_checked
    assert verify_intrinsic_vam_formal_bridge_report(checked_report)
    assert data["promotion_ready"] is False
    assert data["taxonomy_changed"] is False
    assert "does not extract Python or Rust from Lean" in data["boundary"]
    LOGGER.info("R12.5 checked report audit complete")


def test_report_field_mutation_and_subclass_fail_closed(checked_report) -> None:
    LOGGER.info("R12.5 report mutation audit start")
    for field, value in (
        ("r11_binding_digest", "0" * 64),
        ("effect_digest", "0" * 64),
        ("binding_digest", "0" * 64),
        ("capability", BridgeCapability.REFLECTS),
        ("evidence_class", EvidenceClass.KERNEL_PROOF),
        ("evidence_scope", EvidenceScope.FINITE),
        ("promotion_ready", True),
        ("taxonomy_changed", True),
    ):
        forged = replace(checked_report, **{field: value})
        assert not verify_intrinsic_vam_formal_bridge_report(forged)

    class ReportSubclass(type(checked_report)):
        pass

    hostile = ReportSubclass(
        *(getattr(checked_report, field) for field in checked_report.__dataclass_fields__)
    )
    assert not valid_intrinsic_vam_formal_report_shape(hostile)
    LOGGER.info("R12.5 report mutation audit complete")


def test_effect_row_is_exact_formal_preservation_and_cannot_self_promote(
    monkeypatch: pytest.MonkeyPatch,
    checked_report,
) -> None:
    LOGGER.info("R12.5 effect boundary audit start")
    import src.core.intrinsic_vam_formal_effects as effects

    data = intrinsic_vam_formal_effect_data()
    assert data["capabilities"] == ["preserves"]
    assert data["evidence"] == {
        "class": "formal-bridge",
        "scope": "general",
        "id": BRIDGE_ID,
    }
    assert data["boundary"] == EFFECT_BOUNDARY
    assert data["promotion_ready"] is False and data["taxonomy_changed"] is False
    backing = dict(effects._EFFECT_ROW)
    backing["evidence_class"] = EvidenceClass.KERNEL_PROOF
    backing["promotion_ready"] = True
    monkeypatch.setattr(effects, "_EFFECT_ROW", MappingProxyType(backing))
    with pytest.raises(ValueError, match="r12.5-effect-row-invalid"):
        effects.intrinsic_vam_formal_effect_data()
    assert not verify_intrinsic_vam_formal_bridge_report(checked_report)
    LOGGER.info("R12.5 effect boundary audit complete")


def test_source_and_generated_export_mutation_have_exact_fail_closed_reasons() -> None:
    LOGGER.info("R12.5 source mutation audit start")
    generated, sources = _canonical_sources()
    changed_export = dict(sources)
    changed_export["lean_export"] = generated + b"\n"
    with pytest.raises(ValueError, match="r12.5-generated-lean-source-drift"):
        _validate_sources(changed_export, generated)
    changed_source = dict(sources)
    changed_source["formal_effects"] += b"\n# drift\n"
    with pytest.raises(ValueError, match="r12.5-reviewed-tcb-drift"):
        _validate_sources(changed_source, generated)
    LOGGER.info("R12.5 source mutation audit complete")


def test_manifest_types_order_and_source_origins_are_closed(tmp_path: Path) -> None:
    LOGGER.info("R12.5 manifest/origin audit start")
    assert all(
        type(item) is MappingProxyType
        for item in (EXPECTED_R12_5_TCB_DIGESTS, EXPECTED_R12_5_OBJECTS, SNAPSHOT_NAMES)
    )
    assert valid_digest_manifest(EXPECTED_R12_5_TCB_DIGESTS, SOURCE_NAMES)
    assert valid_object_manifest(EXPECTED_R12_5_OBJECTS, OBJECT_NAMES)
    assert valid_snapshot_names(SNAPSHOT_NAMES)
    assert valid_source_origins(dict(SOURCE_PATHS), SOURCE_PATHS)
    assert not valid_source_origins(MappingProxyType(dict(SOURCE_PATHS)), SOURCE_PATHS)
    transplanted = dict(SOURCE_PATHS)
    copied = tmp_path / SOURCE_PATHS["formal_effects"].name
    copied.write_bytes(SOURCE_PATHS["formal_effects"].read_bytes())
    transplanted["formal_effects"] = copied
    assert not valid_source_origins(transplanted, SOURCE_PATHS)
    with pytest.raises(ValueError, match="r12.5-source-path-set-invalid"):
        _read_sources(transplanted, b"")
    LOGGER.info("R12.5 manifest/origin audit complete")


def test_r11_continuity_rejects_any_nonchecked_prerequisite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    LOGGER.info("R12.5 R11 continuity rejection audit start")
    import src.core.intrinsic_vam_formal_bridge_core as core

    monkeypatch.setattr(core, "observer_core_bridge_report", lambda: blocked_r11("forced"))
    with pytest.raises(ValueError, match="r12.5-r11-continuity-rejected"):
        _verified_r11()
    LOGGER.info("R12.5 R11 continuity rejection audit complete")
