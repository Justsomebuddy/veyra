"""Derived counterpressure model and real bounded carry systems for P3-C1."""

from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NonterminatingCountermodel:
    edges: tuple[tuple[str, str], ...]
    local_peaks_joinable: bool
    distinct_normal_forms: tuple[str, str]
    globally_confluent: bool
    countermodel_digest: str


@dataclass(frozen=True)
class CarryNormalizationProbeRow:
    prime_base: int
    precision: int
    raw_digits: tuple[int, ...]
    normalized_digits: tuple[int, ...]
    state_count: int
    edge_count: int
    generated_peak_count: int
    value_preserved: bool
    status: str
    scope: str = "experiment-only-no-general-rule-source"


def local_nonterminating_countermodel() -> NonterminatingCountermodel:
    """Compute local/global properties of exact a↔b rules, never hardcode them."""
    from .common import digest

    logger.debug("local_nonterminating_countermodel entry")
    edges = (("a", "b"), ("a", "c"), ("b", "a"), ("b", "d"))
    nodes = tuple(sorted({item for edge in edges for item in edge}))
    reaches = {node: _reachable(node, edges) for node in nodes}
    outgoing = {node: tuple(target for source, target in edges if source == node) for node in nodes}
    local = all(
        bool(reaches[left] & reaches[right])
        for node in nodes
        for index, left in enumerate(outgoing[node])
        for jndex, right in enumerate(outgoing[node])
        if index != jndex
    )
    normal = tuple(node for node in nodes if not outgoing[node])
    global_ = all(
        bool(reaches[left] & reaches[right]) for node in nodes for left in reaches[node] for right in reaches[node]
    )
    model_digest = digest(
        "veyra.p3c1.nonterminating.v2", tuple(("edge", f"{source}->{target}".encode()) for source, target in edges)
    )
    result = NonterminatingCountermodel(edges, local, normal, global_, model_digest)
    logger.debug("local_nonterminating_countermodel exit local=%s global=%s", local, global_)
    return result


def _reachable(start: str, edges: tuple[tuple[str, str], ...]) -> set[str]:
    logger.debug("_reachable entry start=%s", start)
    seen = {start}
    frontier = [start]
    while frontier:
        source = frontier.pop(0)
        for left, target in edges:
            if left == source and target not in seen:
                seen.add(target)
                frontier.append(target)
    logger.debug("_reachable exit start=%s states=%d", start, len(seen))
    return seen


def carry_normalization_probe() -> tuple[CarryNormalizationProbeRow, ...]:
    """Build six real ranked carry systems and check their generated peaks."""
    logger.debug("carry_normalization_probe entry")
    result = tuple(_carry_probe(prime, precision) for prime in (2, 3) for precision in (1, 2, 3))
    logger.debug("carry_normalization_probe exit rows=%d", len(result))
    return result


def _carry_probe(prime: int, precision: int) -> CarryNormalizationProbeRow:
    from .runtime import generated_finite_confluence, local_join_cell
    from .paths import branch_targets, generated_local_peaks, generated_reachable
    from .source import continuation_edge, continuation_state, ranked_continuation_system
    from .types import GeneratedConfluenceStatus, StateRank

    logger.debug("_carry_probe entry p=%d precision=%d", prime, precision)
    raw = tuple(prime for _ in range(precision + 1)) + (0,)
    state_digits, transitions = _carry_closure(prime, raw)
    states = tuple(continuation_state(_digits_id(row), "carry-digits", bytes(row)) for row in state_digits)
    edges = tuple(
        continuation_edge(
            f"carry:{_digits_id(source)}:{index}",
            _digits_id(source),
            _digits_id(target),
            f"carry-position-{index}",
            bytes((prime, index)),
        )
        for source, index, target in transitions
    )
    ranks = tuple(StateRank(_digits_id(row), sum(row)) for row in state_digits)
    system = ranked_continuation_system(
        "p3c1-carry-experiment",
        f"carry-p{prime}-n{precision}",
        "v1",
        states,
        edges,
        (_digits_id(raw),),
        ranks,
    )
    reachable, _ = generated_reachable(system)
    peaks = generated_local_peaks(system)
    edge_paths = _normalization_paths(system)
    cells = []
    for peak in peaks:
        left_start, right_start = branch_targets(system, peak)
        left_path, left_normal = edge_paths[left_start]
        right_path, right_normal = edge_paths[right_start]
        join = left_normal if left_normal == right_normal else left_normal
        cells.append(local_join_cell(system, peak.peak_id, left_path, right_path, join))
    confluence = generated_finite_confluence(system, tuple(cells))
    normal = edge_paths[_digits_id(raw)][1]
    normal_digits = next(row for row in state_digits if _digits_id(row) == normal)
    preserved = all(_digit_value(source, prime) == _digit_value(target, prime) for source, _, target in transitions)
    preserved = preserved and _digit_value(raw, prime) == _digit_value(normal_digits, prime)
    established = confluence.status is GeneratedConfluenceStatus.GENERATED_FINITE_CONFLUENT_RELATIVE_TO_SYSTEM
    result = CarryNormalizationProbeRow(
        prime,
        precision,
        raw,
        normal_digits,
        len(states),
        len(edges),
        len(peaks),
        preserved,
        "generated-ranked-confluent" if established else confluence.status.value,
    )
    logger.debug("_carry_probe exit p=%d precision=%d peaks=%d", prime, precision, len(peaks))
    return result


def _carry_closure(
    prime: int, raw: tuple[int, ...]
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, ...], int, tuple[int, ...]], ...]]:
    logger.debug("_carry_closure entry p=%d digits=%d", prime, len(raw))
    seen = {raw}
    frontier = [raw]
    transitions = []
    while frontier:
        source = frontier.pop(0)
        for index in range(len(source) - 1):
            if source[index] < prime:
                continue
            target = list(source)
            target[index] -= prime
            target[index + 1] += 1
            frozen = tuple(target)
            transitions.append((source, index, frozen))
            if frozen not in seen:
                seen.add(frozen)
                frontier.append(frozen)
    result = tuple(sorted(seen)), tuple(sorted(transitions, key=lambda row: (_digits_id(row[0]), row[1])))
    logger.debug("_carry_closure exit states=%d edges=%d", len(result[0]), len(result[1]))
    return result


def _normalization_paths(system) -> dict[str, tuple[tuple[str, ...], str]]:
    logger.debug("_normalization_paths entry")
    outgoing = {state.state_id: [] for state in system.states}
    for edge in system.edges:
        outgoing[edge.source_id].append(edge)
    result = {}
    for state_id in outgoing:
        current = state_id
        path = []
        while outgoing[current]:
            edge = sorted(outgoing[current], key=lambda row: row.edge_id)[0]
            path.append(edge.edge_id)
            current = edge.target_id
        result[state_id] = (tuple(path), current)
    logger.debug("_normalization_paths exit states=%d", len(result))
    return result


def _digits_id(digits: tuple[int, ...]) -> str:
    logger.debug("_digits_id entry digits=%d", len(digits))
    result = "d-" + "-".join(str(item) for item in digits)
    logger.debug("_digits_id exit")
    return result


def _digit_value(digits: tuple[int, ...], prime: int) -> int:
    logger.debug("_digit_value entry digits=%d p=%d", len(digits), prime)
    result = sum(digit * prime**index for index, digit in enumerate(digits))
    logger.debug("_digit_value exit value=%d", result)
    return result
