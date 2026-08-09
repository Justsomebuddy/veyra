"""Fresh R11 stage and full ordered-pair replay for P1-A2."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import logging

from ...observer_core_codec import decode_observer
from ...observer_core_semantics import observe
from ...observer_core_support import obstruction_data, response_data
from ...observer_core_types import Blocked, Observation, Ready
from .digest import (
    observation_row_digest, pair_row_digest, response_payload_digest,
)
from .types import RelationRequest
from .types import (
    PairOutcome, RelationPairRow, RelationRunStatus, StageObservationRow,
)
from ...ontology.types import ObserverDoctrine
from .validation import reject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StageReplay:
    """Private fresh outcomes plus immutable public observation row."""

    row: StageObservationRow
    fine: Observation
    coarse: Observation
    fine_bytes: bytes
    coarse_bytes: bytes


def replay_stage_rows(
    doctrine: ObserverDoctrine, request: RelationRequest,
) -> tuple[StageReplay, ...]:
    """Freshly evaluate both exact observers on every ordered stage."""
    logger.debug("replay_stage_rows entry stages=%d", len(request.scope.stages))
    members = {item.observer_id: item for item in doctrine.observers}
    fine_program = decode_observer(members[request.scope.fine_observer_id].canonical)
    coarse_program = decode_observer(members[request.scope.coarse_observer_id].canonical)
    output: list[StageReplay] = []
    stage_map = {
        (item.stage_id, item.commitment): item for item in request.source.stages
    }
    for key in request.scope.stages:
        stage = stage_map[key]
        fine = observe(fine_program, stage.recurrence)
        coarse = observe(coarse_program, stage.recurrence)
        fine_bytes = observation_bytes(fine)
        coarse_bytes = observation_bytes(coarse)
        provisional = StageObservationRow(
            (stage.stage_id, stage.commitment), _run_status(fine),
            _run_status(coarse), response_payload_digest(fine_bytes),
            response_payload_digest(coarse_bytes), "",
        )
        row = replace(provisional, row_digest=observation_row_digest(provisional))
        output.append(StageReplay(row, fine, coarse, fine_bytes, coarse_bytes))
    result = tuple(output)
    logger.debug("replay_stage_rows exit rows=%d", len(result))
    return result


def replay_pair_rows(stages: tuple[StageReplay, ...]) -> tuple[RelationPairRow, ...]:
    """Derive every ordered Cartesian pair row including the diagonal."""
    logger.debug("replay_pair_rows entry stages=%d", len(stages))
    output: list[RelationPairRow] = []
    index = 0
    for left in stages:
        for right in stages:
            provisional = RelationPairRow(
                index, left.row.stage, right.row.stage,
                _pair_outcome(left.fine, right.fine, left.fine_bytes, right.fine_bytes),
                _pair_outcome(
                    left.coarse, right.coarse, left.coarse_bytes, right.coarse_bytes,
                ),
                left.row.fine_payload_digest, right.row.fine_payload_digest,
                left.row.coarse_payload_digest, right.row.coarse_payload_digest, "",
            )
            output.append(replace(provisional, row_digest=pair_row_digest(provisional)))
            index += 1
    result = tuple(output)
    logger.debug("replay_pair_rows exit pairs=%d", len(result))
    return result


def observation_bytes(value: Observation) -> bytes:
    """Canonicalize one exact typed response or obstruction payload."""
    logger.debug("relation observation_bytes entry type=%s", type(value).__name__)
    if type(value) is Ready:
        data: object = {"status": "ready", "response": response_data(value.value)}
    elif type(value) is Blocked:
        data = {
            "status": "blocked",
            "obstructions": [obstruction_data(item) for item in value.obstructions],
        }
    else:
        reject("malformed-relation-observation")
    result = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    logger.debug("relation observation_bytes exit bytes=%d", len(result))
    return result


def _run_status(value: Observation) -> RelationRunStatus:
    """Map one exact observation variant to its closed stage status."""
    logger.debug("relation run_status entry type=%s", type(value).__name__)
    if type(value) is Ready:
        result = RelationRunStatus.READY
    elif type(value) is Blocked:
        result = RelationRunStatus.BLOCKED
    else:
        reject("malformed-relation-observation")
    logger.debug("relation run_status exit status=%s", result.value)
    return result


def _pair_outcome(
    left: Observation, right: Observation, left_bytes: bytes, right_bytes: bytes,
) -> PairOutcome:
    """Derive exact response equality; blockage never becomes mismatch or echo."""
    logger.debug("relation pair_outcome entry")
    if type(left) is Blocked or type(right) is Blocked:
        result = PairOutcome.BLOCKED
    elif type(left) is Ready and type(right) is Ready:
        result = PairOutcome.ECHO if left_bytes == right_bytes else PairOutcome.MISMATCH
    else:
        reject("malformed-relation-observation")
    logger.debug("relation pair_outcome exit outcome=%s", result.value)
    return result
