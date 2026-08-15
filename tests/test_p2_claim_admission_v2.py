"""Positive, compatibility, and boundary tests for P2 claim admission v2."""

from __future__ import annotations

from dataclasses import replace
import inspect
import logging

import pytest

import src.core as core
from src.core.claim_composition import (
    COMPOSITION_PREMISE_KIND,
    build_composition_p2_premise,
    canonical_composition_sources,
)
from src.core.p2_claim_admission_v2 import (
    EVIDENCE_FIELDS,
    EXTENSION_ORACLE_DIGEST,
    JUDGMENT_SCHEMA,
    PERMANENT_NONCLAIMS,
    PREMISE_KIND,
    REGISTRY_DIGEST,
    RULE_ID,
    SCHEMA_AUDIT_NONCLAIMS_V2,
    SCHEMA_AUDIT_SCOPE_V2,
    SourceValidationAuthority,
    VISIBLE_INDICES,
    audit_registry_v2_against_literal_oracle,
    build_composition_presentation_premise,
    build_licensed_composition_presentation,
    build_presentation_schema_audit_report_v2,
    licensed_composition_presentation_from_json,
    licensed_composition_presentation_json,
    promotion_registry_v2,
    validate_composition_presentation_premise,
    validate_licensed_composition_presentation,
    validate_presentation_schema_audit,
    validate_presentation_schema_audit_report_v2,
    validate_registry_v2,
)
from src.core.status_promotion import (
    EvidenceStatus,
    JudgmentKind,
    PositiveProvenance,
    audit_promotion_request,
    audit_allowlisted_schemas,
    audit_registry_against_literal_oracle,
    claim_descriptor,
    promotion_audit_request,
    promotion_policy,
    promotion_registry,
)
from src.core.status_promotion_common import StatusPromotionValidationError
from src.core.status_promotion_oracle import LITERAL_ORACLE_DIGEST
from src.core.status_promotion_types import MetaAuditDecision, MetaOntologicalStatus

from p2_claim_admission_v2_fixture import composition_case, native_and_detached_case

logger = logging.getLogger(__name__)


def test_v1_registry_oracle_and_composition_bytes_remain_exact() -> None:
    """The sibling changes no v1 registry row, digest, oracle, or premise kind."""
    logger.debug("test_v1_registry_oracle_and_composition_bytes_remain_exact entry")
    registry = promotion_registry()
    assert registry.version == "p2-s-promotion-registry-v1"
    assert registry.registry_digest == "375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d"
    assert len(registry.rules) == 17
    assert len(registry.premise_projections) == 40
    assert audit_registry_against_literal_oracle(registry) == LITERAL_ORACLE_DIGEST
    assert COMPOSITION_PREMISE_KIND == "claim-composition-receipt"
    assert all(rule.rule_id != RULE_ID for rule in registry.rules)
    sources, target, license, receipt = composition_case()
    old_premise = build_composition_p2_premise(receipt, sources, target, license)
    assert tuple(item.receipt.receipt_digest for item in sources) == (
        "0a944ae6a7cc2b65564b12f739ed53de65a3e2ed171977e4bd65bd4d68be3211",
        "a7d1e3d4b72d64e9452606c46920ac2d8ea2573a87355dcfc85d2d265e5dde99",
    )
    assert target.contract_digest == "395cc6507683184e142c7e7f70d71257941a4052f4e4ee8b4f11a95e4803c4b5"
    assert license.license_digest == "87a9cfd9bd5e12197c1933a1fac2063d0bd52baf79f2cd6023a9d67e2f60897a"
    assert receipt.assessment_digest == "d7f4feb48382d4528a50b874bc2ff8198a84f8868b955868fbea12621e5213f1"
    assert receipt.receipt_digest == "2327bc0453574cc09a287d28b45c263117e2670a27a8059f0338211113dc6b7f"
    assert old_premise.artifact_digest == receipt.receipt_digest
    assert tuple(item.name for item in old_premise.evidence_fields) == (
        "target-contract",
        "composition-license",
        "composition-assessment",
        "source-family",
        "nonpromotion",
    )
    assert not hasattr(core, "build_licensed_composition_presentation")
    logger.debug("test_v1_registry_oracle_and_composition_bytes_remain_exact exit")


def test_registry_v2_is_exact_additive_snapshot_with_independent_oracle() -> None:
    """The v2 snapshot is the exact v1 prefix plus one literal rule/projection."""
    logger.debug("test_registry_v2_is_exact_additive_snapshot_with_independent_oracle entry")
    old = promotion_registry()
    registry = promotion_registry_v2()
    validated = validate_registry_v2(registry)
    assert validated == registry and validated is not registry
    assert registry.registry_digest == REGISTRY_DIGEST
    assert audit_registry_v2_against_literal_oracle(registry) == EXTENSION_ORACLE_DIGEST
    assert (len(registry.domains), len(registry.rules), len(registry.premise_projections)) == (15, 18, 41)
    assert (len(registry.index_projections), len(registry.schema_targets)) == (1, 5)
    assert registry.domains == old.domains
    assert registry.rules[:-1] == old.rules
    assert registry.premise_projections[:-1] == old.premise_projections
    assert registry.index_projections == old.index_projections
    assert registry.schema_targets == old.schema_targets
    rule = registry.rules[-1]
    assert rule.rule_id == RULE_ID
    assert (rule.output_kind, rule.output_status, rule.output_provenance) == (
        JudgmentKind.PRESENTED,
        EvidenceStatus.ESTABLISHED,
        PositiveProvenance.SUPPLIED_PRESENTATION,
    )
    assert rule.output_indices == VISIBLE_INDICES
    assert rule.premise_signatures[0].artifact_kind == PREMISE_KIND
    assert rule.premise_signatures[0].required_evidence_fields == EVIDENCE_FIELDS
    assert rule.permanent_nonclaims == PERMANENT_NONCLAIMS
    assert registry.premise_projections[-1].source_rule_id == RULE_ID
    assert registry.index_projections == old.index_projections
    assert registry.rules[-1].statement_digest == "a6f3b6742f3f3adbf9bd27b08034d4043575bf2ce07df532cb90c6d0b7cbe7f6"
    assert registry.rules[-1].rule_digest == "b5e6bbff4bd0831e495fcd22f3846441b2a5bc2c0db37f00217322e03e0fe372"
    assert (
        registry.premise_projections[-1].projection_digest
        == "bad46ba3246b4ca5ade758902daa5bbfdf500d556988b6d07ff57fe636176441"
    )
    logger.debug("test_registry_v2_is_exact_additive_snapshot_with_independent_oracle exit")


def test_source_backed_presentation_retains_assumptions_and_validators() -> None:
    """The authority-backed result visibly retains all contract and trust boundaries."""
    logger.debug("test_source_backed_presentation_retains_assumptions_and_validators entry")
    sources, target, license, receipt = composition_case()
    value = build_licensed_composition_presentation(
        sources, target, license, receipt, judgment_id="licensed-presentation"
    )
    assert value.schema_version == JUDGMENT_SCHEMA
    assert value.target_contract == target and value.target_contract is not target
    assert value.receipt == receipt and value.receipt is not receipt
    assert value.assumption_roots == target.assumption_roots
    assert value.source_validator_roots == tuple(item.receipt.source_validator_root for item in sources)
    assert tuple(item.name for item in value.premise.indices) == VISIBLE_INDICES
    assert tuple(item.name for item in value.premise.evidence_fields) == EVIDENCE_FIELDS
    assert value.descriptor.indices == value.premise.indices
    assert value.request.assumptions == ()
    assert value.license == license and value.license is not license
    assert value.assessment.assessment_digest == receipt.assessment_digest
    assert value.registry_digest == REGISTRY_DIGEST
    assert value.extension_oracle_digest == EXTENSION_ORACLE_DIGEST
    assert all(
        item.authority_class is SourceValidationAuthority.EXTERNAL_BINDING_ONLY
        for item in value.source_validation_bindings
    )
    assert value.promotion_schema_audit.assumption_closure == ()
    assert value.promotion_schema_audit.scope == "p2-claim-admission-v2-named-rule-schema-meta-only"
    assert value.promotion_schema_audit.decision is MetaAuditDecision.SCHEMA_CONFORMANT
    assert value.promotion_schema_audit.ontological_establishment is MetaOntologicalStatus.NOT_CLAIMED
    assert value.schema_audit_report.scope == SCHEMA_AUDIT_SCOPE_V2
    assert value.schema_audit_report.nonclaims == SCHEMA_AUDIT_NONCLAIMS_V2
    assert len(value.schema_audit_report.rows) == 5
    assert tuple(item.binding_digest for item in value.source_validation_bindings) == (
        "c762b8cf135c5b3e9f0185067b40f6c0b311035a00779fd3483b8f45989b94cc",
        "a1bd97ae68f2d75f37e7cc6b8241bc823d5820e3ce9a8a9a34e9bfa8904d9bdb",
    )
    assert not any(
        (
            value.truth_established,
            value.coherence_established,
            value.assumptions_discharged,
            value.independence_established,
            value.ontology_established,
            receipt.p2_promotion_established,
        )
    )
    assert value.premise.artifact_digest == "9d59024885a5a9ad8c958c2536e388d29f64d54d1930d04954712367200f8465"
    assert value.descriptor.descriptor_digest == "0cf0ce377b257ab07adeef88e495eff542df3e6bf4604c840bf9c0dab383fb06"
    assert value.request.request_digest == "dcc73c4f3ff718ab02a8c9b05c9a131e97b63c226e3dacee11370d29ecda69b7"
    assert (
        value.promotion_schema_audit.audit_digest == "0e8a46cb177f78aa6af184c4775a3f7ee9dc7b38de3dc456b961e099bc884c63"
    )
    assert value.schema_audit_report.report_digest == "60fe5d614f9e964bb94b95d782b1bd6427df9cd7701f138254f752ee49f2a928"
    assert value.judgment_digest == "c79d5af79c159b714ee96d99f9aaf08b40e99cdf33cbc6e70667a029ff4d2462"
    assert validate_presentation_schema_audit(value.promotion_schema_audit, value.request, promotion_registry_v2())
    assert validate_presentation_schema_audit_report_v2(value.schema_audit_report, promotion_registry_v2())
    assert validate_licensed_composition_presentation(value, sources, target, license, receipt)
    logger.debug("test_source_backed_presentation_retains_assumptions_and_validators exit")


@pytest.mark.requires_posix_file_locks
def test_native_and_detached_same_v1_receipt_have_distinct_v2_authority(tmp_path) -> None:
    """Detached replay preserves v1 semantics but cannot inherit native replay authority."""
    logger.debug("test_native_and_detached_same_v1_receipt_have_distinct_v2_authority entry")
    native, detached, target, license, receipt = native_and_detached_case(tmp_path)
    native_value = build_licensed_composition_presentation(
        native, target, license, receipt, judgment_id="native-authority"
    )
    detached_value = build_licensed_composition_presentation(
        detached, target, license, receipt, judgment_id="native-authority"
    )
    assert tuple(item.receipt for item in native) == tuple(item.receipt for item in detached)
    assert native_value.receipt == detached_value.receipt == receipt
    assert native_value.source_validator_roots == detached_value.source_validator_roots
    assert all(
        item.authority_class is SourceValidationAuthority.NATIVE_GOVERNED_REPLAY
        for item in native_value.source_validation_bindings
    )
    assert all(
        item.authority_class is SourceValidationAuthority.EXTERNAL_BINDING_ONLY
        for item in detached_value.source_validation_bindings
    )
    assert tuple(item.local_receipt_digest for item in native_value.source_validation_bindings) == tuple(
        item.local_receipt_digest for item in detached_value.source_validation_bindings
    )
    assert tuple(item.binding_digest for item in native_value.source_validation_bindings) != tuple(
        item.binding_digest for item in detached_value.source_validation_bindings
    )
    assert native_value.premise.artifact_digest != detached_value.premise.artifact_digest
    assert native_value.descriptor.descriptor_digest != detached_value.descriptor.descriptor_digest
    assert native_value.request.request_digest != detached_value.request.request_digest
    assert native_value.promotion_schema_audit.audit_digest != detached_value.promotion_schema_audit.audit_digest
    assert native_value.schema_audit_report == detached_value.schema_audit_report
    assert native_value.judgment_digest != detached_value.judgment_digest
    for value, sources in ((native_value, native), (detached_value, detached)):
        payload = licensed_composition_presentation_json(value, sources, target, license, receipt)
        assert licensed_composition_presentation_from_json(payload, sources, target, license, receipt) == value
    logger.debug("test_native_and_detached_same_v1_receipt_have_distinct_v2_authority exit")


def test_v2_schema_audits_are_distinct_and_v1_builder_rejects_v2_registry() -> None:
    """Named-rule and fixed-five audits cannot cross-splice or enter the v1 builder."""
    logger.debug("test_v2_schema_audits_are_distinct_and_v1_builder_rejects_v2_registry entry")
    sources, target, license, receipt = composition_case()
    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id="audit-separation")
    registry = promotion_registry_v2()
    assert not validate_presentation_schema_audit(value.schema_audit_report, value.request, registry)
    assert not validate_presentation_schema_audit_report_v2(value.promotion_schema_audit, registry)
    assert build_presentation_schema_audit_report_v2(registry) == value.schema_audit_report
    with pytest.raises(StatusPromotionValidationError):
        audit_allowlisted_schemas(registry, promotion_policy())
    logger.debug("test_v2_schema_audits_are_distinct_and_v1_builder_rejects_v2_registry exit")


def test_premise_is_enriched_without_relabeling_the_v1_premise() -> None:
    """The exact old bridge remains index-free while the new premise is separately replayed."""
    logger.debug("test_premise_is_enriched_without_relabeling_the_v1_premise entry")
    sources, target, license, receipt = composition_case()
    old = build_composition_p2_premise(receipt, sources, target, license)
    new = build_composition_presentation_premise(sources, target, license, receipt)
    assert old.artifact_kind == COMPOSITION_PREMISE_KIND
    assert old.indices == ()
    assert new.artifact_kind == PREMISE_KIND
    assert new != old
    assert validate_composition_presentation_premise(new, sources, target, license, receipt)
    logger.debug("test_premise_is_enriched_without_relabeling_the_v1_premise exit")


def test_v1_registry_rejects_the_additive_rule_and_premise() -> None:
    """Neither a v2 identifier nor its premise can enter frozen P2-S v1."""
    logger.debug("test_v1_registry_rejects_the_additive_rule_and_premise entry")
    sources, target, license, receipt = composition_case()
    premise = build_composition_presentation_premise(sources, target, license, receipt)
    old = promotion_registry()
    descriptor = claim_descriptor(
        "v1-rejects-v2",
        JudgmentKind.PRESENTED,
        EvidenceStatus.ESTABLISHED,
        PositiveProvenance.SUPPLIED_PRESENTATION,
        premise.indices,
        old,
    )
    request = promotion_audit_request(RULE_ID, (premise,), (), descriptor, old)
    with pytest.raises(StatusPromotionValidationError, match="unknown-or-duplicate-promotion-rule"):
        audit_promotion_request(old, request, promotion_policy())
    logger.debug("test_v1_registry_rejects_the_additive_rule_and_premise exit")


@pytest.mark.parametrize("count", [2, 64])
def test_source_count_edges_and_permutation_canonicality(count: int) -> None:
    """Both inherited source-count edges produce one canonical presentation."""
    logger.debug("test_source_count_edges_and_permutation_canonicality entry count=%d", count)
    sources, target, license, receipt = composition_case(count)
    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id=f"edge-{count}")
    reordered = canonical_composition_sources(tuple(reversed(sources)))
    assert reordered == sources
    assert (
        build_licensed_composition_presentation(reordered, target, license, receipt, judgment_id=f"edge-{count}")
        == value
    )
    logger.debug("test_source_count_edges_and_permutation_canonicality exit count=%d", count)


def test_canonical_json_round_trip_replays_raw_authority() -> None:
    """The strict decoder returns only the freshly rebuilt typed presentation."""
    logger.debug("test_canonical_json_round_trip_replays_raw_authority entry")
    sources, target, license, receipt = composition_case()
    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id="json-round-trip")
    first = licensed_composition_presentation_json(value, sources, target, license, receipt)
    second = licensed_composition_presentation_json(value, sources, target, license, receipt)
    assert first == second
    assert licensed_composition_presentation_from_json(first, sources, target, license, receipt) == value
    assert (
        licensed_composition_presentation_from_json(first.encode("ascii"), sources, target, license, receipt) == value
    )
    logger.debug("test_canonical_json_round_trip_replays_raw_authority exit")


def test_producer_accepts_no_caller_audit_conclusion_or_registry_authority() -> None:
    """The sole producer signature leaves every derived P2 object internal."""
    logger.debug("test_producer_accepts_no_caller_audit_conclusion_or_registry_authority entry")
    parameters = tuple(inspect.signature(build_licensed_composition_presentation).parameters)
    assert parameters == ("sources", "target", "license", "receipt", "judgment_id")
    assert not {"registry", "policy", "premise", "conclusion", "request", "audit"}.intersection(parameters)
    logger.debug("test_producer_accepts_no_caller_audit_conclusion_or_registry_authority exit")
