"""Pending-first, replay-bound, exactly recomputable histories for isolated P3-N0."""

from __future__ import annotations

from dataclasses import replace
import logging

from .common import digest, indexed, reject
from .types import N0ReplayEvidence
from .history_arguments import (
    N0PendingHistory, validate_history_outer, validate_pending_history,
    validate_rehash_overrides, validate_replay_argument,
)
from .history_semantics import (
    canonical_pending_event_rows, canonical_pretoken, canonical_strict_prefix,
    reduction_payload as _canonical_reduction_payload,
    response_payload as _canonical_response_payload,
)
from .replay_validation import (
    PRODUCER_IDS, outcome_digest, validate_released_lane, validate_replay_evidence,
)
from .sources import validate_n0_source
from .types import (
    DoctrineAdmission, N0AccessEdge, N0Event, N0History, N0Source, PreTokenKey, SuffixSelector,
)

logger = logging.getLogger(__name__)
RHO_STRUCTURAL_VERSION = "rho-prime-power-coordinate-v2"
PRE_OUTCOME_ACCESS = (
    ("identity-requery", "response-F0"), ("identity-requery", "response-F1"),
    ("reduction", "response-F0"), ("reduction", "response-F1"),
)
OUTCOME_ACCESS = (
    ("n2-selected", "selector"), ("n2-selected", "identity-requery"),
    ("n2-selected", "reduction"), ("n2-selected", "bridge-access"),
    ("n2-selected", "package-access"),
)
REQUIRED_ACCESS = PRE_OUTCOME_ACCESS + OUTCOME_ACCESS
INVARIANT_SUFFIX_IDS = (
    "response-F0", "response-F1", "identity-requery", "reduction", "bridge-access",
)
ALLOWED_DIFFERENCE_IDS = ("selector", "package-access", "n2-selected")

def rho_structural_id(source: N0Source) -> str:
    """Identify rho independently of its history token."""
    logger.debug("rho_structural_id entry")
    validate_n0_source(source)
    result = digest("veyra.p3n0.rho-structural.v2", (
        ("version", RHO_STRUCTURAL_VERSION.encode()),
        ("prime", str(source.prime).encode()), ("depth", str(source.depth).encode()),
        ("tower", source.n1_packages[0].doctrine.doctrine_digest.encode()),
    ))
    logger.debug("rho_structural_id exit")
    return result


def _pretoken(source, strict_past_digest) -> PreTokenKey:
    """Build the exact key before any birth token exists."""
    logger.debug("_pretoken entry")
    result = canonical_pretoken(source, strict_past_digest)
    logger.debug("_pretoken exit")
    return result


def _event(event_id, kind, parents, token, source, payload) -> N0Event:
    """Construct one exact event digest from all semantic fields."""
    logger.debug("_event entry id=%s kind=%s", event_id, kind)
    value = digest("veyra.p3n0.event.v2", (
        ("id", event_id.encode()), ("kind", kind.encode()), *indexed("parent", parents),
        ("token", (token or "PRETOKEN").encode()), ("lineage", source.lineage_id.encode()),
        ("scope", source.scope.scope_digest.encode()), ("payload", payload.encode()),
    ))
    result = N0Event(event_id, kind, parents, token, source.lineage_id,
                     source.scope.scope_digest, payload, value)
    logger.debug("_event exit id=%s", event_id)
    return result


def _edge(consumer, producer, token, source) -> N0AccessEdge:
    """Construct one exact token/lineage/scope-bound access edge."""
    logger.debug("_edge entry consumer=%s producer=%s", consumer, producer)
    value = digest("veyra.p3n0.access.v2", (
        ("consumer", consumer.encode()), ("producer", producer.encode()),
        ("token", token.encode()), ("lineage", source.lineage_id.encode()),
        ("scope", source.scope.scope_digest.encode()),
    ))
    result = N0AccessEdge(consumer, producer, token, source.lineage_id,
                          source.scope.scope_digest, value)
    logger.debug("_edge exit")
    return result


def _response_payload(source, family_id) -> str:
    """Bind one response to its exact bridge coordinate."""
    logger.debug("_response_payload entry family=%s", family_id)
    result = _canonical_response_payload(source, family_id)
    logger.debug("_response_payload exit family=%s", family_id)
    return result


def _reduction_payload(source) -> str:
    """Bind every bridge fine/coarse coordinate reduction."""
    logger.debug("_reduction_payload entry")
    result = _canonical_reduction_payload(source)
    logger.debug("_reduction_payload exit")
    return result


def _strict_prefix(source):
    """Build strict past, key-specific birth, core, and token without any outcome."""
    logger.debug("_strict_prefix entry")
    past, birth, strict_past, core, token = canonical_strict_prefix(source)
    logger.debug("_strict_prefix exit")
    return past, birth, strict_past, core, token


def _pending_suffix(source, selector, prefix) -> N0PendingHistory:
    """Build post-birth producers but deliberately no N2 outcome or efficacy."""
    logger.debug("_pending_suffix entry selector=%s", selector.value)
    past, birth, strict_past, core, token = prefix
    future = tuple(canonical_pending_event_rows(source, selector, token).values())
    result = N0PendingHistory(selector, (*past, birth, *future), strict_past,
                              birth.event_digest, core, token)
    logger.debug("_pending_suffix exit selector=%s", selector.value)
    return result


def pending_histories(source):
    """Return two outcome-free pending suffixes only for an admitted doctrine."""
    logger.debug("pending_histories entry")
    validate_n0_source(source)
    if source.doctrine.admission is not DoctrineAdmission.ADMITTED:
        reject("n0-pending-doctrine-not-admitted")
    prefix = _strict_prefix(source)
    result = tuple(_pending_suffix(source, selector, prefix) for selector in (
        SuffixSelector.STRICT_SUFFIX, SuffixSelector.OPEN_SUFFIX,
    ))
    logger.debug("pending_histories exit")
    return result


def replay_evidence(source, pending, network, n2_result, arrow) -> N0ReplayEvidence:
    """Bind the later fresh P3-T/N2 judgment and exact arrow to pending producers."""
    logger.debug("replay_evidence entry")
    validate_n0_source(source)
    validate_pending_history(source, pending)
    logger.debug("replay_evidence state selector=%s", pending.selector.value)
    package, network, n2_result, arrow = validate_released_lane(
        source, pending.selector, network, n2_result, arrow,
    )
    by_id = {item.event_id: item for item in pending.events}
    if any(name not in by_id for name in PRODUCER_IDS):
        reject("n0-replay-producer-event-missing")
    producers = tuple(by_id[name].event_digest for name in PRODUCER_IDS)
    value = outcome_digest(
        source, pending.selector, producers, network, n2_result, arrow,
    )
    result = N0ReplayEvidence(
        pending.selector.value, package.wrapper_digest, network.source_digest,
        network.judgment_digest, n2_result.judgment_digest, arrow.judgment_digest,
        producers, value,
    )
    logger.debug("replay_evidence exit")
    return result


def finalize_history(source, pending, replay) -> N0History:
    """Append the exact replay-bound outcome, access edges, and efficacy digest."""
    logger.debug("finalize_history entry")
    validate_n0_source(source)
    validate_pending_history(source, pending)
    validate_replay_argument(replay)
    logger.debug("finalize_history state selector=%s", pending.selector.value)
    validate_replay_evidence(source, pending.selector, pending.events, replay)
    if replay.selector != pending.selector.value:
        reject("n0-finalize-selector-drift")
    outcome = _event("n2-selected", "N2F_OUTCOME", ("package-access",),
                     pending.historical_token_id, source, replay.outcome_digest)
    events = (*pending.events, outcome)
    edges = tuple(_edge(c, p, pending.historical_token_id, source) for c, p in REQUIRED_ACCESS)
    efficacy = digest("veyra.p3n0.efficacy.v2", (
        ("outcome", replay.outcome_digest.encode()),
        *indexed("access", (x.edge_digest for x in edges)),
    ))
    history = digest("veyra.p3n0.history.v2", (
        ("selector", pending.selector.value.encode()),
        ("past", pending.strict_past_digest.encode()),
        ("birth", pending.birth_event_digest.encode()), ("core", pending.birth_core_digest.encode()),
        ("token", pending.historical_token_id.encode()),
        *indexed("event", (x.event_digest for x in events)),
        *indexed("access", (x.edge_digest for x in edges)),
        ("replay", replay.outcome_digest.encode()), ("efficacy", efficacy.encode()),
    ))
    result = N0History(
        pending.selector, events, edges, pending.strict_past_digest,
        pending.birth_event_digest, pending.birth_core_digest, pending.historical_token_id,
        replay, replay.outcome_digest, efficacy, history,
    )
    logger.debug("finalize_history exit selector=%s", pending.selector.value)
    return result


def rehash_history(source, history, *, events=None, access_edges=None) -> N0History:
    """Rehash a semantic pressure history without making it canonical."""
    logger.debug("rehash_history entry")
    validate_n0_source(source)
    raw = validate_history_outer(history)
    events = raw["events"] if events is None else events
    edges = raw["access_edges"] if access_edges is None else access_edges
    validate_rehash_overrides(events, edges)
    efficacy = digest("veyra.p3n0.efficacy.v2", (
        ("outcome", raw["outcome_digest"].encode()),
        *indexed("access", (x.edge_digest for x in edges)),
    ))
    value = digest("veyra.p3n0.history.v2", (
        ("selector", raw["selector"].value.encode()), ("past", raw["strict_past_digest"].encode()),
        ("birth", raw["birth_event_digest"].encode()), ("core", raw["birth_core_digest"].encode()),
        ("token", raw["historical_token_id"].encode()),
        *indexed("event", (x.event_digest for x in events)),
        *indexed("access", (x.edge_digest for x in edges)),
        ("replay", raw["replay_evidence"].outcome_digest.encode()),
        ("efficacy", efficacy.encode()),
    ))
    result = replace(history, events=events, access_edges=edges, efficacy_digest=efficacy, history_digest=value)
    logger.debug("rehash_history exit")
    return result
