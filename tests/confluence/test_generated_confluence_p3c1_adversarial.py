"""Required P3-C1 countermodels and hostile boundaries."""

from dataclasses import replace
import pytest

from src.core.generated_confluence import (
    FailedBound,
    GeneratedConfluenceError,
    GeneratedConfluenceResourceLimit,
    GeneratedConfluenceStatus,
    StateRank,
    continuation_edge,
    continuation_state,
    generated_finite_confluence,
    local_join_cell,
    ranked_continuation_system,
    snapshot_ranked_system,
    validate_generated_confluence_result,
)
from generated_confluence_fixture import positive_package

pytestmark = pytest.mark.requires_lean


def test_omitted_generated_peak_is_open_and_caller_cannot_curate_universe():
    system, cells = positive_package()
    result = generated_finite_confluence(system, cells[1:])
    assert len(result.peaks) == 2 and len(result.rows) == 2
    assert result.status is GeneratedConfluenceStatus.OPEN
    assert result.first_counterexample_peak_id == result.peaks[0].peak_id


def test_cycle_hidden_by_equal_payload_alias_is_rejected():
    system, _ = positive_package()
    alias = continuation_state("w-alias", "node", b"w")
    edges = tuple(
        sorted(
            (
                *system.edges,
                continuation_edge("alias-in", "w", "w-alias", "cycle", b"equal-payload"),
                continuation_edge("alias-out", "w-alias", "w", "cycle", b"equal-payload"),
            ),
            key=lambda row: row.edge_id,
        )
    )
    hostile = replace(
        system,
        states=tuple(sorted((*system.states, alias), key=lambda row: row.state_id)),
        edges=edges,
        ranks=tuple(sorted((*system.ranks, StateRank("w-alias", 0)), key=lambda row: row.state_id)),
    )
    assert alias.payload == next(row.payload for row in system.states if row.state_id == "w")
    with pytest.raises(GeneratedConfluenceError, match="strictly-decrease"):
        snapshot_ranked_system(hostile)


def test_rank_after_edges_and_reachable_edge_mutation_fail_closed():
    system, _ = positive_package()
    ranks = tuple(StateRank(row.state_id, 3 if row.state_id == "y" else row.rank) for row in system.ranks)
    with pytest.raises(GeneratedConfluenceError, match="strictly-decrease"):
        snapshot_ranked_system(replace(system, ranks=ranks))
    mutated = tuple(replace(edge, rule_payload=b"mutated") if edge.edge_id == "yw" else edge for edge in system.edges)
    with pytest.raises(GeneratedConfluenceError, match="edge-commitment-mismatch"):
        snapshot_ranked_system(replace(system, edges=mutated))
    added = tuple(sorted((*system.edges, continuation_edge("yz", "y", "z", "late", b"late")), key=lambda x: x.edge_id))
    with pytest.raises(GeneratedConfluenceError):
        snapshot_ranked_system(replace(system, edges=added))


def test_equal_endpoint_ids_cannot_hide_unequal_commitments():
    system, _ = positive_package()
    states = tuple(
        replace(state, state_commitment="0" * 64) if state.state_id == "w" else state for state in system.states
    )
    with pytest.raises(GeneratedConfluenceError, match="state-commitment-mismatch"):
        snapshot_ranked_system(replace(system, states=states))


def test_translation_mode_is_unrepresentable_and_pure_mismatch_is_refuted():
    system, cells = positive_package()
    peak0, peak1 = generated_finite_confluence(system, cells).peaks
    with pytest.raises(GeneratedConfluenceError, match="mode-invalid"):
        local_join_cell(system, peak0.peak_id, ("yw",), ("zw",), "w", "translated-c3")
    false_relation = local_join_cell(system, peak1.peak_id, (), (), "z")
    result = generated_finite_confluence(system, (false_relation,))
    assert result.rows[0].status is GeneratedConfluenceStatus.OPEN
    assert result.rows[1].status is GeneratedConfluenceStatus.REFUTED
    assert result.status is GeneratedConfluenceStatus.REFUTED
    assert "no-c1-c3-transport-claim" in result.nonclaims


def test_two_distinct_pure_fillers_do_not_claim_transport_coherence():
    system, cells = positive_package()
    at_w = generated_finite_confluence(system, cells)
    at_v_cells = tuple(
        local_join_cell(
            system,
            cell.peak_id,
            (*cell.left_edge_ids, "wv"),
            (*cell.right_edge_ids, "wv"),
            "v",
        )
        for cell in cells
    )
    at_v = generated_finite_confluence(system, at_v_cells)
    positive = GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
    assert at_w.status is at_v.status is positive
    assert at_w.result_digest != at_v.result_digest
    assert "transport-path-independence" in at_v.nonclaims


def test_foreign_transplant_and_invalid_same_system_path_raise():
    system, cells = positive_package()
    foreign = replace(system, source_id="foreign", system_digest="0" * 64)
    foreign = ranked_continuation_system(
        foreign.doctrine_fingerprint,
        foreign.source_id,
        foreign.source_version,
        foreign.states,
        foreign.edges,
        foreign.roots,
        foreign.ranks,
    )
    transplanted = local_join_cell(foreign, cells[0].peak_id, ("yw",), ("zw",), "w")
    with pytest.raises(GeneratedConfluenceError, match="commitment-mismatch"):
        generated_finite_confluence(system, (transplanted, cells[1]))
    invalid = local_join_cell(system, cells[0].peak_id, ("zw",), ("yw",), "w")
    with pytest.raises(GeneratedConfluenceError, match="not-composable"):
        generated_finite_confluence(system, (invalid, cells[1]))


def test_resource_refusal_is_typed_and_not_open_or_refuted():
    system, cells = positive_package()
    oversized = replace(system, states=system.states * 17)
    result = generated_finite_confluence(oversized, cells)
    assert type(result) is GeneratedConfluenceResourceLimit
    assert result.failed_bound is FailedBound.STATES
    assert not hasattr(result, "first_counterexample_peak_id")
    assert validate_generated_confluence_result(oversized, cells, result) == result


def test_hostile_result_mutation_and_wrong_outer_type_fail_before_acceptance():
    system, cells = positive_package()
    result = generated_finite_confluence(system, cells)
    with pytest.raises(GeneratedConfluenceError, match="generated-result"):
        validate_generated_confluence_result(system, cells, replace(result, status=GeneratedConfluenceStatus.OPEN))
    with pytest.raises(GeneratedConfluenceError, match="result-type-invalid"):
        validate_generated_confluence_result(system, cells, {"result_digest": result.result_digest})


class _EncodeBomb:
    def encode(self, *args, **kwargs):
        raise AssertionError("must not call attacker encode")


def test_hard_preflight_rejects_nested_type_bombs_before_digest_or_semantics():
    system, cells = positive_package()
    with pytest.raises(GeneratedConfluenceError, match="cell-path-item-type-invalid"):
        generated_finite_confluence(system, (replace(cells[0], left_edge_ids=(7,)), cells[1]))
    with pytest.raises(GeneratedConfluenceError, match="cell-peak_id-type-invalid"):
        generated_finite_confluence(system, (replace(cells[0], peak_id=_EncodeBomb()), cells[1]))
    result = generated_finite_confluence(system, cells)
    with pytest.raises(GeneratedConfluenceError, match="status-type-invalid"):
        validate_generated_confluence_result(system, cells, replace(result, status=7))
    bomb_peak = replace(result.peaks[0], peak_id=_EncodeBomb())
    with pytest.raises(GeneratedConfluenceError, match="peak-peak_id-invalid"):
        validate_generated_confluence_result(system, cells, replace(result, peaks=(bomb_peak, *result.peaks[1:])))


def test_two_megabyte_id_and_root_are_typed_canonical_byte_refusals():
    system, cells = positive_package()
    huge = "x" * (2 * 1024 * 1024)
    hostile_state = replace(system.states[0], state_id=huge)
    hostile_rank = replace(system.ranks[0], state_id=huge)
    hostile_cell = replace(cells[0], left_edge_ids=(huge,))
    cases = (
        (replace(system, source_id=huge), cells),
        (replace(system, roots=(huge,)), cells),
        (replace(system, states=(hostile_state, *system.states[1:])), cells),
        (replace(system, ranks=(hostile_rank, *system.ranks[1:])), cells),
        (system, (hostile_cell, cells[1])),
    )
    for hostile_system, hostile_cells in cases:
        result = generated_finite_confluence(hostile_system, hostile_cells)
        assert type(result) is GeneratedConfluenceResourceLimit
        assert result.failed_bound is FailedBound.CANONICAL_BYTES
