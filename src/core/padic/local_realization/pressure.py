"""Mandatory 25 executed hostile submissions for P3-N3/N4."""

from __future__ import annotations

from dataclasses import replace
import logging
from unittest.mock import patch

from ..completion.package import padic_completion_package
from ..completion.prime import prime_source
from ..family_introduction.package import n1_introduction_package
from ..family_introduction.sources import integer_source
from .bounded import (
    bounded_coordinate_equality_judgment, bounded_coordinate_equality_source,
    bounded_equality_request,
)
from .common import P3N3N4ValidationError
from .ledger import audit_exact_rows
from .runtime import (
    local_realization_judgment, scoped_carrier_equality_judgment,
)
from .requests import n3_request, n4_request
from .sources import (
    THEOREM_IDS, n3_dependency_union, n4_dependency_union, policy,
)
from .types import (
    BridgeDependencyRow, N34Refuted, N34ResourceLimit,
)
from .validation import validate_n3_result

logger = logging.getLogger(__name__)


def _rejected(call) -> bool:
    """Execute one hostile submission and require typed rejection."""
    logger.debug("_rejected entry")
    try:
        call()
    except (P3N3N4ValidationError, ValueError, TypeError, AttributeError):
        logger.debug("_rejected exit result=True")
        return True
    logger.debug("_rejected exit result=False")
    return False


def _different_n1(n1):
    """Build a canonical same-prime family that differs at coordinate zero."""
    logger.debug("_different_n1 entry")
    result = n1_introduction_package(n1.prime, integer_source(n1.integer.z + 1),
        n1.doctrine, n1.theorem_source, n1.ledger, n1.policy)
    logger.debug("_different_n1 exit")
    return result


def _mutate_dependency(rows, row_id: str, forbidden: str):
    """Remove one named dependency from one exact candidate row."""
    logger.debug("_mutate_dependency entry")
    result = tuple(replace(row, direct_dependencies=tuple(
        dep for dep in row.direct_dependencies if forbidden not in dep))
        if row.row_id == row_id else row for row in rows)
    logger.debug("_mutate_dependency exit")
    return result


def required_n34_attacks(n3, n4, n3_result, n4_result, refusal, bounded_open):
    """Execute and type-check all 25 required hostile or mutation submissions."""
    logger.debug("required_n34_attacks entry")
    del n4_result, refusal, bounded_open
    foreign_prime = prime_source(7 if n3.n1.prime.p != 7 else 5)
    foreign_n1 = n1_introduction_package(foreign_prime, n3.n1.integer,
        n3.n1.doctrine, n3.n1.theorem_source, n3.n1.ledger, n3.n1.policy)
    foreign_p2 = padic_completion_package(foreign_prime, n3.pomega2.doctrine,
        n3.pomega2.theorem_source, n3.pomega2.ledger, n3.pomega2.policy)
    bad_theorem = replace(n3.theorem, artifact_sha256="0" * 64)
    bad_policy = replace(n3.policy, policy_digest="0" * 64)
    bad_reduction = replace(n3.n1,
        doctrine=replace(n3.n1.doctrine, reduction_id="foreign-reduction"))
    bad_rho = replace(n4.all_depth, rho_definition_id="foreign-rho")
    opaque = replace(n4.all_depth, ordered_rows=())
    circular_row = replace(n4.all_depth.ordered_rows[-1],
        direct_dependencies=(n4.all_depth.ordered_rows[-1].row_id,))
    circular = replace(n4.all_depth,
        ordered_rows=(*n4.all_depth.ordered_rows[:-1], circular_row))
    copied_role = replace(n4.all_depth,
        right_realized_term_digest=n4.all_depth.left_realized_term_digest)
    n3_union = n3_dependency_union(n3.n1, n3.pomega2)
    n3_root = f"n3:own:{THEOREM_IDS[1]}"
    own1 = f"n3:own:{THEOREM_IDS[0]}"
    missing_rho = _mutate_dependency(n3_union.ordered_rows, own1, "veyraRho")
    missing_007 = _mutate_dependency(n3_union.ordered_rows, own1, "THM_POMEGA2_007")
    unused = (*n3_union.ordered_rows,
        BridgeDependencyRow("n3:hostile:unused", (), "0" * 64, ()))
    n4_rows = n4.all_depth.ordered_rows
    n4_union = n4_dependency_union(n4.left_n1, n4.right_n1,
                                   n4.pomega2, n4.all_depth)
    n4_root = f"n4:own:{THEOREM_IDS[2]}"
    missing_009 = _mutate_dependency(n4_union.ordered_rows, n4_root, "THM_POMEGA2_009")
    different = _different_n1(n3.n1)
    bounded_source = bounded_coordinate_equality_source(n3.n1, different, n3.pomega2, 4)
    bounded_request = bounded_equality_request(n3.n1, different, n3.pomega2, bounded_source)
    bounded_result = bounded_coordinate_equality_judgment(bounded_request)
    low = n3_request(n3.n1, n3.pomega2,
        execution_policy=policy(max_captured_bytes=1))

    def hard_first() -> bool:
        """Prove a low-cap call never touches dependency-union construction."""
        logger.debug("hard_first entry")
        with patch("src.core.padic_local_realization_runtime.n3_dependency_union",
                   side_effect=AssertionError("union touched")):
            result = local_realization_judgment(low)
        logger.debug("hard_first exit")
        return type(result) is N34ResourceLimit

    def oversized_result() -> bool:
        """Prove a 10k theorem envelope is rejected before semantic replay."""
        logger.debug("oversized_result entry")
        hostile = replace(n3_result, theorem_ids=("x",) * 10_000)
        with patch("src.core.padic_local_realization_validation.local_realization_judgment",
                   side_effect=AssertionError("replay touched")):
            result = _rejected(lambda: validate_n3_result(n3, hostile))
        logger.debug("oversized_result exit")
        return result

    rows = (
        ("n1-cross-prime-transplant", type(local_realization_judgment(
            n3_request(foreign_n1, n3.pomega2))) is N34Refuted),
        ("pomega2-cross-prime-transplant", type(local_realization_judgment(
            n3_request(n3.n1, foreign_p2))) is N34Refuted),
        ("same-name-different-source-bytes", _rejected(lambda: n3_request(
            n3.n1, n3.pomega2, bad_theorem))),
        ("finite-table-not-request", _rejected(lambda: local_realization_judgment(object()))),
        ("prior-result-not-request", _rejected(lambda: local_realization_judgment(n3_result))),
        ("prior-result-not-n1", _rejected(lambda: n3_request(n3_result, n3.pomega2))),
        ("prior-result-not-pomega2", _rejected(lambda: n3_request(n3.n1, n3_result))),
        ("n3-result-not-n4-request", _rejected(lambda: scoped_carrier_equality_judgment(n3_result))),
        ("role-digest-copy", _rejected(lambda: n4_request(n4.left_n1, n4.right_n1,
            n4.pomega2, copied_role))),
        ("policy-digest-transplant", _rejected(lambda: n3_request(
            n3.n1, n3.pomega2, execution_policy=bad_policy))),
        ("altered-reduction-definition", _rejected(lambda: n3_request(bad_reduction, n3.pomega2))),
        ("foreign-rho-definition", _rejected(lambda: n4_request(n4.left_n1, n4.right_n1,
            n4.pomega2, bad_rho))),
        ("missing-rho-edge", _rejected(lambda: audit_exact_rows(
            missing_rho, n3_union.ordered_rows, (n3_root,), "n3"))),
        ("unused-leaf-row", _rejected(lambda: audit_exact_rows(
            unused, n3_union.ordered_rows, (n3_root,), "n3"))),
        ("missing-thm007-edge", _rejected(lambda: audit_exact_rows(
            missing_007, n3_union.ordered_rows, (n3_root,), "n3"))),
        ("actual-bounded-mismatch", type(bounded_result) is N34Refuted),
        ("callback-not-premise", _rejected(lambda: n4_request(
            n4.left_n1, n4.right_n1, n4.pomega2, lambda _: True))),
        ("opaque-premise", _rejected(lambda: n4_request(
            n4.left_n1, n4.right_n1, n4.pomega2, opaque))),
        ("circular-premise", _rejected(lambda: n4_request(
            n4.left_n1, n4.right_n1, n4.pomega2, circular))),
        ("missing-thm009-edge", _rejected(lambda: audit_exact_rows(
            missing_009, n4_union.ordered_rows, (n4_root,), "n4"))),
        ("premise-row-transplant", _rejected(lambda: n4_request(
            n4.left_n1, n4.right_n1, n4.pomega2,
            replace(n4.all_depth, ordered_rows=n4_rows[:-1])))),
        ("hostile-union-arm", _rejected(lambda: scoped_carrier_equality_judgment(object()))),
        ("post-request-digest-mutation", _rejected(lambda: local_realization_judgment(
            replace(n3, request_digest="0" * 64)))),
        ("hard-first-resource", hard_first()),
        ("oversized-result-envelope", oversized_result()),
    )
    logger.debug("required_n34_attacks exit passed=%d/%d", sum(ok for _, ok in rows), len(rows))
    return rows
