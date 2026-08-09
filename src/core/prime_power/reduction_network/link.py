"""Exact semantic consumption of the arithmetic-specific P3-T judgment."""

from __future__ import annotations

import logging

from ...observer.network.p1_replay import replay_raw_pair
from ...observer.network.types import (
    LawStatus, RefinementStatus, ResponseStatus, TriangleStatus,
)
from ...observer.relations.types import MorphismEvidenceStatus, ProposalStatus
from .common import digest, reject
from .types import FiniteRelation

logger = logging.getLogger(__name__)


def _coordinate_maps(package):
    """Bind each P1 response token to its exact arithmetic residue."""
    logger.debug("_coordinate_maps entry")
    source = package.finite.p3t_raw_source
    if tuple(x.input_id for x in source.inputs) != tuple(
            f"family-{i}" for i in range(len(package.finite.families))):
        reject("arithmetic-p3t-input-order-not-family-scope")
    result = {}
    for observer, node in zip(source.observers, package.finite.depths, strict=True):
        if observer.observer_id != f"rho-depth-{node.depth}":
            reject("arithmetic-p3t-rho-observer-id-mismatch")
        coordinates = tuple(next(x.residue for x in family.coordinates if x.depth == node.depth)
                            for family in package.finite.families)
        tokens = []
        token_to_residue = {}
        for row, residue in zip(observer.rows, coordinates, strict=True):
            if row.response.status is not ResponseStatus.READY:
                reject("arithmetic-p3t-rho-not-total")
            token = row.response.value.value_digest
            if token in token_to_residue and token_to_residue[token] != residue:
                reject("arithmetic-p3t-token-residue-not-functional")
            token_to_residue[token] = residue
            tokens.append(token)
        if any((tokens[i] == tokens[j]) != (coordinates[i] == coordinates[j])
               for i in range(len(tokens)) for j in range(len(tokens))):
            reject("arithmetic-p3t-equality-partition-not-residue")
        result[node.depth] = (tuple(tokens), token_to_residue)
    logger.debug("_coordinate_maps exit observers=%d", len(result))
    return result


def consume_arithmetic_p3t(package, p3t, finite_arrows) -> str:
    """Require P3-T identities, edges, paths, witnesses, and maps to equal N2-F."""
    logger.debug("consume_arithmetic_p3t entry")
    source = package.finite.p3t_raw_source
    if p3t.source_digest != source.network_digest or p3t.promotions != 0:
        reject("arithmetic-p3t-judgment-source-or-promotion-mismatch")
    coordinates = _coordinate_maps(package)
    identities = {x.source_observer_id: x for x in p3t.identities}
    self_pairs = {(x.source_observer_id, x.target_observer_id): x for x in p3t.observer_pairs}
    for node in package.finite.depths:
        observer_id = f"rho-depth-{node.depth}"
        identity = identities.get(observer_id)
        tokens = coordinates[node.depth][0]
        if (identity is None or set(identity.domain) != set(tokens)
                or any(a != b for a, b in identity.rows)
                or self_pairs[(observer_id, observer_id)].status is not RefinementStatus.ISOMORPHIC):
            reject("arithmetic-p3t-identity-not-n2-identity")
    edge_results = {x.edge_id: x for x in p3t.edges}
    source_edges = {x.edge_id: x for x in source.translations}
    arrow_results = {(x.fine_depth, x.coarse_depth): x for x in finite_arrows}
    consumed = []
    for finite in package.finite.arrows:
        if finite.fine_depth == finite.coarse_depth:
            continue
        edge_id = f"reduce-{finite.fine_depth}-to-{finite.coarse_depth}"
        edge, raw_edge = edge_results.get(edge_id), source_edges.get(edge_id)
        n2 = arrow_results[(finite.fine_depth, finite.coarse_depth)]
        if edge is None or raw_edge is None:
            reject("arithmetic-p3t-reduction-edge-missing")
        fine_tokens, fine_residues = coordinates[finite.fine_depth]
        coarse_tokens, coarse_residues = coordinates[finite.coarse_depth]
        table = dict(edge.operational_map.rows)
        if set(edge.operational_map.domain) != set(fine_tokens):
            reject("arithmetic-p3t-domain-not-full-ready-image")
        target_modulus = package.prime.p ** (finite.coarse_depth + 1)
        for source_token, target_token in zip(fine_tokens, coarse_tokens, strict=True):
            if (table.get(source_token) != target_token
                    or coarse_residues[target_token] != fine_residues[source_token] % target_modulus):
                reject("arithmetic-p3t-map-not-reduction")
        if any(status is not LawStatus.ESTABLISHED for status in (
                edge.translatable, edge.relation_preserving,
                edge.translation_preserving, edge.equal_evaluation_domain)):
            reject("arithmetic-p3t-edge-law-not-established")
        raw_pair = replay_raw_pair(source, raw_edge.source_observer_id, raw_edge.target_observer_id)
        if (raw_pair.forward.morphism_status is not MorphismEvidenceStatus.P1A_ESTABLISHED
                or raw_pair.forward.proposal_status is not ProposalStatus.COMMUTES_ON_SCOPE):
            reject("arithmetic-p3t-p1a-projection-not-established")
        if n2.relation is FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE:
            if edge.refinement is not RefinementStatus.STRICT or edge.separator_input_ids is None:
                reject("arithmetic-p3t-strictness-not-linked")
            indices = tuple(int(value.removeprefix("family-")) for value in edge.separator_input_ids)
            actual = {package.finite.families[i].family_id for i in indices}
            if actual != set(n2.separator_family_ids):
                reject("arithmetic-p3t-separator-not-n2-separator")
        consumed.append(edge.judgment_digest)
    if any(x.left_status is not LawStatus.ESTABLISHED or x.right_status is not LawStatus.ESTABLISHED
           for x in p3t.identity_laws):
        reject("arithmetic-p3t-edge-identity-law-failed")
    if any(x.relation_composed is not LawStatus.ESTABLISHED
           or x.translation_composed is not LawStatus.ESTABLISHED for x in p3t.compositions):
        reject("arithmetic-p3t-composition-not-linked")
    if any(x.status is not TriangleStatus.ESTABLISHED for x in p3t.triangles):
        reject("arithmetic-p3t-triangle-not-linked")
    result = digest("veyra.p3n2.p3t-consumption.v1", (
        ("source", source.network_digest.encode()), ("judgment", p3t.judgment_digest.encode()),
        *((f"edge-{i}", value.encode()) for i, value in enumerate(consumed)),
    ))
    logger.debug("consume_arithmetic_p3t exit edges=%d", len(consumed))
    return result
