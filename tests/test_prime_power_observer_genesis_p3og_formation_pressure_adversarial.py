"""Adversarial boundaries for P3-OG formation-pressure binding replay."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.prime_power_observer_genesis_p3og_formation_pressure_runtime as runtime_module
from src.core.prime_power_observer_genesis_p3og import (
    PressureStatus,
    TransitionKind,
    p3og_source,
    run_p3og_pressure,
)
from src.core.prime_power_observer_genesis_p3og_formation_pressure import (
    P3OGFormationPressureBinding,
    build_p3og_formation_pressure_binding,
    validate_p3og_formation_pressure_binding,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    FirstClosureStatus,
    p3og_formation_source,
    run_p3og_first_closure,
)

logger = logging.getLogger(__name__)
SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


class BindingSubclass(P3OGFormationPressureBinding):
    """Foreign exact-looking binding type that must remain inadmissible."""


class ExplosiveEquality:
    """Fail if validation invokes attacker-controlled equality."""

    def __eq__(self, other: object) -> bool:
        logger.error("test_p3og_binding explosive equality invoked")
        raise AssertionError("attacker equality executed")


def _source(
    *,
    source_instance: str = "bridge-adversarial",
    word: tuple[int, ...] = (0, 1, 0),
    calibration: tuple[int, int] = (0, 1),
):
    """Build one exact single-selected-seed adversarial source."""
    logger.debug("test_p3og_binding_adversarial source entry")
    result = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=source_instance,
        seed_rows=(("alpha", word),),
        calibration_inputs=calibration,
        maintenance_credit=2,
        suffix=SUFFIX,
    )
    logger.debug("test_p3og_binding_adversarial source exit")
    return result


def _premises(
    *,
    source_instance: str = "bridge-adversarial",
    word: tuple[int, ...] = (0, 1, 0),
    calibration: tuple[int, int] = (0, 1),
):
    """Build exact source, formation, lifecycle evidence, and pressure report."""
    logger.debug("test_p3og_binding_adversarial premises entry")
    source = _source(
        source_instance=source_instance,
        word=word,
        calibration=calibration,
    )
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    report = run_p3og_pressure(source)
    logger.debug(
        "test_p3og_binding_adversarial premises exit closure=%s report=%s",
        evidence.status.value,
        report.status.value,
    )
    return source, formation, evidence, report


def _case():
    """Build an exact positive premise family and bridge."""
    logger.debug("test_p3og_binding_adversarial case entry")
    premises = _premises()
    binding = build_p3og_formation_pressure_binding(*premises)
    logger.debug("test_p3og_binding_adversarial case exit")
    return (*premises, binding)


def test_cross_source_and_extensionally_similar_report_splices_are_rejected() -> None:
    """Equal pool behavior cannot erase exact source-instance custody."""
    logger.debug("test_p3og_binding cross source entry")
    source, formation, evidence, report = _premises(source_instance="bridge-first")
    foreign_source, foreign_formation, foreign_evidence, foreign_report = _premises(
        source_instance="bridge-second",
    )
    assert source.seeds == foreign_source.seeds
    assert report.status == foreign_report.status
    assert formation.selection.selected_index == foreign_formation.selection.selected_index
    with pytest.raises(ValueError, match="p3og-formation-source-drift"):
        build_p3og_formation_pressure_binding(
            foreign_source,
            formation,
            evidence,
            foreign_report,
        )
    with pytest.raises(ValueError, match="p3og-report-drift"):
        build_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            foreign_report,
        )
    with pytest.raises(ValueError):
        build_p3og_formation_pressure_binding(
            source,
            foreign_formation,
            foreign_evidence,
            report,
        )
    logger.debug("test_p3og_binding cross source exit")


@pytest.mark.parametrize(
    "target",
    (
        "selection",
        "selected-seed",
        "entry",
        "tick",
        "tick-order",
        "genealogy",
        "evidence",
    ),
)
def test_formation_and_evidence_splices_fail_before_binding(target: str) -> None:
    """Every lifecycle premise remains subject to its original fresh replay."""
    logger.debug("test_p3og_binding lifecycle splice entry target=%s", target)
    source, formation, evidence, report = _premises()
    if target == "selection":
        formation = replace(
            formation,
            selection=replace(formation.selection, receipt_digest="0" * 64),
        )
    elif target == "selected-seed":
        formation = replace(formation, selected_seed_digest="0" * 64)
    elif target == "entry":
        evidence = replace(evidence, pressure_entry_state_digest="0" * 64)
    elif target == "tick":
        evidence = replace(
            evidence,
            ticks=(
                replace(evidence.ticks[0], receipt_digest="0" * 64),
                *evidence.ticks[1:],
            ),
        )
    elif target == "tick-order":
        evidence = replace(evidence, ticks=tuple(reversed(evidence.ticks)))
    elif target == "genealogy":
        evidence = replace(evidence, genealogy_digest="0" * 64)
    else:
        evidence = replace(evidence, evidence_digest="0" * 64)
    with pytest.raises(ValueError):
        build_p3og_formation_pressure_binding(source, formation, evidence, report)
    logger.debug("test_p3og_binding lifecycle splice exit target=%s", target)


@pytest.mark.parametrize(
    "target",
    (
        "selection",
        "selected-result",
        "candidate-result",
        "candidate-seed",
        "maintenance-entry",
        "active-left-entry",
        "active-right-entry",
        "report",
    ),
)
def test_report_and_nested_selected_result_splices_fail_fresh_replay(target: str) -> None:
    """The bridge never accepts a caller-spliced pressure execution."""
    logger.debug("test_p3og_binding report splice entry target=%s", target)
    source, formation, evidence, report = _premises()
    selected_index = report.selection.selected_index
    selected = report.candidates[selected_index]
    if target == "selection":
        report = replace(
            report,
            selection=replace(report.selection, receipt_digest="0" * 64),
        )
    elif target == "selected-result":
        report = replace(report, selected_candidate_result_digest="0" * 64)
    elif target == "report":
        report = replace(report, report_digest="0" * 64)
    else:
        if target == "candidate-result":
            forged = replace(selected, result_digest="0" * 64)
        elif target == "candidate-seed":
            forged = replace(selected, seed_digest="0" * 64)
        elif target == "maintenance-entry":
            assert selected.maintenance_control is not None
            forged = replace(
                selected,
                maintenance_control=replace(
                    selected.maintenance_control,
                    enabled_state_digest="0" * 64,
                ),
            )
        else:
            trace_name = "active_left" if target == "active-left-entry" else "active_right"
            trace = getattr(selected, trace_name)
            assert trace is not None
            forged = replace(
                selected,
                **{
                    trace_name: replace(
                        trace,
                        coupling=replace(trace.coupling, before_digest="0" * 64),
                    )
                },
            )
        candidates = list(report.candidates)
        candidates[selected_index] = forged
        report = replace(report, candidates=tuple(candidates))
    with pytest.raises(ValueError, match="p3og-report-"):
        build_p3og_formation_pressure_binding(source, formation, evidence, report)
    logger.debug("test_p3og_binding report splice exit target=%s", target)


@pytest.mark.parametrize(
    "field,value",
    (
        ("version", "foreign-version"),
        ("pressure_source_digest", "0" * 64),
        ("formation_source_digest", "0" * 64),
        ("formation_evidence_digest", "0" * 64),
        ("pressure_report_digest", "0" * 64),
        ("selection_receipt_digest", "0" * 64),
        ("selected_seed_digest", "0" * 64),
        ("pressure_entry_state_digest", "0" * 64),
        ("selected_candidate_result_digest", "0" * 64),
        ("selected_candidate_status", PressureStatus.REFUTED),
        ("promotions", 1),
        ("nonclaims", ()),
        ("binding_digest", "0" * 64),
    ),
)
def test_binding_field_splices_fail_exact_validation(field: str, value: object) -> None:
    """Every bridge field is replay-derived and digest-bound."""
    logger.debug("test_p3og_binding field splice entry field=%s", field)
    source, formation, evidence, report, binding = _case()
    forged = replace(binding, **{field: value})
    with pytest.raises(ValueError, match="p3og-formation-pressure-binding-"):
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            forged,
        )
    logger.debug("test_p3og_binding field splice exit field=%s", field)


def test_refuted_lifecycle_cannot_be_spliced_into_a_positive_bridge() -> None:
    """A raw word without a first return has no pressure-entry binding."""
    logger.debug("test_p3og_binding refuted lifecycle entry")
    source, formation, evidence, report = _premises(word=(0, 1, 2))
    assert evidence.status is FirstClosureStatus.REFUTED
    with pytest.raises(ValueError, match="^p3og-formation-pressure-first-closure$"):
        build_p3og_formation_pressure_binding(source, formation, evidence, report)
    logger.debug("test_p3og_binding refuted lifecycle exit")


def test_binding_outer_type_uninitialized_hostile_and_resource_shapes_fail_typed() -> None:
    """Validation rejects foreign callbacks and huge tuples before comparison."""
    logger.debug("test_p3og_binding hostile shapes entry")
    source, formation, evidence, report, binding = _case()
    subclass = BindingSubclass(
        **{field.name: getattr(binding, field.name) for field in binding.__dataclass_fields__.values()}
    )
    with pytest.raises(ValueError, match="p3og-formation-pressure-binding-type"):
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            subclass,
        )
    with pytest.raises(ValueError, match="p3og-formation-pressure-binding-malformed"):
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            object.__new__(P3OGFormationPressureBinding),
        )
    hostile = replace(binding, version=ExplosiveEquality())
    with pytest.raises(ValueError, match="p3og-formation-pressure-binding-malformed"):
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            hostile,
        )
    huge = replace(binding, nonclaims=binding.nonclaims * 100_000)
    with pytest.raises(ValueError, match="p3og-formation-pressure-binding-malformed"):
        validate_p3og_formation_pressure_binding(
            source,
            formation,
            evidence,
            report,
            huge,
        )
    logger.debug("test_p3og_binding hostile shapes exit")


@pytest.mark.parametrize(
    ("target", "reason"),
    (
        ("selection", "p3og-formation-pressure-selection"),
        ("selected-seed", "p3og-formation-pressure-selected-seed"),
        ("entry", "p3og-formation-pressure-entry"),
        ("selected-result", "p3og-formation-pressure-selected-result"),
        ("active-entry", "p3og-formation-pressure-active-entry"),
    ),
)
def test_internal_replayed_relation_invariants_fail_closed(target: str, reason: str) -> None:
    """Each bridge-only equality has a stable typed obstruction."""
    logger.debug("test_p3og_binding internal seam entry target=%s", target)
    source, formation, evidence, report = _premises()
    if target == "selection":
        report = replace(
            report,
            selection=replace(report.selection, receipt_digest="0" * 64),
        )
    elif target == "selected-seed":
        formation = replace(formation, selected_seed_digest="0" * 64)
    elif target == "entry":
        evidence = replace(evidence, pressure_entry_state_digest="0" * 64)
    else:
        index = report.selection.selected_index
        selected = report.candidates[index]
        if target == "selected-result":
            report = replace(report, selected_candidate_result_digest="0" * 64)
        else:
            assert selected.maintenance_control is not None
            forged = replace(
                selected,
                maintenance_control=replace(
                    selected.maintenance_control,
                    enabled_state_digest="0" * 64,
                ),
            )
            candidates = list(report.candidates)
            candidates[index] = forged
            report = replace(report, candidates=tuple(candidates))
    with pytest.raises(ValueError, match=f"^{reason}$"):
        runtime_module._build_binding_validated(
            source,
            formation,
            evidence,
            report,
        )
    logger.debug("test_p3og_binding internal seam exit target=%s", target)
