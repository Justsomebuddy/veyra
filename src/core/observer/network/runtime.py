"""Aggregate finite P3-T judgment from raw closed source only."""

from __future__ import annotations

import logging

from .coherence import (
    associativity_law,
    identity_law,
    observer_pair_judgments,
    strict_cycle_check,
    triangle_judgment,
)
from .common import reject
from .digest import records_digest
from .maps import identity_map
from .preflight import network_resource_policy
from .relations import (
    composition_judgment,
    edge_judgment,
    evaluation_domain_judgment,
    isomorphism_judgment,
)
from .types import ObserverNetworkJudgment, ObserverNetworkSource
from .validation import snapshot_network_source

logger = logging.getLogger(__name__)
NONCLAIMS = (
    "observer-independent-equivalence",
    "observer-independent-identity",
    "absolute-objectivity",
    "complete-observer-universe",
    "universal-response-language",
    "guaranteed-reverse-translation",
    "view-from-nowhere",
    "observer-free-truth",
    "ontic-observer-genesis",
    "physical-observer-genesis",
    "preformal-observer-genesis",
    "observer-consciousness",
    "terminal-meta-observer",
    "unbounded-path-coherence",
    "p3-c-generated-confluence",
    "church-rosser-confluence",
    "unique-normal-forms",
    "arithmetic-adapter",
    "all-depth-family",
    "productive-to-all-depth-family",
    "completed-infinity",
    "foundation-independent-infinity",
    "object-formation",
    "objecthood",
    "historical-independence",
    "physical-instantiation",
    "promotion",
    "novelty",
    "metaphysical-proof",
    "universal-refinement",
    "off-scope-refinement",
)


def observer_network_judgment(raw: ObserverNetworkSource, policy=None) -> ObserverNetworkJudgment:
    """Freshly derive identities, maps, relations, units, paths, and coherence."""
    logger.debug("observer_network_judgment entry")
    selected = network_resource_policy() if policy is None else policy
    source = snapshot_network_source(raw, selected)
    pairs, triples = _path_catalog(source, selected.max_paths)
    identities = tuple(identity_map(source, x.observer_id) for x in source.observers)
    evaluation_domains = tuple(evaluation_domain_judgment(source, x.observer_id) for x in source.observers)
    edges = tuple(edge_judgment(source, x.edge_id) for x in source.translations)
    identity_laws = tuple(identity_law(source, x.edge_id) for x in source.translations)
    isomorphisms = _isomorphisms(source, edges)
    edge_map = {x.edge_id: x for x in edges}
    compositions = tuple(composition_judgment(source, edge_map[a], edge_map[b]) for a, b in pairs)
    observer_pairs = observer_pair_judgments(source, edges, isomorphisms, selected.max_paths)
    associativity = tuple(associativity_law(source, x) for x in triples)
    triangles = tuple(triangle_judgment(source, x) for x in source.triangles)
    cycle_status, cycle = strict_cycle_check(source, edges, selected.max_paths)
    children = (
        tuple(x.map_digest for x in identities)
        + tuple(x.judgment_digest for x in evaluation_domains)
        + tuple(x.judgment_digest for x in identity_laws)
        + tuple(x.judgment_digest for x in edges)
        + tuple(x.judgment_digest for x in isomorphisms)
        + tuple(x.judgment_digest for x in observer_pairs)
        + tuple(x.judgment_digest for x in compositions)
        + tuple(x.judgment_digest for x in associativity)
        + tuple(x.judgment_digest for x in triangles)
    )
    jid = records_digest(
        "p3t-network-judgment-v2", (source.network_digest, cycle_status.value, *cycle, "0", *NONCLAIMS), children
    )
    result = ObserverNetworkJudgment(
        source.network_digest,
        identities,
        evaluation_domains,
        identity_laws,
        edges,
        isomorphisms,
        observer_pairs,
        compositions,
        associativity,
        triangles,
        cycle_status,
        cycle,
        0,
        NONCLAIMS,
        jid,
    )
    logger.debug("observer_network_judgment exit edges=%d paths=%d", len(edges), len(compositions))
    return result


def _path_catalog(
    source: ObserverNetworkSource, cap: int
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str, str], ...]]:
    """Enumerate only composable pairs/triples and stop at the hard path cap."""
    logger.debug("network path_catalog entry")
    pairs = []
    for a in source.translations:
        for b in source.translations:
            if a.target_observer_id == b.source_observer_id:
                pairs.append((a.edge_id, b.edge_id))
                if len(pairs) > cap:
                    reject("generated-path-hard-limit")
    triples = []
    for a_id, b_id in pairs:
        b = next((x for x in source.translations if x.edge_id == b_id), None)
        if b is None:
            reject("generated-path-edge-missing")
        for c in source.translations:
            if b.target_observer_id == c.source_observer_id:
                triples.append((a_id, b_id, c.edge_id))
                if len(pairs) + len(triples) + len(source.triangles) > cap:
                    reject("generated-path-hard-limit")
    result = (tuple(pairs), tuple(triples))
    logger.debug("network path_catalog exit pairs=%d triples=%d", len(pairs), len(triples))
    return result


def _isomorphisms(source: ObserverNetworkSource, edges) -> tuple:
    """Replay each exact opposite-edge pair once."""
    logger.debug("network isomorphisms entry")
    output = []
    by_id = {x.edge_id: x for x in edges}
    for forward in source.translations:
        for reverse in source.translations:
            if (
                forward.edge_id < reverse.edge_id
                and forward.source_observer_id == reverse.target_observer_id
                and forward.target_observer_id == reverse.source_observer_id
            ):
                output.append(isomorphism_judgment(source, by_id[forward.edge_id], by_id[reverse.edge_id]))
    result = tuple(output)
    logger.debug("network isomorphisms exit count=%d", len(result))
    return result
