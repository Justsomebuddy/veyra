"""Hostile boundary tests for bounded P3-OG lifecycle replay."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_lifecycle import (
    FirstClosureStatus,
    FormationBoundary,
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
    p3og_formation_source,
    run_p3og_first_closure,
    validate_first_closure_evidence,
    validate_formation_source,
)
from src.core.prime_power_observer_genesis_p3og_lifecycle_runtime import (
    _formation_state,
    _formation_tick_validated,
    _validate_formation_state,
)

logger = logging.getLogger(__name__)
SUFFIX = (
    TransitionKind.IDLE,
    TransitionKind.MAINTAIN,
    TransitionKind.IDLE,
    TransitionKind.ADVANCE,
)


class ExplosiveEquality:
    """Fail if a validator dispatches attacker-controlled equality."""

    def __eq__(self, other):
        logger.error("test_p3og_lifecycle explosive equality invoked")
        raise AssertionError("attacker equality executed")


def _source(label: str = "alpha", word: tuple[int, ...] = (0, 1, 0)):
    """Build one exact bounded adversarial fixture source."""
    logger.debug("test_p3og_lifecycle_adversarial.source entry label=%s", label)
    result = p3og_source(
        prime=3,
        depth=1,
        source_instance_label=f"lifecycle-{label}",
        seed_rows=((label, word),),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=SUFFIX,
    )
    logger.debug(
        "test_p3og_lifecycle_adversarial.source exit source=%s",
        result.source_digest[:12],
    )
    return result


def _evidence(word: tuple[int, ...] = (0, 1, 0)):
    """Return one source, formation source, and exact evidence triple."""
    logger.debug("test_p3og_lifecycle_adversarial.evidence entry")
    source = _source(word=word)
    formation = p3og_formation_source(source)
    evidence = run_p3og_first_closure(source, formation)
    logger.debug("test_p3og_lifecycle_adversarial.evidence exit")
    return source, formation, evidence


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", "foreign-version"),
        ("pressure_source_digest", "0" * 64),
        ("selected_seed_digest", "0" * 64),
        ("formation_word", (0, 2, 0)),
        ("closure_rule_id", "foreign-rule"),
        ("source_digest", "0" * 64),
    ],
)
def test_formation_source_splices_are_rejected(field, value):
    logger.debug("test_p3og_lifecycle source splice entry field=%s", field)
    source = _source()
    formation = p3og_formation_source(source)
    with pytest.raises(ValueError, match="p3og-formation-source-drift"):
        validate_formation_source(source, replace(formation, **{field: value}))
    logger.debug("test_p3og_lifecycle source splice exit field=%s", field)


def test_cross_source_formation_and_evidence_are_rejected():
    logger.debug("test_p3og_lifecycle cross source entry")
    source, formation, evidence = _evidence()
    foreign = _source(label="foreign", word=(4, 5, 4))
    with pytest.raises(ValueError, match="p3og-formation-source-drift"):
        validate_formation_source(foreign, formation)
    with pytest.raises(ValueError, match="p3og-formation-source-drift"):
        validate_first_closure_evidence(foreign, formation, evidence)
    assert source.source_digest != foreign.source_digest
    logger.debug("test_p3og_lifecycle cross source exit")


def test_hostile_source_selection_is_rejected_without_equality_dispatch():
    logger.debug("test_p3og_lifecycle hostile source entry")
    source = _source()
    formation = p3og_formation_source(source)
    forged = replace(formation, selection=ExplosiveEquality())
    with pytest.raises(ValueError, match="p3og-formation-source-malformed"):
        validate_formation_source(source, forged)
    logger.debug("test_p3og_lifecycle hostile source exit")


def test_exact_type_selection_splice_is_rejected():
    logger.debug("test_p3og_lifecycle selection splice entry")
    source = _source()
    formation = p3og_formation_source(source)
    forged = replace(
        formation,
        selection=replace(formation.selection, pool_digest="0" * 64),
    )
    with pytest.raises(ValueError, match="p3og-formation-source-drift"):
        validate_formation_source(source, forged)
    logger.debug("test_p3og_lifecycle selection splice exit")


@pytest.mark.parametrize(
    "target",
    [
        "formation-source",
        "initial-boundary",
        "initial-cursor",
        "tick-before",
        "tick-after",
        "tick-alive",
        "tick-index",
        "tick-symbol",
        "tick-digest",
        "tick-order",
        "final-state",
        "closure-index",
        "pressure-entry",
        "status",
        "reason",
        "genealogy",
        "promotions",
        "nonclaims",
        "evidence",
    ],
)
def test_nested_evidence_splices_fail_fresh_reconstruction(target):
    logger.debug("test_p3og_lifecycle evidence splice entry target=%s", target)
    source, formation, evidence = _evidence((0, 1, 2, 0))
    if target == "formation-source":
        forged = replace(evidence, formation_source_digest="0" * 64)
    elif target == "initial-boundary":
        forged = replace(
            evidence,
            initial_state=replace(
                evidence.initial_state,
                boundary=FormationBoundary.ALIVE,
            ),
        )
    elif target == "initial-cursor":
        forged = replace(
            evidence,
            initial_state=replace(evidence.initial_state, cursor=1),
        )
    elif target in {
        "tick-before",
        "tick-after",
        "tick-alive",
        "tick-index",
        "tick-symbol",
        "tick-digest",
    }:
        first = evidence.ticks[0]
        field = {
            "tick-before": "before_state_digest",
            "tick-after": "after_state_digest",
            "tick-alive": "became_alive",
            "tick-index": "tick_index",
            "tick-symbol": "observed_symbol",
            "tick-digest": "receipt_digest",
        }[target]
        if target == "tick-alive":
            value = True
        elif target in {"tick-index", "tick-symbol"}:
            value = 99
        else:
            value = "0" * 64
        ticks = (replace(first, **{field: value}), *evidence.ticks[1:])
        forged = replace(evidence, ticks=ticks)
    elif target == "tick-order":
        forged = replace(
            evidence,
            ticks=(evidence.ticks[1], evidence.ticks[0], *evidence.ticks[2:]),
        )
    elif target == "final-state":
        forged = replace(
            evidence,
            final_state=replace(evidence.final_state, state_digest="0" * 64),
        )
    elif target == "closure-index":
        forged = replace(evidence, first_closure_index=2)
    elif target == "pressure-entry":
        forged = replace(evidence, pressure_entry_state_digest="0" * 64)
    elif target == "status":
        forged = replace(evidence, status=FirstClosureStatus.REFUTED)
    elif target == "reason":
        forged = replace(evidence, reason="forged")
    elif target == "genealogy":
        forged = replace(evidence, genealogy_digest="0" * 64)
    elif target == "promotions":
        forged = replace(evidence, promotions=1)
    elif target == "nonclaims":
        forged = replace(evidence, nonclaims=())
    else:
        forged = replace(evidence, evidence_digest="0" * 64)
    expected_error = (
        "p3og-first-closure-evidence-malformed" if target == "nonclaims" else "p3og-first-closure-evidence-drift"
    )
    with pytest.raises(ValueError, match=expected_error):
        validate_first_closure_evidence(source, formation, forged)
    logger.debug("test_p3og_lifecycle evidence splice exit target=%s", target)


def test_hostile_evidence_scalar_is_rejected_without_equality_dispatch():
    logger.debug("test_p3og_lifecycle hostile evidence entry")
    source, formation, evidence = _evidence()
    forged = replace(evidence, reason=ExplosiveEquality())
    with pytest.raises(ValueError, match="p3og-first-closure-evidence-malformed"):
        validate_first_closure_evidence(source, formation, forged)
    logger.debug("test_p3og_lifecycle hostile evidence exit")


def test_uninitialized_outer_dtos_fail_with_typed_errors():
    logger.debug("test_p3og_lifecycle uninitialized DTO entry")
    source = _source()
    formation = p3og_formation_source(source)
    with pytest.raises(ValueError, match="p3og-formation-source-malformed"):
        validate_formation_source(source, object.__new__(P3OGFormationSource))
    with pytest.raises(ValueError, match="p3og-first-closure-evidence-malformed"):
        validate_first_closure_evidence(
            source,
            formation,
            object.__new__(P3OGFirstClosureEvidence),
        )
    logger.debug("test_p3og_lifecycle uninitialized DTO exit")


def test_oversized_word_and_evidence_tuple_are_preflighted():
    logger.debug("test_p3og_lifecycle resource preflight entry")
    source, formation, evidence = _evidence()
    with pytest.raises(ValueError, match="p3og-formation-source-malformed"):
        validate_formation_source(
            source,
            replace(formation, formation_word=tuple(range(65))),
        )
    inflated = replace(evidence, ticks=evidence.ticks * 100_000)
    with pytest.raises(ValueError, match="p3og-first-closure-evidence-malformed"):
        validate_first_closure_evidence(source, formation, inflated)
    logger.debug("test_p3og_lifecycle resource preflight exit")


def test_native_tick_rejects_forged_alive_seed_and_postclosure_tick():
    logger.debug("test_p3og_lifecycle native tick guard entry")
    source, formation, evidence = _evidence()
    _, formation = validate_formation_source(source, formation)
    forged_seed = replace(
        evidence.initial_state,
        boundary=FormationBoundary.ALIVE,
    )
    with pytest.raises(ValueError, match="p3og-formation-state-drift"):
        _validate_formation_state(formation, forged_seed)
    with pytest.raises(ValueError, match="p3og-formation-already-closed"):
        _formation_tick_validated(formation, evidence.final_state)
    logger.debug("test_p3og_lifecycle native tick guard exit")


def test_digest_consistent_state_after_first_closure_is_unreachable():
    logger.debug("test_p3og_lifecycle postclosure reachability entry")
    source = _source(word=(0, 1, 0, 2, 0))
    formation = p3og_formation_source(source)
    _, formation = validate_formation_source(source, formation)
    unreachable = _formation_state(formation, FormationBoundary.UNFORMED, 3)
    with pytest.raises(ValueError, match="p3og-formation-state-unreachable"):
        _validate_formation_state(formation, unreachable)
    with pytest.raises(ValueError, match="p3og-formation-state-unreachable"):
        _formation_tick_validated(formation, unreachable)
    logger.debug("test_p3og_lifecycle postclosure reachability exit")


def test_no_return_exhaustion_cannot_be_relabelled_as_witnessed():
    logger.debug("test_p3og_lifecycle no-return relabel entry")
    source, formation, evidence = _evidence((0, 1))
    assert evidence.status is FirstClosureStatus.REFUTED
    forged = replace(
        evidence,
        status=FirstClosureStatus.WITNESSED,
        reason="least-nontrivial-return-witnessed",
        first_closure_index=1,
        pressure_entry_state_digest="0" * 64,
        final_state=replace(
            evidence.final_state,
            boundary=FormationBoundary.ALIVE,
        ),
    )
    with pytest.raises(ValueError, match="p3og-first-closure-evidence-malformed"):
        validate_first_closure_evidence(source, formation, forged)
    logger.debug("test_p3og_lifecycle no-return relabel exit")
