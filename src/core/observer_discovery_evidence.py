"""Shared canonical evidence roots for discovery and later confirmation."""

from __future__ import annotations

import logging

from .observer_discovery_types import DiscoveryConfig, DiscoveryDigests, DiscoveryRow, DiscoverySplit
from .observer_discovery_validation import (
    discovery_grammar_data,
    discovery_grammar_receipt,
    discovery_policy_data,
    discovery_policy_receipt,
)
from .observer_synthesis import canonical_term
from .observer_synthesis_protocol import callable_identity
from .observer_synthesis_types import Canonical, NamedBaseline, ObserverGrammar, ObserverTerm
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)


def discovery_rows_digest(rows: tuple[DiscoveryRow, ...], domain: str) -> str:
    """Digest ordered canonical rows under the caller-supplied fixed domain."""
    logger.debug("discovery_rows_digest entry rows=%d", len(rows))
    result = digest_data([discovery_row_data(row) for row in rows], domain)
    logger.debug("discovery_rows_digest exit digest=%s", result[:12])
    return result


def discovery_row_data(row: DiscoveryRow) -> dict[str, object]:
    """Return the canonical tagged representation of one row."""
    logger.debug("discovery_row_data entry")
    result = {
        "row_id": row.row_id,
        "source_id": row.source_id,
        "content_id": row.content_id,
        "group_id": row.group_id,
        "features": discovery_canonical_data(row.features),
        "target": discovery_canonical_data(row.target),
    }
    logger.debug("discovery_row_data exit")
    return result


def discovery_canonical_data(value: Canonical) -> object:
    """Encode one already-validated canonical categorical value."""
    logger.debug("discovery_canonical_data entry type=%s", type(value).__name__)
    if value is None:
        result: object = {"type": "none"}
    elif type(value) is bool:
        result = {"type": "bool", "value": value}
    elif type(value) is int:
        result = {"type": "int", "value": value}
    elif type(value) is float:
        result = {"type": "float", "value": value.hex()}
    elif type(value) is str:
        result = {"type": "str", "value": value}
    elif type(value) is tuple:
        result = {"type": "tuple", "value": [discovery_canonical_data(item) for item in value]}
    else:
        logger.error("discovery_canonical_data invalid type=%s", type(value).__name__)
        raise TypeError(f"noncanonical:{type(value).__name__}")
    logger.debug("discovery_canonical_data exit type=%s", type(value).__name__)
    return result


def discovery_protocol_material_digest(
    grammar: ObserverGrammar,
    baselines: tuple[NamedBaseline, ...],
) -> str:
    """Bind grammar, callable implementations, and exact named baselines."""
    logger.debug("discovery_protocol_material_digest entry grammar=%s", grammar.grammar_id)
    result = digest_data(
        {
            "grammar_id": grammar.grammar_id,
            "input_kind": grammar.input_kind,
            "accepted_output_kinds": list(grammar.accepted_output_kinds),
            "max_depth": grammar.max_depth,
            "max_cost": grammar.max_cost,
            "primitives": [
                {
                    "name": item.name,
                    "input_kind": item.input_kind,
                    "output_kind": item.output_kind,
                    "cost": item.cost,
                    "callable": callable_identity(item.evaluator, item.semantic_id),
                }
                for item in grammar.primitives
            ],
            "baselines": [
                {
                    "name": row.name,
                    "class": row.observer_class,
                    "term": canonical_term(row.term),
                    "boundary": row.boundary,
                }
                for row in baselines
            ],
        },
        "veyra.observer-discovery.protocol-material.v1",
    )
    logger.debug("discovery_protocol_material_digest exit digest=%s", result[:12])
    return result


def discovery_input_digests(
    grammar: ObserverGrammar,
    split: DiscoverySplit,
    baselines: tuple[NamedBaseline, ...],
    config: DiscoveryConfig,
    catalog: tuple[ObserverTerm, ...],
) -> DiscoveryDigests:
    """Reproduce v1 input roots byte-for-byte without evaluating observers."""
    logger.debug("discovery_input_digests entry")
    material = discovery_protocol_material_digest(grammar, baselines)
    policy = digest_data(
        discovery_policy_data(discovery_policy_receipt(config)),
        "veyra.observer-discovery.policy.v1",
    )
    grammar_digest = digest_data(
        discovery_grammar_data(discovery_grammar_receipt(grammar)),
        "veyra.observer-discovery.grammar.v1",
    )
    protocol = digest_data(
        {"protocol_material": material, "policy": policy, "grammar": grammar_digest},
        "veyra.observer-discovery.protocol.v1",
    )
    result = DiscoveryDigests(
        protocol,
        material,
        policy,
        grammar_digest,
        discovery_rows_digest(split.train, "veyra.observer-discovery.train-data.v1"),
        "",
        discovery_rows_digest(split.holdout, "veyra.observer-discovery.holdout-data.v1"),
        digest_data([canonical_term(term) for term in catalog], "veyra.observer-discovery.catalog.v1"),
        "",
    )
    logger.debug("discovery_input_digests exit protocol=%s", protocol[:12])
    return result
