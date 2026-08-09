"""Positive and boundary tests for isolated P3-N3/N4."""

from unittest.mock import patch

import pytest

from padic_local_realization_fixture import exact_n34_packages
from src.core.padic_local_realization import (
    EqualityStatus, N34Open, N3RealizationJudgment, N4EqualityJudgment,
    P3N3N4ValidationError,
    bounded_coordinate_equality_judgment, bounded_coordinate_equality_source,
    bounded_equality_request, local_realization_judgment,
    n3_dependency_union, n4_dependency_union, scoped_carrier_equality_judgment,
    validate_n4_result,
)

pytestmark = pytest.mark.requires_lean


@pytest.fixture(scope="module")
def established():
    n1, p2, n3, n4 = exact_n34_packages()
    return n1, p2, n3, n4, local_realization_judgment(n3), scoped_carrier_equality_judgment(n4)


def test_n3_exact_local_realization(established):
    *_, result, _ = established
    assert type(result) is N3RealizationJudgment
    assert result.promotions == 0
    assert len({result.family_term_digest, result.introduction_evidence_digest,
                result.realized_term_digest, result.coordinate_evidence_digest,
                result.judgment_digest}) == 5


def test_n4_exact_scoped_equality(established):
    *_, result = established
    assert type(result) is N4EqualityJudgment
    assert result.equality_status is EqualityStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert result.left_realized_term_digest != result.right_realized_term_digest
    assert result.promotions == 0


def test_minimal_n3_union_excludes_unused_pomega2(established):
    n1, p2, *_ = established
    ids = tuple(x.row_id for x in n3_dependency_union(n1, p2).ordered_rows)
    assert any("THM_POMEGA2_007" in x for x in ids)
    assert not any("THM_POMEGA2_006" in x or "THM_POMEGA2_008" in x for x in ids)


def test_minimal_n4_union_uses_thm009_and_owned_premise(established):
    n1, p2, _, n4, *_ = established
    ids = tuple(x.row_id for x in n4_dependency_union(n1, n1, p2, n4.all_depth).ordered_rows)
    assert any("THM_POMEGA2_009" in x for x in ids)
    assert any("THM_P3N4_PREMISE_001" in x for x in ids)
    assert not any("THM_POMEGA2_006" in x or "THM_POMEGA2_008" in x for x in ids)


@pytest.mark.parametrize("depth", [0, 1, 8, 64, 1024])
def test_bounded_coordinate_agreement_stays_open(established, depth):
    n1, p2, *_ = established
    source = bounded_coordinate_equality_source(n1, n1, p2, depth)
    result = bounded_coordinate_equality_judgment(
        bounded_equality_request(n1, n1, p2, source))
    assert type(result) is N34Open
    assert result.equality_status is EqualityStatus.NOT_ESTABLISHED


def test_all_depth_source_owns_exact_graph_and_toolchain(established):
    source = established[3].all_depth
    assert source.ordered_rows and source.theorem_axiom_closure == ("propext",)
    assert len(source.imports) == 3
    assert source.pomega2_package_digest == established[1].package_digest


def test_raw_packages_not_prior_judgments(established):
    n1, p2, n3, n4, *_ = established
    assert n3.n1 == n1 and n3.n1 is not n1
    assert n3.pomega2 == p2 and n3.pomega2 is not p2
    assert n4.left_n1 == n1 and n4.right_n1 == n1
    assert not hasattr(n3, "n1_judgment") and not hasattr(n4, "completion_judgment")


def test_n3_positive_is_rejected_as_n4_before_semantic_replay(established):
    *_, n4, n3_result, _ = established
    with patch("src.core.padic_local_realization_validation.scoped_carrier_equality_judgment",
               side_effect=AssertionError("semantic replay touched")):
        with pytest.raises(P3N3N4ValidationError, match="n4-result-cannot-be-n3-positive"):
            validate_n4_result(n4, n3_result)
