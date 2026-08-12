"""Issue-3 observer multiplicity versus provenance independence controls."""

from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core.observer_provenance import (
    AgreementStatus,
    CorroborationStatus,
    IndependenceStatus,
    ObserverSupportRoute,
    ProvenanceDiagnosticError,
    ProvenanceNode,
    ProvenanceRole,
    assess_provenance_independence,
    build_observer_provenance_dag,
    build_scoped_agreement_binding,
    validate_provenance_independence_assessment,
)

logger = logging.getLogger(__name__)


def _digest(value: int) -> str:
    logger.debug("_digest entry value=%d", value)
    result = f"{value:064x}"
    logger.debug("_digest exit")
    return result


def _binding(status: AgreementStatus = AgreementStatus.ESTABLISHED):
    logger.debug("_binding entry status=%s", status.value)
    result = build_scoped_agreement_binding(
        (_digest(10), _digest(11)),
        _digest(20),
        _digest(21),
        _digest(22),
        _digest(23),
        _digest(24),
        status,
    )
    logger.debug("_binding exit")
    return result


def test_clone_consensus_preserves_agreement_but_refutes_independent_corroboration() -> None:
    """Distinct observer tokens sharing one decisive root are clone consensus."""
    logger.debug("test_clone_consensus_preserves_agreement_but_refutes_independence entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.SHARED_BASIS, (_digest(1),)),
            ProvenanceNode(_digest(3), ProvenanceRole.SHARED_BASIS, (_digest(1),)),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(2)),
            ObserverSupportRoute(_digest(11), _digest(3)),
        ),
        ancestry_complete=True,
    )
    agreement = _binding()
    result = assess_provenance_independence(dag, agreement)
    assert result.multi_observer_agreement is AgreementStatus.ESTABLISHED
    assert result.provenance_independence is IndependenceStatus.REFUTED
    assert result.independent_corroboration is CorroborationStatus.NOT_ESTABLISHED
    assert result.shared_decisive_digests == (_digest(1),)
    assert validate_provenance_independence_assessment(result, dag, agreement) is result
    logger.debug("test_clone_consensus_preserves_agreement_but_refutes_independence exit")


def test_shared_allowed_basis_does_not_defeat_disjoint_decisive_routes() -> None:
    """Shared policy basis is allowed when decisive source and control ancestry is disjoint."""
    logger.debug("test_shared_allowed_basis_does_not_defeat_disjoint_decisive_routes entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.SHARED_BASIS, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, (_digest(1),)),
            ProvenanceNode(_digest(3), ProvenanceRole.DECISIVE_CONTROL, (_digest(1),)),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(2)),
            ObserverSupportRoute(_digest(11), _digest(3)),
        ),
        ancestry_complete=True,
    )
    result = assess_provenance_independence(dag, _binding())
    assert result.provenance_independence is IndependenceStatus.ESTABLISHED
    assert result.independent_corroboration is CorroborationStatus.ESTABLISHED
    assert not result.shared_decisive_digests
    assert "not statistical" in result.boundary
    logger.debug("test_shared_allowed_basis_does_not_defeat_disjoint_decisive_routes exit")


@pytest.mark.parametrize("shared_endpoint", (False, True))
def test_routes_without_decisive_support_remain_open(shared_endpoint: bool) -> None:
    """Complete declaration alone cannot turn basis-only routes into corroboration."""
    logger.debug("test_routes_without_decisive_support_remain_open entry")
    nodes = (
        (ProvenanceNode(_digest(1), ProvenanceRole.SHARED_BASIS, ()),)
        if shared_endpoint
        else (
            ProvenanceNode(_digest(1), ProvenanceRole.SHARED_BASIS, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.SHARED_BASIS, ()),
        )
    )
    dag = build_observer_provenance_dag(
        nodes,
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(1) if shared_endpoint else _digest(2)),
        ),
        ancestry_complete=True,
    )
    result = assess_provenance_independence(dag, _binding())
    assert result.provenance_independence is IndependenceStatus.OPEN
    assert result.independent_corroboration is CorroborationStatus.NOT_ESTABLISHED
    logger.debug("test_routes_without_decisive_support_remain_open exit")


def test_incomplete_ancestry_is_open_and_does_not_invent_corroboration() -> None:
    """Explicitly incomplete provenance stays OPEN even when declared routes are disjoint."""
    logger.debug("test_incomplete_ancestry_is_open entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, ()),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(2)),
        ),
        ancestry_complete=False,
    )
    result = assess_provenance_independence(dag, _binding())
    assert result.provenance_independence is IndependenceStatus.OPEN
    assert result.independent_corroboration is CorroborationStatus.NOT_ESTABLISHED
    logger.debug("test_incomplete_ancestry_is_open exit")


def test_shared_decisive_control_refutes_and_dominates_incomplete_ancestry() -> None:
    """A concrete shared control root refutes independence even in an incomplete DAG."""
    logger.debug("test_shared_decisive_control_refutes entry")
    dag = build_observer_provenance_dag(
        (ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_CONTROL, ()),),
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(1)),
        ),
        ancestry_complete=False,
    )
    result = assess_provenance_independence(dag, _binding())
    assert result.provenance_independence is IndependenceStatus.REFUTED
    logger.debug("test_shared_decisive_control_refutes exit")


def test_three_route_family_detects_one_cloned_pair() -> None:
    """One shared decisive ancestor refutes the whole required three-route family."""
    logger.debug("test_three_route_family_detects_one_cloned_pair entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(3), ProvenanceRole.SHARED_BASIS, (_digest(1),)),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(3)),
            ObserverSupportRoute(_digest(12), _digest(2)),
        ),
        ancestry_complete=True,
    )
    agreement = build_scoped_agreement_binding(
        (_digest(10), _digest(11), _digest(12)),
        _digest(20), _digest(21), _digest(22), _digest(23), _digest(24),
        AgreementStatus.ESTABLISHED,
    )
    result = assess_provenance_independence(dag, agreement)
    assert result.provenance_independence is IndependenceStatus.REFUTED
    assert result.shared_decisive_digests == (_digest(1),)
    logger.debug("test_three_route_family_detects_one_cloned_pair exit")


def test_independent_routes_do_not_invent_missing_agreement() -> None:
    """Provenance separation alone is not corroboration when agreement is absent."""
    logger.debug("test_independent_routes_do_not_invent_missing_agreement entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, ()),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(2)),
        ),
        ancestry_complete=True,
    )
    result = assess_provenance_independence(dag, _binding(AgreementStatus.NOT_ESTABLISHED))
    assert result.provenance_independence is IndependenceStatus.ESTABLISHED
    assert result.independent_corroboration is CorroborationStatus.NOT_ESTABLISHED
    logger.debug("test_independent_routes_do_not_invent_missing_agreement exit")


@pytest.mark.parametrize("reason", ("cyclic-provenance-dag", "missing-provenance-parent"))
def test_malformed_provenance_graphs_fail_closed(reason: str) -> None:
    """Cycles and dangling parent identities never yield partial diagnostics."""
    logger.debug("test_malformed_provenance_graphs_fail_closed entry reason=%s", reason)
    nodes = (
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, (_digest(2),)),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, (_digest(1),)),
        )
        if reason == "cyclic-provenance-dag"
        else (ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, (_digest(9),)),)
    )
    routes = (
        ObserverSupportRoute(_digest(10), _digest(1)),
        ObserverSupportRoute(_digest(11), _digest(1)),
    )
    with pytest.raises(ProvenanceDiagnosticError, match=reason):
        build_observer_provenance_dag(nodes, routes, ancestry_complete=True)
    logger.debug("test_malformed_provenance_graphs_fail_closed exit")


def test_binding_family_mismatch_and_assessment_drift_fail_closed() -> None:
    """Foreign agreement bindings and changed verdicts cannot cross fresh replay."""
    logger.debug("test_binding_family_mismatch_and_assessment_drift_fail_closed entry")
    dag = build_observer_provenance_dag(
        (
            ProvenanceNode(_digest(1), ProvenanceRole.DECISIVE_SOURCE, ()),
            ProvenanceNode(_digest(2), ProvenanceRole.DECISIVE_SOURCE, ()),
        ),
        (
            ObserverSupportRoute(_digest(10), _digest(1)),
            ObserverSupportRoute(_digest(11), _digest(2)),
        ),
        ancestry_complete=True,
    )
    foreign = build_scoped_agreement_binding(
        (_digest(10), _digest(12)),
        _digest(20), _digest(21), _digest(22), _digest(23), _digest(24),
        AgreementStatus.ESTABLISHED,
    )
    with pytest.raises(ProvenanceDiagnosticError, match="agreement-observer-family-mismatch"):
        assess_provenance_independence(dag, foreign)

    agreement = _binding()
    result = assess_provenance_independence(dag, agreement)
    with pytest.raises(ProvenanceDiagnosticError, match="provenance-assessment-not-fresh"):
        validate_provenance_independence_assessment(
            replace(result, independent_corroboration=CorroborationStatus.NOT_ESTABLISHED),
            dag,
            agreement,
        )
    logger.debug("test_binding_family_mismatch_and_assessment_drift_fail_closed exit")
