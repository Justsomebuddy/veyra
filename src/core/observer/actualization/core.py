"""Finite P1-E4 history-relative observer actualization.

One concept end to end: the closed DTO grammar for a finite event history, the
exact causal/access/assumption graph checks, the domain-separated commitments,
the bounded resource preflight, source construction and fresh revalidation, the
target-seal and same-token efficacy audits, mandatory counterfactual replay, the
Historical Actualization Principle runtime, and hostile-safe result validation.

The judgment is relative to the declared finite history only. Physical
instantiation is never established and consciousness is never claimed.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import logging
from typing import TypeAlias

from ...construction.finite_builder.types import (
    ConstructionSourceBinding, FormalGenerability,
)
from ...construction.finite_construction import finite_construction_judgment
from ..genesis.core import observer_genesis_judgment
from ..genesis.types import (
    GenesisJudgment, OEPAdmissionRecord, ObserverGenesisDoctrine,
    ObserverGenesisSource, ObserverRole, PremiseStatus, RecurrenceEvidence,
    RecurrenceWitness, UnavailableRecurrenceEvidence, WitnessScope,
)
from ...ontology.doctrine import stage_commitment
from ...ontology.types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)


class ActualizationStatus(str, Enum):
    ESTABLISHED = "established"
    REFUTED = "refuted"
    OPEN = "open"


class HistoricalActualization(str, Enum):
    ESTABLISHED_RELATIVE_TO_HISTORY = "established-relative-to-history"
    OPEN = "open"


class PhysicalInstantiation(str, Enum):
    NOT_ESTABLISHED = "not-established"


class ConsciousnessStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class EventKind(str, Enum):
    CONSTRUCTION = "construction"
    OEP = "oep"
    BIRTH = "birth"
    TARGET = "target"
    INTERVENTION = "intervention"
    RESPONSE = "response"
    ORACLE = "oracle"
    EXPECTED_RESPONSE = "expected-response"
    LATER_RESULT = "later-result"
    ACTUALIZATION_JUDGMENT = "actualization-judgment"
    ACTUALIZATION_CERTIFICATE = "actualization-certificate"
    COPIED_BIRTH = "copied-birth"
    OTHER = "other"


class EvidenceAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class AccessKind(str, Enum):
    DATA_DEPENDENCY = "data-dependency"
    TARGET_READ = "target-read"
    ORACLE_READ = "oracle-read"
    EXPECTED_RESPONSE_READ = "expected-response-read"
    LATER_RESULT_READ = "later-result-read"


class CounterfactualClass(str, Enum):
    PREFIX_TARGET_VARIATION = "prefix-target-variation"
    TARGET_READING_CHOOSER = "target-reading-chooser"
    FOREIGN_PARENT_COPY = "foreign-parent-copy"


class CounterfactualOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    OPEN = "open"


class ActualizationOperation(str, Enum):
    SOURCE = "historical-observer-source"
    JUDGMENT = "historical-actualization-judgment"


class ActualizationOperationStatus(str, Enum):
    JUDGED = "judged"
    RESOURCE_LIMIT = "resource-limit"


class ActualizationResourceBound(str, Enum):
    EVENTS = "events"
    PARENT_EDGES = "parent-edges"
    ACCESS_EDGES = "access-edges"
    ASSUMPTIONS = "assumptions"
    COUNTERFACTUALS = "counterfactuals"
    ENCODED_BYTES = "encoded-bytes"


@dataclass(frozen=True)
class HistoryEvent:
    event_id: str
    kind: EventKind
    parent_ids: tuple[str, ...]
    logical_time: int
    payload_digest: str
    lineage_id: str
    availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE


@dataclass(frozen=True)
class AccessEdge:
    provider_event_id: str
    consumer_event_id: str
    kind: AccessKind


@dataclass(frozen=True)
class HistoricalAssumption:
    assumption_id: str
    source_event_id: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True)
class ActualizationCounterfactual:
    case_id: str
    kind: CounterfactualClass
    provider_event_id: str
    consumer_event_id: str
    alternate_target_digest: str
    copied_lineage_id: str
    copied_parent_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActualizationResourcePolicy:
    version: str
    max_events: int
    max_parent_edges: int
    max_access_edges: int
    max_assumptions: int
    max_counterfactuals: int
    max_encoded_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class HistoricalObserverSource:
    version: str
    history_id: str
    lineage_id: str
    events: tuple[HistoryEvent, ...]
    access_edges: tuple[AccessEdge, ...]
    assumptions: tuple[HistoricalAssumption, ...]
    assumption_roots: tuple[str, ...]
    counterfactuals: tuple[ActualizationCounterfactual, ...]
    birth_event_id: str
    construction_event_id: str
    oep_event_id: str
    target_event_id: str
    intervention_event_id: str
    response_event_id: str
    policy: ActualizationResourcePolicy
    p0_doctrine: ObserverDoctrine
    construction_source: ConstructionSourceBinding
    construction_target: OntologyStage
    e1_doctrine: ObserverGenesisDoctrine
    e1_source: ObserverGenesisSource
    e1_witness: WitnessScope
    e1_recurrence: RecurrenceEvidence
    e1_oep: OEPAdmissionRecord
    birth_core_digest: str
    historical_token_id: str
    history_digest: str
    doctrine_digest: str
    scope_digest: str
    source_digest: str


@dataclass(frozen=True)
class CounterfactualEvidence:
    case_id: str
    kind: CounterfactualClass
    outcome: CounterfactualOutcome
    evidence_digest: str


@dataclass(frozen=True)
class HistoricalActualizationJudgment:
    source_digest: str
    birth_core_digest: str
    historical_token_id: str
    history_digest: str
    doctrine_digest: str
    scope_digest: str
    past_event_ids: tuple[str, ...]
    future_event_ids: tuple[str, ...]
    counterfactual_evidence: tuple[CounterfactualEvidence, ...]
    oep_role: ActualizationStatus
    prior_construction: ActualizationStatus
    birth_event: ActualizationStatus
    target_independence: ActualizationStatus
    post_birth_efficacy: ActualizationStatus
    historical_actualization: HistoricalActualization
    actualization_judgment_digest: str
    operation_status: ActualizationOperationStatus = ActualizationOperationStatus.JUDGED
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    consciousness: ConsciousnessStatus = ConsciousnessStatus.NOT_CLAIMED
    scope: str = "finite-history-relative-observer-actualization-only"


@dataclass(frozen=True)
class ActualizationResourceLimit:
    operation: ActualizationOperation
    failed_bound: ActualizationResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    operation_status: ActualizationOperationStatus = ActualizationOperationStatus.RESOURCE_LIMIT
    physical_instantiation: PhysicalInstantiation = PhysicalInstantiation.NOT_ESTABLISHED
    consciousness: ConsciousnessStatus = ConsciousnessStatus.NOT_CLAIMED
    scope: str = "resource-refusal-no-historical-evidence"


ActualizationSourceResult: TypeAlias = HistoricalObserverSource | ActualizationResourceLimit
ActualizationResult: TypeAlias = HistoricalActualizationJudgment | ActualizationResourceLimit


class ObserverActualizationValidationError(ValueError):
    """A P1-E4 input violated the closed finite grammar."""


def reject(reason: str) -> None:
    logger.error("observer actualization rejected reason=%s", reason)
    raise ObserverActualizationValidationError(reason)


def identifier(value: object, label: str) -> str:
    logger.debug("identifier entry label=%s", label)
    if type(value) is not str or not value or len(value) > 128:
        reject(f"invalid-{label}")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError:
        reject(f"invalid-{label}")
    logger.debug("identifier exit label=%s", label)
    return value


def hex_digest(value: object, label: str) -> str:
    logger.debug("hex_digest entry label=%s", label)
    if type(value) is not str or len(value) != 64:
        reject(f"invalid-{label}")
    try:
        int(value, 16)
    except ValueError:
        reject(f"invalid-{label}")
    logger.debug("hex_digest exit label=%s", label)
    return value


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash an ordered exact field list under one explicit domain."""
    logger.debug("actualization digest entry domain=%s fields=%d", domain, len(fields))
    h = sha256()
    for token in (b"veyra.p1e4.v1", domain.encode("ascii")):
        h.update(len(token).to_bytes(4, "big"))
        h.update(token)
    for name, value in fields:
        key = name.encode("ascii")
        h.update(len(key).to_bytes(4, "big"))
        h.update(key)
        h.update(len(value).to_bytes(8, "big"))
        h.update(value)
    result = h.hexdigest()
    logger.debug("actualization digest exit domain=%s", domain)
    return result


def event_bytes(value: HistoryEvent) -> bytes:
    logger.debug("event_bytes entry event=%s", value.event_id)
    fields = (
        value.event_id, value.kind.value, "\x1f".join(value.parent_ids),
        str(value.logical_time), value.payload_digest, value.lineage_id,
        value.availability.value,
    )
    result = "\x1e".join(fields).encode("utf-8")
    logger.debug("event_bytes exit event=%s", value.event_id)
    return result


def access_bytes(value: AccessEdge) -> bytes:
    logger.debug("access_bytes entry")
    result = "\x1e".join((
        value.provider_event_id, value.consumer_event_id, value.kind.value,
    )).encode("utf-8")
    logger.debug("access_bytes exit")
    return result


def assumption_bytes(value: HistoricalAssumption) -> bytes:
    logger.debug("assumption_bytes entry")
    result = "\x1e".join((
        value.assumption_id, value.source_event_id, "\x1f".join(value.depends_on),
    )).encode("utf-8")
    logger.debug("assumption_bytes exit")
    return result


def counterfactual_bytes(value: ActualizationCounterfactual) -> bytes:
    logger.debug("counterfactual_bytes entry kind=%s", value.kind.value)
    result = "\x1e".join((
        value.case_id, value.kind.value, value.provider_event_id,
        value.consumer_event_id, value.alternate_target_digest,
        value.copied_lineage_id, "\x1f".join(value.copied_parent_ids),
    )).encode("utf-8")
    logger.debug("counterfactual_bytes exit kind=%s", value.kind.value)
    return result


def policy_digest(values: tuple[int, ...]) -> str:
    logger.debug("policy_digest entry")
    result = digest("resource-policy", tuple(
        (f"bound-{index}", str(value).encode("ascii"))
        for index, value in enumerate(values)
    ))
    logger.debug("policy_digest exit")
    return result


def birth_core_digest(
    history_id: str, lineage_id: str, past: tuple[HistoryEvent, ...],
    birth: HistoryEvent, construction_digest: str, e1_source_digest: str,
    oep_digest: str, target_stage_digest: str, witness_digest: str,
    recurrence_digest: str,
) -> str:
    logger.debug("birth_core_digest entry")
    result = digest("birth-core", (
        ("history-id", history_id.encode()), ("lineage-id", lineage_id.encode()),
        ("past", b"\x00".join(event_bytes(item) for item in past)),
        ("birth", event_bytes(birth)),
        ("construction", construction_digest.encode("ascii")),
        ("e1-source", e1_source_digest.encode("ascii")),
        ("oep", oep_digest.encode("ascii")),
        ("construction-target", target_stage_digest.encode("ascii")),
        ("witness", witness_digest.encode("ascii")),
        ("recurrence", recurrence_digest.encode("ascii")),
    ))
    logger.debug("birth_core_digest exit")
    return result


def token_digest(core_digest: str, lineage_id: str, birth_event_id: str) -> str:
    logger.debug("token_digest entry")
    result = digest("historical-token", (
        ("birth-core", core_digest.encode("ascii")),
        ("lineage", lineage_id.encode()),
        ("birth-event", birth_event_id.encode()),
    ))
    logger.debug("token_digest exit")
    return result


def history_digest(
    history_id: str, token_id: str, events: tuple[HistoryEvent, ...],
    access: tuple[AccessEdge, ...], assumptions: tuple[HistoricalAssumption, ...],
    counterfactuals: tuple[ActualizationCounterfactual, ...],
) -> str:
    logger.debug("history_digest entry")
    result = digest("history", (
        ("history-id", history_id.encode()), ("token", token_id.encode("ascii")),
        ("events", b"\x00".join(event_bytes(item) for item in events)),
        ("access", b"\x00".join(access_bytes(item) for item in access)),
        ("assumptions", b"\x00".join(assumption_bytes(item) for item in assumptions)),
        ("counterfactuals", b"\x00".join(counterfactual_bytes(item) for item in counterfactuals)),
    ))
    logger.debug("history_digest exit")
    return result


def source_digest(
    core: str, token: str, history: str, doctrine: str, scope: str, policy: str,
) -> str:
    logger.debug("source_digest entry")
    result = digest("source", tuple(
        (name, value.encode("ascii")) for name, value in (
            ("core", core), ("token", token), ("history", history),
            ("doctrine", doctrine), ("scope", scope), ("policy", policy),
        )
    ))
    logger.debug("source_digest exit")
    return result


def judgment_digest(
    source: str, statuses: tuple[str, ...], evidence: tuple[str, ...],
) -> str:
    logger.debug("judgment_digest entry")
    result = digest("judgment", (
        ("source", source.encode("ascii")),
        ("statuses", "\x1f".join(statuses).encode()),
        ("evidence", "\x1f".join(evidence).encode()),
    ))
    logger.debug("judgment_digest exit")
    return result


def snapshot_event(value: HistoryEvent) -> HistoryEvent:
    logger.debug("snapshot_event entry")
    if type(value) is not HistoryEvent:
        reject("history-event-must-be-exact")
    try:
        event_id, kind, parents = value.event_id, value.kind, value.parent_ids
        logical_time, payload = value.logical_time, value.payload_digest
        lineage, availability = value.lineage_id, value.availability
    except AttributeError:
        reject("history-event-fields-missing")
    event_id = identifier(event_id, "event-id")
    lineage = identifier(lineage, "lineage-id")
    payload = hex_digest(payload, "event-payload-digest")
    if type(kind) is not EventKind or type(availability) is not EvidenceAvailability:
        reject("invalid-history-event-enum")
    if type(logical_time) is not int or logical_time < 0 or logical_time > 10**9:
        reject("invalid-logical-time")
    if type(parents) is not tuple or len(parents) > 64:
        reject("invalid-parent-ids")
    captured = tuple(identifier(item, "parent-event-id") for item in parents)
    if len(captured) != len(set(captured)) or event_id in captured:
        reject("duplicate-or-self-parent")
    result = HistoryEvent(
        event_id, kind, captured, logical_time, payload, lineage, availability,
    )
    logger.debug("snapshot_event exit event=%s", event_id)
    return result


def snapshot_access(value: AccessEdge) -> AccessEdge:
    logger.debug("snapshot_access entry")
    if type(value) is not AccessEdge:
        reject("access-edge-must-be-exact")
    try:
        provider, consumer, kind = (
            value.provider_event_id, value.consumer_event_id, value.kind,
        )
    except AttributeError:
        reject("access-edge-fields-missing")
    if type(kind) is not AccessKind:
        reject("invalid-access-kind")
    result = AccessEdge(
        identifier(provider, "access-provider"),
        identifier(consumer, "access-consumer"), kind,
    )
    logger.debug("snapshot_access exit")
    return result


def snapshot_assumption(value: HistoricalAssumption) -> HistoricalAssumption:
    logger.debug("snapshot_assumption entry")
    if type(value) is not HistoricalAssumption:
        reject("historical-assumption-must-be-exact")
    try:
        assumption_id = identifier(value.assumption_id, "assumption-id")
        source = identifier(value.source_event_id, "assumption-source-event")
        depends = value.depends_on
    except AttributeError:
        reject("historical-assumption-fields-missing")
    if type(depends) is not tuple or len(depends) > 64:
        reject("invalid-assumption-dependencies")
    captured = tuple(identifier(item, "assumption-dependency") for item in depends)
    if len(captured) != len(set(captured)) or assumption_id in captured:
        reject("duplicate-or-self-assumption-dependency")
    result = HistoricalAssumption(assumption_id, source, captured)
    logger.debug("snapshot_assumption exit")
    return result


def causal_sets(
    events: tuple[HistoryEvent, ...], birth_event_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, HistoryEvent]]:
    """Derive strict past/future from parent edges, never timestamps alone."""
    logger.debug("causal_sets entry events=%d", len(events))
    table = {item.event_id: item for item in events}
    if len(table) != len(events) or birth_event_id not in table:
        reject("duplicate-event-or-missing-birth")
    children = {name: [] for name in table}
    for item in events:
        for parent in item.parent_ids:
            if parent not in table:
                reject("unknown-parent-event")
            if table[parent].logical_time >= item.logical_time:
                reject("nonmonotone-parent-edge")
            children[parent].append(item.event_id)
    def walk(starts: tuple[str, ...], adjacency) -> set[str]:
        logger.debug("causal walk entry starts=%d", len(starts))
        seen: set[str] = set()
        queue = deque(starts)
        while queue:
            current = queue.popleft()
            for nxt in adjacency[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        logger.debug("causal walk exit seen=%d", len(seen))
        return seen
    past = walk(table[birth_event_id].parent_ids, {
        name: list(table[name].parent_ids) for name in table
    }) | set(table[birth_event_id].parent_ids)
    future = walk((birth_event_id,), children)
    future.discard(birth_event_id)
    order = {item.event_id: index for index, item in enumerate(events)}
    result = (
        tuple(sorted(past, key=order.__getitem__)),
        tuple(sorted(future, key=order.__getitem__)), table,
    )
    logger.debug("causal_sets exit past=%d future=%d", len(past), len(future))
    return result


def restricted_access_reaches_past(
    events: tuple[HistoryEvent, ...], access: tuple[AccessEdge, ...],
    past_ids: tuple[str, ...], protected_ids: tuple[str, ...] = (),
) -> bool:
    """Detect restricted reachability into strict past or birth dependencies."""
    logger.debug("restricted_access_reaches_past entry")
    table = {item.event_id: item for item in events}
    adjacency = {name: [] for name in table}
    for item in events:
        for parent in item.parent_ids:
            adjacency[parent].append(item.event_id)
    for edge in access:
        if edge.provider_event_id not in table or edge.consumer_event_id not in table:
            reject("access-edge-unknown-event")
        adjacency[edge.provider_event_id].append(edge.consumer_event_id)
    restricted = {
        item.event_id for item in events if item.kind in {
            EventKind.TARGET, EventKind.ORACLE, EventKind.EXPECTED_RESPONSE,
            EventKind.LATER_RESULT,
        }
    }
    protected = set(past_ids) | set(protected_ids)
    if not protected.issubset(table):
        reject("target-seal-unknown-protected-event")
    queue = deque(restricted)
    seen = set(restricted)
    if restricted & protected:
        logger.debug("restricted_access_reaches_past exit leak=true direct")
        return True
    while queue:
        current = queue.popleft()
        for nxt in adjacency[current]:
            if nxt in protected:
                logger.debug("restricted_access_reaches_past exit leak=true")
                return True
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    logger.debug("restricted_access_reaches_past exit leak=false")
    return False


def assumption_source_closure(
    assumptions: tuple[HistoricalAssumption, ...], roots: tuple[str, ...],
    events: dict[str, HistoryEvent], lineage_id: str,
) -> tuple[str, ...]:
    """Close named assumptions and reject circular actualization sources."""
    logger.debug("assumption_source_closure entry")
    table = {item.assumption_id: item for item in assumptions}
    if len(table) != len(assumptions) or any(root not in table for root in roots):
        reject("invalid-assumption-table-or-root")
    visiting: set[str] = set()
    closed: list[str] = []
    seen: set[str] = set()
    def visit(name: str) -> None:
        logger.debug("assumption visit entry name=%s", name)
        if name in visiting:
            reject("cyclic-historical-assumptions")
        if name in seen:
            return
        visiting.add(name)
        node = table[name]
        if node.source_event_id not in events:
            reject("assumption-source-unknown-event")
        for dependency in node.depends_on:
            if dependency not in table:
                reject("unknown-assumption-dependency")
            visit(dependency)
        visiting.remove(name)
        seen.add(name)
        closed.append(name)
        logger.debug("assumption visit exit name=%s", name)
    for root in roots:
        visit(root)
    forbidden = {
        EventKind.ACTUALIZATION_JUDGMENT, EventKind.ACTUALIZATION_CERTIFICATE,
    }
    for name in closed:
        event = events[table[name].source_event_id]
        if event.kind in forbidden or (
            event.kind in {EventKind.BIRTH, EventKind.COPIED_BIRTH}
            and event.lineage_id == lineage_id
        ):
            reject("circular-actualization-source-closure")
    logger.debug("assumption_source_closure exit size=%d", len(closed))
    return tuple(closed)


def source_container_preflight(
    policy: ActualizationResourcePolicy, events: object, access: object,
    assumptions: object, counterfactuals: object,
) -> tuple[ActualizationResourceBound, int, int] | None:
    """Count raw containers and parent tuple lengths before deep snapshotting."""
    logger.debug("actualization source container preflight entry")
    values = (events, access, assumptions, counterfactuals)
    if any(type(item) is not tuple for item in values):
        reject("actualization-source-containers-must-be-tuples")
    checks = (
        (len(events), policy.max_events, ActualizationResourceBound.EVENTS),
        (len(access), policy.max_access_edges, ActualizationResourceBound.ACCESS_EDGES),
        (len(assumptions), policy.max_assumptions, ActualizationResourceBound.ASSUMPTIONS),
        (len(counterfactuals), policy.max_counterfactuals,
         ActualizationResourceBound.COUNTERFACTUALS),
    )
    for required, allowed, bound in checks:
        if required > allowed:
            logger.debug("actualization source preflight exit bound=%s", bound.value)
            return bound, required, allowed
    parent_count = 0
    for event in events:
        if type(event) is not HistoryEvent:
            reject("history-event-must-be-exact")
        try:
            parents = event.parent_ids
        except AttributeError:
            reject("history-event-fields-missing")
        if type(parents) is not tuple:
            reject("invalid-parent-ids")
        parent_count += len(parents)
    if parent_count > policy.max_parent_edges:
        logger.debug("actualization source preflight exit parent bound")
        return (
            ActualizationResourceBound.PARENT_EDGES, parent_count,
            policy.max_parent_edges,
        )
    logger.debug("actualization source container preflight exit clean")
    return None


def build_policy(
    max_events: int, max_parent_edges: int, max_access_edges: int,
    max_assumptions: int, max_counterfactuals: int, max_encoded_bytes: int,
) -> ActualizationResourcePolicy:
    logger.debug("build_actualization_policy entry")
    values = (
        max_events, max_parent_edges, max_access_edges, max_assumptions,
        max_counterfactuals, max_encoded_bytes,
    )
    if any(type(item) is not int or item < 1 or item > 1_000_000 for item in values):
        reject("invalid-actualization-resource-policy")
    result = ActualizationResourcePolicy("p1-e4-policy-v1", *values, policy_digest(values))
    logger.debug("build_actualization_policy exit")
    return result


def snapshot_policy(value: ActualizationResourcePolicy) -> ActualizationResourcePolicy:
    logger.debug("snapshot_actualization_policy entry")
    if type(value) is not ActualizationResourcePolicy:
        reject("actualization-policy-must-be-exact")
    try:
        version = value.version
        values = (
            value.max_events, value.max_parent_edges, value.max_access_edges,
            value.max_assumptions, value.max_counterfactuals,
            value.max_encoded_bytes,
        )
        supplied = value.policy_digest
    except AttributeError:
        reject("actualization-policy-fields-missing")
    if type(version) is not str or version != "p1-e4-policy-v1":
        reject("actualization-policy-version-drift")
    supplied = hex_digest(supplied, "actualization-policy-digest")
    result = build_policy(*values)
    if supplied != result.policy_digest:
        reject("actualization-policy-digest-drift")
    logger.debug("snapshot_actualization_policy exit")
    return result


def _resource(
    policy: ActualizationResourcePolicy, bound: ActualizationResourceBound,
    required: int, allowed: int,
) -> ActualizationResourceLimit:
    logger.debug("actualization source resource refusal bound=%s", bound.value)
    refusal = digest("resource-refusal", (
        ("policy", policy.policy_digest.encode("ascii")),
        ("bound", bound.value.encode("ascii")),
        ("required", str(required).encode("ascii")),
        ("allowed", str(allowed).encode("ascii")),
    ))
    return ActualizationResourceLimit(
        ActualizationOperation.SOURCE, bound, required, allowed,
        policy.policy_digest, refusal,
    )


def snapshot_counterfactual(
    value: ActualizationCounterfactual,
) -> ActualizationCounterfactual:
    logger.debug("snapshot_counterfactual entry")
    if type(value) is not ActualizationCounterfactual:
        reject("actualization-counterfactual-must-be-exact")
    try:
        case_id, kind = value.case_id, value.kind
        provider, consumer = value.provider_event_id, value.consumer_event_id
        alternate, lineage, parents = (
            value.alternate_target_digest, value.copied_lineage_id,
            value.copied_parent_ids,
        )
    except AttributeError:
        reject("actualization-counterfactual-fields-missing")
    if type(kind) is not CounterfactualClass or type(parents) is not tuple:
        reject("invalid-actualization-counterfactual-shape")
    if len(parents) > 64:
        reject("actualization-counterfactual-parent-limit")
    result = ActualizationCounterfactual(
        identifier(case_id, "counterfactual-id"), kind,
        identifier(provider, "counterfactual-provider"),
        identifier(consumer, "counterfactual-consumer"),
        hex_digest(alternate, "counterfactual-target-digest"),
        identifier(lineage, "counterfactual-lineage"),
        tuple(identifier(item, "counterfactual-parent") for item in parents),
    )
    logger.debug("snapshot_counterfactual exit kind=%s", kind.value)
    return result


def _raw_type_gate(
    p0: object, construction: object, target: object, e1_doctrine: object,
    e1_source: object, witness: object, recurrence: object, oep: object,
) -> None:
    logger.debug("actualization raw type gate entry")
    expected = (
        (p0, ObserverDoctrine), (construction, ConstructionSourceBinding),
        (target, OntologyStage), (e1_doctrine, ObserverGenesisDoctrine),
        (e1_source, ObserverGenesisSource), (witness, WitnessScope),
        (oep, OEPAdmissionRecord),
    )
    if any(type(value) is not kind for value, kind in expected) or type(recurrence) not in {
        RecurrenceWitness, UnavailableRecurrenceEvidence,
    }:
        reject("actualization-raw-input-must-be-exact")
    logger.debug("actualization raw type gate exit")


def build_source(
    policy: ActualizationResourcePolicy, history_id: str, lineage_id: str,
    events: tuple[HistoryEvent, ...], access_edges: tuple[AccessEdge, ...],
    assumptions: tuple[HistoricalAssumption, ...], assumption_roots: tuple[str, ...],
    counterfactuals: tuple[ActualizationCounterfactual, ...],
    birth_event_id: str, construction_event_id: str, oep_event_id: str,
    target_event_id: str, intervention_event_id: str, response_event_id: str,
    p0_doctrine: ObserverDoctrine, construction_source: ConstructionSourceBinding,
    construction_target: OntologyStage, e1_doctrine: ObserverGenesisDoctrine,
    e1_source: ObserverGenesisSource, e1_witness: WitnessScope,
    e1_recurrence, e1_oep: OEPAdmissionRecord,
) -> ActualizationSourceResult:
    """Precharge, then bind one exact finite history and raw P1-B/E1 inputs."""
    logger.debug("build_historical_observer_source entry")
    policy = snapshot_policy(policy)
    failure = source_container_preflight(
        policy, events, access_edges, assumptions, counterfactuals,
    )
    if failure is not None:
        logger.debug("build_historical_observer_source exit resource-limit")
        return _resource(policy, *failure)
    _raw_type_gate(
        p0_doctrine, construction_source, construction_target, e1_doctrine,
        e1_source, e1_witness, e1_recurrence, e1_oep,
    )
    if (
        type(assumption_roots) is not tuple or not assumption_roots
        or not assumptions or len(assumption_roots) > policy.max_assumptions
    ):
        reject("invalid-assumption-roots")
    history_id = identifier(history_id, "history-id")
    lineage_id = identifier(lineage_id, "lineage-id")
    ids = tuple(identifier(item, "designated-event-id") for item in (
        birth_event_id, construction_event_id, oep_event_id, target_event_id,
        intervention_event_id, response_event_id,
    ))
    if len(set(ids)) != len(ids):
        reject("designated-events-must-be-distinct")
    roots = tuple(identifier(item, "assumption-root") for item in assumption_roots)
    captured_events = tuple(snapshot_event(item) for item in events)
    captured_access = tuple(snapshot_access(item) for item in access_edges)
    captured_assumptions = tuple(snapshot_assumption(item) for item in assumptions)
    captured_cases = tuple(snapshot_counterfactual(item) for item in counterfactuals)
    if tuple(item.kind for item in captured_cases) != tuple(CounterfactualClass):
        reject("counterfactual-catalog-must-be-exact-three-class-order")
    if len({item.case_id for item in captured_cases}) != 3:
        reject("duplicate-counterfactual-id")
    past_ids, _, table = causal_sets(captured_events, ids[0])
    if sum(item.kind.value == "birth" for item in captured_events) != 1:
        reject("history-must-have-one-declared-birth")
    if any(name not in table for name in ids):
        reject("designated-event-missing")
    encoded = sum(map(len, (
        *(event_bytes(item) for item in captured_events),
        *(access_bytes(item) for item in captured_access),
        *(assumption_bytes(item) for item in captured_assumptions),
        *(counterfactual_bytes(item) for item in captured_cases),
    )))
    if encoded > policy.max_encoded_bytes:
        return _resource(
            policy, ActualizationResourceBound.ENCODED_BYTES,
            encoded, policy.max_encoded_bytes,
        )
    try:
        construction_digest = construction_source.membership_digest
        e1_source_digest = e1_source.source_digest
        oep_digest = e1_oep.oep_digest
        target_stage_digest = stage_commitment(construction_target)
        witness_digest = e1_witness.witness_digest
        recurrence_digest = e1_recurrence.recurrence_digest
        p0_digest = p0_doctrine.fingerprint
        e1_doctrine_digest = e1_doctrine.doctrine_digest
    except AttributeError:
        reject("actualization-raw-binding-fields-missing")
    for value in (
        construction_digest, e1_source_digest, oep_digest, target_stage_digest,
        witness_digest, recurrence_digest, p0_digest, e1_doctrine_digest,
    ):
        hex_digest(value, "actualization-raw-binding-digest")
    past = tuple(table[name] for name in past_ids)
    core = birth_core_digest(
        history_id, lineage_id, past, table[ids[0]],
        construction_digest, e1_source_digest, oep_digest, target_stage_digest,
        witness_digest, recurrence_digest,
    )
    token = token_digest(core, lineage_id, ids[0])
    history = history_digest(
        history_id, token, captured_events, captured_access,
        captured_assumptions, captured_cases,
    )
    doctrine = digest("doctrine", (
        ("p0", p0_digest.encode("ascii")),
        ("e1", e1_doctrine_digest.encode("ascii")),
    ))
    scope = digest("scope", (
        ("stage", target_stage_digest.encode("ascii")),
        ("witness", witness_digest.encode("ascii")),
    ))
    source = source_digest(core, token, history, doctrine, scope, policy.policy_digest)
    result = HistoricalObserverSource(
        "p1-e4-source-v1", history_id, lineage_id, captured_events,
        captured_access, captured_assumptions, roots, captured_cases, *ids,
        policy, p0_doctrine, construction_source, construction_target,
        e1_doctrine, e1_source, e1_witness, e1_recurrence, e1_oep,
        core, token, history, doctrine, scope, source,
    )
    logger.debug("build_historical_observer_source exit")
    return result


def snapshot_source(value: HistoricalObserverSource) -> HistoricalObserverSource:
    """Rebuild a source from exact fields and reject all digest/transplant drift."""
    logger.debug("snapshot_historical_observer_source entry")
    if type(value) is not HistoricalObserverSource:
        reject("historical-observer-source-must-be-exact")
    try:
        version = value.version
        supplied = (
            value.birth_core_digest, value.historical_token_id, value.history_digest,
            value.doctrine_digest, value.scope_digest, value.source_digest,
        )
        result = build_source(
            value.policy, value.history_id, value.lineage_id, value.events,
            value.access_edges, value.assumptions, value.assumption_roots,
            value.counterfactuals, value.birth_event_id,
            value.construction_event_id, value.oep_event_id, value.target_event_id,
            value.intervention_event_id, value.response_event_id, value.p0_doctrine,
            value.construction_source, value.construction_target, value.e1_doctrine,
            value.e1_source, value.e1_witness, value.e1_recurrence, value.e1_oep,
        )
    except AttributeError:
        reject("historical-observer-source-fields-missing")
    if type(version) is not str or version != "p1-e4-source-v1":
        reject("historical-observer-source-version-drift")
    if type(result) is ActualizationResourceLimit:
        reject("historical-observer-source-resource-drift")
    if any(type(item) is not str for item in supplied) or supplied != (
        result.birth_core_digest, result.historical_token_id, result.history_digest,
        result.doctrine_digest, result.scope_digest, result.source_digest,
    ):
        reject("historical-observer-source-digest-drift")
    logger.debug("snapshot_historical_observer_source exit")
    return result


def target_seal_breached(
    source: HistoricalObserverSource, past_ids: tuple[str, ...],
    assumption_source_ids: set[str],
) -> bool:
    """Seal strict past, birth, and every declared birth-core dependency."""
    logger.debug("target seal audit entry")
    protected = (
        source.birth_event_id, source.construction_event_id, source.oep_event_id,
        *sorted(assumption_source_ids),
    )
    result = restricted_access_reaches_past(
        source.events, source.access_edges, past_ids, protected,
    )
    logger.debug("target seal audit exit breached=%s", result)
    return result


def assumption_sources_outside_past(
    assumption_source_ids: set[str], past_ids: tuple[str, ...],
) -> bool:
    """Report a concrete provenance contradiction at the birth cut."""
    logger.debug("assumption strict-past audit entry")
    result = not assumption_source_ids.issubset(set(past_ids))
    logger.debug("assumption strict-past audit exit outside=%s", result)
    return result


def _ancestors(event_id: str, table: dict[str, HistoryEvent]) -> set[str]:
    logger.debug("efficacy ancestor walk entry event=%s", event_id)
    seen: set[str] = set()
    queue = deque(table[event_id].parent_ids)
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(table[current].parent_ids)
    logger.debug("efficacy ancestor walk exit event=%s count=%d", event_id, len(seen))
    return seen


def efficacy_pressure(
    source: HistoricalObserverSource, future_ids: tuple[str, ...],
    table: dict[str, HistoryEvent], genesis,
) -> tuple[bool, bool]:
    """Bind every claimed efficacy trace to the exact birth token and scope."""
    logger.debug("same-token efficacy audit entry")
    if type(genesis) is not GenesisJudgment:
        logger.debug("same-token efficacy audit exit unavailable raw-e1-result")
        return False, True
    intervention = table[source.intervention_event_id]
    response = table[source.response_event_id]
    expected_response = (
        genesis.premises[5].evidence_digest
        if type(genesis) is GenesisJudgment else None
    )
    traces = tuple(
        item for item in source.events
        if item.kind in {EventKind.INTERVENTION, EventKind.RESPONSE}
    )
    trace_contradiction = False
    for event in traces:
        ancestors = _ancestors(event.event_id, table)
        birth_ancestors = {
            name for name in ancestors
            if table[name].kind in {EventKind.BIRTH, EventKind.COPIED_BIRTH}
        }
        same_token = birth_ancestors == {source.birth_event_id} and token_digest(
            source.birth_core_digest, event.lineage_id, source.birth_event_id,
        ) == source.historical_token_id
        lineage_closed = all(
            table[name].lineage_id == source.lineage_id
            for name in ancestors
            if name in future_ids or name == source.birth_event_id
        )
        response_has_intervention = (
            event.kind is not EventKind.RESPONSE
            or any(table[name].kind is EventKind.INTERVENTION for name in ancestors)
        )
        payload_matches_scope = (
            event.payload_digest == source.e1_witness.witness_digest
            if event.kind is EventKind.INTERVENTION
            else expected_response is not None
            and event.payload_digest == expected_response
        )
        trace_contradiction = trace_contradiction or (
            event.lineage_id != source.lineage_id
            or not same_token
            or not lineage_closed
            or not response_has_intervention
            or event.event_id not in future_ids
            or not payload_matches_scope
        )
    contradicted = trace_contradiction or (
        type(genesis) is GenesisJudgment
        and genesis.residue_efficacy is PremiseStatus.REFUTED
    ) or (
        intervention.kind is not EventKind.INTERVENTION
        or response.kind is not EventKind.RESPONSE
        or source.intervention_event_id not in response.parent_ids
    )
    unavailable = (
        type(genesis) is not GenesisJudgment
        or genesis.residue_efficacy is PremiseStatus.OPEN
        or any(item.availability is EvidenceAvailability.UNAVAILABLE for item in traces)
    )
    logger.debug(
        "same-token efficacy audit exit contradicted=%s unavailable=%s",
        contradicted, unavailable,
    )
    return contradicted, unavailable


def _case_unavailable(
    source: HistoricalObserverSource, case, table,
) -> bool:
    """Treat absent/unavailable required counterfactual provenance as OPEN."""
    logger.debug("counterfactual availability entry kind=%s", case.kind.value)
    required = (case.provider_event_id, case.consumer_event_id)
    if case.kind is CounterfactualClass.FOREIGN_PARENT_COPY:
        required += case.copied_parent_ids
    result = any(
        name not in table
        or table[name].availability is EvidenceAvailability.UNAVAILABLE
        for name in required
    )
    logger.debug("counterfactual availability exit unavailable=%s", result)
    return result


def counterfactual_evidence(
    source: HistoricalObserverSource, past_ids: tuple[str, ...],
) -> tuple[CounterfactualEvidence, ...]:
    """Replay the exact three pressures with missing evidence kept OPEN."""
    logger.debug("counterfactual evidence entry")
    table = {item.event_id: item for item in source.events}
    target = table[source.target_event_id]
    birth = table[source.birth_event_id]
    rows: list[CounterfactualEvidence] = []
    for case in source.counterfactuals:
        unavailable = _case_unavailable(source, case, table)
        passed = False
        contradicted = False
        detail: tuple[tuple[str, bytes], ...]
        if case.kind is CounterfactualClass.PREFIX_TARGET_VARIATION:
            contradicted = (
                case.provider_event_id != source.target_event_id
                or case.consumer_event_id != source.response_event_id
                or target.event_id in past_ids
                or case.alternate_target_digest == target.payload_digest
            )
            varied = tuple(
                replace(item, payload_digest=case.alternate_target_digest)
                if item.event_id == source.target_event_id else item
                for item in source.events
            )
            alternate_history = history_digest(
                source.history_id, source.historical_token_id, varied,
                source.access_edges, source.assumptions, source.counterfactuals,
            )
            passed = (
                not contradicted and alternate_history != source.history_digest
            )
            detail = (("alternate-history", alternate_history.encode("ascii")),)
        elif case.kind is CounterfactualClass.TARGET_READING_CHOOSER:
            contradicted = (
                case.provider_event_id != source.target_event_id
                or case.consumer_event_id != source.construction_event_id
            )
            if unavailable:
                detail = (("availability", b"unavailable"),)
            else:
                simulated = source.access_edges + (AccessEdge(
                    case.provider_event_id, case.consumer_event_id,
                    AccessKind.TARGET_READ,
                ),)
                passed = not contradicted and restricted_access_reaches_past(
                    source.events, simulated, past_ids,
                    (source.birth_event_id, source.construction_event_id,
                     source.oep_event_id),
                )
                detail = (("simulated-leak", str(passed).encode("ascii")),)
        else:
            copied_token = token_digest(
                source.birth_core_digest, case.copied_lineage_id, case.case_id,
            )
            contradicted = (
                case.provider_event_id != source.birth_event_id
                or case.consumer_event_id != source.response_event_id
                or case.copied_lineage_id == source.lineage_id
                or case.copied_parent_ids == birth.parent_ids
                or copied_token == source.historical_token_id
            )
            passed = (
                not contradicted
                and all(name in table for name in case.copied_parent_ids)
            )
            detail = (
                ("copied-lineage", case.copied_lineage_id.encode()),
                ("copied-parents", "\x1f".join(case.copied_parent_ids).encode()),
                ("copied-token", copied_token.encode("ascii")),
            )
        outcome = (
            CounterfactualOutcome.FAILED if contradicted
            else CounterfactualOutcome.OPEN if unavailable
            else CounterfactualOutcome.PASSED if passed
            else CounterfactualOutcome.FAILED
        )
        evidence = digest("counterfactual-evidence", (
            ("case", case.case_id.encode()), ("kind", case.kind.value.encode()),
            ("outcome", outcome.value.encode()), *detail,
        ))
        rows.append(CounterfactualEvidence(case.case_id, case.kind, outcome, evidence))
    result = tuple(rows)
    logger.debug("counterfactual evidence exit rows=%d", len(result))
    return result


def _status(
    *, contradicted: bool = False, unavailable: bool = False,
) -> ActualizationStatus:
    logger.debug("actualization status entry")
    if contradicted:
        result = ActualizationStatus.REFUTED
    elif unavailable:
        result = ActualizationStatus.OPEN
    else:
        result = ActualizationStatus.ESTABLISHED
    logger.debug("actualization status exit status=%s", result.value)
    return result


def _birth_status(
    source: HistoricalObserverSource, past_ids: tuple[str, ...],
    table, assumption_source_ids: set[str], assumptions_outside_past: bool,
) -> ActualizationStatus:
    logger.debug("birth status entry")
    birth = table[source.birth_event_id]
    construction = table[source.construction_event_id]
    oep = table[source.oep_event_id]
    earlier_same_lineage = any(
        table[name].kind in {EventKind.BIRTH, EventKind.COPIED_BIRTH}
        and table[name].lineage_id == source.lineage_id
        for name in past_ids
    )
    contradicted = (
        birth.kind is not EventKind.BIRTH or birth.lineage_id != source.lineage_id
        or source.construction_event_id not in past_ids
        or source.oep_event_id not in past_ids or earlier_same_lineage
        or assumptions_outside_past
        or construction.payload_digest != source.construction_source.membership_digest
        or oep.payload_digest != source.e1_oep.oep_digest
        or birth.payload_digest != source.e1_source.source_digest
    )
    unavailable = (
        not {source.construction_event_id, source.oep_event_id}.issubset(
            assumption_source_ids
        )
        or any(item.availability is EvidenceAvailability.UNAVAILABLE for item in (
            birth, construction, oep,
        ))
    )
    result = _status(contradicted=contradicted, unavailable=unavailable)
    logger.debug("birth status exit status=%s", result.value)
    return result


def _target_status(
    source: HistoricalObserverSource, future_ids: tuple[str, ...], table,
    evidence: tuple[CounterfactualEvidence, ...], leak: bool,
) -> ActualizationStatus:
    logger.debug("target status entry")
    target = table[source.target_event_id]
    contradicted = (
        leak or target.kind is not EventKind.TARGET
        or source.target_event_id not in future_ids
        or any(item.outcome is CounterfactualOutcome.FAILED for item in evidence)
    )
    unavailable = (
        target.availability is EvidenceAvailability.UNAVAILABLE
        or any(item.outcome is CounterfactualOutcome.OPEN for item in evidence)
    )
    result = _status(contradicted=contradicted, unavailable=unavailable)
    logger.debug("target status exit status=%s", result.value)
    return result


def _make_judgment(
    source: HistoricalObserverSource, past: tuple[str, ...], future: tuple[str, ...],
    evidence: tuple[CounterfactualEvidence, ...], oep: ActualizationStatus,
    construction: ActualizationStatus, birth: ActualizationStatus,
    target: ActualizationStatus, efficacy: ActualizationStatus,
    replay_and_closure: tuple[str, ...],
) -> HistoricalActualizationJudgment:
    logger.debug("make actualization judgment entry")
    statuses = (oep, construction, birth, target, efficacy)
    historical = (
        HistoricalActualization.ESTABLISHED_RELATIVE_TO_HISTORY
        if all(item is ActualizationStatus.ESTABLISHED for item in statuses)
        else HistoricalActualization.OPEN
    )
    commitment = judgment_digest(
        source.source_digest,
        tuple(item.value for item in statuses) + (historical.value,),
        tuple(item.evidence_digest for item in evidence)
        + past + future + replay_and_closure,
    )
    result = HistoricalActualizationJudgment(
        source.source_digest, source.birth_core_digest,
        source.historical_token_id, source.history_digest,
        source.doctrine_digest, source.scope_digest, past, future, evidence,
        oep, construction, birth, target, efficacy, historical, commitment,
    )
    logger.debug("make actualization judgment exit status=%s", historical.value)
    return result


def historical_actualization_judgment(
    source: HistoricalObserverSource,
) -> HistoricalActualizationJudgment:
    """Apply HAP after structural target-leak pressure and fresh raw replay."""
    logger.debug("historical_actualization_judgment entry")
    source = snapshot_source(source)
    past, future, table = causal_sets(source.events, source.birth_event_id)
    assumption_closure = assumption_source_closure(
        source.assumptions, source.assumption_roots, table, source.lineage_id,
    )
    assumption_table = {item.assumption_id: item for item in source.assumptions}
    assumption_sources = {
        assumption_table[name].source_event_id for name in assumption_closure
    }
    evidence = counterfactual_evidence(source, past)
    assumptions_outside_past = assumption_sources_outside_past(
        assumption_sources, past,
    )
    leak = target_seal_breached(source, past, assumption_sources)
    target = _target_status(source, future, table, evidence, leak)
    if leak:
        logger.debug("historical_actualization_judgment target leak before replay")
        result = _make_judgment(
            source, past, future, evidence, ActualizationStatus.OPEN,
            ActualizationStatus.OPEN, ActualizationStatus.OPEN, target,
            ActualizationStatus.OPEN,
            ("p1b-replay-withheld-target-leak", "e1-replay-withheld-target-leak")
            + assumption_closure,
        )
        logger.debug("historical_actualization_judgment exit leak-refuted")
        return result
    construction_row = finite_construction_judgment(
        source.p0_doctrine, source.construction_source, source.construction_target,
    )
    construction = _status(
        contradicted=construction_row.formal_generability
        is not FormalGenerability.GENERABLE,
        unavailable=table[source.construction_event_id].availability
        is EvidenceAvailability.UNAVAILABLE,
    )
    genesis = observer_genesis_judgment(
        source.e1_doctrine, source.e1_source, source.e1_witness,
        source.e1_recurrence, source.e1_oep,
    )
    oep = _status(
        unavailable=type(genesis) is not GenesisJudgment
        or genesis.observer_role_relative_to_scope is not ObserverRole.ESTABLISHED
        or table[source.oep_event_id].availability is EvidenceAvailability.UNAVAILABLE,
    )
    birth = _birth_status(
        source, past, table, assumption_sources, assumptions_outside_past,
    )
    efficacy_contradicted, efficacy_open = efficacy_pressure(
        source, future, table, genesis,
    )
    efficacy = _status(
        contradicted=efficacy_contradicted, unavailable=efficacy_open,
    )
    replay_evidence = (
        construction_row.replay.trace_digest,
        genesis.judgment_digest if type(genesis) is GenesisJudgment
        else genesis.refusal_digest,
    ) + assumption_closure
    result = _make_judgment(
        source, past, future, evidence, oep, construction, birth, target, efficacy,
        replay_evidence,
    )
    logger.debug("historical_actualization_judgment exit")
    return result


def _result_envelope(
    source: HistoricalObserverSource, value: HistoricalActualizationJudgment,
) -> tuple:
    """Exact-type and shallow-size gate with no semantic replay or equality."""
    logger.debug("actualization result envelope entry")
    if type(value) is not HistoricalActualizationJudgment:
        reject("historical-actualization-judgment-must-be-exact")
    try:
        digests = (
            value.source_digest, value.birth_core_digest,
            value.historical_token_id, value.history_digest,
            value.doctrine_digest, value.scope_digest,
            value.actualization_judgment_digest,
        )
        past, future, rows = (
            value.past_event_ids, value.future_event_ids,
            value.counterfactual_evidence,
        )
        statuses = (
            value.oep_role, value.prior_construction, value.birth_event,
            value.target_independence, value.post_birth_efficacy,
        )
        tail = (
            value.historical_actualization, value.operation_status,
            value.physical_instantiation, value.consciousness, value.scope,
        )
    except AttributeError:
        reject("historical-actualization-judgment-fields-missing")
    if type(source) is not HistoricalObserverSource:
        reject("historical-observer-source-must-be-exact")
    try:
        policy = source.policy
    except AttributeError:
        reject("historical-observer-source-fields-missing")
    if type(policy) is not ActualizationResourcePolicy:
        reject("actualization-policy-must-be-exact")
    try:
        max_events, max_cases = policy.max_events, policy.max_counterfactuals
    except AttributeError:
        reject("actualization-policy-fields-missing")
    if (
        type(max_events) is not int or type(max_cases) is not int
        or type(past) is not tuple or type(future) is not tuple
        or type(rows) is not tuple
        or len(past) > max_events or len(future) > max_events
        or len(rows) > max_cases
        or any(type(item) is not str for item in digests)
        or any(type(item) is not ActualizationStatus for item in statuses)
        or type(tail[0]) is not HistoricalActualization
        or type(tail[1]) is not ActualizationOperationStatus
        or type(tail[2]) is not PhysicalInstantiation
        or type(tail[3]) is not ConsciousnessStatus
        or type(tail[4]) is not str
    ):
        reject("historical-actualization-judgment-envelope")
    if (
        any(type(item) is not str for item in past)
        or any(type(item) is not str for item in future)
        or any(type(item) is not CounterfactualEvidence for item in rows)
    ):
        reject("historical-actualization-judgment-envelope-element-type")
    if len(rows) != 3:
        reject("historical-actualization-judgment-envelope")
    for item in digests:
        hex_digest(item, "historical-actualization-result-digest")
    if (
        tail[1] is not ActualizationOperationStatus.JUDGED
        or tail[2] is not PhysicalInstantiation.NOT_ESTABLISHED
        or tail[3] is not ConsciousnessStatus.NOT_CLAIMED
        or tail[4] != "finite-history-relative-observer-actualization-only"
    ):
        reject("historical-actualization-judgment-envelope")
    logger.debug("actualization result envelope exit")
    return digests, past, future, rows, statuses, tail


def _counterfactual(
    value: CounterfactualEvidence, expected: CounterfactualEvidence,
) -> CounterfactualEvidence:
    logger.debug("validate counterfactual evidence entry")
    if type(value) is not CounterfactualEvidence:
        reject("counterfactual-evidence-must-be-exact")
    try:
        case_id, kind, outcome, evidence = (
            value.case_id, value.kind, value.outcome, value.evidence_digest,
        )
    except AttributeError:
        reject("counterfactual-evidence-fields-missing")
    case_id = identifier(case_id, "counterfactual-evidence-id")
    evidence = hex_digest(evidence, "counterfactual-evidence-digest")
    if (
        type(kind) is not CounterfactualClass
        or type(outcome) is not CounterfactualOutcome
        or case_id != expected.case_id or kind is not expected.kind
        or outcome is not expected.outcome or evidence != expected.evidence_digest
    ):
        reject("counterfactual-evidence-drift")
    result = CounterfactualEvidence(case_id, kind, outcome, evidence)
    logger.debug("validate counterfactual evidence exit")
    return result


def validate_actualization_result(
    source: HistoricalObserverSource, value: HistoricalActualizationJudgment,
) -> HistoricalActualizationJudgment:
    """Replay raw source evidence and return a fresh exact result."""
    logger.debug("validate_actualization_result entry")
    digests, past, future, rows, statuses, tail = _result_envelope(source, value)
    historical, operation, physical, consciousness, scope = tail
    expected = historical_actualization_judgment(source)
    expected_digests = (
        expected.source_digest, expected.birth_core_digest,
        expected.historical_token_id, expected.history_digest,
        expected.doctrine_digest, expected.scope_digest,
        expected.actualization_judgment_digest,
    )
    if (
        digests != expected_digests
        or type(past) is not tuple or len(past) != len(expected.past_event_ids)
        or type(future) is not tuple or len(future) != len(expected.future_event_ids)
        or statuses != (
            expected.oep_role, expected.prior_construction,
            expected.birth_event, expected.target_independence,
            expected.post_birth_efficacy,
        )
        or historical is not expected.historical_actualization
        or operation is not ActualizationOperationStatus.JUDGED
        or physical is not PhysicalInstantiation.NOT_ESTABLISHED
        or consciousness is not ConsciousnessStatus.NOT_CLAIMED
        or scope != "finite-history-relative-observer-actualization-only"
    ):
        reject("historical-actualization-judgment-outer-drift")
    captured_past = tuple(identifier(item, "past-event-id") for item in past)
    captured_future = tuple(identifier(item, "future-event-id") for item in future)
    if captured_past != expected.past_event_ids or captured_future != expected.future_event_ids:
        reject("historical-actualization-causal-set-drift")
    for item, wanted in zip(rows, expected.counterfactual_evidence, strict=True):
        _counterfactual(item, wanted)
    logger.debug("validate_actualization_result exit")
    return expected


def actualization_resource_policy(
    max_events: int = 64, max_parent_edges: int = 256,
    max_access_edges: int = 256, max_assumptions: int = 128,
    max_counterfactuals: int = 3, max_encoded_bytes: int = 65_536,
) -> ActualizationResourcePolicy:
    """Build the explicit E4 graph/resource envelope."""
    logger.debug("actualization_resource_policy entry")
    result = build_policy(
        max_events, max_parent_edges, max_access_edges, max_assumptions,
        max_counterfactuals, max_encoded_bytes,
    )
    logger.debug("actualization_resource_policy exit")
    return result


def history_event(
    event_id: str, kind: EventKind, parent_ids: tuple[str, ...],
    logical_time: int, payload_digest: str, lineage_id: str,
    availability: EvidenceAvailability = EvidenceAvailability.AVAILABLE,
) -> HistoryEvent:
    """Create one raw event; source construction performs exact validation."""
    logger.debug("history_event entry event=%s", event_id)
    result = HistoryEvent(
        event_id, kind, parent_ids, logical_time, payload_digest, lineage_id,
        availability,
    )
    logger.debug("history_event exit event=%s", event_id)
    return result


def access_edge(
    provider_event_id: str, consumer_event_id: str, kind: AccessKind,
) -> AccessEdge:
    """Create one typed information-flow edge."""
    logger.debug("access_edge entry")
    result = AccessEdge(provider_event_id, consumer_event_id, kind)
    logger.debug("access_edge exit")
    return result


def historical_assumption(
    assumption_id: str, source_event_id: str, depends_on: tuple[str, ...],
) -> HistoricalAssumption:
    """Create one named assumption-DAG node bound to a source event."""
    logger.debug("historical_assumption entry")
    result = HistoricalAssumption(
        assumption_id, source_event_id, depends_on,
    )
    logger.debug("historical_assumption exit")
    return result


def actualization_counterfactual(
    case_id: str, kind: CounterfactualClass,
    provider_event_id: str, consumer_event_id: str,
    alternate_target_digest: str, copied_lineage_id: str,
    copied_parent_ids: tuple[str, ...],
) -> ActualizationCounterfactual:
    """Create one closed counterfactual mutation descriptor."""
    logger.debug("actualization_counterfactual entry kind=%s", kind.value)
    result = ActualizationCounterfactual(
        case_id, kind, provider_event_id, consumer_event_id,
        alternate_target_digest, copied_lineage_id, copied_parent_ids,
    )
    logger.debug("actualization_counterfactual exit kind=%s", kind.value)
    return result


def historical_observer_source(
    policy: ActualizationResourcePolicy, history_id: str, lineage_id: str,
    events: tuple[HistoryEvent, ...], access_edges: tuple[AccessEdge, ...],
    assumptions: tuple[HistoricalAssumption, ...],
    assumption_roots: tuple[str, ...],
    counterfactuals: tuple[ActualizationCounterfactual, ...],
    birth_event_id: str, construction_event_id: str, oep_event_id: str,
    target_event_id: str, intervention_event_id: str, response_event_id: str,
    p0_doctrine: ObserverDoctrine, construction_source: ConstructionSourceBinding,
    construction_target: OntologyStage, e1_doctrine: ObserverGenesisDoctrine,
    e1_source: ObserverGenesisSource, e1_witness: WitnessScope,
    e1_recurrence: RecurrenceEvidence, e1_oep: OEPAdmissionRecord,
) -> ActualizationSourceResult:
    """Bind one finite event DAG to raw P1-B and E1 evidence."""
    logger.debug("historical_observer_source entry")
    result = build_source(
        policy, history_id, lineage_id, events, access_edges, assumptions,
        assumption_roots, counterfactuals, birth_event_id, construction_event_id,
        oep_event_id, target_event_id, intervention_event_id, response_event_id,
        p0_doctrine, construction_source, construction_target, e1_doctrine,
        e1_source, e1_witness, e1_recurrence, e1_oep,
    )
    logger.debug("historical_observer_source exit type=%s", type(result).__name__)
    return result


__all__ = (
    "ObserverActualizationValidationError", "actualization_resource_policy",
    "history_event", "access_edge", "historical_assumption",
    "actualization_counterfactual", "historical_observer_source",
    "historical_actualization_judgment", "validate_actualization_result",
    "ActualizationStatus", "HistoricalActualization", "PhysicalInstantiation",
    "ConsciousnessStatus", "EventKind", "EvidenceAvailability", "AccessKind",
    "CounterfactualClass", "CounterfactualOutcome", "ActualizationOperation",
    "ActualizationOperationStatus", "ActualizationResourceBound",
    "HistoryEvent", "AccessEdge", "HistoricalAssumption",
    "ActualizationCounterfactual", "ActualizationResourcePolicy",
    "HistoricalObserverSource", "CounterfactualEvidence",
    "HistoricalActualizationJudgment", "ActualizationResourceLimit",
    "ActualizationSourceResult", "ActualizationResult",
)
