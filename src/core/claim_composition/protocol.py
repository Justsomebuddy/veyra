"""Fail-closed construction, replay, and export for claim composition."""

from __future__ import annotations

from dataclasses import replace
import logging
from typing import NoReturn

from ..observer_discovery_v3.service import (
    GOVERNED_EVALUATION_READY,
    GovernedEvaluationResult,
    validate_governed_evaluation_result,
)
from ..observer_discovery_v3.dsl import ClosedEvaluationReceipt
from ..proof_core_codec import digest_data
from .types import (
    COMPOSITION_BOUNDARY,
    COMPOSITION_SCHEMA,
    AdaptiveCapability,
    ClaimClass,
    ClaimCompositionSource,
    ClaimContract,
    ClaimQuantifier,
    CompositionAssessment,
    CompositionLicense,
    CompositionReceipt,
    CompositionRule,
    CompositionSourceBinding,
    CompositionStatus,
    CorroborationStatus,
    LocalClaimReceipt,
    LocalReceiptValidity,
    PublicWording,
    SourceEffect,
)

logger = logging.getLogger(__name__)

MAX_COMPOSITION_SOURCES = 64
MAX_COMPOSITION_OUTPUT_UNITS = 2_000_000
MAX_ROOTS_PER_DIMENSION = 256
MAX_TOTAL_CONTRACT_ROOTS = 1024
_HEX = frozenset("0123456789abcdef")
_CONTRACT_DOMAIN = "veyra.claim-composition.contract.v1"
_LOCAL_RECEIPT_DOMAIN = "veyra.claim-composition.local-receipt.v1"
_LICENSE_DOMAIN = "veyra.claim-composition.license.v1"
_ASSESSMENT_DOMAIN = "veyra.claim-composition.assessment.v1"
_RECEIPT_DOMAIN = "veyra.claim-composition.receipt.v1"
_GOVERNED_SOURCE_VALIDATOR_ROOT = digest_data(
    {"schema": COMPOSITION_SCHEMA, "operation": "validate-governed-evaluation-result"},
    "veyra.claim-composition.source-validator.v1",
)


class ClaimCompositionError(ValueError):
    """Stable fail-closed composition construction or replay error."""

    def __init__(self, reason: str) -> None:
        logger.error("ClaimCompositionError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


def build_claim_contract(
    claim_roots: tuple[str, ...],
    scope_roots: tuple[str, ...],
    assumption_roots: tuple[str, ...],
    quantifier: ClaimQuantifier,
    observer_roots: tuple[str, ...],
    doctrine_roots: tuple[str, ...],
    execution_lineage_roots: tuple[str, ...],
    research_lineage_roots: tuple[str, ...],
    provenance_roots: tuple[str, ...],
    claim_classes: tuple[ClaimClass, ...],
    corroboration: CorroborationStatus,
    adaptive_capability: AdaptiveCapability,
    public_wording: PublicWording,
    *,
    component_contract_digests: tuple[str, ...] = (),
) -> ClaimContract:
    """Build one exact canonical contract without inferring missing bindings."""
    logger.debug("build_claim_contract entry")
    roots = {
        "component-contract-digests": _canonical_roots(
            component_contract_digests,
            allow_empty=True,
            reason="component-contract-digests",
        ),
        "claim-roots": _canonical_roots(claim_roots, allow_empty=False, reason="claim-roots"),
        "scope-roots": _canonical_roots(scope_roots, allow_empty=False, reason="scope-roots"),
        "assumption-roots": _canonical_roots(
            assumption_roots, allow_empty=True, reason="assumption-roots"
        ),
        "observer-roots": _canonical_roots(observer_roots, allow_empty=True, reason="observer-roots"),
        "doctrine-roots": _canonical_roots(doctrine_roots, allow_empty=True, reason="doctrine-roots"),
        "execution-lineage-roots": _canonical_roots(
            execution_lineage_roots,
            allow_empty=True,
            reason="execution-lineage-roots",
        ),
        "research-lineage-roots": _canonical_roots(
            research_lineage_roots,
            allow_empty=True,
            reason="research-lineage-roots",
        ),
        "provenance-roots": _canonical_roots(
            provenance_roots, allow_empty=True, reason="provenance-roots"
        ),
    }
    if sum(len(value) for value in roots.values()) > MAX_TOTAL_CONTRACT_ROOTS:
        _reject("contract-total-roots")
    classes = _canonical_claim_classes(claim_classes)
    if (
        type(quantifier) is not ClaimQuantifier
        or type(corroboration) is not CorroborationStatus
        or type(adaptive_capability) is not AdaptiveCapability
        or type(public_wording) is not PublicWording
    ):
        _reject("contract-enum")
    draft = ClaimContract(
        COMPOSITION_SCHEMA,
        roots["component-contract-digests"],
        roots["claim-roots"],
        roots["scope-roots"],
        roots["assumption-roots"],
        quantifier,
        roots["observer-roots"],
        roots["doctrine-roots"],
        roots["execution-lineage-roots"],
        roots["research-lineage-roots"],
        roots["provenance-roots"],
        classes,
        corroboration,
        adaptive_capability,
        public_wording,
        "",
    )
    result = replace(draft, contract_digest=digest_data(_contract_data(draft), _CONTRACT_DOMAIN))
    logger.debug("build_claim_contract exit digest=%s", result.contract_digest[:12])
    return result


def validate_claim_contract(value: object) -> bool:
    """Replay one contract's canonical shape, resource bounds, and digest."""
    logger.debug("validate_claim_contract entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is ClaimContract
            and value.schema_version == COMPOSITION_SCHEMA
            and build_claim_contract(
                value.claim_roots,
                value.scope_roots,
                value.assumption_roots,
                value.quantifier,
                value.observer_roots,
                value.doctrine_roots,
                value.execution_lineage_roots,
                value.research_lineage_roots,
                value.provenance_roots,
                value.claim_classes,
                value.corroboration,
                value.adaptive_capability,
                value.public_wording,
                component_contract_digests=value.component_contract_digests,
            )
            == value
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_claim_contract rejected")
        valid = False
    logger.debug("validate_claim_contract exit valid=%s", valid)
    return valid


def build_local_claim_receipt(
    contract: ClaimContract,
    source_receipt_root: str,
    source_validator_root: str,
    validity: LocalReceiptValidity,
) -> LocalClaimReceipt:
    """Bind an externally validated local receipt to its exact claim contract."""
    logger.debug("build_local_claim_receipt entry")
    if not validate_claim_contract(contract):
        _reject("local-contract")
    if not _is_local_source_contract(contract):
        _reject("aggregate-contract-local-reentry")
    if not _is_digest(source_receipt_root) or not _is_digest(source_validator_root):
        _reject("local-source-root")
    if type(validity) is not LocalReceiptValidity:
        _reject("local-validity")
    draft = LocalClaimReceipt(contract, source_receipt_root, source_validator_root, validity, "")
    result = replace(draft, receipt_digest=digest_data(_local_receipt_data(draft), _LOCAL_RECEIPT_DOMAIN))
    logger.debug("build_local_claim_receipt exit validity=%s", validity.value)
    return result


def _is_local_source_contract(contract: ClaimContract) -> bool:
    """Recognize the strict leaf profile admitted by a local receipt."""
    logger.debug("_is_local_source_contract entry")
    valid = (
        contract.quantifier is ClaimQuantifier.LOCAL
        and contract.component_contract_digests == ()
    )
    logger.debug("_is_local_source_contract exit valid=%s", valid)
    return valid


def validate_local_claim_receipt(value: object) -> bool:
    """Replay one local contract binding without replacing its external validator."""
    logger.debug("validate_local_claim_receipt entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is LocalClaimReceipt
            and build_local_claim_receipt(
                value.contract,
                value.source_receipt_root,
                value.source_validator_root,
                value.validity,
            )
            == value
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_local_claim_receipt rejected")
        valid = False
    logger.debug("validate_local_claim_receipt exit valid=%s", valid)
    return valid


def build_governed_composition_source(
    governed_result: GovernedEvaluationResult,
    effect: SourceEffect,
) -> ClaimCompositionSource:
    """Replay one governed result and derive its complete local contract."""
    logger.debug("build_governed_composition_source entry")
    if not validate_governed_evaluation_result(governed_result) or type(effect) is not SourceEffect:
        _reject("composition-source")
    reservation = governed_result.terminal_ledger.reservation
    worker_root = (
        governed_result.terminal_ledger.outcome_digest
        if governed_result.worker_receipt is None
        else governed_result.worker_receipt.result_digest
    )
    contract = build_claim_contract(
        (governed_result.result_digest,),
        tuple(
            sorted(
                {
                    reservation.parent_result,
                    reservation.test_commitment,
                    reservation.schema_digest,
                    reservation.evaluation_rows_digest,
                    reservation.confirmation_policy_digest,
                }
            )
        ),
        (),
        ClaimQuantifier.LOCAL,
        (governed_result.observer_program_digest,),
        (),
        tuple(
            sorted(
                {
                    governed_result.claimed_ledger.receipt_digest,
                    governed_result.terminal_ledger.receipt_digest,
                }
            )
        ),
        (),
        tuple(
            sorted(
                {
                    worker_root,
                    governed_result.claimed_ledger.capability_digest,
                    governed_result.claimed_ledger.attempt_digest,
                    governed_result.terminal_ledger.receipt_digest,
                }
            )
        ),
        (ClaimClass.STRUCTURAL,),
        CorroborationStatus.SINGLE_LOCAL_RECEIPT,
        AdaptiveCapability.LOCAL_ONLY,
        PublicWording.EVALUATION_COMPLETION,
    )
    validity = (
        LocalReceiptValidity.ESTABLISHED
        if governed_result.status == GOVERNED_EVALUATION_READY
        else LocalReceiptValidity.NOT_ESTABLISHED
    )
    receipt = build_local_claim_receipt(
        contract,
        governed_result.result_digest,
        _GOVERNED_SOURCE_VALIDATOR_ROOT,
        validity,
    )
    result = ClaimCompositionSource(governed_result, receipt, effect)
    logger.debug("build_governed_composition_source exit effect=%s", effect.value)
    return result


def build_external_composition_source(
    receipt: LocalClaimReceipt,
    effect: SourceEffect,
) -> ClaimCompositionSource:
    """Admit a local claim validated under its explicitly bound external validator root."""
    logger.debug("build_external_composition_source entry")
    if not validate_local_claim_receipt(receipt) or type(effect) is not SourceEffect:
        _reject("external-composition-source")
    result = ClaimCompositionSource(None, receipt, effect)
    logger.debug("build_external_composition_source exit effect=%s", effect.value)
    return result


def canonical_composition_sources(
    sources: tuple[ClaimCompositionSource, ...],
) -> tuple[ClaimCompositionSource, ...]:
    """Detach and sort a bounded receipt family by exact receipt digest."""
    logger.debug("canonical_composition_sources entry")
    if type(sources) is not tuple or not 1 <= len(sources) <= MAX_COMPOSITION_SOURCES:
        _reject("composition-source-count")
    _precharge_composition_outputs(sources)
    checked = tuple(_replay_composition_source(source) for source in sources)
    if len({source.receipt.receipt_digest for source in checked}) != len(checked):
        _reject("duplicate-composition-source")
    result = tuple(sorted(checked, key=lambda source: source.receipt.receipt_digest))
    logger.debug("canonical_composition_sources exit count=%d", len(result))
    return result


def _precharge_composition_outputs(sources: tuple[ClaimCompositionSource, ...]) -> None:
    """Bound occurrence-expanded worker outputs before repeated source replay."""
    logger.debug("_precharge_composition_outputs entry count=%d", len(sources))
    total = 0
    try:
        for source in sources:
            if type(source) is not ClaimCompositionSource:
                _reject("composition-source-type")
            if source.governed_result is None:
                continue
            if type(source.governed_result) is not GovernedEvaluationResult:
                _reject("composition-governed-source-type")
            worker = source.governed_result.worker_receipt
            if worker is None:
                continue
            if type(worker) is not ClosedEvaluationReceipt:
                _reject("composition-worker-receipt-type")
            if type(worker.outputs) is not tuple:
                _reject("composition-output-shape")
            for column in worker.outputs:
                if type(column) is not tuple:
                    _reject("composition-output-shape")
                stack: list[object] = list(column)
                while stack:
                    node = stack.pop()
                    total += 1
                    if total > MAX_COMPOSITION_OUTPUT_UNITS:
                        _reject("composition-output-units")
                    if type(node) is tuple:
                        stack.extend(node)
    except (AttributeError, OverflowError, TypeError) as exc:
        logger.error("_precharge_composition_outputs rejected type=%s", type(exc).__name__)
        raise ClaimCompositionError("composition-output-shape") from exc
    logger.debug("_precharge_composition_outputs exit units=%d", total)


def _replay_composition_source(source: ClaimCompositionSource) -> ClaimCompositionSource:
    """Replay either the governed adapter or an explicit external local-receipt binding."""
    logger.debug("_replay_composition_source entry")
    if type(source.effect) is not SourceEffect:
        _reject("composition-source-effect")
    if source.governed_result is None:
        result = build_external_composition_source(source.receipt, source.effect)
    elif type(source.governed_result) is GovernedEvaluationResult:
        result = build_governed_composition_source(source.governed_result, source.effect)
    else:
        _reject("composition-governed-source-type")
    if result != source:
        _reject("composition-source-binding")
    logger.debug("_replay_composition_source exit")
    return result


def build_exact_conjunction_contract(
    sources: tuple[ClaimCompositionSource, ...],
) -> ClaimContract:
    """Derive the flat N-ary target that preserves every local-leaf binding."""
    logger.debug("build_exact_conjunction_contract entry")
    checked = _checked_canonical_sources(sources, minimum=2)
    if any(source.effect is not SourceEffect.INCLUDE_LOCAL_CLAIM for source in checked):
        _reject("exact-conjunction-source-effect")
    result = build_claim_contract(
        _union_roots(checked, "claim_roots"),
        _union_roots(checked, "scope_roots"),
        _union_roots(checked, "assumption_roots"),
        ClaimQuantifier.FINITE_CONJUNCTION,
        _union_roots(checked, "observer_roots"),
        _union_roots(checked, "doctrine_roots"),
        _union_roots(checked, "execution_lineage_roots"),
        _union_roots(checked, "research_lineage_roots"),
        _union_roots(checked, "provenance_roots"),
        _union_claim_classes(checked),
        CorroborationStatus.MULTIPLE_LOCAL_RECEIPTS,
        AdaptiveCapability.LOCAL_ONLY,
        PublicWording.CONJUNCTIVE_SUMMARY,
        component_contract_digests=_component_contract_digests(checked),
    )
    logger.debug("build_exact_conjunction_contract exit digest=%s", result.contract_digest[:12])
    return result


def build_exact_conjunction_license(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
) -> CompositionLicense:
    """Issue the only v1 rule after exact target replay; no upgrade roots are accepted."""
    logger.debug("build_exact_conjunction_license entry")
    checked = _checked_canonical_sources(sources, minimum=2)
    if not validate_claim_contract(target):
        _reject("license-target")
    obstructions = _exact_conjunction_obstructions(checked, target)
    if obstructions:
        _reject(obstructions[0])
    bindings = tuple(
        CompositionSourceBinding(source.receipt.receipt_digest, source.effect) for source in checked
    )
    draft = CompositionLicense(
        COMPOSITION_SCHEMA,
        CompositionRule.EXACT_CONJUNCTION,
        bindings,
        target.contract_digest,
        (),
        "",
    )
    result = replace(draft, license_digest=digest_data(_license_data(draft), _LICENSE_DOMAIN))
    logger.debug("build_exact_conjunction_license exit digest=%s", result.license_digest[:12])
    return result


def validate_composition_license_shape(value: object) -> bool:
    """Validate a license's closed shape and digest without assuming its premises."""
    logger.debug("validate_composition_license_shape entry type=%s", type(value).__name__)
    try:
        valid = _composition_license_valid(value)
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_license_shape rejected")
        valid = False
    logger.debug("validate_composition_license_shape exit valid=%s", valid)
    return valid


def assess_claim_composition(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense | None,
) -> CompositionAssessment:
    """Compute the four independent issue-18 statuses and exact obstructions."""
    logger.debug("assess_claim_composition entry")
    checked = _checked_canonical_sources(sources, minimum=1)
    local_valid = all(source.receipt.validity is LocalReceiptValidity.ESTABLISHED for source in checked)
    target_valid = validate_claim_contract(target)
    obstructions: list[str] = []
    if not local_valid:
        obstructions.append("local-receipts-not-established")
    if not target_valid:
        obstructions.append("aggregate-claim-not-well-formed")

    license_valid = license is not None and validate_composition_license_shape(license)
    license_established = False
    if license is None:
        obstructions.append("composition-license-missing")
    elif not license_valid:
        obstructions.append("composition-license-invalid")
    elif target_valid:
        expected_bindings = tuple(
            CompositionSourceBinding(source.receipt.receipt_digest, source.effect) for source in checked
        )
        if license.sources != expected_bindings:
            obstructions.append("composition-license-source-mismatch")
        if license.target_contract_digest != target.contract_digest:
            obstructions.append("composition-license-target-mismatch")
        if license.capability_roots:
            obstructions.append("unexpected-capability-roots")
        if license.rule is CompositionRule.EXACT_CONJUNCTION:
            obstructions.extend(_exact_conjunction_obstructions(checked, target))
        license_established = not any(
            reason not in {"local-receipts-not-established"} for reason in obstructions
        )

    licensed = local_valid and target_valid and license_established
    source_digests = tuple(source.receipt.receipt_digest for source in checked)
    target_digest = target.contract_digest if _is_digest(getattr(target, "contract_digest", None)) else ""
    license_digest = license.license_digest if license_valid and license is not None else ""
    draft = CompositionAssessment(
        _status(local_valid),
        _status(target_valid),
        _status(license_established),
        _status(licensed),
        source_digests,
        target_digest,
        license_digest,
        tuple(dict.fromkeys(obstructions)),
        "",
    )
    result = replace(draft, assessment_digest=digest_data(_assessment_data(draft), _ASSESSMENT_DOMAIN))
    logger.info(
        "assess_claim_composition state local=%s well_formed=%s license=%s aggregate=%s",
        result.local_receipts_valid.value,
        result.aggregate_claim_well_formed.value,
        result.composition_license_established.value,
        result.aggregate_claim_licensed.value,
    )
    logger.debug("assess_claim_composition exit obstructions=%d", len(result.obstructions))
    return result


def validate_composition_assessment(
    value: object,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense | None,
) -> bool:
    """Replay a supplied assessment from its exact source family, target, and license."""
    logger.debug("validate_composition_assessment entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is CompositionAssessment
            and assess_claim_composition(sources, target, license) == value
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_assessment rejected")
        valid = False
    logger.debug("validate_composition_assessment exit valid=%s", valid)
    return valid


def build_composition_receipt(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> CompositionReceipt:
    """Build a receipt only when all four composition predicates replay as established."""
    logger.debug("build_composition_receipt entry")
    assessment = assess_claim_composition(sources, target, license)
    if assessment.aggregate_claim_licensed is not CompositionStatus.ESTABLISHED:
        _reject("aggregate-claim-not-licensed")
    draft = CompositionReceipt(
        COMPOSITION_SCHEMA,
        assessment.source_receipt_digests,
        target.contract_digest,
        license.license_digest,
        assessment.assessment_digest,
        False,
        "",
        COMPOSITION_BOUNDARY,
    )
    result = replace(draft, receipt_digest=digest_data(_composition_receipt_data(draft), _RECEIPT_DOMAIN))
    logger.info("build_composition_receipt state=LICENSED p2_promotion=False")
    logger.debug("build_composition_receipt exit digest=%s", result.receipt_digest[:12])
    return result


def validate_composition_receipt(
    value: object,
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
    license: CompositionLicense,
) -> bool:
    """Freshly replay a successful receipt and its permanent P2 nonpromotion bit."""
    logger.debug("validate_composition_receipt entry type=%s", type(value).__name__)
    try:
        valid = (
            type(value) is CompositionReceipt
            and value.p2_promotion_established is False
            and value.boundary == COMPOSITION_BOUNDARY
            and build_composition_receipt(sources, target, license) == value
        )
    except (AttributeError, ClaimCompositionError, TypeError, UnicodeError, ValueError):
        logger.error("validate_composition_receipt rejected")
        valid = False
    logger.debug("validate_composition_receipt exit valid=%s", valid)
    return valid


def _composition_license_valid(value: object) -> bool:
    logger.debug("_composition_license_valid entry")
    if (
        type(value) is not CompositionLicense
        or value.schema_version != COMPOSITION_SCHEMA
        or type(value.rule) is not CompositionRule
        or type(value.sources) is not tuple
        or not 1 <= len(value.sources) <= MAX_COMPOSITION_SOURCES
        or not _is_digest(value.target_contract_digest)
        or type(value.capability_roots) is not tuple
        or not _is_digest(value.license_digest)
    ):
        logger.debug("_composition_license_valid exit valid=False")
        return False
    source_rows = tuple(_validate_source_binding(binding) for binding in value.sources)
    if source_rows != value.sources or tuple(sorted(source_rows, key=lambda row: row.receipt_digest)) != source_rows:
        logger.debug("_composition_license_valid exit valid=False")
        return False
    if len({row.receipt_digest for row in source_rows}) != len(source_rows):
        logger.debug("_composition_license_valid exit valid=False")
        return False
    _canonical_roots(value.capability_roots, allow_empty=True, reason="capability-roots")
    expected = digest_data(_license_data(value), _LICENSE_DOMAIN)
    valid: bool = value.license_digest == expected
    logger.debug("_composition_license_valid exit valid=%s", valid)
    return valid


def _validate_source_binding(value: object) -> CompositionSourceBinding:
    logger.debug("_validate_source_binding entry type=%s", type(value).__name__)
    if (
        type(value) is not CompositionSourceBinding
        or not _is_digest(value.receipt_digest)
        or type(value.effect) is not SourceEffect
    ):
        _reject("license-source-binding")
    logger.debug("_validate_source_binding exit")
    return value


def _checked_canonical_sources(
    sources: object,
    *,
    minimum: int,
) -> tuple[ClaimCompositionSource, ...]:
    logger.debug("_checked_canonical_sources entry minimum=%d", minimum)
    if type(sources) is not tuple or not minimum <= len(sources) <= MAX_COMPOSITION_SOURCES:
        _reject("composition-source-count")
    checked = canonical_composition_sources(sources)
    if checked != sources:
        _reject("noncanonical-composition-sources")
    logger.debug("_checked_canonical_sources exit count=%d", len(checked))
    return checked


def _exact_conjunction_obstructions(
    sources: tuple[ClaimCompositionSource, ...],
    target: ClaimContract,
) -> tuple[str, ...]:
    logger.debug("_exact_conjunction_obstructions entry")
    reasons: list[str] = []
    if len(sources) < 2:
        reasons.append("exact-conjunction-needs-two-sources")
    if any(source.effect is not SourceEffect.INCLUDE_LOCAL_CLAIM for source in sources):
        reasons.append("source-effect-not-local-claim-inclusion")
    comparisons = (
        (target.claim_roots, _union_roots(sources, "claim_roots"), "claim-roots-not-exact-union"),
        (
            target.component_contract_digests,
            _component_contract_digests(sources),
            "component-contracts-not-exact",
        ),
        (target.scope_roots, _union_roots(sources, "scope_roots"), "scope-not-exact-union"),
        (
            target.assumption_roots,
            _union_roots(sources, "assumption_roots"),
            "assumptions-not-exact-union",
        ),
        (
            target.observer_roots,
            _union_roots(sources, "observer_roots"),
            "observer-binding-not-exact-union",
        ),
        (
            target.doctrine_roots,
            _union_roots(sources, "doctrine_roots"),
            "doctrine-binding-not-exact-union",
        ),
        (
            target.execution_lineage_roots,
            _union_roots(sources, "execution_lineage_roots"),
            "execution-lineage-not-exact-union",
        ),
        (
            target.research_lineage_roots,
            _union_roots(sources, "research_lineage_roots"),
            "research-lineage-not-exact-union",
        ),
        (
            target.provenance_roots,
            _union_roots(sources, "provenance_roots"),
            "provenance-binding-not-exact-union",
        ),
        (
            target.claim_classes,
            _union_claim_classes(sources),
            "claim-class-reinterpretation",
        ),
    )
    reasons.extend(reason for actual, expected, reason in comparisons if actual != expected)
    if target.quantifier is not ClaimQuantifier.FINITE_CONJUNCTION:
        reasons.append("quantifier-upgrade")
    if target.corroboration is not CorroborationStatus.MULTIPLE_LOCAL_RECEIPTS:
        reasons.append("corroboration-upgrade")
    if target.adaptive_capability is not AdaptiveCapability.LOCAL_ONLY:
        reasons.append("adaptive-capability-upgrade")
    if target.public_wording is not PublicWording.CONJUNCTIVE_SUMMARY:
        reasons.append("public-wording-upgrade")
    result = tuple(reasons)
    logger.debug("_exact_conjunction_obstructions exit count=%d", len(result))
    return result


def _canonical_roots(value: object, *, allow_empty: bool, reason: str) -> tuple[str, ...]:
    logger.debug("_canonical_roots entry reason=%s", reason)
    if (
        type(value) is not tuple
        or len(value) > MAX_ROOTS_PER_DIMENSION
        or (not allow_empty and not value)
        or any(not _is_digest(item) for item in value)
        or tuple(sorted(set(value))) != value
    ):
        _reject(reason)
    logger.debug("_canonical_roots exit count=%d", len(value))
    return value


def _canonical_claim_classes(value: object) -> tuple[ClaimClass, ...]:
    logger.debug("_canonical_claim_classes entry")
    if (
        type(value) is not tuple
        or not 1 <= len(value) <= len(ClaimClass)
        or any(type(item) is not ClaimClass for item in value)
        or tuple(sorted(set(value), key=lambda item: item.value)) != value
    ):
        _reject("claim-classes")
    logger.debug("_canonical_claim_classes exit count=%d", len(value))
    return value


def _union_roots(
    sources: tuple[ClaimCompositionSource, ...],
    field: str,
) -> tuple[str, ...]:
    logger.debug("_union_roots entry field=%s", field)
    result = tuple(sorted({root for source in sources for root in getattr(source.receipt.contract, field)}))
    logger.debug("_union_roots exit count=%d", len(result))
    return result


def _component_contract_digests(
    sources: tuple[ClaimCompositionSource, ...],
) -> tuple[str, ...]:
    """Return the canonical unique semantic-contract set for a source family."""
    logger.debug("_component_contract_digests entry count=%d", len(sources))
    result = tuple(sorted({source.receipt.contract.contract_digest for source in sources}))
    logger.debug("_component_contract_digests exit count=%d", len(result))
    return result


def _union_claim_classes(
    sources: tuple[ClaimCompositionSource, ...],
) -> tuple[ClaimClass, ...]:
    logger.debug("_union_claim_classes entry")
    result = tuple(
        sorted(
            {claim_class for source in sources for claim_class in source.receipt.contract.claim_classes},
            key=lambda item: item.value,
        )
    )
    logger.debug("_union_claim_classes exit count=%d", len(result))
    return result


def _status(value: bool) -> CompositionStatus:
    logger.debug("_status entry value=%s", value)
    result = CompositionStatus.ESTABLISHED if value else CompositionStatus.NOT_ESTABLISHED
    logger.debug("_status exit status=%s", result.value)
    return result


def _is_digest(value: object) -> bool:
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    valid = type(value) is str and len(value) == 64 and all(character in _HEX for character in value)
    logger.debug("_is_digest exit valid=%s", valid)
    return valid


def _contract_data(contract: ClaimContract) -> dict[str, object]:
    logger.debug("_contract_data entry")
    result: dict[str, object] = {
        "schema_version": contract.schema_version,
        "component_contract_digests": list(contract.component_contract_digests),
        "claim_roots": list(contract.claim_roots),
        "scope_roots": list(contract.scope_roots),
        "assumption_roots": list(contract.assumption_roots),
        "quantifier": contract.quantifier.value,
        "observer_roots": list(contract.observer_roots),
        "doctrine_roots": list(contract.doctrine_roots),
        "execution_lineage_roots": list(contract.execution_lineage_roots),
        "research_lineage_roots": list(contract.research_lineage_roots),
        "provenance_roots": list(contract.provenance_roots),
        "claim_classes": [value.value for value in contract.claim_classes],
        "corroboration": contract.corroboration.value,
        "adaptive_capability": contract.adaptive_capability.value,
        "public_wording": contract.public_wording.value,
    }
    logger.debug("_contract_data exit")
    return result


def _local_receipt_data(receipt: LocalClaimReceipt) -> dict[str, object]:
    logger.debug("_local_receipt_data entry")
    result: dict[str, object] = {
        "contract_digest": receipt.contract.contract_digest,
        "source_receipt_root": receipt.source_receipt_root,
        "source_validator_root": receipt.source_validator_root,
        "validity": receipt.validity.value,
    }
    logger.debug("_local_receipt_data exit")
    return result


def _license_data(license: CompositionLicense) -> dict[str, object]:
    logger.debug("_license_data entry")
    result: dict[str, object] = {
        "schema_version": license.schema_version,
        "rule": license.rule.value,
        "sources": [
            {"receipt_digest": source.receipt_digest, "effect": source.effect.value}
            for source in license.sources
        ],
        "target_contract_digest": license.target_contract_digest,
        "capability_roots": list(license.capability_roots),
    }
    logger.debug("_license_data exit")
    return result


def _assessment_data(assessment: CompositionAssessment) -> dict[str, object]:
    logger.debug("_assessment_data entry")
    result: dict[str, object] = {
        "local_receipts_valid": assessment.local_receipts_valid.value,
        "aggregate_claim_well_formed": assessment.aggregate_claim_well_formed.value,
        "composition_license_established": assessment.composition_license_established.value,
        "aggregate_claim_licensed": assessment.aggregate_claim_licensed.value,
        "source_receipt_digests": list(assessment.source_receipt_digests),
        "target_contract_digest": assessment.target_contract_digest,
        "license_digest": assessment.license_digest,
        "obstructions": list(assessment.obstructions),
    }
    logger.debug("_assessment_data exit")
    return result


def _composition_receipt_data(receipt: CompositionReceipt) -> dict[str, object]:
    logger.debug("_composition_receipt_data entry")
    result: dict[str, object] = {
        "schema_version": receipt.schema_version,
        "source_receipt_digests": list(receipt.source_receipt_digests),
        "target_contract_digest": receipt.target_contract_digest,
        "license_digest": receipt.license_digest,
        "assessment_digest": receipt.assessment_digest,
        "p2_promotion_established": receipt.p2_promotion_established,
        "boundary": receipt.boundary,
    }
    logger.debug("_composition_receipt_data exit")
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("claim composition rejected reason=%s", reason)
    raise ClaimCompositionError(reason)
