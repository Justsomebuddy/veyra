"""Exact replay authentication and ancestry-based audits for P3-N0 histories."""

from __future__ import annotations

import logging

from .common import digest, exact_hex, exact_shape, indexed, reject
from .history import (
    ALLOWED_DIFFERENCE_IDS, INVARIANT_SUFFIX_IDS, REQUIRED_ACCESS, _pretoken,
    finalize_history, pending_histories, replay_evidence,
)
from .nested_validation import (
    validate_edge_shape, validate_event_shape,
)
from .history_semantics import (
    canonical_event_row, canonical_pending_event_rows, validate_pressure_prefix,
)
from .replay_validation import validate_replay_evidence
from .sources import validate_n0_source
from .types import (
    N0Event, N0History, PremiseStatus, SuffixSelector,
)

logger = logging.getLogger(__name__)


def _event_digest(event) -> str:
    """Recompute one hostile-safe event from every stored field."""
    logger.debug("_event_digest entry")
    raw = validate_event_shape(event)
    value = digest("veyra.p3n0.event.v2", (
        ("id", raw["event_id"].encode()), ("kind", raw["kind"].encode()),
        *indexed("parent", raw["parents"]),
        ("token", (raw["token_id"] or "PRETOKEN").encode()),
        ("lineage", raw["lineage_id"].encode()),
        ("scope", raw["scope_digest"].encode()),
        ("payload", raw["payload_digest"].encode()),
    ))
    if value != raw["event_digest"]:
        reject("n0-event-digest-drift")
    logger.debug("_event_digest exit")
    return value


def _edge_digest(edge) -> str:
    """Recompute one hostile-safe access edge from every stored field."""
    logger.debug("_edge_digest entry")
    raw = validate_edge_shape(edge)
    value = digest("veyra.p3n0.access.v2", (
        ("consumer", raw["consumer_id"].encode()),
        ("producer", raw["producer_id"].encode()),
        ("token", raw["token_id"].encode()), ("lineage", raw["lineage_id"].encode()),
        ("scope", raw["scope_digest"].encode()),
    ))
    if value != raw["edge_digest"]:
        reject("n0-access-edge-digest-drift")
    logger.debug("_edge_digest exit")
    return value


def _closures(events, pivot="birth"):
    """Return transitive ancestors/descendants and reject disconnected tuple extras."""
    logger.debug("_closures entry pivot=%s", pivot)
    parents = {event.event_id: event.parents for event in events}
    if pivot not in parents:
        reject("n0-history-birth-missing")
    ancestors, frontier = set(), list(parents[pivot])
    while frontier:
        current = frontier.pop()
        if current not in ancestors:
            ancestors.add(current)
            frontier.extend(parents[current])
    children = {name: [] for name in parents}
    for child, values in parents.items():
        for parent in values:
            children[parent].append(child)
    descendants, frontier = set(), list(children[pivot])
    while frontier:
        current = frontier.pop()
        if current not in descendants:
            descendants.add(current)
            frontier.extend(children[current])
    connected = ancestors | {pivot} | descendants
    if connected != set(parents):
        reject("n0-history-disconnected-event")
    logger.debug("_closures exit ancestors=%d descendants=%d", len(ancestors), len(descendants))
    return ancestors, descendants


def _recompute_history_digest(history, efficacy) -> str:
    """Recompute the terminal history digest from exact children."""
    logger.debug("_recompute_history_digest entry")
    value = digest("veyra.p3n0.history.v2", (
        ("selector", history.selector.value.encode()),
        ("past", history.strict_past_digest.encode()),
        ("birth", history.birth_event_digest.encode()),
        ("core", history.birth_core_digest.encode()),
        ("token", history.historical_token_id.encode()),
        *indexed("event", (x.event_digest for x in history.events)),
        *indexed("access", (x.edge_digest for x in history.access_edges)),
        ("replay", history.replay_evidence.outcome_digest.encode()),
        ("efficacy", efficacy.encode()),
    ))
    logger.debug("_recompute_history_digest exit")
    return value


def validate_rehashed_history(source, history) -> N0History:
    """Validate nested shapes, replay, graph closure, outcome equality, and hashes."""
    logger.debug("validate_rehashed_history entry")
    validate_n0_source(source)
    raw = exact_shape(history, N0History, "n0-history")
    if (type(raw["selector"]) is not SuffixSelector
            or type(raw["events"]) is not tuple or len(raw["events"]) > 64
            or type(raw["access_edges"]) is not tuple or len(raw["access_edges"]) > 128):
        reject("n0-history-envelope-invalid")
    for name in (
        "strict_past_digest", "birth_event_digest", "birth_core_digest",
        "historical_token_id", "outcome_digest", "efficacy_digest", "history_digest",
    ):
        exact_hex(raw[name], f"n0-history-{name}")
    tuple(_event_digest(event) for event in history.events)
    tuple(_edge_digest(edge) for edge in history.access_edges)
    ids = tuple(event.event_id for event in history.events)
    if len(ids) != len(set(ids)):
        reject("n0-history-event-id-duplicate")
    positions = {name: index for index, name in enumerate(ids)}
    if any(parent not in positions or positions[parent] >= positions[event.event_id]
           for event in history.events for parent in event.parents):
        reject("n0-history-parent-unknown-forward-or-cycle")
    _closures(history.events)
    validate_pressure_prefix(source, history.events)
    expected_future = canonical_pending_event_rows(
        source, history.selector, history.historical_token_id,
    )
    by_id = {event.event_id: event for event in history.events}
    event_fields = tuple(N0Event.__dataclass_fields__)
    if any(
        name not in by_id
        or tuple(object.__getattribute__(by_id[name], field) for field in event_fields)
        != tuple(object.__getattribute__(expected, field) for field in event_fields)
        for name, expected in expected_future.items()
    ):
        logger.error("validate_rehashed_history future semantic drift")
        reject("n0-history-future-semantic-drift")
    pairs = tuple((edge.consumer_id, edge.producer_id) for edge in history.access_edges)
    if len(pairs) != len(set(pairs)) or not set(pairs) <= set(REQUIRED_ACCESS):
        reject("n0-access-duplicate-or-extra-edge")
    if any(a not in positions or b not in positions for a, b in pairs):
        reject("n0-access-unknown-endpoint")
    validate_replay_evidence(source, history.selector, history.events, history.replay_evidence)
    outcomes = tuple(event for event in history.events if event.event_id == "n2-selected")
    expected_outcome = canonical_event_row(
        source, "n2-selected", "N2F_OUTCOME", ("package-access",),
        history.historical_token_id, history.replay_evidence.outcome_digest,
    )
    if (len(outcomes) != 1
            or tuple(object.__getattribute__(outcomes[0], field) for field in event_fields)
            != tuple(object.__getattribute__(expected_outcome, field) for field in event_fields)
            or history.outcome_digest != history.replay_evidence.outcome_digest):
        reject("n0-history-replay-outcome-split")
    efficacy = digest("veyra.p3n0.efficacy.v2", (
        ("outcome", history.outcome_digest.encode()),
        *indexed("access", (x.edge_digest for x in history.access_edges)),
    ))
    if (efficacy != history.efficacy_digest
            or _recompute_history_digest(history, efficacy) != history.history_digest):
        reject("n0-history-terminal-digest-drift")
    logger.debug("validate_rehashed_history exit")
    return history


def validate_history(source, history, network, n2_result, arrow) -> N0History:
    """Require exact released results and canonical pending/replay recomputation."""
    logger.debug("validate_history entry")
    validate_rehashed_history(source, history)
    index = 0 if history.selector is SuffixSelector.STRICT_SUFFIX else 1
    pending = pending_histories(source)[index]
    replay = replay_evidence(source, pending, network, n2_result, arrow)
    expected = finalize_history(source, pending, replay)
    if history != expected:
        reject("n0-history-canonical-recomputation-drift")
    ancestors, _ = _closures(history.events)
    if ancestors != {"past-doctrine", "past-scope", "past-genealogy", "past-discrimination"}:
        reject("n0-birth-strict-ancestry-closure-drift")
    logger.debug("validate_history exit")
    return history


def access_status(source, history):
    """Classify exact missing access as OPEN and foreign binding as REFUTED."""
    logger.debug("access_status entry")
    validate_rehashed_history(source, history)
    pairs = {(x.consumer_id, x.producer_id) for x in history.access_edges}
    if not set(REQUIRED_ACCESS) <= pairs:
        result = "open"
    elif any(edge.token_id != history.historical_token_id
             or edge.lineage_id != source.lineage_id
             or edge.scope_digest != source.scope.scope_digest
             for edge in history.access_edges):
        result = "refuted"
    else:
        result = "established"
    logger.debug("access_status exit status=%s", result)
    return result


def audit_history(source, history) -> dict[str, PremiseStatus]:
    """Audit strict past and future solely by graph ancestry, never tuple position."""
    logger.debug("audit_history entry")
    validate_rehashed_history(source, history)
    ancestors, descendants = _closures(history.events)
    by_id = {event.event_id: event for event in history.events}
    raw_past = tuple(event for event in history.events
                     if event.event_id in ancestors and event.kind != "ARITHMETIC_ROLE_BIRTH")
    strict_past = digest("veyra.p3n0.strict-past.v2", (
        *indexed("event", (x.event_digest for x in raw_past)),
        ("ledger", source.prebirth_ledger.ledger_digest.encode()),
    ))
    key = _pretoken(source, strict_past)
    birth = by_id["birth"]
    expected_core = digest("veyra.p3n0.birth-core.v2", (
        ("past", strict_past.encode()), ("birth", birth.event_digest.encode()),
        ("key", key.key_digest.encode()),
        ("theorem", source.theorem_source.source_digest.encode()),
    ))
    expected_token = digest("veyra.p3n0.historical-token.v2", (
        ("lineage", source.lineage_id.encode()), ("rho", key.rho_structural_id.encode()),
        ("doctrine", source.doctrine.doctrine_digest.encode()),
        ("core", expected_core.encode()),
    ))
    prior = any(by_id[name].kind == "ARITHMETIC_ROLE_BIRTH"
                and by_id[name].payload_digest == key.key_digest for name in ancestors)
    first_birth = PremiseStatus.REFUTED if prior else PremiseStatus.ESTABLISHED
    independence = (PremiseStatus.REFUTED if any(by_id[name].kind == "TARGET" for name in ancestors)
                    else PremiseStatus.ESTABLISHED)
    token_ok = (history.strict_past_digest == strict_past
                and birth.payload_digest == key.key_digest
                and history.birth_event_digest == birth.event_digest
                and history.birth_core_digest == expected_core
                and history.historical_token_id == expected_token)
    token = PremiseStatus.ESTABLISHED if token_ok else PremiseStatus.REFUTED
    future_ids = {name for name in descendants if by_id[name].token_id == history.historical_token_id}
    persistent_pairs = {
        ("identity-requery", "response-F0"), ("identity-requery", "response-F1"),
        ("reduction", "response-F0"), ("reduction", "response-F1"),
    }
    actual_pairs = {(edge.consumer_id, edge.producer_id) for edge in history.access_edges}
    persistence = (PremiseStatus.ESTABLISHED
                   if {"response-F0", "response-F1", "identity-requery", "reduction"} <= future_ids
                   and persistent_pairs <= actual_pairs else PremiseStatus.OPEN)
    status = access_status(source, history)
    result = {
        "first_birth": first_birth, "target_independence": independence,
        "token_identity": token, "persistence": persistence,
        "post_birth_efficacy": {"established": PremiseStatus.ESTABLISHED,
                                "open": PremiseStatus.OPEN,
                                "refuted": PremiseStatus.REFUTED}[status],
    }
    logger.debug("audit_history exit")
    return result


def audit_counterfactual_pair(source, strict, open_history) -> PremiseStatus:
    """Require exact common causal identities and only allowed suffix differences."""
    logger.debug("audit_counterfactual_pair entry")
    validate_rehashed_history(source, strict)
    validate_rehashed_history(source, open_history)
    smap = {event.event_id: event for event in strict.events}
    omap = {event.event_id: event for event in open_history.events}
    different = {name for name in smap if smap[name] != omap.get(name)}
    prefix_ids = {"past-doctrine", "past-scope", "past-genealogy", "past-discrimination", "birth"}
    result = PremiseStatus.ESTABLISHED if (
        strict.selector is SuffixSelector.STRICT_SUFFIX
        and open_history.selector is SuffixSelector.OPEN_SUFFIX
        and all(smap[name] == omap[name] for name in prefix_ids)
        and strict.birth_core_digest == open_history.birth_core_digest
        and strict.historical_token_id == open_history.historical_token_id
        and strict.access_edges == open_history.access_edges
        and all(smap[name] == omap[name] for name in INVARIANT_SUFFIX_IDS)
        and different == set(ALLOWED_DIFFERENCE_IDS)
        and strict.outcome_digest != open_history.outcome_digest
        and strict.efficacy_digest != open_history.efficacy_digest
    ) else PremiseStatus.REFUTED
    logger.debug("audit_counterfactual_pair exit status=%s", result.value)
    return result
