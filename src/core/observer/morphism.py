"""Provisional P1-A structural observer morphisms over the closed R11 core.

One concept end to end: the immutable source binding, the structural response
translation it authorises, the exact R11 domain thresholds, and the judgment
that separates information factorization on the comparison domain from the
stronger domain inclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import logging
from typing import NoReturn

from ..observer_core_codec import canonical_observer_bytes, decode_observer
from ..observer_core_kernel import crest_observer, tail_observer
from ..observer_core_semantics import observe
from ..observer_core_support import response_data
from ..observer_core_types import (
    Apply, Input, LeafKind, MarkValue, Pair, PairKind, PairValue,
    PrimitiveId, Ready, RecurrenceValue, ResponseKind, ResponseValue,
)
from ..ontology.core import internal_observer
from ..ontology.doctrine import observer_doctrine, snapshot_observer_doctrine
from ..ontology.response import _snapshot_response
from ..ontology.types import InternalObserver, ObserverDoctrine
from ..ontology.validation import PositiveOntologyValidationError
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)
MAX_P1A_ID_BYTES = 128
MAX_P1A_PROJECTION = 128
P1A_DOCTRINE_VERSION = "p1a-v1"


class ProjectionStep(str, Enum):
    """Structural response projection through a product observer."""

    LEFT = "left"
    RIGHT = "right"


class MorphismStatus(str, Enum):
    """Outcomes relative to one explicitly declared structural projection."""

    STRONG = "strong"
    INFORMATION_ONLY = "information-only"
    INCOMPARABLE = "incomparable"


class InformationLoss(str, Enum):
    """Conservative structural information-loss classification."""

    LOSSLESS_IDENTITY = "lossless-identity"
    DROPS_PAIR_COMPONENTS = "drops-pair-components"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ObserverSourceBinding:
    """Immutable doctrine membership binding; never a chronology receipt."""

    binding_id: str
    doctrine_fingerprint: str
    observer_ids: tuple[str, ...]
    observer_digests: tuple[str, ...]
    membership_digest: str
    scope: str = "immutability-membership-not-chronology"


@dataclass(frozen=True)
class R11DomainProfile:
    """Exact minimum recurrence depth for one closed R11 observer domain."""

    observer_id: str
    minimum_pulse_depth: int
    nonempty_witness_depth: int
    structurally_confirmed: bool
    scope: str = "closed-r11-minimum-pulse-domain"


@dataclass(frozen=True)
class ComparisonDomain:
    """The confirmed intersection Dom(fine) intersect Dom(coarse)."""

    fine_minimum_depth: int
    coarse_minimum_depth: int
    witness_depth: int
    confirmed_nonempty: bool
    scope: str = "exact-r11-domain-intersection"


@dataclass(frozen=True)
class ResponseTranslation:
    """A doctrine-bound structural fine-to-coarse response projection."""

    translation_id: str
    doctrine_fingerprint: str
    source_binding_digest: str
    fine_observer_id: str
    coarse_observer_id: str
    projection: tuple[ProjectionStep, ...]
    fine_kind: ResponseKind
    coarse_kind: ResponseKind
    translation_digest: str
    scope: str = "closed-r11-pair-projection"


@dataclass(frozen=True)
class ObserverMorphismJudgment:
    """Information factorization on C plus the separate strong-domain test."""

    morphism_id: str
    doctrine_fingerprint: str
    source_binding_digest: str
    fine_observer_id: str
    coarse_observer_id: str
    fine_domain: R11DomainProfile
    coarse_domain: R11DomainProfile
    comparison_domain: ComparisonDomain
    translation: ResponseTranslation | None
    information_factorizes_on_comparison: bool
    coarse_domain_in_fine_domain: bool
    witness_checked: bool
    information_loss: InformationLoss
    status: MorphismStatus
    obstruction: str
    scope: str = "provisional-p1a-observer-morphism"


class ObserverMorphismValidationError(ValueError):
    """An exact P1-A representation or binding contract was violated."""


def _project_observer(
    observer: object, projection: tuple[ProjectionStep, ...]
) -> object | None:
    """Follow an exact structural Pair path; empty path is identity."""
    logger.debug("_project_observer entry steps=%d", len(projection))
    cursor = observer
    for step in projection:
        if type(cursor) is not Pair:
            logger.debug("_project_observer exit factorizes=False")
            return None
        cursor = cursor.left if step is ProjectionStep.LEFT else cursor.right
    logger.debug("_project_observer exit factorizes=True")
    return cursor


def _projection_factorizes(
    doctrine: ObserverDoctrine,
    fine_id: str,
    coarse_id: str,
    projection: tuple[ProjectionStep, ...],
) -> bool:
    """Check exact canonical endpoint equality for one declared projection."""
    logger.debug("_projection_factorizes entry")
    members = {item.observer_id: item for item in doctrine.observers}
    endpoint = _project_observer(decode_observer(members[fine_id].canonical), projection)
    result = (
        endpoint is not None
        and canonical_observer_bytes(endpoint) == members[coarse_id].canonical
    )
    logger.debug("_projection_factorizes exit result=%s", result)
    return result


def snapshot_morphism_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Normalize lower-layer doctrine failures into the P1-A boundary."""
    logger.debug("snapshot_morphism_doctrine entry")
    try:
        result = snapshot_observer_doctrine(value)
    except PositiveOntologyValidationError as exc:
        logger.error("snapshot_morphism_doctrine rejected")
        raise ObserverMorphismValidationError("invalid-morphism-doctrine") from exc
    logger.debug("snapshot_morphism_doctrine exit")
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("observer morphism rejected reason=%s", reason)
    raise ObserverMorphismValidationError(reason)


def snapshot_p1a_identifier(value: str, field: str) -> str:
    """Capture a bounded exact identifier without hostile formatting."""
    logger.debug("snapshot_p1a_identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_P1A_ID_BYTES:
        _reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        _reject(f"invalid-{field}")
    if size > MAX_P1A_ID_BYTES:
        _reject(f"invalid-{field}")
    logger.debug("snapshot_p1a_identifier exit field=%s bytes=%d", field, size)
    return value


def snapshot_projection(value: tuple[ProjectionStep, ...]) -> tuple[ProjectionStep, ...]:
    """Capture one exact bounded projection, including empty identity."""
    logger.debug("snapshot_projection entry")
    if type(value) is not tuple or len(value) > MAX_P1A_PROJECTION:
        _reject("invalid-projection")
    if any(type(item) is not ProjectionStep for item in value):
        _reject("invalid-projection-step")
    result = tuple(value)
    logger.debug("snapshot_projection exit steps=%d", len(result))
    return result


def response_kind_signature(value: ResponseKind) -> tuple[str, ...]:
    """Encode an exact bounded response kind without tuple-sentinel collision."""
    logger.debug("response_kind_signature entry")
    stack: list[tuple[bool, object]] = [(False, value)]
    active: set[int] = set()
    output: list[str] = []
    nodes = 0
    while stack:
        closing, node = stack.pop()
        if closing:
            active.discard(id(node))
            output.append("pair-close")
            continue
        nodes += 1
        if nodes > 256:
            _reject("response-kind-resource-limit")
        if type(node) is LeafKind:
            output.append(node.value)
            continue
        if type(node) is not PairKind or id(node) in active:
            _reject("invalid-response-kind")
        try:
            left, right = node.left, node.right
        except AttributeError:
            _reject("response-kind-missing-fields")
        active.add(id(node))
        output.append("pair-open")
        stack.extend(((True, node), (False, right), (False, left)))
    result = tuple(output)
    logger.debug("response_kind_signature exit nodes=%d", nodes)
    return result


def membership_digest(
    binding_id: str,
    doctrine_fingerprint: str,
    observer_ids: tuple[str, ...],
    observer_digests: tuple[str, ...],
) -> str:
    """Digest exact source membership with length-prefixed fields."""
    logger.debug("membership_digest entry")
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if (
        type(doctrine_fingerprint) is not str
        or len(doctrine_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in doctrine_fingerprint)
        or type(observer_ids) is not tuple
        or type(observer_digests) is not tuple
        or len(observer_ids) != len(observer_digests)
    ):
        _reject("invalid-membership-digest-input")
    captured_ids = tuple(
        snapshot_p1a_identifier(item, "observer-id") for item in observer_ids
    )
    captured_digests: list[str] = []
    for item in observer_digests:
        if (
            type(item) is not str
            or len(item) != 64
            or any(ch not in "0123456789abcdef" for ch in item)
        ):
            _reject("invalid-membership-digest-input")
        captured_digests.append(item)
    digest = sha256()
    for token in (binding_id, doctrine_fingerprint, *captured_ids, *captured_digests):
        _digest_token(digest, token.encode("utf-8"))
    result = digest.hexdigest()
    logger.debug("membership_digest exit")
    return result


def translation_digest(
    translation_id: str,
    doctrine_fingerprint: str,
    binding_digest: str,
    fine_id: str,
    coarse_id: str,
    projection: tuple[ProjectionStep, ...],
    fine_kind: ResponseKind,
    coarse_kind: ResponseKind,
) -> str:
    """Digest one exact structural translation with kind signatures."""
    logger.debug("translation_digest entry")
    translation_id = snapshot_p1a_identifier(translation_id, "translation-id")
    fine_id = snapshot_p1a_identifier(fine_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if (
        type(doctrine_fingerprint) is not str
        or len(doctrine_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in doctrine_fingerprint)
        or type(binding_digest) is not str
        or len(binding_digest) != 64
        or any(ch not in "0123456789abcdef" for ch in binding_digest)
    ):
        _reject("invalid-translation-digest-input")
    digest = sha256()
    tokens = (
        translation_id, doctrine_fingerprint, binding_digest, fine_id, coarse_id,
        *(item.value for item in projection),
        *response_kind_signature(fine_kind), *response_kind_signature(coarse_kind),
    )
    for token in tokens:
        _digest_token(digest, token.encode("utf-8"))
    result = digest.hexdigest()
    logger.debug("translation_digest exit")
    return result


def snapshot_source_binding(
    value: ObserverSourceBinding, doctrine: ObserverDoctrine
) -> ObserverSourceBinding:
    """Validate immutable membership against one exact doctrine snapshot."""
    logger.debug("snapshot_source_binding entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    if type(value) is not ObserverSourceBinding:
        _reject("source-binding-must-be-exact")
    try:
        binding_id, doctrine_fp = value.binding_id, value.doctrine_fingerprint
        ids, digests = value.observer_ids, value.observer_digests
        supplied, scope = value.membership_digest, value.scope
    except AttributeError:
        _reject("source-binding-missing-fields")
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if (
        type(doctrine_fp) is not str
        or type(scope) is not str
        or type(supplied) is not str
    ):
        _reject("source-binding-string-fields-required")
    if doctrine_fp != doctrine.fingerprint or scope != "immutability-membership-not-chronology":
        _reject("source-binding-doctrine-or-scope-drift")
    if type(ids) is not tuple or type(digests) is not tuple or not ids or len(ids) != len(digests):
        _reject("invalid-source-binding-members")
    if len(ids) > len(doctrine.observers):
        _reject("source-binding-member-limit")
    captured_ids = tuple(snapshot_p1a_identifier(item, "observer-id") for item in ids)
    if len(set(captured_ids)) != len(captured_ids):
        _reject("duplicate-source-binding-member")
    members = {item.observer_id: item for item in doctrine.observers}
    captured_digests: list[str] = []
    for item in digests:
        if type(item) is not str or len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
            _reject("invalid-source-binding-observer-digest")
        captured_digests.append(item)
    expected_digests: list[str] = []
    for observer_id in captured_ids:
        if observer_id not in members:
            _reject("source-binding-nonmember")
        expected_digests.append(sha256(members[observer_id].canonical).hexdigest())
    expected_tuple = tuple(expected_digests)
    if tuple(captured_digests) != expected_tuple:
        _reject("source-binding-observer-drift")
    expected = membership_digest(binding_id, doctrine.fingerprint, captured_ids, expected_tuple)
    if type(supplied) is not str or supplied != expected:
        _reject("source-binding-digest-drift")
    result = ObserverSourceBinding(
        binding_id, doctrine.fingerprint, captured_ids, expected_tuple, expected
    )
    logger.debug("snapshot_source_binding exit members=%d", len(captured_ids))
    return result


def snapshot_translation(
    value: ResponseTranslation,
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> ResponseTranslation:
    """Validate one exact translation against source membership and kinds."""
    logger.debug("snapshot_translation entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    if type(value) is not ResponseTranslation:
        _reject("translation-must-be-exact")
    try:
        translation_id, doctrine_fp = value.translation_id, value.doctrine_fingerprint
        binding_digest = value.source_binding_digest
        fine_id, coarse_id = value.fine_observer_id, value.coarse_observer_id
        projection, fine_kind, coarse_kind = value.projection, value.fine_kind, value.coarse_kind
        supplied, scope = value.translation_digest, value.scope
    except AttributeError:
        _reject("translation-missing-fields")
    translation_id = snapshot_p1a_identifier(translation_id, "translation-id")
    fine_id = snapshot_p1a_identifier(fine_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if (
        type(doctrine_fp) is not str
        or type(binding_digest) is not str
        or type(supplied) is not str
        or type(scope) is not str
    ):
        _reject("translation-string-fields-required")
    members = {item.observer_id: item for item in doctrine.observers}
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        _reject("translation-source-unbound")
    if fine_id not in members or coarse_id not in members:
        _reject("translation-observer-nonmember")
    if not _projection_factorizes(doctrine, fine_id, coarse_id, projection):
        _reject("translation-projection-does-not-factorize")
    expected_fine, expected_coarse = members[fine_id].response_kind, members[coarse_id].response_kind
    if (
        doctrine_fp != doctrine.fingerprint
        or binding_digest != binding.membership_digest
        or response_kind_signature(fine_kind) != response_kind_signature(expected_fine)
        or response_kind_signature(coarse_kind) != response_kind_signature(expected_coarse)
        or scope != "closed-r11-pair-projection"
    ):
        _reject("translation-binding-or-kind-drift")
    expected = translation_digest(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, projection, expected_fine, expected_coarse,
    )
    if type(supplied) is not str or supplied != expected:
        _reject("translation-digest-drift")
    result = ResponseTranslation(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, projection, expected_fine, expected_coarse, expected,
    )
    logger.debug("snapshot_translation exit steps=%d", len(projection))
    return result


def _digest_token(digest: object, token: bytes) -> None:
    logger.debug("_digest_token entry bytes=%d", len(token))
    digest.update(len(token).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(token)  # type: ignore[attr-defined]
    logger.debug("_digest_token exit")


def translate_response(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    translation: ResponseTranslation,
    fine_value: ResponseValue,
) -> ResponseValue:
    """Apply an exact typed pair projection to one fresh response snapshot."""
    logger.debug("translate_response entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    translation = snapshot_translation(translation, doctrine, binding)
    value = _snapshot_response_value(fine_value)
    if response_kind_signature(_response_value_kind(value)) != response_kind_signature(translation.fine_kind):
        logger.error("translate_response fine kind mismatch")
        raise ObserverMorphismValidationError("translation-fine-response-kind-mismatch")
    cursor: ResponseValue = value
    for step in translation.projection:
        if type(cursor) is not PairValue:
            logger.error("translate_response projection shape mismatch")
            raise ObserverMorphismValidationError("translation-response-shape-mismatch")
        cursor = cursor.left if step is ProjectionStep.LEFT else cursor.right
    if response_kind_signature(_response_value_kind(cursor)) != response_kind_signature(translation.coarse_kind):
        logger.error("translate_response coarse kind mismatch")
        raise ObserverMorphismValidationError("translation-coarse-response-kind-mismatch")
    result = _snapshot_response_value(cursor)
    logger.debug("translate_response exit steps=%d", len(translation.projection))
    return result


def _snapshot_response_value(value: ResponseValue) -> ResponseValue:
    """Normalize lower-layer response failures into the P1-A boundary."""
    logger.debug("_snapshot_response_value entry")
    try:
        result = _snapshot_response(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_snapshot_response_value rejected")
        raise ObserverMorphismValidationError("invalid-translation-response") from exc
    logger.debug("_snapshot_response_value exit")
    return result


def _build_translation(
    translation_id: str,
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    fine: InternalObserver,
    coarse: InternalObserver,
    projection: tuple[ProjectionStep, ...],
) -> ResponseTranslation:
    """Build one digest-bound translation after structural factorization."""
    logger.debug("build_translation entry")
    digest = translation_digest(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine.observer_id, coarse.observer_id, projection,
        fine.response_kind, coarse.response_kind,
    )
    result = ResponseTranslation(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine.observer_id, coarse.observer_id, projection,
        fine.response_kind, coarse.response_kind, digest,
    )
    logger.debug("build_translation exit")
    return result


def _check_comparison_witness(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    translation: ResponseTranslation,
    depth: int,
) -> bool:
    """Check one nonempty-domain sanity witness; not the factorization proof."""
    logger.debug("check_comparison_witness entry depth=%d", depth)
    members = {item.observer_id: item for item in doctrine.observers}
    recurrence = _recurrence_at_depth(depth)
    fine = observe(decode_observer(members[translation.fine_observer_id].canonical), recurrence)
    coarse = observe(decode_observer(members[translation.coarse_observer_id].canonical), recurrence)
    result = (
        type(fine) is Ready and type(coarse) is Ready
        and response_data(translate_response(doctrine, binding, translation, fine.value))
        == response_data(coarse.value)
    )
    logger.debug("check_comparison_witness exit result=%s", result)
    return result


def _comparison_is_nonempty(
    fine: InternalObserver, coarse: InternalObserver, depth: int
) -> bool:
    """Confirm the exact threshold intersection has a concrete recurrence."""
    logger.debug("_comparison_is_nonempty entry depth=%d", depth)
    recurrence = _recurrence_at_depth(depth)
    fine_run = observe(decode_observer(fine.canonical), recurrence)
    coarse_run = observe(decode_observer(coarse.canonical), recurrence)
    result = type(fine_run) is Ready and type(coarse_run) is Ready
    logger.debug("_comparison_is_nonempty exit result=%s", result)
    return result


def _observer_member(doctrine: ObserverDoctrine, observer_id: str) -> InternalObserver:
    """Return one exact already-snapshotted doctrine member."""
    logger.debug("observer_member entry")
    result = next((item for item in doctrine.observers if item.observer_id == observer_id), None)
    if result is None:
        logger.error("observer_member missing")
        raise ObserverMorphismValidationError("observer-nonmember")
    logger.debug("observer_member exit")
    return result


def _minimum_pulse_depth(observer: object) -> int:
    """Compute the exact R11 domain threshold on a fresh validated AST."""
    logger.debug("minimum_pulse_depth entry")
    stack: list[tuple[bool, object]] = [(False, observer)]
    values: list[int] = []
    while stack:
        closing, node = stack.pop()
        if not closing:
            stack.append((True, node))
            if type(node) is Apply:
                stack.append((False, node.child))
            elif type(node) is Pair:
                stack.extend(((False, node.right), (False, node.left)))
            continue
        if type(node) is Input:
            values.append(0)
        elif type(node) is Apply:
            child = values.pop()
            values.append(child + (1 if node.primitive is PrimitiveId.TAIL else 0))
        else:
            right, left = values.pop(), values.pop()
            values.append(max(left, right))
    if len(values) != 1:
        logger.error("minimum_pulse_depth shape rejected")
        raise ObserverMorphismValidationError("invalid-domain-profile-shape")
    result = values[0]
    logger.debug("minimum_pulse_depth exit minimum=%d", result)
    return result


def _response_value_kind(value: ResponseValue) -> ResponseKind:
    """Infer the exact kind of a fresh bounded response value."""
    logger.debug("response_value_kind entry")
    stack: list[tuple[bool, object]] = [(False, value)]
    kinds: list[ResponseKind] = []
    while stack:
        closing, node = stack.pop()
        if not closing:
            stack.append((True, node))
            if type(node) is PairValue:
                stack.extend(((False, node.right), (False, node.left)))
            continue
        if type(node) is RecurrenceValue:
            kinds.append(LeafKind.RECURRENCE)
        elif type(node) is MarkValue:
            kinds.append(LeafKind.MARK)
        elif type(node) is PairValue:
            right, left = kinds.pop(), kinds.pop()
            kinds.append(PairKind(left, right))
        else:
            logger.error("response_value_kind exact gate rejected")
            raise ObserverMorphismValidationError("invalid-response-value")
    if len(kinds) != 1:
        logger.error("response_value_kind shape rejected")
        raise ObserverMorphismValidationError("invalid-response-shape")
    result = kinds[0]
    logger.debug("response_value_kind exit")
    return result


def _recurrence_at_depth(depth: int):
    """Construct the canonical nonempty-domain witness at an exact depth."""
    logger.debug("recurrence_at_depth entry")
    if type(depth) is not int or not 0 <= depth <= 128:
        logger.error("recurrence_at_depth invalid depth")
        raise ObserverMorphismValidationError("invalid-comparison-witness-depth")
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("recurrence_at_depth exit depth=%d", depth)
    return result


def p1a_observer_morphism_doctrine() -> ObserverDoctrine:
    """Return the fixed coarse/fine R11 doctrine used by P1-A pressure."""
    logger.debug("p1a_observer_morphism_doctrine entry")
    crest, tail = crest_observer(), tail_observer()
    total = Pair(crest, Input())
    nested = Pair(total, Input())
    result = observer_doctrine(
        "P1A-fixed-observer-morphisms",
        "closed-r11-pair-projection",
        (
            "source-fixed", "membership-not-chronology", "no-object-promotion",
            "family-extension-not-refinement",
        ),
        (
            internal_observer("coarse-crest", crest),
            internal_observer("fine-total", total),
            internal_observer("fine-domain-hole", Pair(crest, tail)),
            internal_observer("fine-nested", nested),
            internal_observer("fine-triply-nested", Pair(nested, Input())),
        ),
        version=P1A_DOCTRINE_VERSION,
    )
    logger.debug("p1a_observer_morphism_doctrine exit")
    return result


def observer_source_binding(
    doctrine: ObserverDoctrine, binding_id: str, observer_ids: tuple[str, ...]
) -> ObserverSourceBinding:
    """Bind exact observer membership and immutability, never chronology."""
    logger.debug("observer_source_binding entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if type(observer_ids) is not tuple or not observer_ids:
        logger.error("observer_source_binding invalid member tuple")
        raise ObserverMorphismValidationError("invalid-source-binding-members")
    if len(observer_ids) > len(doctrine.observers):
        logger.error("observer_source_binding member limit")
        raise ObserverMorphismValidationError("source-binding-member-limit")
    ids = tuple(snapshot_p1a_identifier(item, "observer-id") for item in observer_ids)
    if len(set(ids)) != len(ids):
        logger.error("observer_source_binding duplicate member")
        raise ObserverMorphismValidationError("duplicate-source-binding-member")
    members = {item.observer_id: item for item in doctrine.observers}
    if any(item not in members for item in ids):
        logger.error("observer_source_binding nonmember")
        raise ObserverMorphismValidationError("source-binding-nonmember")
    digests = tuple(sha256(members[item].canonical).hexdigest() for item in ids)
    digest = membership_digest(binding_id, doctrine.fingerprint, ids, digests)
    result = ObserverSourceBinding(binding_id, doctrine.fingerprint, ids, digests, digest)
    logger.debug("observer_source_binding exit members=%d", len(ids))
    return result


def r11_domain_profile(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    observer_id: str,
) -> R11DomainProfile:
    """Derive the exact minimum Pulse depth of one bound R11 observer."""
    logger.debug("r11_domain_profile entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    observer_id = snapshot_p1a_identifier(observer_id, "observer-id")
    if observer_id not in binding.observer_ids:
        logger.error("r11_domain_profile observer unbound")
        raise ObserverMorphismValidationError("domain-profile-source-unbound")
    member = _observer_member(doctrine, observer_id)
    minimum = _minimum_pulse_depth(decode_observer(member.canonical))
    witness = _recurrence_at_depth(minimum)
    if type(observe(decode_observer(member.canonical), witness)) is not Ready:
        logger.error("r11_domain_profile nonempty witness failed")
        raise ObserverMorphismValidationError("domain-profile-witness-failed")
    result = R11DomainProfile(observer_id, minimum, minimum, True)
    logger.debug("r11_domain_profile exit minimum=%d", minimum)
    return result


def observer_morphism_judgment(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    fine_observer_id: str,
    coarse_observer_id: str,
    projection: tuple[ProjectionStep, ...],
) -> ObserverMorphismJudgment:
    """Check factorization on C and then the stronger domain inclusion."""
    logger.debug("observer_morphism_judgment entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    morphism_id = snapshot_p1a_identifier(morphism_id, "morphism-id")
    fine_id = snapshot_p1a_identifier(fine_observer_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_observer_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        logger.error("observer_morphism_judgment source unbound")
        raise ObserverMorphismValidationError("morphism-source-unbound")
    fine_member, coarse_member = _observer_member(doctrine, fine_id), _observer_member(doctrine, coarse_id)
    fine_domain = r11_domain_profile(doctrine, binding, fine_id)
    coarse_domain = r11_domain_profile(doctrine, binding, coarse_id)
    comparison_depth = max(fine_domain.minimum_pulse_depth, coarse_domain.minimum_pulse_depth)
    comparison_nonempty = _comparison_is_nonempty(
        fine_member, coarse_member, comparison_depth
    )
    comparison = ComparisonDomain(
        fine_domain.minimum_pulse_depth, coarse_domain.minimum_pulse_depth,
        comparison_depth, comparison_nonempty,
    )
    structural_factorizes = _projection_factorizes(
        doctrine, fine_id, coarse_id, projection
    )
    factorizes = False
    translation: ResponseTranslation | None = None
    witness_checked = False
    if structural_factorizes and comparison.confirmed_nonempty:
        translation = _build_translation(
            morphism_id, doctrine, binding, fine_member, coarse_member, projection
        )
        witness_checked = _check_comparison_witness(
            doctrine, binding, translation, comparison_depth
        )
        factorizes = witness_checked
    domain_inclusion = (
        coarse_domain.minimum_pulse_depth >= fine_domain.minimum_pulse_depth
    )
    if factorizes and domain_inclusion:
        status, obstruction = MorphismStatus.STRONG, ""
    elif factorizes:
        status, obstruction = MorphismStatus.INFORMATION_ONLY, "fine-domain-hole"
    elif not structural_factorizes:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "declared-projection-does-not-factorize"
    elif not comparison.confirmed_nonempty:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "comparison-domain-unconfirmed"
    else:
        status = MorphismStatus.INCOMPARABLE
        obstruction = "comparison-witness-failed"
    if not factorizes:
        information_loss = InformationLoss.UNAVAILABLE
    elif projection:
        information_loss = InformationLoss.DROPS_PAIR_COMPONENTS
    else:
        information_loss = InformationLoss.LOSSLESS_IDENTITY
    result = ObserverMorphismJudgment(
        morphism_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, fine_domain, coarse_domain, comparison, translation,
        factorizes, domain_inclusion, witness_checked, information_loss,
        status, obstruction,
    )
    logger.debug("observer_morphism_judgment exit status=%s", status.value)
    return result


def identity_observer_morphism(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    observer_id: str,
) -> ObserverMorphismJudgment:
    """Construct the empty-projection identity with inherited bindings."""
    logger.debug("identity_observer_morphism entry")
    result = observer_morphism_judgment(
        doctrine, binding, morphism_id, observer_id, observer_id, ()
    )
    logger.debug("identity_observer_morphism exit status=%s", result.status.value)
    return result


def compose_observer_morphisms(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    morphism_id: str,
    fine_to_middle: ResponseTranslation,
    middle_to_coarse: ResponseTranslation,
) -> ObserverMorphismJudgment:
    """Compose exact bound projections without weakening doctrine/domain sources."""
    logger.debug("compose_observer_morphisms entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    first = snapshot_translation(fine_to_middle, doctrine, binding)
    second = snapshot_translation(middle_to_coarse, doctrine, binding)
    if first.coarse_observer_id != second.fine_observer_id:
        logger.error("compose_observer_morphisms middle mismatch")
        raise ObserverMorphismValidationError("morphism-composition-middle-mismatch")
    result = observer_morphism_judgment(
        doctrine, binding, morphism_id, first.fine_observer_id,
        second.coarse_observer_id, first.projection + second.projection,
    )
    logger.debug("compose_observer_morphisms exit status=%s", result.status.value)
    return result
