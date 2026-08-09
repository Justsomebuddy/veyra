"""Strict-review regressions for exact graphs, preflight, and bounded evidence."""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from padic_local_realization_fixture import exact_n34_packages
from src.core.padic_family_introduction import integer_source, n1_introduction_package
from src.core.padic_local_realization import (
    N34Open, N34Refuted, N34ResourceLimit, N34Status, N3Kind,
    N3RealizationJudgment, N34_NONCLAIMS, P3N3N4ValidationError,
    bounded_coordinate_equality_judgment, bounded_coordinate_equality_source,
    bounded_equality_request, n3_dependency_union, n3_request, policy,
    validate_bounded_result,
)
from src.core.padic_local_realization_formal import _read
from src.core.padic_local_realization_ledger import audit_exact_rows
from src.core.padic_local_realization_runtime import local_realization_judgment
from src.core.padic_local_realization_sources import (
    ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS,
)
from src.core.padic_local_realization_validation import validate_n3_result


def _different(n1):
    return n1_introduction_package(n1.prime, integer_source(n1.integer.z + 1),
        n1.doctrine, n1.theorem_source, n1.ledger, n1.policy)


def test_n3_schema_has_explicit_rho_and_rejects_missing_edges_or_unused_leaf():
    n1, p2, *_ = exact_n34_packages()
    union = n3_dependency_union(n1, p2)
    root = f"n3:own:{THEOREM_IDS[1]}"
    own1_id = f"n3:own:{THEOREM_IDS[0]}"
    own1 = next(row for row in union.ordered_rows if row.row_id == own1_id)
    assert any(dep.endswith("def:veyraRho") for dep in own1.direct_dependencies)
    for needle in ("veyraRho", "THM_POMEGA2_007"):
        rows = tuple(replace(row, direct_dependencies=tuple(
            dep for dep in row.direct_dependencies if needle not in dep))
            if row.row_id == own1_id else row for row in union.ordered_rows)
        with pytest.raises(P3N3N4ValidationError):
            audit_exact_rows(rows, union.ordered_rows, (root,), "n3")
    leaf = replace(union.ordered_rows[0], row_id="n3:hostile:unused")
    with pytest.raises(P3N3N4ValidationError):
        audit_exact_rows((*union.ordered_rows, leaf), union.ordered_rows, (root,), "n3")


def test_low_cap_refuses_before_dependency_union():
    n1, p2, *_ = exact_n34_packages()
    request = n3_request(n1, p2, execution_policy=policy(max_captured_bytes=1))
    with patch("src.core.padic_local_realization_runtime.n3_dependency_union",
               side_effect=AssertionError("union touched")):
        assert type(local_realization_judgment(request)) is N34ResourceLimit


def test_bounded_exact_agreement_open_and_mismatch_refuted_with_fresh_validation():
    n1, p2, *_ = exact_n34_packages()
    same_request = bounded_equality_request(n1, n1, p2,
        bounded_coordinate_equality_source(n1, n1, p2, 8))
    same = bounded_coordinate_equality_judgment(same_request)
    assert type(same) is N34Open
    replay = validate_bounded_result(same_request, same)
    assert replay == same and replay is not same
    other = _different(n1)
    different_request = bounded_equality_request(n1, other, p2,
        bounded_coordinate_equality_source(n1, other, p2, 8))
    different = bounded_coordinate_equality_judgment(different_request)
    assert type(different) is N34Refuted
    assert different.reason == "bounded-coordinate-mismatch-at-depth-0"


def test_bounded_resource_precedes_actual_mismatch():
    n1, p2, *_ = exact_n34_packages()
    other = _different(n1)
    source = bounded_coordinate_equality_source(n1, other, p2, 8)
    request = bounded_equality_request(n1, other, p2, source,
                                       policy(max_static_cost=1))
    assert type(bounded_coordinate_equality_judgment(request)) is N34ResourceLimit


def test_oversized_result_is_rejected_before_replay():
    _, _, n3, _ = exact_n34_packages()
    hostile = N3RealizationJudgment(N34Status.ESTABLISHED,
        N3Kind.LOCAL_REALIZATION_ESTABLISHED_RELATIVE_TO_EXACT_POMEGA2,
        *("0" * 64 for _ in range(8)), ("x",) * 10_000, ("propext",), 0,
        N34_NONCLAIMS, "0" * 64)
    with patch("src.core.padic_local_realization_validation.local_realization_judgment",
               side_effect=AssertionError("replay touched")):
        with pytest.raises(P3N3N4ValidationError):
            validate_n3_result(n3, hostile)


def test_formal_read_never_uses_unbounded_read_bytes():
    with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read")):
        assert len(_read(ARTIFACT_PATH, ARTIFACT_SHA256)) > 0
