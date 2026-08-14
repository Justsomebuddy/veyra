"""Canonical R13 theorem object consumed by the exact R8 promotion contract."""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from typing import TypeGuard

from .intrinsic_observer_echo_effects import (
    intrinsic_observer_echo_effect_digest,
)
from .intrinsic_observer_echo_evidence import (
    intrinsic_observer_echo_evidence,
    verify_intrinsic_observer_echo_evidence,
)
from .intrinsic_observer_echo_source import (
    intrinsic_observer_echo_source_artifact,
    verify_intrinsic_observer_echo_source_artifact,
)
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)
SCHEMA = "veyra.intrinsic-observer-echo-theorem.r13.3.v1"
THEOREM_ID = "THM-R13-003"
STATEMENT_DOMAIN = "veyra-r13-intrinsic-observer-echo-statement-v1"
ARTIFACT_DOMAIN = "veyra-r13-intrinsic-observer-echo-theorem-v1"
STATEMENT = (
    "forall target observer value response, "
    "observerBounded(observer) -> "
    "r11RecurrenceBounded(value) -> "
    "echoOutcomeBounded(echo(observer,value,value)) -> "
    "observeIntrinsic(observer,intrinsicMode(value))=ready(response) -> "
    "echoIR(observer,lowerRecurrenceIR(weave(value,pulse(silence))),"
    "lowerRecurrenceIR(value))=some(echo(lowerResponseIR(response)))"
)
PROOF_RULES = (
    "r7-check-sound",
    "r9-intrinsic-image",
    "r11-ready-domain-reflexivity",
    "r12-echo-transport",
)
NATIVE_LAWS = ("weave-unit-right",)
EXPECTED_STATEMENT_DIGEST = "9aa80350921552fdd569bb54474c9f51bd12baee1d3e154dfa40e2dba882a497"
EXPECTED_ARTIFACT_DIGEST = "89605a48cd32c0722bcd45b3ac59975adddcdb809d768afd241ff91668376e1d"
BOUNDARY = (
    "general only under explicit R12 bounds: observer nodes<=2048/depth<=128, "
    "recurrence tacts<=128, and transported echo outcome nodes<=4096/depth<=128; "
    "readiness and the exact intrinsic lowering image are required; observer totality, "
    "echo reflection, raw IR, VAMI, receipt authority, and broad cyclic resonance "
    "remain excluded"
)


@dataclass(frozen=True, slots=True)
class IntrinsicObserverEchoTheorem:
    """Exact replay-bound theorem metadata for THM-R13-003."""

    schema: str
    theorem_id: str
    statement: str
    statement_digest: str
    source_artifact_digest: str
    source_proof_digest: str
    executable_evidence_digest: str
    effect_digest: str
    proof_rules: tuple[str, ...]
    native_laws: tuple[str, ...]
    status: str
    boundary: str
    artifact_digest: str


def _body(theorem: IntrinsicObserverEchoTheorem) -> dict[str, object]:
    """Serialize every theorem field except its self-digest."""
    logger.debug("intrinsic_observer_echo_theorem._body entry")
    result: dict[str, object] = {
        "schema": theorem.schema,
        "theorem_id": theorem.theorem_id,
        "statement": theorem.statement,
        "statement_digest": theorem.statement_digest,
        "source_artifact_digest": theorem.source_artifact_digest,
        "source_proof_digest": theorem.source_proof_digest,
        "executable_evidence_digest": theorem.executable_evidence_digest,
        "effect_digest": theorem.effect_digest,
        "proof_rules": list(theorem.proof_rules),
        "native_laws": list(theorem.native_laws),
        "status": theorem.status,
        "boundary": theorem.boundary,
    }
    logger.debug("intrinsic_observer_echo_theorem._body exit fields=%d", len(result))
    return result


def _valid_shape(value: object) -> TypeGuard[IntrinsicObserverEchoTheorem]:
    """Reject subclasses and hostile theorem field containers."""
    logger.debug(
        "intrinsic_observer_echo_theorem._valid_shape entry type=%s",
        type(value).__name__,
    )
    if type(value) is not IntrinsicObserverEchoTheorem:
        return False
    try:
        texts = (
            value.schema,
            value.theorem_id,
            value.statement,
            value.statement_digest,
            value.source_artifact_digest,
            value.source_proof_digest,
            value.executable_evidence_digest,
            value.effect_digest,
            value.status,
            value.boundary,
            value.artifact_digest,
        )
        result = (
            all(type(item) is str for item in texts)
            and type(value.proof_rules) is tuple
            and all(type(item) is str for item in value.proof_rules)
            and type(value.native_laws) is tuple
            and all(type(item) is str for item in value.native_laws)
        )
    except AttributeError:
        result = False
    logger.debug("intrinsic_observer_echo_theorem._valid_shape exit result=%s", result)
    return result


def _build() -> IntrinsicObserverEchoTheorem:
    """Replay source/evidence/effect and construct the canonical theorem object."""
    logger.debug("intrinsic_observer_echo_theorem._build entry")
    source = intrinsic_observer_echo_source_artifact()
    source_check = verify_intrinsic_observer_echo_source_artifact(source)
    evidence = intrinsic_observer_echo_evidence()
    if not source_check.ok or not verify_intrinsic_observer_echo_evidence(evidence):
        raise ValueError("r13-theorem-parent-evidence-rejected")
    statement_digest = digest_data(STATEMENT, STATEMENT_DOMAIN)
    seed = IntrinsicObserverEchoTheorem(
        SCHEMA,
        THEOREM_ID,
        STATEMENT,
        statement_digest,
        source.artifact_digest,
        source.proof_digest,
        evidence.digest,
        intrinsic_observer_echo_effect_digest(),
        PROOF_RULES,
        NATIVE_LAWS,
        "local-source-evidence-effect-bound",
        BOUNDARY,
        "",
    )
    result = replace(seed, artifact_digest=digest_data(_body(seed), ARTIFACT_DOMAIN))
    logger.debug(
        "intrinsic_observer_echo_theorem._build exit artifact=%s",
        result.artifact_digest,
    )
    return result


def intrinsic_observer_echo_theorem() -> IntrinsicObserverEchoTheorem:
    """Return only the exact reviewed R13 theorem object."""
    logger.debug("intrinsic_observer_echo_theorem entry")
    result = _build()
    if (
        result.statement_digest != EXPECTED_STATEMENT_DIGEST
        or result.artifact_digest != EXPECTED_ARTIFACT_DIGEST
    ):
        raise ValueError("r13-theorem-reviewed-envelope-drift")
    logger.debug(
        "intrinsic_observer_echo_theorem exit theorem=%s", result.theorem_id,
    )
    return result


def verify_intrinsic_observer_echo_theorem(value: object) -> bool:
    """Fail closed unless the exact source/effect/evidence theorem replays."""
    logger.debug(
        "verify_intrinsic_observer_echo_theorem entry type=%s",
        type(value).__name__,
    )
    if not _valid_shape(value):
        return False
    try:
        expected = _build()
        result = (
            value == expected
            and value.statement_digest == EXPECTED_STATEMENT_DIGEST
            and value.artifact_digest == EXPECTED_ARTIFACT_DIGEST
            and value.statement_digest == digest_data(value.statement, STATEMENT_DOMAIN)
            and value.artifact_digest == digest_data(_body(value), ARTIFACT_DOMAIN)
        )
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        logger.exception("R13 theorem verification failed")
        result = False
    logger.debug("verify_intrinsic_observer_echo_theorem exit result=%s", result)
    return result
