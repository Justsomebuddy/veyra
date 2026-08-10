"""Construction and fresh validation for finite P1-E4 source packages."""
from __future__ import annotations
import logging
from .construction.finite_builder.types import ConstructionSourceBinding
from .observer_actualization_digest import (
    access_bytes, assumption_bytes, birth_core_digest, counterfactual_bytes,
    digest, event_bytes, history_digest, policy_digest, source_digest,
    token_digest,
)
from .observer_actualization_graph import (
    causal_sets, hex_digest, identifier, reject, snapshot_access,
    snapshot_assumption, snapshot_event,
)
from .observer_actualization_preflight import source_container_preflight
from .observer_actualization_types import (
    AccessEdge, ActualizationCounterfactual, ActualizationOperation,
    ActualizationResourceBound, ActualizationResourceLimit,
    ActualizationResourcePolicy, ActualizationSourceResult,
    CounterfactualClass, HistoricalAssumption, HistoricalObserverSource,
    HistoryEvent,
)
from .observer_genesis_types import (
    OEPAdmissionRecord, ObserverGenesisDoctrine, ObserverGenesisSource,
    RecurrenceWitness, UnavailableRecurrenceEvidence, WitnessScope,
)
from .positive_ontology_doctrine import stage_commitment
from .positive_ontology_types import ObserverDoctrine, OntologyStage
logger = logging.getLogger(__name__)
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
