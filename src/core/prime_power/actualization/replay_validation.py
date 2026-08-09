"""Fresh released-validator replay and exact P3-N0 outcome authentication."""

from __future__ import annotations

import logging

from ...observer.network.core import observer_network_judgment
from ...observer.network.result_validation import validate_observer_network_result
from .common import (
    N0ValidationError, digest, indexed, reject,
)
from .types import N0ReplayEvidence
from .nested_validation import (
    validate_event_shape, validate_replay_shape,
)
from .result_nested_validation import (
    _n2_arrow_shape, validate_n2_positive_shape,
)
from .sources import validate_n0_source
from .types import (
    N2FPackage, SuffixSelector,
)
from ..reduction_network.core import prime_power_reduction_judgment
from ..reduction_network.types import (
    FiniteArrowJudgment, FiniteRelation, PrimePowerReductionJudgment,
)
from ..reduction_network.validation import validate_prime_power_reduction_result

logger = logging.getLogger(__name__)
PRODUCER_IDS = (
    "response-F0", "response-F1", "identity-requery", "reduction", "bridge-access",
    "selector", "package-access",
)


def _wrapper(source, selector):
    """Select one exact precommitted wrapper without accepting strings as selectors."""
    logger.debug("_wrapper entry")
    validate_n0_source(source)
    if type(selector) is not SuffixSelector:
        logger.error("_wrapper selector invalid")
        reject("n0-replay-source-or-selector-invalid")
    logger.debug("_wrapper state selector=%s", selector.value)
    result = (source.strict_package if selector is SuffixSelector.STRICT_SUFFIX
              else source.open_package)
    if (type(result) is not N2FPackage or result.selector is not selector
            or result.network_source != result.raw_package.finite.p3t_raw_source):
        reject("n0-replay-wrapper-binding-drift")
    logger.debug("_wrapper exit")
    return result


def validate_released_lane(source, selector, network, n2_result, arrow):
    """Use the released P3-T/N2 validators and bind the selected released arrow."""
    logger.debug("validate_released_lane entry")
    wrapper = _wrapper(source, selector)
    logger.debug("validate_released_lane state selector=%s", selector.value)
    validate_n2_positive_shape(n2_result)
    try:
        validated_network = validate_observer_network_result(
            wrapper.network_source, network, wrapper.network_policy,
        )
        validated_n2 = validate_prime_power_reduction_result(wrapper.raw_package, n2_result)
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("validate_released_lane foreign validator rejection")
        reject(f"n0-released-lane-rejected-{type(exc).__name__}")
    if type(validated_n2) is not PrimePowerReductionJudgment or type(arrow) is not FiniteArrowJudgment:
        reject("n0-replay-positive-n2-arrow-required")
    _n2_arrow_shape(arrow, -1)
    expected_relation = (FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE
                         if selector is SuffixSelector.STRICT_SUFFIX else FiniteRelation.OPEN)
    selected = tuple(item for item in validated_n2.finite_arrows
                     if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    if len(selected) != 1:
        reject("n0-replay-selected-arrow-drift")
    try:
        same_arrow = arrow == selected[0]
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("validate_released_lane hostile arrow equality rejected")
        reject(f"n0-replay-arrow-equality-rejected-{type(exc).__name__}")
    if type(same_arrow) is not bool or not same_arrow or arrow.relation is not expected_relation:
        reject("n0-replay-selected-arrow-drift")
    logger.debug("validate_released_lane exit")
    return wrapper, validated_network, validated_n2, selected[0]


def fresh_released_lane(source, selector):
    """Construct and validate the one released lane selected by the history."""
    logger.debug("fresh_released_lane entry")
    wrapper = _wrapper(source, selector)
    logger.debug("fresh_released_lane state selector=%s", selector.value)
    try:
        network = observer_network_judgment(wrapper.network_source, wrapper.network_policy)
        n2_result = prime_power_reduction_judgment(wrapper.raw_package)
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("fresh_released_lane foreign runtime rejection")
        reject(f"n0-released-lane-runtime-rejected-{type(exc).__name__}")
    if type(n2_result) is not PrimePowerReductionJudgment:
        reject("n0-replay-fresh-positive-n2-required")
    selected = tuple(item for item in n2_result.finite_arrows
                     if (item.fine_depth, item.coarse_depth) == source.scope.arrow)
    if len(selected) != 1:
        reject("n0-replay-fresh-arrow-missing-or-duplicate")
    result = validate_released_lane(source, selector, network, n2_result, selected[0])
    logger.debug("fresh_released_lane exit")
    return result


def outcome_digest(source, selector, producer_digests, network, n2_result, arrow) -> str:
    """Recompute the outcome from an exact package, released results, and seven producers."""
    logger.debug("outcome_digest entry")
    wrapper, network, n2_result, arrow = validate_released_lane(
        source, selector, network, n2_result, arrow,
    )
    if type(producer_digests) is not tuple or len(producer_digests) != len(PRODUCER_IDS):
        reject("n0-replay-producer-envelope-invalid")
    from .common import exact_hex
    for index, item in enumerate(producer_digests):
        exact_hex(item, f"n0-replay-producer-{index}")
    value = digest("veyra.p3n0.n2f-outcome.v2", (
        ("selector", selector.value.encode()), ("package", wrapper.wrapper_digest.encode()),
        ("network-source", network.source_digest.encode()),
        ("network-judgment", network.judgment_digest.encode()),
        ("n2-judgment", n2_result.judgment_digest.encode()),
        ("n2-replay", n2_result.p3t_replay_digest.encode()),
        ("arrow", arrow.judgment_digest.encode()), *indexed("producer", producer_digests),
    ))
    logger.debug("outcome_digest exit")
    return value


def validate_replay_evidence(source, selector, events, replay) -> N0ReplayEvidence:
    """Freshly authenticate all replay fields against exact event producers."""
    logger.debug("validate_replay_evidence entry")
    validate_n0_source(source)
    raw = validate_replay_shape(replay)
    if type(events) is not tuple or len(events) > 64:
        reject("n0-replay-event-envelope-invalid")
    checked_events = tuple(validate_event_shape(item) for item in events)
    for index, item in enumerate(checked_events):
        expected_digest = digest("veyra.p3n0.event.v2", (
            ("id", item["event_id"].encode()), ("kind", item["kind"].encode()),
            *indexed("parent", item["parents"]),
            ("token", (item["token_id"] or "PRETOKEN").encode()),
            ("lineage", item["lineage_id"].encode()),
            ("scope", item["scope_digest"].encode()),
            ("payload", item["payload_digest"].encode()),
        ))
        if item["event_digest"] != expected_digest:
            logger.error("validate_replay_evidence event digest drift index=%d", index)
            reject("n0-replay-event-digest-drift")
    by_id = {item["event_id"]: item for item in checked_events}
    if len(by_id) != len(events) or any(name not in by_id for name in PRODUCER_IDS):
        reject("n0-replay-producer-event-set-invalid")
    producers = tuple(by_id[name]["event_digest"] for name in PRODUCER_IDS)
    wrapper, network, n2_result, arrow = fresh_released_lane(source, selector)
    expected_outcome = outcome_digest(source, selector, producers, network, n2_result, arrow)
    expected = N0ReplayEvidence(
        selector.value, wrapper.wrapper_digest, network.source_digest,
        network.judgment_digest, n2_result.judgment_digest, arrow.judgment_digest,
        producers, expected_outcome,
    )
    if raw["selector"] != selector.value or replay != expected:
        reject("n0-replay-evidence-drift")
    logger.debug("validate_replay_evidence exit")
    return replay
