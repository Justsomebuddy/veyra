"""Construction-safe catalog enumeration and immutable discovery snapshots."""
from __future__ import annotations

import logging
from math import isfinite

from .observer_discovery_types import DiscoveryConfig, DiscoveryRow, DiscoverySplit
from .observer_synthesis import canonical_term, observer_term_cost
from .observer_synthesis_types import (
    Canonical,
    NamedBaseline,
    ObserverGrammar,
    ObserverPrimitive,
    ObserverTerm,
)

logger = logging.getLogger(__name__)

_MAX_CONSTRUCTED_TERMS = 8192
_MAX_ROWS_PER_SPLIT = 8192
_MAX_PRIMITIVES = 12
_MAX_BASELINES = 4096
_MAX_CANONICAL_NODES_PER_VALUE = 4096
_MAX_CANONICAL_NODES_TOTAL = 1_000_000
_MAX_CANONICAL_BYTES_TOTAL = 1_000_000
_MAX_CANONICAL_DEPTH = 16
_MAX_TERM_OCCURRENCES_PER_TERM = 4096
_MAX_TERM_OCCURRENCES_TOTAL = 65_536
_MAX_TERM_DEPTH = 16
_MAX_STRING_BYTES = 4096
_MAX_INTEGER_BITS = _MAX_STRING_BYTES * 8
_MAX_TERM_TEXT_BYTES_TOTAL = 1_000_000


class DiscoveryProtocolError(ValueError):
    """Stable pre-evaluation protocol or construction-budget rejection."""

    def __init__(self, reason: str, detail: str) -> None:
        logger.error("DiscoveryProtocolError entry reason=%s", reason)
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}:{detail}")
        logger.debug("DiscoveryProtocolError exit reason=%s", reason)


def snapshot_discovery_inputs(
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
) -> tuple[ObserverGrammar, DiscoverySplit, tuple[NamedBaseline, ...], DiscoveryConfig]:
    """Detach validated caller-owned records before any evaluator callback."""
    logger.debug("snapshot_discovery_inputs entry")
    if type(grammar) is not ObserverGrammar:
        raise DiscoveryProtocolError("invalid-grammar", "immutable-record-required")
    if type(split) is not DiscoverySplit:
        raise DiscoveryProtocolError("invalid-data", "immutable-split-required")
    if type(config) is not DiscoveryConfig:
        raise DiscoveryProtocolError("invalid-config", "immutable-record-required")
    primitive_refs = grammar.primitives
    accepted_kinds = grammar.accepted_output_kinds
    train_refs = split.train
    holdout_refs = split.holdout
    if (
        type(primitive_refs) is not tuple
        or len(primitive_refs) > _MAX_PRIMITIVES
        or any(type(item) is not ObserverPrimitive for item in primitive_refs)
    ):
        raise DiscoveryProtocolError("resource-limit", "snapshot-primitives")
    if type(accepted_kinds) is not tuple or len(accepted_kinds) > _MAX_BASELINES:
        raise DiscoveryProtocolError("resource-limit", "snapshot-output-kinds")
    if (
        type(train_refs) is not tuple
        or type(holdout_refs) is not tuple
        or len(train_refs) > _MAX_ROWS_PER_SPLIT
        or len(holdout_refs) > _MAX_ROWS_PER_SPLIT
        or any(type(row) is not DiscoveryRow for row in (*train_refs, *holdout_refs))
    ):
        raise DiscoveryProtocolError("resource-limit", "snapshot-rows")
    if (
        type(baselines) is not tuple
        or len(baselines) > _MAX_BASELINES
        or any(type(row) is not NamedBaseline for row in baselines)
    ):
        logger.error("snapshot_discovery_inputs invalid baselines")
        raise DiscoveryProtocolError("invalid-baseline", "immutable-records-required")
    canonical_budget = [0, 0]
    term_budget = [0, 0]
    grammar_copy = ObserverGrammar(
        grammar.grammar_id,
        grammar.input_kind,
        tuple(accepted_kinds),
        tuple(_primitive_copy(item) for item in primitive_refs),
        grammar.max_depth,
        grammar.max_cost,
    )
    split_copy = DiscoverySplit(
        tuple(_row_copy(row, canonical_budget) for row in train_refs),
        tuple(_row_copy(row, canonical_budget) for row in holdout_refs),
    )
    baseline_copy = tuple(
        NamedBaseline(
            row.name, row.observer_class, _term_copy(row.term, term_budget), row.boundary,
        )
        for row in baselines
    )
    config_copy = DiscoveryConfig(
        config.complexity_cost_per_unit,
        config.minimum_train_objective,
        config.minimum_holdout_information_bits,
        config.significance_alpha,
        config.permutation_count,
        config.bootstrap_replicates,
        config.minimum_stability,
        config.determinism_checks,
        config.max_catalog_size,
        config.random_seed,
    )
    result = (grammar_copy, split_copy, baseline_copy, config_copy)
    logger.debug("snapshot_discovery_inputs exit")
    return result


def enumerate_observer_terms_bounded(
    grammar: ObserverGrammar,
    accepted_limit: int,
) -> tuple[ObserverTerm, ...]:
    """Stream R5 closure proposals and stop before a construction overflow."""
    logger.debug("enumerate_observer_terms_bounded entry grammar=%s", grammar.grammar_id)
    registry = {item.name: item for item in grammar.primitives}
    seed = ObserverTerm("input", grammar.input_kind)
    known = {canonical_term(seed): seed}
    construction_limit = min(_MAX_CONSTRUCTED_TERMS, max(64, accepted_limit * 4))
    changed = True
    while changed:
        changed = False
        current = tuple(sorted(known.values(), key=canonical_term))
        for child in current:
            for primitive in registry.values():
                if primitive.input_kind == child.output_kind:
                    proposal = ObserverTerm(
                        "apply", primitive.output_kind, primitive.name, (child,),
                    )
                    changed |= _retain(proposal, known, registry, grammar, construction_limit)
        for left_index, left in enumerate(current):
            for right in current[left_index:]:
                proposal = ObserverTerm("pair", "pair", children=(left, right))
                changed |= _retain(proposal, known, registry, grammar, construction_limit)
    accepted = tuple(
        term for term in known.values()
        if term.output_kind in grammar.accepted_output_kinds
    )
    if len(accepted) > accepted_limit:
        logger.error("enumerate_observer_terms_bounded accepted cutoff count=%d", len(accepted))
        raise DiscoveryProtocolError("catalog-cutoff", "accepted-catalog-limit")
    result = tuple(sorted(
        accepted,
        key=lambda term: (
            observer_term_cost(term, registry),
            _term_depth(term),
            canonical_term(term),
        ),
    ))
    logger.debug("enumerate_observer_terms_bounded exit count=%d", len(result))
    return result


def _retain(
    term: ObserverTerm,
    known: dict[str, ObserverTerm],
    registry: dict[str, ObserverPrimitive],
    grammar: ObserverGrammar,
    construction_limit: int,
) -> bool:
    logger.debug("_retain entry op=%s", term.op)
    try:
        cost = observer_term_cost(term, registry)
    except ValueError:
        logger.debug("_retain exit retained=False reason=invalid")
        return False
    if cost > grammar.max_cost or _term_depth(term) > grammar.max_depth:
        logger.debug("_retain exit retained=False reason=budget")
        return False
    key = canonical_term(term)
    if key in known:
        logger.debug("_retain exit retained=False reason=known")
        return False
    if len(known) >= construction_limit:
        logger.error("_retain construction cutoff count=%d", len(known))
        raise DiscoveryProtocolError("catalog-cutoff", "construction-term-limit")
    known[key] = term
    logger.debug("_retain exit retained=True")
    return True


def _row_copy(row: DiscoveryRow, total_budget: list[int]) -> DiscoveryRow:
    logger.debug("_row_copy entry")
    result = DiscoveryRow(
        row.row_id,
        row.source_id,
        row.content_id,
        row.group_id,
        _canonical_copy(row.features, total_budget, [0], 0),
        row.target,
    )
    logger.debug("_row_copy exit")
    return result


def _primitive_copy(item: ObserverPrimitive) -> ObserverPrimitive:
    logger.debug("_primitive_copy entry name=%s", item.name)
    result = ObserverPrimitive(
        item.name, item.input_kind, item.output_kind, item.cost,
        item.evaluator, item.semantic_id,
    )
    logger.debug("_primitive_copy exit name=%s", item.name)
    return result


def _term_copy(
    term: ObserverTerm,
    total_budget: list[int],
    local_budget: list[int] | None = None,
    active: set[int] | None = None,
    depth: int = 0,
) -> ObserverTerm:
    logger.debug("_term_copy entry type=%s", type(term).__name__)
    local_budget = [0] if local_budget is None else local_budget
    active = set() if active is None else active
    if type(term) is not ObserverTerm:
        raise DiscoveryProtocolError("invalid-baseline", "term-record")
    fields = (term.op, term.output_kind, term.primitive)
    if any(type(value) is not str for value in fields):
        raise DiscoveryProtocolError("invalid-baseline", "term-text")
    if any(len(value) > _MAX_STRING_BYTES for value in fields):
        raise DiscoveryProtocolError("resource-limit", "snapshot-term-text")
    term_text_bytes = sum(len(value.encode("utf-8")) for value in fields)
    identity = id(term)
    if identity in active:
        raise DiscoveryProtocolError("invalid-baseline", "cyclic-term")
    local_budget[0] += 1
    total_budget[0] += 1
    total_budget[1] += term_text_bytes
    if (
        depth > _MAX_TERM_DEPTH
        or local_budget[0] > _MAX_TERM_OCCURRENCES_PER_TERM
        or total_budget[0] > _MAX_TERM_OCCURRENCES_TOTAL
        or total_budget[1] > _MAX_TERM_TEXT_BYTES_TOTAL
    ):
        raise DiscoveryProtocolError("resource-limit", "snapshot-term-shape")
    if type(term.children) is not tuple:
        raise DiscoveryProtocolError("invalid-baseline", "term-children")
    active.add(identity)
    result = ObserverTerm(
        term.op,
        term.output_kind,
        term.primitive,
        tuple(
            _term_copy(child, total_budget, local_budget, active, depth + 1)
            for child in term.children
        ),
    )
    active.remove(identity)
    logger.debug("_term_copy exit op=%s", term.op)
    return result


def _canonical_copy(
    value: Canonical,
    total_budget: list[int],
    local_budget: list[int],
    depth: int,
) -> Canonical:
    logger.debug("_canonical_copy entry type=%s", type(value).__name__)
    local_budget[0] += 1
    total_budget[0] += 1
    if (
        depth > _MAX_CANONICAL_DEPTH
        or local_budget[0] > _MAX_CANONICAL_NODES_PER_VALUE
        or total_budget[0] > _MAX_CANONICAL_NODES_TOTAL
    ):
        raise DiscoveryProtocolError("resource-limit", "snapshot-canonical-shape")
    if type(value) is tuple:
        result = tuple(
            _canonical_copy(item, total_budget, local_budget, depth + 1)
            for item in value
        )
    elif value is None or type(value) is bool:
        result = value
    elif type(value) is int:
        bits = value.bit_length()
        total_budget[1] += max(1, (bits + 7) // 8)
        if bits > _MAX_INTEGER_BITS or total_budget[1] > _MAX_CANONICAL_BYTES_TOTAL:
            raise DiscoveryProtocolError("resource-limit", "snapshot-canonical-integer")
        result = value
    elif type(value) is float and isfinite(value):
        result = value
    elif type(value) is str and len(value) <= _MAX_STRING_BYTES:
        encoded_size = len(value.encode("utf-8"))
        total_budget[1] += encoded_size
        if encoded_size > _MAX_STRING_BYTES or total_budget[1] > _MAX_CANONICAL_BYTES_TOTAL:
            raise DiscoveryProtocolError("resource-limit", "snapshot-canonical-bytes")
        result = value
    else:
        raise DiscoveryProtocolError("invalid-data", "noncanonical-feature")
    logger.debug("_canonical_copy exit type=%s", type(value).__name__)
    return result


def _term_depth(term: ObserverTerm) -> int:
    logger.debug("_term_depth entry op=%s", term.op)
    result = 0 if not term.children else 1 + max(_term_depth(child) for child in term.children)
    logger.debug("_term_depth exit depth=%d", result)
    return result
