"""Fresh raw P1-A and P1-A2 replay bridge for P3-T."""

from __future__ import annotations

import logging

from ..relations.request import observer_relation_scope
from ..relations.runtime import observer_relation_judgment
from ..relations.translation import morphism_replay_spec
from ..relations.types import (
    ComparisonMode,
    LawStatus as P1LawStatus,
    ObserverRelationJudgment,
)
from .common import reject
from .types import LawStatus, ObserverNetworkSource

logger = logging.getLogger(__name__)


def replay_raw_pair(source: ObserverNetworkSource, source_id: str, target_id: str) -> ObserverRelationJudgment:
    """Replay one committed raw ordered P1-A2 source, plus raw P1-A when declared."""
    logger.debug("replay_raw_pair entry source=%s target=%s", source_id, target_id)
    raw = next(
        (x for x in source.raw_pairs if (x.source_observer_id, x.target_observer_id) == (source_id, target_id)), None
    )
    if raw is None:
        reject("raw-p1a2-pair-source-missing")
    keys = tuple((x.stage_id, x.commitment) for x in source.p1a_stage_source.stages)
    mode = ComparisonMode.WITH_P1A_REPLAY if raw.projection is not None else ComparisonMode.EXTENSIONAL_ONLY
    scope = observer_relation_scope(
        source.p1a_doctrine, source.p1a_binding, source.p1a_stage_source, source_id, target_id, keys, mode
    )
    forward = (
        None if raw.projection is None else morphism_replay_spec(raw.morphism_id, source_id, target_id, raw.projection)
    )
    result = observer_relation_judgment(
        source.p1a_doctrine, source.p1a_binding, source.p1a_stage_source, scope, forward
    )
    if type(result) is not ObserverRelationJudgment:
        reject("raw-p1a2-resource-refusal")
    logger.debug("replay_raw_pair exit class=%s", result.classification.value)
    return result


def map_p1_law(status: P1LawStatus) -> LawStatus:
    """Map only exact upstream three-way law status without strengthening it."""
    logger.debug("map_p1_law entry type=%s", type(status).__name__)
    mapping = {
        P1LawStatus.ESTABLISHED: LawStatus.ESTABLISHED,
        P1LawStatus.REFUTED: LawStatus.REFUTED,
        P1LawStatus.OPEN: LawStatus.OPEN,
    }
    if type(status) is not P1LawStatus:
        reject("raw-p1a2-law-status-invalid")
    result = mapping[status]
    logger.debug("map_p1_law exit status=%s", result.value)
    return result


def witness_input_ids(source: ObserverNetworkSource, judgment: ObserverRelationJudgment, kind: str):
    """Resolve one exact upstream pair witness back to bound input occurrence IDs."""
    logger.debug("witness_input_ids entry kind=%s", kind)
    witness = judgment.preservation_witness if kind == "preservation" else judgment.reflection_witness
    if witness is None:
        logger.debug("witness_input_ids exit absent")
        return None
    row = judgment.pairs[witness.pair_index]
    mapping = {x.stage_commitment: x.input_id for x in source.inputs}
    result = (mapping[row.left[1]], mapping[row.right[1]])
    logger.debug("witness_input_ids exit present")
    return result
