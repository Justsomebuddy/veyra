"""Declared finite confluence aggregation for P1-C2.

One concept end to end: the closed catalog DTOs, tagged commitments and
canonical catalog bytes, zero/nonzero history construction and replay,
requirement and policy snapshots, deep catalog revalidation, atomic
whole-catalog resource accounting, the arbitrary same-endpoint global 2-cell,
the preflight-first aggregation runtime, and hostile-safe result revalidation.

The catalog is declared and finite. Nothing here claims exhaustive generated
path coverage, termination, or any unbounded confluence property; the permanent
nonclaims are enumerated in ``C2_NONCLAIMS``.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
import json
import logging
from typing import TypeAlias

from .digest import _digest, cell_trace_digest, response_row_digest, trace_digest
from .path import replay_diagram_path
from .plan import (
    _snapshot_alignment, snapshot_direct_echo_transport, snapshot_fork_join_plan,
)
from .preflight import ConfluenceValidationError
from .runtime import _outcome_name, _payload, _status, fork_confluence_judgment
from .types import (
    AlignmentPoint, ConfluenceObstruction, ConfluenceStatus, DirectEchoTransport,
    FiniteDiagramSource, ForkConfluenceJudgment, ForkJoinPlan, TransportMode,
    TransportResponseRow,
)
from .validation import (
    _hex_digest, _identifier, snapshot_confluence_doctrine,
    snapshot_finite_diagram_source,
)
from ..observer_core_codec import decode_observer
from ..observer_core_semantics import echo
from ..ontology.doctrine import stage_commitment
from ..ontology.types import ObserverDoctrine, OntologyStage

logger = logging.getLogger(__name__)

HISTORY_VERSION = "p1-c2-history-v1"
CATALOG_VERSION = "p1-c2-v1"
CATALOG_SCOPE = "declared-finite-catalog-not-generated-path-universe"
POLICY_VERSION = "p1-c2-policy-v1"
MAX_CANONICAL_BYTES = 2 * 1024 * 1024
MAX_TOTAL_CHECKS = 16_384

C2_NONCLAIMS = (
    "exhaustive-generated-path-coverage", "termination", "newman-lemma",
    "church-rosser", "unbounded-confluence", "object-formation",
    "absolute-identity", "absolute-existence", "all-depth-family",
    "completed-carrier", "novelty", "r8-promotion", "layer-promotion",
    "sage-promotion",
)


class RequirementKind(str, Enum):
    LOCAL = "local-critical-fork"
    GLOBAL = "global-declared-history-pair"


class LocalFiniteStatus(str, Enum):
    CONFLUENT = "local-finite-confluent"
    REFUTED = "refuted"
    OPEN = "open"


class GlobalDeclaredFiniteStatus(str, Enum):
    CONFLUENT = "global-declared-finite-confluent"
    REFUTED = "refuted"
    OPEN = "open"


class AggregateCoverageStatus(str, Enum):
    COMPLETE = "complete"


class AggregateResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class AggregateFailedBound(str, Enum):
    CANONICAL_BYTES = "canonical-bytes"
    TOTAL_CHECKS = "total-checks"


@dataclass(frozen=True)
class IdentityHistory:
    version: str
    history_id: str
    stage_id: str
    stage_commitment: str
    history_digest: str


@dataclass(frozen=True)
class DeclaredHistory:
    version: str
    history_id: str
    path_id: str
    path_commitment: str
    start_stage_id: str
    end_stage_id: str
    history_digest: str


HistoryRef: TypeAlias = IdentityHistory | DeclaredHistory


@dataclass(frozen=True)
class LocalCriticalForkRequirement:
    requirement_id: str
    plan: ForkJoinPlan
    transport: DirectEchoTransport
    requirement_digest: str


@dataclass(frozen=True)
class GlobalPathPairRequirement:
    requirement_id: str
    left: HistoryRef
    right: HistoryRef
    alignment: tuple[AlignmentPoint, ...]
    transport: DirectEchoTransport
    requirement_digest: str


RequirementKey: TypeAlias = tuple[RequirementKind, str, str]


@dataclass(frozen=True)
class ConfluenceAggregatePolicy:
    version: str
    max_checks: int
    max_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class FiniteConfluenceCatalogSource:
    doctrine_fingerprint: str
    diagram_digest: str
    local_requirements: tuple[LocalCriticalForkRequirement, ...]
    global_requirements: tuple[GlobalPathPairRequirement, ...]
    expected_local_keys: tuple[RequirementKey, ...]
    expected_global_keys: tuple[RequirementKey, ...]
    policy: ConfluenceAggregatePolicy
    catalog_digest: str
    version: str = "p1-c2-v1"
    scope: str = "declared-finite-catalog-not-generated-path-universe"


@dataclass(frozen=True)
class GlobalHistory2CellArtifact:
    doctrine_fingerprint: str
    diagram_digest: str
    requirement_digest: str
    left_history_digest: str
    right_history_digest: str
    left_stage_commitments: tuple[str, ...]
    right_stage_commitments: tuple[str, ...]
    alignment: tuple[AlignmentPoint, ...]
    required_observer_ids: tuple[str, ...]
    mode: TransportMode
    transport_digest: str
    response_rows: tuple[TransportResponseRow, ...]
    left_trace_digest: str
    right_trace_digest: str
    trace_digest: str
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    status: ConfluenceStatus
    artifact_digest: str
    scope: str = "global-declared-finite-history-2-cell"


@dataclass(frozen=True)
class ConfluenceRequirementRow:
    key: RequirementKey
    plan_digest: str | None
    left_history_digest: str | None
    right_history_digest: str | None
    transport_digest: str
    local_judgment_digest: str | None
    global_history_cell_digest: str | None
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    status: ConfluenceStatus
    row_digest: str


@dataclass(frozen=True)
class FiniteConfluenceAggregate:
    doctrine_fingerprint: str
    diagram_digest: str
    catalog_digest: str
    policy_digest: str
    run_digest: str
    expected_local_keys: tuple[RequirementKey, ...]
    expected_global_keys: tuple[RequirementKey, ...]
    rows: tuple[ConfluenceRequirementRow, ...]
    local_status: LocalFiniteStatus
    global_status: GlobalDeclaredFiniteStatus
    coverage: AggregateCoverageStatus
    first_obstruction: ConfluenceObstruction | None
    total_charge: int
    nonclaims: tuple[str, ...]
    aggregate_digest: str


@dataclass(frozen=True)
class ConfluenceAggregateResourceLimit:
    status: AggregateResultStatus
    doctrine_fingerprint: str
    diagram_digest: str
    catalog_digest: str
    policy_digest: str
    run_digest: str
    failed_bound: AggregateFailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


FiniteConfluenceResult: TypeAlias = (
    FiniteConfluenceAggregate | ConfluenceAggregateResourceLimit
)


@dataclass(frozen=True)
class ReplayedHistory:
    history_id: str
    history_digest: str
    edge_ids: tuple[str, ...]
    stages: tuple[OntologyStage, ...]
    stage_commitments: tuple[str, ...]


def reject(reason: str) -> None:
    """Raise the closed C2 validation error without rendering attacker data."""
    logger.error("aggregate rejected reason=%s", reason)
    raise ConfluenceValidationError(reason)


_reject = reject


def exact_instance(value: object, kind: type, field: str) -> None:
    """Require exact DTO type and exactly its declared instance-field set."""
    logger.debug("aggregate exact instance entry field=%s", field)
    if type(value) is not kind:
        reject(f"confluence-aggregate-{field}-must-be-exact")
    try:
        mapping = vars(value)
    except TypeError as exc:
        logger.error("aggregate exact instance missing dictionary field=%s", field)
        raise ConfluenceValidationError(
            f"confluence-aggregate-{field}-instance-fields"
        ) from exc
    expected = tuple(item.name for item in fields(kind))
    if type(mapping) is not dict or len(mapping) != len(expected):
        reject(f"confluence-aggregate-{field}-instance-fields")
    keys = tuple(mapping.keys())
    if any(type(item) is not str for item in keys):
        reject(f"confluence-aggregate-{field}-instance-fields")
    if tuple(sorted(keys)) != tuple(sorted(expected)):
        reject(f"confluence-aggregate-{field}-instance-fields")
    logger.debug("aggregate exact instance exit field=%s", field)


def exact_fields(
    raw: object, expected: object, schema: tuple[tuple[str, type], ...], reason: str,
) -> None:
    """Compare exact primitive/enum fields without coercive equality hooks."""
    logger.debug("aggregate exact fields entry reason=%s", reason)
    for name, kind in schema:
        try:
            supplied, wanted = getattr(raw, name), getattr(expected, name)
        except AttributeError as exc:
            logger.error("aggregate exact fields missing reason=%s", reason)
            raise ConfluenceValidationError(reason) from exc
        if type(supplied) is not kind:
            reject(reason)
        if issubclass(kind, Enum):
            if supplied is not wanted:
                reject(reason)
        elif supplied != wanted:
            reject(reason)
    logger.debug("aggregate exact fields exit reason=%s", reason)


def exact_optional_string(raw: object, expected: object, reason: str) -> None:
    """Compare an optional string without accepting subclasses or coercions."""
    logger.debug("aggregate optional string entry reason=%s", reason)
    if expected is None:
        if raw is not None:
            reject(reason)
    elif type(raw) is not str or raw != expected:
        reject(reason)
    logger.debug("aggregate optional string exit reason=%s", reason)


def tagged_digest(domain: str, *fields: tuple[str, str | bytes | int]) -> str:
    """Hash exact tagged primitive fields."""
    logger.debug("tagged_digest entry domain=%s fields=%d", domain, len(fields))
    encoded = tuple(
        (tag, value if type(value) is bytes else (
            value.to_bytes(8, "big") if type(value) is int else value.encode()
        )) for tag, value in fields
    )
    result = _digest(domain, encoded)
    logger.debug("tagged_digest exit domain=%s", domain)
    return result


def sequence_digest(domain: str, fields: tuple[tuple[str, str], ...]) -> str:
    """Hash an ordered count-framed string sequence."""
    logger.debug("sequence_digest entry domain=%s count=%d", domain, len(fields))
    packed = [("count", len(fields).to_bytes(8, "big"))]
    packed.extend((f"{tag}-{i}", value.encode()) for i, (tag, value) in enumerate(fields))
    result = _digest(domain, tuple(packed))
    logger.debug("sequence_digest exit domain=%s", domain)
    return result


def c1_judgment_digest(value: ForkConfluenceJudgment) -> str:
    """Commit the freshly derived C1 judgment without accepting it as input."""
    logger.debug("c1_judgment_digest entry")
    cell = "none" if value.transport_cell is None else value.transport_cell.trace_digest
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    result = tagged_digest(
        "veyra.p1c2.c1-judgment.v1", ("plan-id", value.plan_id),
        ("plan", value.plan_digest), ("status", value.status.value),
        ("cell", cell), ("obstruction", obstruction),
        ("charged", value.charged_checks),
    )
    logger.debug("c1_judgment_digest exit")
    return result


def response_commitment(rows: tuple[TransportResponseRow, ...]) -> str:
    """Commit every ordered response-row digest."""
    logger.debug("response_commitment entry rows=%d", len(rows))
    result = sequence_digest(
        "veyra.p1c2.responses.v1", tuple(("row", item.row_digest) for item in rows),
    )
    logger.debug("response_commitment exit")
    return result


def cell_artifact_digest(value: GlobalHistory2CellArtifact) -> str:
    """Commit one derived global-history 2-cell."""
    logger.debug("cell_artifact_digest entry")
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    result = tagged_digest(
        "veyra.p1c2.global-cell.v1", ("doctrine", value.doctrine_fingerprint),
        ("diagram", value.diagram_digest), ("requirement", value.requirement_digest),
        ("left-history", value.left_history_digest),
        ("right-history", value.right_history_digest),
        ("transport", value.transport_digest), ("trace", value.trace_digest),
        ("responses", response_commitment(value.response_rows)),
        ("obstruction", obstruction), ("charged", value.charged_checks),
        ("status", value.status.value), ("scope", value.scope),
    )
    logger.debug("cell_artifact_digest exit")
    return result


def row_digest(value: ConfluenceRequirementRow) -> str:
    """Commit one exact aggregate row."""
    logger.debug("aggregate row_digest entry")
    kind, requirement_id, requirement_digest = value.key
    obstruction = "none" if value.first_obstruction is None else tagged_digest(
        "veyra.p1c2.obstruction.v1",
        ("lane", value.first_obstruction.lane),
        ("occurrence", value.first_obstruction.occurrence),
        ("observer", value.first_obstruction.observer_id),
        ("outcome", value.first_obstruction.outcome),
    )
    fields = (
        ("kind", kind.value), ("id", requirement_id),
        ("requirement", requirement_digest), ("plan", value.plan_digest or "none"),
        ("left", value.left_history_digest or "none"),
        ("right", value.right_history_digest or "none"),
        ("transport", value.transport_digest),
        ("local", value.local_judgment_digest or "none"),
        ("global", value.global_history_cell_digest or "none"),
        ("obstruction", obstruction), ("charged", value.charged_checks),
        ("status", value.status.value),
    )
    result = tagged_digest("veyra.p1c2.requirement-row.v1", *fields)
    logger.debug("aggregate row_digest exit")
    return result


def catalog_canonical_bytes(value: FiniteConfluenceCatalogSource) -> bytes:
    """Encode every catalog payload in deterministic semantic order."""
    logger.debug("catalog_canonical_bytes entry")
    payload = {
        "version": value.version, "scope": value.scope,
        "doctrine": value.doctrine_fingerprint, "diagram": value.diagram_digest,
        "policy": _policy_json(value.policy),
        "local": [_local_json(item) for item in value.local_requirements],
        "global": [_global_json(item) for item in value.global_requirements],
    }
    result = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    logger.debug("catalog_canonical_bytes exit bytes=%d", len(result))
    return result


def _policy_json(value: ConfluenceAggregatePolicy) -> dict[str, object]:
    logger.debug("aggregate policy json entry")
    try:
        result = {"version": value.version, "max_checks": value.max_checks,
                  "max_bytes": value.max_bytes, "digest": value.policy_digest}
    except Exception:
        logger.error("aggregate policy json error")
        raise
    logger.debug("aggregate policy json exit")
    return result


def _local_json(value: LocalCriticalForkRequirement) -> dict[str, object]:
    logger.debug("aggregate local json entry")
    try:
        plan = value.plan
        result = {
            "id": value.requirement_id, "digest": value.requirement_digest,
            "plan": {
                "id": plan.plan_id, "digest": plan.plan_digest,
                "diagram": plan.diagram_digest, "fork": plan.fork_stage_commitment,
                "branches": [plan.left_branch_path_id, plan.right_branch_path_id],
                "joins": [plan.left_join_path_id, plan.right_join_path_id],
                "join": plan.join_stage_commitment,
                "alignment": [[x.left_index, x.right_index] for x in plan.alignment],
                "transport": plan.transport_digest, "version": plan.version,
                "scope": plan.scope,
            },
            "transport": _transport_json(value.transport),
        }
    except Exception:
        logger.error("aggregate local json error")
        raise
    logger.debug("aggregate local json exit")
    return result


def _history_json(value: IdentityHistory | DeclaredHistory) -> dict[str, object]:
    logger.debug("aggregate history json entry")
    try:
        if type(value) is IdentityHistory:
            result = {"kind": "identity", "version": value.version, "id": value.history_id,
                      "stage": value.stage_id, "stage_commitment": value.stage_commitment,
                      "digest": value.history_digest}
        else:
            result = {"kind": "declared", "version": value.version, "id": value.history_id,
                      "path": value.path_id, "path_commitment": value.path_commitment,
                      "start": value.start_stage_id, "end": value.end_stage_id,
                      "digest": value.history_digest}
    except Exception:
        logger.error("aggregate history json error")
        raise
    logger.debug("aggregate history json exit")
    return result


def _transport_json(value: object) -> dict[str, object]:
    logger.debug("aggregate transport json entry")
    try:
        result = {"observers": list(value.observer_ids), "mode": value.mode.value,
                  "scope": value.scope, "digest": value.transport_digest}
    except Exception:
        logger.error("aggregate transport json error")
        raise
    logger.debug("aggregate transport json exit")
    return result


def _global_json(value: GlobalPathPairRequirement) -> dict[str, object]:
    logger.debug("aggregate global json entry")
    try:
        result = {"id": value.requirement_id, "digest": value.requirement_digest,
                  "left": _history_json(value.left), "right": _history_json(value.right),
                  "alignment": [[x.left_index, x.right_index] for x in value.alignment],
                  "transport": _transport_json(value.transport)}
    except Exception:
        logger.error("aggregate global json error")
        raise
    logger.debug("aggregate global json exit")
    return result


def identity_history(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    history_id: str, stage_id: str,
) -> IdentityHistory:
    """Construct the only zero-edge history from one exact diagram stage."""
    logger.debug("identity_history entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    history_id = _identifier(history_id, "history-id")
    stage_id = _identifier(stage_id, "identity-stage-id")
    stages = {item.stage_id: item for item in diagram.stages}
    if stage_id not in stages:
        _reject("unknown-identity-stage")
    commitment = stage_commitment(stages[stage_id])
    digest = tagged_digest(
        "veyra.p1c2.identity-history.v1", ("version", HISTORY_VERSION),
        ("history-id", history_id), ("diagram", diagram.source_digest),
        ("stage-id", stage_id), ("stage", commitment),
    )
    result = IdentityHistory(HISTORY_VERSION, history_id, stage_id, commitment, digest)
    logger.debug("identity_history exit")
    return result


def declared_history(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    history_id: str, path_id: str,
) -> DeclaredHistory:
    """Construct one exact nonempty history from a declared C1 path."""
    logger.debug("declared_history entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    history_id = _identifier(history_id, "history-id")
    path_id = _identifier(path_id, "history-path-id")
    paths = {item.path_id: item for item in diagram.paths}
    commitments = dict(zip(
        (item.path_id for item in diagram.paths), diagram.path_commitments, strict=True,
    ))
    if path_id not in paths:
        _reject("unknown-history-path")
    path = paths[path_id]
    digest = tagged_digest(
        "veyra.p1c2.declared-history.v1", ("version", HISTORY_VERSION),
        ("history-id", history_id), ("diagram", diagram.source_digest),
        ("path-id", path_id), ("path", commitments[path_id]),
        ("start", path.start_stage_id), ("end", path.end_stage_id),
    )
    result = DeclaredHistory(
        HISTORY_VERSION, history_id, path_id, commitments[path_id],
        path.start_stage_id, path.end_stage_id, digest,
    )
    logger.debug("declared_history exit")
    return result


def snapshot_history(
    value: HistoryRef, doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
) -> HistoryRef:
    """Rebuild an exact closed history variant and reject relabeling."""
    logger.debug("snapshot_history entry")
    if type(value) is IdentityHistory:
        try:
            result = identity_history(doctrine, diagram, value.history_id, value.stage_id)
            supplied = (value.version, value.stage_commitment, value.history_digest)
        except AttributeError:
            _reject("identity-history-missing-fields")
        if (
            any(type(item) is not str for item in supplied)
            or supplied != (result.version, result.stage_commitment, result.history_digest)
        ):
            _reject("identity-history-drift")
    elif type(value) is DeclaredHistory:
        try:
            result = declared_history(doctrine, diagram, value.history_id, value.path_id)
            supplied = (
                value.version, value.path_commitment, value.start_stage_id,
                value.end_stage_id, value.history_digest,
            )
        except AttributeError:
            _reject("declared-history-missing-fields")
        if (
            any(type(item) is not str for item in supplied)
            or supplied != (
                result.version, result.path_commitment, result.start_stage_id,
                result.end_stage_id, result.history_digest,
            )
        ):
            _reject("declared-history-drift")
    else:
        _reject("history-ref-must-be-exact-closed-variant")
    logger.debug("snapshot_history exit kind=%s", type(result).__name__)
    return result


def replay_history(
    value: HistoryRef, doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
) -> ReplayedHistory:
    """Freshly replay an identity or a nonempty declared path."""
    logger.debug("replay_history entry")
    value = snapshot_history(value, doctrine, diagram)
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    if type(value) is IdentityHistory:
        stage = next(item for item in diagram.stages if item.stage_id == value.stage_id)
        result = ReplayedHistory(
            value.history_id, value.history_digest, (), (stage,),
            (value.stage_commitment,),
        )
    else:
        replay = replay_diagram_path(doctrine, diagram, value.path_id)
        result = ReplayedHistory(
            value.history_id, value.history_digest, replay.edge_ids,
            replay.stages, replay.stage_commitments,
        )
    logger.debug("replay_history exit edges=%d stages=%d", len(result.edge_ids), len(result.stages))
    return result


def history_digest_field(value: object, field: str) -> str:
    """Expose strict digest validation for result validators."""
    logger.debug("history_digest_field entry field=%s", field)
    result = _hex_digest(value, field)
    logger.debug("history_digest_field exit field=%s", field)
    return result


def confluence_aggregate_policy(
    max_checks: int = 4096, max_bytes: int = MAX_CANONICAL_BYTES,
) -> ConfluenceAggregatePolicy:
    """Construct the bounded operational policy independently of catalog identity."""
    logger.debug("confluence_aggregate_policy entry")
    if (
        type(max_checks) is not int or not 1 <= max_checks <= 4096
        or type(max_bytes) is not int or not 1 <= max_bytes <= MAX_CANONICAL_BYTES
    ):
        _reject("invalid-confluence-aggregate-policy")
    digest = tagged_digest(
        "veyra.p1c2.policy.v1", ("version", POLICY_VERSION),
        ("max-checks", max_checks), ("max-bytes", max_bytes),
    )
    result = ConfluenceAggregatePolicy(POLICY_VERSION, max_checks, max_bytes, digest)
    logger.debug("confluence_aggregate_policy exit")
    return result


def snapshot_policy(value: ConfluenceAggregatePolicy) -> ConfluenceAggregatePolicy:
    """Rebuild one exact policy and reject Boolean/int or digest drift."""
    logger.debug("snapshot_policy entry")
    if type(value) is not ConfluenceAggregatePolicy:
        _reject("confluence-aggregate-policy-must-be-exact")
    try:
        result = confluence_aggregate_policy(value.max_checks, value.max_bytes)
        supplied = (value.version, value.policy_digest)
    except AttributeError:
        _reject("confluence-aggregate-policy-missing-fields")
    if any(type(item) is not str for item in supplied) or supplied != (
        result.version, result.policy_digest,
    ):
        _reject("confluence-aggregate-policy-drift")
    logger.debug("snapshot_policy exit")
    return result


def local_critical_fork_requirement(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, requirement_id: str,
    plan: ForkJoinPlan, transport: DirectEchoTransport,
) -> LocalCriticalForkRequirement:
    """Bind one genuinely one-edge C1 critical fork from raw inputs."""
    logger.debug("local_critical_fork_requirement entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    transport = snapshot_direct_echo_transport(transport, doctrine)
    plan = snapshot_fork_join_plan(plan, diagram, transport, doctrine)
    requirement_id = _identifier(requirement_id, "confluence-requirement-id")
    paths = {item.path_id: item for item in diagram.paths}
    left, right = paths[plan.left_branch_path_id], paths[plan.right_branch_path_id]
    if len(left.edge_ids) != 1 or len(right.edge_ids) != 1:
        _reject("local-critical-branch-must-have-one-edge")
    if left.edge_ids[0] == right.edge_ids[0]:
        _reject("local-critical-edges-must-differ")
    if plan.left_join_path_id is None or plan.right_join_path_id is None:
        _reject("local-critical-fork-requires-nonempty-joins")
    digest = tagged_digest(
        "veyra.p1c2.local-requirement.v1", ("id", requirement_id),
        ("diagram", diagram.source_digest), ("plan", plan.plan_digest),
        ("transport", transport.transport_digest),
    )
    result = LocalCriticalForkRequirement(requirement_id, plan, transport, digest)
    logger.debug("local_critical_fork_requirement exit")
    return result


def global_path_pair_requirement(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, requirement_id: str,
    left: object, right: object, alignment: tuple[AlignmentPoint, ...],
    transport: DirectEchoTransport,
) -> GlobalPathPairRequirement:
    """Bind two distinct arbitrary same-endpoint declared histories."""
    logger.debug("global_path_pair_requirement entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    requirement_id = _identifier(requirement_id, "confluence-requirement-id")
    left = snapshot_history(left, doctrine, diagram)  # type: ignore[arg-type]
    right = snapshot_history(right, doctrine, diagram)  # type: ignore[arg-type]
    transport = snapshot_direct_echo_transport(transport, doctrine)
    left_replay = replay_history(left, doctrine, diagram)
    right_replay = replay_history(right, doctrine, diagram)
    if left.history_id == right.history_id:
        _reject("global-histories-require-distinct-ids")
    if type(left) is type(right):
        same = (
            left.stage_id == right.stage_id if hasattr(left, "stage_id")
            else left.path_id == right.path_id
        )
        if same:
            _reject("global-histories-identical-under-distinct-ids")
    if (
        left_replay.stage_commitments[0] != right_replay.stage_commitments[0]
        or left_replay.stage_commitments[-1] != right_replay.stage_commitments[-1]
    ):
        _reject("global-history-endpoint-mismatch")
    alignment = _global_alignment(
        alignment, len(left_replay.stages), len(right_replay.stages),
    )
    digest = tagged_digest(
        "veyra.p1c2.global-requirement.v1", ("id", requirement_id),
        ("diagram", diagram.source_digest), ("left", left.history_digest),
        ("right", right.history_digest),
        ("alignment", _alignment_digest(alignment)),
        ("transport", transport.transport_digest),
    )
    result = GlobalPathPairRequirement(
        requirement_id, left, right, alignment, transport, digest,
    )
    logger.debug("global_path_pair_requirement exit")
    return result


def _global_alignment(
    value: tuple[AlignmentPoint, ...], left_stages: int, right_stages: int,
) -> tuple[AlignmentPoint, ...]:
    logger.debug("global alignment entry")
    rows = _snapshot_alignment(value)
    if (
        not rows or rows[0] != AlignmentPoint(0, 0)
        or rows[-1] != AlignmentPoint(left_stages - 1, right_stages - 1)
    ):
        _reject("global-alignment-endpoint-drift")
    for previous, current in zip(rows, rows[1:]):
        delta = (
            current.left_index - previous.left_index,
            current.right_index - previous.right_index,
        )
        if delta not in {(1, 0), (0, 1), (1, 1)}:
            _reject("global-alignment-not-full-monotone")
    logger.debug("global alignment exit points=%d", len(rows))
    return rows


def _alignment_digest(value: tuple[AlignmentPoint, ...]) -> str:
    logger.debug("aggregate alignment digest entry points=%d", len(value))
    try:
        fields = tuple(("point", f"{x.left_index}:{x.right_index}") for x in value)
        result = sequence_digest("veyra.p1c2.alignment.v1", fields)
    except Exception:
        logger.error("aggregate alignment digest error")
        raise
    logger.debug("aggregate alignment digest exit")
    return result


def finite_confluence_catalog(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    local: tuple[LocalCriticalForkRequirement, ...],
    global_: tuple[GlobalPathPairRequirement, ...],
    policy: ConfluenceAggregatePolicy,
) -> FiniteConfluenceCatalogSource:
    """Build the complete immutable ordered C2 requirement catalog."""
    logger.debug("finite_confluence_catalog entry")
    doctrine = snapshot_confluence_doctrine(doctrine)
    diagram = snapshot_finite_diagram_source(diagram, doctrine)
    policy = snapshot_policy(policy)
    if type(local) is not tuple or not 1 <= len(local) <= 64:
        _reject("invalid-local-requirement-catalog")
    if type(global_) is not tuple or not 1 <= len(global_) <= 128:
        _reject("invalid-global-requirement-catalog")
    locals_ = tuple(_snapshot_local(x, doctrine, diagram) for x in local)
    globals_ = tuple(_snapshot_global(x, doctrine, diagram) for x in global_)
    ids = tuple(x.requirement_id for x in (*locals_, *globals_))
    if len(set(ids)) != len(ids):
        _reject("duplicate-cross-catalog-requirement-id")
    local_keys = tuple(
        (RequirementKind.LOCAL, x.requirement_id, x.requirement_digest) for x in locals_
    )
    global_keys = tuple(
        (RequirementKind.GLOBAL, x.requirement_id, x.requirement_digest) for x in globals_
    )
    digest = _catalog_digest(
        doctrine.fingerprint, diagram.source_digest, local_keys, global_keys, policy,
    )
    result = FiniteConfluenceCatalogSource(
        doctrine.fingerprint, diagram.source_digest, locals_, globals_,
        local_keys, global_keys, policy, digest,
    )
    if len(catalog_canonical_bytes(result)) > MAX_CANONICAL_BYTES:
        _reject("confluence-catalog-hard-byte-limit")
    logger.debug("finite_confluence_catalog exit local=%d global=%d", len(locals_), len(globals_))
    return result


def _snapshot_local(value, doctrine, diagram) -> LocalCriticalForkRequirement:
    logger.debug("aggregate snapshot local entry")
    try:
        if type(value) is not LocalCriticalForkRequirement:
            _reject("local-requirement-must-be-exact")
        result = local_critical_fork_requirement(
            doctrine, diagram, value.requirement_id, value.plan, value.transport,
        )
        if _hex_digest(value.requirement_digest, "local-requirement-digest") != result.requirement_digest:
            _reject("local-requirement-drift")
    except Exception:
        logger.error("aggregate snapshot local error")
        raise
    logger.debug("aggregate snapshot local exit")
    return result


def _snapshot_global(value, doctrine, diagram) -> GlobalPathPairRequirement:
    logger.debug("aggregate snapshot global entry")
    try:
        if type(value) is not GlobalPathPairRequirement:
            _reject("global-requirement-must-be-exact")
        result = global_path_pair_requirement(
            doctrine, diagram, value.requirement_id, value.left, value.right,
            value.alignment, value.transport,
        )
        if _hex_digest(value.requirement_digest, "global-requirement-digest") != result.requirement_digest:
            _reject("global-requirement-drift")
    except Exception:
        logger.error("aggregate snapshot global error")
        raise
    logger.debug("aggregate snapshot global exit")
    return result


def _catalog_digest(doctrine, diagram, local_keys, global_keys, policy) -> str:
    logger.debug("aggregate catalog digest entry")
    try:
        key_rows = tuple(
            ("key", f"{kind.value}\0{identifier}\0{digest}")
            for kind, identifier, digest in (*local_keys, *global_keys)
        )
        keys = sequence_digest("veyra.p1c2.catalog-keys.v1", key_rows)
        result = tagged_digest(
            "veyra.p1c2.catalog.v1", ("version", CATALOG_VERSION),
            ("scope", CATALOG_SCOPE), ("doctrine", doctrine),
            ("diagram", diagram), ("keys", keys), ("policy", policy.policy_digest),
        )
    except Exception:
        logger.error("aggregate catalog digest error")
        raise
    logger.debug("aggregate catalog digest exit")
    return result


def snapshot_finite_confluence_catalog(
    value: FiniteConfluenceCatalogSource, doctrine: ObserverDoctrine,
    diagram: FiniteDiagramSource,
) -> FiniteConfluenceCatalogSource:
    """Rebuild all requirements, expected keys, policy, order, and digest."""
    logger.debug("snapshot_finite_confluence_catalog entry")
    if type(value) is not FiniteConfluenceCatalogSource:
        _reject("finite-confluence-catalog-must-be-exact")
    try:
        local, global_, policy = (
            value.local_requirements, value.global_requirements, value.policy,
        )
        supplied_local, supplied_global = (
            value.expected_local_keys, value.expected_global_keys,
        )
        outer = (
            value.doctrine_fingerprint, value.diagram_digest,
            value.catalog_digest, value.version, value.scope,
        )
    except AttributeError:
        _reject("finite-confluence-catalog-missing-fields")
    if type(local) is not tuple or type(global_) is not tuple:
        _reject("finite-confluence-catalog-container-drift")
    if type(supplied_local) is not tuple or type(supplied_global) is not tuple:
        _reject("finite-confluence-catalog-key-container-drift")
    result = finite_confluence_catalog(doctrine, diagram, local, global_, policy)
    captured_local = _catalog_keys(supplied_local, RequirementKind.LOCAL, 64)
    captured_global = _catalog_keys(supplied_global, RequirementKind.GLOBAL, 128)
    if (
        len(captured_local) != len(result.expected_local_keys)
        or len(captured_global) != len(result.expected_global_keys)
        or captured_local != result.expected_local_keys
        or captured_global != result.expected_global_keys
    ):
        _reject("finite-confluence-catalog-key-drift")
    doctrine_fp, diagram_digest, catalog_digest, version, scope = outer
    if (
        type(doctrine_fp) is not str or type(diagram_digest) is not str
        or type(version) is not str or type(scope) is not str
        or _hex_digest(catalog_digest, "catalog-digest") != result.catalog_digest
        or doctrine_fp != result.doctrine_fingerprint
        or diagram_digest != result.diagram_digest
        or version != CATALOG_VERSION or scope != CATALOG_SCOPE
    ):
        _reject("finite-confluence-catalog-binding-drift")
    logger.debug("snapshot_finite_confluence_catalog exit")
    return result


def _catalog_keys(value: tuple, expected_kind: RequirementKind, cap: int) -> tuple:
    logger.debug("aggregate catalog keys entry kind=%s", expected_kind.value)
    if len(value) > cap:
        _reject("finite-confluence-catalog-key-count-limit")
    rows = []
    for item in value:
        if type(item) is not tuple or len(item) != 3:
            _reject("finite-confluence-catalog-key-shape")
        kind, identifier, digest = item
        if type(kind) is not RequirementKind or kind is not expected_kind:
            _reject("finite-confluence-catalog-key-kind")
        if type(identifier) is not str or not identifier:
            _reject("finite-confluence-catalog-key-id")
        rows.append((kind, identifier, _hex_digest(digest, "catalog-key-digest")))
    result = tuple(rows)
    logger.debug("aggregate catalog keys exit kind=%s rows=%d", expected_kind.value, len(result))
    return result


def aggregate_run_digest(catalog: FiniteConfluenceCatalogSource) -> str:
    """Bind one deterministic replay run to exact source and policy identities."""
    logger.debug("aggregate_run_digest entry")
    result = tagged_digest(
        "veyra.p1c2.run.v1", ("doctrine", catalog.doctrine_fingerprint),
        ("diagram", catalog.diagram_digest), ("catalog", catalog.catalog_digest),
        ("policy", catalog.policy.policy_digest),
    )
    logger.debug("aggregate_run_digest exit")
    return result


def total_catalog_charge(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    catalog: FiniteConfluenceCatalogSource,
) -> int:
    """Charge each history edge once plus each aligned observer comparison."""
    logger.debug("total_catalog_charge entry")
    paths = {item.path_id: item for item in diagram.paths}
    edges = {item.edge_id: item for item in diagram.edges}
    total = 0
    for item in catalog.local_requirements:
        plan = item.plan
        selected = (
            plan.left_branch_path_id, plan.right_branch_path_id,
            plan.left_join_path_id, plan.right_join_path_id,
        )
        if any(path_id is None for path_id in selected):
            _reject("local-requirement-missing-joined-history")
        local_edges = tuple(
            edge_id for path_id in selected if path_id is not None
            for edge_id in paths[path_id].edge_ids
        )
        total += len(local_edges)
        total += len(plan.alignment) * len(item.transport.observer_ids)
        c1_charge = sum(
            max(1, len(edges[edge_id].preserved_observer_ids))
            for edge_id in local_edges
        ) + len(plan.alignment) * len(item.transport.observer_ids)
        if c1_charge > 4096:
            _reject("confluence-aggregate-local-c1-check-limit")
    for item in catalog.global_requirements:
        left = replay_history(item.left, doctrine, diagram)
        right = replay_history(item.right, doctrine, diagram)
        total += len(left.edge_ids) + len(right.edge_ids)
        total += len(item.alignment) * len(item.transport.observer_ids)
    if total > MAX_TOTAL_CHECKS:
        _reject("confluence-aggregate-hard-check-limit")
    logger.debug("total_catalog_charge exit checks=%d", total)
    return total


def aggregate_preflight(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    catalog: FiniteConfluenceCatalogSource,
) -> tuple[int, int, str, ConfluenceAggregateResourceLimit | None]:
    """Apply canonical-byte then total-check policy before any observation."""
    logger.debug("aggregate_preflight entry")
    encoded_bytes = len(catalog_canonical_bytes(catalog))
    if encoded_bytes > MAX_CANONICAL_BYTES:
        _reject("confluence-aggregate-hard-byte-limit")
    run = aggregate_run_digest(catalog)
    # Hard semantic validity is prior to every operational policy outcome.
    # Only a hard-valid request participates in the byte-then-check policy order.
    charged = total_catalog_charge(doctrine, diagram, catalog)
    if encoded_bytes > catalog.policy.max_bytes:
        refusal = _refusal(
            catalog, run, AggregateFailedBound.CANONICAL_BYTES,
            encoded_bytes, catalog.policy.max_bytes,
        )
        logger.debug("aggregate_preflight exit refused bound=canonical-bytes")
        return charged, encoded_bytes, run, refusal
    if charged <= catalog.policy.max_checks:
        logger.debug("aggregate_preflight exit accepted checks=%d bytes=%d", charged, encoded_bytes)
        return charged, encoded_bytes, run, None
    refusal = _refusal(
        catalog, run, AggregateFailedBound.TOTAL_CHECKS,
        charged, catalog.policy.max_checks,
    )
    logger.debug("aggregate_preflight exit refused bound=total-checks")
    return charged, encoded_bytes, run, refusal


def _refusal(
    catalog: FiniteConfluenceCatalogSource, run: str,
    failed: AggregateFailedBound, required: int, allowed: int,
) -> ConfluenceAggregateResourceLimit:
    """Construct a typed no-partial-evidence refusal after one failed bound."""
    logger.debug("aggregate refusal entry bound=%s", failed.value)
    refusal_digest = tagged_digest(
        "veyra.p1c2.resource-limit.v1", ("doctrine", catalog.doctrine_fingerprint),
        ("diagram", catalog.diagram_digest), ("catalog", catalog.catalog_digest),
        ("policy", catalog.policy.policy_digest), ("run", run),
        ("failed", failed.value), ("required", required), ("allowed", allowed),
    )
    refusal = ConfluenceAggregateResourceLimit(
        AggregateResultStatus.RESOURCE_LIMIT, catalog.doctrine_fingerprint,
        catalog.diagram_digest, catalog.catalog_digest, catalog.policy.policy_digest,
        run, failed, required, allowed, C2_NONCLAIMS, refusal_digest,
    )
    logger.debug("aggregate refusal exit bound=%s", failed.value)
    return refusal


def global_history_2cell(
    doctrine: ObserverDoctrine, diagram: FiniteDiagramSource,
    requirement: GlobalPathPairRequirement,
) -> GlobalHistory2CellArtifact:
    """Derive a full direct-echo 2-cell without C1 fork-shape coercion."""
    logger.debug("global_history_2cell entry")
    left = replay_history(requirement.left, doctrine, diagram)
    right = replay_history(requirement.right, doctrine, diagram)
    mismatches, openings = _persistence_obstructions(diagram, left, "left-history")
    right_bad, right_open = _persistence_obstructions(diagram, right, "right-history")
    mismatches.extend(right_bad)
    openings.extend(right_open)
    rows = tuple(
        _response_row(
            requirement.requirement_digest, point_index,
            point.left_index, point.right_index,
            left.stages[point.left_index], right.stages[point.right_index], observer_id,
        )
        for point_index, point in enumerate(requirement.alignment)
        for observer_id in requirement.transport.observer_ids
    )
    for row in rows:
        if row.status is ConfluenceStatus.REFUTED:
            mismatches.append(_row_obstruction(row))
        elif row.status is ConfluenceStatus.OPEN:
            openings.append(_row_obstruction(row))
    status = ConfluenceStatus.REFUTED if mismatches else (
        ConfluenceStatus.OPEN if openings else ConfluenceStatus.ESTABLISHED
    )
    first = mismatches[0] if mismatches else (openings[0] if openings else None)
    charged = (
        len(left.edge_ids) + len(right.edge_ids)
        + len(requirement.alignment) * len(requirement.transport.observer_ids)
    )
    left_trace = trace_digest("global-left", left.history_digest, rows)
    right_trace = trace_digest("global-right", right.history_digest, rows)
    combined = cell_trace_digest(left_trace, right_trace, requirement.requirement_digest)
    provisional = GlobalHistory2CellArtifact(
        doctrine.fingerprint, diagram.source_digest, requirement.requirement_digest,
        left.history_digest, right.history_digest, left.stage_commitments,
        right.stage_commitments, requirement.alignment,
        requirement.transport.observer_ids, requirement.transport.mode,
        requirement.transport.transport_digest, rows, left_trace, right_trace,
        combined, first, charged, status, "",
    )
    result = replace(provisional, artifact_digest=cell_artifact_digest(provisional))
    logger.debug("global_history_2cell exit status=%s rows=%d", status.value, len(rows))
    return result


def _persistence_obstructions(
    diagram: FiniteDiagramSource, history: ReplayedHistory, lane: str,
) -> tuple[list[ConfluenceObstruction], list[ConfluenceObstruction]]:
    logger.debug("global persistence entry lane=%s edges=%d", lane, len(history.edge_ids))
    edges = {item.edge_id: item for item in diagram.edges}
    stages = {item.stage_id: item for item in diagram.stages}
    mismatches: list[ConfluenceObstruction] = []
    openings: list[ConfluenceObstruction] = []
    for occurrence, edge_id in enumerate(history.edge_ids, start=1):
        edge = edges[edge_id]
        if not edge.preserved_observer_ids:
            openings.append(ConfluenceObstruction(lane, occurrence, "none", "not-queried"))
            continue
        upper = {item.observer_id: item for item in stages[edge.upper_stage_id].observers}
        for observer_id in edge.preserved_observer_ids:
            outcome = echo(
                decode_observer(upper[observer_id].canonical),
                stages[edge.lower_stage_id].representative,
                stages[edge.upper_stage_id].representative,
            )
            status = _status(outcome)
            obstruction = ConfluenceObstruction(
                lane, occurrence, observer_id, _outcome_name(outcome),
            )
            if status is ConfluenceStatus.REFUTED:
                mismatches.append(obstruction)
            elif status is ConfluenceStatus.OPEN:
                openings.append(obstruction)
    logger.debug("global persistence exit lane=%s bad=%d open=%d", lane, len(mismatches), len(openings))
    return mismatches, openings


def _response_row(
    requirement_digest: str, point_index: int, left_index: int, right_index: int,
    left: OntologyStage, right: OntologyStage, observer_id: str,
) -> TransportResponseRow:
    logger.debug("global response row entry point=%d", point_index)
    left_map = {item.observer_id: item for item in left.observers}
    right_map = {item.observer_id: item for item in right.observers}
    if observer_id not in left_map or observer_id not in right_map:
        status = ConfluenceStatus.OPEN
        outcome_name, payload = "observer-unavailable", b'{"tag":"observer-unavailable"}'
    else:
        outcome = echo(
            decode_observer(left_map[observer_id].canonical),
            left.representative, right.representative,
        )
        status, outcome_name, payload = _status(outcome), _outcome_name(outcome), _payload(outcome)
    fields = (
        ("requirement", requirement_digest.encode()),
        ("point", point_index.to_bytes(8, "big")),
        ("left-index", left_index.to_bytes(8, "big")),
        ("right-index", right_index.to_bytes(8, "big")),
        ("left-stage", left.stage_id.encode()), ("right-stage", right.stage_id.encode()),
        ("observer", observer_id.encode()), ("status", status.value.encode()),
        ("outcome", outcome_name.encode()), ("payload", payload),
    )
    result = TransportResponseRow(
        point_index, left_index, right_index, left.stage_id, right.stage_id,
        observer_id, status, outcome_name, payload, response_row_digest(fields),
    )
    logger.debug("global response row exit status=%s", status.value)
    return result


def _row_obstruction(row: TransportResponseRow) -> ConfluenceObstruction:
    logger.debug("global row obstruction entry point=%d", row.point_index)
    result = ConfluenceObstruction(
        "transport-alignment", row.point_index, row.observer_id, row.outcome,
    )
    logger.debug("global row obstruction exit")
    return result


def finite_confluence_aggregate(
    raw_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_catalog: FiniteConfluenceCatalogSource,
) -> FiniteConfluenceResult:
    """Replay every exact key only after atomic whole-catalog preflight."""
    logger.debug("finite_confluence_aggregate entry")
    doctrine = snapshot_confluence_doctrine(raw_doctrine)
    diagram = snapshot_finite_diagram_source(raw_diagram, doctrine)
    catalog = snapshot_finite_confluence_catalog(raw_catalog, doctrine, diagram)
    charged, _, run_digest, refusal = aggregate_preflight(doctrine, diagram, catalog)
    if refusal is not None:
        logger.debug("finite_confluence_aggregate exit resource-limit")
        return refusal
    local_rows = tuple(_local_row(doctrine, diagram, item) for item in catalog.local_requirements)
    global_rows = tuple(_global_row(doctrine, diagram, item) for item in catalog.global_requirements)
    rows = (*local_rows, *global_rows)
    actual_keys = tuple(item.key for item in rows)
    expected = (*catalog.expected_local_keys, *catalog.expected_global_keys)
    if actual_keys != expected:
        logger.error("finite_confluence_aggregate internal coverage drift")
        raise RuntimeError("internal confluence aggregate coverage drift")
    local_status = _local_status(local_rows)
    global_status = _global_status(global_rows)
    first = next((item.first_obstruction for item in rows if item.first_obstruction is not None), None)
    provisional = FiniteConfluenceAggregate(
        doctrine.fingerprint, diagram.source_digest, catalog.catalog_digest,
        catalog.policy.policy_digest, run_digest, catalog.expected_local_keys,
        catalog.expected_global_keys, rows, local_status, global_status,
        AggregateCoverageStatus.COMPLETE, first, charged, C2_NONCLAIMS, "",
    )
    result = replace(provisional, aggregate_digest=_aggregate_digest(provisional))
    logger.debug(
        "finite_confluence_aggregate exit local=%s global=%s rows=%d",
        local_status.value, global_status.value, len(rows),
    )
    return result


def _local_row(doctrine, diagram, requirement) -> ConfluenceRequirementRow:
    logger.debug("aggregate local row entry id=%s", requirement.requirement_id)
    judgment = fork_confluence_judgment(
        doctrine, diagram, requirement.plan, requirement.transport,
    )
    paths = {item.path_id: item for item in diagram.paths}
    plan = requirement.plan
    edge_occurrences = sum(
        len(paths[path_id].edge_ids) for path_id in (
            plan.left_branch_path_id, plan.right_branch_path_id,
            plan.left_join_path_id, plan.right_join_path_id,
        ) if path_id is not None
    )
    charged = edge_occurrences + len(plan.alignment) * len(requirement.transport.observer_ids)
    provisional = ConfluenceRequirementRow(
        (RequirementKind.LOCAL, requirement.requirement_id, requirement.requirement_digest),
        plan.plan_digest, None, None, requirement.transport.transport_digest,
        c1_judgment_digest(judgment), None, judgment.first_obstruction,
        charged, judgment.status, "",
    )
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("aggregate local row exit status=%s", result.status.value)
    return result


def _global_row(doctrine, diagram, requirement) -> ConfluenceRequirementRow:
    logger.debug("aggregate global row entry id=%s", requirement.requirement_id)
    left = replay_history(requirement.left, doctrine, diagram)
    right = replay_history(requirement.right, doctrine, diagram)
    cell = global_history_2cell(doctrine, diagram, requirement)
    provisional = ConfluenceRequirementRow(
        (RequirementKind.GLOBAL, requirement.requirement_id, requirement.requirement_digest),
        None, left.history_digest, right.history_digest,
        requirement.transport.transport_digest, None, cell.artifact_digest,
        cell.first_obstruction, cell.charged_checks, cell.status, "",
    )
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("aggregate global row exit status=%s", result.status.value)
    return result


def _local_status(rows: tuple[ConfluenceRequirementRow, ...]) -> LocalFiniteStatus:
    logger.debug("aggregate local status entry rows=%d", len(rows))
    statuses = tuple(item.status for item in rows)
    result = LocalFiniteStatus.REFUTED if ConfluenceStatus.REFUTED in statuses else (
        LocalFiniteStatus.OPEN if ConfluenceStatus.OPEN in statuses
        else LocalFiniteStatus.CONFLUENT
    )
    logger.debug("aggregate local status exit status=%s", result.value)
    return result


def _global_status(rows: tuple[ConfluenceRequirementRow, ...]) -> GlobalDeclaredFiniteStatus:
    logger.debug("aggregate global status entry rows=%d", len(rows))
    statuses = tuple(item.status for item in rows)
    result = GlobalDeclaredFiniteStatus.REFUTED if ConfluenceStatus.REFUTED in statuses else (
        GlobalDeclaredFiniteStatus.OPEN if ConfluenceStatus.OPEN in statuses
        else GlobalDeclaredFiniteStatus.CONFLUENT
    )
    logger.debug("aggregate global status exit status=%s", result.value)
    return result


def _aggregate_digest(value: FiniteConfluenceAggregate) -> str:
    logger.debug("aggregate digest entry")
    rows = sequence_digest(
        "veyra.p1c2.aggregate-rows.v1", tuple(("row", item.row_digest) for item in value.rows),
    )
    result = tagged_digest(
        "veyra.p1c2.aggregate.v1", ("doctrine", value.doctrine_fingerprint),
        ("diagram", value.diagram_digest), ("catalog", value.catalog_digest),
        ("policy", value.policy_digest), ("run", value.run_digest),
        ("rows", rows), ("local", value.local_status.value),
        ("global", value.global_status.value), ("coverage", value.coverage.value),
        ("charge", value.total_charge),
    )
    logger.debug("aggregate digest exit")
    return result


def validate_finite_confluence_result(
    raw_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_catalog: FiniteConfluenceCatalogSource, value: FiniteConfluenceResult,
) -> FiniteConfluenceResult:
    """Freshly derive the expected union variant, then validate supplied shape."""
    logger.debug("validate_finite_confluence_result entry")
    expected = finite_confluence_aggregate(raw_doctrine, raw_diagram, raw_catalog)
    if type(value) is not type(expected):
        _reject("confluence-aggregate-result-variant-drift")
    if type(expected) is ConfluenceAggregateResourceLimit:
        _validate_refusal(value, expected)
    elif type(expected) is FiniteConfluenceAggregate:
        _validate_aggregate(value, expected)
    else:
        _reject("unknown-confluence-aggregate-result-variant")
    logger.debug("validate_finite_confluence_result exit type=%s", type(expected).__name__)
    return expected


def _validate_refusal(raw, expected) -> None:
    logger.debug("validate aggregate refusal entry")
    exact_instance(raw, ConfluenceAggregateResourceLimit, "resource-limit")
    exact_fields(raw, expected, (
        ("status", type(expected.status)), ("doctrine_fingerprint", str),
        ("diagram_digest", str), ("catalog_digest", str), ("policy_digest", str),
        ("run_digest", str), ("failed_bound", type(expected.failed_bound)),
        ("required_value", int), ("allowed_value", int), ("refusal_digest", str),
    ), "confluence-aggregate-refusal-drift")
    _nonclaims(raw.nonclaims)
    logger.debug("validate aggregate refusal exit")


def _validate_aggregate(raw, expected) -> None:
    logger.debug("validate aggregate positive entry")
    exact_instance(raw, FiniteConfluenceAggregate, "positive-result")
    if (
        type(raw.expected_local_keys) is not tuple
        or type(raw.expected_global_keys) is not tuple
        or type(raw.rows) is not tuple or type(raw.nonclaims) is not tuple
    ):
        _reject("confluence-aggregate-outer-container-drift")
    exact_fields(raw, expected, (
        ("doctrine_fingerprint", str), ("diagram_digest", str),
        ("catalog_digest", str), ("policy_digest", str), ("run_digest", str),
        ("local_status", type(expected.local_status)),
        ("global_status", type(expected.global_status)),
        ("coverage", type(expected.coverage)), ("total_charge", int),
        ("aggregate_digest", str),
    ), "confluence-aggregate-outer-drift")
    lengths = (
        len(raw.expected_local_keys), len(raw.expected_global_keys), len(raw.rows),
        len(raw.nonclaims),
    )
    expected_lengths = (
        len(expected.expected_local_keys), len(expected.expected_global_keys),
        len(expected.rows), len(expected.nonclaims),
    )
    if lengths != expected_lengths:
        _reject("confluence-aggregate-outer-length-drift")
    _keys(raw.expected_local_keys, expected.expected_local_keys, RequirementKind.LOCAL)
    _keys(raw.expected_global_keys, expected.expected_global_keys, RequirementKind.GLOBAL)
    _nonclaims(raw.nonclaims)
    _obstruction(raw.first_obstruction, expected.first_obstruction, "aggregate-first")
    for supplied, wanted in zip(raw.rows, expected.rows, strict=True):
        _row(supplied, wanted)
    logger.debug("validate aggregate positive exit rows=%d", len(expected.rows))


def _row(raw, expected) -> None:
    logger.debug("validate aggregate row entry")
    exact_instance(raw, ConfluenceRequirementRow, "requirement-row")
    _key(raw.key, expected.key)
    exact_fields(raw, expected, (
        ("transport_digest", str), ("charged_checks", int),
        ("status", type(expected.status)), ("row_digest", str),
    ), "confluence-aggregate-row-drift")
    for name in (
        "plan_digest", "left_history_digest", "right_history_digest",
        "local_judgment_digest", "global_history_cell_digest",
    ):
        supplied, wanted = getattr(raw, name), getattr(expected, name)
        exact_optional_string(
            supplied, wanted, "confluence-aggregate-row-variant-drift",
        )
    _obstruction(raw.first_obstruction, expected.first_obstruction, "row-first")
    logger.debug("validate aggregate row exit")


def _keys(raw: tuple, expected: tuple, kind: RequirementKind) -> None:
    logger.debug("validate aggregate keys entry kind=%s", kind.value)
    for supplied, wanted in zip(raw, expected, strict=True):
        _key(supplied, wanted)
        if supplied[0] is not kind:
            _reject("confluence-aggregate-key-kind-drift")
    logger.debug("validate aggregate keys exit kind=%s", kind.value)


def _key(raw, expected) -> None:
    logger.debug("validate aggregate key entry")
    if type(raw) is not tuple or len(raw) != 3:
        _reject("confluence-aggregate-key-shape-drift")
    if (
        type(raw[0]) is not RequirementKind or raw[0] is not expected[0]
        or type(raw[1]) is not str or raw[1] != expected[1]
        or type(raw[2]) is not str or raw[2] != expected[2]
    ):
        _reject("confluence-aggregate-key-drift")
    logger.debug("validate aggregate key exit")


def _obstruction(raw, expected, field: str) -> None:
    logger.debug("validate aggregate obstruction entry field=%s", field)
    if expected is None:
        if raw is not None:
            _reject(f"confluence-{field}-obstruction-drift")
    else:
        exact_instance(raw, ConfluenceObstruction, f"{field}-obstruction")
        exact_fields(raw, expected, (
            ("lane", str), ("occurrence", int), ("observer_id", str),
            ("outcome", str),
        ), f"confluence-{field}-obstruction-drift")
    logger.debug("validate aggregate obstruction exit field=%s", field)


def _nonclaims(value) -> None:
    logger.debug("validate aggregate nonclaims entry")
    if (
        type(value) is not tuple or len(value) != len(C2_NONCLAIMS)
        or any(type(item) is not str for item in value) or value != C2_NONCLAIMS
    ):
        _reject("confluence-aggregate-nonclaims-drift")
    logger.debug("validate aggregate nonclaims exit")


def confluence_aggregate_scope_boundary() -> tuple[str, ...]:
    """Expose exact permanent nonclaims without promoting the finite catalog."""
    logger.debug("confluence_aggregate_scope_boundary entry")
    result = C2_NONCLAIMS
    logger.debug("confluence_aggregate_scope_boundary exit rows=%d", len(result))
    return result


__all__ = [
    "AggregateCoverageStatus", "AggregateFailedBound", "AggregateResultStatus",
    "C2_NONCLAIMS", "ConfluenceAggregatePolicy", "ConfluenceAggregateResourceLimit",
    "ConfluenceRequirementRow", "DeclaredHistory", "FiniteConfluenceAggregate",
    "FiniteConfluenceCatalogSource", "FiniteConfluenceResult",
    "GlobalDeclaredFiniteStatus", "GlobalHistory2CellArtifact",
    "GlobalPathPairRequirement", "IdentityHistory", "LocalCriticalForkRequirement",
    "LocalFiniteStatus", "RequirementKind", "confluence_aggregate_policy",
    "confluence_aggregate_scope_boundary", "declared_history",
    "finite_confluence_aggregate", "finite_confluence_catalog",
    "global_path_pair_requirement", "identity_history",
    "local_critical_fork_requirement", "validate_finite_confluence_result",
]
