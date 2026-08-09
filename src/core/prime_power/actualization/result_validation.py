"""Hostile-safe request-aware fresh terminal replay for isolated P3-N0."""

from __future__ import annotations

import logging

from ...padic.family_introduction.types import (
    N1FamilyJudgment, N1FormalFailure, N1ResourceLimit,
)
from .attestation import n0_theorem_source, validate_attestation
from .common import (
    N0ValidationError, exact_hex, exact_shape, reject,
)
from .nested_validation import (
    bounded_text, exact_bounded_int, exact_tuple, validate_attestation_shape,
    validate_bound_ledger_shape,
)
from .types import (
    N0DoctrineOpen, N0GenealogyUnavailable, N0UnavailableBridgeRequest,
)
from .outcomes import validate_bound_postbirth_ledger
from .result_nested_validation import (
    validate_native_nested, validate_positive_children,
)
from .runtime import prime_power_observer_actualization
from .sources import validate_n0_source
from .types import (
    ActualizationStatus, BoundaryStatus, FailedBound, FormalFailureKind,
    N0FormalFailure, N0Premises, N0ResourceLimit, N0Source, PremiseStatus,
    PrimePowerObserverActualizationJudgment, RoleStatus,
)
from .unavailable import (
    run_unavailable_bridge, validate_unavailable_request,
)
from ..reduction_network.types import (
    FiniteRelation, N2FormalFailure, N2ResourceLimit, PrimePowerReductionJudgment,
)

logger = logging.getLogger(__name__)


def _validate_relations(strict_relation, open_relation) -> None:
    """Validate the two exact released relation labels before child replay."""
    logger.debug("_validate_relations entry")
    bounded_text(strict_relation, "n0-result-strict-relation", maximum=128)
    bounded_text(open_relation, "n0-result-open-relation", maximum=128)
    if (strict_relation != FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE.value
            or open_relation != FiniteRelation.OPEN.value):
        reject("n0-result-relation-drift")
    logger.debug("_validate_relations exit")


def _terminal_equal(value, expected) -> bool:
    """Normalize hostile final terminal equality to the sole N0 exception."""
    logger.debug("_terminal_equal entry")
    try:
        result = type(value) is type(expected) and value == expected
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("_terminal_equal foreign equality rejection")
        reject(f"n0-result-equality-rejected-{type(exc).__name__}")
    logger.debug("_terminal_equal exit matched=%s", result)
    return result


def _bound_positive(source, value) -> None:
    """Bound all positive containers and nested evidence before fresh replay."""
    logger.debug("_bound_positive entry")
    raw = exact_shape(value, PrimePowerObserverActualizationJudgment, "n0-judgment")
    for name in (
        "run_digest", "rho_structural_id", "scope_digest", "birth_core_digest",
        "historical_token_id", "strict_history_digest", "open_history_digest",
        "strict_outcome_digest", "open_outcome_digest", "strict_efficacy_digest",
        "open_efficacy_digest", "judgment_digest",
    ):
        exact_hex(raw[name], f"n0-result-{name}")
    n1 = exact_tuple(raw["n1_results"], "n0-result-n1", maximum=3, length=3)
    n2 = exact_tuple(raw["n2_results"], "n0-result-n2", maximum=2, length=2)
    nonclaims = exact_tuple(raw["nonclaims"], "n0-result-nonclaims", maximum=32)
    premises = exact_shape(raw["premises"], N0Premises, "n0-result-premises")
    if (any(type(item) is not PremiseStatus for item in premises.values())
            or type(raw["role"]) is not RoleStatus
            or type(raw["actualization"]) is not ActualizationStatus
            or any(type(item) is not N1FamilyJudgment for item in n1)
            or any(type(item) is not PrimePowerReductionJudgment for item in n2)):
        reject("n0-result-child-envelope-invalid")
    for index, item in enumerate(nonclaims):
        bounded_text(item, f"n0-result-nonclaim-{index}", maximum=256)
    _validate_relations(raw["strict_relation"], raw["open_relation"])
    validate_bound_ledger_shape(raw["postbirth_evidence_ledger"])
    validate_attestation_shape(raw["formal_attestation"])
    if type(raw["promotions"]) is not int or raw["promotions"] != 0:
        reject("n0-result-promotion-forbidden")
    if (raw["generic_e4_bridge"] is not BoundaryStatus.OPEN
            or raw["physical_instantiation"] is not BoundaryStatus.NOT_ESTABLISHED
            or raw["consciousness"] is not BoundaryStatus.NOT_CLAIMED
            or raw["absolute_observerhood"] is not BoundaryStatus.NOT_CLAIMED):
        reject("n0-result-boundary-promotion-forbidden")
    validate_positive_children(source, n1, n2)
    bound = raw["postbirth_evidence_ledger"]
    if (bound.strict_outcome_digest != raw["strict_outcome_digest"]
            or bound.open_outcome_digest != raw["open_outcome_digest"]
            or bound.strict_efficacy_digest != raw["strict_efficacy_digest"]
            or bound.open_efficacy_digest != raw["open_efficacy_digest"]):
        reject("n0-result-bound-ledger-drift")
    validate_bound_postbirth_ledger(bound)
    validate_attestation(n0_theorem_source(), raw["formal_attestation"])
    logger.debug("_bound_positive exit")


def _bound_doctrine_open(value) -> None:
    """Validate the distinct NOT_ADMITTED terminal envelope."""
    logger.debug("_bound_doctrine_open entry")
    raw = exact_shape(value, N0DoctrineOpen, "n0-doctrine-open")
    for name in ("source_digest", "run_digest", "doctrine_digest", "result_digest"):
        exact_hex(raw[name], f"n0-doctrine-open-{name}")
    if (raw["genealogy"] is not PremiseStatus.ESTABLISHED
            or raw["role"] is not RoleStatus.OPEN
            or raw["actualization"] is not ActualizationStatus.OPEN):
        reject("n0-doctrine-open-status-drift")
    logger.debug("_bound_doctrine_open exit")


def _bound_unavailable(value) -> None:
    """Validate the disjoint genealogy-unavailable terminal envelope."""
    logger.debug("_bound_unavailable entry")
    raw = exact_shape(value, N0GenealogyUnavailable, "n0-genealogy-unavailable")
    for name in (
        "source_digest", "request_digest", "run_digest", "evidence_digest", "result_digest",
    ):
        exact_hex(raw[name], f"n0-genealogy-unavailable-{name}")
    if (raw["genealogy"] is not PremiseStatus.OPEN
            or raw["role"] is not RoleStatus.OPEN
            or raw["actualization"] is not ActualizationStatus.OPEN):
        reject("n0-genealogy-unavailable-status-drift")
    logger.debug("_bound_unavailable exit")


def _bound_resource(source, value) -> None:
    """Validate exact finite resource refusal fields and nested variant."""
    logger.debug("_bound_resource entry")
    raw = exact_shape(value, N0ResourceLimit, "n0-resource")
    for name in ("source_digest", "run_digest", "refusal_digest"):
        exact_hex(raw[name], f"n0-resource-{name}")
    if type(raw["failed_bound"]) is not FailedBound:
        reject("n0-resource-bound-invalid")
    exact_bounded_int(raw["required"], "n0-resource-required", maximum=2**63 - 1)
    exact_bounded_int(raw["allowed"], "n0-resource-allowed", maximum=2**63 - 1)
    if raw["nested_result"] is not None and type(raw["nested_result"]) not in (
            N1ResourceLimit, N2ResourceLimit):
        reject("n0-resource-nested-variant-invalid")
    if raw["nested_result"] is not None:
        validate_native_nested(source, raw["nested_result"])
    logger.debug("_bound_resource exit")


def _bound_failure(source, value) -> None:
    """Validate exact formal failure scalars without foreign exceptions."""
    logger.debug("_bound_failure entry")
    raw = exact_shape(value, N0FormalFailure, "n0-formal-failure")
    for name in ("source_digest", "run_digest", "attempt_digest"):
        exact_hex(raw[name], f"n0-failure-{name}")
    if type(raw["kind"]) is not FormalFailureKind:
        reject("n0-failure-kind-invalid")
    bounded_text(raw["diagnostic"], "n0-failure-diagnostic", maximum=256, empty=True)
    if raw["nested_result"] is not None and type(raw["nested_result"]) not in (
            N1FormalFailure, N2FormalFailure):
        reject("n0-failure-nested-variant-invalid")
    if raw["nested_result"] is not None:
        validate_native_nested(source, raw["nested_result"])
    logger.debug("_bound_failure exit")


def validate_n0_result(source_or_request, value):
    """Replay the matching available or unavailable source; reject terminal cross-casts."""
    logger.debug("validate_n0_result entry type=%s", type(value).__name__)
    request = None
    available_source = None
    if type(source_or_request) is N0UnavailableBridgeRequest:
        request = validate_unavailable_request(source_or_request)
        _bound_unavailable(value)
    elif type(source_or_request) is N0Source:
        source_or_request = validate_n0_source(source_or_request)
        available_source = source_or_request
        if type(value) is PrimePowerObserverActualizationJudgment:
            _bound_positive(source_or_request, value)
        elif type(value) is N0DoctrineOpen:
            _bound_doctrine_open(value)
        elif type(value) is N0ResourceLimit:
            _bound_resource(source_or_request, value)
        elif type(value) is N0FormalFailure:
            _bound_failure(source_or_request, value)
        else:
            reject("n0-available-result-variant-invalid")
    else:
        reject("n0-result-source-or-request-variant-invalid")
    try:
        expected = (run_unavailable_bridge(request) if request is not None
                    else prime_power_observer_actualization(available_source))
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("validate_n0_result foreign replay rejection")
        reject(f"n0-result-replay-rejected-{type(exc).__name__}")
    matches = _terminal_equal(value, expected)
    if not matches:
        reject("n0-result-fresh-replay-mismatch")
    logger.debug("validate_n0_result exit")
    return expected
