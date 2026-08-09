"""Hostile public-path regressions for P3-N0 replay, pressure, and history."""

from dataclasses import replace
from unittest.mock import patch

import pytest

from src.core.observer_network import observer_network_judgment
from src.core.prime_power_observer_actualization import N0ValidationError
from src.core.prime_power_observer_actualization_common import digest, indexed
from src.core.prime_power_observer_actualization_counterfactuals import (
    counterfactual_histories,
)
from src.core.prime_power_observer_actualization_history import (
    PRODUCER_IDS, _event, finalize_history, pending_histories, rehash_history,
    replay_evidence,
)
from src.core.prime_power_observer_actualization_history_arguments import (
    N0PendingHistory, validate_pending_history,
)
from src.core.prime_power_observer_actualization_history_validation import (
    audit_history, validate_rehashed_history,
)
from src.core.prime_power_observer_actualization_pressure import (
    discrimination_candidate, refute_discrimination, refute_separator,
    separator_candidate,
)
from src.core.prime_power_observer_actualization_replay_validation import (
    fresh_released_lane, outcome_digest, validate_released_lane,
    validate_replay_evidence,
)
from src.core.prime_power_reduction_network import prime_power_reduction_judgment
from src.core.prime_power_reduction_network_types import FiniteArrowJudgment

from prime_power_observer_actualization_fixture import exact_p3n0_source

pytestmark = pytest.mark.requires_lean


class AlwaysEqual:
    def __eq__(self, _other): return True


class ExplosiveSelector:
    @property
    def value(self):
        raise RuntimeError("selector accessed before validation")

    def __repr__(self):
        raise RuntimeError("selector represented before validation")


def _fully_rehashed_future_forgery(
    source, history, event_id, *, kind=None, payload=None, parents=None,
    lineage_id=None, scope_digest=None,
):
    events = list(history.events)
    index = next(i for i, item in enumerate(events) if item.event_id == event_id)
    original = events[index]
    raw = replace(
        original, kind=kind or original.kind,
        parents=original.parents if parents is None else parents,
        lineage_id=original.lineage_id if lineage_id is None else lineage_id,
        scope_digest=original.scope_digest if scope_digest is None else scope_digest,
        payload_digest=original.payload_digest if payload is None else payload,
        event_digest="",
    )
    value = digest("veyra.p3n0.event.v2", (
        ("id", raw.event_id.encode()), ("kind", raw.kind.encode()),
        *indexed("parent", raw.parents),
        ("token", (raw.token_id or "PRETOKEN").encode()),
        ("lineage", raw.lineage_id.encode()), ("scope", raw.scope_digest.encode()),
        ("payload", raw.payload_digest.encode()),
    ))
    events[index] = replace(raw, event_digest=value)
    by_id = {item.event_id: item for item in events}
    producers = tuple(by_id[name].event_digest for name in PRODUCER_IDS)
    _, network, n2_result, arrow = fresh_released_lane(source, history.selector)
    outcome = outcome_digest(
        source, history.selector, producers, network, n2_result, arrow,
    )
    replay = replace(
        history.replay_evidence, producer_digests=producers, outcome_digest=outcome,
    )
    outcome_index = next(i for i, item in enumerate(events) if item.event_id == "n2-selected")
    old_outcome = events[outcome_index]
    events[outcome_index] = _event(
        old_outcome.event_id, old_outcome.kind, old_outcome.parents,
        old_outcome.token_id, source, outcome,
    )
    base = replace(
        history, events=tuple(events), replay_evidence=replay, outcome_digest=outcome,
    )
    return rehash_history(source, base, events=tuple(events))


@pytest.fixture(scope="module")
def source():
    return exact_p3n0_source()


@pytest.fixture(scope="module")
def strict_history(source):
    return counterfactual_histories(source)[0]


@pytest.mark.parametrize("path", (
    lambda source: discrimination_candidate(source, object(), (), ()),
    lambda source: separator_candidate(source, object(), ()),
    lambda source: refute_discrimination(source, object(), object()),
    lambda source: refute_separator(source, object(), object()),
))
def test_pressure_public_paths_validate_complete_source_first(source, path):
    hostile = replace(source, scope=replace(source.scope, scope_digest=AlwaysEqual()))
    with pytest.raises(N0ValidationError, match="source-scope-scope_digest-exact-type-drift"):
        path(hostile)


def test_pressure_candidate_fields_and_digests_are_recomputed(source, strict_history):
    discrimination = discrimination_candidate(
        source, strict_history, ("integer:0", "integer:1"), (0, 1), True,
    )
    with pytest.raises(N0ValidationError, match="n0-discrimination-candidate-digest-drift"):
        refute_discrimination(
            source, strict_history, replace(discrimination, candidate_digest="0" * 64),
        )
    with pytest.raises(N0ValidationError, match="n0-discrimination-package_digest-digest-invalid"):
        refute_discrimination(
            source, strict_history, replace(discrimination, package_digest=AlwaysEqual()),
        )
    separator = separator_candidate(source, strict_history, (0, 2), True)
    with pytest.raises(N0ValidationError, match="n0-separator-candidate-digest-drift"):
        refute_separator(
            source, strict_history, replace(separator, candidate_digest="0" * 64),
        )
    with pytest.raises(N0ValidationError, match="n0-separator-scope_digest-digest-invalid"):
        refute_separator(
            source, strict_history, replace(separator, scope_digest=AlwaysEqual()),
        )


@pytest.mark.parametrize("path", (
    lambda source: replay_evidence(source, object(), object(), object(), object()),
    lambda source: finalize_history(source, object(), object()),
    lambda source: rehash_history(source, object()),
))
def test_history_public_paths_normalize_hostile_outer_arguments(source, path):
    with pytest.raises(N0ValidationError):
        path(source)


def test_history_selector_and_replay_are_validated_before_logging_or_access(source):
    sha = "0" * 64
    hostile = N0PendingHistory(AlwaysEqual(), (), sha, sha, sha, sha)
    with pytest.raises(N0ValidationError, match="n0-pending-selector-exact-enum-required"):
        replay_evidence(source, hostile, object(), object(), object())
    pending = pending_histories(source)[0]
    with pytest.raises(N0ValidationError, match="n0-replay-evidence-exact-type-required"):
        finalize_history(source, pending, object())


def test_standalone_replay_arrow_is_exact_before_equality(source):
    wrapper = source.strict_package
    network = observer_network_judgment(wrapper.network_source, wrapper.network_policy)
    n2_result = prime_power_reduction_judgment(wrapper.raw_package)
    arrow = next(item for item in n2_result.finite_arrows
                 if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    hostile = replace(arrow, judgment_digest=AlwaysEqual())
    with pytest.raises(N0ValidationError, match="n0-n2-arrow--1-judgment-digest-invalid"):
        validate_released_lane(source, pending_histories(source)[0].selector,
                               network, n2_result, hostile)
    with (
        patch(
            "src.core.prime_power_observer_actualization_replay_validation."
            "validate_prime_power_reduction_result",
            return_value=n2_result,
        ),
        patch.object(FiniteArrowJudgment, "__eq__", side_effect=RuntimeError),
        pytest.raises(N0ValidationError, match="n0-replay-arrow-equality-rejected-RuntimeError"),
    ):
        validate_released_lane(source, pending_histories(source)[0].selector,
                               network, n2_result, arrow)


@pytest.mark.parametrize("field,value", (("kind", "BANANA"), ("payload", "0" * 64)))
def test_pending_future_semantics_are_source_derived(source, field, value):
    pending = pending_histories(source)[0]
    original = pending.events[5]
    forged = _event(
        original.event_id, value if field == "kind" else original.kind,
        original.parents, original.token_id, source,
        value if field == "payload" else original.payload_digest,
    )
    hostile = replace(pending, events=(*pending.events[:5], forged, *pending.events[6:]))
    with pytest.raises(N0ValidationError, match="n0-pending-future-semantic-drift"):
        validate_pending_history(source, hostile)


@pytest.mark.parametrize("field,value", (("kind", "BANANA"), ("payload", "0" * 64)))
def test_fully_rehashed_future_semantics_cannot_establish(source, strict_history, field, value):
    hostile = _fully_rehashed_future_forgery(
        source, strict_history, "response-F0", **{field: value},
    )
    pressure_paths = (
        lambda: validate_rehashed_history(source, hostile),
        lambda: audit_history(source, hostile),
        lambda: discrimination_candidate(source, hostile, ("integer:0", "integer:1"), (0, 1)),
        lambda: separator_candidate(source, hostile, (0, 2)),
        lambda: refute_discrimination(source, hostile, object()),
        lambda: refute_separator(source, hostile, object()),
    )
    for path in pressure_paths:
        with pytest.raises(N0ValidationError, match="n0-history-future-semantic-drift"):
            path()


@pytest.mark.parametrize("field,value", (
    ("lineage_id", "foreign-lineage"),
    ("scope_digest", "1" * 64),
    ("parents", ("birth", "past-doctrine")),
))
def test_fully_rehashed_future_source_binding_cannot_establish(
    source, strict_history, field, value,
):
    hostile = _fully_rehashed_future_forgery(
        source, strict_history, "response-F0", **{field: value},
    )
    paths = (
        lambda: validate_rehashed_history(source, hostile),
        lambda: audit_history(source, hostile),
        lambda: discrimination_candidate(source, hostile, ("integer:0", "integer:1"), (0, 1)),
        lambda: separator_candidate(source, hostile, (0, 2)),
        lambda: refute_discrimination(source, hostile, object()),
        lambda: refute_separator(source, hostile, object()),
    )
    for path in paths:
        with pytest.raises(N0ValidationError, match="n0-history-future-semantic-drift"):
            path()


def test_only_explicit_target_or_prior_birth_pressure_extras_are_admitted(
    source, strict_history,
):
    extra = _event(
        "caller-extra", "BANANA", ("n2-selected",), None, source,
        strict_history.outcome_digest,
    )
    hostile = rehash_history(source, strict_history, events=(*strict_history.events, extra))
    with pytest.raises(N0ValidationError, match="n0-history-extra-pressure-event-invalid"):
        validate_rehashed_history(source, hostile)


def test_replay_events_are_exact_shape_before_event_digest_access(source, strict_history):
    events = (object(), *strict_history.events[1:])
    with pytest.raises(N0ValidationError, match="n0-event-exact-type-required"):
        validate_replay_evidence(
            source, strict_history.selector, events, strict_history.replay_evidence,
        )


def test_selector_is_validated_before_logging_or_value_access(source, strict_history):
    wrapper = source.strict_package
    network = observer_network_judgment(wrapper.network_source, wrapper.network_policy)
    n2_result = prime_power_reduction_judgment(wrapper.raw_package)
    arrow = next(item for item in n2_result.finite_arrows
                 if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    paths = (
        lambda: validate_released_lane(source, ExplosiveSelector(), network, n2_result, arrow),
        lambda: fresh_released_lane(source, ExplosiveSelector()),
        lambda: outcome_digest(source, ExplosiveSelector(), (), network, n2_result, arrow),
    )
    for path in paths:
        with pytest.raises(N0ValidationError, match="n0-replay-source-or-selector-invalid"):
            path()
