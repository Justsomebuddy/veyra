"""Shared exact positive fixture for isolated P1-E4 tests."""

from __future__ import annotations

from hashlib import sha256
import logging

from src.core.finite_builder_types import PulseStep, SeedRef
from src.core.finite_construction import (
    construction_source_binding, finite_builder_program, finite_recurrence_seed,
)
from src.core.observer_actualization import (
    AccessKind, CounterfactualClass, EventKind,
    access_edge, actualization_counterfactual, actualization_resource_policy,
    historical_assumption, historical_observer_source, history_event,
)
from src.core.observer_actualization_types import HistoricalObserverSource
from src.core.observer_genesis import (
    ADAPTER_ID, derive_fixed_machine, genesis_resource_policy,
    observer_genesis_doctrine, observer_genesis_judgment,
    observer_genesis_source, oep_admission_record, origin_mode_spec,
    recurrence_witness, witness_scope,
)
from src.core.observer_genesis_types import (
    GenesisJudgment, MachineState, OEPAdmission,
)
from src.core.positive_ontology import ontology_stage
from src.core.positive_ontology_doctrine import p0_observer_doctrine
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def d(label: str) -> str:
    logger.debug("e4 fixture digest entry label=%s", label)
    result = sha256(label.encode()).hexdigest()
    logger.debug("e4 fixture digest exit")
    return result


def fixture_inputs() -> dict[str, object]:
    logger.debug("fixture_inputs e4 entry")
    p0 = p0_observer_doctrine()
    seed = finite_recurrence_seed("e4-seed", Silence())
    program = finite_builder_program(
        "e4-builder", "e4-stage", ("crest",), PulseStep(SeedRef("e4-seed")),
    )
    construction = construction_source_binding(
        p0, "e4-construction", program, (seed,),
    )
    target = ontology_stage("e4-stage", Pulse(Silence()), p0, 1)
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
    assert type(genesis) is GenesisJudgment
    lineage = "observer-lineage"
    events = (
        history_event(
            "construction", EventKind.CONSTRUCTION, (), 0,
            construction.membership_digest, lineage,
        ),
        history_event(
            "oep", EventKind.OEP, ("construction",), 1, oep.oep_digest, lineage,
        ),
        history_event(
            "birth", EventKind.BIRTH, ("construction", "oep"), 2,
            e1_source.source_digest, lineage,
        ),
        history_event("target", EventKind.TARGET, ("birth",), 3, d("target-a"), lineage),
        history_event(
            "intervention", EventKind.INTERVENTION, ("birth",), 4,
            witness.witness_digest, lineage,
        ),
        history_event(
            "response", EventKind.RESPONSE, ("intervention", "target"), 5,
            genesis.premises[5].evidence_digest, lineage,
        ),
    )
    assumptions = (
        historical_assumption("a-construction", "construction", ()),
        historical_assumption("a-oep", "oep", ("a-construction",)),
    )
    counterfactuals = (
        actualization_counterfactual(
            "cf-prefix", CounterfactualClass.PREFIX_TARGET_VARIATION,
            "target", "response", d("target-b"), "unused-lineage",
            ("construction",),
        ),
        actualization_counterfactual(
            "cf-chooser", CounterfactualClass.TARGET_READING_CHOOSER,
            "target", "construction", d("target-b"), "unused-lineage",
            ("construction",),
        ),
        actualization_counterfactual(
            "cf-copy", CounterfactualClass.FOREIGN_PARENT_COPY,
            "birth", "response", d("target-b"), "foreign-lineage",
            ("construction",),
        ),
    )
    result: dict[str, object] = {
        "policy": actualization_resource_policy(), "history_id": "history-a",
        "lineage_id": lineage, "events": events, "access_edges": (),
        "assumptions": assumptions, "assumption_roots": ("a-oep",),
        "counterfactuals": counterfactuals, "birth_event_id": "birth",
        "construction_event_id": "construction", "oep_event_id": "oep",
        "target_event_id": "target", "intervention_event_id": "intervention",
        "response_event_id": "response", "p0_doctrine": p0,
        "construction_source": construction, "construction_target": target,
        "e1_doctrine": e1_doctrine, "e1_source": e1_source,
        "e1_witness": witness, "e1_recurrence": recurrence, "e1_oep": oep,
    }
    logger.debug("fixture_inputs e4 exit")
    return result


def build_source(**changes) -> HistoricalObserverSource:
    logger.debug("build_source fixture entry")
    values = fixture_inputs()
    values.update(changes)
    result = historical_observer_source(**values)  # type: ignore[arg-type]
    assert type(result) is HistoricalObserverSource
    logger.debug("build_source fixture exit")
    return result


def leak_edge() -> tuple:
    logger.debug("leak_edge fixture entry")
    result = (access_edge("target", "construction", AccessKind.TARGET_READ),)
    logger.debug("leak_edge fixture exit")
    return result
