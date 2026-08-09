"""Complete reserved-row and strict-prefix regressions for P3-N0 histories."""

from dataclasses import replace

import pytest

from src.core.prime_power_observer_actualization import N0ValidationError
from src.core.prime_power_observer_actualization_common import digest, indexed
from src.core.prime_power_observer_actualization_counterfactuals import (
    counterfactual_histories,
)
from src.core.prime_power_observer_actualization_history import (
    _event, _pretoken, pending_histories, rehash_history,
)
from src.core.prime_power_observer_actualization_history_arguments import (
    N0PendingHistory, validate_pending_history,
)
from src.core.prime_power_observer_actualization_history_semantics import (
    RESERVED_FUTURE_ROWS, canonical_pending_event_rows,
)
from src.core.prime_power_observer_actualization_history_validation import (
    audit_history, validate_rehashed_history,
)
from src.core.prime_power_observer_actualization_replay_validation import (
    validate_replay_evidence,
)

from prime_power_observer_actualization_fixture import exact_p3n0_source

pytestmark = pytest.mark.requires_lean


def _rehashed_event(event, **changes):
    """Replace selected fields and recompute the complete event digest."""
    raw = replace(event, **changes, event_digest="")
    value = digest("veyra.p3n0.event.v2", (
        ("id", raw.event_id.encode()), ("kind", raw.kind.encode()),
        *indexed("parent", raw.parents),
        ("token", (raw.token_id or "PRETOKEN").encode()),
        ("lineage", raw.lineage_id.encode()),
        ("scope", raw.scope_digest.encode()),
        ("payload", raw.payload_digest.encode()),
    ))
    return replace(raw, event_digest=value)


@pytest.fixture(scope="module")
def source():
    return exact_p3n0_source()


@pytest.fixture(scope="module")
def strict_history(source):
    return counterfactual_histories(source)[0]


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("field,value", (
    ("kind", "BANANA"), ("payload_digest", "0" * 64),
))
def test_every_reserved_prefix_row_is_exact(source, index, field, value):
    pending = pending_histories(source)[0]
    events = list(pending.events)
    events[index] = _rehashed_event(events[index], **{field: value})
    hostile = replace(pending, events=tuple(events))
    with pytest.raises(N0ValidationError, match="n0-pending-prefix-semantic-drift"):
        validate_pending_history(source, hostile)


def test_fully_rehashed_prefix_cannot_mint_observer_token(source):
    pending = pending_histories(source)[0]
    past = list(pending.events[:4])
    past[0] = _rehashed_event(past[0], kind="BANANA", payload_digest="0" * 64)
    strict_past = digest("veyra.p3n0.strict-past.v2", (
        *indexed("event", (item.event_digest for item in past)),
        ("ledger", source.prebirth_ledger.ledger_digest.encode()),
    ))
    key = _pretoken(source, strict_past)
    birth = _event(
        "birth", "ARITHMETIC_ROLE_BIRTH",
        ("past-genealogy", "past-discrimination"), None, source, key.key_digest,
    )
    core = digest("veyra.p3n0.birth-core.v2", (
        ("past", strict_past.encode()), ("birth", birth.event_digest.encode()),
        ("key", key.key_digest.encode()),
        ("theorem", source.theorem_source.source_digest.encode()),
    ))
    token = digest("veyra.p3n0.historical-token.v2", (
        ("lineage", source.lineage_id.encode()),
        ("rho", key.rho_structural_id.encode()),
        ("doctrine", source.doctrine.doctrine_digest.encode()),
        ("core", core.encode()),
    ))
    future = tuple(canonical_pending_event_rows(source, pending.selector, token).values())
    hostile = N0PendingHistory(
        pending.selector, (*past, birth, *future), strict_past,
        birth.event_digest, core, token,
    )
    with pytest.raises(N0ValidationError, match="n0-pending-prefix-semantic-drift"):
        validate_pending_history(source, hostile)


@pytest.mark.parametrize(
    "event_id", (*tuple(row[0] for row in RESERVED_FUTURE_ROWS), "n2-selected"),
)
def test_every_reserved_postbirth_row_rejects_complete_rehash(
    source, strict_history, event_id,
):
    events = list(strict_history.events)
    index = next(i for i, item in enumerate(events) if item.event_id == event_id)
    events[index] = _rehashed_event(events[index], kind="BANANA")
    hostile = rehash_history(source, strict_history, events=tuple(events))
    reason = ("n0-history-replay-outcome-split" if event_id == "n2-selected"
              else "n0-history-future-semantic-drift")
    with pytest.raises(N0ValidationError, match=reason):
        validate_rehashed_history(source, hostile)


def test_typed_target_extra_is_narrow_and_refuting(source, strict_history):
    birth = strict_history.events[4]
    target = _event("target-pressure", "TARGET", birth.parents, None, source, "0" * 64)
    changed_birth = _event(
        birth.event_id, birth.kind, (*birth.parents, target.event_id),
        None, source, birth.payload_digest,
    )
    events = (*strict_history.events[:4], target, changed_birth, *strict_history.events[5:])
    hostile = rehash_history(source, strict_history, events=events)
    validate_rehashed_history(source, hostile)
    assert audit_history(source, hostile)["target_independence"].value == "refuted"


def test_replay_recomputes_each_event_digest(source, strict_history):
    events = list(strict_history.events)
    events[5] = replace(events[5], kind="BANANA")
    with pytest.raises(N0ValidationError, match="n0-replay-event-digest-drift"):
        validate_replay_evidence(
            source, strict_history.selector, tuple(events),
            strict_history.replay_evidence,
        )
