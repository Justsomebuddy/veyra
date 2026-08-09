"""Adversarial exact-type and noncircularity regressions for executable P0."""

from dataclasses import replace
import logging

import pytest

import src.core.positive_ontology as ontology
from src.core.observer_core_kernel import crest_observer, tail_observer
from src.core.observer_core_types import (
    Blocked,
    LeafKind,
    MarkValue,
    PairKind,
    PairValue,
    Ready,
)
from src.core.positive_ontology import (
    presentation_commitment,
    continuation_witness,
    observer_support_judgment,
    family_extension_judgment,
    internal_observer,
    ontology_presentation,
    ontology_stage,
    persistence_judgment,
    silence_modalities,
)
from src.core.positive_ontology_boundaries import (
    nonfinite_infinity_boundary,
    silence_boundary_judgment,
)
from src.core.positive_ontology_doctrine import observer_doctrine, p0_observer_doctrine
from src.core.positive_ontology_facets import ontology_facet_report
from src.core.positive_ontology_types import (
    PresentationCommitment,
    InfinityLevel,
    OntologyStage,
    SilenceModality,
)
from src.core.positive_ontology_validation import (
    PositiveOntologyValidationError,
    snapshot_recurrence,
)
from src.core.proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


class NameTrapMeta(type):
    """A hostile metaclass that forbids pre-gate class-name inspection."""

    def __getattribute__(cls, name):
        if name == "__name__":
            raise AssertionError("hostile metaclass name accessed")
        return super().__getattribute__(name)


class NameTrap(metaclass=NameTrapMeta):
    """Untrusted input for exact-gate logging attacks."""


def _tail_doctrine():
    logger.debug("_tail_doctrine entry")
    result = observer_doctrine(
        "tail-only-attack", "closed-r11-test", ("fixed-before-target",),
        (internal_observer("tail", tail_observer()),),
    )
    logger.debug("_tail_doctrine exit")
    return result


def test_untyped_callable_kind_tamper_and_hostile_metaclass_are_rejected():
    logger.debug("test_untyped_callable_kind_tamper_and_hostile_metaclass entry")
    doctrine = p0_observer_doctrine()
    with pytest.raises(Exception):
        internal_observer("callable", lambda value: value)
    with pytest.raises(PositiveOntologyValidationError):
        internal_observer("hostile", NameTrap())
    observer = doctrine.observers[0]
    forged = replace(observer, response_kind=LeafKind.RECURRENCE)
    bad_doctrine = replace(doctrine, observers=(forged, doctrine.observers[1]))
    with pytest.raises(PositiveOntologyValidationError):
        ontology_stage("s", Silence(), bad_doctrine, 1)
    tuple_child = PairKind(("close", 123), LeafKind.MARK)  # type: ignore[arg-type]
    tuple_kind = replace(observer, response_kind=tuple_child)
    with pytest.raises(PositiveOntologyValidationError, match="response-kind"):
        observer_doctrine(
            "tuple-kind", "closed-r11-test", ("malformed-kind",),
            (tuple_kind, doctrine.observers[1]),
        )
    with pytest.raises(PositiveOntologyValidationError):
        ontology_stage(NameTrap(), Silence(), doctrine, 0)  # type: ignore[arg-type]
    logger.debug("test_untyped_callable_kind_tamper_and_hostile_metaclass exit")


def test_diagram_boundary_rejects_hostile_metaclass_before_g4_logging():
    logger.debug("test_diagram_boundary_hostile_metaclass entry")
    from src.core.positive_ontology_boundaries import diagram_coherence_judgment
    with pytest.raises(PositiveOntologyValidationError, match="diagram-source"):
        diagram_coherence_judgment(NameTrap(), ())  # type: ignore[arg-type]
    logger.debug("test_diagram_boundary_hostile_metaclass exit")


def test_doctrine_stage_drift_fails_before_echo(monkeypatch):
    logger.debug("test_doctrine_stage_drift_fails_before_echo entry")
    doctrine = p0_observer_doctrine()
    lower = ontology_stage("s0", Pulse(Silence()), doctrine, 1)
    upper = ontology_stage("s1", Pulse(Silence()), doctrine, 2)
    reordered = replace(upper, observers=tuple(reversed(upper.observers)))
    witness = continuation_witness("w", "p", "s0", "s1", ("crest",))
    calls = 0

    def forbidden_echo(*args):
        nonlocal calls
        calls += 1
        raise AssertionError("echo ran before doctrine validation")

    monkeypatch.setattr(ontology, "echo", forbidden_echo)
    with pytest.raises(PositiveOntologyValidationError, match="doctrine-prefix"):
        ontology_presentation(doctrine, "bad", (lower, reordered), (witness,))
    drifted = replace(upper, doctrine_id="other")
    with pytest.raises(PositiveOntologyValidationError, match="doctrine-drift"):
        ontology_presentation(doctrine, "bad-2", (lower, drifted), (witness,))
    assert calls == 0
    logger.debug("test_doctrine_stage_drift_fails_before_echo exit")


def test_constant_observer_collapse_is_rejected_at_doctrine_admission():
    logger.debug("test_constant_observer_collapse entry")
    first = internal_observer("first", crest_observer())
    second = replace(first, observer_id="second")
    with pytest.raises(PositiveOntologyValidationError, match="observer-program"):
        observer_doctrine(
            "collapsed", "closed-r11-test", ("fixed-before-target",),
            (first, second),
        )
    logger.debug("test_constant_observer_collapse exit")


def test_doctrine_fingerprint_and_fixed_p0_claim_boundary_are_enforced():
    logger.debug("test_doctrine_fingerprint_and_fixed_boundary entry")
    fixed = p0_observer_doctrine()
    with pytest.raises(PositiveOntologyValidationError, match="fingerprint"):
        ontology_stage("drift", Silence(), replace(fixed, fingerprint="0" * 64), 1)
    custom = _tail_doctrine()
    custom_stage = ontology_stage("custom", Silence(), custom, 1)
    with pytest.raises(PositiveOntologyValidationError, match="fixed-p0"):
        ontology_presentation(custom, "invalid-claim", (custom_stage,), ())
    logger.debug("test_doctrine_fingerprint_and_fixed_boundary exit")


def test_noncomposable_interleaved_path_is_rejected():
    logger.debug("test_noncomposable_interleaved_path_is_rejected entry")
    doctrine = p0_observer_doctrine()
    stages = tuple(
        ontology_stage(name, Pulse(Silence()), doctrine, 1)
        for name in ("a", "b", "c", "d")
    )
    witnesses = (
        continuation_witness("ab", "path", "a", "b", ("crest",)),
        continuation_witness("cd", "path", "c", "d", ("crest",)),
    )
    presentation = ontology_presentation(doctrine, "fork", stages, witnesses)
    with pytest.raises(PositiveOntologyValidationError, match="noncomposable"):
        persistence_judgment(presentation, "path")
    logger.debug("test_noncomposable_interleaved_path_is_rejected exit")


def test_selected_family_echo_does_not_become_full_persistence_facet():
    logger.debug("test_selected_family_echo_does_not_become_full_persistence_facet entry")
    doctrine = p0_observer_doctrine()
    lower = ontology_stage("q0", Pulse(Silence()), doctrine, 1)
    upper = ontology_stage("q1", Pulse(Pulse(Silence())), doctrine, 2)
    witness = continuation_witness("qw", "qp", "q0", "q1", ("crest",))
    presentation = ontology_presentation(doctrine, "selected", (lower, upper), (witness,))
    assert persistence_judgment(presentation, "qp").status.value == "echo"
    assert family_extension_judgment(presentation, "qw").full_status.value == "split"
    facet = ontology_facet_report(
        lower, doctrine, persistence_presentation=presentation,
        persistence_path_id="qp",
    )
    assert facet.persistent.value == "open"
    logger.debug("test_selected_family_echo_does_not_become_full_persistence_facet exit")


def test_unrelated_path_cannot_establish_target_persistence():
    logger.debug("test_unrelated_path_cannot_establish_target_persistence entry")
    doctrine = p0_observer_doctrine()
    target = ontology_stage("target", Pulse(Silence()), doctrine, 2)
    alien_a = ontology_stage("alien-a", Pulse(Silence()), doctrine, 2)
    alien_b = ontology_stage("alien-b", Pulse(Silence()), doctrine, 2)
    witness = continuation_witness(
        "alien-w", "alien-path", "alien-a", "alien-b", ("crest", "tail")
    )
    presentation = ontology_presentation(
        doctrine, "alien-presentation", (target, alien_a, alien_b), (witness,)
    )
    with pytest.raises(PositiveOntologyValidationError, match="path-unbound"):
        ontology_facet_report(
            target, doctrine, persistence_presentation=presentation,
            persistence_path_id="alien-path",
        )
    logger.debug("test_unrelated_path_cannot_establish_target_persistence exit")


def test_presentation_commitment_never_establishes_constructibility():
    logger.debug("test_presentation_commitment_boundary entry")
    doctrine = p0_observer_doctrine()
    stage = ontology_stage("facet", Silence(), doctrine, 1)
    valid = presentation_commitment("builder", stage)
    forged = PresentationCommitment(valid.witness_id, "other-stage", valid.stage_commitment)
    with pytest.raises(PositiveOntologyValidationError, match="binding"):
        ontology_facet_report(stage, doctrine, presentation=forged)
    asserted = ontology_facet_report(stage, doctrine, presentation=valid)
    assert asserted.constructible.value == "open"
    assert asserted.scoped_object.value == "open"
    assert asserted.object_completion_boundary == "object-completion-rule-not-supplied"
    logger.debug("test_presentation_commitment_boundary exit")


def test_observation_snapshots_reject_empty_invalid_cyclic_and_overflow_values():
    logger.debug("test_observation_snapshots_reject_attacks entry")
    with pytest.raises(PositiveOntologyValidationError, match="blocked"):
        silence_modalities(Silence(), Blocked(()))
    with pytest.raises(PositiveOntologyValidationError, match="mark"):
        silence_modalities(Silence(), Ready(MarkValue("silent")))  # type: ignore[arg-type]
    cycle = PairValue(MarkValue.__new__(MarkValue), MarkValue.__new__(MarkValue))
    object.__setattr__(cycle, "left", cycle)
    object.__setattr__(cycle, "right", cycle)
    with pytest.raises(PositiveOntologyValidationError, match="circular"):
        silence_modalities(Silence(), Ready(cycle))
    value = MarkValue.__new__(MarkValue)
    object.__setattr__(value, "mark", object())
    for _ in range(130):
        value = PairValue(value, value)
    with pytest.raises(PositiveOntologyValidationError, match="resource"):
        silence_modalities(Silence(), Ready(value))
    logger.debug("test_observation_snapshots_reject_attacks exit")


def test_recurrence_cycle_is_rejected_during_single_snapshot_pass():
    logger.debug("test_recurrence_cycle_is_rejected entry")
    cycle = Pulse(Silence())
    object.__setattr__(cycle, "tail", cycle)
    with pytest.raises(PositiveOntologyValidationError, match="circular"):
        snapshot_recurrence(cycle)
    logger.debug("test_recurrence_cycle_is_rejected exit")


def test_blocked_run_remains_open_and_never_upgrades_to_absence():
    logger.debug("test_blocked_run_remains_open entry")
    doctrine = _tail_doctrine()
    row = observer_support_judgment(ontology_stage("blocked", Silence(), doctrine, 1))
    external = {
        SilenceModality.OPERATIONAL_ABSENCE,
        SilenceModality.OBSERVER_BLINDNESS,
        SilenceModality.EPISTEMIC_OPEN,
        SilenceModality.RESOURCE_LIMITED,
        SilenceModality.DIVERGENT,
        SilenceModality.INCONSISTENT,
        SilenceModality.UNRESOLVED_IN_SYSTEM,
    }
    assert row.support.value == "open" and not (set(row.silence) & external)
    with pytest.raises(PositiveOntologyValidationError, match="explicit-boundary"):
        silence_boundary_judgment(SilenceModality.DOMAIN_UNDEFINED, "blocked-run")
    logger.debug("test_blocked_run_remains_open exit")


def test_malformed_exact_instances_bool_levels_and_huge_ids_fail_closed():
    logger.debug("test_malformed_exact_instances entry")
    doctrine = p0_observer_doctrine()
    with pytest.raises(PositiveOntologyValidationError):
        observer_support_judgment(OntologyStage.__new__(OntologyStage))
    with pytest.raises(PositiveOntologyValidationError):
        ontology_stage("x" * 129, Silence(), doctrine, 0)
    with pytest.raises(PositiveOntologyValidationError):
        ontology_stage("bool", Silence(), doctrine, True)  # type: ignore[arg-type]
    with pytest.raises(PositiveOntologyValidationError):
        nonfinite_infinity_boundary(True)  # type: ignore[arg-type]
    with pytest.raises(PositiveOntologyValidationError):
        nonfinite_infinity_boundary(InfinityLevel.BOUNDED_WINDOW)
    logger.debug("test_malformed_exact_instances exit")
