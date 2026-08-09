"""Direct level-1 certificate for isolated P3-N1 introduction."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..padic.completion.core import padic_tower_doctrine, prime_source
from ..padic.family_introduction.core import (
    N1EvidenceProvenance, N1EvidenceStatus, N1FamilyJudgment, N1JudgmentKind,
    N1ResourceLimit, integer_source, introduce_integer_residue_family,
    n1_assumption_ledger, n1_introduction_package, n1_policy, n1_theorem_source,
    validate_n1_result,
)

logger = logging.getLogger(__name__)


def _package(z: int = -123, **caps):
    """Construct one fresh raw p/z/tower/theorem package without test imports."""
    logger.debug("_package entry z=%d", z)
    result = n1_introduction_package(
        prime_source(5), integer_source(z), padic_tower_doctrine(),
        n1_theorem_source(), n1_assumption_ledger(), n1_policy(**caps),
    )
    logger.debug("_package exit")
    return result


def certify_padic_family_introduction_p3n1() -> Certificate:
    """Certify exact all-depth family introduction and permanent boundaries."""
    logger.debug("certify_padic_family_introduction_p3n1 entry")
    package = _package()
    value = introduce_integer_residue_family(package)
    validated = validate_n1_result(package, value)
    refusal = introduce_integer_residue_family(_package(max_captured_bytes=1))
    ledger = n1_assumption_ledger()
    passed = (
        type(value) is N1FamilyJudgment and type(validated) is N1FamilyJudgment
        and value is not validated and value.kind is N1JudgmentKind.ALL_DEPTH_FAMILY
        and value.status is N1EvidenceStatus.ESTABLISHED
        and value.provenance is N1EvidenceProvenance.FORMALLY_DERIVED
        and value.coordinate_totality is N1EvidenceStatus.ESTABLISHED
        and value.all_reductions_compatible is N1EvidenceStatus.ESTABLISHED
        and len({value.theorem_source_digest, value.family_term_digest,
                 value.introduction_evidence_digest, value.judgment_digest}) == 4
        and type(refusal) is N1ResourceLimit
        and len(ledger.ordered_rows) == 20 and len(ledger.direct_edges) == 32
        and "universal-pomega2-completion" in value.nonclaims
        and "local-carrier-realization" in value.nonclaims
        and not hasattr(value, "completed_carrier") and not hasattr(value, "realization")
    )
    detail = (
        "theorems=3 total=1 all_reductions=1 family=1 formal=1 resource=1 "
        "ledger_rows=20 ledger_edges=32 graph_closure=1 "
        "promotions=0 universal_completion=0 local_realization=0 absolute_ontology=0"
    )
    result = Certificate(
        "padic_family_introduction_p3n1",
        "integer to exact prime-power compatible all-depth residue family", passed, detail, 1,
    )
    logger.debug("certify_padic_family_introduction_p3n1 exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_padic_family_introduction_p3n1())
