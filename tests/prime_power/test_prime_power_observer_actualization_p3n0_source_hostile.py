"""Strict hostile source-envelope regressions for isolated P3-N0."""

from dataclasses import replace

import pytest

from src.core.prime_power_observer_actualization import N0History, N0ValidationError
from src.core.prime_power_observer_actualization_history import replay_evidence
from src.core.prime_power_observer_actualization_history_validation import audit_history

from prime_power_observer_actualization_fixture import exact_p3n0_source


class AlwaysEqual:
    def __eq__(self, _other): return True


def test_public_paths_validate_source_before_nested_dereference():
    source = exact_p3n0_source()
    bad_doctrine = replace(source, doctrine=1)
    with pytest.raises(N0ValidationError, match="n0-source-child-envelope-invalid"):
        audit_history(bad_doctrine, object())
    with pytest.raises(N0ValidationError, match="n0-source-child-envelope-invalid"):
        replay_evidence(bad_doctrine, object(), object(), object(), object())
    bad_scope = replace(source, scope=1)
    with pytest.raises(N0ValidationError, match="n0-source-child-envelope-invalid"):
        audit_history(bad_scope, object())
    bad_digest = replace(source, doctrine=replace(
        source.doctrine, doctrine_digest=AlwaysEqual(),
    ))
    with pytest.raises(N0ValidationError, match="n0-source-doctrine-digest-digest-invalid"):
        audit_history(bad_digest, object())
    bad_arrow = replace(source, scope=replace(
        source.scope, arrow=(AlwaysEqual(), source.depth),
    ))
    with pytest.raises(N0ValidationError, match="source-scope-arrow-0-exact-type-drift"):
        audit_history(bad_arrow, object())


def test_history_extra_scope_is_exact_shape_rejection():
    source = exact_p3n0_source()
    sha = "0" * 64
    hostile_history = N0History(None, (), (), sha, sha, sha, sha, None, sha, sha, sha)
    object.__setattr__(hostile_history, "scope", 1)
    with pytest.raises(N0ValidationError, match="n0-history-shape-invalid"):
        audit_history(source, hostile_history)
