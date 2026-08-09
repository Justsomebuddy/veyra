"""Nested native-terminal shape regressions for isolated P3-N0."""

from dataclasses import replace
import pytest

from src.core.padic_family_introduction_types import (
    N1FailedBound, N1_NONCLAIMS, N1ResourceLimit, N1ResultStatus,
)
from src.core.prime_power_observer_actualization import N0ValidationError
from src.core.prime_power_observer_actualization_result_nested_validation import (
    validate_n2_positive_shape, validate_native_nested,
)
from src.core.prime_power_observer_actualization_result_validation import (
    _terminal_equal, _validate_relations,
)
from src.core.prime_power_reduction_network_runtime import prime_power_reduction_judgment
from src.core.prime_power_reduction_network_types import (
    FailedBound, FormalFailureKind, N2FormalFailure, N2ResourceLimit, ResultStatus,
)

from prime_power_observer_actualization_fixture import exact_p3n0_source

pytestmark = pytest.mark.requires_lean


class AlwaysEqual:
    def __eq__(self, _other): return True


class ExplodingEquality:
    def __eq__(self, _other): raise RuntimeError("hostile equality")


def test_n2_theorem_ids_and_outer_relations_are_exact():
    source = exact_p3n0_source()
    value = prime_power_reduction_judgment(source.strict_package.raw_package)
    hostile = replace(value, theorem_ids=(AlwaysEqual(), *value.theorem_ids[1:]))
    with pytest.raises(N0ValidationError, match="n0-nested-n2-theorem-0-text-invalid"):
        validate_n2_positive_shape(hostile)
    with pytest.raises(N0ValidationError, match="n0-result-strict-relation-text-invalid"):
        _validate_relations(AlwaysEqual(), "open")
    with pytest.raises(N0ValidationError, match="n0-result-equality-rejected-RuntimeError"):
        _terminal_equal(ExplodingEquality(), ExplodingEquality())


def test_nested_n2_resource_and_failure_scalars_are_exact():
    source = exact_p3n0_source()
    package = source.strict_package.raw_package.package_digest
    resource = N2ResourceLimit(
        ResultStatus.RESOURCE_LIMIT, FailedBound.CAPTURED_BYTES, True, 0,
        package, "0" * 64,
    )
    with pytest.raises(N0ValidationError, match="n0-nested-n2-resource-required-int-invalid"):
        validate_native_nested(source, resource)
    failure = N2FormalFailure(FormalFailureKind.TIMEOUT, package, 1, "0" * 64)
    with pytest.raises(N0ValidationError, match="n0-nested-n2-failure-diagnostic-text-invalid"):
        validate_native_nested(source, failure)


def test_nested_n1_foreign_validator_exception_is_normalized():
    source = exact_p3n0_source()
    package = source.n1_packages[0]
    resource = N1ResourceLimit(
        N1ResultStatus.RESOURCE_LIMIT, package.package_digest, package.policy.policy_digest,
        "0" * 64, N1FailedBound.STATIC_COST, True, 0, N1_NONCLAIMS, "0" * 64,
    )
    with pytest.raises(N0ValidationError, match="n0-nested-n1-terminal-validation-rejected"):
        validate_native_nested(source, resource)
