"""Doctrine-relative P1-E1 judgment runtime."""

from __future__ import annotations

import logging

from .digest import judgment_digest
from .evidence import derive_premises
from .envelope import snapshot_source_envelope
from .preflight import preflight_genesis
from .request import (
    snapshot_oep_record, snapshot_recurrence, snapshot_witness,
)
from .types import (
    GenesisJudgment, GenesisOperationStatus, GenesisResult,
    OEPAdmission, OEPAdmissionRecord, ObserverGenesisDoctrine,
    ObserverGenesisSource, ObserverRole, PremiseStatus,
    RecurrenceEvidence, WitnessScope,
)
from .validation import snapshot_doctrine, snapshot_source

logger = logging.getLogger(__name__)


def observer_genesis_judgment(
    doctrine: ObserverGenesisDoctrine, source: ObserverGenesisSource,
    witness: WitnessScope, recurrence: RecurrenceEvidence,
    oep: OEPAdmissionRecord,
) -> GenesisResult:
    """Replay raw source and derive one finite OEP-relative role judgment."""
    logger.debug("observer_genesis_judgment entry")
    doctrine = snapshot_doctrine(doctrine)
    envelope = snapshot_source_envelope(doctrine, source)
    witness = snapshot_witness(envelope, witness)
    recurrence = snapshot_recurrence(envelope, witness, recurrence)
    oep = snapshot_oep_record(doctrine, oep)
    run, refusal = preflight_genesis(doctrine, envelope, witness, recurrence, oep)
    if refusal is not None:
        logger.debug("observer_genesis_judgment exit resource-limit")
        return refusal
    source = snapshot_source(doctrine, envelope)
    witness = snapshot_witness(source, witness)
    recurrence = snapshot_recurrence(source, witness, recurrence)
    premises = derive_premises(source.machine, witness, recurrence)
    statuses = tuple(item.status for item in premises)
    role = (
        ObserverRole.ESTABLISHED
        if oep.admission is OEPAdmission.ADMITTED
        and all(item is PremiseStatus.ESTABLISHED for item in statuses)
        else ObserverRole.OPEN
    )
    result = GenesisJudgment(
        doctrine.doctrine_digest, source.source_digest, source.adapter_digest,
        witness.witness_digest, recurrence.recurrence_digest, oep.oep_digest,
        run, judgment_digest(
            run, tuple(item.evidence_digest for item in premises), role.value,
        ),
        GenesisOperationStatus.JUDGED, premises,
        statuses[0], statuses[1], statuses[2], statuses[3], statuses[4],
        statuses[5], role,
    )
    logger.debug("observer_genesis_judgment exit role=%s", role.value)
    return result
