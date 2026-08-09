"""Level-1 certificate for AFIP's first exact periodic all-depth family."""

from __future__ import annotations

import logging

from ..construction.all_depth_family.core import (
    ORACLE_CONSTRUCTOR_ID, ORACLE_PURITY_HYPOTHESIS_ID,
    ORACLE_STABILITY_HYPOTHESIS_ID, ORACLE_TOTALITY_HYPOTHESIS_ID,
    SUPPLIED_COMPATIBILITY_LAW_ID, SUPPLIED_CONSTRUCTOR_ID,
    SUPPLIED_COORDINATE_LAW_ID, admit_oracle_family,
    admit_supplied_family, all_depth_family_spec, assess_family_law_counterexample,
    finite_family_law_witness, oracle_family_hypothesis,
    hypothesis_family_ledger, periodic_family_formal_source, periodic_family_ledger,
    project_family_stage, relation_edge, restriction_row,
    supplied_family_hypothesis, symbolic_family_term,
)
from ..construction.all_depth_family.counterexample import FamilyLaw, FamilyNonexistence
from ..construction.all_depth_family.runtime import derive_periodic_family, open_all_depth_family
from ..construction.all_depth_family.types import (
    CompletedCarrierStatus, FamilyEvidenceStatus, FamilyProjectionArtifact,
    FamilyProjectionRefusal, FamilyProvenance, LawStatus, ProjectionStatus,
)
from ..certify_types import Certificate
from ..construction.infinity_prefix import prefix_alphabet
from ..ontology.doctrine import p0_observer_doctrine
from ..construction.productivity.core import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    execution_policy, periodic_program, productive_process_source,
)

logger = logging.getLogger(__name__)


def _counterexample_witnesses():
    logger.debug("_counterexample_witnesses entry")
    result = (
        finite_family_law_witness(FamilyLaw.RELATION_REFLEXIVE, ("a",), (), (), ("a",)),
        finite_family_law_witness(
            FamilyLaw.RELATION_TRANSITIVE, ("a", "b", "c"),
            (relation_edge("a", "b"), relation_edge("b", "c")), (), ("a", "b", "c"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_CONGRUENCE, ("a", "b", "c", "d"),
            (relation_edge("a", "b"),),
            (restriction_row("r", "a", "c"), restriction_row("r", "b", "d")),
            ("r", "a", "b"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_IDENTITY, ("a", "b"),
            (relation_edge("a", "b"),), (restriction_row("id", "a", "b"),),
            ("id", "a"),
        ),
        finite_family_law_witness(
            FamilyLaw.RESTRICTION_COMPOSITION, ("a", "b", "c", "d"),
            (relation_edge("d", "c"),),
            (restriction_row("u", "a", "b"), restriction_row("l", "b", "c"),
             restriction_row("d", "a", "d")), ("u", "l", "d", "a"),
        ),
    )
    logger.debug("_counterexample_witnesses exit count=%d", len(result))
    return result


def certify_all_depth_family_p1d3() -> Certificate:
    """Certify derived/assumed/open lanes and operational identity separation."""
    logger.debug("certify_all_depth_family_p1d3 entry")
    doctrine = p0_observer_doctrine()
    alphabet = prefix_alphabet(("a", "b"))
    spec = all_depth_family_spec(doctrine, alphabet)
    ledger = periodic_family_ledger()
    program = periodic_program(alphabet, ("a", "b", "a"))
    p1 = execution_policy(8, 4096)
    p2 = execution_policy(16, 8192)
    d1 = productive_process_source(
        program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID, OUTPUT_ENCODING_ID, p1,
    )
    derived = derive_periodic_family(
        doctrine, spec, d1, periodic_family_formal_source(), ledger,
    )
    first = project_family_stage(derived.source, 6, p1)  # type: ignore[arg-type]
    second = project_family_stage(derived.source, 6, p2)  # type: ignore[arg-type]
    refusal = project_family_stage(derived.source, 9, p1)  # type: ignore[arg-type]
    supplied_term = symbolic_family_term(spec, SUPPLIED_CONSTRUCTOR_ID, b"F[n]:prefix")
    supplied_ledger = hypothesis_family_ledger(("H-supplied", SUPPLIED_COORDINATE_LAW_ID, SUPPLIED_COMPATIBILITY_LAW_ID))
    supplied_h = supplied_family_hypothesis(
        spec, supplied_term, "H-supplied", SUPPLIED_COORDINATE_LAW_ID,
        SUPPLIED_COMPATIBILITY_LAW_ID, supplied_ledger,
    )
    supplied = admit_supplied_family(doctrine, spec, supplied_h, supplied_ledger)
    unavailable = project_family_stage(supplied.source, 2, p1)  # type: ignore[arg-type]
    oracle_term = symbolic_family_term(spec, ORACLE_CONSTRUCTOR_ID, b"O[n]:prefix")
    oracle_ids = ("H-oracle", "oracle-v1", ORACLE_TOTALITY_HYPOTHESIS_ID,
                  ORACLE_PURITY_HYPOTHESIS_ID, ORACLE_STABILITY_HYPOTHESIS_ID, "trust-v1")
    oracle_ledger = hypothesis_family_ledger(oracle_ids)
    oracle_h = oracle_family_hypothesis(
        spec, oracle_term, *oracle_ids, oracle_ledger,
    )
    oracle = admit_oracle_family(doctrine, spec, oracle_h, oracle_ledger)
    opened = open_all_depth_family(doctrine, spec, ledger)
    counterexamples = tuple(
        assess_family_law_counterexample(spec, derived.source, witness)
        for witness in _counterexample_witnesses()
    )
    counterpressure = (
        len(counterexamples) == 5
        and all(row.affected_status is LawStatus.REFUTED for row in counterexamples)
        and all(row.family_evidence is FamilyEvidenceStatus.OPEN for row in counterexamples)
        and all(row.family_nonexistence is FamilyNonexistence.NOT_PROVED for row in counterexamples)
        and all(row.afip_introduction is False for row in counterexamples)
    )
    passed = (
        derived.evidence_status is FamilyEvidenceStatus.ESTABLISHED_RELATIVE_TO_LEDGER
        and derived.provenance is FamilyProvenance.FORMALLY_DERIVED
        and supplied.evidence_status is oracle.evidence_status is FamilyEvidenceStatus.ASSUMED
        and supplied.provenance is FamilyProvenance.SUPPLIED_HYPOTHESIS
        and oracle.provenance is FamilyProvenance.ORACLE_DEPENDENT
        and opened.evidence_status is FamilyEvidenceStatus.OPEN
        and opened.source is opened.provenance is opened.family_term_digest is None
        and isinstance(first, FamilyProjectionArtifact)
        and isinstance(second, FamilyProjectionArtifact)
        and first.family_term_digest == second.family_term_digest
        and first.introduction_evidence_digest == second.introduction_evidence_digest
        and first.policy_digest != second.policy_digest and first.run_digest != second.run_digest
        and isinstance(refusal, FamilyProjectionRefusal)
        and refusal.status is ProjectionStatus.RESOURCE_LIMIT
        and isinstance(unavailable, FamilyProjectionRefusal)
        and unavailable.status is ProjectionStatus.PROJECTION_UNAVAILABLE
        and counterpressure
        and all(row.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED for row in (
            derived, supplied, oracle, opened, first, second, refusal, unavailable,
        ))
    )
    result = Certificate(
        "all_depth_family_p1d3",
        "AFIP relative periodic family plus visibly assumed supplied/oracle lanes",
        passed,
        "derived=1 assumed=2 open=1 projections=2 resource=1 unavailable=1 "
        "countermodels=5 promotions=0",
        1,
    )
    logger.debug("certify_all_depth_family_p1d3 exit passed=%s", passed)
    return result
