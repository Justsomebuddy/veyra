"""Focused structural, causal, hostile, and boundary tests for isolated P3-N0."""

from dataclasses import replace
from unittest.mock import patch

import pytest

from src.core.observer_network import observer_network_judgment
from src.core.prime_power_observer_actualization import (
    ActualizationStatus, BoundaryStatus, FiniteRelation, N0DoctrineOpen,
    N0GenealogyUnavailable,
    N0ValidationError, PremiseStatus, PrimePowerObserverActualizationJudgment,
    RoleStatus, SuffixSelector, audit_counterfactual_pair, counterfactual_histories,
    history_ledger, postbirth_ledger, prebirth_ledger,
    run_unavailable_bridge, unavailable_bridge_request, unavailable_n0_source,
    validate_n0_result,
)
from src.core.prime_power_observer_actualization_attack_matrix import run_attack_matrix
from src.core.prime_power_observer_actualization_attestation import AXIOM_ROWS, THEOREM_IDS
from src.core.prime_power_observer_actualization_formal import capture_size_required
from src.core.prime_power_observer_actualization_history import (
    REQUIRED_ACCESS, _event, pending_histories, rehash_history,
)
from src.core.prime_power_observer_actualization_history_validation import (
    audit_history, validate_history,
)
from src.core.prime_power_observer_actualization_runtime import (
    prime_power_observer_actualization,
)
from src.core.prime_power_reduction_network import finite_reduction_source
from src.core.prime_power_reduction_network_common import PrimePowerReductionValidationError
from src.core.prime_power_reduction_network_runtime import _finite_arrows

from prime_power_observer_actualization_fixture import exact_p3n0_source

pytestmark = pytest.mark.requires_lean


@pytest.fixture(scope="module")
def source():
    return exact_p3n0_source()


@pytest.fixture(scope="module")
def positive(source):
    value = prime_power_observer_actualization(source)
    assert type(value) is PrimePowerObserverActualizationJudgment
    return value


def test_exact_raw_packages_bridge_scope_and_theorem_source(source):
    assert tuple(package.integer.z for package in source.n1_packages) == (0, 1, 2)
    assert tuple(x.integer for x in source.strict_package.raw_package.finite.families) == (0, 2)
    assert tuple(x.integer for x in source.open_package.raw_package.finite.families) == (0,)
    assert source.scope.allowed_selectors == (
        SuffixSelector.STRICT_SUFFIX, SuffixSelector.OPEN_SUFFIX,
    )
    assert source.theorem_source.theorem_ids == THEOREM_IDS
    assert source.theorem_source.axiom_rows == AXIOM_ROWS
    assert capture_size_required(source) <= source.policy.max_captured_bytes


def test_admitted_and_nonadmitted_ledger_schemas_and_oracles_are_distinct(source):
    admitted = (prebirth_ledger(True), postbirth_ledger(True), history_ledger(True))
    nonadmitted = (prebirth_ledger(False), postbirth_ledger(False), history_ledger(False))
    assert all(item.axioms == ("A-HAP-admitted-model-doctrine",) for item in admitted)
    assert all(item.axioms == () for item in nonadmitted)
    assert all(item.ordered_rows == ("NA01", "NA02", "NA03", "NA04")
               for item in nonadmitted)
    assert len({item.ledger_digest for item in (*admitted, *nonadmitted)}) == 6


def test_pending_histories_have_no_outcome_then_replay_creates_bound_outcomes(source):
    pending = pending_histories(source)
    assert all("n2-selected" not in {event.event_id for event in item.events}
               for item in pending)
    strict, opened = counterfactual_histories(source)
    assert strict.events[-1].kind == opened.events[-1].kind == "N2F_OUTCOME"
    assert strict.events[-1].payload_digest == strict.replay_evidence.outcome_digest
    assert opened.events[-1].payload_digest == opened.replay_evidence.outcome_digest
    assert strict.outcome_digest != opened.outcome_digest
    assert strict.efficacy_digest != opened.efficacy_digest
    assert audit_counterfactual_pair(source, strict, opened) is PremiseStatus.ESTABLISHED


def test_positive_result_binds_concrete_la_rows_and_formal_receipts(source, positive):
    assert validate_n0_result(source, positive) == positive
    assert positive.role is RoleStatus.ESTABLISHED_RELATIVE_TO_DOCTRINE
    assert positive.actualization is (
        ActualizationStatus.ESTABLISHED_RELATIVE_TO_FINITE_ARITHMETIC_HISTORY
    )
    assert tuple(name for name, _ in positive.postbirth_evidence_ledger.row_payloads) == (
        "LA19", "LA20", "LA22",
    )
    assert len(positive.formal_attestation.receipts) == 4
    assert all(item.return_code == 0 for item in positive.formal_attestation.receipts)
    assert positive.promotions == 0


def test_nonadmitted_runtime_constructs_no_pending_birth_or_n2_outcome():
    source = exact_p3n0_source(admitted=False)
    with (patch("src.core.prime_power_observer_actualization_runtime.pending_histories") as pending,
          patch("src.core.prime_power_observer_actualization_runtime._replay_n2") as replay):
        value = prime_power_observer_actualization(source)
    assert type(value) is N0DoctrineOpen
    assert value.genealogy is PremiseStatus.ESTABLISHED
    assert value.role is RoleStatus.OPEN and value.actualization is ActualizationStatus.OPEN
    assert pending.call_count == replay.call_count == 0
    assert not hasattr(value, "historical_token_id")


def test_unavailable_bridge_runner_returns_only_semantic_genealogy_open(source):
    unavailable_source = unavailable_n0_source(
        source.prime, source.depth, source.lineage_id, policy=source.policy,
    )
    request = unavailable_bridge_request(unavailable_source)
    value = run_unavailable_bridge(request)
    assert type(value) is N0GenealogyUnavailable
    assert value.genealogy is PremiseStatus.OPEN
    assert value.role is RoleStatus.OPEN and value.actualization is ActualizationStatus.OPEN
    assert not hasattr(value, "historical_token_id")
    assert not hasattr(value, "n1_results") and not hasattr(value, "n2_results")
    assert validate_n0_result(request, value) == value
    with pytest.raises(N0ValidationError, match="n0-available-result-variant-invalid"):
        validate_n0_result(source, value)
    doctrine_source = exact_p3n0_source(admitted=False)
    doctrine = prime_power_observer_actualization(doctrine_source)
    with pytest.raises(N0ValidationError, match="n0-genealogy-unavailable-exact-type-required"):
        validate_n0_result(request, doctrine)


def test_exact_history_validation_rejects_rehashed_invariant_forgery(source, positive):
    strict, _ = counterfactual_histories(source)
    original = strict.events[5]
    forged = _event(original.event_id, original.kind, original.parents, original.token_id,
                    source, "0" * 64)
    history = rehash_history(
        source, strict, events=(*strict.events[:5], forged, *strict.events[6:]),
    )
    network = observer_network_judgment(source.strict_package.network_source,
                                        source.strict_package.network_policy)
    n2 = positive.n2_results[0]
    arrow = next(item for item in n2.finite_arrows
                 if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    with pytest.raises(N0ValidationError, match="n0-history-future-semantic-drift"):
        validate_history(source, history, network, n2, arrow)


def test_key_specific_prior_birth_and_missing_response_access_are_semantic(source):
    strict, _ = counterfactual_histories(source)
    birth = strict.events[4]
    earlier = _event("earlier-birth", birth.kind, birth.parents, None, source,
                     birth.payload_digest)
    causal_birth = _event(
        birth.event_id, birth.kind, (*birth.parents, earlier.event_id), None, source,
        birth.payload_digest,
    )
    prior = rehash_history(source, strict, events=(
        *strict.events[:4], earlier, causal_birth, *strict.events[5:],
    ))
    assert audit_history(source, prior)["first_birth"] is PremiseStatus.REFUTED
    missing = tuple(edge for edge in strict.access_edges
                    if (edge.consumer_id, edge.producer_id)
                    != ("reduction", "response-F0"))
    no_access = rehash_history(source, strict, access_edges=missing)
    assert audit_history(source, no_access)["post_birth_efficacy"] is PremiseStatus.OPEN


def test_disconnected_tuple_position_is_not_ancestry(source):
    strict, _ = counterfactual_histories(source)
    extra = _event("disconnected-target", "TARGET", (), None, source, "0" * 64)
    disconnected = rehash_history(source, strict, events=(extra, *strict.events))
    with pytest.raises(N0ValidationError, match="n0-history-disconnected-event"):
        audit_history(source, disconnected)


def test_replay_and_outcome_split_forgery_are_rejected(source):
    strict, _ = counterfactual_histories(source)
    forged_replay = replace(strict.replay_evidence, network_judgment_digest="0" * 64)
    forged = replace(strict, replay_evidence=forged_replay)
    with pytest.raises(N0ValidationError, match="n0-replay-evidence-drift"):
        audit_history(source, forged)
    split = rehash_history(source, replace(strict, outcome_digest="0" * 64))
    with pytest.raises(N0ValidationError, match="n0-history-replay-outcome-split"):
        audit_history(source, split)


def test_hostile_nested_shapes_raise_only_n0_validation(source, positive):
    hostile_attestation = replace(positive.formal_attestation, captured_hashes=1)
    with pytest.raises(N0ValidationError, match="n0-attestation-hashes-tuple-invalid"):
        validate_n0_result(source, replace(positive, formal_attestation=hostile_attestation))
    strict, _ = counterfactual_histories(source)
    hostile_event = replace(strict.events[0], parents=1)
    with pytest.raises(N0ValidationError, match="n0-event-parents-tuple-invalid"):
        audit_history(source, replace(strict, events=(hostile_event, *strict.events[1:])))
    hostile_replay = replace(strict.replay_evidence, producer_digests=1)
    with pytest.raises(N0ValidationError, match="n0-replay-producers-tuple-invalid"):
        audit_history(source, replace(strict, replay_evidence=hostile_replay))
    hostile_edge = replace(strict.access_edges[0], consumer_id=1)
    with pytest.raises(N0ValidationError, match="n0-edge-consumer-text-invalid"):
        audit_history(source, replace(strict, access_edges=(hostile_edge, *strict.access_edges[1:])))
    hostile_ledger = replace(source.prebirth_ledger, ordered_rows=1)
    with pytest.raises(N0ValidationError, match="source-prebirth_ledger-ordered_rows-exact-type-drift"):
        audit_history(replace(source, prebirth_ledger=hostile_ledger), strict)
    hostile_bound = replace(positive.postbirth_evidence_ledger, row_payloads=1)
    with pytest.raises(N0ValidationError, match="n0-bound-ledger-rows-tuple-invalid"):
        validate_n0_result(source, replace(positive, postbirth_evidence_ledger=hostile_bound))
    hostile_receipt = replace(positive.formal_attestation.receipts[0], phase_index=True)
    hostile_receipts = replace(
        positive.formal_attestation,
        receipts=(hostile_receipt, *positive.formal_attestation.receipts[1:]),
    )
    with pytest.raises(N0ValidationError, match="n0-phase-receipt-0-phase-int-invalid"):
        validate_n0_result(source, replace(positive, formal_attestation=hostile_receipts))


def test_positive_nested_results_are_freshly_revalidated(source, positive):
    class AlwaysEqual:
        def __eq__(self, _other): return True
    bad_n1 = replace(positive.n1_results[0], judgment_digest="0" * 64)
    with pytest.raises(N0ValidationError, match="n0-nested-n1-positive-0-validation-rejected"):
        validate_n0_result(source, replace(
            positive, n1_results=(bad_n1, *positive.n1_results[1:]),
        ))
    bad_n2 = replace(positive.n2_results[0], promotions=1)
    with pytest.raises(N0ValidationError, match="n0-nested-n2-promotions-invalid"):
        validate_n0_result(source, replace(
            positive, n2_results=(bad_n2, positive.n2_results[1]),
        ))
    theorem_ids = (AlwaysEqual(), *positive.n2_results[0].theorem_ids[1:])
    hostile_n2 = replace(positive.n2_results[0], theorem_ids=theorem_ids)
    with pytest.raises(N0ValidationError, match="n0-nested-n2-theorem-0-text-invalid"):
        validate_n0_result(source, replace(positive, n2_results=(hostile_n2, positive.n2_results[1])))
    for name in ("strict_relation", "open_relation"):
        with pytest.raises(N0ValidationError, match=f"n0-result-{name.replace('_', '-')}-text-invalid"):
            validate_n0_result(source, replace(positive, **{name: AlwaysEqual()}))
    with patch.object(PrimePowerObserverActualizationJudgment, "__eq__", side_effect=RuntimeError):
        with pytest.raises(N0ValidationError, match="n0-result-equality-rejected"):
            validate_n0_result(source, positive)


def test_released_n2_relations_are_strict_and_positive_open(source):
    strict = next(item for item in _finite_arrows(source.strict_package.raw_package)
                  if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    opened = next(item for item in _finite_arrows(source.open_package.raw_package)
                  if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    assert strict.relation is FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE
    assert opened.relation is FiniteRelation.OPEN
    with pytest.raises(PrimePowerReductionValidationError,
                       match="coarse-partition-not-representable"):
        finite_reduction_source(source.n1_packages[0].prime,
                                source.n1_packages[0].doctrine, (0, 1), (0, 1))


def test_boundary_nonpromotions_remain_exact(positive):
    assert positive.generic_e4_bridge is BoundaryStatus.OPEN
    assert positive.physical_instantiation is BoundaryStatus.NOT_ESTABLISHED
    assert positive.consciousness is BoundaryStatus.NOT_CLAIMED
    assert positive.absolute_observerhood is BoundaryStatus.NOT_CLAIMED
    assert positive.strict_relation != positive.open_relation


def test_result_validator_recomputes_attestation_and_concrete_ledger(source, positive):
    receipt = replace(positive.formal_attestation.receipts[0], return_code=1)
    attestation = replace(
        positive.formal_attestation,
        receipts=(receipt, *positive.formal_attestation.receipts[1:]),
    )
    with pytest.raises(N0ValidationError, match="n0-formal-attestation-drift"):
        validate_n0_result(source, replace(positive, formal_attestation=attestation))
    ledger = replace(
        positive.postbirth_evidence_ledger,
        row_payloads=(("LA19", "0" * 64),
                      *positive.postbirth_evidence_ledger.row_payloads[1:]),
    )
    with pytest.raises(N0ValidationError, match="n0-bound-postbirth-ledger-drift"):
        validate_n0_result(source, replace(positive, postbirth_evidence_ledger=ledger))


def test_collision_safe_public_aliases_remain_isolated():
    from src.core.prime_power_observer_actualization_public import (
        P3N0Policy, P3N0Source, p3n0_exact_source,
    )

    value = p3n0_exact_source()
    assert type(value) is P3N0Source and type(value.policy) is P3N0Policy


def test_all_24_base_attacks_execute_as_40_exact_submissions(source, positive):
    submissions = run_attack_matrix(source, positive)
    assert len(submissions) == 40
    assert {item.base_id for item in submissions} == {f"A{i:02d}" for i in range(1, 25)}
    assert all(item.actual == item.expected and item.passed for item in submissions)
    assert {(item.base_id, item.variant) for item in submissions} >= {
        ("A04", "forged-event-unhashed"), ("A04", "forged-event-rehashed"),
        ("A15", "same-pretoken-prior-birth-rehashed"),
        ("A18", "missing-response-access-rehashed"),
    }


def test_required_access_set_is_exact():
    assert len(REQUIRED_ACCESS) == 9 and len(set(REQUIRED_ACCESS)) == 9
