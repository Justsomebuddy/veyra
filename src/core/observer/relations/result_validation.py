"""Fresh raw-input revalidation for returned P1-A2 artifacts."""

from __future__ import annotations

import logging
from enum import Enum

from ..morphism import ObserverSourceBinding
from .types import (
    ObserverRelationResult, RelationResourceLimit, RelationResourcePolicy,
)
from .runtime import observer_relation_judgment
from .types import (
    DomainWitness, ObserverRelationJudgment, ObserverRelationScope,
    RelationEvaluationSource, RelationPairRow, RelationWitness,
    StageObservationRow, TranslationAssessment, TranslationInput,
    TranslationTriangleRow,
)
from ...ontology.types import ObserverDoctrine
from .validation import reject

logger = logging.getLogger(__name__)


def validate_observer_relation_result(
    doctrine: ObserverDoctrine, raw_observer_source: ObserverSourceBinding,
    raw_stage_source: RelationEvaluationSource, raw_scope: ObserverRelationScope,
    forward: TranslationInput | None, reverse: TranslationInput | None,
    policy: RelationResourcePolicy, raw_result: ObserverRelationResult,
) -> ObserverRelationResult:
    """Recompute from raw evidence and return a fresh exact expected artifact."""
    logger.debug("validate_observer_relation_result entry")
    expected = observer_relation_judgment(
        doctrine, raw_observer_source, raw_stage_source, raw_scope,
        forward, reverse, policy,
    )
    if type(raw_result) is not type(expected):
        reject("relation-result-variant-drift")
    if type(expected) is RelationResourceLimit:
        _validate_refusal_outer(raw_result, expected)
    elif type(expected) is ObserverRelationJudgment:
        _validate_judgment(raw_result, expected)
    else:
        reject("unknown-relation-result-variant")
    logger.debug("validate_observer_relation_result exit type=%s", type(expected).__name__)
    return expected


def _validate_refusal_outer(
    raw: RelationResourceLimit, expected: RelationResourceLimit,
) -> None:
    """Compare fixed refusal fields before any attacker-controlled hashing."""
    logger.debug("validate relation refusal entry")
    _exact_dataclass(raw, RelationResourceLimit, "relation-refusal")
    _nonclaims(raw.nonclaims, expected.nonclaims, "relation-refusal-nonclaims-drift")
    _same_fields(raw, expected, (
        ("operation", type(expected.operation)), ("status", type(expected.status)),
        ("policy_version", str), ("policy_digest", str),
        ("doctrine_fingerprint", str), ("observer_source_digest", str),
        ("stage_source_digest", str), ("scope_digest", str),
        ("required_cost", int), ("allowed_cost", int),
        ("required_encoded_bytes", int), ("allowed_encoded_bytes", int),
        ("observer_independent_identity", type(expected.observer_independent_identity)),
        ("universal_refinement", type(expected.universal_refinement)),
        ("refusal_digest", str),
    ), "relation-refusal-outer-precheck")
    logger.debug("validate relation refusal exit")


def _validate_judgment(
    raw: ObserverRelationJudgment, expected: ObserverRelationJudgment,
) -> None:
    """Bind outer lengths/statuses/digests before walking bounded nested rows."""
    logger.debug("validate relation judgment entry")
    _exact_dataclass(raw, ObserverRelationJudgment, "relation-judgment")
    if (
        type(raw.observations) is not tuple or type(raw.pairs) is not tuple
        or type(raw.forward) is not TranslationAssessment
        or type(raw.reverse) is not TranslationAssessment
        or type(raw.forward.triangles) is not tuple
        or type(raw.reverse.triangles) is not tuple
    ):
        reject("relation-judgment-outer-precheck")
    _same_fields(raw, expected, (
        ("doctrine_fingerprint", str), ("observer_source_digest", str),
        ("stage_source_digest", str), ("scope_digest", str),
        ("preservation", type(expected.preservation)),
        ("reflection", type(expected.reflection)),
        ("domain_equality", type(expected.domain_equality)),
        ("classification", type(expected.classification)),
        ("structural_invertibility", type(expected.structural_invertibility)),
        ("information_loss", type(expected.information_loss)),
        ("coverage", type(expected.coverage)), ("charged_checks", int),
        ("observer_independent_identity", type(expected.observer_independent_identity)),
        ("universal_refinement", type(expected.universal_refinement)),
        ("judgment_digest", str),
    ), "relation-judgment-outer-precheck")
    _nonclaims(raw.nonclaims, expected.nonclaims, "relation-judgment-nonclaims-drift")
    lengths = (
        len(raw.observations), len(raw.pairs), len(raw.forward.triangles),
        len(raw.reverse.triangles),
    )
    expected_lengths = (
        len(expected.observations), len(expected.pairs),
        len(expected.forward.triangles), len(expected.reverse.triangles),
    )
    if lengths != expected_lengths:
        reject("relation-judgment-outer-precheck")
    _tuple_rows(raw.observations, expected.observations, StageObservationRow, "observation")
    _tuple_rows(raw.pairs, expected.pairs, RelationPairRow, "pair")
    _assessment(raw.forward, expected.forward, "forward")
    _assessment(raw.reverse, expected.reverse, "reverse")
    _optional(raw.preservation_witness, expected.preservation_witness, RelationWitness, "preservation")
    _optional(raw.reflection_witness, expected.reflection_witness, RelationWitness, "reflection")
    _optional(raw.domain_witness, expected.domain_witness, DomainWitness, "domain")
    logger.debug("validate relation judgment exit")


def _assessment(
    raw: TranslationAssessment, expected: TranslationAssessment, lane: str,
) -> None:
    """Compare one exact assessment after its triangle count was outer-bound."""
    logger.debug("validate relation assessment entry lane=%s", lane)
    _exact_dataclass(raw, TranslationAssessment, f"{lane}-assessment")
    if type(raw.triangles) is not tuple:
        reject(f"relation-{lane}-assessment-drift")
    _same_fields(raw, expected, (
        ("input_kind", type(expected.input_kind)), ("input_commitment", str),
        ("morphism_status", type(expected.morphism_status)),
        ("proposal_status", type(expected.proposal_status)),
        ("translation_digest", str),
    ), f"relation-{lane}-assessment-drift")
    _tuple_rows(
        raw.triangles, expected.triangles, TranslationTriangleRow,
        f"{lane}-triangle",
    )
    _optional(raw.conflict, expected.conflict, TranslationTriangleRow, f"{lane}-conflict")
    logger.debug("validate relation assessment exit lane=%s", lane)


def _tuple_rows(raw: object, expected: tuple, kind: type, field: str) -> None:
    """Compare a pre-bound exact tuple without duck/subclass acceptance."""
    logger.debug("validate relation tuple entry field=%s", field)
    if type(raw) is not tuple or len(raw) != len(expected):
        reject(f"relation-{field}-outer-precheck")
    for supplied, wanted in zip(raw, expected, strict=True):
        if kind is StageObservationRow:
            _observation_row(supplied, wanted, field)
        elif kind is RelationPairRow:
            _pair_row(supplied, wanted, field)
        elif kind is TranslationTriangleRow:
            _triangle_row(supplied, wanted, field)
        else:
            reject(f"relation-{field}-unknown-row-kind")
    logger.debug("validate relation tuple exit field=%s", field)


def _optional(raw: object, expected: object, kind: type, field: str) -> None:
    """Compare one exact optional witness variant."""
    logger.debug("validate relation optional entry field=%s", field)
    if expected is None:
        if raw is not None:
            reject(f"relation-{field}-witness-drift")
    else:
        if kind is RelationWitness:
            _relation_witness(raw, expected, field)
        elif kind is DomainWitness:
            _domain_witness(raw, expected, field)
        elif kind is TranslationTriangleRow:
            _triangle_row(raw, expected, field)
        else:
            reject(f"relation-{field}-unknown-witness-kind")
    logger.debug("validate relation optional exit field=%s", field)


def _exact_dataclass(value: object, kind: type, field: str) -> None:
    """Enforce exact frozen DTO type before field/equality access."""
    logger.debug("validate relation exact type entry field=%s", field)
    if type(value) is not kind:
        reject(f"relation-{field}-must-be-exact")
    logger.debug("validate relation exact type exit field=%s", field)


def _nonclaims(raw: object, expected: tuple[str, ...], reason: str) -> None:
    """Validate the exact ordered permanent-nonclaim allowlist."""
    logger.debug("validate relation nonclaims entry")
    if type(raw) is not tuple or len(raw) != len(expected):
        reject(reason)
    if any(type(item) is not str for item in raw) or raw != expected:
        reject(reason)
    logger.debug("validate relation nonclaims exit count=%d", len(expected))


def _same_fields(
    raw: object, expected: object, schema: tuple[tuple[str, type], ...], reason: str,
) -> None:
    """Compare exact primitive/enum fields; never use coercive dataclass equality."""
    logger.debug("validate relation same_fields entry reason=%s", reason)
    for name, kind in schema:
        supplied, wanted = getattr(raw, name), getattr(expected, name)
        if type(supplied) is not kind:
            reject(reason)
        if issubclass(kind, Enum):
            if supplied is not wanted:
                reject(reason)
        elif supplied != wanted:
            reject(reason)
    logger.debug("validate relation same_fields exit reason=%s", reason)


def _stage_key(raw: object, expected: object, field: str) -> None:
    """Validate an exact two-string stage key."""
    logger.debug("validate relation stage_key entry field=%s", field)
    if type(raw) is not tuple or type(expected) is not tuple or len(raw) != 2:
        reject(f"relation-{field}-stage-key-drift")
    if any(type(item) is not str for item in raw) or raw != expected:
        reject(f"relation-{field}-stage-key-drift")
    logger.debug("validate relation stage_key exit field=%s", field)


def _observation_row(raw: object, expected: object, field: str) -> None:
    """Validate one exact observation row field-by-field."""
    logger.debug("validate relation observation_row entry")
    _exact_dataclass(raw, StageObservationRow, field)
    _stage_key(raw.stage, expected.stage, field)
    _same_fields(raw, expected, (
        ("fine_status", type(expected.fine_status)),
        ("coarse_status", type(expected.coarse_status)),
        ("fine_payload_digest", str), ("coarse_payload_digest", str),
        ("row_digest", str),
    ), f"relation-{field}-drift")
    logger.debug("validate relation observation_row exit")


def _pair_row(raw: object, expected: object, field: str) -> None:
    """Validate one exact ordered-pair row field-by-field."""
    logger.debug("validate relation pair_row entry")
    _exact_dataclass(raw, RelationPairRow, field)
    _stage_key(raw.left, expected.left, field)
    _stage_key(raw.right, expected.right, field)
    _same_fields(raw, expected, (
        ("pair_index", int), ("fine_outcome", type(expected.fine_outcome)),
        ("coarse_outcome", type(expected.coarse_outcome)),
        ("fine_left_payload", str), ("fine_right_payload", str),
        ("coarse_left_payload", str), ("coarse_right_payload", str),
        ("row_digest", str),
    ), f"relation-{field}-drift")
    logger.debug("validate relation pair_row exit")


def _triangle_row(raw: object, expected: object, field: str) -> None:
    """Validate one exact response triangle field-by-field."""
    logger.debug("validate relation triangle_row entry")
    _exact_dataclass(raw, TranslationTriangleRow, field)
    _stage_key(raw.stage, expected.stage, field)
    _same_fields(raw, expected, (
        ("stage_index", int), ("status", type(expected.status)),
        ("fine_payload_digest", str), ("translated_payload_digest", str),
        ("coarse_payload_digest", str), ("row_digest", str),
    ), f"relation-{field}-drift")
    logger.debug("validate relation triangle_row exit")


def _relation_witness(raw: object, expected: object, field: str) -> None:
    """Validate one exact implication witness."""
    logger.debug("validate relation witness row entry")
    _exact_dataclass(raw, RelationWitness, field)
    _stage_key(raw.left, expected.left, field)
    _stage_key(raw.right, expected.right, field)
    _same_fields(raw, expected, (("pair_index", int), ("row_digest", str)), f"relation-{field}-witness-drift")
    logger.debug("validate relation witness row exit")


def _domain_witness(raw: object, expected: object, field: str) -> None:
    """Validate one exact asymmetric-domain witness."""
    logger.debug("validate relation domain witness entry")
    _exact_dataclass(raw, DomainWitness, field)
    _stage_key(raw.stage, expected.stage, field)
    _same_fields(raw, expected, (
        ("stage_index", int), ("fine_status", type(expected.fine_status)),
        ("coarse_status", type(expected.coarse_status)), ("row_digest", str),
    ), f"relation-{field}-witness-drift")
    logger.debug("validate relation domain witness exit")
