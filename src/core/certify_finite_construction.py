"""Executable provisional P1-B formal finite-construction certificate."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .construction.finite_builder.runtime import replay_finite_builder, snapshot_replay_artifact
from .construction.finite_builder.types import (
    FormalGenerability, OnticGenesis, PulseStep, ScopedObjectFormation,
    SeedRef, TargetIndependence,
)
from .finite_construction import (
    compose_finite_builder_expressions, construction_source_binding,
    finite_builder_program,
    finite_construction_judgment, finite_recurrence_seed,
)
from .positive_ontology import ontology_stage
from .positive_ontology_doctrine import p0_observer_doctrine
from .proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def certify_finite_construction_p1b() -> Certificate:
    """Certify source-relative replay without genesis or object promotion."""
    logger.debug("certify_finite_construction_p1b entry")
    doctrine = p0_observer_doctrine()
    seed = finite_recurrence_seed("silence-seed", Silence())
    program = finite_builder_program(
        "two-pulse-builder", "constructed-two", ("crest",),
        PulseStep(PulseStep(SeedRef("silence-seed"))),
    )
    source = construction_source_binding(
        doctrine, "p1b-fixed-source", program, (seed,)
    )
    first = replay_finite_builder(doctrine, source)
    second = replay_finite_builder(doctrine, source)
    revalidated = snapshot_replay_artifact(doctrine, source, first)
    outer = PulseStep(SeedRef("outer-port"))
    middle = PulseStep(PulseStep(SeedRef("middle-port")))
    inner = PulseStep(SeedRef("silence-seed"))
    associative_left_expr = compose_finite_builder_expressions(
        outer, compose_finite_builder_expressions(middle, inner)
    )
    associative_right_expr = compose_finite_builder_expressions(
        compose_finite_builder_expressions(outer, middle), inner
    )
    associative_left = finite_builder_program(
        "associative", "associative-stage", (), associative_left_expr
    )
    associative_right = finite_builder_program(
        "associative", "associative-stage", (), associative_right_expr
    )
    target = ontology_stage(
        "constructed-two", Pulse(Pulse(Silence())), doctrine, 1
    )
    mismatch_target = ontology_stage(
        "constructed-two", Pulse(Pulse(Pulse(Silence()))), doctrine, 1
    )
    positive = finite_construction_judgment(doctrine, source, target)
    mismatch = finite_construction_judgment(doctrine, source, mismatch_target)
    deterministic_fresh = (
        first.stage_commitment == second.stage_commitment
        and first.recurrence_commitment == second.recurrence_commitment
        and first.trace_digest == second.trace_digest
        and first.stage is not second.stage
        and first.stage.representative is not second.stage.representative
        and first.stage is not target
        and first.stage.representative is not target.representative
        and revalidated.stage is not first.stage
        and revalidated.stage_commitment == first.stage_commitment
    )
    nonclaims = all(
        row.ontic_genesis is OnticGenesis.NOT_ESTABLISHED
        and row.target_independence is TargetIndependence.NOT_ESTABLISHED
        and row.scoped_object is ScopedObjectFormation.OPEN
        for row in (positive, mismatch)
    )
    passed = (
        positive.formal_generability is FormalGenerability.GENERABLE
        and mismatch.formal_generability is FormalGenerability.TARGET_MISMATCH
        and mismatch.obstruction == "replayed-stage-does-not-match-target"
        and first.pulse_depth == 2
        and first.builder_nodes == 3
        and deterministic_fresh
        and associative_left.canonical == associative_right.canonical
        and associative_left.program_digest == associative_right.program_digest
        and compose_finite_builder_expressions(SeedRef("unit-port"), inner) == inner
        and compose_finite_builder_expressions(
            inner, SeedRef("silence-seed")
        ) == inner
        and nonclaims
        and source.scope
        == "immutability-membership-not-chronology-or-target-independence"
    )
    method = (
        "provisional P1-B closed SeedRef/PulseStep fresh finite replay; formal "
        "generability only, not ontic genesis, chronology, target independence, "
        "scoped-object formation, confluence, refinement, productivity, all-depth, "
        "infinity, or PΩ"
    )
    detail = (
        "two-pulse target generated; three-pulse mismatch; deterministic commitments "
        "with fresh identities and revalidation; builder composition unital/associative; "
        "genesis/independence not-established; object open"
    )
    result = Certificate("finite_construction_p1b", method, passed, detail, 1)
    logger.debug("certify_finite_construction_p1b exit result=%r", result)
    return result
