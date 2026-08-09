"""Regression reproducers for the repaired unreleased P3-N6 trust boundary."""
from __future__ import annotations
from dataclasses import fields, replace
import importlib
import inspect
import logging
from pathlib import Path
import sys
import types
from typing import get_args
import pytest
logger = logging.getLogger(__name__)


def _repository_root() -> Path:
    """Directory holding `pyproject.toml`, found by walking upward."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("repository root not found")
def _modules():
    """Load the candidate without importing the aggregate public surface."""
    logger.debug("_modules entry")
    name = "p3n6_hardening_core"
    package = sys.modules.get(name)
    if package is None:
        package = types.ModuleType(name)
        package.__path__ = [str((_repository_root() / "src/core").resolve())]
        sys.modules[name] = package
    result = tuple(importlib.import_module(f"{name}.{module}") for module in (
        "padic.completion.core", "padic.family_introduction.core",
        "prime_power_unbounded_common", "prime_power_unbounded_sources",
        "prime_power_unbounded_types", "prime_power_unbounded_capability",
        "prime_power_unbounded_requests", "prime_power_unbounded_preflight",
        "prime_power_unbounded_results", "prime_power_unbounded_failures",
    ))
    logger.debug("_modules exit count=%d", len(result))
    return result
def _packages():
    """Build one fresh exact N1-zero/PΩ2 pair."""
    logger.debug("_packages entry")
    completion, family, *_ = _modules()
    prime = completion.prime_source(5)
    doctrine = completion.padic_tower_doctrine()
    p2 = completion.padic_completion_package(
        prime, doctrine, completion.padic_completion_theorem_source(),
        completion.padic_completion_ledger(), completion.padic_completion_policy(),
    )
    n1 = family.n1_introduction_package(
        prime, family.integer_source(0), doctrine, family.n1_theorem_source(),
        family.n1_assumption_ledger(), family.n1_policy(),
    )
    logger.debug("_packages exit")
    return n1, p2
def test_raw_defaults_are_inert_and_no_capability_issuer_is_importable() -> None:
    """Defaults do not hash early and no detached authority/materializer exists."""
    logger.debug("test_raw_defaults_are_inert_and_capability_is_not_forgeable_or_mutable entry")
    _, _, _, _, _, capability_module, requests, _, *_ = _modules()
    n1, p2 = _packages()
    assert not hasattr(requests, "theorem_source")
    assert not hasattr(requests, "policy")
    raw = requests.raw_e_request(n1, p2)
    assert raw.theorem is None and raw.policy is None
    assert not hasattr(capability_module, "_issue_capability")
    assert not hasattr(capability_module, "_N6EPrechargeCapability")
    assert not hasattr(requests, "_materialize_e_request")
    dispatcher = importlib.import_module(
        f"{requests.__package__}.prime_power_unbounded_dispatch"
    )
    assert dispatcher.dispatch_e_request.__closure__ is None
    logger.debug("test_raw_defaults_are_inert_and_capability_is_not_forgeable_or_mutable exit")
def test_no_detached_source_issuer_or_mutable_source_spec_exists() -> None:
    """The public parser has no closure cell or positive authority."""
    logger.debug("test_partial_source_open_closes_prior_fds_and_frozen_hash_is_enforced entry")
    _, _, _, _, _, capability_module, _, preflight, *_ = _modules()
    for name in (
        "_SOURCE_SPECS", "_PROJECT_ROOT", "_create_handle", "_handle_identity",
        "_open_project_root", "_open_fixed_source", "_open_fixed_sources",
    ):
        assert not hasattr(capability_module, name)
    assert not hasattr(preflight, "_precharged_dispatch")
    assert preflight.preflight_e_request.__closure__ is None
    logger.debug("test_partial_source_open_closes_prior_fds_and_frozen_hash_is_enforced exit")
def test_hostile_fake_dataclass_is_owned_malformed_not_code_execution() -> None:
    """A forged dataclass marker is rejected without iterating attacker state."""
    logger.debug("test_hostile_fake_dataclass_is_owned_malformed_not_code_execution entry")
    _, _, common, _, type_module, _, requests, preflight, *_ = _modules()
    n1, p2 = _packages()
    class BombFields:
        def __iter__(self):
            raise AssertionError("hostile-dataclass-fields-iteration-ran")
    class Attack:
        __dataclass_fields__ = BombFields()
    raw = requests.raw_e_request(replace(n1, prime=Attack()), p2)
    with pytest.raises(common.P3N6ValidationError, match="raw-type-invalid"):
        preflight.preflight_e_request(raw)
    callback_ran = False
    def bomb(_self):
        nonlocal callback_ran
        callback_ran = True
        raise AssertionError("mutated-class-property-ran")
    request_type = type_module.N6ERawRequestV1
    original = inspect.getattr_static(request_type, "n1_zero")
    trusted_raw = requests.raw_e_request(n1, p2)
    try:
        setattr(request_type, "n1_zero", property(bomb))
        with pytest.raises(common.P3N6ValidationError, match="descriptor-drift"):
            preflight.preflight_e_request(trusted_raw)
    finally:
        setattr(request_type, "n1_zero", original)
    assert callback_ran is False
    logger.debug("test_hostile_fake_dataclass_is_owned_malformed_not_code_execution exit")
def test_raw_bags_have_no_detached_callable_owner() -> None:
    """Raw validators cannot own positives; only request-bound e_result can."""
    logger.debug("test_empty_positive_cannot_be_sealed_or_owned entry")
    _, _, common, _, type_module, _, _, _, results, _ = _modules()
    adapter = results.PPEqualityAdapterRawV1(*(("",) * 8))
    evidence = results.PowerInjectionEvidenceRawV1(
        *("",) * 16, (), (), ""
    )
    judgment = results.PowerInjectionJudgmentRawV1(
        type_module.N6Kind.POWER_INJECTION_RELATIVE_TO_EXACT_POMEGA2,
        "", evidence, "", "", "", "", 0, (), "",
    )
    assert not hasattr(results, "_own_adapter")
    assert not hasattr(results, "_own_evidence")
    assert not hasattr(results, "_own_judgment")
    assert not hasattr(results, "_seal_derivation")
    with pytest.raises(common.P3N6ValidationError, match="digest-invalid"):
        results._validate_adapter(adapter)
    with pytest.raises(common.P3N6ValidationError, match="digest-invalid"):
        results._validate_evidence(evidence)
    with pytest.raises(common.P3N6ValidationError, match="digest-invalid"):
        results._validate_judgment(judgment, evidence)
    forged = object.__new__(results.PowerInjectionJudgmentV1)
    object.__setattr__(forged, "status", type_module.N6Status.ESTABLISHED)
    assert not hasattr(results, "validate_owned_adapter")
    assert not hasattr(results, "validate_owned_evidence")
    assert not hasattr(results, "validate_owned_power_injection_judgment")
    logger.debug("test_empty_positive_cannot_be_sealed_or_owned exit")
def test_formal_failure_toolchain_id_is_exact() -> None:
    """A nonpositive formal DTO cannot select an alternate toolchain."""
    logger.debug("test_formal_failure_toolchain_id_is_bounded entry")
    _, _, common, _, type_module, _, _, _, _, failures = _modules()
    formal = importlib.import_module(
        f"{failures.__package__}.prime_power_unbounded_formal_failures"
    )
    diagnostic = failures.N6SanitizedDiagnosticV1(
        type_module.N6DiagnosticCode.TIMEOUT, "0" * 64
    )
    with pytest.raises(common.P3N6ValidationError, match="execution-identity-invalid"):
        formal.N6EFormalFailureV1(
            type_module.N6FormalFailureKind.TIMEOUT,
            "0" * 64, "1" * 64, "alternate-toolchain", "2" * 64, "3" * 64,
            "4" * 64, diagnostic,
        )
    logger.debug("test_formal_failure_toolchain_id_is_bounded exit")
def test_hostile_exact_dataclass_and_judgment_fields_do_not_execute() -> None:
    """Trusted layouts never enumerate hostile maps or dereference alien evidence."""
    logger.debug("test_hostile_exact_dataclass_and_judgment_fields_do_not_execute entry")
    _, _, common, _, type_module, _, _, _, results, _ = _modules()
    n1, _p2 = _packages()
    class BombKey:
        def __hash__(self):
            return 1
        def __eq__(self, _other):
            raise AssertionError("hostile-key-equality-ran")
    damaged = replace(n1.policy)
    namespace = object.__getattribute__(damaged, "__dict__")
    namespace.clear()
    namespace[BombKey()] = "alien"
    layout = common.freeze_layout(
        type(n1.policy), tuple(field.name for field in fields(type(n1.policy)))
    )
    with pytest.raises(common.P3N6ValidationError, match="field-names|fields-missing"):
        common.exact_shape(damaged, layout, "hostile-policy")
    class BombEvidence:
        @property
        def evidence_digest(self):
            raise AssertionError("hostile-evidence-property-ran")
    bomb = BombEvidence()
    raw = results.PowerInjectionJudgmentRawV1(
        type_module.N6Kind.POWER_INJECTION_RELATIVE_TO_EXACT_POMEGA2,
        "0" * 64, bomb, "Nat", results.POWER_MAP_DEFINITION_ID,
        "carrier", "equality", 0, type_module.N6_NONCLAIMS, "1" * 64,
    )
    with pytest.raises(common.P3N6ValidationError, match="exact-type"):
        results._validate_judgment(raw, bomb)
    logger.debug("test_hostile_exact_dataclass_and_judgment_fields_do_not_execute exit")
@pytest.mark.requires_lean
def test_nonpositive_digests_subject_and_execution_identity_are_bound() -> None:
    """Supported results reconstruct deeply and bind one expected E request."""
    logger.debug("test_nonpositive_digests_subject_and_execution_identity_are_bound entry")
    _, _, common, sources, type_module, _, requests, _, _, failures = _modules()
    digests = importlib.import_module(
        f"{failures.__package__}.prime_power_unbounded_result_digests"
    )
    validation = importlib.import_module(
        f"{failures.__package__}.prime_power_unbounded_failure_validation"
    )
    formal = importlib.import_module(
        f"{failures.__package__}.prime_power_unbounded_formal_failures"
    )
    n1, p2 = _packages()
    request = requests.e_request(n1, p2)
    open_result = requests.e_result(request)
    assert validation.validate_e_result(open_result, request) == open_result
    alien_request_digest = "a" * 64
    alien_open = failures.N6EOpenV1(
        type_module.N6Status.OPEN,
        type_module.N6EOpenReason.MISSING_EXACT_EQUALITY_ADAPTER,
        type_module.N6GoalID.EXACT_EQUALITY_ADAPTER,
        alien_request_digest,
        digests.open_result_digest(
            type_module.N6Lane.E_POWER_INJECTION,
            type_module.N6EOpenReason.MISSING_EXACT_EQUALITY_ADAPTER.value,
            type_module.N6GoalID.EXACT_EQUALITY_ADAPTER,
            alien_request_digest,
        ),
    )
    with pytest.raises(common.P3N6ValidationError, match="supported-arm"):
        validation.validate_e_result(alien_open, request)
    partial = object.__new__(failures.N6EOpenV1)
    object.__setattr__(partial, "status", type_module.N6Status.OPEN)
    with pytest.raises(common.P3N6ValidationError, match="supported-arm"):
        validation.validate_e_result(partial, request)
    class UnsupportedRefuted:
        @property
        def counterexample(self):
            raise AssertionError("unsupported-nested-counterexample-ran")
    with pytest.raises(common.P3N6ValidationError, match="supported-arm"):
        validation.validate_e_result(UnsupportedRefuted(), request)
    request_digest = request.request_digest
    source_digest = request.theorem.source_digest
    diagnostic = failures.N6SanitizedDiagnosticV1(
        type_module.N6DiagnosticCode.TIMEOUT, "d" * 64
    )
    attempt = digests.formal_attempt_digest(
        type_module.N6Lane.E_POWER_INJECTION,
        type_module.N6FormalFailureKind.TIMEOUT, request_digest,
        source_digest, sources.TOOLCHAIN_ID, request.policy.policy_digest,
        "e" * 64, diagnostic.code.value, diagnostic.detail_digest,
    )
    failure = formal.N6EFormalFailureV1(
        type_module.N6FormalFailureKind.TIMEOUT, request_digest, source_digest,
        sources.TOOLCHAIN_ID, request.policy.policy_digest, "e" * 64,
        attempt, diagnostic,
    )
    with pytest.raises(common.P3N6ValidationError, match="replay-variant-mismatch"):
        validation.validate_e_result(failure, request)
    with pytest.raises(common.P3N6ValidationError, match="attempt-digest-drift"):
        replace(failure, attempt_digest="f" * 64)
    logger.debug("test_nonpositive_digests_subject_and_execution_identity_are_bound exit")
def test_w_missing_admission_is_typed_open_and_union_is_closed() -> None:
    """Missing CI is representable while alien receipts and lane collapse fail."""
    logger.debug("test_w_missing_admission_is_typed_open_and_union_is_closed entry")
    _, _, common, sources, type_module, _, requests, _, _, failures = _modules()
    validation = importlib.import_module(
        f"{failures.__package__}.prime_power_unbounded_failure_validation"
    )
    n1, p2 = _packages()
    request = requests.w_request(n1, p2)
    result = requests.w_result(request)
    assert result.status is type_module.N6Status.OPEN
    assert result.reason is type_module.N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION
    assert validation.validate_w_result(result, request) == result
    assert set(get_args(failures.N6WResultV1)) == {
        failures.N6WOpenV1,
        importlib.import_module(
            f"{failures.__package__}.prime_power_unbounded_formal_failures"
        ).N6WFormalFailureV1,
    }
    with pytest.raises(common.P3N6ValidationError, match="exact-type"):
        requests.w_request(n1, p2, object())
    receipt_values = (
        p2.doctrine.doctrine_digest,
        p2.doctrine.index_id,
        "candidate-foundation-v1",
        p2.package_digest,
        sources.theorem_source(type_module.N6Lane.W_INFORMATION_GROWTH).source_digest,
    )
    receipt = type_module.CompletedInfinityReceiptV1(
        *receipt_values,
        common.digest(
            "veyra.p3n6.ci-receipt.v1",
            tuple(
                (label, value.encode())
                for label, value in zip(
                    ("doctrine", "index", "foundation", "package", "source"),
                    receipt_values,
                    strict=True,
                )
            ),
        ),
    )
    some_request = requests.w_request(n1, p2, receipt)
    assert some_request.completed_infinity == receipt
    some_result = requests.w_result(some_request)
    assert some_result.kind is type_module.N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE
    assert validation.validate_w_result(some_result, some_request) == some_result
    logger.debug("test_w_missing_admission_is_typed_open_and_union_is_closed exit")
