"""Executable ten-attack boundary ledger for P3-C1."""

from __future__ import annotations

from dataclasses import dataclass, replace
import logging

from .common import GeneratedConfluenceError
from .countermodels import local_nonterminating_countermodel
from .runtime import generated_finite_confluence, local_join_cell
from .source import (
    continuation_edge,
    continuation_state,
    ranked_continuation_system,
    snapshot_ranked_system,
)
from .types import (
    CellMode,
    GeneratedConfluenceResourceLimit,
    GeneratedConfluenceStatus,
    GeneratedFiniteConfluence,
    LocalJoinCell,
    NO_C1_C3_TRANSPORT_CLAIM,
    RankedContinuationSystem,
    StateRank,
)

logger = logging.getLogger(__name__)
ATTACK_IDS = (
    "omitted-generated-peak",
    "local-nonterminating-two-normals",
    "equal-payload-hidden-cycle",
    "rank-after-edge-selection",
    "endpoint-id-unequal-commitment",
    "translation-does-not-create-join",
    "two-fillers-not-transport-coherence",
    "reachable-edge-after-snapshot",
    "foreign-cell-transplant",
    "resource-not-open-or-refuted",
)


@dataclass(frozen=True)
class GeneratedConfluenceAttackRow:
    attack_id: str
    passed: bool


def required_counterpressure(
    system: RankedContinuationSystem,
    cells: tuple[LocalJoinCell, ...],
    positive: GeneratedFiniteConfluence,
) -> tuple[GeneratedConfluenceAttackRow, ...]:
    """Run and derive the exact ordered ten P3-C1 attacks."""
    logger.debug("required_counterpressure entry")
    omitted = generated_finite_confluence(system, cells[1:])
    counter = local_nonterminating_countermodel()
    alias = continuation_state("w-alias", "node", b"w")
    cycle_edges = tuple(
        sorted(
            (
                *system.edges,
                continuation_edge("w-alias-in", "w", "w-alias", "alias-cycle", b"same-payload"),
                continuation_edge("w-alias-out", "w-alias", "w", "alias-cycle", b"same-payload"),
            ),
            key=lambda row: row.edge_id,
        )
    )
    hidden_cycle = replace(
        system,
        states=tuple(sorted((*system.states, alias), key=lambda row: row.state_id)),
        edges=cycle_edges,
        ranks=tuple(sorted((*system.ranks, StateRank("w-alias", 0)), key=lambda row: row.state_id)),
    )
    ranks = tuple(StateRank(row.state_id, 4 if row.state_id == "y" else row.rank) for row in system.ranks)
    rank_after = replace(system, ranks=ranks)
    bad_states = tuple(replace(row, state_commitment="0" * 64) if row.state_id == "w" else row for row in system.states)
    endpoint = replace(system, states=bad_states)
    translation_rejected = _rejects(
        lambda: local_join_cell(
            system,
            cells[0].peak_id,
            cells[0].left_edge_ids,
            cells[0].right_edge_ids,
            "w",
            "translated-c3",  # type: ignore[arg-type]
        )
    )
    alternate_cells = tuple(
        local_join_cell(
            system,
            cell.peak_id,
            (*cell.left_edge_ids, "wv"),
            (*cell.right_edge_ids, "wv"),
            "v",
        )
        for cell in cells
    )
    alternate = generated_finite_confluence(system, alternate_cells)
    late_edges = tuple(
        sorted(
            (
                *system.edges,
                continuation_edge("yv-late", "y", "v", "late", b"late"),
            ),
            key=lambda row: row.edge_id,
        )
    )
    late = replace(system, edges=late_edges)
    foreign_system = ranked_continuation_system(
        system.doctrine_fingerprint,
        "foreign-system",
        system.source_version,
        system.states,
        system.edges,
        system.roots,
        system.ranks,
    )
    transplanted = local_join_cell(
        foreign_system,
        cells[0].peak_id,
        cells[0].left_edge_ids,
        cells[0].right_edge_ids,
        cells[0].claimed_join_state_id,
    )
    resource = generated_finite_confluence(replace(system, states=system.states * 17), cells)
    values = (
        omitted.status is GeneratedConfluenceStatus.OPEN and len(omitted.peaks) == 2,
        counter.local_peaks_joinable and not counter.globally_confluent and counter.distinct_normal_forms == ("c", "d"),
        alias.payload == next(row.payload for row in system.states if row.state_id == "w")
        and _rejects(lambda: snapshot_ranked_system(hidden_cycle)),
        _rejects(lambda: snapshot_ranked_system(rank_after)),
        _rejects(lambda: snapshot_ranked_system(endpoint)),
        translation_rejected
        and tuple(CellMode) == (CellMode.PURE_RELATION_PATH,)
        and NO_C1_C3_TRANSPORT_CLAIM in positive.nonclaims,
        alternate.status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
        and alternate.result_digest != positive.result_digest
        and "transport-path-independence" in alternate.nonclaims,
        _rejects(lambda: snapshot_ranked_system(late)),
        _rejects(lambda: generated_finite_confluence(system, (transplanted, cells[1]))),
        type(resource) is GeneratedConfluenceResourceLimit,
    )
    result = tuple(GeneratedConfluenceAttackRow(name, passed) for name, passed in zip(ATTACK_IDS, values, strict=True))
    logger.debug("required_counterpressure exit passed=%d", sum(row.passed for row in result))
    return result


def _rejects(action) -> bool:
    logger.debug("_rejects entry")
    try:
        action()
    except GeneratedConfluenceError:
        logger.debug("_rejects exit rejected=true")
        return True
    logger.error("_rejects exit rejected=false")
    return False
