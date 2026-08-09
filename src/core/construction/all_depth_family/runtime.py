"""AFIP judgment construction with source/proof/ledger separation."""

from __future__ import annotations

import logging

from .common import reject
from .digest import judgment_digest as make_judgment_digest
from .formal import FormalFamilySource
from .ledger import snapshot_assumption_ledger
from .sources import (
    derived_family_source, oracle_family_source, supplied_family_source,
)
from .spec import snapshot_family_spec
from .types import (
    AlgebraicLawStatus, AllDepthFamilyJudgment, AllDepthFamilySpec, AssumptionLedger,
    CompletedCarrierStatus, FamilyEvidenceStatus, FamilyHypothesis, FamilyProvenance,
    HigherStatus, LawStatus, LedgerStatus, OracleFamilyHypothesis,
)
from ...ontology.doctrine import snapshot_observer_doctrine
from ...ontology.types import ObserverDoctrine
from ..productivity.types import ProductiveProcessSource

logger = logging.getLogger(__name__)


def _laws(status: LawStatus = LawStatus.ESTABLISHED) -> AlgebraicLawStatus:
    logger.debug("_laws entry status=%s", status.value)
    result = AlgebraicLawStatus(*(status for _ in range(7)))
    logger.debug("_laws exit")
    return result


def _bind_doctrine(doctrine: ObserverDoctrine, spec: AllDepthFamilySpec) -> AllDepthFamilySpec:
    logger.debug("_bind_doctrine entry")
    doctrine = snapshot_observer_doctrine(doctrine)
    spec = snapshot_family_spec(spec)
    if (
        doctrine.version != spec.doctrine_version
        or doctrine.fingerprint != spec.doctrine_fingerprint
    ):
        reject("family-spec-doctrine-transplant")
    logger.debug("_bind_doctrine exit")
    return spec


def _judgment(
    spec: AllDepthFamilySpec, source, evidence: FamilyEvidenceStatus,
    provenance: FamilyProvenance | None, coordinate: LawStatus, compatibility: LawStatus,
    ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    logger.debug("_judgment entry evidence=%s", evidence.value)
    ledger = snapshot_assumption_ledger(ledger)
    family = None if source is None else source.term.family_term_digest
    intro = None if source is None else source.introduction_evidence_digest
    fields = (
        ("spec", spec.specification_digest.encode()),
        ("source", b"none" if source is None else source.source_digest.encode()),
        ("spec-status", LawStatus.ESTABLISHED.value.encode()),
        ("coordinate", coordinate.value.encode()), ("compatibility", compatibility.value.encode()),
        ("evidence", evidence.value.encode()),
        ("provenance", b"none" if provenance is None else provenance.value.encode()),
        ("ledger", ledger.ledger_digest.encode()), ("foundation", ledger.foundation_id.encode()),
        ("tcb", ledger.tcb_digest.encode()),
        ("family", b"none" if family is None else family.encode()),
        ("introduction", b"none" if intro is None else intro.encode()),
        ("completed-carrier", CompletedCarrierStatus.NOT_ESTABLISHED.value.encode()),
        ("universal-realization", HigherStatus.OPEN.value.encode()),
        ("observer-separation", HigherStatus.OPEN.value.encode()),
        ("scope", b"doctrine-ledger-relative-all-depth-family"),
    )
    result = AllDepthFamilyJudgment(
        spec, source, LawStatus.ESTABLISHED, coordinate, compatibility, _laws(),
        evidence, provenance, LedgerStatus.CLOSED, ledger.ledger_digest,
        ledger.foundation_id, ledger.tcb_digest, family, intro,
        make_judgment_digest(fields),
    )
    logger.debug("_judgment exit")
    return result


def _derive_periodic_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    d1_source: ProductiveProcessSource, formal_source: FormalFamilySource,
    ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    logger.debug("_derive_periodic_family entry")
    spec = _bind_doctrine(doctrine, spec)
    source = derived_family_source(spec, d1_source, formal_source, ledger)
    result = _judgment(
        spec, source, FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER,
        FamilyProvenance.FORMALLY_DERIVED, LawStatus.ESTABLISHED,
        LawStatus.ESTABLISHED, source.ledger,
    )
    logger.debug("_derive_periodic_family exit")
    return result


def derive_periodic_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    d1_source: ProductiveProcessSource, formal_source: FormalFamilySource,
    ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    """Derive, then freshly revalidate, the first extensional family judgment."""
    logger.debug("derive_periodic_family entry")
    candidate = _derive_periodic_family(doctrine, spec, d1_source, formal_source, ledger)
    from .result_validation import validate_derived_family_judgment
    result = validate_derived_family_judgment(
        doctrine, spec, d1_source, formal_source, ledger, candidate,
    )
    logger.debug("derive_periodic_family exit")
    return result


def _admit_supplied_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: FamilyHypothesis, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    logger.debug("_admit_supplied_family entry")
    spec = _bind_doctrine(doctrine, spec)
    source = supplied_family_source(spec, hypothesis, ledger)
    result = _judgment(
        spec, source, FamilyEvidenceStatus.ASSUMED, FamilyProvenance.SUPPLIED_HYPOTHESIS,
        LawStatus.ASSUMED, LawStatus.ASSUMED, source.ledger,
    )
    logger.debug("_admit_supplied_family exit")
    return result


def admit_supplied_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: FamilyHypothesis, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    """Admit an explicit supplied hypothesis without promoting it to established."""
    logger.debug("admit_supplied_family entry")
    candidate = _admit_supplied_family(doctrine, spec, hypothesis, ledger)
    from .result_validation import validate_supplied_family_judgment
    result = validate_supplied_family_judgment(doctrine, spec, hypothesis, ledger, candidate)
    logger.debug("admit_supplied_family exit")
    return result


def _admit_oracle_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: OracleFamilyHypothesis, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    logger.debug("_admit_oracle_family entry")
    spec = _bind_doctrine(doctrine, spec)
    source = oracle_family_source(spec, hypothesis, ledger)
    result = _judgment(
        spec, source, FamilyEvidenceStatus.ASSUMED, FamilyProvenance.ORACLE_DEPENDENT,
        LawStatus.ASSUMED, LawStatus.ASSUMED, source.ledger,
    )
    logger.debug("_admit_oracle_family exit")
    return result


def admit_oracle_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    hypothesis: OracleFamilyHypothesis, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    """Admit explicit total-oracle assumptions without querying the interface."""
    logger.debug("admit_oracle_family entry")
    candidate = _admit_oracle_family(doctrine, spec, hypothesis, ledger)
    from .result_validation import validate_oracle_family_judgment
    result = validate_oracle_family_judgment(doctrine, spec, hypothesis, ledger, candidate)
    logger.debug("admit_oracle_family exit")
    return result


def _open_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    logger.debug("_open_family entry")
    spec = _bind_doctrine(doctrine, spec)
    result = _judgment(
        spec, None, FamilyEvidenceStatus.OPEN, None,
        LawStatus.OPEN, LawStatus.OPEN, ledger,
    )
    logger.debug("_open_family exit")
    return result


def open_all_depth_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec, ledger: AssumptionLedger,
) -> AllDepthFamilyJudgment:
    """Represent valid missing evidence as OPEN with no provenance/source payload."""
    logger.debug("open_all_depth_family entry")
    candidate = _open_family(doctrine, spec, ledger)
    from .result_validation import validate_open_family_judgment
    result = validate_open_family_judgment(doctrine, spec, ledger, candidate)
    logger.debug("open_all_depth_family exit")
    return result
