"""Composite source/surface/R7/R9 artifact for proof-grade elaboration."""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import logging
from typing import NoReturn

from .intrinsic_mode_bridge import (
    IntrinsicModeBridgeReport, intrinsic_mode_bridge_report,
    verify_intrinsic_mode_bridge_report,
)
from .intrinsic_mode_manifest import TCB_SCHEMA as R9_TCB_SCHEMA
from .proof_core_artifact import (
    artifact_json, make_proof_artifact, verify_proof_artifact,
)
from .proof_core_codec import canonical_json, digest_data, prop_data
from .proof_core_kernel import ProofKernelError, infer_proof
from .proof_core_types import CoreProp, ProofContext, ProofTerm
from .proof_dependency_support import (
    image_composition_support, prop_support, support_by_category,
)
from .proof_surface_codec import surface_program_data, surface_syntax_digest
from .proof_surface_elaborator import ElaboratedProgram, compile_surface_program
from .proof_surface_types import SURFACE_LANGUAGE_ID

logger = logging.getLogger(__name__)
SCHEMA = "veyra-proof-elaboration-v1"
SOURCE_DOMAIN = b"veyra-proof-elaboration-source-v1\0"
SURFACE_DOMAIN = "veyra-proof-surface-ast-v1"
BINDING_DOMAIN = "veyra-proof-elaboration-binding-v1"
BOUNDARY = (
    "closed recurrence proof elaboration bound to exact source and canonical "
    "surface syntax, R7 replay, and the fixed-anchor unary R9 image only"
)


@dataclass(frozen=True)
class ProofElaborationArtifact:
    """Immutable composite evidence for one generic, closed elaboration."""

    schema: str
    surface_schema: str
    theorem_id: str
    source_digest: str
    source_size: int
    canonical_surface_ast: str
    surface_syntax_digest: str
    semantic_digest: str
    elaborated_statement: str
    r7_artifact: str
    r7_artifact_digest: str
    rule_closure: tuple[str, ...]
    native_law_closure: tuple[str, ...]
    dependency_support: tuple[tuple[str, tuple[str, ...]], ...]
    r9_tcb_schema: str
    r9_theorem_ids: tuple[str, ...]
    r9_source_digests: tuple[tuple[str, str], ...]
    r9_binding_digest: str
    toolchain: str
    boundary: str
    binding_digest: str


@dataclass(frozen=True)
class ElaborationArtifactCheck:
    """Non-throwing exact-origin replay result."""

    ok: bool
    errors: tuple[str, ...]


def _reject(reason: str) -> NoReturn:
    logger.error("proof_elaboration_artifact rejected reason=%s", reason)
    raise ValueError(reason)


def _source_digest(source: bytes) -> str:
    logger.debug("proof_elaboration_artifact._source_digest entry bytes=%d", len(source))
    if type(source) is not bytes:
        raise TypeError("elaboration-source-must-be-bytes")
    result = sha256(SOURCE_DOMAIN + source).hexdigest()
    logger.debug("proof_elaboration_artifact._source_digest exit result=%s", result)
    return result


def _body(artifact: ProofElaborationArtifact) -> dict[str, object]:
    logger.debug("proof_elaboration_artifact._body entry theorem=%s", artifact.theorem_id)
    result = {
        "schema": artifact.schema,
        "surface_schema": artifact.surface_schema,
        "theorem": artifact.theorem_id,
        "source_digest": artifact.source_digest,
        "source_size": artifact.source_size,
        "surface_ast": artifact.canonical_surface_ast,
        "surface_syntax_digest": artifact.surface_syntax_digest,
        "semantic_digest": artifact.semantic_digest,
        "statement": artifact.elaborated_statement,
        "r7_artifact": artifact.r7_artifact,
        "r7_artifact_digest": artifact.r7_artifact_digest,
        "rules": list(artifact.rule_closure),
        "native_laws": list(artifact.native_law_closure),
        "support": [
            [category, list(items)]
            for category, items in artifact.dependency_support
        ],
        "r9_tcb_schema": artifact.r9_tcb_schema,
        "r9_theorems": list(artifact.r9_theorem_ids),
        "r9_sources": [list(item) for item in artifact.r9_source_digests],
        "r9_binding": artifact.r9_binding_digest,
        "toolchain": artifact.toolchain,
        "boundary": artifact.boundary,
    }
    logger.debug("proof_elaboration_artifact._body exit fields=%d", len(result))
    return result


def _checked_r9(report: object) -> IntrinsicModeBridgeReport:
    logger.debug("proof_elaboration_artifact._checked_r9 entry type=%s", type(report).__name__)
    if (
        type(report) is not IntrinsicModeBridgeReport
        or not verify_intrinsic_mode_bridge_report(report)
        or report.status != "checked"
        or not report.r7_artifact_checked
        or not report.manifest_checked
        or not report.source_bound
        or not report.lean_checked
    ):
        _reject("elaboration-r9-bridge-rejected")
    logger.debug("proof_elaboration_artifact._checked_r9 exit binding=%s", report.binding_digest)
    return report


def make_elaboration_artifact(
    theorem_id: str,
    surface_schema: str,
    source: bytes,
    surface_ast_data: object,
    declared_statement: CoreProp,
    proof: ProofTerm,
    *,
    r9_report: IntrinsicModeBridgeReport | None = None,
) -> ProofElaborationArtifact:
    """Check a closed proof and bind every supplied and inferred representation."""
    logger.debug(
        "make_elaboration_artifact entry theorem=%r surface_schema=%r",
        theorem_id,
        surface_schema,
    )
    if type(theorem_id) is not str or not theorem_id:
        _reject("invalid-elaboration-theorem-id")
    if type(surface_schema) is not str or not surface_schema:
        _reject("invalid-elaboration-surface-schema")
    source_digest = _source_digest(source)
    canonical_surface = canonical_json(surface_ast_data)
    syntax_digest = digest_data(surface_ast_data, SURFACE_DOMAIN)
    context = ProofContext()
    judgment = infer_proof(context, proof)
    if judgment.conclusion != declared_statement:
        _reject("declared-inferred-statement-mismatch")
    r7_artifact = make_proof_artifact(theorem_id, context, proof)
    semantic_artifact = make_proof_artifact(SURFACE_LANGUAGE_ID, context, proof)
    if not verify_proof_artifact(r7_artifact).ok:
        _reject("elaborated-r7-artifact-rejected")
    report = _checked_r9(intrinsic_mode_bridge_report() if r9_report is None else r9_report)
    support = image_composition_support(proof) | prop_support(declared_statement)
    seed = ProofElaborationArtifact(
        SCHEMA,
        surface_schema,
        theorem_id,
        source_digest,
        len(source),
        canonical_surface,
        syntax_digest,
        semantic_artifact.proof_digest,
        canonical_json(prop_data(declared_statement)),
        artifact_json(r7_artifact),
        r7_artifact.proof_digest,
        tuple(item.value for item in judgment.rule_closure),
        tuple(item.value for item in judgment.native_law_closure),
        support_by_category(frozenset(support)),
        R9_TCB_SCHEMA,
        report.theorem_ids,
        report.source_digests,
        report.binding_digest,
        report.toolchain,
        BOUNDARY,
        "",
    )
    result = replace(seed, binding_digest=digest_data(_body(seed), BINDING_DOMAIN))
    logger.debug("make_elaboration_artifact exit binding=%s", result.binding_digest)
    return result


def make_surface_elaboration_artifact(
    theorem_id: str,
    source: bytes,
    elaborated: ElaboratedProgram,
    *,
    r9_report: IntrinsicModeBridgeReport | None = None,
) -> ProofElaborationArtifact:
    """Reparse a stable surface program before binding it to generic R7/R9 evidence."""
    logger.debug("make_surface_elaboration_artifact entry theorem=%r", theorem_id)
    if type(elaborated) is not ElaboratedProgram:
        raise TypeError("invalid-elaborated-program")
    if type(source) is not bytes:
        raise TypeError("elaboration-source-must-be-bytes")
    try:
        text = source.decode("ascii")
    except UnicodeDecodeError:
        _reject("elaboration-source-not-ascii")
    replayed = compile_surface_program(text)
    if replayed != elaborated:
        _reject("surface-elaboration-replay-mismatch")
    if elaborated.syntax_digest != surface_syntax_digest(elaborated.surface):
        _reject("surface-syntax-digest-mismatch")
    if elaborated.semantic_digest != elaborated.artifact.proof_digest:
        _reject("surface-semantic-digest-mismatch")
    result = make_elaboration_artifact(
        theorem_id,
        SURFACE_LANGUAGE_ID,
        source,
        surface_program_data(elaborated.surface),
        elaborated.claim,
        elaborated.proof,
        r9_report=r9_report,
    )
    if result.surface_syntax_digest != elaborated.syntax_digest:
        _reject("artifact-surface-syntax-digest-mismatch")
    if result.semantic_digest != elaborated.semantic_digest:
        _reject("artifact-semantic-digest-mismatch")
    logger.debug("make_surface_elaboration_artifact exit binding=%s", result.binding_digest)
    return result


def elaboration_artifact_json(artifact: ProofElaborationArtifact) -> str:
    """Serialize the composite artifact canonically."""
    logger.debug("elaboration_artifact_json entry theorem=%s", artifact.theorem_id)
    if type(artifact) is not ProofElaborationArtifact:
        raise TypeError("invalid-elaboration-artifact-type")
    result = canonical_json({**_body(artifact), "binding_digest": artifact.binding_digest})
    logger.debug("elaboration_artifact_json exit bytes=%d", len(result.encode()))
    return result


def verify_elaboration_artifact(
    artifact: object,
    source: bytes,
    surface_ast_data: object,
    declared_statement: CoreProp,
    proof: ProofTerm,
) -> ElaborationArtifactCheck:
    """Rebuild from all origins and reject any source, AST, proof, or trust drift."""
    logger.debug("verify_elaboration_artifact entry type=%s", type(artifact).__name__)
    errors: list[str] = []
    try:
        if type(artifact) is not ProofElaborationArtifact:
            _reject("invalid-elaboration-artifact-type")
        rebuilt = make_elaboration_artifact(
            artifact.theorem_id,
            artifact.surface_schema,
            source,
            surface_ast_data,
            declared_statement,
            proof,
        )
        if artifact != rebuilt:
            _reject("elaboration-artifact-replay-mismatch")
        if artifact.binding_digest != digest_data(_body(artifact), BINDING_DOMAIN):
            _reject("forged-elaboration-binding")
        decoded = json.loads(artifact.r7_artifact)
        if canonical_json(decoded) != artifact.r7_artifact:
            _reject("noncanonical-embedded-r7-artifact")
    except (
        AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError,
        ProofKernelError, RecursionError,
    ) as exc:
        logger.error("verify_elaboration_artifact blocked error=%s", exc)
        errors.append(str(exc))
    result = ElaborationArtifactCheck(not errors, tuple(errors))
    logger.debug("verify_elaboration_artifact exit ok=%s errors=%r", result.ok, result.errors)
    return result
