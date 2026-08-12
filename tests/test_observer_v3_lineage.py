from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.core.observer_discovery_v3.dsl import closed_rows_digest, observer_program_digest
from src.core.observer_discovery_v3.dsl.types import ClosedObserverGrammar, ClosedObserverTerm
from src.core.observer_discovery_v3.ledger import OneShotReservation, reserve_one_shot
from src.core.observer_discovery_v3.lineage import (
    AdaptivePolicyStatus,
    AdaptiveValidityStatus,
    ExperimentDesignMode,
    FamilyRecordingStatus,
    LocalValidityStatus,
    PolicyClaimScope,
    ResearchLineError,
    TerminalLocalStatus,
    adaptive_inference_policy,
    assess_research_line,
    build_experiment_lineage_node,
    build_experiment_research_line,
    validate_experiment_research_line,
    validate_research_line_assessment,
)
from src.core.observer_discovery_v3.schema import (
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
)
from src.core.observer_discovery_v3.service import execute_one_shot_closed_evaluation


def digest(symbol: str) -> str:
    return symbol * 64


def node(
    symbol: str,
    *,
    parents: tuple[str, ...] = (),
    visible: tuple[str, ...] = (),
    mode: ExperimentDesignMode = ExperimentDesignMode.ISOLATED,
    reason: str = "",
    experiment_root: str | None = None,
    outcome_root: str | None = None,
    local_status: TerminalLocalStatus = TerminalLocalStatus.LOCALLY_VALID,
):
    return build_experiment_lineage_node(
        experiment_root or digest(symbol),
        parents,
        digest("a"),
        digest("b"),
        digest("c"),
        digest("d"),
        (digest("e"), digest("f")),
        visible,
        mode,
        reason,
        local_status,
        outcome_root or digest("0" if symbol != "0" else "1"),
    )


def governed_result(tmp_path: Path):
    schema = RepresentationSchema(
        "lineage-schema",
        (RepresentationField("bit", "binary", (0, 1)),),
        ("no", "yes"),
    )
    presentation = canonical_presentation(
        schema,
        (
            RepresentationRow("r0", "s0", "c0", "g0", (0,), "no"),
            RepresentationRow("r1", "s1", "c1", "g1", (1,), "yes"),
        ),
    )
    grammar = ClosedObserverGrammar("lineage-grammar", 1, (0,), ("column",), 1, 0, 1)
    terms = (ClosedObserverTerm("column", (0,)),)
    rows = tuple(tuple(row.values) for row in presentation.rows)
    reservation = OneShotReservation(
        "lineage-terminal",
        "lineage local validation",
        digest("a"),
        presentation.payload_digest,
        presentation.schema_digest,
        closed_rows_digest(rows),
        observer_program_digest(grammar, terms),
        digest("d"),
    )
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    capability = b"l" * 32
    reserve_one_shot(directory, reservation, capability)
    return execute_one_shot_closed_evaluation(
        directory,
        reservation.reservation_id,
        capability,
        "attempt-1",
        presentation,
        grammar,
        terms,
    )


def test_adaptive_line_records_visible_outcome_but_does_not_establish_inference(tmp_path: Path) -> None:
    first = node("1")
    result = governed_result(tmp_path)
    terminal = node(
        "2",
        parents=(first.node_digest,),
        visible=(first.terminal_outcome_root,),
        mode=ExperimentDesignMode.ADAPTIVE_AFTER_OUTCOME,
        reason="changed the grammar after inspecting the first null result",
        experiment_root=result.result_digest,
        outcome_root=result.terminal_ledger.outcome_digest,
    )
    lineage = build_experiment_research_line((terminal, first))
    assessment = assess_research_line(
        lineage,
        terminal.node_digest,
        governed_results=(result,),
    )

    assert validate_experiment_research_line(lineage)
    assert lineage.nodes == (first, terminal)
    assert assessment.local_validity is LocalValidityStatus.ESTABLISHED
    assert validate_research_line_assessment(
        assessment,
        lineage,
        governed_results=(result,),
    )
    assert assessment.family_recording is FamilyRecordingStatus.RECORDED_RELATIVE_TO_DECLARATION
    assert assessment.adaptive_validity is AdaptiveValidityStatus.NOT_ESTABLISHED
    assert assessment.policy_status is AdaptivePolicyStatus.ABSENT
    assert not assessment.significance_wording_allowed
    assert not assessment.population_wording_allowed
    assert not validate_research_line_assessment(
        replace(assessment, assessment_digest=digest("9")),
        lineage,
        governed_results=(result,),
    )


def test_named_policy_remains_unverified_and_exploratory_policy_forbids_inference() -> None:
    first = node("1")
    terminal = node(
        "2",
        parents=(first.node_digest,),
        visible=(first.terminal_outcome_root,),
        mode=ExperimentDesignMode.ADAPTIVE_AFTER_OUTCOME,
        reason="retry after outcome",
    )
    lineage = build_experiment_research_line((first, terminal))
    named = adaptive_inference_policy(
        "family-policy-1",
        "caller-defined-alpha-spending",
        digest("4"),
        PolicyClaimScope.INFERENTIAL,
    )
    named_result = assess_research_line(lineage, terminal.node_digest, policy=named)
    exploratory = adaptive_inference_policy(
        "exploratory-only",
        "no-family-inference",
        "",
        PolicyClaimScope.EXPLORATORY_ONLY,
    )
    exploratory_result = assess_research_line(lineage, terminal.node_digest, policy=exploratory)

    assert named_result.policy_status is AdaptivePolicyStatus.DECLARED_UNVERIFIED
    assert named_result.policy_id == "family-policy-1"
    assert named_result.policy_root == named.policy_root
    assert named_result.policy_evidence_root == digest("4")
    assert named_result.adaptive_validity is AdaptiveValidityStatus.NOT_ESTABLISHED
    assert exploratory_result.policy_status is AdaptivePolicyStatus.EXPLORATORY_ONLY
    assert exploratory_result.adaptive_validity is AdaptiveValidityStatus.EXPLORATORY_NO_INFERENCE_CLAIMED
    assert exploratory_result.allowed_claims == (
        "exploratory-family",
        "no-significance-or-population-claim",
    )
    with pytest.raises(ResearchLineError, match="policy-shape"):
        assess_research_line(
            lineage,
            terminal.node_digest,
            policy=replace(named, policy_root=digest("9")),
        )


def test_isolated_and_predeclared_modes_are_distinct_from_outcome_adaptation() -> None:
    isolated = node("1")
    predeclared = node(
        "2",
        parents=(isolated.node_digest,),
        mode=ExperimentDesignMode.PREDECLARED_CONTINUATION,
    )
    singleton = build_experiment_research_line((isolated,))
    lineage = build_experiment_research_line((predeclared, isolated))

    isolated_result = assess_research_line(singleton, isolated.node_digest)
    family_result = assess_research_line(lineage, predeclared.node_digest)
    assert isolated_result.adaptive_validity is AdaptiveValidityStatus.ISOLATED_LOCAL_ONLY
    assert family_result.adaptive_validity is AdaptiveValidityStatus.NOT_ESTABLISHED
    with pytest.raises(ResearchLineError, match="assessment-terminal-not-leaf"):
        assess_research_line(lineage, isolated.node_digest)


def test_hidden_or_forged_adaptive_history_fails_closed() -> None:
    first = node("1")
    with pytest.raises(ResearchLineError, match="adaptive-node-missing-history"):
        node(
            "2",
            parents=(first.node_digest,),
            mode=ExperimentDesignMode.ADAPTIVE_AFTER_OUTCOME,
            reason="retry",
        )
    forged_visible = node(
        "2",
        parents=(first.node_digest,),
        visible=(digest("9"),),
        mode=ExperimentDesignMode.ADAPTIVE_AFTER_OUTCOME,
        reason="retry",
    )
    with pytest.raises(ResearchLineError, match="visible-outcome-not-ancestor"):
        build_experiment_research_line((first, forged_visible))
    with pytest.raises(ResearchLineError, match="unknown-parent"):
        build_experiment_research_line(
            (
                node(
                    "3",
                    parents=(digest("9"),),
                    mode=ExperimentDesignMode.PREDECLARED_CONTINUATION,
                ),
            )
        )
    assert not validate_experiment_research_line(
        replace(build_experiment_research_line((first,)), lineage_digest=digest("9"))
    )


def test_hostile_resource_shapes_are_precharged() -> None:
    with pytest.raises(ResearchLineError, match="data-commitments"):
        build_experiment_lineage_node(
            digest("1"),
            (),
            digest("a"),
            digest("b"),
            digest("c"),
            digest("d"),
            (digest("e"),) * 9,
            (),
            ExperimentDesignMode.ISOLATED,
            "",
            TerminalLocalStatus.LOCALLY_VALID,
            digest("f"),
        )
    with pytest.raises(ResearchLineError, match="adaptation-reason"):
        node(
            "2",
            parents=(digest("1"),),
            visible=(digest("0"),),
            mode=ExperimentDesignMode.ADAPTIVE_AFTER_OUTCOME,
            reason="x" * 513,
        )
    with pytest.raises(ResearchLineError, match="lineage-node-count"):
        build_experiment_research_line((node("1"),) * 129)
