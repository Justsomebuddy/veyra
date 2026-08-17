"""Focused laws for the non-promoting P3-OG formation-pressure bridge."""

from __future__ import annotations

from dataclasses import fields
import logging

import pytest

import src.core.prime_power_observer_genesis_p3og_formation_pressure as bridge_facade
from src.core.prime_power_observer_genesis_p3og import (
    PressureStatus,
    TransitionKind,
    deterministic_select,
    p3og_source,
    run_p3og_pressure,
)
from src.core.prime_power_observer_genesis_p3og_codec import digest as pressure_digest
from src.core.prime_power_observer_genesis_p3og_formation_pressure import (
    P3OGFormationPressureBinding,
    P3OG_FORMATION_PRESSURE_NONCLAIMS,
    build_p3og_formation_pressure_binding,
    validate_p3og_formation_pressure_binding,
)
from src.core.prime_power_observer_genesis_p3og_formation_pressure_codec import (
    formation_pressure_digest,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    FirstClosureStatus,
    p3og_formation_source,
    run_p3og_first_closure,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle_codec import (
    lifecycle_digest,
)

logger = logging.getLogger(__name__)
SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


def _source(
    *,
    word: tuple[int, ...] = (0, 1, 0),
    calibration: tuple[int, int] = (0, 1),
    source_instance: str = "formation-pressure-source",
    seed_rows: tuple[tuple[str, tuple[int, ...]], ...] | None = None,
):
    """Build one exact bridge fixture source without outcome fields."""
    logger.debug(
        "test_p3og_binding source entry seeds=%d",
        1 if seed_rows is None else len(seed_rows),
    )
    rows = (("alpha", word),) if seed_rows is None else seed_rows
    result = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=source_instance,
        seed_rows=rows,
        calibration_inputs=calibration,
        maintenance_credit=2,
        suffix=SUFFIX,
    )
    logger.debug("test_p3og_binding source exit")
    return result


def _artifacts(
    *,
    word: tuple[int, ...] = (0, 1, 0),
    calibration: tuple[int, int] = (0, 1),
    source_instance: str = "formation-pressure-source",
    seed_rows: tuple[tuple[str, tuple[int, ...]], ...] | None = None,
):
    """Build all four replay premises and their exact bridge."""
    logger.debug("test_p3og_binding artifacts entry")
    source = _source(
        word=word,
        calibration=calibration,
        source_instance=source_instance,
        seed_rows=seed_rows,
    )
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    report = run_p3og_pressure(source)
    binding = build_p3og_formation_pressure_binding(source, formation, evidence, report)
    logger.debug(
        "test_p3og_binding artifacts exit closure=%s pressure=%s",
        evidence.status.value,
        binding.selected_candidate_status.value,
    )
    return source, formation, evidence, report, binding


def test_witnessed_formation_binds_exact_selected_pressure_execution() -> None:
    """The positive bridge contains only identities replayed from its premises."""
    logger.debug("test_p3og_binding positive entry")
    source, formation, evidence, report, binding = _artifacts()
    selected = report.candidates[report.selection.selected_index]
    assert evidence.status is FirstClosureStatus.WITNESSED
    assert binding.version == "p3og-formation-pressure-binding-v1"
    assert binding.pressure_source_digest == source.source_digest
    assert binding.formation_source_digest == formation.source_digest
    assert binding.formation_evidence_digest == evidence.evidence_digest
    assert binding.pressure_report_digest == report.report_digest
    assert binding.selection_receipt_digest == report.selection.receipt_digest
    assert binding.selected_seed_digest == formation.selected_seed_digest
    assert binding.pressure_entry_state_digest == evidence.pressure_entry_state_digest
    assert binding.selected_candidate_result_digest == selected.result_digest
    assert binding.selected_candidate_status is selected.status is PressureStatus.PASSED
    assert selected.maintenance_control is not None
    assert selected.active_left is not None
    assert selected.active_right is not None
    assert {
        selected.maintenance_control.enabled_state_digest,
        selected.active_left.coupling.before_digest,
        selected.active_right.coupling.before_digest,
    } == {binding.pressure_entry_state_digest}
    logger.debug("test_p3og_binding positive exit")


def test_validation_freshly_reconstructs_the_complete_binding() -> None:
    """Validation returns a detached exact replay, not caller authority."""
    logger.debug("test_p3og_binding fresh validation entry")
    source, formation, evidence, report, binding = _artifacts()
    replay = validate_p3og_formation_pressure_binding(
        source,
        formation,
        evidence,
        report,
        binding,
    )
    assert replay == binding
    assert replay is not binding
    assert replay.nonclaims == P3OG_FORMATION_PRESSURE_NONCLAIMS
    logger.debug("test_p3og_binding fresh validation exit")


def test_genuine_selected_pressure_refutation_is_preserved_not_blocked() -> None:
    """Binding exact execution is independent of whether its pressure passed."""
    logger.debug("test_p3og_binding genuine refutation entry")
    source, formation, evidence, report, binding = _artifacts(calibration=(0, 9))
    selected = report.candidates[report.selection.selected_index]
    assert evidence.status is FirstClosureStatus.WITNESSED
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "calibration-not-discriminated"
    assert selected.status is PressureStatus.REFUTED
    assert selected.reason == "calibration-not-discriminated"
    assert binding.selected_candidate_status is PressureStatus.REFUTED
    assert binding.selected_candidate_result_digest == selected.result_digest
    assert (
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            binding,
        )
        == binding
    )
    logger.debug("test_p3og_binding genuine refutation exit")


def test_multiseed_binding_uses_the_deterministic_selected_index() -> None:
    """The bridge binds the selected result rather than the first result row."""
    logger.debug("test_p3og_binding multiseed entry")
    seed_rows = tuple((f"seed-{index}", (index, index + 1, index)) for index in range(1, 9))
    source, formation, _evidence, report, binding = _artifacts(
        source_instance="formation-pressure-multiseed",
        seed_rows=seed_rows,
    )
    selection = deterministic_select(source)
    assert selection == formation.selection == report.selection
    assert selection.selected_index != 0
    selected = report.candidates[selection.selected_index]
    assert binding.selected_seed_digest == source.seeds[selection.selected_index].seed_digest
    assert binding.selected_candidate_result_digest == selected.result_digest
    assert binding.selected_candidate_result_digest != report.candidates[0].result_digest
    logger.debug("test_p3og_binding multiseed exit index=%d", selection.selected_index)


def test_binding_is_authority_free_and_not_root_exported() -> None:
    """The facade exposes only the bridge and grants no role/token capability."""
    logger.debug("test_p3og_binding facade boundary entry")
    *_premises, binding = _artifacts()
    assert bridge_facade.__all__ == (
        "P3OGFormationPressureBinding",
        "P3OG_FORMATION_PRESSURE_NONCLAIMS",
        "build_p3og_formation_pressure_binding",
        "validate_p3og_formation_pressure_binding",
    )
    assert all(hasattr(bridge_facade, name) for name in bridge_facade.__all__)
    names = {field.name for field in fields(P3OGFormationPressureBinding)}
    assert {
        "observer_role",
        "hap_witness",
        "birth_core_digest",
        "historical_token_id",
        "doctrine_admission",
        "truth_status",
    }.isdisjoint(names)
    assert binding.promotions == 0
    assert binding.nonclaims == P3OG_FORMATION_PRESSURE_NONCLAIMS
    assert {
        "endogenous-observer-role",
        "birth-core-or-historical-token",
        "typed-history-dag-or-chronology",
        "typed-hap-history-or-witness",
        "raw-cycle-operational-representation-invariance",
        "formal-theorem-or-certificate",
        "prime-power-carrier-or-completed-infinity",
        "promotion",
    }.issubset(binding.nonclaims)
    import src.core as root_core

    assert not hasattr(root_core, "build_p3og_formation_pressure_binding")
    assert not hasattr(root_core, "P3OGFormationPressureBinding")
    logger.debug("test_p3og_binding facade boundary exit")


def test_binding_digest_has_an_isolated_domain_and_exact_positive_pin() -> None:
    """Bridge identity cannot collide with pressure or lifecycle label domains."""
    logger.debug("test_p3og_binding digest domain entry")
    *_premises, binding = _artifacts()
    values = ("same", (0, 1, 0))
    assert formation_pressure_digest(*values) != pressure_digest(
        "formation-pressure-binding",
        *values,
    )
    assert formation_pressure_digest(*values) != lifecycle_digest(
        "formation-pressure-binding",
        *values,
    )
    assert binding.binding_digest == ("6802d057df56caccd303a6bd3fe9fbd5ddf48f28e22f3a99831df560df92a2f6")
    logger.debug("test_p3og_binding digest domain exit")


def test_raw_cycle_representation_refutation_cannot_be_relabelled_as_binding() -> None:
    """Operational similarity does not upgrade a REFUTED raw-word lifecycle."""
    logger.debug("test_p3og_binding representation boundary entry")
    _artifacts(word=(0, 1, 0), source_instance="representation-witnessed")
    source = _source(word=(0, 1, 2), source_instance="representation-refuted")
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    report = run_p3og_pressure(source)
    assert evidence.status is FirstClosureStatus.REFUTED
    assert evidence.pressure_entry_state_digest is None
    assert report.status is PressureStatus.REFUTED
    assert report.reason == "nonrecurrent-seed"
    with pytest.raises(ValueError, match="^p3og-formation-pressure-first-closure$"):
        build_p3og_formation_pressure_binding(source, formation, evidence, report)
    logger.debug("test_p3og_binding representation boundary exit")
