"""Fail-fast raw-input recomputation for P1-D3 family judgments."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_identifier, exact_shape, reject
from .formal import FormalFamilySource
from .sources import snapshot_family_source
from .spec import snapshot_family_spec
from .types import (
    AlgebraicLawStatus, AllDepthFamilyJudgment, AllDepthFamilySpec, AssumptionLedger,
    CompletedCarrierStatus, FamilyEvidenceStatus, FamilyHypothesis,
    FamilyIntroductionSource, FamilyProvenance,
    HigherStatus, LawStatus, LedgerStatus, OracleFamilyHypothesis,
)
from ...ontology.types import ObserverDoctrine
from ..productivity.types import ProductiveProcessSource

logger = logging.getLogger(__name__)


def _validate_exact_judgment(
    value: AllDepthFamilyJudgment, expected: AllDepthFamilyJudgment,
) -> AllDepthFamilyJudgment:
    logger.debug("_validate_exact_judgment entry")
    exact_shape(value, AllDepthFamilyJudgment, "all-depth-family-judgment")
    try:
        snapshot_family_spec(value.spec)
        if value.source is not None:
            if type(value.source) is not FamilyIntroductionSource:
                reject("family-judgment-source-must-be-exact")
            snapshot_family_source(value.source)
        exact_shape(value.algebraic_laws, AlgebraicLawStatus, "algebraic-law-status")
        enum_fields = (
            (value.spec_validity, LawStatus), (value.coordinate_totality, LawStatus),
            (value.restriction_compatibility, LawStatus),
            (value.evidence_status, FamilyEvidenceStatus),
            (value.ledger_status, LedgerStatus),
            (value.completed_carrier, CompletedCarrierStatus),
            (value.universal_realization, HigherStatus),
            (value.observer_separation, HigherStatus),
        )
        if any(type(actual) is not kind for actual, kind in enum_fields):
            reject("family-judgment-enum-lookalike")
        if value.provenance is not None and type(value.provenance) is not FamilyProvenance:
            reject("family-provenance-lookalike")
        for item in vars(value.algebraic_laws).values():
            if type(item) is not LawStatus:
                reject("algebraic-law-status-lookalike")
        for field in ("ledger_digest", "tcb_digest", "judgment_digest"):
            exact_digest(getattr(value, field), field.replace("_", "-"))
        exact_identifier(value.foundation_id, "foundation-id")
        if type(value.scope) is not str:
            reject("invalid-scope")
        for field in ("family_term_digest", "introduction_evidence_digest"):
            item = getattr(value, field)
            if item is not None:
                exact_digest(item, field.replace("_", "-"))
    except AttributeError:
        reject("all-depth-family-judgment-missing-fields")
    if type(value) is not type(expected) or value != expected:
        reject("all-depth-family-judgment-semantic-drift")
    if value.evidence_status is FamilyEvidenceStatus.OPEN:
        if any(item is not None for item in (
            value.source, value.provenance, value.family_term_digest,
            value.introduction_evidence_digest,
        )):
            reject("open-family-positive-payload")
    elif value.source is None or value.provenance is None:
        reject("positive-family-source-or-provenance-missing")
    logger.debug("_validate_exact_judgment exit")
    return expected


def validate_derived_family_judgment(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    d1_source: ProductiveProcessSource, formal_source: FormalFamilySource,
    ledger: AssumptionLedger, value: AllDepthFamilyJudgment,
) -> AllDepthFamilyJudgment:
    """Recompute from raw D1 and formal source; no earlier result is evidence."""
    logger.debug("validate_derived_family_judgment entry")
    from .runtime import _derive_periodic_family
    expected = _derive_periodic_family(doctrine, spec, d1_source, formal_source, ledger)
    result = _validate_exact_judgment(value, expected)
    logger.debug("validate_derived_family_judgment exit")
    return result


def validate_supplied_family_judgment(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: FamilyHypothesis, ledger: AssumptionLedger,
    value: AllDepthFamilyJudgment,
) -> AllDepthFamilyJudgment:
    """Freshly recompute the assumed supplied-family judgment."""
    logger.debug("validate_supplied_family_judgment entry")
    from .runtime import _admit_supplied_family
    expected = _admit_supplied_family(doctrine, spec, hypothesis, ledger)
    result = _validate_exact_judgment(value, expected)
    logger.debug("validate_supplied_family_judgment exit")
    return result


def validate_oracle_family_judgment(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: OracleFamilyHypothesis, ledger: AssumptionLedger,
    value: AllDepthFamilyJudgment,
) -> AllDepthFamilyJudgment:
    """Freshly recompute explicit oracle assumptions without querying them."""
    logger.debug("validate_oracle_family_judgment entry")
    from .runtime import _admit_oracle_family
    expected = _admit_oracle_family(doctrine, spec, hypothesis, ledger)
    result = _validate_exact_judgment(value, expected)
    logger.debug("validate_oracle_family_judgment exit")
    return result


def validate_open_family_judgment(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec, ledger: AssumptionLedger,
    value: AllDepthFamilyJudgment,
) -> AllDepthFamilyJudgment:
    """Freshly recompute valid evidence absence without inventing provenance."""
    logger.debug("validate_open_family_judgment entry")
    from .runtime import _open_family
    expected = _open_family(doctrine, spec, ledger)
    result = _validate_exact_judgment(value, expected)
    logger.debug("validate_open_family_judgment exit")
    return result
