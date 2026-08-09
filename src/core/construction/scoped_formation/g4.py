"""Fresh response-derived G4 bridge replay for P1-C4."""

from __future__ import annotations

from dataclasses import replace
from itertools import combinations
import json
import logging

from ...confluence.path import replay_diagram_path
from ...observer_core_codec import decode_observer
from ...observer_core_semantics import echo
from ...observer_core_support import outcome_data
from ...observer_core_types import DomainBlocked, Echo, Mismatch
from ...observer.patch_atlas import (
    exact_gluing_criterion, generated_echo_closure, local_observer_section,
)
from .codec import ScopedFormationValidationError, digest
from .types import (
    BoundG4BridgeJudgment, BoundG4BridgeSource, G4ContradictionRow, G4ResponseRow,
    ScopedFormationStatus,
)

logger = logging.getLogger(__name__)


def expected_g4_response_keys(bridge: BoundG4BridgeSource) -> tuple[tuple[str, str, str, str], ...]:
    """Derive the exact ordered response catalog without observation."""
    logger.debug("expected_g4_response_keys entry")
    result = tuple(
        (patch.name, observer_id, left, right)
        for patch, requirement in zip(bridge.atlas.patches, bridge.patch_requirements, strict=True)
        for left, right in combinations(patch.nodes, 2)
        for observer_id in requirement.observer_ids
    )
    logger.debug("expected_g4_response_keys exit rows=%d", len(result))
    return result


def replay_bound_g4_bridge(doctrine, diagram, bridge: BoundG4BridgeSource) -> BoundG4BridgeJudgment:
    """Derive every response row, local section, and exact-gluing obstruction."""
    logger.debug("replay_bound_g4_bridge entry")
    stages = {x.stage_id: x for x in diagram.stages}
    observers = {x.observer_id: x for x in doctrine.observers}
    mapped = {x.node_id: stages[x.stage_id] for x in bridge.stage_map}
    rows: list[G4ResponseRow] = []
    sections = []
    for patch, requirement in zip(bridge.atlas.patches, bridge.patch_requirements, strict=True):
        _require_path_coverage(doctrine, diagram, requirement.path_ids, tuple(mapped[x].stage_id for x in patch.nodes))
        patch_rows: list[G4ResponseRow] = []
        for left, right in combinations(patch.nodes, 2):
            for observer_id in requirement.observer_ids:
                outcome = echo(
                    decode_observer(observers[observer_id].canonical),
                    mapped[left].representative, mapped[right].representative,
                )
                patch_rows.append(_response_row(patch.name, observer_id, left, right, outcome))
        rows.extend(patch_rows)
        blocks = _derived_blocks(patch.nodes, patch_rows, requirement.observer_ids)
        sections.append(local_observer_section(bridge.atlas, patch.name, blocks))
    section_tuple = tuple(sections)
    contradiction_rows = _positive_contradictions(bridge.atlas, section_tuple, rows)
    first_contradiction = contradiction_rows[0] if contradiction_rows else None
    criterion = exact_gluing_criterion(bridge.atlas, section_tuple)
    opened = next((x for x in rows if x.status is ScopedFormationStatus.OPEN), None)
    if contradiction_rows:
        status = ScopedFormationStatus.REFUTED
        obstruction = first_contradiction.contradiction_digest
    elif opened is not None:
        status, obstruction = ScopedFormationStatus.OPEN, opened.row_digest
    elif not criterion.iff_holds or not criterion.exact_gluing_exists:
        logger.error("replay_bound_g4_bridge criterion invariant failed")
        raise RuntimeError("g4 exact criterion invariant failed")
    else:
        status, obstruction = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, ""
    section_digests = tuple(digest("c4.g4.section", x.patch_name, x.blocks) for x in section_tuple)
    expected_patch_keys = tuple(x.name for x in bridge.atlas.patches)
    expected_response_keys = expected_g4_response_keys(bridge)
    actual_response_keys = tuple(
        (x.patch_id, x.observer_id, x.left_node, x.right_node) for x in rows
    )
    if actual_response_keys != expected_response_keys:
        logger.error("replay_bound_g4_bridge response catalog drift")
        raise RuntimeError("g4 response catalog drift")
    criterion_digest = digest(
        "c4.g4.criterion", criterion.obstruction_count,
        criterion.no_local_contradiction, criterion.exact_gluing_exists,
        criterion.witness, criterion.iff_holds,
    )
    trace = digest(
        "c4.g4.trace", tuple(x.row_digest for x in rows), section_digests,
        contradiction_rows, first_contradiction,
    )
    run = digest(
        "c4.g4.run", bridge.doctrine_fingerprint, bridge.diagram_digest,
        bridge.bridge_digest, expected_patch_keys, expected_response_keys,
    )
    provisional = BoundG4BridgeJudgment(
        bridge.doctrine_fingerprint, bridge.diagram_digest, bridge.bridge_digest,
        expected_patch_keys, expected_response_keys, tuple(rows), section_tuple,
        section_digests, contradiction_rows, first_contradiction, criterion_digest,
        status, obstruction, trace, run, "",
    )
    result = replace(provisional, judgment_digest=digest("c4.g4.judgment", provisional))
    logger.debug("replay_bound_g4_bridge exit status=%s rows=%d", status.value, len(rows))
    return result


def g4_response_check_count(bridge: BoundG4BridgeSource) -> int:
    """Count every required patch-pair observer response before replay."""
    logger.debug("g4_response_check_count entry")
    total = sum(
        (len(req.expected_nodes) * (len(req.expected_nodes) - 1) // 2) * len(req.observer_ids)
        for req in bridge.patch_requirements
    )
    logger.debug("g4_response_check_count exit checks=%d", total)
    return total


def _require_path_coverage(doctrine, diagram, path_ids: tuple[str, ...], stage_ids: tuple[str, ...]) -> None:
    """Require every mapped patch stage to occur in its bound raw histories."""
    logger.debug("_require_path_coverage entry paths=%d", len(path_ids))
    seen: set[str] = set()
    for path_id in path_ids:
        seen.update(x.stage_id for x in replay_diagram_path(doctrine, diagram, path_id).stages)
    if any(x not in seen for x in stage_ids):
        logger.error("_require_path_coverage incomplete")
        raise ScopedFormationValidationError("g4-history-coverage-incomplete")
    logger.debug("_require_path_coverage exit")


def _response_row(patch: str, observer: str, left: str, right: str, outcome: object) -> G4ResponseRow:
    """Encode one fresh exact response comparison without hidden payloads."""
    logger.debug("_response_row entry patch=%s", patch)
    if type(outcome) is Echo:
        status, name = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, "echo"
    elif type(outcome) is Mismatch:
        status, name = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, "split"
    elif type(outcome) is DomainBlocked:
        status, name = ScopedFormationStatus.OPEN, "blocked"
    else:
        logger.error("_response_row unexpected outcome type=%s", type(outcome).__name__)
        raise RuntimeError("unexpected G4 echo outcome")
    encoded = outcome_data(outcome)
    if type(outcome) is Echo:
        left_data = right_data = encoded["value"]
    elif type(outcome) is Mismatch:
        left_data, right_data = encoded["left"], encoded["right"]
    else:
        try:
            left_data, right_data = encoded["left"], encoded["right"]
        except KeyError as exc:
            logger.error("_response_row domain-blocked canonical keys missing")
            raise RuntimeError("domain-blocked canonical payload drift") from exc
    left_bytes = json.dumps(left_data, sort_keys=True, separators=(",", ":")).encode()
    right_bytes = json.dumps(right_data, sort_keys=True, separators=(",", ":")).encode()
    row = G4ResponseRow(
        patch, observer, left, right, status, name,
        digest("c4.g4.payload", left_bytes), digest("c4.g4.payload", right_bytes), "",
    )
    result = replace(row, row_digest=digest("c4.g4.response", row))
    logger.debug("_response_row exit status=%s", status.value)
    return result


def _derived_blocks(nodes: tuple[str, ...], rows: list[G4ResponseRow], observer_ids: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Generate equality only when every demanded response is positive echo."""
    logger.debug("_derived_blocks entry nodes=%d", len(nodes))
    parent = {x: x for x in nodes}

    def root(value: str) -> str:
        logger.debug("root entry")
        while parent[value] != value:
            value = parent[value]
        logger.debug("root exit")
        return value

    grouped = {(left, right): [] for left, right in combinations(nodes, 2)}
    for row in rows:
        grouped[(row.left_node, row.right_node)].append(row)
    for pair, pair_rows in grouped.items():
        complete = len(pair_rows) == len(observer_ids)
        if not complete:
            logger.error("_derived_blocks incomplete pair=%r", pair)
            raise RuntimeError("incomplete G4 response pair")
        if all(x.outcome == "echo" for x in pair_rows):
            left, right = root(pair[0]), root(pair[1])
            parent[right] = left
        elif any(x.outcome not in {"echo", "blocked", "split"} for x in pair_rows):
            logger.error("_derived_blocks unknown outcome pair=%r", pair)
            raise RuntimeError("unknown G4 response outcome")
    blocks: list[tuple[str, ...]] = []
    for node in nodes:
        key = root(node)
        existing = next((i for i, block in enumerate(blocks) if root(block[0]) == key), None)
        if existing is None:
            blocks.append((node,))
        else:
            blocks[existing] += (node,)
    result = tuple(blocks)
    logger.debug("_derived_blocks exit blocks=%d", len(result))
    return result


def _positive_contradictions(atlas, sections, rows: list[G4ResponseRow]) -> tuple[G4ContradictionRow, ...]:
    """Refute only when positive echo closure crosses an actual positive split."""
    logger.debug("_positive_contradictions entry rows=%d", len(rows))
    closure = generated_echo_closure(atlas, sections)
    seen: set[tuple[str, str, str]] = set()
    result: list[G4ContradictionRow] = []
    for row in rows:
        pair = (row.left_node, row.right_node) if row.left_node <= row.right_node else (row.right_node, row.left_node)
        key = (row.patch_id, *pair)
        if row.outcome == "split" and pair in closure and key not in seen:
            seen.add(key)
            result.append(G4ContradictionRow(
                row.patch_id, pair[0], pair[1],
                digest("c4.g4.contradiction", row.patch_id, pair[0], pair[1]),
            ))
    frozen = tuple(result)
    logger.debug("_positive_contradictions exit rows=%d", len(frozen))
    return frozen
