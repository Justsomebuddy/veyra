"""Level-1 certificate for the five closed P1-D2 inference audits."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..construction.productivity.counterpressure import (
    counterpressure_alphabet, counterpressure_basis_source, counterpressure_result,
    decreasing_tree_request, ledger_request, long_run_request,
    shrinking_stage_request, target_chooser_request,
)
from ..construction.productivity.counterpressure import (
    AllDepthFamilyStatus, BasisUse, CompletedCarrierStatus,
    CounterpressureCertificate, CounterpressureInference,
    CounterpressureOutcomeKind, CounterpressureStatus, GeneratorNonexistence,
    HistoricalTargetIndependence, LedgerRow,
)

logger = logging.getLogger(__name__)


def certify_productivity_counterpressure() -> Certificate:
    """Certify two insufficiency rows and three exact countermodels only."""
    logger.debug("certify_productivity_counterpressure entry")
    basis = counterpressure_basis_source()
    requests = (
        ledger_request((LedgerRow(2, "w2", "s2"), LedgerRow(5, "w5", "s5"))),
        decreasing_tree_request(5, basis),
        target_chooser_request(counterpressure_alphabet(("a", "b")), ("a", "b", "a")),
        long_run_request(1_000_000),
        shrinking_stage_request(7, basis),
    )
    results = tuple(counterpressure_result(request) for request in requests)
    certificates = tuple(
        value for value in results if type(value) is CounterpressureCertificate
    )
    insufficiencies = sum(
        value.outcome_kind is CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY
        and value.status is CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
        for value in certificates
    )
    countermodels = sum(
        value.outcome_kind is CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL
        and value.status is CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        for value in certificates
    )
    expected_rows = (
        (
            CounterpressureInference.LEDGER_GENERATOR,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH, BasisUse.NONE,
        ),
        (
            CounterpressureInference.FINITE_DEPTH_BRANCH,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION, BasisUse.BOUND,
        ),
        (
            CounterpressureInference.POSTHOC_INDEPENDENCE,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION, BasisUse.NONE,
        ),
        (
            CounterpressureInference.LONG_RUN_FAMILY,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH, BasisUse.NONE,
        ),
        (
            CounterpressureInference.NESTED_COMMON_POINT,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION, BasisUse.BOUND,
        ),
    )
    exact_catalog = len(certificates) == len(expected_rows) and all(
        value.inference_id is expected[0]
        and value.outcome_kind is expected[1]
        and value.status is expected[2]
        and value.basis_use is expected[3]
        for value, expected in zip(certificates, expected_rows, strict=True)
    )
    exact_basis_rows = tuple(value.basis_digest for value in certificates) == (
        None, basis.basis_digest, None, None, basis.basis_digest,
    )
    lean_countermodels = sum(
        value.outcome_kind is CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL
        and value.basis_use is BasisUse.BOUND
        and value.basis_digest == basis.basis_digest
        for value in certificates
    )
    structural_chooser = sum(
        value.inference_id is CounterpressureInference.POSTHOC_INDEPENDENCE
        and value.outcome_kind is CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL
        and value.status is CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        and value.basis_use is BasisUse.NONE and value.basis_digest is None
        for value in certificates
    )
    permanent = all(
        value.generator_nonexistence is GeneratorNonexistence.NOT_PROVED
        and value.all_depth_family is AllDepthFamilyStatus.OPEN
        and value.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
        and value.historical_target_independence
        is HistoricalTargetIndependence.NOT_ESTABLISHED
        and value.scope == "counterpressure-only"
        for value in certificates
    )
    passed = (
        len(certificates) == 5 and insufficiencies == 2 and countermodels == 3
        and exact_catalog and exact_basis_rows
        and lean_countermodels == 2 and structural_chooser == 1 and permanent
    )
    detail = (
        f"rows={len(certificates)}/5 insufficiency={insufficiencies}/2 "
        f"countermodels={countermodels}/3 lean_countermodels={lean_countermodels}/2 "
        f"structural_chooser={structural_chooser}/1 promotions=0"
    )
    result = Certificate(
        "productivity_counterpressure_p1d2",
        "finite evidence insufficiency and exact foundation-relative countermodels",
        passed, detail, 1,
    )
    logger.debug("certify_productivity_counterpressure exit passed=%s", passed)
    return result
