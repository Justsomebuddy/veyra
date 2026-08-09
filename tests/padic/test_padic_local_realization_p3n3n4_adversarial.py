"""All mandatory hostile/transplant attacks for P3-N3/N4."""

from padic_local_realization_fixture import exact_n34_packages
from src.core.padic_local_realization import (
    bounded_coordinate_equality_judgment, bounded_coordinate_equality_source,
    bounded_equality_request, local_realization_judgment, n3_request, policy,
    scoped_carrier_equality_judgment,
)
from src.core.padic_local_realization_pressure import required_n34_attacks
import pytest

pytestmark = pytest.mark.requires_lean


def test_all_25_required_attacks_pass():
    n1, p2, n3, n4 = exact_n34_packages()
    n3_result = local_realization_judgment(n3)
    n4_result = scoped_carrier_equality_judgment(n4)
    refusal = local_realization_judgment(n3_request(
        n1, p2, execution_policy=policy(max_captured_bytes=1)))
    bounded = bounded_coordinate_equality_judgment(bounded_equality_request(
        n1, n1, p2, bounded_coordinate_equality_source(n1, n1, p2, 64)))
    attacks = required_n34_attacks(n3, n4, n3_result, n4_result, refusal, bounded)
    assert len(attacks) == 25
    assert all(ok for _, ok in attacks), tuple(name for name, ok in attacks if not ok)
