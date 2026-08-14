"""Internal fail-closed R11-continuous Lean bridge for the R12.5 lowering image."""
from __future__ import annotations

import logging
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from .intrinsic_vam_formal_bridge_io import (
    LEAN_TOOLCHAIN,
    binding_digest,
    lean_command,
    materialize_snapshot,
    sha_digest,
    toolchain_identity,
)
from .intrinsic_vam_formal_compile import compile_snapshot
from .intrinsic_vam_formal_effects import (
    EFFECT_BOUNDARY, EFFECT_SCHEMA, EVIDENCE_ID,
    intrinsic_vam_formal_effect_data, intrinsic_vam_formal_effect_digest,
)
from .intrinsic_vam_formal_lean_render import (
    THEOREM_IDS, THEOREM_ROWS, canonical_intrinsic_vam_formal_lean,
)
from .intrinsic_vam_formal_manifest import (
    BRIDGE_ID, EXPECTED_BINDING_DIGEST, EXPECTED_R11_BINDING,
    EXPECTED_R12_5_TCB_DIGESTS, EXPECTED_SNAPSHOT_DIGEST,
    EXPECTED_TOOLCHAIN_IDENTITY, MANIFEST_BOUNDARY,
)
from .intrinsic_vam_formal_objects import (
    _EXPECTED_R12_5_OBJECT_ROWS, EXPECTED_R12_5_OBJECTS,
)
from .intrinsic_vam_formal_report import (
    IntrinsicVamFormalBridgeReport,
    valid_digest_manifest,
    valid_object_manifest,
    valid_source_origins,
)
from .intrinsic_vam_formal_snapshot import (
    _SNAPSHOT_NAME_ROWS, require_valid_snapshot_layout,
)
from .observer_core_bridge import (
    observer_core_bridge_report, verify_observer_core_bridge_report,
)
from .observer_core_bridge_report import (
    read_exact_regular_source,
    valid_observer_core_bridge_report_shape,
)
from .shadow_effect_types import (
    BridgeCapability,
    CarrierId,
    EvidenceClass,
    EvidenceScope,
)
from .shadow_effects import shadow_effect_registry_digest
from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
SOURCE_PATHS = MappingProxyType(
    {
        "formal_effects": PROJECT_ROOT / "src/core/intrinsic_vam_formal_effects.py",
        "formal_report": PROJECT_ROOT / "src/core/intrinsic_vam_formal_report.py",
        "formal_snapshot": PROJECT_ROOT / "src/core/intrinsic_vam_formal_snapshot.py",
        "formal_bridge_io": PROJECT_ROOT / "src/core/intrinsic_vam_formal_bridge_io.py",
        "formal_compile": PROJECT_ROOT / "src/core/intrinsic_vam_formal_compile.py",
        "formal_lean_render": PROJECT_ROOT / "src/core/intrinsic_vam_formal_lean_render.py",
        "formal_bridge_core": PROJECT_ROOT / "src/core/intrinsic_vam_formal_bridge_core.py",
        "formal_bridge": PROJECT_ROOT / "src/core/intrinsic_vam_formal_bridge.py",
        "effect_types": PROJECT_ROOT / "src/core/shadow_effect_types.py",
        "effects": PROJECT_ROOT / "src/core/shadow_effects.py",
        "intrinsic_ir_types": PROJECT_ROOT / "vam/src/intrinsic_ir_types.py",
        "intrinsic_ir": PROJECT_ROOT / "vam/src/intrinsic_ir.py",
        "lowering_types": PROJECT_ROOT / "src/core/intrinsic_vam_lowering_types.py",
        "lowering_values": PROJECT_ROOT / "src/core/intrinsic_vam_values.py",
        "lowering_receipts": PROJECT_ROOT / "src/core/intrinsic_vam_receipts.py",
        "lowering": PROJECT_ROOT / "src/core/intrinsic_vam_lowering.py",
        "toolchain_runtime": PROJECT_ROOT / "src/core/proof_elaboration_toolchain.py",
        "runtime_guard": PROJECT_ROOT / "src/core/proof_elaboration_runtime_guard.py",
        "lean_arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
        "lean_semantics": LEAN_DIR / "VeyraNativeSemantics.lean",
        "lean_intrinsic_runtime": LEAN_DIR / "VeyraIntrinsicRuntime.lean",
        "lean_kernel": LEAN_DIR / "VeyraProofKernel.lean",
        "lean_soundness": LEAN_DIR / "VeyraProofSoundness.lean",
        "lean_transport": LEAN_DIR / "VeyraRecurrenceModeBridge.lean",
        "lean_observer_core": LEAN_DIR / "VeyraObserverCore.lean",
        "lean_observer_proof": LEAN_DIR / "VeyraObserverProof.lean",
        "lean_intrinsic_vam": LEAN_DIR / "VeyraIntrinsicVamBridge.lean",
    }
)
_CANONICAL_SOURCE_ROWS = tuple(SOURCE_PATHS.items())
_SOURCE_NAMES = (*tuple(SOURCE_PATHS), "lean_export")
_OBJECT_NAMES = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
_CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/{len(_SNAPSHOT_NAME_ROWS)}:{Path(filename).stem}:rc=0"
    for index, (_, filename) in enumerate(_SNAPSHOT_NAME_ROWS, 1)
)


def _local_trust_shape() -> None:
    """Validate local manifests/effects before invoking inherited R11 trust."""
    logger.debug("intrinsic_vam_formal_bridge._local_trust_shape entry")
    require_valid_snapshot_layout()
    try:
        live_source_rows = tuple(SOURCE_PATHS.items())
    except RuntimeError as exc:
        raise ValueError("r12.5-source-origin-manifest-invalid") from exc
    if live_source_rows != _CANONICAL_SOURCE_ROWS:
        raise ValueError("r12.5-source-origin-manifest-invalid")
    if not valid_digest_manifest(EXPECTED_R12_5_TCB_DIGESTS, _SOURCE_NAMES):
        raise ValueError("r12.5-source-manifest-shape-mismatch")
    if not valid_object_manifest(EXPECTED_R12_5_OBJECTS, _OBJECT_NAMES):
        raise ValueError("r12.5-object-manifest-shape-mismatch")
    effect = intrinsic_vam_formal_effect_data()
    expected_effect = {
        "schema": EFFECT_SCHEMA,
        "sources": [
            CarrierId.R7_RECURRENCE.value,
            CarrierId.R9_INTRINSIC_MODE.value,
            CarrierId.R11_RESPONSE.value,
        ],
        "target": CarrierId.VAM_INTRINSIC_IR.value,
        "capabilities": [BridgeCapability.PRESERVES.value],
        "evidence": {
            "class": EvidenceClass.FORMAL_BRIDGE.value,
            "scope": EvidenceScope.GENERAL.value,
            "id": EVIDENCE_ID,
        },
        "boundary": EFFECT_BOUNDARY,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
    if type(effect) is not dict or effect != expected_effect:
        raise ValueError("r12.5-effect-contract-mismatch")
    logger.debug("intrinsic_vam_formal_bridge._local_trust_shape exit")


def _verified_r11():
    logger.debug("intrinsic_vam_formal_bridge._verified_r11 entry")
    report = observer_core_bridge_report()
    if (
        not valid_observer_core_bridge_report_shape(report)
        or report.status != "checked"
        or not verify_observer_core_bridge_report(report)
    ):
        raise ValueError("r12.5-r11-continuity-rejected")
    logger.debug("intrinsic_vam_formal_bridge._verified_r11 exit binding=%s", report.binding_digest)
    return report


def _read_sources(paths: Mapping[str, Path], generated: bytes) -> dict[str, bytes]:
    logger.debug("intrinsic_vam_formal_bridge._read_sources entry")
    canonical = dict(_CANONICAL_SOURCE_ROWS)
    if paths is not SOURCE_PATHS and not valid_source_origins(paths, canonical):
        raise ValueError("r12.5-source-path-set-invalid")
    result = {name: read_exact_regular_source(path) for name, path in _CANONICAL_SOURCE_ROWS}
    if type(generated) is not bytes:
        raise TypeError("r12.5-generated-export-not-bytes")
    result["lean_export"] = generated
    logger.debug("intrinsic_vam_formal_bridge._read_sources exit count=%d", len(result))
    return result


def _blocked(reason: str) -> IntrinsicVamFormalBridgeReport:
    logger.error("intrinsic VAM formal bridge blocked reason=%s", reason)
    return IntrinsicVamFormalBridgeReport(
        "blocked", BRIDGE_ID, (), "", (), (), "", "", "",
        BridgeCapability.PRESERVES, EvidenceClass.FORMAL_BRIDGE,
        EvidenceScope.GENERAL, "", False, False, False, False, False,
        False, False, False, LEAN_TOOLCHAIN, reason, MANIFEST_BOUNDARY,
    )


def _validate_sources(
    sources: Mapping[str, bytes],
    generated: bytes,
) -> dict[str, str]:
    logger.debug("intrinsic_vam_formal_bridge._validate_sources entry")
    if sources["lean_export"] != generated:
        raise ValueError("r12.5-generated-lean-source-drift")
    lean_bytes = b"\n".join(sources[name] for name, _ in _SNAPSHOT_NAME_ROWS)
    forbidden = tuple(sorted(set(PLACEHOLDER.findall(lean_bytes.decode("utf-8")))))
    if forbidden:
        raise ValueError("r12.5-forbidden-lean-placeholder:" + ",".join(forbidden))
    for _, symbol in THEOREM_ROWS:
        encoded = symbol.encode()
        if encoded not in sources["lean_intrinsic_vam"] or encoded not in generated:
            raise ValueError("r12.5-lean-theorem-set-incomplete")
    digests = {name: sha_digest(source) for name, source in sources.items()}
    if (
        not valid_digest_manifest(EXPECTED_R12_5_TCB_DIGESTS, _SOURCE_NAMES)
        or tuple(digests.items()) != tuple(EXPECTED_R12_5_TCB_DIGESTS.items())
    ):
        raise ValueError("r12.5-reviewed-tcb-drift")
    logger.debug("intrinsic_vam_formal_bridge._validate_sources exit")
    return digests


def _report_body(
    r11,
    digests: Mapping[str, str],
    snapshot: str,
    registry: str,
    effect: str,
    toolchain: str,
) -> dict[str, object]:
    logger.debug("intrinsic_vam_formal_bridge._report_body entry")
    result = {
        "bridge_id": BRIDGE_ID,
        "theorem_ids": list(THEOREM_IDS),
        "r11_binding_digest": r11.binding_digest,
        "source_digests": [list(item) for item in digests.items()],
        "object_records": [
            [name, list(record)] for name, record in _EXPECTED_R12_5_OBJECT_ROWS
        ],
        "snapshot_digest": snapshot,
        "effect_registry_digest": registry,
        "effect_digest": effect,
        "capability": BridgeCapability.PRESERVES.value,
        "evidence_class": EvidenceClass.FORMAL_BRIDGE.value,
        "evidence_scope": EvidenceScope.GENERAL.value,
        "toolchain": toolchain,
        "promotion_ready": False,
        "taxonomy_changed": False,
    }
    logger.debug("intrinsic_vam_formal_bridge._report_body exit")
    return result


def _checked_report(r11, digests, snapshot, registry, effect, toolchain, diagnostics):
    logger.debug("intrinsic_vam_formal_bridge._checked_report entry")
    body = _report_body(r11, digests, snapshot, registry, effect, toolchain)
    result = IntrinsicVamFormalBridgeReport(
        "checked", BRIDGE_ID, THEOREM_IDS, r11.binding_digest,
        tuple(digests.items()), _EXPECTED_R12_5_OBJECT_ROWS, snapshot,
        registry, effect, BridgeCapability.PRESERVES,
        EvidenceClass.FORMAL_BRIDGE, EvidenceScope.GENERAL,
        binding_digest(body), True, True, True, True, True, True,
        False, False, toolchain, diagnostics, MANIFEST_BOUNDARY,
    )
    actual = (
        result.r11_binding_digest, result.snapshot_digest,
        result.binding_digest, result.toolchain,
    )
    expected = (
        EXPECTED_R11_BINDING, EXPECTED_SNAPSHOT_DIGEST,
        EXPECTED_BINDING_DIGEST, EXPECTED_TOOLCHAIN_IDENTITY,
    )
    if actual != expected:
        raise ValueError("r12.5-reviewed-envelope-drift")
    logger.debug("intrinsic_vam_formal_bridge._checked_report exit binding=%s", result.binding_digest)
    return result


def _origins(
    source_paths: Mapping[str, Path] | None,
    generated_export: bytes | None,
):
    logger.debug("intrinsic_vam_formal_bridge._origins entry")
    _local_trust_shape()
    r11 = _verified_r11()
    registry, effect = shadow_effect_registry_digest(), intrinsic_vam_formal_effect_digest()
    generated = canonical_intrinsic_vam_formal_lean(r11.binding_digest, registry, effect)
    if generated_export is not None:
        generated = generated_export
    paths = SOURCE_PATHS if source_paths is None else source_paths
    sources = _read_sources(paths, generated)
    expected = canonical_intrinsic_vam_formal_lean(r11.binding_digest, registry, effect)
    digests = _validate_sources(sources, expected)
    command = lean_command()
    if not command:
        raise ValueError("r12.5-pinned-lean-not-found")
    toolchain = toolchain_identity(command)
    snapshot = materialize_snapshot(
        sources, digests, r11.binding_digest, registry, effect, toolchain,
    )
    logger.debug("intrinsic_vam_formal_bridge._origins exit")
    return r11, registry, effect, sources, digests, command, toolchain, snapshot


def check_intrinsic_vam_formal_bridge(
    source_paths: Mapping[str, Path] | None = None,
    generated_export: bytes | None = None,
) -> IntrinsicVamFormalBridgeReport:
    """Check local trust first, then R11 continuity and fresh guarded Lean."""
    logger.debug("check_intrinsic_vam_formal_bridge entry")
    try:
        r11, registry, effect, sources, digests, command, toolchain, snapshot = _origins(
            source_paths, generated_export,
        )
        checked, diagnostics = compile_snapshot(command, snapshot, sources)
        if not checked:
            raise ValueError(diagnostics)
        result = _checked_report(
            r11, digests, snapshot.root.name, registry, effect, toolchain, diagnostics,
        )
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        result = _blocked(str(exc))
    logger.debug("check_intrinsic_vam_formal_bridge exit status=%s", result.status)
    return result
