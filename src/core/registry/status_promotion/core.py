"""P2-S status and promotion meta-calculus."""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from hashlib import sha256
import json
import logging
from typing import NoReturn, TypeAlias

from ...construction.all_depth_family.types import AllDepthFamilyJudgment
from ...construction.finite_builder.types import FiniteConstructionJudgment
from ...confluence.aggregate import FiniteConfluenceAggregate
from ...confluence.types import ForkConfluenceJudgment
from ...observer.genesis.types import GenesisJudgment

logger = logging.getLogger(__name__)

class JudgmentKind(str, Enum):
    PRESENTED = "presented"
    ADMISSIBLE = "admissible"
    OBSERVABLE = "observable"
    GENERABLE = "generable"
    COHERENT = "coherent"
    PERSISTENT = "persistent"
    CONFLUENT = "confluent"
    REFINEMENT_ROBUST = "refinement-robust"
    OBSERVER_ROLE = "observer-role"
    HISTORICALLY_ACTUALIZED = "historically-actualized"
    SCOPED_OBJECT = "scoped-object"
    ALL_DEPTH_FAMILY = "all-depth-family"
    COMPLETED_CARRIER = "completed-carrier"
    OBJECTIVELY_STABLE = "objectively-stable"
    PHYSICALLY_INSTANTIATED = "physically-instantiated"


class EvidenceStatus(str, Enum):
    ESTABLISHED = "established"
    ESTABLISHED_RELATIVE_TO_DOCTRINE = "established-relative-to-doctrine"
    ESTABLISHED_RELATIVE_TO_SCOPE = "established-relative-to-scope"
    ESTABLISHED_RELATIVE_TO_HISTORY = "established-relative-to-history"
    ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE = "established-relative-to-formation-scope"
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"
    ESTABLISHED_RELATIVE_TO_NETWORK = "established-relative-to-network"
    ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE = "established-relative-to-empirical-bridge"
    ASSUMED = "assumed"
    REFUTED = "refuted"
    OPEN = "open"
    NOT_ESTABLISHED = "not-established"
    NOT_CLAIMED = "not-claimed"


class PositiveProvenance(str, Enum):
    SUPPLIED_PRESENTATION = "supplied-presentation"
    DOCTRINE_REPLAY = "doctrine-replay"
    EXECUTABLE_REPLAY = "executable-replay"
    FORMALLY_DERIVED = "formally-derived"
    SUPPLIED_HYPOTHESIS = "supplied-hypothesis"
    ORACLE_DEPENDENT = "oracle-dependent"
    HISTORICAL_REPLAY = "historical-replay"
    EMPIRICAL_BRIDGE = "empirical-bridge"


class MetaAuditDecision(str, Enum):
    SCHEMA_CONFORMANT = "schema-conformant"


class MetaOntologicalStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class ResourceBound(str, Enum):
    PREMISE_COUNT = "premise-count"
    ASSUMPTION_COUNT = "assumption-count"
    FIELD_COUNT = "field-count"
    SCHEMA_COUNT = "schema-count"


class CastAttackOutcome(str, Enum):
    REJECTED = "rejected"


@dataclass(frozen=True)
class StatusProvenancePair:
    status: EvidenceStatus
    provenance: PositiveProvenance


@dataclass(frozen=True)
class KindStatusDomain:
    kind: JudgmentKind
    allowed_statuses: tuple[EvidenceStatus, ...]
    positive_pairs: tuple[StatusProvenancePair, ...]
    domain_digest: str


@dataclass(frozen=True)
class PremiseSignature:
    premise_name: str
    artifact_kind: str
    required_evidence_fields: tuple[str, ...]
    required_indices: tuple[str, ...]


@dataclass(frozen=True)
class PromotionRule:
    rule_id: str
    statement_digest: str
    premise_signatures: tuple[PremiseSignature, ...]
    output_kind: JudgmentKind
    output_status: EvidenceStatus
    output_provenance: PositiveProvenance
    output_indices: tuple[str, ...]
    forbidden_source_types: tuple[str, ...]
    forbidden_conclusion_fields: tuple[str, ...]
    assumption_policy_id: str
    permanent_nonclaims: tuple[str, ...]
    rule_digest: str


@dataclass(frozen=True)
class PremiseProjectionRule:
    projection_id: str
    source_rule_id: str
    premise_name: str
    projection_digest: str


@dataclass(frozen=True)
class IndexProjectionRule:
    projection_id: str
    kind: JudgmentKind
    input_indices: tuple[str, ...]
    hidden_index: str
    retained_indices: tuple[str, ...]
    projection_digest: str


@dataclass(frozen=True)
class SchemaTarget:
    schema_id: str
    exact_fields: tuple[str, ...]
    forbidden_positive_fields: tuple[str, ...]
    schema_digest: str


@dataclass(frozen=True)
class PromotionRegistry:
    version: str
    domains: tuple[KindStatusDomain, ...]
    rules: tuple[PromotionRule, ...]
    premise_projections: tuple[PremiseProjectionRule, ...]
    index_projections: tuple[IndexProjectionRule, ...]
    schema_targets: tuple[SchemaTarget, ...]
    registry_digest: str


@dataclass(frozen=True)
class IndexBinding:
    name: str
    value_digest: str


@dataclass(frozen=True)
class EvidenceField:
    name: str
    evidence_digest: str


@dataclass(frozen=True)
class PremiseArtifact:
    premise_name: str
    artifact_kind: str
    artifact_digest: str
    indices: tuple[IndexBinding, ...]
    evidence_fields: tuple[EvidenceField, ...]


@dataclass(frozen=True)
class AssumptionNode:
    assumption_id: str
    claim_id: str
    depends_on: tuple[str, ...]
    evidence_digest: str


@dataclass(frozen=True)
class ClaimDescriptor:
    claim_id: str
    kind: JudgmentKind
    status: EvidenceStatus
    provenance: PositiveProvenance | None
    indices: tuple[IndexBinding, ...]
    descriptor_digest: str


@dataclass(frozen=True)
class PromotionAuditRequest:
    version: str
    rule_id: str
    premises: tuple[PremiseArtifact, ...]
    assumptions: tuple[AssumptionNode, ...]
    conclusion: ClaimDescriptor
    request_digest: str


@dataclass(frozen=True)
class PromotionAuditPolicy:
    version: str
    max_premises: int
    max_assumptions: int
    max_fields: int
    max_schemas: int
    policy_digest: str


@dataclass(frozen=True)
class PromotionSchemaAudit:
    registry_digest: str
    rule_digest: str
    request_digest: str
    policy_digest: str
    conclusion: ClaimDescriptor
    premise_artifacts: tuple[PremiseArtifact, ...]
    assumption_closure: tuple[str, ...]
    nonclaims: tuple[str, ...]
    decision: MetaAuditDecision
    audit_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED
    scope: str = "promotion-schema-meta-validation-only"


@dataclass(frozen=True)
class PromotionResourceLimit:
    operation: str
    request_digest: str
    failed_bound: ResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


PromotionAuditResult: TypeAlias = PromotionSchemaAudit | PromotionResourceLimit


@dataclass(frozen=True)
class PremiseProjection:
    projection_rule_digest: str
    source_audit_digest: str
    artifact: PremiseArtifact
    projection_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class IndexProjection:
    projection_rule_digest: str
    source_descriptor: ClaimDescriptor
    retained_indices: tuple[IndexBinding, ...]
    hidden_binding: IndexBinding
    existential: bool
    projection_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class SchemaAuditRow:
    schema_id: str
    exact_match: bool
    forbidden_fields_absent: bool
    row_digest: str


@dataclass(frozen=True)
class SchemaAuditReport:
    registry_digest: str
    policy_digest: str
    rows: tuple[SchemaAuditRow, ...]
    scope: str
    nonclaims: tuple[str, ...]
    report_digest: str
    decision: MetaAuditDecision
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class CastAttack:
    attack_id: str
    weaker_kind: JudgmentKind
    stronger_kind: JudgmentKind
    reason: str
    attack_digest: str


@dataclass(frozen=True)
class CastAttackRow:
    attack: CastAttack
    outcome: CastAttackOutcome
    matching_rule_count: int
    row_digest: str


@dataclass(frozen=True)
class CastAttackMatrixReport:
    registry_digest: str
    rows: tuple[CastAttackRow, ...]
    report_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED

S = EvidenceStatus
K = JudgmentKind
P = PositiveProvenance

MAX_ID_BYTES = 128
MAX_STATIC_ROWS = 256


class StatusPromotionValidationError(ValueError):
    """A P2-S registry, audit, projection, or attack representation was invalid."""


def reject(reason: str) -> NoReturn:
    logger.error("status-promotion rejected reason=%s", reason)
    raise StatusPromotionValidationError(reason)


def exact_shape(value: object, expected_type: type, field: str) -> None:
    logger.debug("exact_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"{field}-must-be-exact")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"{field}-shape-drift")
    logger.debug("exact_shape exit field=%s", field)


def exact_identifier(value: object, field: str) -> str:
    logger.debug("exact_identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_ID_BYTES:
        reject(f"invalid-{field}")
    logger.debug("exact_identifier exit field=%s", field)
    return value


def exact_digest(value: object, field: str) -> str:
    logger.debug("exact_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("exact_digest exit field=%s", field)
    return value


def exact_tuple(value: object, field: str, *, nonempty: bool = False) -> tuple:
    logger.debug("exact_tuple entry field=%s", field)
    if type(value) is not tuple or (nonempty and not value) or len(value) > MAX_STATIC_ROWS:
        reject(f"invalid-{field}")
    logger.debug("exact_tuple exit field=%s rows=%d", field, len(value))
    return value


def exact_bool(value: object, field: str) -> bool:
    logger.debug("exact_bool entry field=%s", field)
    if type(value) is not bool:
        reject(f"invalid-{field}")
    logger.debug("exact_bool exit field=%s", field)
    return value


def exact_natural(value: object, field: str, maximum: int = 1_000_000) -> int:
    logger.debug("exact_natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= maximum:
        reject(f"invalid-{field}")
    logger.debug("exact_natural exit field=%s", field)
    return value
def frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    logger.debug("frame entry domain=%s fields=%d", domain, len(fields))
    out = bytearray(b"VEYRA-P2-S\x00")
    _token(out, b"domain", domain.encode())
    _token(out, b"count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(out, tag.encode(), value)
    result = bytes(out)
    logger.debug("frame exit domain=%s bytes=%d", domain, len(result))
    return result


def _token(out: bytearray, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d value=%d", len(tag), len(value))
    out.extend(len(tag).to_bytes(4, "big"))
    out.extend(tag)
    out.extend(len(value).to_bytes(8, "big"))
    out.extend(value)
    logger.debug("_token exit")


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("digest entry domain=%s", domain)
    result = sha256(frame(domain, fields)).hexdigest()
    logger.debug("digest exit domain=%s", domain)
    return result


def text_rows(prefix: str, rows: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    logger.debug("text_rows entry prefix=%s rows=%d", prefix, len(rows))
    result = ((f"{prefix}-count", len(rows).to_bytes(8, "big")),) + tuple(
        (f"{prefix}-{index}", value.encode()) for index, value in enumerate(rows)
    )
    logger.debug("text_rows exit prefix=%s", prefix)
    return result


def nested_rows(prefix: str, rows: tuple[bytes, ...]) -> tuple[tuple[str, bytes], ...]:
    logger.debug("nested_rows entry prefix=%s rows=%d", prefix, len(rows))
    result = ((f"{prefix}-count", len(rows).to_bytes(8, "big")),) + tuple(
        (f"{prefix}-{index}", value) for index, value in enumerate(rows)
    )
    logger.debug("nested_rows exit prefix=%s", prefix)
    return result
def premise_projection_digest(
    projection_id: str, source_rule_id: str, premise_name: str,
) -> str:
    """Bind the public projection name together with its exact source pair."""
    logger.debug("premise_projection_digest entry projection=%s", projection_id)
    projection_id = exact_identifier(projection_id, "projection-id")
    source_rule_id = exact_identifier(source_rule_id, "source-rule-id")
    premise_name = exact_identifier(premise_name, "premise-name")
    result = digest("veyra.p2s.premise-projection-rule.v1", (
        ("projection-id", projection_id.encode()),
        ("rule", source_rule_id.encode()),
        ("premise", premise_name.encode()),
    ))
    logger.debug("premise_projection_digest exit")
    return result
SCHEMA_ROWS = (
    ("finite-construction-judgment", (
        "doctrine_fingerprint", "source_binding_digest", "target_stage_id",
        "target_commitment", "replay", "formal_generability", "obstruction",
        "ontic_genesis", "target_independence", "scoped_object", "scope",
    )),
    ("observer-genesis-judgment", (
        "doctrine_digest", "source_digest", "adapter_digest", "witness_digest",
        "recurrence_digest", "oep_digest", "run_digest", "judgment_digest",
        "operation_status", "premises", "primitive_genealogy", "structural_closure",
        "recurrent_return", "counterfactual_discrimination", "bounded_persistence",
        "residue_efficacy", "observer_role_relative_to_scope",
        "historical_target_independence", "physical_instantiation", "scope",
    )),
    ("fork-confluence-judgment", (
        "plan_id", "plan_digest", "status", "transport_cell", "first_obstruction",
        "charged_checks", "local_finite_confluence", "global_confluence",
        "scoped_formation", "scope",
    )),
    ("finite-confluence-aggregate", (
        "doctrine_fingerprint", "diagram_digest", "catalog_digest", "policy_digest",
        "run_digest", "expected_local_keys", "expected_global_keys", "rows",
        "local_status", "global_status", "coverage", "first_obstruction",
        "total_charge", "nonclaims", "aggregate_digest",
    )),
    ("all-depth-family-judgment", (
        "spec", "source", "spec_validity", "coordinate_totality",
        "restriction_compatibility", "algebraic_laws", "evidence_status",
        "provenance", "ledger_status", "ledger_digest", "foundation_id",
        "tcb_digest", "family_term_digest", "introduction_evidence_digest",
        "judgment_digest", "completed_carrier", "universal_realization",
        "observer_separation", "scope",
    )),
)


def schema_targets(forbidden: tuple[str, ...]) -> tuple[SchemaTarget, ...]:
    """Return exact allowlisted schema commitments without module discovery."""
    logger.debug("schema_targets entry rows=%d", len(SCHEMA_ROWS))
    result = tuple(
        SchemaTarget(schema_id, fields, forbidden, digest("veyra.p2s.schema.v1", (
            ("schema-id", schema_id.encode()),
            *text_rows("field", fields),
            *text_rows("forbidden", forbidden),
        )))
        for schema_id, fields in SCHEMA_ROWS
    )
    logger.debug("schema_targets exit rows=%d", len(result))
    return result
REGISTRY_VERSION = "p2-s-promotion-registry-v1"
ASSUMPTION_POLICY_ID = "p2-s-acyclic-no-own-conclusion-v1"
FORBIDDEN_SOURCE_TYPES = (
    "bool", "digest-only", "old-certificate", "old-judgment", "finite-sample-table",
)
FORBIDDEN_CONCLUSION_FIELDS = (
    "exists", "global_exists", "metaphysically_exists", "proof_complete",
    "observer_independent", "physical_exists",
)
NONCLAIMS = (
    "ontology-completeness", "codebase-completeness", "retroactive-certification",
    "metaphysical-truth", "automatic-promotion",
)
_SCOPE_KINDS = (
    K.OBSERVABLE, K.GENERABLE, K.COHERENT, K.PERSISTENT,
    K.CONFLUENT, K.REFINEMENT_ROBUST,
)


def _pair(status: S, provenance: P) -> StatusProvenancePair:
    logger.debug("_pair entry")
    result = StatusProvenancePair(status, provenance)
    logger.debug("_pair exit")
    return result


def _domain(kind: K, statuses: tuple[S, ...], pairs: tuple[StatusProvenancePair, ...]):
    logger.debug("_domain entry kind=%s", kind.value)
    value = digest("veyra.p2s.kind-domain.v1", (
        ("kind", kind.value.encode()),
        *text_rows("status", tuple(item.value for item in statuses)),
        *nested_rows("pair", tuple(frame("veyra.p2s.status-pair.v1", (
            ("status", item.status.value.encode()),
            ("provenance", item.provenance.value.encode()),
        )) for item in pairs)),
    ))
    result = KindStatusDomain(kind, statuses, pairs, value)
    logger.debug("_domain exit")
    return result


def _domains() -> tuple[KindStatusDomain, ...]:
    logger.debug("_domains entry")
    scope_statuses = (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN)
    scope_pairs = (
        _pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
        _pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED),
    )
    by_kind = {
        K.PRESENTED: ((S.ESTABLISHED, S.OPEN), (_pair(S.ESTABLISHED, P.SUPPLIED_PRESENTATION),)),
        K.ADMISSIBLE: (
            (S.ESTABLISHED_RELATIVE_TO_DOCTRINE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_DOCTRINE, P.DOCTRINE_REPLAY),),
        ),
        **{kind: (scope_statuses, scope_pairs) for kind in _SCOPE_KINDS},
        K.OBSERVER_ROLE: (
            (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_SCOPE, P.DOCTRINE_REPLAY),),
        ),
        K.HISTORICALLY_ACTUALIZED: (
            (S.ESTABLISHED_RELATIVE_TO_HISTORY, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY),),
        ),
        K.SCOPED_OBJECT: (
            (S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, P.DOCTRINE_REPLAY),),
        ),
        K.ALL_DEPTH_FAMILY: (
            (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.ASSUMED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),
             _pair(S.ASSUMED, P.SUPPLIED_HYPOTHESIS),
             _pair(S.ASSUMED, P.ORACLE_DEPENDENT)),
        ),
        K.COMPLETED_CARRIER: (
            (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),),
        ),
        K.OBJECTIVELY_STABLE: (
            (S.ESTABLISHED_RELATIVE_TO_NETWORK, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_NETWORK, P.EXECUTABLE_REPLAY),
             _pair(S.ESTABLISHED_RELATIVE_TO_NETWORK, P.FORMALLY_DERIVED)),
        ),
        K.PHYSICALLY_INSTANTIATED: (
            (S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, S.REFUTED, S.OPEN),
            (_pair(S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, P.EMPIRICAL_BRIDGE),),
        ),
    }
    result = tuple(_domain(kind, *by_kind[kind]) for kind in K)
    logger.debug("_domains exit count=%d", len(result))
    return result


def _premise(name: str, kind: str, fields: tuple[str, ...], indices: tuple[str, ...]):
    logger.debug("_premise entry name=%s", name)
    result = PremiseSignature(name, kind, fields, indices)
    logger.debug("_premise exit")
    return result


_RULE_ROWS = (
    ("exact-snapshot-v1", K.PRESENTED, S.ESTABLISHED, P.SUPPLIED_PRESENTATION, ("scope",),
     (("representation", "bounded-representation", ("canonical",), ("scope",)),)),
    ("doctrine-admission-v1", K.ADMISSIBLE, S.ESTABLISHED_RELATIVE_TO_DOCTRINE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope"),
     (("presentation", "presentation-artifact", ("canonical",), ("scope",)),
      ("doctrine", "doctrine-replay", ("admission",), ("doctrine",)))),
    ("observer-execution-v1", K.OBSERVABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "observer"),
     (("coupling", "admitted-coupling", ("response",), ("doctrine", "observer")),
      ("input", "exact-input", ("input",), ("scope",)))),
    ("p1-b-finite-generation-v1", K.GENERABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "stage"),
     (("seed", "seed-source", ("seed",), ("doctrine",)),
      ("program", "closed-program", ("replay",), ("scope", "stage")))),
    ("compatibility-replay-v1", K.COHERENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope"),
     (("relations", "exact-relations", ("relation-laws",), ("doctrine", "scope")),
      ("restrictions", "exact-restrictions", ("restriction-laws",), ("scope",)))),
    ("continuation-replay-v1", K.PERSISTENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "history"),
     (("trace", "trace-artifact", ("trace",), ("history",)),
      ("continuation", "named-continuation", ("persistence",), ("scope",)))),
    ("oep-observer-role-v1", K.OBSERVER_ROLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope", "observer"),
     tuple((name, f"oep-{name}", (name,), ("scope", "observer")) for name in
           ("genealogy", "recurrence", "discrimination", "persistence", "efficacy"))),
    ("hap-historical-actualization-v1", K.HISTORICALLY_ACTUALIZED,
     S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY,
     ("doctrine", "scope", "history", "observer"),
     (("oep", "observer-role-artifact", ("role",), ("doctrine", "scope", "observer")),
      ("history", "birth-history", ("prior-history", "causal-pressure"), ("history",)))),
    ("c2-c3-confluence-v1", K.CONFLUENT, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "history"),
     (("diagrams", "demanded-path-diagrams", ("coverage", "commutation"),
       ("doctrine", "scope", "history")),)),
    ("a2-refinement-survival-v1", K.REFINEMENT_ROBUST, S.ESTABLISHED_RELATIVE_TO_SCOPE,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "refinement"),
     (("refinement", "genuine-refinement", ("strictness", "survival"),
       ("doctrine", "scope", "refinement")),)),
    ("sfp-scoped-formation-v1", K.SCOPED_OBJECT, S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE,
     P.DOCTRINE_REPLAY, ("doctrine", "scope", "history"),
     tuple((name, f"sfp-{name}", (name,), ("doctrine", "scope")) for name in
           ("construction", "support", "g4", "persistence", "confluence", "refinement"))),
    ("afip-formally-derived-v1", K.ALL_DEPTH_FAMILY, S.ESTABLISHED_RELATIVE_TO_LEDGER,
     P.FORMALLY_DERIVED, ("doctrine", "ledger", "family"),
     (("totality", "formal-totality-source", ("theorem", "formal-source"), ("ledger",)),
      ("restriction", "formal-restriction-laws", ("theorem",), ("family",)),
      ("ledger", "assumption-ledger", ("closure",), ("ledger",)))),
    ("afip-supplied-hypothesis-v1", K.ALL_DEPTH_FAMILY, S.ASSUMED,
     P.SUPPLIED_HYPOTHESIS, ("doctrine", "ledger", "family"),
     (("hypothesis", "supplied-family-hypothesis", ("totality", "compatibility"),
       ("ledger", "family")),)),
    ("afip-oracle-hypothesis-v1", K.ALL_DEPTH_FAMILY, S.ASSUMED,
     P.ORACLE_DEPENDENT, ("doctrine", "ledger", "family"),
     (("oracle", "total-oracle-hypothesis", ("totality", "purity", "stability", "trust"),
       ("ledger", "family")),)),
    ("pomega-carrier-completion-v1", K.COMPLETED_CARRIER,
     S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED,
     ("doctrine", "ledger", "carrier"),
     (("carrier", "carrier-formation", ("constructor",), ("carrier",)),
      ("realization", "universal-realization", ("theorem",), ("ledger", "carrier")),
      ("separation", "joint-separation", ("theorem",), ("carrier",)),
      ("nonvacuity", "family-class-witness", ("witness",), ("ledger",)))),
    ("network-invariance-v1", K.OBJECTIVELY_STABLE, S.ESTABLISHED_RELATIVE_TO_NETWORK,
     P.EXECUTABLE_REPLAY, ("doctrine", "scope", "network", "history"),
     (("translations", "network-translations", ("preservation", "reflection", "domain"),
       ("network",)), ("confluence", "network-confluence", ("all-demanded",), ("history",)),
      ("refinements", "network-refinements", ("survival", "no-conflict"), ("scope",)))),
    ("empirical-bridge-v1", K.PHYSICALLY_INSTANTIATED,
     S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, P.EMPIRICAL_BRIDGE,
     ("doctrine", "scope", "measurement"),
     (("measurement", "external-measurement", ("measurement", "provenance"),
       ("measurement",)), ("bridge", "empirical-doctrine", ("identification",),
       ("doctrine", "scope")))),
)


def _rule(row: tuple) -> PromotionRule:
    logger.debug("_rule entry rule=%s", row[0])
    rule_id, kind, status, provenance, indices, premise_rows = row
    premises = tuple(_premise(*premise_row) for premise_row in premise_rows)
    statement = digest("veyra.p2s.rule-statement.v1", (
        ("rule-id", rule_id.encode()),
        ("statement", f"named-introduction:{rule_id}".encode()),
    ))
    premise_frames = tuple(frame("veyra.p2s.premise-signature.v1", (
        ("name", item.premise_name.encode()),
        ("artifact-kind", item.artifact_kind.encode()),
        *text_rows("evidence", item.required_evidence_fields),
        *text_rows("index", item.required_indices),
    )) for item in premises)
    value = digest("veyra.p2s.promotion-rule.v1", (
        ("rule-id", rule_id.encode()), ("statement", statement.encode()),
        *nested_rows("premise", premise_frames),
        ("output-kind", kind.value.encode()), ("output-status", status.value.encode()),
        ("output-provenance", provenance.value.encode()),
        *text_rows("output-index", indices),
        *text_rows("forbidden-source", FORBIDDEN_SOURCE_TYPES),
        *text_rows("forbidden-conclusion", FORBIDDEN_CONCLUSION_FIELDS),
        ("assumption-policy", ASSUMPTION_POLICY_ID.encode()),
        *text_rows("nonclaim", NONCLAIMS),
    ))
    result = PromotionRule(
        rule_id, statement, premises, kind, status, provenance, indices,
        FORBIDDEN_SOURCE_TYPES, FORBIDDEN_CONCLUSION_FIELDS,
        ASSUMPTION_POLICY_ID, NONCLAIMS, value,
    )
    logger.debug("_rule exit rule=%s", rule_id)
    return result


def _premise_projections(rules: tuple[PromotionRule, ...]):
    logger.debug("_premise_projections entry rules=%d", len(rules))
    result = tuple(
        PremiseProjectionRule(
            projection_id, rule.rule_id, premise.premise_name,
            premise_projection_digest(projection_id, rule.rule_id, premise.premise_name),
        )
        for rule in rules for premise in rule.premise_signatures
        for projection_id in (f"p2-project-{rule.rule_id}-{premise.premise_name}-v1",)
    )
    logger.debug("_premise_projections exit rows=%d", len(result))
    return result


def _index_projections() -> tuple[IndexProjectionRule, ...]:
    logger.debug("_index_projections entry")
    projection_id = "p2-exists-generable-stage-v1"
    input_indices = ("doctrine", "scope", "stage")
    retained = ("doctrine", "scope")
    value = digest("veyra.p2s.index-projection-rule.v1", (
        ("projection-id", projection_id.encode()), ("kind", K.GENERABLE.value.encode()),
        *text_rows("input", input_indices), ("hidden", b"stage"),
        *text_rows("retained", retained),
    ))
    result = (IndexProjectionRule(
        projection_id, K.GENERABLE, input_indices, "stage", retained, value,
    ),)
    logger.debug("_index_projections exit")
    return result


def promotion_registry() -> PromotionRegistry:
    """Build the frozen versioned P2-S registry and its exact commitment."""
    logger.debug("promotion_registry entry")
    domains = _domains()
    rules = tuple(_rule(row) for row in _RULE_ROWS)
    premise_projections = _premise_projections(rules)
    index_projections = _index_projections()
    schemas = schema_targets(FORBIDDEN_CONCLUSION_FIELDS)
    value = digest("veyra.p2s.registry.v1", (
        ("version", REGISTRY_VERSION.encode()),
        *text_rows("domain", tuple(item.domain_digest for item in domains)),
        *text_rows("rule", tuple(item.rule_digest for item in rules)),
        *text_rows("premise-projection", tuple(
            item.projection_digest for item in premise_projections)),
        *text_rows("index-projection", tuple(
            item.projection_digest for item in index_projections)),
        *text_rows("schema", tuple(item.schema_digest for item in schemas)),
    ))
    result = PromotionRegistry(
        REGISTRY_VERSION, domains, rules, premise_projections,
        index_projections, schemas, value,
    )
    logger.debug("promotion_registry exit digest=%s", value[:12])
    return result
REQUEST_VERSION = "p2-s-promotion-request-v1"
POLICY_VERSION = "p2-s-promotion-policy-v1"


def _enum(value: object, enum_type: type, field: str):
    logger.debug("_enum entry field=%s", field)
    if type(value) is not enum_type:
        reject(f"invalid-{field}")
    logger.debug("_enum exit field=%s", field)
    return value


def _names(values: tuple, field: str) -> tuple[str, ...]:
    logger.debug("_names entry field=%s", field)
    exact_tuple(values, field)
    result = tuple(exact_identifier(value, f"{field}-member") for value in values)
    if len(set(result)) != len(result):
        reject(f"duplicate-{field}")
    logger.debug("_names exit field=%s", field)
    return result


def validate_registry(value: object) -> PromotionRegistry:
    """Validate every bounded registry cell before canonical equality."""
    logger.debug("validate_registry entry")
    exact_shape(value, PromotionRegistry, "registry")
    exact_identifier(value.version, "registry-version")
    for field_name in (
        "domains", "rules", "premise_projections", "index_projections", "schema_targets",
    ):
        exact_tuple(getattr(value, field_name), f"registry-{field_name}")
    exact_digest(value.registry_digest, "registry-digest")
    for domain in value.domains:
        exact_shape(domain, KindStatusDomain, "domain")
        _enum(domain.kind, JudgmentKind, "domain-kind")
        exact_tuple(domain.allowed_statuses, "allowed-statuses")
        exact_tuple(domain.positive_pairs, "positive-pairs")
        for status in domain.allowed_statuses:
            _enum(status, EvidenceStatus, "allowed-status")
        for pair in domain.positive_pairs:
            exact_shape(pair, StatusProvenancePair, "status-provenance-pair")
            _enum(pair.status, EvidenceStatus, "pair-status")
            _enum(pair.provenance, PositiveProvenance, "pair-provenance")
        exact_digest(domain.domain_digest, "domain-digest")
    _validate_rule_rows(value)
    _validate_projection_rows(value)
    _validate_schema_rows(value)
    if value != promotion_registry():
        reject("registry-not-canonical")
    logger.debug("validate_registry exit")
    return value


def _validate_rule_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_rule_rows entry")
    for rule in value.rules:
        exact_shape(rule, PromotionRule, "promotion-rule")
        exact_identifier(rule.rule_id, "rule-id")
        exact_digest(rule.statement_digest, "statement-digest")
        exact_tuple(rule.premise_signatures, "premise-signatures", nonempty=True)
        for premise in rule.premise_signatures:
            exact_shape(premise, PremiseSignature, "premise-signature")
            exact_identifier(premise.premise_name, "premise-name")
            exact_identifier(premise.artifact_kind, "artifact-kind")
            _names(premise.required_evidence_fields, "required-evidence-fields")
            _names(premise.required_indices, "required-indices")
        _enum(rule.output_kind, JudgmentKind, "output-kind")
        _enum(rule.output_status, EvidenceStatus, "output-status")
        _enum(rule.output_provenance, PositiveProvenance, "output-provenance")
        _names(rule.output_indices, "output-indices")
        _names(rule.forbidden_source_types, "forbidden-source-types")
        _names(rule.forbidden_conclusion_fields, "forbidden-conclusion-fields")
        exact_identifier(rule.assumption_policy_id, "assumption-policy-id")
        _names(rule.permanent_nonclaims, "permanent-nonclaims")
        exact_digest(rule.rule_digest, "rule-digest")
    logger.debug("_validate_rule_rows exit")


def _validate_projection_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_projection_rows entry")
    for item in value.premise_projections:
        exact_shape(item, PremiseProjectionRule, "premise-projection-rule")
        exact_identifier(item.projection_id, "projection-id")
        exact_identifier(item.source_rule_id, "source-rule-id")
        exact_identifier(item.premise_name, "projection-premise-name")
        exact_digest(item.projection_digest, "projection-digest")
    for item in value.index_projections:
        exact_shape(item, IndexProjectionRule, "index-projection-rule")
        exact_identifier(item.projection_id, "projection-id")
        _enum(item.kind, JudgmentKind, "projection-kind")
        _names(item.input_indices, "projection-input-indices")
        exact_identifier(item.hidden_index, "hidden-index")
        _names(item.retained_indices, "retained-indices")
        exact_digest(item.projection_digest, "projection-digest")
    logger.debug("_validate_projection_rows exit")


def _validate_schema_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_schema_rows entry")
    for item in value.schema_targets:
        exact_shape(item, SchemaTarget, "schema-target")
        exact_identifier(item.schema_id, "schema-id")
        _names(item.exact_fields, "schema-fields")
        _names(item.forbidden_positive_fields, "schema-forbidden-fields")
        exact_digest(item.schema_digest, "schema-digest")
    logger.debug("_validate_schema_rows exit")


def promotion_policy(
    max_premises: int = 64, max_assumptions: int = 64,
    max_fields: int = 256, max_schemas: int = 16,
) -> PromotionAuditPolicy:
    logger.debug("promotion_policy entry")
    values = tuple(exact_natural(value, name) for name, value in (
        ("max-premises", max_premises), ("max-assumptions", max_assumptions),
        ("max-fields", max_fields), ("max-schemas", max_schemas),
    ))
    value = digest("veyra.p2s.policy.v1", (
        ("version", POLICY_VERSION.encode()),
        *tuple((name, number.to_bytes(8, "big")) for name, number in zip(
            ("max-premises", "max-assumptions", "max-fields", "max-schemas"), values)),
    ))
    result = PromotionAuditPolicy(POLICY_VERSION, *values, value)
    logger.debug("promotion_policy exit")
    return result


DEFAULT_POLICY = promotion_policy()


def validate_policy(value: object) -> PromotionAuditPolicy:
    logger.debug("validate_policy entry")
    exact_shape(value, PromotionAuditPolicy, "policy")
    exact_identifier(value.version, "policy-version")
    for name in ("max_premises", "max_assumptions", "max_fields", "max_schemas"):
        exact_natural(getattr(value, name), name)
    exact_digest(value.policy_digest, "policy-digest")
    expected = promotion_policy(
        value.max_premises, value.max_assumptions, value.max_fields, value.max_schemas,
    )
    if value != expected:
        reject("policy-digest-mismatch")
    logger.debug("validate_policy exit")
    return value


def index_binding(name: str, value_digest: str) -> IndexBinding:
    logger.debug("index_binding entry")
    result = IndexBinding(exact_identifier(name, "index-name"), exact_digest(
        value_digest, "index-value-digest"))
    logger.debug("index_binding exit")
    return result


def evidence_field(name: str, evidence_digest: str) -> EvidenceField:
    logger.debug("evidence_field entry")
    result = EvidenceField(exact_identifier(name, "evidence-name"), exact_digest(
        evidence_digest, "evidence-digest"))
    logger.debug("evidence_field exit")
    return result


def premise_artifact(
    premise_name: str, artifact_kind: str, artifact_digest: str,
    indices: tuple[IndexBinding, ...], evidence_fields: tuple[EvidenceField, ...],
) -> PremiseArtifact:
    logger.debug("premise_artifact entry")
    exact_tuple(indices, "artifact-indices")
    exact_tuple(evidence_fields, "artifact-evidence", nonempty=True)
    result = PremiseArtifact(
        exact_identifier(premise_name, "premise-name"),
        exact_identifier(artifact_kind, "artifact-kind"),
        exact_digest(artifact_digest, "artifact-digest"), indices, evidence_fields,
    )
    validate_premise_artifact(result)
    logger.debug("premise_artifact exit")
    return result


def validate_premise_artifact(value: object) -> PremiseArtifact:
    logger.debug("validate_premise_artifact entry")
    exact_shape(value, PremiseArtifact, "premise-artifact")
    exact_identifier(value.premise_name, "premise-name")
    exact_identifier(value.artifact_kind, "artifact-kind")
    exact_digest(value.artifact_digest, "artifact-digest")
    exact_tuple(value.indices, "artifact-indices")
    exact_tuple(value.evidence_fields, "artifact-evidence", nonempty=True)
    for item in value.indices:
        exact_shape(item, IndexBinding, "index-binding")
        index_binding(item.name, item.value_digest)
    for item in value.evidence_fields:
        exact_shape(item, EvidenceField, "evidence-field")
        evidence_field(item.name, item.evidence_digest)
    if len({item.name for item in value.indices}) != len(value.indices):
        reject("duplicate-artifact-index")
    if len({item.name for item in value.evidence_fields}) != len(value.evidence_fields):
        reject("duplicate-evidence-field")
    logger.debug("validate_premise_artifact exit")
    return value
def assumption_node(
    assumption_id: str, claim_id: str, depends_on: tuple[str, ...], evidence_digest: str,
) -> AssumptionNode:
    logger.debug("assumption_node entry")
    exact_tuple(depends_on, "depends-on")
    dependencies = tuple(exact_identifier(item, "dependency-id") for item in depends_on)
    if len(set(dependencies)) != len(dependencies):
        reject("duplicate-dependency")
    result = AssumptionNode(
        exact_identifier(assumption_id, "assumption-id"),
        exact_identifier(claim_id, "assumption-claim-id"), dependencies,
        exact_digest(evidence_digest, "assumption-evidence-digest"),
    )
    logger.debug("assumption_node exit")
    return result


def claim_descriptor(
    claim_id: str, kind: JudgmentKind, status: EvidenceStatus,
    provenance: PositiveProvenance | None, indices: tuple[IndexBinding, ...],
    registry: PromotionRegistry | None = None,
) -> ClaimDescriptor:
    logger.debug("claim_descriptor entry")
    registry = promotion_registry() if registry is None else registry
    exact_tuple(indices, "descriptor-indices")
    _enum(kind, JudgmentKind, "descriptor-kind")
    _enum(status, EvidenceStatus, "descriptor-status")
    if provenance is not None:
        _enum(provenance, PositiveProvenance, "descriptor-provenance")
    checked = tuple(index_binding(item.name, item.value_digest) if (
        exact_shape(item, IndexBinding, "descriptor-index") is None
    ) else item for item in indices)
    if len({item.name for item in checked}) != len(checked):
        reject("duplicate-descriptor-index")
    _validate_pair(registry, kind, status, provenance)
    value = digest("veyra.p2s.claim-descriptor.v1", (
        ("claim-id", exact_identifier(claim_id, "claim-id").encode()),
        ("kind", kind.value.encode()), ("status", status.value.encode()),
        ("provenance", b"none" if provenance is None else provenance.value.encode()),
        *nested_rows("index", tuple(frame("veyra.p2s.index-binding.v1", (
            ("name", item.name.encode()), ("value", item.value_digest.encode()),
        )) for item in checked)),
    ))
    result = ClaimDescriptor(claim_id, kind, status, provenance, checked, value)
    logger.debug("claim_descriptor exit")
    return result


def _validate_pair(
    registry: PromotionRegistry, kind: JudgmentKind, status: EvidenceStatus,
    provenance: PositiveProvenance | None,
) -> None:
    logger.debug("_validate_pair entry")
    domains = tuple(item for item in registry.domains if item.kind is kind)
    if len(domains) != 1 or status not in domains[0].allowed_statuses:
        reject("status-outside-kind-domain")
    if status in (EvidenceStatus.OPEN, EvidenceStatus.REFUTED):
        if provenance is not None:
            reject("nonpositive-status-has-positive-provenance")
    elif provenance is None or not any(
        pair.status is status and pair.provenance is provenance
        for pair in domains[0].positive_pairs
    ):
        reject("invalid-positive-provenance-pair")
    logger.debug("_validate_pair exit")


def validate_claim_descriptor(
    value: object, registry: PromotionRegistry,
) -> ClaimDescriptor:
    logger.debug("validate_claim_descriptor entry")
    exact_shape(value, ClaimDescriptor, "claim-descriptor")
    exact_identifier(value.claim_id, "claim-id")
    _enum(value.kind, JudgmentKind, "descriptor-kind")
    _enum(value.status, EvidenceStatus, "descriptor-status")
    if value.provenance is not None:
        _enum(value.provenance, PositiveProvenance, "descriptor-provenance")
    exact_tuple(value.indices, "descriptor-indices")
    expected = claim_descriptor(
        value.claim_id, value.kind, value.status, value.provenance, value.indices, registry,
    )
    exact_digest(value.descriptor_digest, "descriptor-digest")
    if value != expected:
        reject("descriptor-digest-mismatch")
    logger.debug("validate_claim_descriptor exit")
    return value


def promotion_audit_request(
    rule_id: str, premises: tuple, assumptions: tuple[AssumptionNode, ...],
    conclusion: ClaimDescriptor, registry: PromotionRegistry | None = None,
) -> PromotionAuditRequest:
    logger.debug("promotion_audit_request entry")
    registry = promotion_registry() if registry is None else registry
    exact_tuple(premises, "request-premises")
    exact_tuple(assumptions, "request-assumptions")
    premise_values = tuple(validate_premise_artifact(item) for item in premises)
    assumption_values = tuple(validate_assumption_node(item) for item in assumptions)
    conclusion_value = validate_claim_descriptor(conclusion, registry)
    value = digest("veyra.p2s.audit-request.v1", (
        ("version", REQUEST_VERSION.encode()),
        ("rule-id", exact_identifier(rule_id, "rule-id").encode()),
        *nested_rows("premise", tuple(_premise_frame(item) for item in premise_values)),
        *nested_rows("assumption", tuple(_assumption_frame(item) for item in assumption_values)),
        ("conclusion", conclusion_value.descriptor_digest.encode()),
    ))
    result = PromotionAuditRequest(
        REQUEST_VERSION, rule_id, premise_values, assumption_values, conclusion_value, value,
    )
    logger.debug("promotion_audit_request exit")
    return result


def _premise_frame(item) -> bytes:
    logger.debug("_premise_frame entry premise=%s", item.premise_name)
    result = frame("veyra.p2s.premise-artifact.v1", (
        ("name", item.premise_name.encode()), ("kind", item.artifact_kind.encode()),
        ("artifact", item.artifact_digest.encode()),
        *nested_rows("index", tuple(frame("veyra.p2s.index-binding.v1", (
            ("name", binding.name.encode()), ("value", binding.value_digest.encode()),
        )) for binding in item.indices)),
        *nested_rows("evidence", tuple(frame("veyra.p2s.evidence-field.v1", (
            ("name", evidence.name.encode()),
            ("value", evidence.evidence_digest.encode()),
        )) for evidence in item.evidence_fields)),
    ))
    logger.debug("_premise_frame exit")
    return result


def _assumption_frame(item: AssumptionNode) -> bytes:
    logger.debug("_assumption_frame entry")
    result = frame("veyra.p2s.assumption.v1", (
        ("id", item.assumption_id.encode()), ("claim", item.claim_id.encode()),
        *text_rows("depends", item.depends_on), ("evidence", item.evidence_digest.encode()),
    ))
    logger.debug("_assumption_frame exit")
    return result


def validate_assumption_node(value: object) -> AssumptionNode:
    logger.debug("validate_assumption_node entry")
    exact_shape(value, AssumptionNode, "assumption-node")
    result = assumption_node(
        value.assumption_id, value.claim_id, value.depends_on, value.evidence_digest,
    )
    if value != result:
        reject("assumption-node-mismatch")
    logger.debug("validate_assumption_node exit")
    return value


def validate_request_shallow(value: object) -> PromotionAuditRequest:
    """Validate only the outer DTO and bounded containers before traversal."""
    logger.debug("validate_request_shallow entry")
    exact_shape(value, PromotionAuditRequest, "audit-request")
    exact_identifier(value.version, "request-version")
    exact_identifier(value.rule_id, "request-rule-id")
    exact_tuple(value.premises, "request-premises")
    exact_tuple(value.assumptions, "request-assumptions")
    exact_shape(value.conclusion, ClaimDescriptor, "request-conclusion")
    exact_digest(value.request_digest, "request-digest")
    logger.debug("validate_request_shallow exit")
    return value


def validate_request_deep(
    value: PromotionAuditRequest, registry: PromotionRegistry,
) -> PromotionAuditRequest:
    logger.debug("validate_request_deep entry")
    validate_request_shallow(value)
    expected = promotion_audit_request(
        value.rule_id, value.premises, value.assumptions, value.conclusion, registry,
    )
    if value != expected:
        reject("request-digest-mismatch")
    logger.debug("validate_request_deep exit")
    return value
def _resource(
    operation: str, request_digest: str, bound: ResourceBound,
    required: int, allowed: int, policy: PromotionAuditPolicy,
) -> PromotionResourceLimit:
    logger.debug("_resource entry bound=%s", bound.value)
    value = digest("veyra.p2s.resource-refusal.v1", (
        ("operation", operation.encode()), ("request", request_digest.encode()),
        ("bound", bound.value.encode()), ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")),
        ("policy", policy.policy_digest.encode()),
    ))
    result = PromotionResourceLimit(
        operation, request_digest, bound, required, allowed, policy.policy_digest, value,
    )
    logger.debug("_resource exit")
    return result


def audit_promotion_request(
    registry: PromotionRegistry, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionAuditResult:
    """Audit exact rule syntax; never establish the rule conclusion itself."""
    logger.debug("audit_promotion_request entry")
    validate_registry(registry)
    validate_policy(policy)
    validate_request_shallow(request)
    if len(request.premises) > policy.max_premises:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.PREMISE_COUNT,
            len(request.premises), policy.max_premises, policy,
        )
    if len(request.assumptions) > policy.max_assumptions:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.ASSUMPTION_COUNT,
            len(request.assumptions), policy.max_assumptions, policy,
        )
    validate_request_deep(request, registry)
    fields = sum(len(item.indices) + len(item.evidence_fields) for item in request.premises)
    fields += len(request.conclusion.indices)
    if fields > policy.max_fields:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.FIELD_COUNT,
            fields, policy.max_fields, policy,
        )
    rules = tuple(item for item in registry.rules if item.rule_id == request.rule_id)
    if len(rules) != 1:
        reject("unknown-or-duplicate-promotion-rule")
    result = _audit_rule(registry, rules[0], request, policy)
    logger.debug("audit_promotion_request exit decision=%s", result.decision.value)
    return result


def _audit_rule(
    registry: PromotionRegistry, rule: PromotionRule, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionSchemaAudit:
    logger.debug("_audit_rule entry rule=%s", rule.rule_id)
    conclusion = request.conclusion
    if (
        conclusion.kind is not rule.output_kind
        or conclusion.status is not rule.output_status
        or conclusion.provenance is not rule.output_provenance
    ):
        reject("conclusion-does-not-match-named-rule")
    if tuple(item.name for item in conclusion.indices) != rule.output_indices:
        reject("conclusion-indices-not-exact")
    if len(request.premises) != len(rule.premise_signatures):
        reject("premise-count-not-exact")
    for artifact, signature in zip(request.premises, rule.premise_signatures):
        if artifact.artifact_kind in rule.forbidden_source_types:
            reject("forbidden-promotion-source")
        if artifact.premise_name != signature.premise_name:
            reject("premise-name-not-exact")
        if artifact.artifact_kind != signature.artifact_kind:
            reject("premise-artifact-kind-not-exact")
        if tuple(item.name for item in artifact.indices) != signature.required_indices:
            reject("premise-indices-not-exact")
        if tuple(item.name for item in artifact.evidence_fields) != (
            signature.required_evidence_fields
        ):
            reject("premise-evidence-fields-not-exact")
    closure = _assumption_closure(request)
    value = digest("veyra.p2s.schema-audit.v1", (
        ("registry", registry.registry_digest.encode()),
        ("rule", rule.rule_digest.encode()),
        ("request", request.request_digest.encode()),
        ("policy", policy.policy_digest.encode()),
        ("conclusion", conclusion.descriptor_digest.encode()),
        *text_rows("premise", tuple(item.artifact_digest for item in request.premises)),
        *text_rows("assumption", closure), *text_rows("nonclaim", rule.permanent_nonclaims),
        ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = PromotionSchemaAudit(
        registry.registry_digest, rule.rule_digest, request.request_digest,
        policy.policy_digest, conclusion, request.premises, closure,
        rule.permanent_nonclaims, MetaAuditDecision.SCHEMA_CONFORMANT, value,
    )
    logger.debug("_audit_rule exit")
    return result


def _assumption_closure(request: PromotionAuditRequest) -> tuple[str, ...]:
    logger.debug("_assumption_closure entry rows=%d", len(request.assumptions))
    nodes = {item.assumption_id: item for item in request.assumptions}
    if len(nodes) != len(request.assumptions):
        reject("duplicate-assumption-id")
    for item in request.assumptions:
        if item.claim_id == request.conclusion.claim_id:
            reject("conclusion-in-assumption-closure")
        if any(dependency not in nodes for dependency in item.depends_on):
            reject("missing-assumption-dependency")
    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(node_id: str) -> None:
        logger.debug("visit entry node=%s", node_id)
        if node_id in visiting:
            reject("cyclic-assumption-dag")
        if node_id not in visited:
            visiting.add(node_id)
            for dependency in nodes[node_id].depends_on:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)
            ordered.append(node_id)
        logger.debug("visit exit node=%s", node_id)

    for node in request.assumptions:
        visit(node.assumption_id)
    result = tuple(ordered)
    logger.debug("_assumption_closure exit rows=%d", len(result))
    return result


def validate_schema_audit(
    value: object, registry: PromotionRegistry, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionSchemaAudit:
    """Freshly replay and compare an exact successful audit DTO."""
    logger.debug("validate_schema_audit entry")
    exact_shape(value, PromotionSchemaAudit, "promotion-schema-audit")
    for name in (
        "registry_digest", "rule_digest", "request_digest", "policy_digest", "audit_digest",
    ):
        exact_digest(getattr(value, name), f"audit-{name}")
    validate_request_deep(request, registry)
    validate_claim_descriptor(value.conclusion, registry)
    exact_tuple(value.premise_artifacts, "audit-premise-artifacts")
    for artifact in value.premise_artifacts:
        validate_premise_artifact(artifact)
    exact_tuple(value.assumption_closure, "audit-assumption-closure")
    exact_tuple(value.nonclaims, "audit-nonclaims")
    for item in value.assumption_closure:
        exact_identifier(item, "audit-assumption-id")
    for item in value.nonclaims:
        exact_identifier(item, "audit-nonclaim")
    if type(value.decision) is not MetaAuditDecision:
        reject("invalid-audit-decision")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-audit-ontology-status")
    exact_identifier(value.scope, "audit-scope")
    expected = audit_promotion_request(registry, request, policy)
    if type(expected) is not PromotionSchemaAudit or value != expected:
        reject("promotion-schema-audit-not-fresh")
    logger.debug("validate_schema_audit exit")
    return value
ORACLE_NONCLAIMS = (
    "ontology-completeness", "codebase-completeness", "retroactive-certification",
    "metaphysical-truth", "automatic-promotion",
)
ORACLE_FORBIDDEN_SOURCE_TYPES = (
    "bool", "digest-only", "old-certificate", "old-judgment", "finite-sample-table",
)
ORACLE_FORBIDDEN_CONCLUSION_FIELDS = (
    "exists", "global_exists", "metaphysically_exists", "proof_complete",
    "observer_independent", "physical_exists",
)
ORACLE_ASSUMPTION_POLICY_ID = "p2-s-acyclic-no-own-conclusion-v1"
ORACLE_STATEMENT_DIGESTS = (
    ("exact-snapshot-v1", "7193ddf2d2598a56b564c952bd80672daa46b01ddfdc023a9fc3dfadadce66a8"),
    ("doctrine-admission-v1", "29acbe874df8dff98f2449d87c15c2733e290029e4b40bb6bc08d09734087f72"),
    ("observer-execution-v1", "77f992c3889b415d3eef066b271f64d7a6f8e7b92c45ed5e3ecc7baa7dce96bc"),
    ("p1-b-finite-generation-v1", "9ec416f62b7fd2281f7c00c960714b89e01618999680fcca4373b07b0c8e45ec"),
    ("compatibility-replay-v1", "9239382e6465ae4cbb7492f9e7a645cf41f6a378dfb707527b05654ddf4f1fac"),
    ("continuation-replay-v1", "860055be19607289ba38e37fe654f8a0814496abe21952496a057bc5b767d2fc"),
    ("oep-observer-role-v1", "699348a474109f33edd49c14fd1d44db8895f204520682965dec71ed6a43b325"),
    ("hap-historical-actualization-v1", "f4204b625e0928e2a544c45fb7d146b740c639fb4bd89f1dd129ae02f33e7a54"),
    ("c2-c3-confluence-v1", "3f02f92e0f3db97a49d1f9969469dbcc88bce74196c672d5dc25ae33fa2e20ea"),
    ("a2-refinement-survival-v1", "250cda395a619a3b175c9163e7da0693f238ba283e778ee8c2e34d649f53d775"),
    ("sfp-scoped-formation-v1", "25da8e2a0ba45baf4cf1cef51e5ef77ba0f6633ad2b00ccbf84d41acf36a51c5"),
    ("afip-formally-derived-v1", "21a48d4860e79f97d5c7d1dd4c2af19ee2c492ad706e3b2247e1e828ddd0f0d3"),
    ("afip-supplied-hypothesis-v1", "aaedeed11fdd116b9ce16d687d570093a24dce0759726b3e94fa0df8900aa2a6"),
    ("afip-oracle-hypothesis-v1", "3db5e7193a0e4de30a07048d3205468c8f4442d5091c54cfc7c79601534218cf"),
    ("pomega-carrier-completion-v1", "821e8c8bac1552c9756c91a1eef564fc5e2b9ba1dbcea47ede5f080157b2d212"),
    ("network-invariance-v1", "f29a09e021441b88e09368ed0119dae9eadbc785d4632f41303b7af47514d3f2"),
    ("empirical-bridge-v1", "0698107b4e9439d9f7e78e760cdd5df65f5f93d69609a5973952221bc8745068"),
)

ORACLE_DOMAIN_ROWS = (
    (K.PRESENTED, (S.ESTABLISHED, S.OPEN), ((S.ESTABLISHED, P.SUPPLIED_PRESENTATION),)),
    (K.ADMISSIBLE, (S.ESTABLISHED_RELATIVE_TO_DOCTRINE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_DOCTRINE, P.DOCTRINE_REPLAY),)),
    (K.OBSERVABLE, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.GENERABLE, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.COHERENT, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.PERSISTENT, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.CONFLUENT, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.REFINEMENT_ROBUST, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_SCOPE, P.FORMALLY_DERIVED))),
    (K.OBSERVER_ROLE, (S.ESTABLISHED_RELATIVE_TO_SCOPE, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_SCOPE, P.DOCTRINE_REPLAY),)),
    (K.HISTORICALLY_ACTUALIZED, (S.ESTABLISHED_RELATIVE_TO_HISTORY, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY),)),
    (K.SCOPED_OBJECT,
     (S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, P.DOCTRINE_REPLAY),)),
    (K.ALL_DEPTH_FAMILY, (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.ASSUMED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),
      (S.ASSUMED, P.SUPPLIED_HYPOTHESIS), (S.ASSUMED, P.ORACLE_DEPENDENT))),
    (K.COMPLETED_CARRIER, (S.ESTABLISHED_RELATIVE_TO_LEDGER, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED),)),
    (K.OBJECTIVELY_STABLE,
     (S.ESTABLISHED_RELATIVE_TO_NETWORK, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_NETWORK, P.EXECUTABLE_REPLAY),
      (S.ESTABLISHED_RELATIVE_TO_NETWORK, P.FORMALLY_DERIVED))),
    (K.PHYSICALLY_INSTANTIATED,
     (S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, S.REFUTED, S.OPEN),
     ((S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE, P.EMPIRICAL_BRIDGE),)),
)

ORACLE_RULE_ROWS = (
    ("exact-snapshot-v1", (("representation", "bounded-representation", ("canonical",),
      ("scope",)),), K.PRESENTED, S.ESTABLISHED, P.SUPPLIED_PRESENTATION,
     ("scope",), ORACLE_NONCLAIMS),
    ("doctrine-admission-v1", (("presentation", "presentation-artifact", ("canonical",),
      ("scope",)), ("doctrine", "doctrine-replay", ("admission",), ("doctrine",))),
     K.ADMISSIBLE, S.ESTABLISHED_RELATIVE_TO_DOCTRINE, P.DOCTRINE_REPLAY,
     ("doctrine", "scope"), ORACLE_NONCLAIMS),
    ("observer-execution-v1", (("coupling", "admitted-coupling", ("response",),
      ("doctrine", "observer")), ("input", "exact-input", ("input",), ("scope",))),
     K.OBSERVABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "observer"), ORACLE_NONCLAIMS),
    ("p1-b-finite-generation-v1", (("seed", "seed-source", ("seed",), ("doctrine",)),
      ("program", "closed-program", ("replay",), ("scope", "stage"))), K.GENERABLE,
     S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "stage"), ORACLE_NONCLAIMS),
    ("compatibility-replay-v1", (("relations", "exact-relations", ("relation-laws",),
      ("doctrine", "scope")), ("restrictions", "exact-restrictions",
      ("restriction-laws",), ("scope",))), K.COHERENT,
     S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope"), ORACLE_NONCLAIMS),
    ("continuation-replay-v1", (("trace", "trace-artifact", ("trace",), ("history",)),
      ("continuation", "named-continuation", ("persistence",), ("scope",))),
     K.PERSISTENT, S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "history"), ORACLE_NONCLAIMS),
    ("oep-observer-role-v1", (("genealogy", "oep-genealogy", ("genealogy",),
      ("scope", "observer")), ("recurrence", "oep-recurrence", ("recurrence",),
      ("scope", "observer")), ("discrimination", "oep-discrimination",
      ("discrimination",), ("scope", "observer")), ("persistence", "oep-persistence",
      ("persistence",), ("scope", "observer")), ("efficacy", "oep-efficacy",
      ("efficacy",), ("scope", "observer"))), K.OBSERVER_ROLE,
     S.ESTABLISHED_RELATIVE_TO_SCOPE, P.DOCTRINE_REPLAY,
     ("doctrine", "scope", "observer"), ORACLE_NONCLAIMS),
    ("hap-historical-actualization-v1", (("oep", "observer-role-artifact", ("role",),
      ("doctrine", "scope", "observer")), ("history", "birth-history",
      ("prior-history", "causal-pressure"), ("history",))), K.HISTORICALLY_ACTUALIZED,
     S.ESTABLISHED_RELATIVE_TO_HISTORY, P.HISTORICAL_REPLAY,
     ("doctrine", "scope", "history", "observer"), ORACLE_NONCLAIMS),
    ("c2-c3-confluence-v1", (("diagrams", "demanded-path-diagrams",
      ("coverage", "commutation"), ("doctrine", "scope", "history")),), K.CONFLUENT,
     S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "history"), ORACLE_NONCLAIMS),
    ("a2-refinement-survival-v1", (("refinement", "genuine-refinement",
      ("strictness", "survival"), ("doctrine", "scope", "refinement")),),
     K.REFINEMENT_ROBUST, S.ESTABLISHED_RELATIVE_TO_SCOPE, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "refinement"), ORACLE_NONCLAIMS),
    ("sfp-scoped-formation-v1", (("construction", "sfp-construction", ("construction",),
      ("doctrine", "scope")), ("support", "sfp-support", ("support",),
      ("doctrine", "scope")), ("g4", "sfp-g4", ("g4",), ("doctrine", "scope")),
      ("persistence", "sfp-persistence", ("persistence",), ("doctrine", "scope")),
      ("confluence", "sfp-confluence", ("confluence",), ("doctrine", "scope")),
      ("refinement", "sfp-refinement", ("refinement",), ("doctrine", "scope"))),
     K.SCOPED_OBJECT, S.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE, P.DOCTRINE_REPLAY,
     ("doctrine", "scope", "history"), ORACLE_NONCLAIMS),
    ("afip-formally-derived-v1", (("totality", "formal-totality-source",
      ("theorem", "formal-source"), ("ledger",)), ("restriction",
      "formal-restriction-laws", ("theorem",), ("family",)), ("ledger",
      "assumption-ledger", ("closure",), ("ledger",))), K.ALL_DEPTH_FAMILY,
     S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED,
     ("doctrine", "ledger", "family"), ORACLE_NONCLAIMS),
    ("afip-supplied-hypothesis-v1", (("hypothesis", "supplied-family-hypothesis",
      ("totality", "compatibility"), ("ledger", "family")),), K.ALL_DEPTH_FAMILY,
     S.ASSUMED, P.SUPPLIED_HYPOTHESIS, ("doctrine", "ledger", "family"),
     ORACLE_NONCLAIMS),
    ("afip-oracle-hypothesis-v1", (("oracle", "total-oracle-hypothesis",
      ("totality", "purity", "stability", "trust"), ("ledger", "family")),),
     K.ALL_DEPTH_FAMILY, S.ASSUMED, P.ORACLE_DEPENDENT,
     ("doctrine", "ledger", "family"), ORACLE_NONCLAIMS),
    ("pomega-carrier-completion-v1", (("carrier", "carrier-formation",
      ("constructor",), ("carrier",)), ("realization", "universal-realization",
      ("theorem",), ("ledger", "carrier")), ("separation", "joint-separation",
      ("theorem",), ("carrier",)), ("nonvacuity", "family-class-witness",
      ("witness",), ("ledger",))), K.COMPLETED_CARRIER,
     S.ESTABLISHED_RELATIVE_TO_LEDGER, P.FORMALLY_DERIVED,
     ("doctrine", "ledger", "carrier"), ORACLE_NONCLAIMS),
    ("network-invariance-v1", (("translations", "network-translations",
      ("preservation", "reflection", "domain"), ("network",)), ("confluence",
      "network-confluence", ("all-demanded",), ("history",)), ("refinements",
      "network-refinements", ("survival", "no-conflict"), ("scope",))),
     K.OBJECTIVELY_STABLE, S.ESTABLISHED_RELATIVE_TO_NETWORK, P.EXECUTABLE_REPLAY,
     ("doctrine", "scope", "network", "history"), ORACLE_NONCLAIMS),
    ("empirical-bridge-v1", (("measurement", "external-measurement",
      ("measurement", "provenance"), ("measurement",)), ("bridge",
      "empirical-doctrine", ("identification",), ("doctrine", "scope"))),
     K.PHYSICALLY_INSTANTIATED, S.ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE,
     P.EMPIRICAL_BRIDGE, ("doctrine", "scope", "measurement"), ORACLE_NONCLAIMS),
)

ORACLE_PREMISE_PROJECTION_TRIPLES = (
    ("p2-project-exact-snapshot-v1-representation-v1", "exact-snapshot-v1", "representation"),
    ("p2-project-doctrine-admission-v1-presentation-v1", "doctrine-admission-v1", "presentation"),
    ("p2-project-doctrine-admission-v1-doctrine-v1", "doctrine-admission-v1", "doctrine"),
    ("p2-project-observer-execution-v1-coupling-v1", "observer-execution-v1", "coupling"),
    ("p2-project-observer-execution-v1-input-v1", "observer-execution-v1", "input"),
    ("p2-project-p1-b-finite-generation-v1-seed-v1", "p1-b-finite-generation-v1", "seed"),
    ("p2-project-p1-b-finite-generation-v1-program-v1", "p1-b-finite-generation-v1", "program"),
    ("p2-project-compatibility-replay-v1-relations-v1", "compatibility-replay-v1", "relations"),
    ("p2-project-compatibility-replay-v1-restrictions-v1", "compatibility-replay-v1", "restrictions"),
    ("p2-project-continuation-replay-v1-trace-v1", "continuation-replay-v1", "trace"),
    ("p2-project-continuation-replay-v1-continuation-v1", "continuation-replay-v1", "continuation"),
    ("p2-project-oep-observer-role-v1-genealogy-v1", "oep-observer-role-v1", "genealogy"),
    ("p2-project-oep-observer-role-v1-recurrence-v1", "oep-observer-role-v1", "recurrence"),
    ("p2-project-oep-observer-role-v1-discrimination-v1", "oep-observer-role-v1", "discrimination"),
    ("p2-project-oep-observer-role-v1-persistence-v1", "oep-observer-role-v1", "persistence"),
    ("p2-project-oep-observer-role-v1-efficacy-v1", "oep-observer-role-v1", "efficacy"),
    ("p2-project-hap-historical-actualization-v1-oep-v1", "hap-historical-actualization-v1", "oep"),
    ("p2-project-hap-historical-actualization-v1-history-v1", "hap-historical-actualization-v1", "history"),
    ("p2-project-c2-c3-confluence-v1-diagrams-v1", "c2-c3-confluence-v1", "diagrams"),
    ("p2-project-a2-refinement-survival-v1-refinement-v1", "a2-refinement-survival-v1", "refinement"),
    ("p2-project-sfp-scoped-formation-v1-construction-v1", "sfp-scoped-formation-v1", "construction"),
    ("p2-project-sfp-scoped-formation-v1-support-v1", "sfp-scoped-formation-v1", "support"),
    ("p2-project-sfp-scoped-formation-v1-g4-v1", "sfp-scoped-formation-v1", "g4"),
    ("p2-project-sfp-scoped-formation-v1-persistence-v1", "sfp-scoped-formation-v1", "persistence"),
    ("p2-project-sfp-scoped-formation-v1-confluence-v1", "sfp-scoped-formation-v1", "confluence"),
    ("p2-project-sfp-scoped-formation-v1-refinement-v1", "sfp-scoped-formation-v1", "refinement"),
    ("p2-project-afip-formally-derived-v1-totality-v1", "afip-formally-derived-v1", "totality"),
    ("p2-project-afip-formally-derived-v1-restriction-v1", "afip-formally-derived-v1", "restriction"),
    ("p2-project-afip-formally-derived-v1-ledger-v1", "afip-formally-derived-v1", "ledger"),
    ("p2-project-afip-supplied-hypothesis-v1-hypothesis-v1", "afip-supplied-hypothesis-v1", "hypothesis"),
    ("p2-project-afip-oracle-hypothesis-v1-oracle-v1", "afip-oracle-hypothesis-v1", "oracle"),
    ("p2-project-pomega-carrier-completion-v1-carrier-v1", "pomega-carrier-completion-v1", "carrier"),
    ("p2-project-pomega-carrier-completion-v1-realization-v1", "pomega-carrier-completion-v1", "realization"),
    ("p2-project-pomega-carrier-completion-v1-separation-v1", "pomega-carrier-completion-v1", "separation"),
    ("p2-project-pomega-carrier-completion-v1-nonvacuity-v1", "pomega-carrier-completion-v1", "nonvacuity"),
    ("p2-project-network-invariance-v1-translations-v1", "network-invariance-v1", "translations"),
    ("p2-project-network-invariance-v1-confluence-v1", "network-invariance-v1", "confluence"),
    ("p2-project-network-invariance-v1-refinements-v1", "network-invariance-v1", "refinements"),
    ("p2-project-empirical-bridge-v1-measurement-v1", "empirical-bridge-v1", "measurement"),
    ("p2-project-empirical-bridge-v1-bridge-v1", "empirical-bridge-v1", "bridge"),
)

ORACLE_INDEX_PROJECTION = (
    "p2-exists-generable-stage-v1", K.GENERABLE,
    ("doctrine", "scope", "stage"), "stage", ("doctrine", "scope"),
)
LITERAL_ORACLE_DIGEST = "2cbe0f2f1f1025696b947c73e32196f230e7748c77c030543d2292a34585875a"


def _plain(value):
    logger.debug("_plain entry type=%s", type(value).__name__)
    if isinstance(value, Enum):
        result = value.value
    elif type(value) is tuple:
        result = [_plain(item) for item in value]
    elif type(value) is str:
        result = value
    else:
        raise TypeError("literal-oracle-unexpected-type")
    logger.debug("_plain exit")
    return result


def compute_literal_oracle_digest() -> str:
    """Commit the separately written literal tables with stdlib canonical JSON."""
    logger.debug("compute_literal_oracle_digest entry")
    payload = {
        "domains": _plain(ORACLE_DOMAIN_ROWS),
        "rules": _plain(ORACLE_RULE_ROWS),
        "statement_digests": _plain(ORACLE_STATEMENT_DIGESTS),
        "forbidden_source_types": _plain(ORACLE_FORBIDDEN_SOURCE_TYPES),
        "forbidden_conclusion_fields": _plain(ORACLE_FORBIDDEN_CONCLUSION_FIELDS),
        "assumption_policy_id": ORACLE_ASSUMPTION_POLICY_ID,
        "premise_projections": _plain(ORACLE_PREMISE_PROJECTION_TRIPLES),
        "index_projection": _plain(ORACLE_INDEX_PROJECTION),
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    result = sha256(encoded).hexdigest()
    logger.debug("compute_literal_oracle_digest exit digest=%s", result[:12])
    return result


def audit_registry_against_literal_oracle(registry: PromotionRegistry) -> str:
    """Reject any generated registry cell that differs from literal review data."""
    logger.debug("audit_registry_against_literal_oracle entry")
    validate_registry(registry)
    if compute_literal_oracle_digest() != LITERAL_ORACLE_DIGEST:
        reject("literal-oracle-digest-drift")
    if len(ORACLE_DOMAIN_ROWS) != 15 or len(ORACLE_RULE_ROWS) != 17:
        reject("literal-oracle-cardinality-drift")
    domains = tuple(
        (
            item.kind, item.allowed_statuses,
            tuple((pair.status, pair.provenance) for pair in item.positive_pairs),
        )
        for item in registry.domains
    )
    if domains != ORACLE_DOMAIN_ROWS:
        reject("registry-domain-oracle-mismatch")
    statement_ids = tuple(item[0] for item in ORACLE_STATEMENT_DIGESTS)
    if statement_ids != tuple(item[0] for item in ORACLE_RULE_ROWS):
        reject("literal-oracle-statement-order-drift")
    statement_digests = dict(ORACLE_STATEMENT_DIGESTS)
    expected_rules = tuple((
        row[0], statement_digests[row[0]], row[1], row[2], row[3], row[4], row[5],
        ORACLE_FORBIDDEN_SOURCE_TYPES, ORACLE_FORBIDDEN_CONCLUSION_FIELDS,
        ORACLE_ASSUMPTION_POLICY_ID, row[6],
    ) for row in ORACLE_RULE_ROWS)
    rules = tuple(
        (
            item.rule_id, item.statement_digest,
            tuple((
                premise.premise_name, premise.artifact_kind,
                premise.required_evidence_fields, premise.required_indices,
            ) for premise in item.premise_signatures),
            item.output_kind, item.output_status, item.output_provenance,
            item.output_indices, item.forbidden_source_types,
            item.forbidden_conclusion_fields, item.assumption_policy_id,
            item.permanent_nonclaims,
        )
        for item in registry.rules
    )
    if rules != expected_rules:
        reject("registry-rule-oracle-mismatch")
    triples = tuple(
        (item.projection_id, item.source_rule_id, item.premise_name)
        for item in registry.premise_projections
    )
    if (
        len(triples) != 40 or len(set(triples)) != 40
        or len({item[0] for item in triples}) != 40
        or triples != ORACLE_PREMISE_PROJECTION_TRIPLES
    ):
        reject("registry-premise-projection-oracle-mismatch")
    if len(registry.index_projections) != 1:
        reject("registry-index-projection-count-mismatch")
    item = registry.index_projections[0]
    actual_index = (
        item.projection_id, item.kind, item.input_indices,
        item.hidden_index, item.retained_indices,
    )
    if actual_index != ORACLE_INDEX_PROJECTION:
        reject("registry-index-projection-oracle-mismatch")
    logger.debug("audit_registry_against_literal_oracle exit")
    return LITERAL_ORACLE_DIGEST
def project_premise_artifact(
    registry: PromotionRegistry, request: PromotionAuditRequest,
    audit: PromotionSchemaAudit, projection_id: str, policy: PromotionAuditPolicy,
) -> PremiseProjection:
    """Return the original premise artifact through an explicit named rule."""
    logger.debug("project_premise_artifact entry projection=%s", projection_id)
    validate_registry(registry)
    validate_schema_audit(audit, registry, request, policy)
    rules = tuple(item for item in registry.premise_projections if (
        item.projection_id == projection_id
    ))
    if len(rules) != 1 or rules[0].source_rule_id != request.rule_id:
        reject("invalid-premise-projection-rule")
    artifacts = tuple(item for item in request.premises if (
        item.premise_name == rules[0].premise_name
    ))
    if len(artifacts) != 1:
        reject("projected-premise-not-exact")
    value = digest("veyra.p2s.premise-projection.v1", (
        ("rule", rules[0].projection_digest.encode()),
        ("audit", audit.audit_digest.encode()),
        ("artifact", artifacts[0].artifact_digest.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = PremiseProjection(
        rules[0].projection_digest, audit.audit_digest, artifacts[0], value,
    )
    logger.debug("project_premise_artifact exit")
    return result


def project_index_existential(
    registry: PromotionRegistry, descriptor: ClaimDescriptor, projection_id: str,
) -> IndexProjection:
    """Hide exactly one named index while retaining an auditable binding."""
    logger.debug("project_index_existential entry projection=%s", projection_id)
    validate_registry(registry)
    validate_claim_descriptor(descriptor, registry)
    rules = tuple(item for item in registry.index_projections if (
        item.projection_id == projection_id
    ))
    if len(rules) != 1 or descriptor.kind is not rules[0].kind:
        reject("invalid-index-projection-rule")
    names = tuple(item.name for item in descriptor.indices)
    if names != rules[0].input_indices:
        reject("index-projection-input-not-exact")
    hidden = tuple(item for item in descriptor.indices if item.name == rules[0].hidden_index)
    retained = tuple(item for item in descriptor.indices if item.name in rules[0].retained_indices)
    if len(hidden) != 1 or tuple(item.name for item in retained) != rules[0].retained_indices:
        reject("index-projection-loss-not-named")
    value = digest("veyra.p2s.index-projection.v1", (
        ("rule", rules[0].projection_digest.encode()),
        ("source", descriptor.descriptor_digest.encode()),
        *text_rows("retained", tuple(item.value_digest for item in retained)),
        ("hidden-name", hidden[0].name.encode()),
        ("hidden-value", hidden[0].value_digest.encode()),
        ("existential", b"true"),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = IndexProjection(
        rules[0].projection_digest, descriptor, retained, hidden[0], True, value,
    )
    logger.debug("project_index_existential exit")
    return result


def validate_index_projection(
    value: object, registry: PromotionRegistry, projection_id: str,
) -> IndexProjection:
    logger.debug("validate_index_projection entry")
    exact_shape(value, IndexProjection, "index-projection")
    exact_digest(value.projection_rule_digest, "index-projection-rule-digest")
    validate_claim_descriptor(value.source_descriptor, registry)
    exact_tuple(value.retained_indices, "index-projection-retained")
    for item in value.retained_indices:
        exact_shape(item, IndexBinding, "retained-index")
        index_binding(item.name, item.value_digest)
    exact_shape(value.hidden_binding, IndexBinding, "hidden-binding")
    index_binding(value.hidden_binding.name, value.hidden_binding.value_digest)
    exact_bool(value.existential, "projection-existential")
    exact_digest(value.projection_digest, "index-projection-digest")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-index-projection-ontology-status")
    expected = project_index_existential(registry, value.source_descriptor, projection_id)
    if value != expected:
        reject("index-projection-not-fresh")
    logger.debug("validate_index_projection exit")
    return value
SCHEMA_AUDIT_SCOPE = "fixed-allowlist-five-only"
SCHEMA_AUDIT_NONCLAIMS = (
    "codebase-completeness", "ontology-correctness", "retroactive-certification",
)

_ALLOWLIST = {
    "finite-construction-judgment": FiniteConstructionJudgment,
    "observer-genesis-judgment": GenesisJudgment,
    "fork-confluence-judgment": ForkConfluenceJudgment,
    "finite-confluence-aggregate": FiniteConfluenceAggregate,
    "all-depth-family-judgment": AllDepthFamilyJudgment,
}
_SCHEMA_REQUEST_DIGEST = digest("veyra.p2s.schema-audit-request.v1", (
    ("allowlist", b"p2-s-fixed-five-v1"),
))


def audit_allowlisted_schemas(
    registry: PromotionRegistry, policy: PromotionAuditPolicy,
) -> SchemaAuditReport | PromotionResourceLimit:
    """Inspect only five direct classes after fixed-count preflight."""
    logger.debug("audit_allowlisted_schemas entry")
    validate_registry(registry)
    validate_policy(policy)
    schema_count = len(registry.schema_targets)
    if schema_count > policy.max_schemas:
        return _resource(
            "schema-audit", _SCHEMA_REQUEST_DIGEST, ResourceBound.SCHEMA_COUNT,
            schema_count, policy.max_schemas, policy,
        )
    field_count = sum(len(item.exact_fields) for item in registry.schema_targets)
    if field_count > policy.max_fields:
        return _resource(
            "schema-audit", _SCHEMA_REQUEST_DIGEST, ResourceBound.FIELD_COUNT,
            field_count, policy.max_fields, policy,
        )
    rows = tuple(_audit_target(target) for target in registry.schema_targets)
    report_digest = digest("veyra.p2s.schema-audit-report.v1", (
        ("registry", registry.registry_digest.encode()),
        ("policy", policy.policy_digest.encode()),
        *text_rows("row", tuple(item.row_digest for item in rows)),
        ("scope", SCHEMA_AUDIT_SCOPE.encode()),
        *text_rows("nonclaim", SCHEMA_AUDIT_NONCLAIMS),
        ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = SchemaAuditReport(
        registry.registry_digest, policy.policy_digest, rows,
        SCHEMA_AUDIT_SCOPE, SCHEMA_AUDIT_NONCLAIMS, report_digest,
        MetaAuditDecision.SCHEMA_CONFORMANT,
    )
    logger.debug("audit_allowlisted_schemas exit rows=%d", len(rows))
    return result


def validate_schema_audit_report(
    value: object, registry: PromotionRegistry, policy: PromotionAuditPolicy,
) -> SchemaAuditReport:
    """Validate the exact scoped meta-report before canonical equality."""
    logger.debug("validate_schema_audit_report entry")
    exact_shape(value, SchemaAuditReport, "schema-audit-report")
    exact_digest(value.registry_digest, "schema-report-registry-digest")
    exact_digest(value.policy_digest, "schema-report-policy-digest")
    exact_tuple(value.rows, "schema-report-rows")
    for row in value.rows:
        exact_shape(row, SchemaAuditRow, "schema-audit-row")
        exact_identifier(row.schema_id, "schema-row-id")
        exact_bool(row.exact_match, "schema-row-exact-match")
        exact_bool(row.forbidden_fields_absent, "schema-row-forbidden-absent")
        exact_digest(row.row_digest, "schema-row-digest")
    exact_identifier(value.scope, "schema-report-scope")
    exact_tuple(value.nonclaims, "schema-report-nonclaims", nonempty=True)
    for nonclaim in value.nonclaims:
        exact_identifier(nonclaim, "schema-report-nonclaim")
    exact_digest(value.report_digest, "schema-report-digest")
    if type(value.decision) is not MetaAuditDecision:
        reject("invalid-schema-report-decision")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-schema-report-ontology-status")
    expected = audit_allowlisted_schemas(registry, policy)
    if type(expected) is not SchemaAuditReport or value != expected:
        reject("schema-audit-report-not-fresh")
    logger.debug("validate_schema_audit_report exit")
    return value


def _audit_target(target) -> SchemaAuditRow:
    logger.debug("_audit_target entry schema=%s", target.schema_id)
    dto_type = _ALLOWLIST.get(target.schema_id)
    if dto_type is None:
        reject("schema-target-not-allowlisted")
    actual = tuple(item.name for item in fields(dto_type))
    exact_match = actual == target.exact_fields
    forbidden_absent = not set(actual).intersection(target.forbidden_positive_fields)
    if not exact_match or not forbidden_absent:
        reject("allowlisted-schema-drift")
    row_digest = digest("veyra.p2s.schema-audit-row.v1", (
        ("schema", target.schema_id.encode()), *text_rows("actual", actual),
        ("exact", b"true"), ("forbidden-absent", b"true"),
    ))
    result = SchemaAuditRow(target.schema_id, True, True, row_digest)
    logger.debug("_audit_target exit schema=%s", target.schema_id)
    return result
_ATTACK_ROWS = (
    ("presented-to-object", K.PRESENTED, K.SCOPED_OBJECT, "missing-sfp"),
    ("observation-to-role", K.OBSERVABLE, K.OBSERVER_ROLE, "response-is-not-role"),
    ("role-to-history", K.OBSERVER_ROLE, K.HISTORICALLY_ACTUALIZED, "missing-history"),
    ("role-to-physical", K.OBSERVER_ROLE, K.PHYSICALLY_INSTANTIATED, "missing-bridge"),
    ("generation-to-confluence", K.GENERABLE, K.CONFLUENT, "missing-paths"),
    ("cell-to-all-confluence", K.COHERENT, K.CONFLUENT, "one-cell-not-all-paths"),
    ("sample-to-robustness", K.PERSISTENT, K.REFINEMENT_ROBUST, "sample-not-network"),
    ("finite-to-all-depth", K.GENERABLE, K.ALL_DEPTH_FAMILY, "finite-not-totality"),
    ("family-to-carrier", K.ALL_DEPTH_FAMILY, K.COMPLETED_CARRIER, "missing-cip"),
    ("silence-to-refutation", K.OBSERVABLE, K.ADMISSIBLE, "silence-is-not-refutation"),
    ("higher-cast-down", K.SCOPED_OBJECT, K.GENERABLE, "missing-premise-projection"),
    ("qa-to-metaphysics", K.PRESENTED, K.PHYSICALLY_INSTANTIATED, "qa-is-not-ontology"),
)


def adjacent_cast_attack_matrix(registry: PromotionRegistry) -> CastAttackMatrixReport:
    """Prove the fixed twelve bare-status casts have no registry constructor."""
    logger.debug("adjacent_cast_attack_matrix entry")
    validate_registry(registry)
    rows = tuple(_attack_row(registry, *spec) for spec in _ATTACK_ROWS)
    value = digest("veyra.p2s.cast-attack-report.v1", (
        ("registry", registry.registry_digest.encode()),
        *text_rows("row", tuple(item.row_digest for item in rows)),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = CastAttackMatrixReport(registry.registry_digest, rows, value)
    logger.debug("adjacent_cast_attack_matrix exit rows=%d", len(rows))
    return result


def _attack_row(
    registry: PromotionRegistry, attack_id: str, weaker: K, stronger: K, reason: str,
) -> CastAttackRow:
    logger.debug("_attack_row entry attack=%s", attack_id)
    attack_digest = digest("veyra.p2s.cast-attack.v1", (
        ("id", attack_id.encode()), ("weaker", weaker.value.encode()),
        ("stronger", stronger.value.encode()), ("reason", reason.encode()),
    ))
    attack = CastAttack(attack_id, weaker, stronger, reason, attack_digest)
    forbidden_kind = f"bare-{weaker.value}-status"
    count = sum(
        1 for rule in registry.rules
        if rule.output_kind is stronger
        and len(rule.premise_signatures) == 1
        and rule.premise_signatures[0].artifact_kind == forbidden_kind
    )
    if count != 0:
        raise AssertionError("bare-status-cast-entered-registry")
    row_digest = digest("veyra.p2s.cast-attack-row.v1", (
        ("attack", attack_digest.encode()),
        ("outcome", CastAttackOutcome.REJECTED.value.encode()),
        ("matching", count.to_bytes(8, "big")),
    ))
    result = CastAttackRow(attack, CastAttackOutcome.REJECTED, count, row_digest)
    logger.debug("_attack_row exit attack=%s", attack_id)
    return result
