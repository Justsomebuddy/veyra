"""Public exact surface for P1-D3 all-depth family introduction."""

from __future__ import annotations

import logging

from .common import AllDepthFamilyValidationError, reject
from .counterexample import (
    assess_family_law_counterexample, validate_family_law_counterexample_assessment,
)
from .counterexample import *  # noqa: F403
from .counterexample import (
    finite_family_law_witness, relation_edge, restriction_row,
)
from .formal import (
    ARTIFACT_NAME, ARTIFACT_SHA256, AXIOM_CLOSURE, LEAN_TCB_DIGEST,
    LEAN_TOOLCHAIN_ID, THEOREM_IDS, check_formal_source,
    periodic_family_formal_source,
)
from .hypotheses import (
    ORACLE_PURITY_HYPOTHESIS_ID, ORACLE_STABILITY_HYPOTHESIS_ID,
    ORACLE_TOTALITY_HYPOTHESIS_ID, SUPPLIED_COMPATIBILITY_LAW_ID,
    SUPPLIED_COORDINATE_LAW_ID, oracle_family_hypothesis,
    supplied_family_hypothesis,
)
from .ledger import (
    assumption_ledger, assumption_row, hypothesis_family_ledger,
    periodic_family_ledger,
)
from .projection import project_family_stage, validate_family_projection
from .result_validation import (
    validate_derived_family_judgment, validate_open_family_judgment,
    validate_oracle_family_judgment, validate_supplied_family_judgment,
)
from .runtime import (
    admit_oracle_family, admit_supplied_family, derive_periodic_family,
    open_all_depth_family,
)
from .spec import (
    ORACLE_CONSTRUCTOR_ID, PERIODIC_CONSTRUCTOR_ID, SUPPLIED_CONSTRUCTOR_ID,
    all_depth_family_spec, periodic_family_term, symbolic_family_term,
)
from .types import *  # noqa: F403
from .types import (
    AllDepthFamilySpec, AssumptionLedger, FamilyHypothesis, FormalFamilySource,
    OracleFamilyHypothesis,
)
from ...ontology.types import ObserverDoctrine
from ..productivity.types import ProductiveProcessSource

logger = logging.getLogger(__name__)


def replay_all_depth_family(
    doctrine: ObserverDoctrine, spec: AllDepthFamilySpec,
    raw_source: ProductiveProcessSource | FamilyHypothesis | OracleFamilyHypothesis | None,
    ledger: AssumptionLedger, formal_source: FormalFamilySource | None = None,
):
    """Dispatch only on raw exact source packages; never on an old judgment."""
    logger.debug("replay_all_depth_family entry type=%s", type(raw_source).__name__)
    if type(raw_source) is ProductiveProcessSource:
        if type(formal_source) is not FormalFamilySource:
            reject("derived-family-formal-source-required")
        result = derive_periodic_family(doctrine, spec, raw_source, formal_source, ledger)
    elif type(raw_source) is FamilyHypothesis:
        if formal_source is not None:
            reject("supplied-family-formal-source-forbidden")
        result = admit_supplied_family(doctrine, spec, raw_source, ledger)
    elif type(raw_source) is OracleFamilyHypothesis:
        if formal_source is not None:
            reject("oracle-family-formal-source-forbidden")
        result = admit_oracle_family(doctrine, spec, raw_source, ledger)
    elif raw_source is None:
        if formal_source is not None:
            reject("open-family-formal-source-forbidden")
        result = open_all_depth_family(doctrine, spec, ledger)
    else:
        reject("unsupported-all-depth-family-source")
    logger.debug("replay_all_depth_family exit status=%s", result.evidence_status.value)
    return result


__all__ = [
    "ARTIFACT_NAME", "ARTIFACT_SHA256", "AXIOM_CLOSURE",
    "AllDepthFamilyValidationError", "LEAN_TCB_DIGEST", "LEAN_TOOLCHAIN_ID",
    "ORACLE_CONSTRUCTOR_ID", "ORACLE_PURITY_HYPOTHESIS_ID",
    "ORACLE_STABILITY_HYPOTHESIS_ID", "ORACLE_TOTALITY_HYPOTHESIS_ID",
    "PERIODIC_CONSTRUCTOR_ID", "SUPPLIED_COMPATIBILITY_LAW_ID",
    "SUPPLIED_CONSTRUCTOR_ID", "SUPPLIED_COORDINATE_LAW_ID",
    "THEOREM_IDS", "admit_oracle_family", "admit_supplied_family",
    "all_depth_family_spec", "assess_family_law_counterexample",
    "assumption_ledger", "assumption_row", "finite_family_law_witness",
    "hypothesis_family_ledger",
    "check_formal_source", "derive_periodic_family", "open_all_depth_family",
    "oracle_family_hypothesis", "periodic_family_formal_source",
    "periodic_family_ledger", "periodic_family_term", "project_family_stage",
    "relation_edge", "replay_all_depth_family", "restriction_row",
    "supplied_family_hypothesis", "symbolic_family_term",
    "validate_derived_family_judgment",
    "validate_family_law_counterexample_assessment", "validate_family_projection",
    "validate_open_family_judgment", "validate_oracle_family_judgment",
    "validate_supplied_family_judgment",
]
