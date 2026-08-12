"""Fail-fast hostile-safe P1-C4 result revalidation."""

from __future__ import annotations

import logging

from .scoped_formation_codec import (
    ScopedFormationValidationError, bounded_int, canonical_bytes, hex_digest,
    identifier,
)
from .scoped_formation_components import expected_component_keys
from .scoped_formation_g4 import g4_response_check_count
from .observer_patch_validation import LocalObserverSection
from .construction.finite_builder.validation import _snapshot_target_stage
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import OntologyStage
from .scoped_formation_preflight import snapshot_formation_request
from .scoped_formation_result_bindings import validate_result_bindings
from .scoped_formation_runtime import scoped_formation_judgment
from .scoped_formation_types import (
    BoundG4BridgeJudgment, FiniteScopedObjectPresentation, G4ContradictionRow,
    FormationComponentRow, G4ResponseRow, ScopedFormationJudgment,
    ScopedFormationResourceLimit, SCOPED_FORMATION_NONCLAIMS,
    FormationFailedBound, FormationLimitSource,
    ScopedFormationStatus,
)

logger = logging.getLogger(__name__)


def _reject(message: str, exc: Exception | None = None):
    """Log every hostile-result rejection before raising the typed error."""
    logger.error("scoped formation result rejected: %s", message)
    if exc is None:
        raise ScopedFormationValidationError(message)
    raise ScopedFormationValidationError(message) from exc


def validate_scoped_formation_result(raw_rule_source, raw_scope, value):
    """Recompute from raw sources after exact shallow variant and length gates."""
    logger.debug("validate_scoped_formation_result entry")
    request = snapshot_formation_request(raw_rule_source, raw_scope)
    expected_keys = expected_component_keys(request.scope)
    _shallow_result(value, request, expected_keys)
    expected = scoped_formation_judgment(request.rule, request.scope)
    _compare_result(value, expected)
    logger.debug("validate_scoped_formation_result exit type=%s", type(expected).__name__)
    return expected


def _shallow_result(value, request, expected_keys: tuple[tuple[str, str], ...]) -> None:
    """Reject wrong variants, scalar transplants, and huge rows before traversal."""
    logger.debug("_shallow_result entry type=%s", type(value).__name__)
    validate_result_bindings(value, request, expected_keys)
    common = (
        request.rule.source_digest, request.scope.scope_digest,
        request.scope.policy.policy_digest, request.run_digest,
    )
    if type(value) is ScopedFormationResourceLimit:
        try:
            supplied = (value.rule_source_digest, value.scope_digest, value.policy_digest, value.run_digest)
            sources, required, allowed = value.source_digests, value.required_value, value.allowed_value
        except AttributeError as exc:
            _reject("formation-limit-missing-fields", exc)
        if supplied != common or type(sources) is not tuple or len(sources) != len(request.source_digests):
            _reject("formation-limit-source-drift")
        bounded_int(required, "formation-limit-required", 0, 4 * 1024 * 1024)
        bounded_int(allowed, "formation-limit-allowed", 0, 4 * 1024 * 1024)
        if any(type(x) is not str or len(x) != 64 for x in sources):
            _reject("formation-limit-digest-vector-drift")
        for item in sources:
            hex_digest(item, "formation-limit-source-digest")
        if (
            type(value.failed_bound) is not FormationFailedBound
            or type(value.limit_source) is not FormationLimitSource
            or type(value.status) is not str or value.status != "resource-limit"
            or not _exact_nonclaims(value.nonclaims)
        ):
            _reject("formation-limit-scalar-drift")
        cap = 16_384 if value.failed_bound is FormationFailedBound.CHECKS else 4 * 1024 * 1024
        bounded_int(required, "formation-limit-bound-required", 0, cap)
        bounded_int(allowed, "formation-limit-bound-allowed", 0, cap)
        hex_digest(value.refusal_digest, "formation-refusal-digest")
    elif type(value) is ScopedFormationJudgment:
        try:
            supplied = (value.rule_source_digest, value.scope_digest, value.policy_digest, value.run_digest)
            rows, keys, sources = value.component_rows, value.expected_component_keys, value.source_digests
            presentation, status = value.presentation, value.status
        except AttributeError as exc:
            _reject("formation-judgment-missing-fields", exc)
        if supplied != common or type(rows) is not tuple or len(rows) != len(expected_keys):
            _reject("formation-judgment-shallow-drift")
        charged = bounded_int(value.charged_checks, "formation-charged-checks", 0, 16_384)
        encoded = bounded_int(value.canonical_bytes, "formation-canonical-bytes", 0, 4 * 1024 * 1024)
        if charged != request.checks or encoded != request.encoded_bytes:
            _reject("formation-judgment-resource-accounting-drift")
        if type(keys) is not tuple or len(keys) != len(expected_keys) or type(sources) is not tuple or len(sources) != len(request.source_digests):
            _reject("formation-judgment-catalog-length-drift")
        if type(status) is not ScopedFormationStatus:
            _reject("formation-judgment-status-drift")
        if (status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE) != (type(presentation) is FiniteScopedObjectPresentation):
            _reject("formation-presentation-presence-drift")
        if type(value.g4) is not BoundG4BridgeJudgment:
            _reject("formation-g4-result-type-drift")
        if any(type(x) is not str or len(x) != 64 for x in sources):
            _reject("formation-source-digest-vector-drift")
        for item in sources:
            hex_digest(item, "formation-source-digest")
        if not _exact_nonclaims(value.nonclaims):
            _reject("formation-nonclaims-drift")
        hex_digest(value.judgment_digest, "formation-judgment-digest")
        hex_digest(value.target_commitment, "formation-target-commitment")
        if type(value.first_obstruction) is not str or len(value.first_obstruction.encode()) > 256:
            _reject("formation-first-obstruction-drift")
        if presentation is not None:
            _shallow_presentation(presentation, request)
        _shallow_g4(value.g4, request)
        _shallow_rows(rows, expected_keys)
    else:
        _reject("unknown-scoped-formation-result-variant")
    logger.debug("_shallow_result exit")


def _shallow_rows(rows: tuple, expected_keys: tuple[tuple[str, str], ...]) -> None:
    """Check exact row DTOs and key scalars without hashing nested contents."""
    logger.debug("_shallow_rows entry rows=%d", len(rows))
    for row, key in zip(rows, expected_keys, strict=True):
        if type(row) is not FormationComponentRow:
            _reject("formation-component-row-must-be-exact")
        try:
            actual = row.component, row.key
        except AttributeError as exc:
            _reject("formation-component-row-missing-fields", exc)
        if actual != key or type(row.status) is not ScopedFormationStatus:
            _reject("formation-component-row-key-drift")
        identifier(row.component, "component-name")
        identifier(row.key, "component-key")
        hex_digest(row.evidence_digest, "component-evidence-digest")
        hex_digest(row.row_digest, "component-row-digest")
        if type(row.obstruction) is not str or len(row.obstruction.encode()) > 256:
            _reject("formation-component-obstruction-drift")
    logger.debug("_shallow_rows exit")


def _shallow_g4(value: BoundG4BridgeJudgment, request) -> None:
    """Bound hostile G4 row/section/contradiction containers before encoding."""
    logger.debug("_shallow_g4 entry")
    try:
        rows = value.response_rows
        patch_keys = value.expected_patch_keys
        response_keys = value.expected_response_keys
        derived_sections = value.sections
        sections = value.section_digests
        contradictions = value.contradiction_rows
        first = value.first_contradiction
    except AttributeError as exc:
        _reject("formation-g4-result-missing-fields", exc)
    expected_rows = g4_response_check_count(request.scope.g4_bridge)
    max_contradictions = sum(
        len(x.expected_nodes) * (len(x.expected_nodes) - 1) // 2
        for x in request.scope.g4_bridge.patch_requirements
    )
    if type(value.status) is not ScopedFormationStatus:
        _reject("formation-g4-status-drift")
    if type(value.first_obstruction) is not str or len(value.first_obstruction.encode()) > 256:
        _reject("formation-g4-obstruction-drift")
    for item in (
        value.doctrine_fingerprint, value.diagram_digest, value.bridge_digest,
        value.criterion_digest, value.trace_digest, value.run_digest,
        value.judgment_digest,
    ):
        hex_digest(item, "formation-g4-digest")
    expected_patches = tuple(x.name for x in request.scope.g4_bridge.atlas.patches)
    if (
        type(patch_keys) is not tuple or len(patch_keys) != len(expected_patches)
        or any(type(x) is not str for x in patch_keys)
        or tuple(patch_keys) != expected_patches
    ):
        _reject("formation-g4-patch-key-drift")
    if type(response_keys) is not tuple or len(response_keys) != expected_rows:
        _reject("formation-g4-response-key-length-drift")
    for item in response_keys:
        if type(item) is not tuple or len(item) != 4 or any(type(x) is not str for x in item):
            _reject("formation-g4-response-key-drift")
        for field in item:
            identifier(field, "g4-response-key-field")
    if type(rows) is not tuple or len(rows) != expected_rows:
        _reject("formation-g4-response-length-drift")
    patch_count = len(request.scope.g4_bridge.atlas.patches)
    if type(derived_sections) is not tuple or len(derived_sections) != patch_count:
        _reject("formation-g4-derived-section-length-drift")
    if type(sections) is not tuple or len(sections) != patch_count:
        _reject("formation-g4-section-length-drift")
    if type(contradictions) is not tuple or len(contradictions) > max_contradictions:
        _reject("formation-g4-contradiction-length-drift")
    for row in rows:
        if type(row) is not G4ResponseRow or type(row.status) is not ScopedFormationStatus:
            _reject("formation-g4-response-row-drift")
        for item in (row.patch_id, row.observer_id, row.left_node, row.right_node, row.outcome):
            identifier(item, "g4-response-field")
        for item in (row.left_payload_digest, row.right_payload_digest, row.row_digest):
            hex_digest(item, "g4-response-digest")
    for item in sections:
        hex_digest(item, "g4-section-digest")
    for item in derived_sections:
        if type(item) is not LocalObserverSection:
            _reject("formation-g4-derived-section-type-drift")
        identifier(item.patch_name, "g4-derived-section-patch")
        if type(item.blocks) is not tuple or not item.blocks or len(item.blocks) > 128:
            _reject("formation-g4-derived-section-blocks-drift")
        flat = []
        for block in item.blocks:
            if type(block) is not tuple or not block or len(block) > 128:
                _reject("formation-g4-derived-section-block-drift")
            flat.extend(identifier(x, "g4-derived-section-node") for x in block)
        if len(flat) > 128 or len(set(flat)) != len(flat):
            _reject("formation-g4-derived-section-node-drift")
    for item in contradictions:
        if type(item) is not G4ContradictionRow:
            _reject("formation-g4-contradiction-row-drift")
        for field in (item.patch_id, item.left_node, item.right_node):
            identifier(field, "g4-contradiction-field")
        hex_digest(item.contradiction_digest, "g4-contradiction-digest")
    if first is not None and type(first) is not G4ContradictionRow:
        _reject("formation-g4-first-contradiction-type-drift")
    if (first is None) != (not contradictions) or (
        first is not None and first != contradictions[0]
    ):
        _reject("formation-g4-first-contradiction-order-drift")
    if first is not None and (
        value.status is not ScopedFormationStatus.REFUTED
        or value.first_obstruction != first.contradiction_digest
    ):
        _reject("formation-g4-first-contradiction-obstruction-drift")
    logger.debug("_shallow_g4 exit")


def _shallow_presentation(value: FiniteScopedObjectPresentation, request) -> None:
    """Bound and validate the positive presentation shell before encoding."""
    logger.debug("_shallow_presentation entry")
    identifier(value.presentation_id, "presentation-id")
    identifier(value.target_stage_id, "presentation-target-stage-id")
    if type(value.status) is not ScopedFormationStatus or value.status is not ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE:
        _reject("formation-presentation-status-drift")
    if type(value.target_stage) is not OntologyStage:
        _reject("formation-presentation-target-type-drift")
    target = _snapshot_target_stage(value.target_stage, request.scope.doctrine)
    if target.stage_id != request.scope.target.stage_id or stage_commitment(target) != request.scope.expected_target_commitment:
        _reject("formation-presentation-target-drift")
    digests = (
        value.target_commitment, value.doctrine_fingerprint,
        value.rule_source_digest, value.scope_digest, value.construction_digest,
        value.support_digest, value.persistence_digest, value.g4_digest,
        value.confluence_digest, value.refinement_digest, value.survival_digest,
        value.component_order_digest, value.presentation_digest,
    )
    for item in digests:
        hex_digest(item, "formation-presentation-digest")
    logger.debug("_shallow_presentation exit")


def _exact_nonclaims(value: object) -> bool:
    """Compare the bounded permanent nonclaim tuple without hostile equality."""
    logger.debug("_exact_nonclaims entry")
    result = (
        type(value) is tuple
        and len(value) == len(SCOPED_FORMATION_NONCLAIMS)
        and all(type(x) is str and len(x.encode()) <= 128 for x in value)
        and tuple(value) == SCOPED_FORMATION_NONCLAIMS
    )
    logger.debug("_exact_nonclaims exit result=%s", result)
    return result


def _compare_result(supplied, expected) -> None:
    """Compare fully bounded exact immutable results after fresh replay."""
    logger.debug("_compare_result entry")
    try:
        supplied_bytes = canonical_bytes(supplied)
        expected_bytes = canonical_bytes(expected)
    except ScopedFormationValidationError:
        logger.error("_compare_result noncanonical nested value")
        raise
    if len(supplied_bytes) > 4 * 1024 * 1024:
        _reject("scoped-formation-result-byte-limit")
    if type(supplied) is not type(expected) or supplied_bytes != expected_bytes:
        logger.error("_compare_result mismatch")
        _reject("scoped-formation-result-drift")
    logger.debug("_compare_result exit")
