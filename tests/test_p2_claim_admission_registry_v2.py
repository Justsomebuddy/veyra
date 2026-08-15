"""Compatibility and hostile tests for the meta-only P2 registry-v2 wave."""

from __future__ import annotations

from dataclasses import fields, replace
import logging

import pytest

import src.core as core
import src.core.p2_claim_admission_v2 as registry_api
import src.core.p2_claim_admission_v2.registry as registry_module
from src.core.p2_claim_admission_v2 import (
    EVIDENCE_FIELDS,
    EXTENSION_ORACLE_DIGEST,
    PERMANENT_NONCLAIMS,
    PREMISE_KIND,
    REGISTRY_DIGEST,
    RULE_ID,
    VISIBLE_INDICES,
    P2ClaimAdmissionError,
    audit_registry_v2_against_literal_oracle,
    promotion_registry_v2,
    validate_registry_v2,
)
from src.core.status_promotion import (
    EvidenceStatus,
    JudgmentKind,
    PositiveProvenance,
    audit_registry_against_literal_oracle,
    promotion_registry,
    validate_registry,
)
from src.core.status_promotion_common import StatusPromotionValidationError
from src.core.status_promotion_oracle import LITERAL_ORACLE_DIGEST
from src.core.status_promotion_types import PremiseSignature, PromotionRegistry, PromotionRule

logger = logging.getLogger(__name__)

_V1_REGISTRY_DIGEST = "375f1654807b462c3a9ebd9a112a75ee28fc96a4029cf767acae1fd591a60e9d"
_V1_ORACLE_DIGEST = "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"
_EXPECTED_NONCLAIMS = (
    "source-truth",
    "external-validator-trust",
    "logical-consistency",
    "logical-coherence",
    "assumption-discharge",
    "unconditionalization",
    "independence",
    "corroboration",
    "adaptive-validity",
    "family-validity",
    "statistical-validity",
    "population-validity",
    "universalization",
    "existential-upgrade",
    "objectivity",
    "observer-independence",
    "theorem",
    "certificate",
    "formal-proof",
    "ontology",
    "object",
    "history",
    "lifecycle",
    "empirical-instantiation",
    "physical-instantiation",
    "authentication",
    "custody",
    "chronology",
    "audit-as-truth",
)


def test_v1_registry_oracle_dtos_and_root_exports_remain_exact() -> None:
    """The additive sibling changes no v1 DTO, digest, oracle, count, or root facade."""
    logger.debug("test_v1_registry_oracle_dtos_and_root_exports_remain_exact entry")
    old = promotion_registry()
    assert old.registry_digest == _V1_REGISTRY_DIGEST
    assert LITERAL_ORACLE_DIGEST == _V1_ORACLE_DIGEST
    assert audit_registry_against_literal_oracle(old) == _V1_ORACLE_DIGEST
    assert (len(old.domains), len(old.rules), len(old.premise_projections)) == (15, 17, 40)
    assert (len(old.index_projections), len(old.schema_targets)) == (1, 5)
    assert tuple(item.name for item in fields(PremiseSignature)) == (
        "premise_name",
        "artifact_kind",
        "required_evidence_fields",
        "required_indices",
    )
    assert tuple(item.name for item in fields(PromotionRule)) == (
        "rule_id",
        "statement_digest",
        "premise_signatures",
        "output_kind",
        "output_status",
        "output_provenance",
        "output_indices",
        "forbidden_source_types",
        "forbidden_conclusion_fields",
        "assumption_policy_id",
        "permanent_nonclaims",
        "rule_digest",
    )
    assert tuple(item.name for item in fields(PromotionRegistry)) == (
        "version",
        "domains",
        "rules",
        "premise_projections",
        "index_projections",
        "schema_targets",
        "registry_digest",
    )
    assert not hasattr(core, "promotion_registry_v2")
    assert not hasattr(core, "build_licensed_composition_presentation")
    logger.debug("test_v1_registry_oracle_dtos_and_root_exports_remain_exact exit")


def test_registry_v2_is_exact_v1_plus_one_literal_rule_and_projection() -> None:
    """The complete v2 snapshot preserves the exact v1 prefix and fixed counts."""
    logger.debug("test_registry_v2_is_exact_v1_plus_one_literal_rule_and_projection entry")
    old = promotion_registry()
    value = promotion_registry_v2()
    validated = validate_registry_v2(value)
    assert validated == value and validated is not value
    assert value.registry_digest == REGISTRY_DIGEST
    assert REGISTRY_DIGEST == "ba6020151518faf5eb2fa2eb22943af4c7d0abd88b393b1388f848e63dbc3eb4"
    assert (len(value.domains), len(value.rules), len(value.premise_projections)) == (15, 18, 41)
    assert (len(value.index_projections), len(value.schema_targets)) == (1, 5)
    assert value.domains == old.domains
    assert value.rules[:-1] == old.rules
    assert value.premise_projections[:-1] == old.premise_projections
    assert value.index_projections == old.index_projections
    assert value.schema_targets == old.schema_targets
    logger.debug("test_registry_v2_is_exact_v1_plus_one_literal_rule_and_projection exit")


def test_only_new_rule_has_frozen_conservative_contract() -> None:
    """The new row exposes every binding and cannot output stronger semantics."""
    logger.debug("test_only_new_rule_has_frozen_conservative_contract entry")
    value = promotion_registry_v2()
    rule = value.rules[-1]
    assert rule.rule_id == RULE_ID == "composition-licensed-presentation-v2"
    assert rule.statement_digest == "a6f3b6742f3f3adbf9bd27b08034d4043575bf2ce07df532cb90c6d0b7cbe7f6"
    assert rule.rule_digest == "b5e6bbff4bd0831e495fcd22f3846441b2a5bc2c0db37f00217322e03e0fe372"
    assert (rule.output_kind, rule.output_status, rule.output_provenance) == (
        JudgmentKind.PRESENTED,
        EvidenceStatus.ESTABLISHED,
        PositiveProvenance.SUPPLIED_PRESENTATION,
    )
    assert len(rule.premise_signatures) == 1
    premise = rule.premise_signatures[0]
    assert premise.artifact_kind == PREMISE_KIND == "claim-composition-presentation-v2"
    assert (
        premise.required_evidence_fields
        == EVIDENCE_FIELDS
        == (
            "target-contract",
            "claim-set",
            "scope-set",
            "assumption-set",
            "doctrine-set",
            "source-validator-family",
            "source-family",
            "composition-license",
            "composition-assessment",
            "nonpromotion",
        )
    )
    assert (
        premise.required_indices
        == rule.output_indices
        == VISIBLE_INDICES
        == (
            "contract",
            "claims",
            "scope",
            "assumptions",
            "doctrine",
            "source-validators",
            "composition",
        )
    )
    assert rule.permanent_nonclaims == PERMANENT_NONCLAIMS == _EXPECTED_NONCLAIMS
    assert value.premise_projections[-1].projection_digest == (
        "bad46ba3246b4ca5ade758902daa5bbfdf500d556988b6d07ff57fe636176441"
    )
    assert value.index_projections == promotion_registry().index_projections
    logger.debug("test_only_new_rule_has_frozen_conservative_contract exit")


def test_extension_oracle_binds_literal_v1_anchors_and_new_row(monkeypatch) -> None:
    """The handwritten oracle has an independent exact pin and fails closed on drift."""
    logger.debug("test_extension_oracle_binds_literal_v1_anchors_and_new_row entry")
    value = promotion_registry_v2()
    assert EXTENSION_ORACLE_DIGEST == "ee55fcb02a6c69b8915e54ceee0ac7d0e2b741452198be6c49e9f14ae37488d3"
    assert audit_registry_v2_against_literal_oracle(value) == EXTENSION_ORACLE_DIGEST
    monkeypatch.setattr(registry_module, "compute_extension_oracle_digest", lambda: "0" * 64)
    with pytest.raises(P2ClaimAdmissionError, match="extension-oracle-digest-drift"):
        audit_registry_v2_against_literal_oracle(value)
    logger.debug("test_extension_oracle_binds_literal_v1_anchors_and_new_row exit")


def test_v1_validator_rejects_additive_snapshot_and_knows_no_new_rule() -> None:
    """V1 remains closed and cannot consume or certify the additive rule."""
    logger.debug("test_v1_validator_rejects_additive_snapshot_and_knows_no_new_rule entry")
    old = promotion_registry()
    assert all(rule.rule_id != RULE_ID for rule in old.rules)
    with pytest.raises(StatusPromotionValidationError):
        validate_registry(promotion_registry_v2())
    logger.debug("test_v1_validator_rejects_additive_snapshot_and_knows_no_new_rule exit")


@pytest.mark.parametrize(
    "mutator",
    (
        lambda value: replace(value, registry_digest="0" * 64),
        lambda value: replace(value, domains=value.domains[:-1]),
        lambda value: replace(value, rules=value.rules[:-1]),
        lambda value: replace(
            value,
            rules=value.rules[:-1] + (replace(value.rules[-1], output_kind=JudgmentKind.COHERENT),),
        ),
        lambda value: replace(
            value,
            rules=value.rules[:-1]
            + (
                replace(
                    value.rules[-1],
                    premise_signatures=(
                        replace(value.rules[-1].premise_signatures[0], required_indices=VISIBLE_INDICES[:-1]),
                    ),
                ),
            ),
        ),
        lambda value: replace(value, premise_projections=value.premise_projections[:-1]),
        lambda value: replace(
            value,
            premise_projections=value.premise_projections[:-1]
            + (replace(value.premise_projections[-1], projection_digest="0" * 64),),
        ),
    ),
)
def test_registry_v2_rejects_cardinality_semantic_and_digest_splices(mutator) -> None:
    """Every governed additive row and prefix boundary is exact rather than shape-only."""
    logger.debug("test_registry_v2_rejects_cardinality_semantic_and_digest_splices entry")
    with pytest.raises(P2ClaimAdmissionError):
        validate_registry_v2(mutator(promotion_registry_v2()))
    logger.debug("test_registry_v2_rejects_cardinality_semantic_and_digest_splices exit")


def test_nested_primitive_callback_rejects_before_registry_equality() -> None:
    """Exact nested-type preflight prevents attacker equality callbacks."""
    logger.debug("test_nested_primitive_callback_rejects_before_registry_equality entry")

    class ExplosiveStr(str):
        def __eq__(self, _other):
            raise AssertionError("nested equality callback reached")

    value = replace(promotion_registry_v2())
    object.__setattr__(value, "version", ExplosiveStr(value.version))
    with pytest.raises(P2ClaimAdmissionError, match="registry-v2-nested-type"):
        validate_registry_v2(value)
    logger.debug("test_nested_primitive_callback_rejects_before_registry_equality exit")


def test_hostile_top_level_container_rejects_before_len_or_iteration() -> None:
    """A tuple subclass cannot run callbacks before the exact-container gate."""
    logger.debug("test_hostile_top_level_container_rejects_before_len_or_iteration entry")

    class ExplosiveTuple(tuple):
        def __len__(self):
            raise AssertionError("hostile len reached")

        def __iter__(self):
            raise AssertionError("hostile iteration reached")

    value = replace(promotion_registry_v2())
    object.__setattr__(value, "domains", ExplosiveTuple(value.domains))
    with pytest.raises(P2ClaimAdmissionError, match="registry-v2-nested-type"):
        validate_registry_v2(value)
    logger.debug("test_hostile_top_level_container_rejects_before_len_or_iteration exit")


def test_oversized_nested_tuple_rejects_before_deep_element_scan() -> None:
    """Nested cardinality is precharged before element validation or equality."""
    logger.debug("test_oversized_nested_tuple_rejects_before_deep_element_scan entry")
    value = promotion_registry_v2()
    rule = replace(value.rules[-1], permanent_nonclaims=("bounded",) * 65_537)
    spliced = replace(value, rules=value.rules[:-1] + (rule,))
    with pytest.raises(P2ClaimAdmissionError, match="structural-node-limit"):
        validate_registry_v2(spliced)
    logger.debug("test_oversized_nested_tuple_rejects_before_deep_element_scan exit")


@pytest.mark.parametrize(
    ("identifier", "reason"),
    (
        ("x" * 128, "registry-v2-not-canonical"),
        ("x" * 129, "registry-v2-identifier-limit"),
        ("é" * 64, "registry-v2-not-canonical"),
        ("é" * 65, "registry-v2-identifier-limit"),
    ),
)
def test_registry_identifier_utf8_limit_precedes_equality(identifier: str, reason: str) -> None:
    """Exactly 128 UTF-8 bytes pass the resource gate; byte 129 fails there."""
    logger.debug("test_registry_identifier_utf8_limit_precedes_equality entry bytes=%d", len(identifier.encode()))
    value = replace(promotion_registry_v2(), version=identifier)
    with pytest.raises(P2ClaimAdmissionError, match=reason):
        validate_registry_v2(value)
    logger.debug("test_registry_identifier_utf8_limit_precedes_equality exit")


def test_p2_claim_admission_v2_exports_exact_registry_and_producer_surface() -> None:
    """The completed sibling exports only its fixed registry and producer API."""
    logger.debug("test P2 claim-admission v2 exact exports entry")
    assert set(registry_api.__all__) == {
        "EVIDENCE_FIELDS",
        "EXTENSION_ORACLE_DIGEST",
        "JUDGMENT_BOUNDARY",
        "JUDGMENT_SCHEMA",
        "LicensedCompositionPresentation",
        "MAX_DEPTH",
        "MAX_IDENTIFIER_BYTES",
        "MAX_JSON_BYTES",
        "MAX_NONPAYLOAD_TEXT_BYTES",
        "MAX_STRUCTURAL_NODES",
        "P2ClaimAdmissionError",
        "P2_CLAIM_ADMISSION_VERSION",
        "PERMANENT_NONCLAIMS",
        "PREMISE_KIND",
        "PREMISE_NAME",
        "PROJECTION_ID",
        "REGISTRY_DIGEST",
        "REGISTRY_VERSION",
        "RULE_ID",
        "SCHEMA_AUDIT_NONCLAIMS_V2",
        "SCHEMA_AUDIT_SCOPE_V2",
        "SourceValidationAuthority",
        "SourceValidationBinding",
        "VISIBLE_INDICES",
        "audit_registry_v2_against_literal_oracle",
        "build_composition_presentation_premise",
        "build_licensed_composition_presentation",
        "build_presentation_schema_audit",
        "build_presentation_schema_audit_report_v2",
        "licensed_composition_presentation_from_json",
        "licensed_composition_presentation_json",
        "promotion_registry_v2",
        "validate_composition_presentation_premise",
        "validate_licensed_composition_presentation",
        "validate_presentation_schema_audit",
        "validate_presentation_schema_audit_report_v2",
        "validate_registry_v2",
    }
    logger.debug("test P2 claim-admission v2 exact exports exit")
