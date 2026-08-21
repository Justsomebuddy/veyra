"""Hostile replay, codec, resource, and log-boundary tests for P2 v2."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from enum import Enum
import json
import logging
from threading import Thread

import pytest

import src.core.p2_claim_admission_v2.codec as codec_module
import src.core.p2_claim_admission_v2.public as public_module
import src.core.p2_claim_admission_v2.replay as replay_module
from src.core.claim_composition import (
    AdaptiveCapability,
    ClaimClass,
    ClaimQuantifier,
    CorroborationStatus,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
    build_claim_contract,
    build_composition_receipt,
    build_exact_conjunction_contract,
    build_exact_conjunction_license,
    build_external_composition_source,
    build_local_claim_receipt,
    canonical_composition_sources,
    validate_claim_contract,
)
from src.core.claim_composition.types import ClaimCompositionSource
from src.core.p2_claim_admission_v2 import (
    MAX_IDENTIFIER_BYTES,
    MAX_JSON_BYTES,
    MAX_NONPAYLOAD_TEXT_BYTES,
    MAX_STRUCTURAL_NODES,
    P2ClaimAdmissionError,
    SourceValidationAuthority,
    build_licensed_composition_presentation,
    validate_composition_presentation_premise,
    licensed_composition_presentation_from_json,
    licensed_composition_presentation_json,
    promotion_registry_v2,
    validate_licensed_composition_presentation,
    validate_presentation_schema_audit,
    validate_presentation_schema_audit_report_v2,
    validate_registry_v2,
)
from src.core.p2_claim_admission_v2.codec import _canonical_json, _decode_payload
from src.core.p2_claim_admission_v2.log_boundary import protected_replay_logs
from src.core.p2_claim_admission_v2.validation import charge_structure, charge_text, preflight_authoritative_inputs
from src.core.status_promotion_types import EvidenceStatus, JudgmentKind, PositiveProvenance

from p2_claim_admission_v2_fixture import composition_case, root

logger = logging.getLogger(__name__)


def _build(case, judgment_id: str = "hostile-control"):
    """Build one control judgment from a four-item fixture tuple."""
    logger.debug("_build entry")
    sources, target, license, receipt = case
    result = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id=judgment_id)
    logger.debug("_build exit")
    return result


def _large_shared_root_case(root_count: int):
    """Build one valid v1 family near the combined sibling text ceiling."""
    logger.debug("_large_shared_root_case entry root_count=%d", root_count)
    pools = [tuple(sorted(root(f"pool-{dimension}-{index}") for index in range(root_count))) for dimension in range(4)]
    sources = []
    for source_index in range(14):
        dimensions = [list(items) for items in pools]
        dimensions[source_index % 4].append(root(f"unique-{source_index}"))
        ordered = [tuple(sorted(items)) for items in dimensions]
        contract = build_claim_contract(
            ordered[0],
            ordered[1],
            ordered[2],
            ClaimQuantifier.LOCAL,
            (),
            ordered[3],
            (),
            (),
            (),
            (ClaimClass.EMPIRICAL,),
            CorroborationStatus.SINGLE_LOCAL_RECEIPT,
            AdaptiveCapability.LOCAL_ONLY,
            PublicWording.BOUNDED_LOCAL,
        )
        local = build_local_claim_receipt(
            contract,
            root(f"shared-source-{source_index}"),
            root(f"shared-validator-{source_index}"),
            LocalReceiptValidity.ESTABLISHED,
        )
        sources.append(build_external_composition_source(local, SourceEffect.INCLUDE_LOCAL_CLAIM))
    canonical = canonical_composition_sources(tuple(sources))
    target = build_exact_conjunction_contract(canonical)
    license = build_exact_conjunction_license(canonical, target)
    receipt = build_composition_receipt(canonical, target, license)
    logger.debug("_large_shared_root_case exit root_count=%d", root_count)
    return canonical, target, license, receipt


def test_raw_source_target_license_and_receipt_splices_fail_closed() -> None:
    """Every authority-bearing raw input is freshly replayed rather than digest-trusted."""
    logger.debug("test_raw_source_target_license_and_receipt_splices_fail_closed entry")
    case = composition_case()
    sources, target, license, receipt = case
    value = _build(case)
    forged_local = replace(sources[0].receipt, source_validator_root=root("foreign-validator"))
    forged_source = replace(sources[0], receipt=forged_local)
    forged_sources = (forged_source,) + sources[1:]
    attacks = (
        (forged_sources, target, license, receipt),
        (sources, replace(target, claim_roots=(root("foreign-claim"),)), license, receipt),
        (sources, target, replace(license, target_contract_digest=root("foreign-target")), receipt),
        (sources, target, license, replace(receipt, assessment_digest=root("foreign-assessment"))),
    )
    assert all(
        not validate_licensed_composition_presentation(
            value, attack_sources, attack_target, attack_license, attack_receipt
        )
        for attack_sources, attack_target, attack_license, attack_receipt in attacks
    )
    logger.debug("test_raw_source_target_license_and_receipt_splices_fail_closed exit")


def test_premise_descriptor_request_audit_and_false_flag_splices_fail() -> None:
    """No derived DTO or conclusion-like flag is accepted independently of raw replay."""
    logger.debug("test_premise_descriptor_request_audit_and_false_flag_splices_fail entry")
    case = composition_case()
    sources, target, license, receipt = case
    value = _build(case)
    premise = replace(value.premise, artifact_digest=root("foreign-premise"))
    descriptor = replace(value.descriptor, descriptor_digest=root("foreign-descriptor"))
    request = replace(value.request, request_digest=root("foreign-request"))
    audit = replace(value.promotion_schema_audit, audit_digest=root("foreign-audit"))
    conclusion_audit = replace(
        value.promotion_schema_audit,
        conclusion=replace(value.promotion_schema_audit.conclusion, kind=JudgmentKind.COHERENT),
    )
    schema_report = replace(value.schema_audit_report, report_digest=root("foreign-schema-report"))
    binding = replace(
        value.source_validation_bindings[0],
        authority_class=SourceValidationAuthority.NATIVE_GOVERNED_REPLAY,
    )
    attacks = (
        replace(value, premise=premise),
        replace(value, descriptor=descriptor),
        replace(value, request=request),
        replace(value, promotion_schema_audit=audit),
        replace(value, promotion_schema_audit=conclusion_audit),
        replace(value, schema_audit_report=schema_report),
        replace(
            value,
            source_validation_bindings=(binding,) + value.source_validation_bindings[1:],
        ),
        replace(value, source_validation_bindings=tuple(reversed(value.source_validation_bindings))),
        replace(value, license=replace(value.license, license_digest=root("foreign-license"))),
        replace(value, assessment=replace(value.assessment, assessment_digest=root("foreign-assessment"))),
        replace(value, registry_digest=root("foreign-registry")),
        replace(value, extension_oracle_digest=root("foreign-oracle")),
        replace(value, truth_established=True),
        replace(value, coherence_established=True),
        replace(value, assumptions_discharged=True),
        replace(value, independence_established=True),
        replace(value, ontology_established=True),
    )
    assert all(
        not validate_licensed_composition_presentation(item, sources, target, license, receipt) for item in attacks
    )
    logger.debug("test_premise_descriptor_request_audit_and_false_flag_splices_fail exit")


def test_registry_splice_and_stronger_conclusions_are_impossible() -> None:
    """The literal registry and sole output triple reject coherent/objective/physical drift."""
    logger.debug("test_registry_splice_and_stronger_conclusions_are_impossible entry")
    registry = promotion_registry_v2()
    for kind in (JudgmentKind.COHERENT, JudgmentKind.OBJECTIVELY_STABLE, JudgmentKind.PHYSICALLY_INSTANTIATED):
        forged_rule = replace(registry.rules[-1], output_kind=kind)
        with pytest.raises(P2ClaimAdmissionError, match="registry-v2-not-canonical"):
            validate_registry_v2(replace(registry, rules=registry.rules[:-1] + (forged_rule,)))
    assert registry.rules[-1].output_status is EvidenceStatus.ESTABLISHED
    assert registry.rules[-1].output_provenance is PositiveProvenance.SUPPLIED_PRESENTATION
    logger.debug("test_registry_splice_and_stronger_conclusions_are_impossible exit")


def test_registry_nested_callback_splice_rejects_before_equality() -> None:
    """A forged primitive subclass cannot reach dataclass equality callbacks."""
    logger.debug("test_registry_nested_callback_splice_rejects_before_equality entry")

    class ExplosiveStr(str):
        def __eq__(self, _other):
            raise AssertionError("nested equality callback reached")

    registry = promotion_registry_v2()
    forged = replace(registry)
    object.__setattr__(forged, "version", ExplosiveStr(registry.version))
    with pytest.raises(P2ClaimAdmissionError, match="registry-v2-nested-type"):
        validate_registry_v2(forged)
    logger.debug("test_registry_nested_callback_splice_rejects_before_equality exit")


def test_all_public_validators_reject_nested_callbacks_before_access() -> None:
    """Exact whitelists reject spoofed primitives and enums without callbacks."""
    logger.debug("test all public validators nested callback rejection entry")

    class ExplosiveStr(str):
        def __eq__(self, _other):
            raise AssertionError("nested equality callback reached")

    class ExplosiveEnum(str, Enum):
        X = "FINITE_CONJUNCTION"

        @property
        def value(self):
            raise AssertionError("enum value callback reached")

    ExplosiveEnum.__module__ = "src.core.hostile"
    sources, target, license, receipt = composition_case()
    raw_target = replace(target)
    object.__setattr__(raw_target, "schema_version", ExplosiveStr(target.schema_version))
    with pytest.raises(P2ClaimAdmissionError, match="presentation-nested-type"):
        build_licensed_composition_presentation(sources, raw_target, license, receipt, judgment_id="raw-callback")

    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id="candidate-callback")
    forged_target = replace(value.target_contract)
    object.__setattr__(forged_target, "quantifier", ExplosiveEnum.X)
    assert not validate_licensed_composition_presentation(
        replace(value, target_contract=forged_target), sources, target, license, receipt
    )

    forged_index = replace(value.premise.indices[0])
    object.__setattr__(forged_index, "name", ExplosiveStr(forged_index.name))
    forged_premise = replace(
        value.premise,
        indices=(forged_index, *value.premise.indices[1:]),
    )
    assert not validate_composition_presentation_premise(forged_premise, sources, target, license, receipt)

    forged_audit = replace(value.promotion_schema_audit)
    object.__setattr__(
        forged_audit,
        "scope",
        ExplosiveStr(value.promotion_schema_audit.scope),
    )
    assert not validate_presentation_schema_audit(forged_audit, value.request, promotion_registry_v2())
    forged_report = replace(value.schema_audit_report)
    object.__setattr__(
        forged_report,
        "scope",
        ExplosiveStr(value.schema_audit_report.scope),
    )
    assert not validate_presentation_schema_audit_report_v2(forged_report, promotion_registry_v2())
    logger.debug("test all public validators nested callback rejection exit")


def test_authoritative_inputs_are_captured_before_replay_toctou(monkeypatch) -> None:
    """Mutation of caller DTOs after capture cannot enter the issued judgment."""
    logger.debug("test authoritative input capture TOCTOU entry")
    sources, target, license, receipt = composition_case()
    original_replay = public_module._authoritative_replay

    def mutate_caller_after_replay(*args):
        replay = original_replay(*args)
        object.__setattr__(target, "claim_roots", (root("raced-caller-root"),))
        return replay

    monkeypatch.setattr(public_module, "_authoritative_replay", mutate_caller_after_replay)
    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id="toctou-capture")
    assert value.target_contract is not target
    assert value.target_contract.claim_roots != target.claim_roots
    assert validate_claim_contract(value.target_contract)
    logger.debug("test authoritative input capture TOCTOU exit")


def test_empty_p2_closure_never_discharges_opaque_target_assumptions() -> None:
    """An empty syntactic DAG remains distinct from retained opaque assumption roots."""
    logger.debug("test_empty_p2_closure_never_discharges_opaque_target_assumptions entry")
    case = composition_case()
    value = _build(case)
    assert value.assumption_roots
    assert value.request.assumptions == ()
    assert value.promotion_schema_audit.assumption_closure == ()
    assert value.assumptions_discharged is False
    logger.debug("test_empty_p2_closure_never_discharges_opaque_target_assumptions exit")


def test_strict_json_rejects_duplicate_trailing_noncanonical_and_unknown_enum() -> None:
    """The decoder accepts exactly one canonical schema and reconstructs authority."""
    logger.debug("test_strict_json_rejects_duplicate_trailing_noncanonical_and_unknown_enum entry")
    case = composition_case()
    sources, target, license, receipt = case
    value = _build(case, "strict-json")
    payload = licensed_composition_presentation_json(value, sources, target, license, receipt)
    duplicate = '{"schema_version":"duplicate",' + payload[1:]
    decoded = json.loads(payload)
    pretty = json.dumps(decoded, indent=2, sort_keys=True)
    decoded["descriptor"]["kind"] = "coherent"
    unknown = json.dumps(decoded, sort_keys=True, separators=(",", ":"))
    for hostile, reason in (
        (duplicate, "presentation-json-duplicate-key"),
        (payload + " ", "presentation-json-noncanonical"),
        (pretty, "presentation-json-noncanonical"),
        (unknown, "presentation-json-authority-mismatch"),
    ):
        with pytest.raises(P2ClaimAdmissionError, match=reason):
            licensed_composition_presentation_from_json(hostile, sources, target, license, receipt)
    logger.debug("test_strict_json_rejects_duplicate_trailing_noncanonical_and_unknown_enum exit")


def test_json_rejects_authority_and_schema_audit_splices() -> None:
    """Canonical syntax cannot turn detached authority or either audit into caller authority."""
    logger.debug("test_json_rejects_authority_and_schema_audit_splices entry")
    case = composition_case()
    sources, target, license, receipt = case
    value = _build(case, "json-authority-splice")
    payload = licensed_composition_presentation_json(value, sources, target, license, receipt)
    attacks = []
    decoded = json.loads(payload)
    decoded["source_validation_bindings"][0]["authority_class"] = "NATIVE_GOVERNED_REPLAY"
    attacks.append(decoded)
    decoded = json.loads(payload)
    decoded["promotion_schema_audit"]["scope"] = "foreign-scope"
    attacks.append(decoded)
    decoded = json.loads(payload)
    decoded["schema_audit_report"]["rows"][0]["row_digest"] = root("foreign-row")
    attacks.append(decoded)
    for attack in attacks:
        hostile = json.dumps(attack, sort_keys=True, separators=(",", ":"))
        with pytest.raises(P2ClaimAdmissionError, match="presentation-json-authority-mismatch"):
            licensed_composition_presentation_from_json(hostile, sources, target, license, receipt)
    logger.debug("test_json_rejects_authority_and_schema_audit_splices exit")


def test_identifier_text_node_json_and_depth_caps_are_inclusive() -> None:
    """Every sibling cap accepts its exact edge and rejects the next unit."""
    logger.debug("test_identifier_text_node_json_and_depth_caps_are_inclusive entry")
    case = composition_case()
    sources, target, license, receipt = case
    exact_id = "é" * (MAX_IDENTIFIER_BYTES // 2)
    value = build_licensed_composition_presentation(sources, target, license, receipt, judgment_id=exact_id)
    assert value.judgment_id == exact_id
    with pytest.raises(P2ClaimAdmissionError, match="judgment-id"):
        build_licensed_composition_presentation(sources, target, license, receipt, judgment_id=exact_id + "é")

    assert charge_text("a" * MAX_NONPAYLOAD_TEXT_BYTES) == MAX_NONPAYLOAD_TEXT_BYTES
    with pytest.raises(P2ClaimAdmissionError, match="nonpayload-text-limit"):
        charge_text("a" * (MAX_NONPAYLOAD_TEXT_BYTES + 1))

    exact_nodes = tuple(None for _ in range(MAX_STRUCTURAL_NODES - 1))
    assert charge_structure(exact_nodes) == MAX_STRUCTURAL_NODES
    with pytest.raises(P2ClaimAdmissionError, match="structural-node-limit"):
        charge_structure(exact_nodes + (None,))

    with pytest.raises(P2ClaimAdmissionError, match="presentation-json-syntax"):
        _decode_payload(" " * MAX_JSON_BYTES)
    with pytest.raises(P2ClaimAdmissionError, match="presentation-json-byte-limit"):
        _decode_payload(" " * (MAX_JSON_BYTES + 1))
    assert len(_canonical_json("a" * (MAX_JSON_BYTES - 2))) == MAX_JSON_BYTES
    with pytest.raises(P2ClaimAdmissionError, match="presentation-json-byte-limit"):
        _canonical_json("a" * (MAX_JSON_BYTES - 1))
    with pytest.raises(P2ClaimAdmissionError, match="presentation-json-number"):
        _decode_payload("1")
    with pytest.raises(P2ClaimAdmissionError, match="invalid-node-allowance"):
        charge_structure(None, allowance=True)

    exact_depth: object = None
    for _ in range(128):
        exact_depth = [exact_depth]
    assert charge_structure(exact_depth) == 129
    too_deep = [exact_depth]
    with pytest.raises(P2ClaimAdmissionError, match="structural-depth-limit"):
        charge_structure(too_deep)
    logger.debug("test_identifier_text_node_json_and_depth_caps_are_inclusive exit")


def test_builder_enforces_combined_raw_and_result_text_ceiling() -> None:
    """Every returned presentation must pass its own combined resource gate."""
    logger.debug("test builder combined raw/result text ceiling entry")
    control = _large_shared_root_case(240)
    value = build_licensed_composition_presentation(*control, judgment_id="combined-text-control")
    assert validate_licensed_composition_presentation(value, *control)
    over_limit = _large_shared_root_case(249)
    with pytest.raises(P2ClaimAdmissionError, match="nonpayload-text-limit"):
        build_licensed_composition_presentation(*over_limit, judgment_id="combined-text-refusal")
    logger.debug("test builder combined raw/result text ceiling exit")


def test_json_export_never_emits_a_payload_its_decoder_refuses() -> None:
    """Exporter and decoder must share the same raw-plus-decoded text ledger."""
    logger.debug("test JSON codec combined text closure entry")
    roundtrip_case = _large_shared_root_case(243)
    roundtrip_value = build_licensed_composition_presentation(*roundtrip_case, judgment_id="a")
    payload = licensed_composition_presentation_json(roundtrip_value, *roundtrip_case)
    assert licensed_composition_presentation_from_json(payload, *roundtrip_case) == roundtrip_value

    decoder_only_overflow = _large_shared_root_case(244)
    overflow_value = build_licensed_composition_presentation(*decoder_only_overflow, judgment_id="a")
    assert validate_licensed_composition_presentation(overflow_value, *decoder_only_overflow)
    with pytest.raises(P2ClaimAdmissionError, match="nonpayload-text-limit"):
        licensed_composition_presentation_json(overflow_value, *decoder_only_overflow)
    logger.debug("test JSON codec combined text closure exit")


def test_source_count_preflight_rejects_one_and_sixty_five_before_replay() -> None:
    """The inherited 2..64 boundary is enforced by the sibling's first preflight."""
    logger.debug("test_source_count_preflight_rejects_one_and_sixty_five_before_replay entry")
    sources, target, license, receipt = composition_case()
    for hostile in ((sources[0],), tuple(sources[0] for _ in range(65))):
        with pytest.raises(P2ClaimAdmissionError, match="source-count"):
            preflight_authoritative_inputs(hostile, target, license, receipt, "source-edge")
    logger.debug("test_source_count_preflight_rejects_one_and_sixty_five_before_replay exit")


def test_resource_preflights_run_before_deep_replay_json_parse_and_equality(monkeypatch) -> None:
    """Literal over-limits fail before the authority, parser, or candidate comparison paths."""
    logger.debug("test_resource_preflights_run_before_deep_replay_json_parse_and_equality entry")
    case = composition_case()
    sources, target, license, receipt = case

    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("deep replay reached")

    monkeypatch.setattr(replay_module, "validate_composition_receipt", forbidden_replay)
    with pytest.raises(P2ClaimAdmissionError, match="judgment-id"):
        build_licensed_composition_presentation(
            sources, target, license, receipt, judgment_id="x" * (MAX_IDENTIFIER_BYTES + 1)
        )

    def forbidden_loads(*_args, **_kwargs):
        raise AssertionError("JSON parse reached")

    monkeypatch.setattr(codec_module.json, "loads", forbidden_loads)
    hostile = "[" + ",".join("null" for _ in range(MAX_STRUCTURAL_NODES)) + "]"
    with pytest.raises(P2ClaimAdmissionError, match="structural-node-limit"):
        licensed_composition_presentation_from_json(hostile, sources, target, license, receipt)

    monkeypatch.undo()
    value = _build(case)
    hostile_value = replace(value, boundary="z" * MAX_NONPAYLOAD_TEXT_BYTES)
    raw_nodes, raw_text = preflight_authoritative_inputs(sources, target, license, receipt, value.judgment_id)
    with pytest.raises(P2ClaimAdmissionError, match="nonpayload-text-limit"):
        public_module._preflight_candidate(hostile_value, raw_nodes, raw_text)
    logger.debug("test_resource_preflights_run_before_deep_replay_json_parse_and_equality exit")


def _unrelated_lower_log() -> None:
    """Emit one unrelated-thread marker while the sibling filter is installed."""
    logger.debug("_unrelated_lower_log entry")
    logging.getLogger("src.core.proof_core_codec").warning("unrelated-thread-visible")
    logger.debug("_unrelated_lower_log exit")


def test_first_position_log_redaction_restores_filters_factory_and_concurrency(caplog) -> None:
    """Only the active replay thread is redacted and global logging state is restored."""
    logger.debug("test_first_position_log_redaction_restores_filters_factory_and_concurrency entry")
    lower = logging.getLogger("src.core.proof_core_codec")
    baseline_filters = tuple(lower.filters)
    baseline_factory = logging.getLogRecordFactory()
    caplog.set_level(logging.DEBUG)
    with protected_replay_logs():
        assert tuple(lower.filters)[1:] == baseline_filters
        lower.error("private-digest=%s", root("private-log-root"))
        thread = Thread(target=_unrelated_lower_log)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert tuple(lower.filters) == baseline_filters
    assert logging.getLogRecordFactory() is baseline_factory
    with pytest.raises(RuntimeError, match="boundary-control"):
        with protected_replay_logs():
            raise RuntimeError("boundary-control")
    assert tuple(lower.filters) == baseline_filters
    assert logging.getLogRecordFactory() is baseline_factory
    text = caplog.text
    assert root("private-log-root") not in text
    assert "p2 claim-admission replay event" in text
    assert "unrelated-thread-visible" in text

    case = composition_case()
    caplog.clear()
    value = _build(case, "log-control")
    assert validate_licensed_composition_presentation(value, *case)
    for secret in (
        value.judgment_digest,
        value.receipt.receipt_digest,
        *value.assumption_roots,
        *value.source_validator_roots,
        *(item.binding_digest for item in value.source_validation_bindings),
        value.license.license_digest,
        value.assessment.assessment_digest,
        value.promotion_schema_audit.audit_digest,
        value.schema_audit_report.report_digest,
    ):
        assert secret not in caplog.text
    assert tuple(lower.filters) == baseline_filters
    assert logging.getLogRecordFactory() is baseline_factory
    logger.debug("test_first_position_log_redaction_restores_filters_factory_and_concurrency exit")


def _concurrent_build(case):
    """Build one deterministic presentation in a worker thread."""
    logger.debug("_concurrent_build entry")
    result = _build(case, "concurrent-control")
    logger.debug("_concurrent_build exit")
    return result


def test_concurrent_public_replay_is_deterministic() -> None:
    """The redaction lock serializes sibling boundaries without changing output."""
    logger.debug("test_concurrent_public_replay_is_deterministic entry")
    case = composition_case()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = tuple(executor.map(_concurrent_build, (case,) * 8))
    assert len(set(results)) == 1
    logger.debug("test_concurrent_public_replay_is_deterministic exit")
