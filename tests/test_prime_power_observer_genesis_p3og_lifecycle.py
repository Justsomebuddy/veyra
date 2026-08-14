"""Focused laws for authority-free bounded P3-OG formation replay."""

from __future__ import annotations

from dataclasses import fields
import logging

import pytest

import src.core.prime_power_observer_genesis_p3og as pressure_facade
import src.core.prime_power_observer_genesis_p3og_lifecycle as lifecycle_facade
from src.core.prime_power_observer_genesis_p3og import (
    P3OG_NONCLAIMS,
    TransitionKind,
    deterministic_select,
    p3og_source,
    run_p3og_pressure,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    FirstClosureStatus,
    FormationBoundary,
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
    P3OG_LIFECYCLE_NONCLAIMS,
    p3og_formation_source,
    run_p3og_first_closure,
    validate_first_closure_evidence,
    validate_formation_source,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle_codec import (
    lifecycle_digest,
)
from src.core.prime_power_observer_genesis_p3og_machine import initial_state

logger = logging.getLogger(__name__)
GOOD_SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


def _source(word: tuple[int, ...] = (0, 1, 0), label: str = "alpha"):
    """Build one bounded source whose only cycle is the formation word."""
    logger.debug("test_p3og_lifecycle.source entry word_length=%d", len(word))
    result = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="lifecycle-source",
        seed_rows=((label, word),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=GOOD_SUFFIX,
    )
    logger.debug(
        "test_p3og_lifecycle.source exit source=%s",
        result.source_digest[:12],
    )
    return result


def _run(word: tuple[int, ...] = (0, 1, 0)):
    """Build and replay one exact lifecycle source."""
    logger.debug("test_p3og_lifecycle.run entry word_length=%d", len(word))
    source = _source(word)
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    logger.debug("test_p3og_lifecycle.run exit status=%s", evidence.status.value)
    return source, formation, evidence


def test_seed_is_unformed_and_nonempty_native_replay_reaches_alive():
    logger.debug("test_p3og_lifecycle native replay entry")
    _, _, evidence = _run()
    assert evidence.initial_state.boundary is FormationBoundary.UNFORMED
    assert evidence.initial_state.cursor == 0
    assert evidence.initial_state.tick_count == 0
    assert evidence.ticks
    assert evidence.final_state.boundary is FormationBoundary.ALIVE
    assert evidence.first_closure_index == 2
    assert evidence.status is FirstClosureStatus.WITNESSED
    assert all(not row.became_alive for row in evidence.ticks[:-1])
    assert evidence.ticks[-1].became_alive is True
    logger.debug("test_p3og_lifecycle native replay exit")


def test_witness_binds_existing_operational_alive_pressure_entry_digest():
    logger.debug("test_p3og_lifecycle pressure entry binding entry")
    source, formation, evidence = _run()
    selected = source.seeds[formation.selection.selected_index]
    pressure_entry = initial_state(source, selected)
    assert evidence.status is FirstClosureStatus.WITNESSED
    assert evidence.pressure_entry_state_digest == pressure_entry.state_digest
    assert pressure_entry.boundary.value == "alive"
    logger.debug("test_p3og_lifecycle pressure entry binding exit")


def test_first_return_is_least_even_when_later_return_exists():
    logger.debug("test_p3og_lifecycle least return entry")
    _, formation, evidence = _run((0, 1, 0, 2, 0))
    assert formation.formation_word == (0, 1, 0, 2, 0)
    assert evidence.first_closure_index == 2
    assert len(evidence.ticks) == 2
    assert evidence.final_state.current_symbol == 0
    logger.debug("test_p3og_lifecycle least return exit")


@pytest.mark.parametrize("word", [(0, 0), (0, 1)])
def test_constant_or_nonreturning_word_is_scoped_refutation(word):
    logger.debug("test_p3og_lifecycle scoped refutation entry word=%r", word)
    _, _, evidence = _run(word)
    assert evidence.status is FirstClosureStatus.REFUTED
    assert evidence.reason == "formation-word-exhausted-without-closure"
    assert evidence.first_closure_index is None
    assert evidence.pressure_entry_state_digest is None
    assert evidence.final_state.boundary is FormationBoundary.UNFORMED
    assert len(evidence.ticks) == len(word) - 1
    logger.debug("test_p3og_lifecycle scoped refutation exit")


def test_source_binds_full_pressure_source_selection_seed_and_word():
    logger.debug("test_p3og_lifecycle source binding entry")
    source = _source((4, 7, 4))
    formation = p3og_formation_source(source)
    assert formation.pressure_source_digest == source.source_digest
    assert formation.selection.source_digest == source.source_digest
    assert formation.selected_seed_digest == source.seeds[0].seed_digest
    assert formation.formation_word == source.seeds[0].cycle
    assert formation.closure_rule_id == "least-nontrivial-return-v1"
    rebuilt_source, rebuilt = validate_formation_source(source, formation)
    assert rebuilt_source == source
    assert rebuilt == formation
    assert rebuilt is not formation
    logger.debug("test_p3og_lifecycle source binding exit")


def test_multiseed_lifecycle_replays_existing_deterministic_selection_only():
    logger.debug("test_p3og_lifecycle multiseed selection entry")
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="lifecycle-multiseed",
        seed_rows=(
            ("alpha", (10, 11, 10)),
            ("beta", (20, 21, 20)),
            ("gamma", (30, 31, 30)),
        ),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=GOOD_SUFFIX,
    )
    existing_selection = deterministic_select(source)
    selected = source.seeds[existing_selection.selected_index]
    unselected_words = {
        seed.cycle for index, seed in enumerate(source.seeds) if index != existing_selection.selected_index
    }
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    assert formation.selection == existing_selection
    assert formation.selected_seed_digest == selected.seed_digest
    assert formation.formation_word == selected.cycle
    assert formation.formation_word not in unselected_words
    assert tuple(tick.observed_symbol for tick in evidence.ticks) == selected.cycle[1:]
    assert evidence.first_closure_index == 2
    logger.debug("test_p3og_lifecycle multiseed selection exit")


def test_tick_receipts_form_exact_initial_to_final_adjacency_chain():
    logger.debug("test_p3og_lifecycle receipt adjacency entry")
    _, formation, evidence = _run((0, 1, 2, 0))
    assert evidence.ticks[0].before_state_digest == evidence.initial_state.state_digest
    assert all(
        previous.after_state_digest == following.before_state_digest
        for previous, following in zip(evidence.ticks[:-1], evidence.ticks[1:], strict=True)
    )
    assert evidence.ticks[-1].after_state_digest == evidence.final_state.state_digest
    assert tuple(tick.tick_index for tick in evidence.ticks) == tuple(range(1, len(evidence.ticks) + 1))
    assert (
        tuple(tick.observed_symbol for tick in evidence.ticks)
        == (formation.formation_word[1 : evidence.final_state.cursor + 1])
    )
    logger.debug("test_p3og_lifecycle receipt adjacency exit")


def test_lifecycle_digest_domain_is_separate_from_pressure_evidence():
    logger.debug("test_p3og_lifecycle digest domain entry")
    values = ("same-source", (0, 1, 0))
    assert lifecycle_digest("formation-source", *values) != pressure_digest(
        "formation-source",
        *values,
    )
    logger.debug("test_p3og_lifecycle digest domain exit")


def test_validation_freshly_reconstructs_evidence():
    logger.debug("test_p3og_lifecycle fresh validation entry")
    source, formation, evidence = _run()
    replay = validate_first_closure_evidence(source, formation, evidence)
    assert replay == evidence
    assert replay is not evidence
    assert replay.initial_state is not evidence.initial_state
    assert replay.ticks is not evidence.ticks
    logger.debug("test_p3og_lifecycle fresh validation exit")


def test_evidence_is_authority_free_and_keeps_exact_lifecycle_nonclaims():
    logger.debug("test_p3og_lifecycle nonclaims entry")
    _, _, evidence = _run()
    names = {field.name for field in fields(P3OGFirstClosureEvidence)}
    forbidden = {
        "token_id",
        "historical_token_id",
        "birth_core_digest",
        "doctrine_admission",
        "observer_role",
        "hap_witness",
    }
    assert forbidden.isdisjoint(names)
    assert evidence.promotions == 0
    assert evidence.nonclaims == P3OG_LIFECYCLE_NONCLAIMS
    assert {
        "criterion-blind-historical-selection",
        "typed-history-dag-or-full-def-og-003",
        "endogenous-observer-role",
        "birth-core-or-historical-token",
        "n0-or-hap-lift",
        "formal-theorem-or-certificate",
    }.issubset(evidence.nonclaims)
    logger.debug("test_p3og_lifecycle nonclaims exit")


def test_lifecycle_source_contains_no_result_target_or_authority_fields():
    logger.debug("test_p3og_lifecycle source fields entry")
    names = {field.name for field in fields(P3OGFormationSource)}
    assert {
        "status",
        "reason",
        "target",
        "expected_closure_index",
        "result_digest",
        "token_id",
        "observer_role",
    }.isdisjoint(names)
    logger.debug("test_p3og_lifecycle source fields exit")


def test_lifecycle_facade_is_explicit_and_root_package_does_not_promote_it():
    logger.debug("test_p3og_lifecycle facade entry")
    assert set(lifecycle_facade.__all__) == {
        "FirstClosureStatus",
        "FormationBoundary",
        "FormationState",
        "FormationTickReceipt",
        "P3OGFirstClosureEvidence",
        "P3OGFormationSource",
        "P3OG_LIFECYCLE_NONCLAIMS",
        "p3og_formation_source",
        "run_p3og_first_closure",
        "validate_first_closure_evidence",
        "validate_formation_source",
    }
    assert all(hasattr(lifecycle_facade, name) for name in lifecycle_facade.__all__)
    import src.core as root_core

    assert not hasattr(root_core, "run_p3og_first_closure")
    logger.debug("test_p3og_lifecycle facade exit")


def test_existing_pressure_facade_nonclaims_and_digest_remain_exact():
    logger.debug("test_p3og_lifecycle pressure compatibility entry")
    assert set(pressure_facade.__all__) == {
        "CandidatePressureResult",
        "DeterministicSelectionReceipt",
        "P3OG_NONCLAIMS",
        "P3OGPressureReport",
        "P3OGSource",
        "PressureStatus",
        "PrimitiveModeSeed",
        "TransitionKind",
        "deterministic_select",
        "p3og_source",
        "run_p3og_pressure",
        "validate_pressure_report",
        "validate_source",
    }
    source = p3og_source(
        prime=3,
        depth=1,
        source_instance_label="source-1",
        seed_rows=(("alpha", (0, 1, 0)), ("beta", (1, 0, 1))),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=GOOD_SUFFIX,
    )
    report = run_p3og_pressure(source)
    assert source.source_digest == ("0238df62dd849ecd51df3e017720237491e191c10daf9b91ca4570b54fd76010")
    assert report.report_digest == ("6cb296c650deaf458649b0211546815490a46aa0ab8d7606362daea3fc38faf7")
    assert report.nonclaims == P3OG_NONCLAIMS
    logger.debug("test_p3og_lifecycle pressure compatibility exit")


def test_maximum_64_symbol_word_replays_in_one_bounded_pass():
    logger.debug("test_p3og_lifecycle maximum word entry")
    word = (*tuple(range(63)), 0)
    source, formation, evidence = _run(word)
    assert len(formation.formation_word) == 64
    assert len(evidence.ticks) == 63
    assert evidence.first_closure_index == 63
    assert evidence.status is FirstClosureStatus.WITNESSED
    assert validate_first_closure_evidence(source, formation, evidence) == evidence
    logger.debug("test_p3og_lifecycle maximum word exit")
