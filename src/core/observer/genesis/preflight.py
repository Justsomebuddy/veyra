"""Bounded preflight for observer-genesis judgments."""

from __future__ import annotations

import logging

from .digest import encoded_request_bytes, refusal_digest, request_digest
from .types import (
    GenesisOperation, GenesisResourceBound, GenesisResourceLimit,
    OEPAdmissionRecord, ObserverGenesisDoctrine, ObserverGenesisSource,
    RecurrenceEvidence, RecurrenceWitness, WitnessScope,
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

def _resource(
    source: ObserverGenesisSource, witness: WitnessScope,
    recurrence: RecurrenceEvidence, oep: OEPAdmissionRecord, run: str,
    bound: GenesisResourceBound, required: int, allowed: int,
) -> GenesisResourceLimit:
    logger.debug("_resource entry bound=%s", bound.value)
    result = GenesisResourceLimit(
        GenesisOperation.JUDGMENT, bound, required, allowed,
        source.doctrine_digest, source.source_digest, source.adapter_digest,
        witness.witness_digest, recurrence.recurrence_digest, oep.oep_digest,
        run, refusal_digest(run, bound.value, required, allowed),
    )
    logger.debug("_resource exit")
    return result

def preflight_genesis(
    doctrine: ObserverGenesisDoctrine, source: ObserverGenesisSource,
    witness: WitnessScope, recurrence: RecurrenceEvidence,
    oep: OEPAdmissionRecord,
) -> tuple[str, GenesisResourceLimit | None]:
    """Charge every bound before `_step`, BFS, trace, or premise construction."""
    logger.debug("preflight_genesis entry")
    run = request_digest(
        source.source_digest, witness.witness_digest,
        recurrence.recurrence_digest, oep.oep_digest,
    )
    policy = doctrine.policy
    return_steps = (
        len(recurrence.left_return_word) + len(recurrence.right_return_word)
        if type(recurrence) is RecurrenceWitness else 0
    )
    charges = (
        (GenesisResourceBound.TRANSITION_ROWS, len(source.machine.rows), policy.max_transition_rows),
        (
            GenesisResourceBound.REACHABILITY_CHECKS,
            len(source.machine.control_states) * len(source.machine.residues)
            * len(source.machine.couplings),
            policy.max_reachability_checks,
        ),
        (
            GenesisResourceBound.CONTINUATION_STEPS,
            2 * witness.persistence_horizon, policy.max_continuation_steps,
        ),
        (
            GenesisResourceBound.RETURN_WORD_STEPS,
            return_steps,
            policy.max_return_word_steps,
        ),
        (
            GenesisResourceBound.RESPONSE_CHECKS,
            2 + 2 * witness.persistence_horizon, policy.max_response_checks,
        ),
        (
            GenesisResourceBound.ENCODED_BYTES,
            encoded_request_bytes(source, witness, recurrence, oep),
            policy.max_encoded_bytes,
        ),
    )
    for bound, required, allowed in charges:
        if required > allowed:
            result = _resource(
                source, witness, recurrence, oep, run,
                bound, required, allowed,
            )
            logger.debug("preflight_genesis exit refused=%s", bound.value)
            return run, result
    logger.debug("preflight_genesis exit allowed")
    return run, None
