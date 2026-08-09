"""R14.1 exact typed ordered grammar regressions."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

import src.core.observer_synthesis_v2_grammar as grammar_module
from src.core.observer_core_codec import (
    canonical_observer_bytes,
    decode_observer,
)
from src.core.observer_core_semantics import infer_observer_kind
from src.core.observer_core_types import (
    Apply,
    Input,
    LeafKind,
    Pair,
    PairKind,
    PrimitiveId,
)
from src.core.observer_synthesis_v2_grammar import (
    BOUNDARY,
    DEFAULT_GRAMMAR,
    EXPECTED_DEFAULT_CANDIDATES,
    EXPECTED_DEFAULT_CANONICAL_BYTES,
    EXPECTED_DEFAULT_CATALOG_DIGEST,
    EXPECTED_DEFAULT_MAX_ROW_BYTES,
    EXPECTED_DEFAULT_STRATA,
    ObserverGrammarV2Error,
    enumerate_observer_grammar_v2,
)
from src.core.observer_synthesis_v2_types import (
    ObserverCandidateV2,
    ObserverGrammarEnumerationV2,
    SynthesisStatus,
)
from src.core.observer_synthesis_v2_validation import (
    verify_observer_grammar_enumeration_v2,
)

logger = logging.getLogger(__name__)


def _structure_metrics(observer: object) -> tuple[int, int]:
    logger.debug("R14.1 structure metrics entry type=%s", type(observer).__name__)
    if type(observer) is Input:
        result = (0, 0)
    elif type(observer) is Apply:
        child_cost, child_depth = _structure_metrics(observer.child)
        result = (1 + child_cost, 1 + child_depth)
    elif type(observer) is Pair:
        left_cost, left_depth = _structure_metrics(observer.left)
        right_cost, right_depth = _structure_metrics(observer.right)
        result = (
            1 + left_cost + right_cost,
            1 + max(left_depth, right_depth),
        )
    else:
        raise AssertionError(f"unexpected observer type: {type(observer).__name__}")
    logger.debug("R14.1 structure metrics exit result=%r", result)
    return result


@pytest.fixture(scope="module")
def grammar_report() -> ObserverGrammarEnumerationV2:
    logger.info("R14.1 default grammar fixture start")
    result = enumerate_observer_grammar_v2()
    logger.info(
        "R14.1 default grammar fixture complete candidates=%d bytes=%d",
        len(result.candidates),
        result.canonical_bytes,
    )
    return result


def test_default_ordered_grammar_has_exact_reviewed_counts(
    grammar_report: ObserverGrammarEnumerationV2,
) -> None:
    logger.info("R14.1 exact count test start")
    assert tuple(len(row.candidates) for row in grammar_report.strata) == (
        EXPECTED_DEFAULT_STRATA
    )
    assert len(grammar_report.candidates) == EXPECTED_DEFAULT_CANDIDATES == 1565
    assert grammar_report.canonical_bytes == EXPECTED_DEFAULT_CANONICAL_BYTES == 488_550
    assert grammar_report.max_row_bytes == EXPECTED_DEFAULT_MAX_ROW_BYTES == 338
    assert grammar_report.catalog_digest == EXPECTED_DEFAULT_CATALOG_DIGEST
    assert grammar_report.complete is True
    assert grammar_report.boundary == BOUNDARY
    logger.info("R14.1 exact count test complete")


def test_every_candidate_is_typed_canonical_and_ranked(
    grammar_report: ObserverGrammarEnumerationV2,
) -> None:
    logger.info("R14.1 canonical/type audit start")
    seen: set[bytes] = set()
    for stratum in grammar_report.strata:
        ranking = tuple((item.depth, item.canonical) for item in stratum.candidates)
        assert ranking == tuple(sorted(ranking))
        assert all(item.cost == stratum.cost for item in stratum.candidates)
        for item in stratum.candidates:
            assert item.canonical not in seen
            seen.add(item.canonical)
            assert item.response_kind == infer_observer_kind(item.observer)
            assert canonical_observer_bytes(item.observer) == item.canonical
            assert decode_observer(item.canonical) == item.observer
            assert _structure_metrics(item.observer) == (item.cost, item.depth)
            assert 0 <= item.depth <= DEFAULT_GRAMMAR.max_depth
            assert 0 <= item.cost <= DEFAULT_GRAMMAR.max_cost
    assert len(seen) == EXPECTED_DEFAULT_CANDIDATES
    logger.info("R14.1 canonical/type audit complete candidates=%d", len(seen))


def test_ordered_pair_keeps_both_reverse_branches(
    grammar_report: ObserverGrammarEnumerationV2,
) -> None:
    logger.info("R14.1 ordered Pair audit start")
    tail = Apply(PrimitiveId.TAIL, Input())
    crest = Apply(PrimitiveId.CREST, Input())
    left_right = Pair(tail, crest)
    right_left = Pair(crest, tail)
    table = {item.canonical: item for item in grammar_report.candidates}
    first = table[canonical_observer_bytes(left_right)]
    second = table[canonical_observer_bytes(right_left)]
    assert first.observer == left_right
    assert second.observer == right_left
    assert first.canonical != second.canonical
    assert first.cost == second.cost == 3
    assert first.depth == second.depth == 2
    assert first.response_kind == PairKind(LeafKind.RECURRENCE, LeafKind.MARK)
    assert second.response_kind == PairKind(LeafKind.MARK, LeafKind.RECURRENCE)
    logger.info("R14.1 ordered Pair audit complete")


def test_every_pair_has_its_ordered_reverse(
    grammar_report: ObserverGrammarEnumerationV2,
) -> None:
    logger.info("R14.1 exhaustive ordered Pair closure start")
    catalog = {item.canonical for item in grammar_report.candidates}
    pair_count = 0
    for candidate in grammar_report.candidates:
        if type(candidate.observer) is not Pair:
            continue
        pair_count += 1
        reverse = Pair(candidate.observer.right, candidate.observer.left)
        assert canonical_observer_bytes(reverse) in catalog
    assert pair_count > 1000
    logger.info("R14.1 exhaustive ordered Pair closure complete pairs=%d", pair_count)


def test_cost_and_depth_bounds_prune_independently() -> None:
    logger.info("R14.1 custom bound test start")
    cost_one = enumerate_observer_grammar_v2(
        replace(DEFAULT_GRAMMAR, grammar_id="test-cost-one", max_cost=1)
    )
    depth_zero = enumerate_observer_grammar_v2(
        replace(DEFAULT_GRAMMAR, grammar_id="test-depth-zero", max_depth=0)
    )
    assert tuple(len(row.candidates) for row in cost_one.strata) == (1, 3)
    assert len(depth_zero.candidates) == 1
    assert type(depth_zero.candidates[0].observer) is Input
    logger.info("R14.1 custom bound test complete")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("schema", "forged", "invalid-v2-grammar-limits"),
        ("max_cost", True, "invalid-v2-grammar-limits"),
        ("max_depth", -1, "invalid-v2-grammar-limits"),
        ("candidate_limit", 0, "invalid-v2-grammar-limits"),
        ("canonical_bytes_limit", 0, "invalid-v2-grammar-limits"),
        ("max_cost", 7, "invalid-v2-grammar-limits"),
        ("max_depth", 5, "invalid-v2-grammar-limits"),
        ("candidate_limit", 2049, "invalid-v2-grammar-limits"),
        ("canonical_bytes_limit", 8 * 1024 * 1024 + 1, "invalid-v2-grammar-limits"),
    ),
)
def test_malformed_exact_grammar_limits_fail_closed(
    field: str,
    value: object,
    reason: str,
) -> None:
    logger.info("R14.1 invalid grammar test start field=%s", field)
    with pytest.raises(ObserverGrammarV2Error, match=reason):
        enumerate_observer_grammar_v2(replace(DEFAULT_GRAMMAR, **{field: value}))
    logger.info("R14.1 invalid grammar test complete field=%s", field)


def test_candidate_and_retained_caps_fail_before_partial_success() -> None:
    logger.info("R14.1 hard cap test start")
    with pytest.raises(ObserverGrammarV2Error, match="v2-candidate-limit"):
        enumerate_observer_grammar_v2(
            replace(DEFAULT_GRAMMAR, grammar_id="test-candidate-cap", candidate_limit=1564)
        )
    with pytest.raises(ObserverGrammarV2Error, match="v2-canonical-bytes-limit"):
        enumerate_observer_grammar_v2(
            replace(
                DEFAULT_GRAMMAR,
                grammar_id="test-byte-cap",
                canonical_bytes_limit=488_549,
            )
        )
    logger.info("R14.1 hard cap test complete")


def test_candidate_cap_is_charged_before_candidate_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.1 candidate precharge test start")
    calls = 0
    original = grammar_module._candidate

    def counted_candidate(*args: object, **kwargs: object) -> ObserverCandidateV2:
        nonlocal calls
        logger.debug("R14.1 counted candidate call=%d", calls + 1)
        calls += 1
        return original(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(grammar_module, "_candidate", counted_candidate)
    with pytest.raises(ObserverGrammarV2Error, match="v2-candidate-limit"):
        enumerate_observer_grammar_v2(
            replace(
                DEFAULT_GRAMMAR,
                grammar_id="test-precharged-candidate-cap",
                max_cost=1,
                candidate_limit=1,
            )
        )
    assert calls == 1
    logger.info("R14.1 candidate precharge test complete calls=%d", calls)


def test_reserved_terminal_status_vocabulary_is_exact() -> None:
    logger.info("R14.1 terminal status audit start")
    assert tuple(item.value for item in SynthesisStatus) == (
        "FOUND",
        "EXHAUSTED",
        "INCOMPLETE",
        "INVALID",
    )
    logger.info("R14.1 terminal status audit complete")


def test_catalog_digest_and_independent_replay_reject_forged_dto(
    grammar_report: ObserverGrammarEnumerationV2,
) -> None:
    logger.info("R14.1 catalog replay validation start")
    assert verify_observer_grammar_enumeration_v2(grammar_report)
    first = grammar_report.candidates[0]
    forged = replace(first, digest="0" * 64)
    assert type(forged) is ObserverCandidateV2
    assert not verify_observer_grammar_enumeration_v2(
        replace(
            grammar_report,
            candidates=(forged,) + grammar_report.candidates[1:],
        )
    )
    assert not verify_observer_grammar_enumeration_v2(
        replace(grammar_report, catalog_digest="0" * 64)
    )
    assert not verify_observer_grammar_enumeration_v2(
        replace(grammar_report, complete=False)
    )
    logger.info("R14.1 catalog replay validation complete")


def test_response_kind_hook_cannot_mutate_prior_catalog_candidate() -> None:
    logger.info("R14.1 response-kind hook rejection start")
    report = enumerate_observer_grammar_v2()
    first = report.candidates[0]
    hook_called = False

    class Trap:
        def __eq__(self, other: object) -> bool:
            nonlocal hook_called
            hook_called = True
            object.__setattr__(
                first,
                "observer",
                Apply(PrimitiveId.CREST, Input()),
            )
            return True

    poisoned = replace(report.candidates[-1], response_kind=Trap())
    hostile = replace(
        report,
        candidates=report.candidates[:-1] + (poisoned,),
    )
    assert not verify_observer_grammar_enumeration_v2(hostile)
    assert hook_called is False
    assert type(first.observer) is Input
    logger.info("R14.1 response-kind hook rejection exit")
