"""Finite diagnostic for observer multiplicity versus provenance independence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import NoReturn

from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

MAX_PROVENANCE_NODES = 256
MAX_PROVENANCE_OBSERVERS = 64
PROVENANCE_DIAGNOSTIC_SCHEMA = "veyra.observer-provenance-diagnostic.v1"
PROVENANCE_DIAGNOSTIC_BOUNDARY = (
    "policy-relative separation in one declared finite provenance DAG; not statistical "
    "independence, source truth, complete disclosure, causality, observer-free truth, "
    "or a change to scoped agreement or objective-in semantics"
)
_HEX = frozenset("0123456789abcdef")


class ProvenanceDiagnosticError(ValueError):
    """Stable fail-closed error for malformed finite provenance declarations."""

    def __init__(self, reason: str) -> None:
        logger.error("ProvenanceDiagnosticError state=blocked reason=%s", reason)
        self.reason = reason
        super().__init__(reason)


class AgreementStatus(str, Enum):
    """Externally validated scoped-agreement status retained by the diagnostic."""

    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class IndependenceStatus(str, Enum):
    """Policy-relative ancestry-separation result."""

    ESTABLISHED = "ESTABLISHED"
    REFUTED = "REFUTED"
    OPEN = "OPEN"


class CorroborationStatus(str, Enum):
    """Public conjunction of established agreement and provenance separation."""

    ESTABLISHED = "ESTABLISHED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class ProvenanceRole(str, Enum):
    """Policy role of one declared support node."""

    SHARED_BASIS = "SHARED_BASIS"
    DECISIVE_SOURCE = "DECISIVE_SOURCE"
    DECISIVE_CONTROL = "DECISIVE_CONTROL"


@dataclass(frozen=True, slots=True)
class ProvenanceNode:
    """One declared support node whose parents point toward earlier ancestry."""

    node_digest: str
    role: ProvenanceRole
    parent_digests: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObserverSupportRoute:
    """Bind one formally distinct observer token to one support-DAG endpoint."""

    observer_digest: str
    support_node_digest: str


@dataclass(frozen=True, slots=True)
class ScopedAgreementBinding:
    """External agreement identity; this module does not validate agreement semantics."""

    observer_family_digest: str
    claim_root: str
    scope_root: str
    doctrine_root: str
    agreement_receipt_digest: str
    agreement_validator_root: str
    status: AgreementStatus
    binding_digest: str


@dataclass(frozen=True, slots=True)
class ObserverProvenanceDAG:
    """Canonical finite observer-support declaration."""

    schema_version: str
    nodes: tuple[ProvenanceNode, ...]
    routes: tuple[ObserverSupportRoute, ...]
    ancestry_complete: bool
    dag_digest: str


@dataclass(frozen=True, slots=True)
class ProvenanceIndependenceAssessment:
    """Agreement, ancestry separation, and corroboration remain separate fields."""

    schema_version: str
    multi_observer_agreement: AgreementStatus
    provenance_independence: IndependenceStatus
    independent_corroboration: CorroborationStatus
    observer_count: int
    decisive_ancestor_count: int
    observer_ancestry: tuple[tuple[str, tuple[str, ...]], ...]
    shared_decisive_digests: tuple[str, ...]
    provenance_dag_digest: str
    agreement_binding_digest: str
    assessment_digest: str
    boundary: str = PROVENANCE_DIAGNOSTIC_BOUNDARY


def build_scoped_agreement_binding(
    observer_digests: tuple[str, ...],
    claim_root: str,
    scope_root: str,
    doctrine_root: str,
    agreement_receipt_digest: str,
    agreement_validator_root: str,
    status: AgreementStatus,
) -> ScopedAgreementBinding:
    """Bind an external agreement verdict to the exact observer family and scope."""
    logger.debug("build_scoped_agreement_binding entry")
    observers = _canonical_digests(observer_digests, "agreement-observers", minimum=2)
    if type(status) is not AgreementStatus:
        _reject("agreement-status")
    values = tuple(
        _exact_digest(value, name)
        for value, name in (
            (claim_root, "claim-root"),
            (scope_root, "scope-root"),
            (doctrine_root, "doctrine-root"),
            (agreement_receipt_digest, "agreement-receipt"),
            (agreement_validator_root, "agreement-validator"),
        )
    )
    family = _observer_family_digest(observers)
    payload = {
        "observer_family_digest": family,
        "claim_root": values[0],
        "scope_root": values[1],
        "doctrine_root": values[2],
        "agreement_receipt_digest": values[3],
        "agreement_validator_root": values[4],
        "status": status.value,
    }
    result = ScopedAgreementBinding(
        family,
        values[0],
        values[1],
        values[2],
        values[3],
        values[4],
        status,
        digest_data(payload, "veyra.observer-provenance.agreement-binding.v1"),
    )
    logger.debug("build_scoped_agreement_binding exit digest=%s", result.binding_digest[:12])
    return result


def build_observer_provenance_dag(
    nodes: tuple[ProvenanceNode, ...],
    routes: tuple[ObserverSupportRoute, ...],
    *,
    ancestry_complete: bool,
) -> ObserverProvenanceDAG:
    """Canonicalize and validate one bounded acyclic support declaration."""
    logger.debug("build_observer_provenance_dag entry")
    if type(nodes) is not tuple or not 1 <= len(nodes) <= MAX_PROVENANCE_NODES:
        _reject("provenance-node-count")
    if type(routes) is not tuple or not 2 <= len(routes) <= MAX_PROVENANCE_OBSERVERS:
        _reject("provenance-observer-count")
    if type(ancestry_complete) is not bool:
        _reject("ancestry-complete")
    checked_nodes = tuple(_validate_node(node) for node in nodes)
    checked_routes = tuple(_validate_route(route) for route in routes)
    if len({node.node_digest for node in checked_nodes}) != len(checked_nodes):
        _reject("duplicate-provenance-node")
    if len({route.observer_digest for route in checked_routes}) != len(checked_routes):
        _reject("duplicate-observer-token")
    node_ids = {node.node_digest for node in checked_nodes}
    if any(parent not in node_ids for node in checked_nodes for parent in node.parent_digests):
        _reject("missing-provenance-parent")
    if any(route.support_node_digest not in node_ids for route in checked_routes):
        _reject("missing-observer-support-node")
    canonical_nodes = tuple(sorted(checked_nodes, key=lambda node: node.node_digest))
    canonical_routes = tuple(sorted(checked_routes, key=lambda route: route.observer_digest))
    _ancestry_rows(canonical_nodes, canonical_routes)
    payload = {
        "schema_version": PROVENANCE_DIAGNOSTIC_SCHEMA,
        "nodes": [
            {
                "node_digest": node.node_digest,
                "role": node.role.value,
                "parent_digests": list(node.parent_digests),
            }
            for node in canonical_nodes
        ],
        "routes": [
            {
                "observer_digest": route.observer_digest,
                "support_node_digest": route.support_node_digest,
            }
            for route in canonical_routes
        ],
        "ancestry_complete": ancestry_complete,
    }
    result = ObserverProvenanceDAG(
        PROVENANCE_DIAGNOSTIC_SCHEMA,
        canonical_nodes,
        canonical_routes,
        ancestry_complete,
        digest_data(payload, "veyra.observer-provenance-dag.v1"),
    )
    logger.debug("build_observer_provenance_dag exit digest=%s", result.dag_digest[:12])
    return result


def assess_provenance_independence(
    dag: ObserverProvenanceDAG,
    agreement: ScopedAgreementBinding,
) -> ProvenanceIndependenceAssessment:
    """Diagnose decisive-ancestry overlap without modifying agreement semantics."""
    logger.debug("assess_provenance_independence entry")
    checked = validate_observer_provenance_dag(dag)
    binding = validate_scoped_agreement_binding(agreement)
    observers = tuple(route.observer_digest for route in checked.routes)
    if binding.observer_family_digest != _observer_family_digest(observers):
        _reject("agreement-observer-family-mismatch")
    ancestry_rows = _ancestry_rows(checked.nodes, checked.routes)
    roles = {node.node_digest: node.role for node in checked.nodes}
    decisive = {
        node_id
        for node_id, role in roles.items()
        if role in {ProvenanceRole.DECISIVE_SOURCE, ProvenanceRole.DECISIVE_CONTROL}
    }
    counts: dict[str, int] = {}
    route_decisive: list[frozenset[str]] = []
    for _, ancestry in ancestry_rows:
        route_support = frozenset(decisive.intersection(ancestry))
        route_decisive.append(route_support)
        for node_id in route_support:
            counts[node_id] = counts.get(node_id, 0) + 1
    shared = tuple(sorted(node_id for node_id, count in counts.items() if count > 1))
    if shared:
        independence = IndependenceStatus.REFUTED
    elif not all(route_decisive):
        independence = IndependenceStatus.OPEN
    elif checked.ancestry_complete:
        independence = IndependenceStatus.ESTABLISHED
    else:
        independence = IndependenceStatus.OPEN
    corroboration = (
        CorroborationStatus.ESTABLISHED
        if binding.status is AgreementStatus.ESTABLISHED
        and independence is IndependenceStatus.ESTABLISHED
        else CorroborationStatus.NOT_ESTABLISHED
    )
    payload = {
        "schema_version": PROVENANCE_DIAGNOSTIC_SCHEMA,
        "multi_observer_agreement": binding.status.value,
        "provenance_independence": independence.value,
        "independent_corroboration": corroboration.value,
        "observer_count": len(checked.routes),
        "decisive_ancestor_count": len(counts),
        "observer_ancestry": [
            {"observer_digest": observer, "ancestor_digests": list(ancestry)}
            for observer, ancestry in ancestry_rows
        ],
        "shared_decisive_digests": list(shared),
        "provenance_dag_digest": checked.dag_digest,
        "agreement_binding_digest": binding.binding_digest,
        "boundary": PROVENANCE_DIAGNOSTIC_BOUNDARY,
    }
    result = ProvenanceIndependenceAssessment(
        PROVENANCE_DIAGNOSTIC_SCHEMA,
        binding.status,
        independence,
        corroboration,
        len(checked.routes),
        len(counts),
        ancestry_rows,
        shared,
        checked.dag_digest,
        binding.binding_digest,
        digest_data(payload, "veyra.observer-provenance-assessment.v1"),
    )
    logger.info(
        "assess_provenance_independence state agreement=%s independence=%s corroboration=%s",
        result.multi_observer_agreement.value,
        result.provenance_independence.value,
        result.independent_corroboration.value,
    )
    logger.debug("assess_provenance_independence exit shared=%d", len(shared))
    return result


def validate_scoped_agreement_binding(value: object) -> ScopedAgreementBinding:
    """Validate exact binding shape and digest while leaving validator trust external."""
    logger.debug("validate_scoped_agreement_binding entry type=%s", type(value).__name__)
    if type(value) is not ScopedAgreementBinding or type(value.status) is not AgreementStatus:
        _reject("agreement-binding-type")
    for field in (
        "observer_family_digest",
        "claim_root",
        "scope_root",
        "doctrine_root",
        "agreement_receipt_digest",
        "agreement_validator_root",
        "binding_digest",
    ):
        _exact_digest(getattr(value, field), field)
    payload = {
        "observer_family_digest": value.observer_family_digest,
        "claim_root": value.claim_root,
        "scope_root": value.scope_root,
        "doctrine_root": value.doctrine_root,
        "agreement_receipt_digest": value.agreement_receipt_digest,
        "agreement_validator_root": value.agreement_validator_root,
        "status": value.status.value,
    }
    if value.binding_digest != digest_data(
        payload, "veyra.observer-provenance.agreement-binding.v1"
    ):
        _reject("agreement-binding-not-fresh")
    logger.debug("validate_scoped_agreement_binding exit")
    return value


def validate_observer_provenance_dag(value: object) -> ObserverProvenanceDAG:
    """Freshly reconstruct an exact canonical provenance DAG."""
    logger.debug("validate_observer_provenance_dag entry type=%s", type(value).__name__)
    if type(value) is not ObserverProvenanceDAG:
        _reject("provenance-dag-type")
    if value.schema_version != PROVENANCE_DIAGNOSTIC_SCHEMA or not _is_digest(value.dag_digest):
        _reject("provenance-dag-shape")
    expected = build_observer_provenance_dag(
        value.nodes, value.routes, ancestry_complete=value.ancestry_complete
    )
    if value != expected:
        _reject("provenance-dag-not-fresh")
    logger.debug("validate_observer_provenance_dag exit")
    return value


def validate_provenance_independence_assessment(
    value: object,
    dag: ObserverProvenanceDAG,
    agreement: ScopedAgreementBinding,
) -> ProvenanceIndependenceAssessment:
    """Freshly replay a diagnostic assessment against its exact DAG and agreement binding."""
    logger.debug(
        "validate_provenance_independence_assessment entry type=%s", type(value).__name__
    )
    if type(value) is not ProvenanceIndependenceAssessment:
        _reject("provenance-assessment-type")
    if value.boundary != PROVENANCE_DIAGNOSTIC_BOUNDARY or not _is_digest(
        value.assessment_digest
    ):
        _reject("provenance-assessment-shape")
    expected = assess_provenance_independence(dag, agreement)
    if value != expected:
        _reject("provenance-assessment-not-fresh")
    logger.debug("validate_provenance_independence_assessment exit")
    return value


def _validate_node(value: object) -> ProvenanceNode:
    """Validate one exact, bounded provenance node."""
    logger.debug("_validate_node entry type=%s", type(value).__name__)
    if (
        type(value) is not ProvenanceNode
        or not _is_digest(value.node_digest)
        or type(value.role) is not ProvenanceRole
    ):
        _reject("provenance-node")
    if type(value.parent_digests) is not tuple or len(value.parent_digests) > MAX_PROVENANCE_NODES:
        _reject("provenance-parents")
    if any(not _is_digest(parent) for parent in value.parent_digests):
        _reject("provenance-parent")
    if tuple(sorted(set(value.parent_digests))) != value.parent_digests:
        _reject("noncanonical-provenance-parents")
    logger.debug("_validate_node exit")
    return value


def _validate_route(value: object) -> ObserverSupportRoute:
    """Validate one exact observer-to-support binding."""
    logger.debug("_validate_route entry type=%s", type(value).__name__)
    if (
        type(value) is not ObserverSupportRoute
        or not _is_digest(value.observer_digest)
        or not _is_digest(value.support_node_digest)
    ):
        _reject("observer-support-route")
    logger.debug("_validate_route exit")
    return value


def _ancestry_rows(
    nodes: tuple[ProvenanceNode, ...],
    routes: tuple[ObserverSupportRoute, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Resolve full endpoint ancestry with explicit cycle detection."""
    logger.debug("_ancestry_rows entry nodes=%d routes=%d", len(nodes), len(routes))
    by_id = {node.node_digest: node for node in nodes}
    memo: dict[str, tuple[str, ...]] = {}
    visiting: set[str] = set()

    def ancestry(node_id: str) -> tuple[str, ...]:
        logger.debug("ancestry entry node=%s", node_id[:12])
        if node_id in visiting:
            _reject("cyclic-provenance-dag")
        if node_id in memo:
            logger.debug("ancestry exit node=%s cached=True", node_id[:12])
            return memo[node_id]
        visiting.add(node_id)
        node = by_id[node_id]
        result = tuple(
            sorted(
                {node_id}.union(
                    ancestor for parent in node.parent_digests for ancestor in ancestry(parent)
                )
            )
        )
        visiting.remove(node_id)
        memo[node_id] = result
        logger.debug("ancestry exit node=%s cached=False", node_id[:12])
        return result

    result = tuple(
        (route.observer_digest, ancestry(route.support_node_digest)) for route in routes
    )
    logger.debug("_ancestry_rows exit rows=%d", len(result))
    return result


def _observer_family_digest(observer_digests: tuple[str, ...]) -> str:
    """Commit one canonical family of distinct observer tokens."""
    logger.debug("_observer_family_digest entry count=%d", len(observer_digests))
    result = digest_data(
        {"observer_digests": list(observer_digests)},
        "veyra.observer-provenance.observer-family.v1",
    )
    logger.debug("_observer_family_digest exit")
    return result


def _canonical_digests(
    values: tuple[str, ...], field: str, *, minimum: int = 0
) -> tuple[str, ...]:
    """Validate a bounded, sorted, duplicate-free digest tuple."""
    logger.debug("_canonical_digests entry field=%s", field)
    if type(values) is not tuple or not minimum <= len(values) <= MAX_PROVENANCE_NODES:
        _reject(field)
    result = tuple(_exact_digest(value, field) for value in values)
    if tuple(sorted(set(result))) != result:
        _reject(f"noncanonical-{field}")
    logger.debug("_canonical_digests exit field=%s count=%d", field, len(result))
    return result


def _exact_digest(value: object, field: str) -> str:
    """Return one lowercase SHA-256-shaped public identity or fail closed."""
    logger.debug("_exact_digest entry field=%s", field)
    if not _is_digest(value):
        _reject(field)
    assert type(value) is str
    logger.debug("_exact_digest exit field=%s", field)
    return value


def _is_digest(value: object) -> bool:
    """Accept only lowercase SHA-256-shaped public identities."""
    logger.debug("observer_provenance._is_digest entry type=%s", type(value).__name__)
    valid = type(value) is str and len(value) == 64 and all(char in _HEX for char in value)
    logger.debug("observer_provenance._is_digest exit valid=%s", valid)
    return valid


def _reject(reason: str) -> NoReturn:
    """Raise one logged stable provenance-boundary error."""
    logger.error("observer provenance rejected reason=%s", reason)
    raise ProvenanceDiagnosticError(reason)
