"""Atomic complete raw-source preflight for P1-C4."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .confluence_aggregate_digest import catalog_canonical_bytes
from .confluence_aggregate_preflight import total_catalog_charge
from .observer_relation_preflight import encoded_request_bytes, request_cost, snapshot_request
from .construction.finite_builder.codec import _decode_builder
from .finite_builder_validation import _builder_shape
from .scoped_formation_codec import ScopedFormationValidationError, canonical_bytes, digest
from .scoped_formation_g4 import g4_response_check_count
from .scoped_formation_scope import snapshot_formation_scope
from .scoped_formation_sources import snapshot_rule_source
from .scoped_formation_types import (
    FiniteScopedFormationRuleSource, FormationFailedBound, FormationLimitSource,
    FormationScope, ScopedFormationResourceLimit, SurvivalMode,
)
from .translated_confluence_preflight import snapshot_translated_request

logger = logging.getLogger(__name__)
HARD_CHECKS = 16_384
HARD_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class FormationRequest:
    rule: FiniteScopedFormationRuleSource
    scope: FormationScope
    checks: int
    encoded_bytes: int
    source_digests: tuple[str, ...]
    run_digest: str
    nested_limits: tuple[tuple[FormationFailedBound, FormationLimitSource, int, int], ...]


def snapshot_formation_request(raw_rule, raw_scope) -> FormationRequest:
    """Capture and charge every nested raw request before any observation."""
    logger.debug("snapshot_formation_request entry")
    if type(raw_scope) is not FormationScope:
        logger.error("snapshot_formation_request scope type rejected")
        raise ScopedFormationValidationError("formation-scope-must-be-exact")
    rule = snapshot_rule_source(raw_rule, raw_scope.doctrine)
    scope = snapshot_formation_scope(rule, raw_scope)
    encoded = len(canonical_bytes((rule, scope)))
    if encoded > HARD_BYTES:
        logger.error("snapshot_formation_request hard byte limit")
        raise ScopedFormationValidationError("formation-hard-byte-limit")
    checks, nested = _charges_and_nested(scope)
    if checks > HARD_CHECKS:
        logger.error("snapshot_formation_request hard check limit")
        raise ScopedFormationValidationError("formation-hard-check-limit")
    sources = _source_digests(scope)
    run = digest("c4.run", rule.source_digest, scope.scope_digest, scope.policy.policy_digest, sources, checks, encoded)
    result = FormationRequest(rule, scope, checks, encoded, sources, run, nested)
    logger.debug("snapshot_formation_request exit checks=%d bytes=%d", checks, encoded)
    return result


def formation_preflight(request: FormationRequest) -> ScopedFormationResourceLimit | None:
    """Refuse bytes before checks across outer and transparent nested policies."""
    logger.debug("formation_preflight entry")
    failures = (
        (FormationFailedBound.BYTES, FormationLimitSource.OUTER, request.encoded_bytes, request.scope.policy.max_bytes),
        *(x for x in request.nested_limits if x[0] is FormationFailedBound.BYTES),
        (FormationFailedBound.CHECKS, FormationLimitSource.OUTER, request.checks, request.scope.policy.max_checks),
        *(x for x in request.nested_limits if x[0] is FormationFailedBound.CHECKS),
    )
    failed = next((x for x in failures if x[2] > x[3]), None)
    if failed is None:
        logger.debug("formation_preflight exit admitted")
        return None
    bound, source, required, allowed = failed
    refusal = digest("c4.resource-limit", request.rule.source_digest, request.scope.scope_digest, request.run_digest, bound, source, required, allowed)
    result = ScopedFormationResourceLimit(
        request.rule.source_digest, request.scope.scope_digest,
        request.scope.policy.policy_digest, request.run_digest,
        request.source_digests, bound, source, required, allowed, refusal,
    )
    logger.debug("formation_preflight exit bound=%s source=%s", bound.value, source.value)
    return result


def _charges_and_nested(scope: FormationScope) -> tuple[int, tuple[tuple[FormationFailedBound, FormationLimitSource, int, int], ...]]:
    """Compute the exact component sum and every reachable nested limit."""
    logger.debug("_charges_and_nested entry")
    path_map = {x.path_id: x for x in scope.diagram.paths}
    checks = _builder_shape(
        _decode_builder(scope.construction_source.program.canonical)
    )[2]
    checks += sum(len(path_map[x.path_id].edge_ids) for x in scope.persistence)
    c2_checks = total_catalog_charge(scope.doctrine, scope.diagram, scope.c2_catalog)
    c2_bytes = len(catalog_canonical_bytes(scope.c2_catalog))
    checks += c2_checks + len(scope.support_observer_ids) + g4_response_check_count(scope.g4_bridge)
    limits: list[tuple[FormationFailedBound, FormationLimitSource, int, int]] = [
        (FormationFailedBound.BYTES, FormationLimitSource.NESTED_C2, c2_bytes, scope.c2_catalog.policy.max_bytes),
        (FormationFailedBound.CHECKS, FormationLimitSource.NESTED_C2, c2_checks, scope.c2_catalog.policy.max_checks),
    ]
    for requirement in scope.refinements:
        a2_request = snapshot_request(
            requirement.a2_doctrine, requirement.a2_observer_source,
            requirement.a2_stage_source, requirement.relation_scope,
            requirement.morphism, None, requirement.relation_policy,
        )[1]
        a2_checks, a2_bytes = request_cost(a2_request), encoded_request_bytes(a2_request)
        checks += a2_checks
        limits.extend((
            (FormationFailedBound.BYTES, FormationLimitSource.NESTED_A2, a2_bytes, requirement.relation_policy.max_encoded_bytes),
            (FormationFailedBound.CHECKS, FormationLimitSource.NESTED_A2, a2_checks, requirement.relation_policy.max_cost),
        ))
        if requirement.survival_mode is SurvivalMode.DIRECT:
            checks += sum(len(path_map[x].edge_ids) for x in requirement.path_ids)
        else:
            translated = snapshot_translated_request(
                scope.doctrine, scope.diagram, requirement.translated_plan,
                requirement.a2_doctrine, requirement.a2_observer_source,
                requirement.a2_stage_source, requirement.translated_bridge,
                requirement.translated_spec, requirement.translated_policy,
            )
            # Runtime performs the C4 A2 replay above and C3 performs its own A2 replay.
            checks += translated.required_checks
            limits.extend((
                (FormationFailedBound.BYTES, FormationLimitSource.NESTED_C3, translated.required_bytes, translated.policy.max_bytes),
                (FormationFailedBound.BYTES, FormationLimitSource.NESTED_A2, translated.a2_required_bytes, translated.spec.relation_policy.max_encoded_bytes),
                (FormationFailedBound.CHECKS, FormationLimitSource.NESTED_C3, translated.required_checks, translated.policy.max_checks),
                (FormationFailedBound.CHECKS, FormationLimitSource.NESTED_A2, translated.a2_required_checks, translated.spec.relation_policy.max_cost),
            ))
    result = checks, tuple(limits)
    logger.debug("_charges_and_nested exit checks=%d limits=%d", checks, len(limits))
    return result


def _source_digests(scope: FormationScope) -> tuple[str, ...]:
    """Expose the complete bounded source identity vector in fixed order."""
    logger.debug("_source_digests entry")
    result = (
        scope.construction_source.membership_digest, scope.expected_target_commitment,
        scope.diagram.source_digest, scope.c2_catalog.catalog_digest,
        scope.g4_bridge.bridge_digest,
        *(x.requirement_digest for x in scope.persistence),
        *(x.requirement_digest for x in scope.refinements),
    )
    logger.debug("_source_digests exit count=%d", len(result))
    return result
