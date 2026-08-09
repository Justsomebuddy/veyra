"""Construction and replay validation of asymmetric P1-C3 transport specs."""

from __future__ import annotations

import logging

from ..plan import build_direct_echo_transport, snapshot_fork_join_plan
from ..types import FiniteDiagramSource, ForkJoinPlan
from ...observer.morphism import (
    ObserverMorphismValidationError, ObserverSourceBinding, ProjectionStep,
)
from ...observer.relations.preflight import snapshot_policy
from ...observer.relations.types import RelationResourcePolicy
from ...observer.relations.request import snapshot_scope, snapshot_stage_source
from ...observer.relations.translation import snapshot_translation_input
from ...observer.relations.types import (
    ComparisonMode, LawStatus, LossStatus, MorphismReplaySpec,
    ObserverRelationScope, RelationClass, RelationEvaluationSource,
)
from ...observer.relations.validation import ObserverRelationValidationError
from ...ontology.types import ObserverDoctrine
from .bridge import snapshot_response_bridge
from .digest import digest, sequence
from .types import (
    C3TransportMode, P0P1AResponseBridgeSource, TranslatedEchoTransportSpec,
    TranslatedConfluencePolicy, TranslationDirection,
)
from .validation import (
    TranslatedConfluenceValidationError, hex_digest, identifier, reject,
)

logger = logging.getLogger(__name__)
POLICY_VERSION = "p1-c3-policy-v1"
SPEC_VERSION = "p1-c3-spec-v1"
SPEC_SCOPE = "one-directed-finite-translated-cell"


def translated_confluence_policy(
    *, max_checks: int = 4096, max_bytes: int = 2 * 1024 * 1024,
) -> TranslatedConfluencePolicy:
    """Build one bounded C3 outer policy within invariant hard caps."""
    logger.debug("translated_confluence_policy entry")
    if (
        type(max_checks) is not int or type(max_bytes) is not int
        or not 1 <= max_checks <= 4096 or not 1 <= max_bytes <= 2 * 1024 * 1024
    ):
        reject("invalid-translated-confluence-policy")
    version = POLICY_VERSION
    policy_digest = digest("p1-c3-policy-v1", (
        ("version", version.encode()), ("checks", max_checks.to_bytes(8, "big")),
        ("bytes", max_bytes.to_bytes(8, "big")),
    ))
    result = TranslatedConfluencePolicy(version, max_checks, max_bytes, policy_digest)
    logger.debug("translated_confluence_policy exit")
    return result


def snapshot_translated_policy(value: TranslatedConfluencePolicy) -> TranslatedConfluencePolicy:
    """Rebuild one exact outer policy before source traversal."""
    logger.debug("snapshot_translated_policy entry")
    supplied = shallow_outer_policy(value)
    result = translated_confluence_policy(
        max_checks=supplied[1], max_bytes=supplied[2],
    )
    expected = shallow_outer_policy(result)
    if supplied != expected:
        reject("translated-confluence-policy-drift")
    logger.debug("snapshot_translated_policy exit")
    return result


def _validated_lower(
    p1a: ObserverDoctrine, binding: ObserverSourceBinding,
    source: RelationEvaluationSource, scope: ObserverRelationScope,
    morphism: MorphismReplaySpec,
) -> tuple[RelationEvaluationSource, ObserverRelationScope, MorphismReplaySpec]:
    """Validate the complete raw A2 scope and directed raw P1-A morphism."""
    logger.debug("c3 validated_lower entry")
    try:
        source = snapshot_stage_source(source, p1a, binding)
        scope = snapshot_scope(scope, p1a, binding, source)
    except (ObserverRelationValidationError, ObserverMorphismValidationError) as exc:
        logger.error("c3 validated_lower source/scope rejected")
        raise TranslatedConfluenceValidationError("invalid-translated-a2-source-or-scope") from exc
    if scope.mode is not ComparisonMode.WITH_P1A_REPLAY:
        reject("translated-scope-must-request-p1a-replay")
    all_stages = tuple((row.stage_id, row.commitment) for row in source.stages)
    if scope.stages != all_stages:
        reject("translated-scope-must-cover-complete-stage-source")
    try:
        value = snapshot_translation_input(
            morphism, scope.fine_observer_id, scope.coarse_observer_id, p1a, binding,
        )
    except (ObserverRelationValidationError, ObserverMorphismValidationError) as exc:
        logger.error("c3 validated_lower morphism rejected")
        raise TranslatedConfluenceValidationError("invalid-translated-raw-morphism") from exc
    if type(value) is not MorphismReplaySpec:
        reject("translated-transport-requires-raw-morphism")
    logger.debug("c3 validated_lower exit stages=%d", len(scope.stages))
    return source, scope, value


def _mapped_pair(
    bridge: P0P1AResponseBridgeSource, diagram_fine: str, diagram_coarse: str,
    p1a_fine: str, p1a_coarse: str,
) -> None:
    """Require exact non-name-only bridge rows for both directed endpoints."""
    logger.debug("c3 mapped_pair entry")
    pairs = {(row.diagram_observer_id, row.p1a_observer_id) for row in bridge.observer_rows}
    if (
        diagram_fine == diagram_coarse or p1a_fine == p1a_coarse
        or (diagram_fine, p1a_fine) not in pairs
        or (diagram_coarse, p1a_coarse) not in pairs
    ):
        reject("translated-observer-pair-not-exactly-bridged")
    logger.debug("c3 mapped_pair exit")


def translated_echo_transport_spec(
    p0_doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, plan: ForkJoinPlan,
    p1a_doctrine: ObserverDoctrine, p1a_source: ObserverSourceBinding,
    a2_stage_source: RelationEvaluationSource, bridge: P0P1AResponseBridgeSource,
    spec_id: str, direction: TranslationDirection,
    diagram_fine_observer_id: str, diagram_coarse_observer_id: str,
    morphism: MorphismReplaySpec, relation_scope: ObserverRelationScope,
    relation_policy, required_class: RelationClass,
    required_loss: LossStatus | None = None,
) -> TranslatedEchoTransportSpec:
    """Build a source-bound asymmetric raw replay specification."""
    logger.debug("translated_echo_transport_spec entry")
    bridge = snapshot_response_bridge(
        p0_doctrine, diagram, p1a_doctrine, p1a_source, a2_stage_source, bridge,
    )
    if type(direction) is not TranslationDirection:
        reject("invalid-translation-direction")
    spec_id = identifier(spec_id, "translated-spec-id")
    diagram_fine = identifier(diagram_fine_observer_id, "diagram-fine-observer-id")
    diagram_coarse = identifier(diagram_coarse_observer_id, "diagram-coarse-observer-id")
    source, relation_scope, morphism = _validated_lower(
        p1a_doctrine, p1a_source, a2_stage_source, relation_scope, morphism,
    )
    try:
        relation_policy = snapshot_policy(relation_policy)
    except ObserverRelationValidationError as exc:
        logger.error("c3 nested relation policy rejected")
        raise TranslatedConfluenceValidationError("invalid-translated-relation-policy") from exc
    p1a_fine, p1a_coarse = relation_scope.fine_observer_id, relation_scope.coarse_observer_id
    _mapped_pair(bridge, diagram_fine, diagram_coarse, p1a_fine, p1a_coarse)
    placeholder = build_direct_echo_transport(p0_doctrine, (diagram_fine, diagram_coarse))
    plan = snapshot_fork_join_plan(plan, diagram, placeholder, p0_doctrine)
    if type(required_class) is not RelationClass or required_class not in {
        RelationClass.EQUIVALENT_ON_SCOPE, RelationClass.STRICT_REFINEMENT_ON_SCOPE,
    } or (required_loss is not None and type(required_loss) is not LossStatus):
        reject("invalid-translated-relation-requirement")
    spec_digest = digest("p1-c3-translated-spec-v1", (
        ("version", SPEC_VERSION.encode()),
        ("mode", C3TransportMode.TYPED_TRANSLATION.value.encode()),
        ("public-scope", SPEC_SCOPE.encode()),
        ("id", spec_id.encode()), ("bridge", bridge.bridge_digest.encode()),
        ("plan", plan.plan_digest.encode()),
        ("direction", direction.value.encode()),
        ("diagram-pair", sequence("id", (diagram_fine, diagram_coarse))),
        ("p1a-pair", sequence("id", (p1a_fine, p1a_coarse))),
        ("morphism", sequence("field", (
            morphism.morphism_id, morphism.fine_observer_id, morphism.coarse_observer_id,
            *(step.value for step in morphism.projection),
        ))),
        ("a2-source", source.source_digest.encode()),
        ("scope", relation_scope.scope_digest.encode()),
        ("relation-policy", relation_policy.policy_digest.encode()),
        ("required-laws", sequence("law", (
            LawStatus.ESTABLISHED.value, LawStatus.ESTABLISHED.value,
            required_class.value,
            "absent" if required_loss is None else required_loss.value,
        ))),
    ))
    result = TranslatedEchoTransportSpec(
        spec_id, bridge.bridge_digest, plan.plan_digest, direction, diagram_fine, diagram_coarse,
        p1a_fine, p1a_coarse, morphism, relation_scope, relation_policy,
        LawStatus.ESTABLISHED, LawStatus.ESTABLISHED, required_class,
        required_loss, spec_digest,
    )
    logger.debug("translated_echo_transport_spec exit direction=%s", direction.value)
    return result


def snapshot_translated_spec(
    p0_doctrine: ObserverDoctrine, diagram: FiniteDiagramSource, plan: ForkJoinPlan,
    p1a_doctrine: ObserverDoctrine, p1a_source: ObserverSourceBinding,
    a2_stage_source: RelationEvaluationSource, bridge: P0P1AResponseBridgeSource,
    value: TranslatedEchoTransportSpec,
) -> TranslatedEchoTransportSpec:
    """Freshly rebuild and exact-compare a supplied translated spec."""
    logger.debug("snapshot_translated_spec entry")
    supplied = shallow_spec(value)
    morphism = MorphismReplaySpec(*supplied[8])
    relation_scope = ObserverRelationScope(*supplied[9])
    relation_policy = RelationResourcePolicy(*supplied[10])
    expected = translated_echo_transport_spec(
        p0_doctrine, diagram, plan, p1a_doctrine, p1a_source, a2_stage_source,
        bridge, supplied[0], supplied[3], supplied[4], supplied[5],
        morphism, relation_scope, relation_policy,
        supplied[13], supplied[14],
    )
    if supplied != shallow_spec(expected):
        reject("translated-transport-spec-drift")
    logger.debug("snapshot_translated_spec exit")
    return expected

def _get(value: object, names: tuple[str, ...], reason: str) -> tuple[object, ...]:
    """Read exact DTO fields without dynamic property lookup."""
    logger.debug("c3 spec get entry reason=%s", reason)
    try:
        result = tuple(object.__getattribute__(value, name) for name in names)
    except AttributeError:
        reject(reason)
    logger.debug("c3 spec get exit fields=%d", len(result))
    return result


def shallow_outer_policy(value: object) -> tuple[object, ...]:
    """Capture one exact outer policy before reconstruction."""
    logger.debug("c3 shallow_outer_policy entry")
    if type(value) is not TranslatedConfluencePolicy:
        reject("translated-confluence-policy-must-be-exact")
    row = _get(value, TranslatedConfluencePolicy.__slots__, "translated-confluence-policy-missing-fields")
    if (
        type(row[0]) is not str or type(row[1]) is not int
        or type(row[2]) is not int or type(row[3]) is not str
    ):
        reject("translated-confluence-policy-field-type")
    hex_digest(row[3], "translated-confluence-policy-digest")
    logger.debug("c3 shallow_outer_policy exit")
    return row


def _morphism(value: object) -> tuple[object, ...]:
    """Capture exact raw morphism syntax with a closed projection tuple."""
    logger.debug("c3 shallow morphism entry")
    if type(value) is not MorphismReplaySpec:
        reject("translated-transport-requires-raw-morphism")
    row = _get(
        value, ("morphism_id", "fine_observer_id", "coarse_observer_id", "projection"),
        "translated-morphism-missing-fields",
    )
    if any(type(item) is not str for item in row[:3]) or type(row[3]) is not tuple or len(row[3]) > 128:
        reject("translated-morphism-field-type-or-length")
    if any(type(item) is not ProjectionStep for item in row[3]):
        reject("translated-morphism-projection-drift")
    result = (*row[:3], tuple(row[3]))
    logger.debug("c3 shallow morphism exit steps=%d", len(row[3]))
    return result


def _stage_key(value: object, field: str) -> tuple[str, str]:
    """Capture one exact two-string A2 stage key."""
    logger.debug("c3 shallow stage_key entry field=%s", field)
    if type(value) is not tuple or len(value) != 2 or any(type(item) is not str for item in value):
        reject(f"translated-{field}-stage-key-drift")
    result = (value[0], value[1])
    logger.debug("c3 shallow stage_key exit field=%s", field)
    return result


def _scope(value: object) -> tuple[object, ...]:
    """Capture exact A2 scope containers before lower-layer replay."""
    logger.debug("c3 shallow scope entry")
    if type(value) is not ObserverRelationScope:
        reject("translated-relation-scope-must-be-exact")
    names = (
        "doctrine_fingerprint", "observer_source_digest", "stage_source_digest",
        "fine_observer_id", "coarse_observer_id", "stages", "ordered_pairs",
        "mode", "scope_digest",
    )
    row = _get(value, names, "translated-relation-scope-missing-fields")
    if (
        any(type(item) is not str for item in (*row[:5], row[8]))
        or type(row[5]) is not tuple or not 1 <= len(row[5]) <= 32
        or type(row[6]) is not tuple or len(row[6]) != len(row[5]) ** 2
        or type(row[7]) is not ComparisonMode
    ):
        reject("translated-relation-scope-field-type-or-length")
    for item in (*row[:3], row[8]):
        hex_digest(item, "translated-relation-scope-digest")
    stages = tuple(_stage_key(item, "scope") for item in row[5])
    pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for item in row[6]:
        if type(item) is not tuple or len(item) != 2:
            reject("translated-scope-pair-drift")
        pairs.append((_stage_key(item[0], "pair-left"), _stage_key(item[1], "pair-right")))
    result = (*row[:5], stages, tuple(pairs), row[7], row[8])
    logger.debug("c3 shallow scope exit stages=%d pairs=%d", len(stages), len(pairs))
    return result


def _relation_policy(value: object) -> tuple[object, ...]:
    """Capture exact nested A2 policy primitive fields."""
    logger.debug("c3 shallow relation_policy entry")
    if type(value) is not RelationResourcePolicy:
        reject("translated-relation-policy-must-be-exact")
    row = _get(
        value, ("version", "max_cost", "max_encoded_bytes", "policy_digest"),
        "translated-relation-policy-missing-fields",
    )
    if type(row[0]) is not str or type(row[1]) is not int or type(row[2]) is not int or type(row[3]) is not str:
        reject("translated-relation-policy-field-type")
    hex_digest(row[3], "translated-relation-policy-digest")
    logger.debug("c3 shallow relation_policy exit")
    return row


def shallow_spec(value: object) -> tuple[object, ...]:
    """Capture every public spec field before reconstruction or equality."""
    logger.debug("c3 shallow_spec entry")
    if type(value) is not TranslatedEchoTransportSpec:
        reject("translated-transport-spec-must-be-exact")
    row = _get(value, TranslatedEchoTransportSpec.__slots__, "translated-transport-spec-missing-fields")
    if (
        any(type(row[index]) is not str for index in (0, 1, 2, 4, 5, 6, 7, 15, 16, 18))
        or type(row[3]) is not TranslationDirection
        or type(row[11]) is not LawStatus or type(row[12]) is not LawStatus
        or type(row[13]) is not RelationClass
        or (row[14] is not None and type(row[14]) is not LossStatus)
        or type(row[17]) is not C3TransportMode
    ):
        reject("translated-transport-spec-field-type")
    for index in (1, 2, 15):
        hex_digest(row[index], "translated-transport-spec-digest")
    result = (
        *row[:8], _morphism(row[8]), _scope(row[9]), _relation_policy(row[10]),
        *row[11:],
    )
    logger.debug("c3 shallow_spec exit")
    return result
