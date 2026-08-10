"""Finite P1-E4 Historical Actualization Principle runtime."""

from __future__ import annotations

import logging

from .construction.finite_builder.types import FormalGenerability
from .finite_construction import finite_construction_judgment
from .observer_actualization_audits import (
    assumption_sources_outside_past, efficacy_pressure, target_seal_breached,
)
from .observer_actualization_counterfactuals import counterfactual_evidence
from .observer_actualization_digest import judgment_digest
from .observer_actualization_graph import (
    assumption_source_closure, causal_sets,
)
from .observer_actualization_types import (
    ActualizationStatus, CounterfactualEvidence, CounterfactualOutcome,
    EventKind, EvidenceAvailability, HistoricalActualization,
    HistoricalActualizationJudgment, HistoricalObserverSource,
)
from .observer_actualization_validation import snapshot_source
from .observer_genesis import observer_genesis_judgment
from .observer_genesis_types import (
    GenesisJudgment, ObserverRole,
)

logger = logging.getLogger(__name__)


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
