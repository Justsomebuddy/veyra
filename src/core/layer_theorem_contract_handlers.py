"""Trusted executable handlers and evidence normalization for R8 contracts."""
from __future__ import annotations

from collections.abc import Callable
import logging

from .layer_theorem_contract_types import (
    LayerTheoremContract,
    STATEMENT_DOMAIN,
)
from .layer_theorem_contract_executable import handler_executable_digest
from .intrinsic_observer_echo_formal_bridge import (
    intrinsic_observer_echo_contract_bridge_report,
    is_trusted_intrinsic_observer_echo_contract_report,
)
from .intrinsic_observer_echo_formal_manifest import (
    BRIDGE_ID as R13_LEAN_BRIDGE_ID,
    EXPECTED_BINDING_DIGEST as EXPECTED_R13_BINDING_DIGEST,
)
from .intrinsic_observer_echo_formal_report import (
    IntrinsicObserverEchoFormalBridgeReport,
)
from .intrinsic_observer_echo_theorem import (
    EXPECTED_ARTIFACT_DIGEST as EXPECTED_R13_ARTIFACT_DIGEST,
    IntrinsicObserverEchoTheorem,
    intrinsic_observer_echo_theorem,
    verify_intrinsic_observer_echo_theorem,
)
from .proof_core_codec import digest_data, prop_data
from .proof_core_resonance import (
    IntrinsicResonanceTheorem,
    intrinsic_resonance_theorem,
    verify_intrinsic_theorem_binding,
)
from .proof_elaboration_bridge import (
    THEOREM_IDS as R10_THEOREM_IDS,
    ProofElaborationBridgeReport,
    proof_elaboration_bridge_report,
    verify_proof_elaboration_bridge_report,
)

logger = logging.getLogger(__name__)
INTRINSIC_TRANSPORT_CARRIER = "veyra.proof.recurrence-equiv-strict-intrinsic-mode.v1"
R10_LEAN_BRIDGE_ID = "veyra.lean.r10.proof-elaboration-tcb.v1"
R10_HANDLER_ID = "veyra.handler.intrinsic-resonance.r10.v1"
R10_TRUSTED_CONTRACT_DIGEST = "484534000ee59a28d0d131b777dcc775d56d24b82c70797954ba82c8570a8eba"
R13_HANDLER_ID = "veyra.handler.intrinsic-observer-echo.r13.v1"
R13_TRANSPORT_CARRIER = (
    "veyra.proof.r7-unit-weave.r9-image.r11-ready-echo.r12-lowering-image.r13.v1"
)
R13_TRUSTED_CONTRACT_DIGEST = "0c71003a9114faad3e5fb497993030fa86155d3ef2aa155405cbd3050a2ea09e"
R13_TRUSTED_EXECUTABLE_DIGEST = "ee12d603d86b0a1387bcba3e9c6a76fbba983940908e5ec07a0b5d856a9d5673"
EvidenceTuple = tuple[
    str, str, str, str, tuple[str, ...], tuple[str, ...], str,
]


def verify_intrinsic_contract(
    contract: LayerTheoremContract,
    theorem: object,
) -> bool:
    """Accept only the exact old R7 theorem under the old carrier and bridge."""
    logger.debug("verify_intrinsic_contract entry")
    result = (
        contract.semantic_carrier == INTRINSIC_TRANSPORT_CARRIER
        and contract.bridge_id == R10_LEAN_BRIDGE_ID
        and type(theorem) is IntrinsicResonanceTheorem
        and verify_intrinsic_theorem_binding(theorem)
    )
    logger.debug("verify_intrinsic_contract exit result=%s", result)
    return result


def verify_r10_bridge(
    contract: LayerTheoremContract,
    report: object,
    artifact_digest: str,
) -> bool:
    """Accept only the independently rehashed R10 report for the old artifact."""
    logger.debug("verify_r10_bridge entry bridge=%s", contract.bridge_id)
    result = (
        contract.bridge_id == R10_LEAN_BRIDGE_ID
        and type(report) is ProofElaborationBridgeReport
        and verify_proof_elaboration_bridge_report(report)
        and report.status == "checked"
        and report.artifact_checked
        and report.source_bound
        and report.snapshot_checked
        and report.manifest_checked
        and report.lean_checked
        and report.r7_artifact_digest == artifact_digest
        and report.theorem_ids == R10_THEOREM_IDS
    )
    logger.debug("verify_r10_bridge exit result=%s", result)
    return result


def verify_r13_contract(
    contract: LayerTheoremContract,
    theorem: object,
) -> bool:
    """Accept only the exact R13 theorem under its narrow composite carrier."""
    logger.debug("verify_r13_contract entry")
    result = (
        contract.semantic_carrier == R13_TRANSPORT_CARRIER
        and contract.bridge_id == R13_LEAN_BRIDGE_ID
        and type(theorem) is IntrinsicObserverEchoTheorem
        and verify_intrinsic_observer_echo_theorem(theorem)
    )
    logger.debug("verify_r13_contract exit result=%s", result)
    return result


def verify_r13_bridge(
    contract: LayerTheoremContract,
    report: object,
    artifact_digest: str,
) -> bool:
    """Accept only the exact once-checked report returned by the trusted provider."""
    logger.debug("verify_r13_bridge entry bridge=%s", contract.bridge_id)
    trusted_report = is_trusted_intrinsic_observer_echo_contract_report(report)
    result = (
        trusted_report
        and contract.bridge_id == R13_LEAN_BRIDGE_ID
        and artifact_digest == EXPECTED_R13_ARTIFACT_DIGEST
        and type(report) is IntrinsicObserverEchoFormalBridgeReport
        and report.status == "checked"
        and report.binding_digest == EXPECTED_R13_BINDING_DIGEST
        and report.phase_checked
        and report.r12_checked
        and report.manifest_checked
        and report.source_bound
        and report.object_bound
        and report.snapshot_checked
        and report.lean_checked
        and report.promotion_ready is False
        and report.taxonomy_changed is False
    )
    logger.debug("verify_r13_bridge exit result=%s", result)
    return result


def normalize_theorem_evidence(
    contract: LayerTheoremContract,
    theorem: object,
) -> EvidenceTuple:
    """Normalize theorem evidence through trusted handler-ID dispatch only."""
    logger.debug("normalize_theorem_evidence entry handler=%s", contract.handler_id)
    if contract.handler_id == R10_HANDLER_ID and type(theorem) is IntrinsicResonanceTheorem:
        result = (
            theorem.theorem_id,
            digest_data(prop_data(theorem.statement), STATEMENT_DOMAIN),
            theorem.artifact.proof_digest,
            theorem.artifact.proof_digest,
            tuple(item.value for item in theorem.rule_closure),
            tuple(item.value for item in theorem.native_law_closure),
            theorem.boundary,
        )
    elif contract.handler_id == R13_HANDLER_ID and type(theorem) is IntrinsicObserverEchoTheorem:
        result = (
            theorem.theorem_id,
            theorem.statement_digest,
            theorem.artifact_digest,
            theorem.source_proof_digest,
            theorem.proof_rules,
            theorem.native_laws,
            theorem.boundary,
        )
    else:
        raise ValueError("theorem-contract-evidence-normalizer-mismatch")
    logger.debug("normalize_theorem_evidence exit theorem=%s", result[0])
    return result


def validate_contract_handlers(
    contract: LayerTheoremContract,
    digest: Callable[[LayerTheoremContract], str],
) -> None:
    """Reject unknown handlers, static drift, and provider/verifier replacement."""
    logger.debug("validate_contract_handlers entry layer=%s", contract.layer)
    actual = (
        contract.theorem_provider,
        contract.theorem_verifier,
        contract.bridge_provider,
        contract.bridge_verifier,
    )
    executable_rows = (
        ("theorem_provider", contract.theorem_provider),
        ("theorem_verifier", contract.theorem_verifier),
        ("bridge_provider", contract.bridge_provider),
        ("bridge_verifier", contract.bridge_verifier),
        ("evidence_normalizer", normalize_theorem_evidence),
    )
    trusted = {
        R10_HANDLER_ID: (
            R10_TRUSTED_CONTRACT_DIGEST,
            None,
            intrinsic_resonance_theorem,
            verify_intrinsic_contract,
            proof_elaboration_bridge_report,
            verify_r10_bridge,
        ),
        R13_HANDLER_ID: (
            R13_TRUSTED_CONTRACT_DIGEST,
            R13_TRUSTED_EXECUTABLE_DIGEST,
            intrinsic_observer_echo_theorem,
            verify_r13_contract,
            intrinsic_observer_echo_contract_bridge_report,
            verify_r13_bridge,
        ),
    }.get(contract.handler_id)
    if trusted is None:
        logger.error(
            "validate_contract_handlers unknown handler layer=%s handler=%s",
            contract.layer,
            contract.handler_id,
        )
        raise ValueError("theorem-contract-handler-id-mismatch")
    actual_contract_digest = digest(contract)
    if actual_contract_digest != trusted[0]:
        logger.error(
            "validate_contract_handlers binding mismatch layer=%s expected=%s actual=%s",
            contract.layer,
            trusted[0],
            actual_contract_digest,
        )
        raise ValueError("theorem-contract-trusted-binding-mismatch")
    if any(left is not right for left, right in zip(actual, trusted[2:], strict=True)):
        logger.error(
            "validate_contract_handlers identity mismatch layer=%s",
            contract.layer,
        )
        raise ValueError("theorem-contract-handler-mismatch")
    expected_executable = trusted[1]
    if expected_executable is not None:
        actual_executable = handler_executable_digest(
            contract.handler_id,
            executable_rows,
        )
        if (
            contract.executable_digest != expected_executable
            or actual_executable != expected_executable
        ):
            logger.error(
                "validate_contract_handlers executable mismatch layer=%s expected=%s actual=%s",
                contract.layer,
                expected_executable,
                actual_executable,
            )
            raise ValueError("theorem-contract-handler-executable-mismatch")
    logger.debug("validate_contract_handlers exit layer=%s", contract.layer)
