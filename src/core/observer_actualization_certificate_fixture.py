"""Private deterministic raw fixture for the P1-E4 direct certificate."""

from __future__ import annotations

from hashlib import sha256
import logging

from .construction.finite_builder.types import PulseStep, SeedRef
from .finite_construction import (
    construction_source_binding, finite_builder_program, finite_recurrence_seed,
)
from .observer_actualization import (
    AccessEdge, CounterfactualClass, EventKind, HistoricalObserverSource,
    actualization_counterfactual, actualization_resource_policy,
    historical_assumption, historical_observer_source, history_event,
)
from .observer_genesis import (
    ADAPTER_ID, derive_fixed_machine, genesis_resource_policy,
    observer_genesis_doctrine, observer_genesis_judgment,
    observer_genesis_source, oep_admission_record, origin_mode_spec,
    recurrence_witness, witness_scope,
)
from .observer_genesis_types import GenesisJudgment, MachineState, OEPAdmission
from .positive_ontology import ontology_stage
from .positive_ontology_doctrine import p0_observer_doctrine
from .proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def _d(label: str) -> str:
    logger.debug("actualization certificate digest entry")
    result = sha256(label.encode()).hexdigest()
    logger.debug("actualization certificate digest exit")
    return result


def certificate_source(
    target_label: str = "target-a", access_edges: tuple[AccessEdge, ...] = (),
) -> HistoricalObserverSource:
    """Build the exact six-event positive certificate source."""
    logger.debug("certificate_source p1e4 entry")
    p0 = p0_observer_doctrine()
    seed = finite_recurrence_seed("e4-cert-seed", Silence())
    program = finite_builder_program(
        "e4-cert-builder", "e4-cert-stage", ("crest",),
        PulseStep(SeedRef("e4-cert-seed")),
    )
    construction = construction_source_binding(
        p0, "e4-cert-construction", program, (seed,),
    )
    target = ontology_stage("e4-cert-stage", Pulse(Silence()), p0, 1)
    e1_doctrine = observer_genesis_doctrine(genesis_resource_policy())
    genealogy = origin_mode_spec()
    machine = derive_fixed_machine(genealogy)
    e1_source = observer_genesis_source(
        e1_doctrine, genealogy, ADAPTER_ID, machine,
    )
    witness = witness_scope(
        e1_source, MachineState("base", "zero"), "left", "right",
        ("tick",), 1, 1,
    )
    recurrence = recurrence_witness(
        e1_source, witness, ("left", "tick", "reset"),
        ("right", "tick", "reset"),
    )
    oep = oep_admission_record(e1_doctrine, OEPAdmission.ADMITTED)
    genesis = observer_genesis_judgment(
        e1_doctrine, e1_source, witness, recurrence, oep,
    )
    if type(genesis) is not GenesisJudgment:
        raise RuntimeError("certificate-genesis-fixture-refused")
    lineage = "certificate-lineage"
    events = (
        history_event(
            "construction", EventKind.CONSTRUCTION, (), 0,
            construction.membership_digest, lineage,
        ),
        history_event("oep", EventKind.OEP, ("construction",), 1, oep.oep_digest, lineage),
        history_event(
            "birth", EventKind.BIRTH, ("construction", "oep"), 2,
            e1_source.source_digest, lineage,
        ),
        history_event("target", EventKind.TARGET, ("birth",), 3, _d(target_label), lineage),
        history_event(
            "intervention", EventKind.INTERVENTION, ("birth",), 4,
            witness.witness_digest, lineage,
        ),
        history_event(
            "response", EventKind.RESPONSE, ("intervention", "target"), 5,
            genesis.premises[5].evidence_digest, lineage,
        ),
    )
    cases = (
        actualization_counterfactual(
            "cf-prefix", CounterfactualClass.PREFIX_TARGET_VARIATION,
            "target", "response", _d("target-b"), "unused", ("construction",),
        ),
        actualization_counterfactual(
            "cf-chooser", CounterfactualClass.TARGET_READING_CHOOSER,
            "target", "construction", _d("target-b"), "unused",
            ("construction",),
        ),
        actualization_counterfactual(
            "cf-copy", CounterfactualClass.FOREIGN_PARENT_COPY,
            "birth", "response", _d("target-b"), "foreign-lineage",
            ("construction",),
        ),
    )
    result = historical_observer_source(
        actualization_resource_policy(), "certificate-history", lineage,
        events, access_edges,
        (
            historical_assumption("a-construction", "construction", ()),
            historical_assumption("a-oep", "oep", ("a-construction",)),
        ),
        ("a-oep",), cases, "birth", "construction", "oep", "target",
        "intervention", "response", p0, construction, target, e1_doctrine,
        e1_source, witness, recurrence, oep,
    )
    if type(result) is not HistoricalObserverSource:
        raise RuntimeError("certificate-source-fixture-refused")
    logger.debug("certificate_source p1e4 exit")
    return result
