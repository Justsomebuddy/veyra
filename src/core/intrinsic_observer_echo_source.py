"""Canonical phase-one source artifact for the R13 observer-echo candidate."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import logging
from typing import NoReturn

from .proof_core_codec import digest_data
from .proof_elaboration_artifact import make_surface_elaboration_artifact
from .proof_surface_elaborator import compile_surface_program

logger = logging.getLogger(__name__)

SCHEMA = "veyra.intrinsic-observer-echo-source.r13.2.v1"
PHASE = "canonical-source-only"
THEOREM_LABEL = "R13-SOURCE-UNIT-WEAVE"
THEOREM_DOMAIN = "veyra-r13-source-theorem-v1"
ARTIFACT_DOMAIN = "veyra-r13-source-artifact-v1"
CANONICAL_SOURCE = b"""(veyra-proof 1
  (claim (forall item recurrence
    (equal (weave (var item) (pulse (silence))) (var item))))
  (proof (forall-intro item recurrence
    (native-law weave-unit-right (var item)))))"""
EXPECTED_SOURCE_DIGEST = "1280f1c4114122b4b004cc5c46f841f644b2ee61d5feb693252ac1ea232370f6"
EXPECTED_THEOREM_DIGEST = "088ba0532cd323451adadc6e6be609eca0963954ba191cec12639d7d760de3a5"
EXPECTED_SYNTAX_DIGEST = "768b387de013190381ac86cab8b9311f37eb04a3141b5aa37d27b34647ef3ae8"
EXPECTED_SEMANTIC_DIGEST = "8784be9b8ed5c56388542e14a91263336f17b3c79d3dbacb7291e9426779810b"
EXPECTED_PROOF_DIGEST = "290865c60b7d4013f890afc673d9dc8d26dd2c2259880970f35430d67449d9a2"
EXPECTED_R10_BINDING_DIGEST = "ef56991387741cfc931ef7f2ce9f8887730bd8720daecdd1d80a93e08f3bbd58"
EXPECTED_ARTIFACT_DIGEST = "6e2514f93049be5b50b21f1af9051357461c039d14469950fb826322c0b3a4ef"
BOUNDARY = (
    "parser- and kernel-accepted unit-weave equality source only; no R13 "
    "observer-echo theorem, Lean bridge, effect, promotion, taxonomy, or certificate"
)


@dataclass(frozen=True)
class IntrinsicObserverEchoSourceArtifact:
    """Exact source replay and its reviewed phase-one bindings."""

    schema: str
    phase: str
    theorem_label: str
    source: str
    source_size: int
    source_digest: str
    theorem_digest: str
    syntax_digest: str
    semantic_digest: str
    proof_digest: str
    r10_binding_digest: str
    statement: str
    rule_closure: tuple[str, ...]
    native_law_closure: tuple[str, ...]
    boundary: str
    artifact_digest: str


@dataclass(frozen=True)
class IntrinsicObserverEchoSourceCheck:
    """Non-throwing exact-origin verification result."""

    ok: bool
    errors: tuple[str, ...]


def _reject(reason: str) -> NoReturn:
    logger.debug("intrinsic_observer_echo_source._reject entry reason=%s", reason)
    logger.error("intrinsic_observer_echo_source rejected reason=%s", reason)
    raise ValueError(reason)


def _body(artifact: IntrinsicObserverEchoSourceArtifact) -> dict[str, object]:
    logger.debug("_body entry theorem=%s", artifact.theorem_label)
    result = {
        "schema": artifact.schema,
        "phase": artifact.phase,
        "theorem_label": artifact.theorem_label,
        "source": artifact.source,
        "source_size": artifact.source_size,
        "source_digest": artifact.source_digest,
        "theorem_digest": artifact.theorem_digest,
        "syntax_digest": artifact.syntax_digest,
        "semantic_digest": artifact.semantic_digest,
        "proof_digest": artifact.proof_digest,
        "r10_binding_digest": artifact.r10_binding_digest,
        "statement": artifact.statement,
        "rules": list(artifact.rule_closure),
        "native_laws": list(artifact.native_law_closure),
        "boundary": artifact.boundary,
    }
    logger.debug("_body exit fields=%d", len(result))
    return result


def _shape_errors(artifact: object) -> tuple[str, ...]:
    logger.debug("_shape_errors entry type=%s", type(artifact).__name__)
    errors: list[str] = []
    if type(artifact) is not IntrinsicObserverEchoSourceArtifact:
        errors.append("invalid-r13-source-artifact-type")
    else:
        string_fields = (
            artifact.schema,
            artifact.phase,
            artifact.theorem_label,
            artifact.source,
            artifact.source_digest,
            artifact.theorem_digest,
            artifact.syntax_digest,
            artifact.semantic_digest,
            artifact.proof_digest,
            artifact.r10_binding_digest,
            artifact.statement,
            artifact.boundary,
            artifact.artifact_digest,
        )
        if type(artifact.source_size) is not int:
            errors.append("invalid-r13-source-scalar-types")
        if any(type(item) is not str for item in string_fields):
            errors.append("invalid-r13-source-scalar-types")
        closures = (artifact.rule_closure, artifact.native_law_closure)
        if any(type(row) is not tuple or any(type(item) is not str for item in row) for row in closures):
            errors.append("invalid-r13-source-closures")
    result = tuple(errors)
    logger.debug("_shape_errors exit errors=%r", result)
    return result


def _build_source_artifact() -> IntrinsicObserverEchoSourceArtifact:
    logger.debug("_build_source_artifact entry source_bytes=%d", len(CANONICAL_SOURCE))
    try:
        source_text = CANONICAL_SOURCE.decode("ascii")
        elaborated = compile_surface_program(source_text)
        r10_artifact = make_surface_elaboration_artifact(
            THEOREM_LABEL, CANONICAL_SOURCE, elaborated,
        )
        theorem_digest = digest_data(
            json.loads(r10_artifact.elaborated_statement), THEOREM_DOMAIN,
        )
        seed = IntrinsicObserverEchoSourceArtifact(
            SCHEMA,
            PHASE,
            THEOREM_LABEL,
            source_text,
            len(CANONICAL_SOURCE),
            r10_artifact.source_digest,
            theorem_digest,
            r10_artifact.surface_syntax_digest,
            r10_artifact.semantic_digest,
            r10_artifact.r7_artifact_digest,
            r10_artifact.binding_digest,
            r10_artifact.elaborated_statement,
            r10_artifact.rule_closure,
            r10_artifact.native_law_closure,
            BOUNDARY,
            "",
        )
        result = replace(seed, artifact_digest=digest_data(_body(seed), ARTIFACT_DOMAIN))
    except (AttributeError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.error("_build_source_artifact error=%s", exc)
        raise
    logger.debug("_build_source_artifact exit artifact=%s", result.artifact_digest)
    return result


def _pin_errors(artifact: IntrinsicObserverEchoSourceArtifact) -> tuple[str, ...]:
    logger.debug("_pin_errors entry artifact=%s", artifact.artifact_digest)
    expected = (
        (artifact.schema, SCHEMA, "schema"),
        (artifact.phase, PHASE, "phase"),
        (artifact.theorem_label, THEOREM_LABEL, "theorem-label"),
        (artifact.source, CANONICAL_SOURCE.decode("ascii"), "source"),
        (artifact.source_size, len(CANONICAL_SOURCE), "source-size"),
        (artifact.source_digest, EXPECTED_SOURCE_DIGEST, "source-digest"),
        (artifact.theorem_digest, EXPECTED_THEOREM_DIGEST, "theorem-digest"),
        (artifact.syntax_digest, EXPECTED_SYNTAX_DIGEST, "syntax-digest"),
        (artifact.semantic_digest, EXPECTED_SEMANTIC_DIGEST, "semantic-digest"),
        (artifact.proof_digest, EXPECTED_PROOF_DIGEST, "proof-digest"),
        (artifact.r10_binding_digest, EXPECTED_R10_BINDING_DIGEST, "r10-binding"),
        (artifact.rule_closure, ("forall-intro", "native-law"), "rule-closure"),
        (artifact.native_law_closure, ("weave-unit-right",), "native-law-closure"),
        (artifact.boundary, BOUNDARY, "boundary"),
        (artifact.artifact_digest, EXPECTED_ARTIFACT_DIGEST, "artifact-digest"),
    )
    result = tuple(f"r13-source-{label}-mismatch" for actual, wanted, label in expected if actual != wanted)
    logger.debug("_pin_errors exit errors=%r", result)
    return result


def intrinsic_observer_echo_source_artifact() -> IntrinsicObserverEchoSourceArtifact:
    """Replay the reviewed source and return only its pinned phase-one artifact."""
    logger.debug("intrinsic_observer_echo_source_artifact entry")
    result = _build_source_artifact()
    errors = _shape_errors(result) + _pin_errors(result)
    if errors:
        logger.error("intrinsic_observer_echo_source_artifact error=%r", errors)
        _reject(errors[0])
    logger.debug("intrinsic_observer_echo_source_artifact exit artifact=%s", result.artifact_digest)
    return result


def verify_intrinsic_observer_echo_source_artifact(
    artifact: object,
) -> IntrinsicObserverEchoSourceCheck:
    """Fail closed unless every reviewed source, theorem, and proof binding replays."""
    logger.debug(
        "verify_intrinsic_observer_echo_source_artifact entry exact_type=%s",
        type(artifact) is IntrinsicObserverEchoSourceArtifact,
    )
    errors: list[str] = []
    if type(artifact) is not IntrinsicObserverEchoSourceArtifact:
        errors.append("invalid-r13-source-artifact-type")
    else:
        try:
            errors.extend(_shape_errors(artifact))
            if not errors:
                errors.extend(_pin_errors(artifact))
                if not errors and artifact != _build_source_artifact():
                    errors.append("r13-source-artifact-replay-mismatch")
                if not errors and artifact.artifact_digest != digest_data(
                    _body(artifact), ARTIFACT_DOMAIN
                ):
                    errors.append("r13-source-artifact-binding-mismatch")
        except Exception:
            logger.error(
                "verify_intrinsic_observer_echo_source_artifact blocked stage=validation"
            )
            errors.append("invalid-r13-source-artifact-shape")
    result = IntrinsicObserverEchoSourceCheck(not errors, tuple(errors))
    if errors:
        logger.error("verify_intrinsic_observer_echo_source_artifact blocked errors=%r", errors)
    logger.debug(
        "verify_intrinsic_observer_echo_source_artifact exit ok=%s errors=%d",
        result.ok,
        len(result.errors),
    )
    return result
