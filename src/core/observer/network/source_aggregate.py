"""Hard-first aggregate constructor for one exact P3-T network source."""

from __future__ import annotations

import logging

from ..morphism import ObserverSourceBinding
from ..relations.types import RelationEvaluationSource
from ...ontology.types import ObserverDoctrine
from .common import exact_shape, exact_text, reject
from .digest import records_digest
from .preflight import hard_preflight, network_resource_policy
from .types import (
    InputSnapshot,
    ObserverNetworkSource,
    ObserverSource,
    RawObserverPairSource,
    TranslationSource,
    TriangleDemand,
)

logger = logging.getLogger(__name__)
NETWORK_VERSION = "p3-t-observer-network-v2"


def observer_network_source(
    doctrine_id: str,
    source_id: str,
    source_version: str,
    inputs: tuple[InputSnapshot, ...],
    observers: tuple[ObserverSource, ...],
    translations: tuple[TranslationSource, ...],
    triangles: tuple[TriangleDemand, ...],
    p1a_doctrine: ObserverDoctrine,
    p1a_binding: ObserverSourceBinding,
    p1a_stage_source: RelationEvaluationSource,
    raw_pairs: tuple[RawObserverPairSource, ...],
) -> ObserverNetworkSource:
    """Preflight every exact child before reading it to encode the aggregate."""
    logger.debug("observer_network_source entry")
    for label, value in (("doctrine", doctrine_id), ("source-id", source_id), ("source-version", source_version)):
        exact_text(value, label)
    groups = (inputs, observers, translations, triangles, raw_pairs)
    kinds = (InputSnapshot, ObserverSource, TranslationSource, TriangleDemand, RawObserverPairSource)
    if any(type(group) is not tuple for group in groups):
        reject("network-constructor-shape-invalid")
    for group, kind in zip(groups, kinds):
        for item in group:
            exact_shape(item, kind, "network-constructor-child")
    exact_shape(p1a_doctrine, ObserverDoctrine, "network-constructor-doctrine")
    exact_shape(p1a_binding, ObserverSourceBinding, "network-constructor-binding")
    exact_shape(p1a_stage_source, RelationEvaluationSource, "network-constructor-stage-source")
    provisional = ObserverNetworkSource(
        NETWORK_VERSION,
        doctrine_id,
        source_id,
        source_version,
        inputs,
        observers,
        translations,
        triangles,
        p1a_doctrine,
        p1a_binding,
        p1a_stage_source,
        raw_pairs,
        "0" * 64,
    )
    hard_preflight(provisional, network_resource_policy())
    identity = (
        NETWORK_VERSION,
        doctrine_id,
        source_id,
        source_version,
        p1a_doctrine.fingerprint,
        p1a_binding.membership_digest,
        p1a_stage_source.source_digest,
    )
    children = (
        tuple(item for source in inputs for item in (source.stage_commitment, source.commitment))
        + tuple(item.observer_digest for item in observers)
        + tuple(item.translation_digest for item in translations)
        + tuple(item.pair_digest for item in raw_pairs)
    )
    demands = tuple(
        records_digest("p3t-demand-v2", (item.demand_id, item.direct_edge_id, *item.indirect_edge_ids), ())
        for item in triangles
    )
    network_digest = records_digest("p3t-network-v2", identity, children + demands)
    raw = ObserverNetworkSource(
        NETWORK_VERSION,
        doctrine_id,
        source_id,
        source_version,
        inputs,
        observers,
        translations,
        triangles,
        p1a_doctrine,
        p1a_binding,
        p1a_stage_source,
        raw_pairs,
        network_digest,
    )
    from .validation import snapshot_network_source

    result = snapshot_network_source(raw)
    logger.debug("observer_network_source exit observers=%d edges=%d", len(observers), len(translations))
    return result
