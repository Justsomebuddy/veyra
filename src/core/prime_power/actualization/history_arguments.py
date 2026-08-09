"""Exact public history arguments validated before selector or child access."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .common import (
    digest, exact_hex, exact_shape, indexed, reject,
)
from .nested_validation import (
    exact_tuple, validate_edge_shape, validate_event_shape, validate_replay_shape,
)
from .history_semantics import (
    canonical_pending_event_rows, canonical_strict_prefix,
)
from .sources import validate_n0_source
from .types import (
    N0Event, N0History, SuffixSelector,
)

logger = logging.getLogger(__name__)
PENDING_IDS = (
    "past-doctrine", "past-scope", "past-genealogy", "past-discrimination", "birth",
    "response-F0", "response-F1", "identity-requery", "reduction", "selector",
    "bridge-access", "package-access",
)
PENDING_PARENTS = (
    (), ("past-doctrine",), ("past-scope",), ("past-genealogy",),
    ("past-genealogy", "past-discrimination"), ("birth",), ("response-F0",),
    ("response-F1",), ("identity-requery",), ("reduction",), ("selector",),
    ("bridge-access",),
)


@dataclass(frozen=True)
class N0PendingHistory:
    selector: SuffixSelector
    events: tuple[N0Event, ...]
    strict_past_digest: str
    birth_event_digest: str
    birth_core_digest: str
    historical_token_id: str


def _event_digest(raw, index) -> str:
    """Recompute one already shape-validated pending event."""
    logger.debug("_event_digest entry index=%d", index)
    value = digest("veyra.p3n0.event.v2", (
        ("id", raw["event_id"].encode()), ("kind", raw["kind"].encode()),
        *indexed("parent", raw["parents"]),
        ("token", (raw["token_id"] or "PRETOKEN").encode()),
        ("lineage", raw["lineage_id"].encode()),
        ("scope", raw["scope_digest"].encode()),
        ("payload", raw["payload_digest"].encode()),
    ))
    if value != raw["event_digest"]:
        reject(f"n0-pending-event-{index}-digest-drift")
    logger.debug("_event_digest exit index=%d", index)
    return value


def validate_pending_history(source, pending) -> dict:
    """Authenticate exact pending shape, DAG, pre-token, birth core, and token."""
    logger.debug("validate_pending_history entry")
    validate_n0_source(source)
    raw = exact_shape(pending, N0PendingHistory, "n0-pending-history")
    if type(raw["selector"]) is not SuffixSelector:
        reject("n0-pending-selector-exact-enum-required")
    events = exact_tuple(raw["events"], "n0-pending-events", maximum=12, length=12)
    children = tuple(validate_event_shape(item) for item in events)
    if (tuple(item["event_id"] for item in children) != PENDING_IDS
            or tuple(item["parents"] for item in children) != PENDING_PARENTS):
        reject("n0-pending-canonical-dag-drift")
    tuple(_event_digest(item, index) for index, item in enumerate(children))
    for name in (
        "strict_past_digest", "birth_event_digest", "birth_core_digest",
        "historical_token_id",
    ):
        exact_hex(raw[name], f"n0-pending-{name}")
    past, birth, strict_past, core, token = canonical_strict_prefix(source)
    expected_prefix = (*past, birth)
    expected = canonical_pending_event_rows(source, raw["selector"], token)
    event_fields = tuple(N0Event.__dataclass_fields__)
    if any(
        tuple(item[name] for name in event_fields)
        != tuple(object.__getattribute__(wanted, name) for name in event_fields)
        for item, wanted in zip(children[:5], expected_prefix, strict=True)
    ):
        logger.error("validate_pending_history prefix semantic drift")
        reject("n0-pending-prefix-semantic-drift")
    if any(
        tuple(item[name] for name in event_fields)
        != tuple(object.__getattribute__(expected[item["event_id"]], name)
                 for name in event_fields)
        for item in children[5:]
    ):
        logger.error("validate_pending_history future semantic drift")
        reject("n0-pending-future-semantic-drift")
    if any(item["lineage_id"] != source.lineage_id
           or item["scope_digest"] != source.scope.scope_digest for item in children):
        reject("n0-pending-source-binding-drift")
    if any(item["token_id"] is not None for item in children[:5]) or any(
            item["token_id"] != raw["historical_token_id"] for item in children[5:]):
        reject("n0-pending-token-placement-drift")
    if (raw["strict_past_digest"] != strict_past
            or raw["birth_event_digest"] != birth.event_digest
            or raw["birth_core_digest"] != core or raw["historical_token_id"] != token):
        reject("n0-pending-canonical-binding-drift")
    logger.debug("validate_pending_history exit")
    return raw


def validate_replay_argument(replay) -> dict:
    """Validate exact replay outer and all scalar children before caller access."""
    logger.debug("validate_replay_argument entry")
    raw = validate_replay_shape(replay)
    logger.debug("validate_replay_argument exit")
    return raw


def validate_history_outer(history) -> dict:
    """Validate exact history outer and nested DTO shapes before rehash access."""
    logger.debug("validate_history_outer entry")
    raw = exact_shape(history, N0History, "n0-rehash-history")
    if type(raw["selector"]) is not SuffixSelector:
        reject("n0-rehash-selector-exact-enum-required")
    events = exact_tuple(raw["events"], "n0-rehash-events", maximum=64)
    edges = exact_tuple(raw["access_edges"], "n0-rehash-edges", maximum=128)
    tuple(validate_event_shape(item) for item in events)
    tuple(validate_edge_shape(item) for item in edges)
    validate_replay_shape(raw["replay_evidence"])
    for name in (
        "strict_past_digest", "birth_event_digest", "birth_core_digest",
        "historical_token_id", "outcome_digest", "efficacy_digest", "history_digest",
    ):
        exact_hex(raw[name], f"n0-rehash-{name}")
    logger.debug("validate_history_outer exit")
    return raw


def validate_rehash_overrides(events, edges) -> None:
    """Validate supplied override tuples and every child before hashing."""
    logger.debug("validate_rehash_overrides entry")
    checked_events = exact_tuple(events, "n0-rehash-override-events", maximum=64)
    checked_edges = exact_tuple(edges, "n0-rehash-override-edges", maximum=128)
    tuple(validate_event_shape(item) for item in checked_events)
    tuple(validate_edge_shape(item) for item in checked_edges)
    logger.debug("validate_rehash_overrides exit")
