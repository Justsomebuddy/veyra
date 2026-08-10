from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.observer_discovery import BLOCKED, FOUND, NOT_FOUND_WITHIN_BUDGET, discover_observer
from src.core.observer_discovery_claim_types import (
    ClaimDisposition,
    DiscoveryExecutionLevel,
    DiscoveryInterpretationLevel,
    DiscoveryObserverRole,
    DiscoveryOntologyLevel,
)
from src.core.observer_discovery_claims import (
    observer_discovery_claim,
    validate_observer_discovery_claim,
)
from src.core.observer_discovery_types import DiscoveryConfig, DiscoveryRow, DiscoverySplit
from src.core.observer_synthesis_types import (
    NamedBaseline,
    ObserverGrammar,
    ObserverPrimitive,
    ObserverTerm,
)


def first_bit(value: object) -> int:
    return value[0]  # type: ignore[index]


def parity(value: object) -> int:
    return value[0] ^ value[1]  # type: ignore[index]


def constant_zero(_value: object) -> int:
    return 0


def _term(name: str) -> ObserverTerm:
    return ObserverTerm("apply", "scalar", name, (ObserverTerm("input", "input"),))


def _grammar() -> ObserverGrammar:
    return ObserverGrammar(
        "test-discovery-claims",
        "input",
        ("scalar",),
        (
            ObserverPrimitive("first", "input", "scalar", 1, first_bit, "claim:first:v1"),
            ObserverPrimitive("parity", "input", "scalar", 1, parity, "claim:parity:v1"),
            ObserverPrimitive("constant", "input", "scalar", 1, constant_zero, "claim:constant:v1"),
        ),
        1,
        1,
    )


def _baseline() -> tuple[NamedBaseline, ...]:
    return (
        NamedBaseline(
            "constant",
            "constant-observers",
            _term("constant"),
            "declared claim test baseline",
        ),
    )


def _rows(name: str, target_mode: str = "parity") -> tuple[DiscoveryRow, ...]:
    rows = []
    for index in range(24):
        bits = ((index // 2) % 2, index % 2)
        target = bits[0] ^ bits[1] if target_mode == "parity" else bits[0]
        rows.append(
            DiscoveryRow(
                f"{name}-row-{index}",
                f"{name}-source-{index}",
                f"{name}-content-{index}",
                f"{name}-group-{index}",
                bits,
                target,
            ),
        )
    return tuple(rows)


def _config(**changes: object) -> DiscoveryConfig:
    values: dict[str, object] = {
        "permutation_count": 39,
        "bootstrap_replicates": 16,
        "max_catalog_size": 32,
        "random_seed": "claim-envelope-test",
    }
    values.update(changes)
    return DiscoveryConfig(**values)  # type: ignore[arg-type]


def _report(holdout_mode: str = "parity", **config: object):
    split = DiscoverySplit(_rows("train"), _rows("holdout", holdout_mode))
    return discover_observer(_grammar(), split, _baseline(), _config(**config))


def test_found_report_maps_to_orthogonal_nonpromoting_claim() -> None:
    report = _report()
    assert report.status == FOUND

    claim = observer_discovery_claim(report)

    assert claim.execution is DiscoveryExecutionLevel.LOCKED_HOLDOUT_PASSED
    assert claim.interpretation is DiscoveryInterpretationLevel.DECLARED_BASELINE_GAP
    assert claim.ontology is DiscoveryOntologyLevel.PRESENTATION_ONLY
    assert claim.observer_role is DiscoveryObserverRole.RESEARCH_SHADOW
    assert claim.association_witness is ClaimDisposition.SUPPORTED
    assert claim.bounded_search_nonfinding is ClaimDisposition.NOT_CLAIMED
    assert {
        claim.causality,
        claim.semantic_explanation,
        claim.theoremhood,
        claim.object_formation,
        claim.p0_admission,
        claim.historical_novelty,
    } == {ClaimDisposition.NOT_CLAIMED}
    assert validate_observer_discovery_claim(claim, report)


def test_not_found_supports_only_finite_protocol_absence() -> None:
    report = _report(holdout_mode="first")
    assert report.status == NOT_FOUND_WITHIN_BUDGET

    claim = observer_discovery_claim(report)

    assert claim.execution is DiscoveryExecutionLevel.BOUNDED_SEARCH_COMPLETE
    assert claim.interpretation is DiscoveryInterpretationLevel.NONE
    assert claim.association_witness is ClaimDisposition.NOT_ESTABLISHED
    assert claim.bounded_search_nonfinding is ClaimDisposition.SUPPORTED
    assert claim.theoremhood is ClaimDisposition.NOT_CLAIMED


def test_blocked_report_carries_no_empirical_claim() -> None:
    report = _report(permutation_count=1)
    assert report.status == BLOCKED

    claim = observer_discovery_claim(report)

    assert claim.execution is DiscoveryExecutionLevel.BLOCKED
    assert claim.interpretation is DiscoveryInterpretationLevel.NONE
    assert claim.association_witness is ClaimDisposition.NOT_CLAIMED
    assert claim.bounded_search_nonfinding is ClaimDisposition.NOT_CLAIMED


def test_claim_is_deterministic_and_bound_to_report_roots() -> None:
    report = _report()
    first = observer_discovery_claim(report)
    second = observer_discovery_claim(report)

    assert first == second
    assert len(first.claim_digest) == 64
    assert first.scope.result_digest == report.digests.result
    assert first.scope.protocol_digest == report.digests.protocol
    assert first.scope.train_data_digest == report.digests.train_data
    assert first.scope.holdout_data_digest == report.digests.holdout_data


def test_claim_validator_rejects_status_scope_and_digest_promotion() -> None:
    report = _report()
    claim = observer_discovery_claim(report)

    attacks = (
        replace(claim, causality=ClaimDisposition.SUPPORTED),
        replace(claim, ontology=DiscoveryOntologyLevel.PRESENTATION_ONLY, claim_digest="0" * 64),
        replace(claim, scope=replace(claim.scope, result_digest="f" * 64)),
        replace(claim, bounded_search_nonfinding=ClaimDisposition.SUPPORTED),
    )
    assert all(not validate_observer_discovery_claim(attack, report) for attack in attacks)
    assert not validate_observer_discovery_claim(object(), report)


def test_invalid_source_report_cannot_issue_claim() -> None:
    report = _report()
    forged = replace(report, status=BLOCKED)

    with pytest.raises(ValueError, match="invalid-discovery-report"):
        observer_discovery_claim(forged)
    assert not validate_observer_discovery_claim(observer_discovery_claim(report), forged)


def test_trusted_train_root_pin_is_preserved() -> None:
    report = _report()
    claim = observer_discovery_claim(
        report,
        expected_train_evaluation=report.digests.train_evaluation,
    )

    assert validate_observer_discovery_claim(
        claim,
        report,
        expected_train_evaluation=report.digests.train_evaluation,
    )
    with pytest.raises(ValueError, match="invalid-discovery-report"):
        observer_discovery_claim(report, expected_train_evaluation="0" * 64)
