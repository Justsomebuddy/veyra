"""Pre-replay exact source-binding shell for hostile C4 results."""

from __future__ import annotations

import logging

from .codec import ScopedFormationValidationError
from .g4 import expected_g4_response_keys
from .types import (
    BoundG4BridgeJudgment, FiniteScopedObjectPresentation, FormationComponentRow,
    G4ResponseRow, ScopedFormationJudgment, ScopedFormationResourceLimit,
)

logger = logging.getLogger(__name__)


def _reject(reason: str) -> None:
    """Reject before result encoding or semantic replay."""
    logger.error("scoped formation result binding rejected: %s", reason)
    raise ScopedFormationValidationError(reason)


def _exact_text(value: object, expected: str, reason: str) -> None:
    """Type-check before comparing one exact text binding."""
    logger.debug("_exact_text entry reason=%s", reason)
    if type(value) is not str or value != expected:
        _reject(reason)
    logger.debug("_exact_text exit reason=%s", reason)


def _exact_text_tuple(value: object, expected: tuple[str, ...], reason: str) -> None:
    """Type-check a complete string vector before exact equality."""
    logger.debug("_exact_text_tuple entry reason=%s", reason)
    if type(value) is not tuple or len(value) != len(expected):
        _reject(reason)
    if any(type(item) is not str for item in value) or value != expected:
        _reject(reason)
    logger.debug("_exact_text_tuple exit reason=%s", reason)


def _exact_key_catalog(value: object, expected: tuple[tuple[str, ...], ...], reason: str) -> None:
    """Type-check nested ordered key tuples before exact equality."""
    logger.debug("_exact_key_catalog entry reason=%s", reason)
    if type(value) is not tuple or len(value) != len(expected):
        _reject(reason)
    for item, wanted in zip(value, expected, strict=True):
        if type(item) is not tuple or len(item) != len(wanted):
            _reject(reason)
        if any(type(field) is not str for field in item) or item != wanted:
            _reject(reason)
    logger.debug("_exact_key_catalog exit reason=%s", reason)


def _validate_g4(value: object, request) -> None:
    """Bind the exact doctrine, diagram, bridge, and response-key catalog."""
    logger.debug("_validate_g4 entry")
    if type(value) is not BoundG4BridgeJudgment:
        _reject("formation-g4-result-type-drift")
    bridge = request.scope.g4_bridge
    _exact_text(value.doctrine_fingerprint, request.scope.doctrine.fingerprint, "formation-g4-doctrine-transplant")
    _exact_text(value.diagram_digest, request.scope.diagram.source_digest, "formation-g4-diagram-transplant")
    _exact_text(value.bridge_digest, bridge.bridge_digest, "formation-g4-bridge-transplant")
    patches = tuple(patch.name for patch in bridge.atlas.patches)
    _exact_text_tuple(value.expected_patch_keys, patches, "formation-g4-patch-catalog-transplant")
    expected = expected_g4_response_keys(bridge)
    _exact_key_catalog(value.expected_response_keys, expected, "formation-g4-response-catalog-transplant")
    if type(value.response_rows) is not tuple or len(value.response_rows) != len(expected):
        _reject("formation-g4-response-row-catalog-transplant")
    for row, key in zip(value.response_rows, expected, strict=True):
        if type(row) is not G4ResponseRow:
            _reject("formation-g4-response-row-catalog-transplant")
        actual = (row.patch_id, row.observer_id, row.left_node, row.right_node)
        if any(type(item) is not str for item in actual) or actual != key:
            _reject("formation-g4-response-row-catalog-transplant")
    logger.debug("_validate_g4 exit")


def _validate_presentation(value: object, request) -> None:
    """Bind every positive presentation source identity before target traversal."""
    logger.debug("_validate_presentation entry")
    if type(value) is not FiniteScopedObjectPresentation:
        _reject("formation-presentation-type-transplant")
    scope = request.scope
    _exact_text(value.presentation_id, scope.presentation_id, "formation-presentation-id-transplant")
    _exact_text(value.target_stage_id, scope.expected_target_stage_id, "formation-presentation-stage-transplant")
    _exact_text(value.target_commitment, scope.expected_target_commitment, "formation-presentation-target-transplant")
    _exact_text(value.doctrine_fingerprint, scope.doctrine.fingerprint, "formation-presentation-doctrine-transplant")
    _exact_text(value.rule_source_digest, request.rule.source_digest, "formation-presentation-rule-transplant")
    _exact_text(value.scope_digest, scope.scope_digest, "formation-presentation-scope-transplant")
    logger.debug("_validate_presentation exit")


def validate_result_bindings(value: object, request, expected_keys) -> None:
    """Reject five transplant classes before canonical result encoding/observation."""
    logger.debug("validate_result_bindings entry type=%s", type(value).__name__)
    if type(value) not in {ScopedFormationJudgment, ScopedFormationResourceLimit}:
        _reject("unknown-scoped-formation-result-variant")
    _exact_text(value.rule_source_digest, request.rule.source_digest, "formation-rule-transplant")
    _exact_text(value.scope_digest, request.scope.scope_digest, "formation-scope-transplant")
    _exact_text(value.policy_digest, request.scope.policy.policy_digest, "formation-policy-transplant")
    _exact_text(value.run_digest, request.run_digest, "formation-run-transplant")
    _exact_text_tuple(value.source_digests, request.source_digests, "formation-source-vector-transplant")
    if type(value) is ScopedFormationJudgment:
        _exact_text(value.target_commitment, request.scope.expected_target_commitment, "formation-target-transplant")
        _exact_key_catalog(value.expected_component_keys, expected_keys, "formation-component-catalog-transplant")
        if type(value.component_rows) is not tuple or len(value.component_rows) != len(expected_keys):
            _reject("formation-component-row-catalog-transplant")
        for row, key in zip(value.component_rows, expected_keys, strict=True):
            if type(row) is not FormationComponentRow:
                _reject("formation-component-row-catalog-transplant")
            actual = row.component, row.key
            if any(type(item) is not str for item in actual) or actual != key:
                _reject("formation-component-row-catalog-transplant")
        _validate_g4(value.g4, request)
        if value.presentation is not None:
            _validate_presentation(value.presentation, request)
    logger.debug("validate_result_bindings exit")
