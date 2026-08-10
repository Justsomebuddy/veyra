"""Internal fail-closed phase/R12-continuous R13 Lean bridge."""
from __future__ import annotations

import logging
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from .intrinsic_observer_echo_evidence import (
    intrinsic_observer_echo_evidence,
    verify_intrinsic_observer_echo_evidence,
)
from .intrinsic_observer_echo_effects import (
    BRIDGE_ID,
    EFFECT_BOUNDARY,
    intrinsic_observer_echo_effect_data,
    intrinsic_observer_echo_effect_digest,
)
from .intrinsic_observer_echo_formal_bridge_io import (
    LEAN_TOOLCHAIN, binding_digest, lean_command, materialize_snapshot,
    sha_digest, toolchain_identity,
)
from .intrinsic_observer_echo_formal_compile import compile_snapshot
from .intrinsic_observer_echo_formal_lean_render import (
    THEOREM_IDS, THEOREM_ROWS, canonical_intrinsic_observer_echo_formal_lean,
)
from .intrinsic_observer_echo_formal_manifest import (
    EXPECTED_BINDING_DIGEST, EXPECTED_PHASE_ARTIFACT, EXPECTED_R11_BINDING,
    EXPECTED_R12_BINDING, EXPECTED_R13_TCB_DIGESTS,
    EXPECTED_SNAPSHOT_DIGEST, EXPECTED_SOURCE_ELABORATION_BINDING,
    EXPECTED_TOOLCHAIN_IDENTITY, MANIFEST_BOUNDARY,
)
from .intrinsic_observer_echo_formal_objects import (
    _EXPECTED_R13_OBJECT_ROWS, EXPECTED_R13_OBJECTS,
)
from .intrinsic_observer_echo_formal_report import (
    IntrinsicObserverEchoFormalBridgeReport, valid_digest_manifest,
    valid_object_manifest, valid_source_origins,
)
from .intrinsic_observer_echo_formal_snapshot import (
    _SNAPSHOT_NAME_ROWS, require_valid_snapshot_layout,
)
from .intrinsic_observer_echo_source import (
    intrinsic_observer_echo_source_artifact,
    verify_intrinsic_observer_echo_source_artifact,
)
from .intrinsic_vam_formal_bridge import (
    intrinsic_vam_formal_bridge_report,
    verify_intrinsic_vam_formal_bridge_report,
)
from .intrinsic_vam_formal_report import valid_intrinsic_vam_formal_report_shape
from .observer_core_bridge_report import read_exact_regular_source
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope
from .shadow_effects import shadow_effect_registry_digest

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
SOURCE_PATHS = MappingProxyType({
    "evidence": PROJECT_ROOT / "src/core/intrinsic_observer_echo_evidence.py",
    "effects": PROJECT_ROOT / "src/core/intrinsic_observer_echo_effects.py",
    "formal_report": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_report.py",
    "formal_snapshot": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_snapshot.py",
    "formal_bridge_io": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_bridge_io.py",
    "formal_compile": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_compile.py",
    "formal_lean_render": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_lean_render.py",
    "formal_bridge_core": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_bridge_core.py",
    "formal_bridge": PROJECT_ROOT / "src/core/intrinsic_observer_echo_formal_bridge.py",
    "phase_source": PROJECT_ROOT / "src/core/intrinsic_observer_echo_source.py",
    "toolchain_runtime": PROJECT_ROOT / "src/core/proof_elaboration_toolchain.py",
    "runtime_guard": PROJECT_ROOT / "src/core/proof_elaboration_runtime_guard.py",
    "effect_types": PROJECT_ROOT / "src/core/shadow_effect_types.py",
    "effects_registry": PROJECT_ROOT / "src/core/shadow_effects.py",
    "lean_arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
    "lean_semantics": LEAN_DIR / "VeyraNativeSemantics.lean",
    "lean_intrinsic_runtime": LEAN_DIR / "VeyraIntrinsicRuntime.lean",
    "lean_kernel": LEAN_DIR / "VeyraProofKernel.lean",
    "lean_soundness": LEAN_DIR / "VeyraProofSoundness.lean",
    "lean_transport": LEAN_DIR / "VeyraRecurrenceModeBridge.lean",
    "lean_observer_core": LEAN_DIR / "VeyraObserverCore.lean",
    "lean_observer_proof": LEAN_DIR / "VeyraObserverProof.lean",
    "lean_intrinsic_vam": LEAN_DIR / "VeyraIntrinsicVamBridge.lean",
    "lean_intrinsic_observer_echo": LEAN_DIR / "VeyraIntrinsicObserverEcho.lean",
})
_CANONICAL_SOURCE_ROWS = tuple(SOURCE_PATHS.items())
_SOURCE_NAMES = (*tuple(SOURCE_PATHS), "lean_export")
_OBJECT_NAMES = tuple(name for name, _ in _SNAPSHOT_NAME_ROWS[:-1])
_CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/{len(_SNAPSHOT_NAME_ROWS)}:{Path(filename).stem}:rc=0"
    for index, (_, filename) in enumerate(_SNAPSHOT_NAME_ROWS, 1)
)


def _local_trust_shape() -> tuple[object, object, str, str, str]:
    """Validate every local root before invoking the expensive R12 parent."""
    logger.debug("r13_bridge_core._local_trust_shape entry")
    require_valid_snapshot_layout()
    try:
        live_rows = tuple(SOURCE_PATHS.items())
    except RuntimeError as exc:
        raise ValueError("r13.2-source-origin-manifest-invalid") from exc
    if live_rows != _CANONICAL_SOURCE_ROWS:
        raise ValueError("r13.2-source-origin-manifest-invalid")
    if not valid_digest_manifest(EXPECTED_R13_TCB_DIGESTS, _SOURCE_NAMES):
        raise ValueError("r13.2-source-manifest-shape-mismatch")
    if not valid_object_manifest(EXPECTED_R13_OBJECTS, _OBJECT_NAMES):
        raise ValueError("r13.2-object-manifest-shape-mismatch")
    phase = intrinsic_observer_echo_source_artifact()
    evidence = intrinsic_observer_echo_evidence()
    if (
        not verify_intrinsic_observer_echo_source_artifact(phase).ok
        or phase.artifact_digest != EXPECTED_PHASE_ARTIFACT
        or phase.r10_binding_digest != EXPECTED_SOURCE_ELABORATION_BINDING
        or not verify_intrinsic_observer_echo_evidence(evidence)
    ):
        raise ValueError("r13.2-local-evidence-rejected")
    effect = intrinsic_observer_echo_effect_data()
    if (
        type(effect) is not dict
        or effect["capabilities"] != [BridgeCapability.PRESERVES.value]
        or effect["promotion_ready"] is not False
        or effect["taxonomy_changed"] is not False
        or effect["boundary"] != EFFECT_BOUNDARY
    ):
        raise ValueError("r13.2-effect-contract-mismatch")
    registry, effect_digest = shadow_effect_registry_digest(), intrinsic_observer_echo_effect_digest()
    logger.debug("r13_bridge_core._local_trust_shape exit")
    return phase, evidence, registry, effect_digest, EFFECT_BOUNDARY


def _verified_r12() -> object:
    """Verify the public R12 report once and preserve its embedded R11 root."""
    logger.debug("r13_bridge_core._verified_r12 entry")
    report = intrinsic_vam_formal_bridge_report()
    if (
        not valid_intrinsic_vam_formal_report_shape(report)
        or report.status != "checked"
        or report.binding_digest != EXPECTED_R12_BINDING
        or report.r11_binding_digest != EXPECTED_R11_BINDING
        or not verify_intrinsic_vam_formal_bridge_report(report)
    ):
        raise ValueError("r13.2-r12-continuity-rejected")
    logger.debug("r13_bridge_core._verified_r12 exit binding=%s", report.binding_digest)
    return report


def _read_sources(paths: Mapping[str, Path], generated: bytes) -> dict[str, bytes]:
    """Read only canonical regular origins plus exact generated bytes."""
    logger.debug("r13_bridge_core._read_sources entry")
    canonical = dict(_CANONICAL_SOURCE_ROWS)
    if paths is not SOURCE_PATHS and not valid_source_origins(paths, canonical):
        raise ValueError("r13.2-source-path-set-invalid")
    result = {name: read_exact_regular_source(path) for name, path in _CANONICAL_SOURCE_ROWS}
    if type(generated) is not bytes:
        raise TypeError("r13.2-generated-export-not-bytes")
    result["lean_export"] = generated
    logger.debug("r13_bridge_core._read_sources exit count=%d", len(result))
    return result


def _blocked(reason: str) -> IntrinsicObserverEchoFormalBridgeReport:
    """Return one stable non-promoting blocked report."""
    logger.error("R13 formal bridge blocked reason=%s", reason)
    return IntrinsicObserverEchoFormalBridgeReport(
        "blocked", BRIDGE_ID, (), "", "", "", "", "", "", "", (), (), "",
        BridgeCapability.PRESERVES, EvidenceClass.FORMAL_BRIDGE,
        EvidenceScope.GENERAL, "", False, False, False, False, False, False,
        False, False, False, LEAN_TOOLCHAIN, reason, MANIFEST_BOUNDARY,
    )


def _validate_sources(sources: Mapping[str, bytes], generated: bytes) -> dict[str, str]:
    """Reject source/export/placeholder/theorem or manual-digest drift."""
    logger.debug("r13_bridge_core._validate_sources entry")
    if sources["lean_export"] != generated:
        raise ValueError("r13.2-generated-lean-source-drift")
    lean_bytes = b"\n".join(sources[name] for name, _ in _SNAPSHOT_NAME_ROWS)
    forbidden = tuple(sorted(set(PLACEHOLDER.findall(lean_bytes.decode("utf-8")))))
    if forbidden:
        raise ValueError("r13.2-forbidden-lean-placeholder:" + ",".join(forbidden))
    for _, symbol in THEOREM_ROWS:
        if symbol.encode() not in sources["lean_intrinsic_observer_echo"] or symbol.encode() not in generated:
            raise ValueError("r13.2-lean-theorem-set-incomplete")
    digests = {name: sha_digest(source) for name, source in sources.items()}
    if (
        not valid_digest_manifest(EXPECTED_R13_TCB_DIGESTS, _SOURCE_NAMES)
        or tuple(digests.items()) != tuple(EXPECTED_R13_TCB_DIGESTS.items())
    ):
        raise ValueError("r13.2-reviewed-tcb-drift")
    logger.debug("r13_bridge_core._validate_sources exit")
    return digests


def _report_body(local, r12, digests, snapshot, toolchain) -> dict[str, object]:
    """Build the canonical report-binding body."""
    logger.debug("r13_bridge_core._report_body entry")
    phase, evidence, registry, effect, _ = local
    result = {
        "bridge_id": BRIDGE_ID, "theorem_ids": THEOREM_IDS,
        "phase_artifact_digest": phase.artifact_digest,
        "source_elaboration_binding_digest": phase.r10_binding_digest,
        "r11_binding_digest": r12.r11_binding_digest,
        "r12_binding_digest": r12.binding_digest,
        "executable_evidence_digest": evidence.digest,
        "effect_registry_digest": registry, "effect_digest": effect,
        "source_digests": tuple(digests.items()),
        "object_records": _EXPECTED_R13_OBJECT_ROWS,
        "snapshot_digest": snapshot,
        "capability": BridgeCapability.PRESERVES.value,
        "evidence_class": EvidenceClass.FORMAL_BRIDGE.value,
        "evidence_scope": EvidenceScope.GENERAL.value,
        "toolchain": toolchain, "promotion_ready": False, "taxonomy_changed": False,
    }
    logger.debug("r13_bridge_core._report_body exit")
    return result


def _checked_report(local, r12, digests, snapshot, toolchain, diagnostics):
    """Build and pin one complete checked report."""
    logger.debug("r13_bridge_core._checked_report entry")
    phase, evidence, registry, effect, _ = local
    body = _report_body(local, r12, digests, snapshot, toolchain)
    result = IntrinsicObserverEchoFormalBridgeReport(
        "checked", BRIDGE_ID, THEOREM_IDS, phase.artifact_digest,
        phase.r10_binding_digest, r12.r11_binding_digest, r12.binding_digest,
        evidence.digest, registry, effect, tuple(digests.items()),
        _EXPECTED_R13_OBJECT_ROWS, snapshot, BridgeCapability.PRESERVES,
        EvidenceClass.FORMAL_BRIDGE, EvidenceScope.GENERAL, binding_digest(body),
        True, True, True, True, True, True, True, False, False,
        toolchain, diagnostics, MANIFEST_BOUNDARY,
    )
    actual = (result.snapshot_digest, result.binding_digest, result.toolchain)
    expected = (EXPECTED_SNAPSHOT_DIGEST, EXPECTED_BINDING_DIGEST, EXPECTED_TOOLCHAIN_IDENTITY)
    if actual != expected:
        raise ValueError("r13.2-reviewed-envelope-drift")
    logger.debug("r13_bridge_core._checked_report exit binding=%s", result.binding_digest)
    return result


def _origins(source_paths=None, generated_export=None):
    """Resolve local roots before one verified R12 replay, then materialize."""
    logger.debug("r13_bridge_core._origins entry")
    local = _local_trust_shape()
    r12 = _verified_r12()
    phase, evidence, registry, effect, _ = local
    values = (
        phase.artifact_digest, phase.r10_binding_digest, r12.r11_binding_digest,
        r12.binding_digest, evidence.digest, registry, effect,
    )
    expected = canonical_intrinsic_observer_echo_formal_lean(*values)
    generated = expected if generated_export is None else generated_export
    paths = SOURCE_PATHS if source_paths is None else source_paths
    sources = _read_sources(paths, generated)
    digests = _validate_sources(sources, expected)
    command = lean_command()
    if not command:
        raise ValueError("r13.2-pinned-lean-not-found")
    toolchain = toolchain_identity(command)
    snapshot = materialize_snapshot(sources, digests, values, toolchain)
    logger.debug("r13_bridge_core._origins exit")
    return local, r12, sources, digests, command, toolchain, snapshot


def check_intrinsic_observer_echo_formal_bridge(
    source_paths=None,
    generated_export=None,
) -> IntrinsicObserverEchoFormalBridgeReport:
    """Check local trust, then parent continuity and fresh guarded Lean."""
    logger.debug("check_r13_formal_bridge entry")
    try:
        local, r12, sources, digests, command, toolchain, snapshot = _origins(
            source_paths, generated_export,
        )
        checked, diagnostics = compile_snapshot(command, snapshot, sources)
        if not checked:
            raise ValueError(diagnostics)
        result = _checked_report(
            local, r12, digests, snapshot.root.name, toolchain, diagnostics,
        )
    except (KeyError, OSError, TypeError, UnicodeDecodeError, ValueError) as exc:
        result = _blocked(str(exc))
    logger.debug("check_r13_formal_bridge exit status=%s", result.status)
    return result
