"""R14.3a closed case-protocol regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging

import pytest

from src.core.proof_core_types import Bound, Pulse, Silence
from src.core.observer_synthesis_v2_protocol import (
    CacheDisposition,
    EvaluationInvalidReason,
    ExpectedRelation,
    MAX_CASE_ID,
    ObserverCaseV2,
    ObserverSynthesisProtocolError,
    SplitId,
    build_observer_case_v2,
    clone_payload_digest,
    ordered_payload_digest,
    validate_observer_case_v2,
)

logger = logging.getLogger(__name__)


def _case() -> ObserverCaseV2:
    logger.debug("_case fixture helper entry")
    result = build_observer_case_v2(
        7,
        70,
        SplitId.TRAIN,
        Silence(),
        Pulse(Silence()),
        ExpectedRelation.SEPARATE,
        True,
    )
    logger.debug("_case fixture helper exit")
    return result


def test_exact_closed_protocol_vocabularies() -> None:
    logger.info("R14.3a protocol vocabulary test entry")
    assert tuple(item.value for item in ExpectedRelation) == (
        "ECHO",
        "SEPARATE",
        "DOMAIN_BLOCKED",
    )
    assert tuple(item.value for item in SplitId) == (
        "TRAIN",
        "HOLDOUT",
        "UNSEEN",
        "ADVERSARIAL",
    )
    assert tuple(item.value for item in CacheDisposition) == ("MISS", "HIT")
    assert tuple(item.value for item in EvaluationInvalidReason) == (
        "invalid-case",
        "invalid-observer",
        "invalid-ledger",
        "invalid-cache",
        "invalid-outcome",
    )
    logger.info("R14.3a protocol vocabulary test exit")


def test_ordered_payload_digest_never_collapses_reversed_sides() -> None:
    logger.info("R14.3a ordered digest test entry")
    left, right = Silence(), Pulse(Silence())
    forward = ordered_payload_digest(left, right)
    reverse = ordered_payload_digest(right, left)
    assert forward != reverse
    first = build_observer_case_v2(
        1, 10, SplitId.TRAIN, left, right, ExpectedRelation.SEPARATE, True
    )
    second = build_observer_case_v2(
        2, 10, SplitId.TRAIN, right, left, ExpectedRelation.SEPARATE, True
    )
    assert first.payload_digest == forward
    assert second.payload_digest == reverse
    assert first.clone_digest == second.clone_digest
    assert first.clone_digest == clone_payload_digest(left, right)
    assert first.case_digest != second.case_digest
    logger.info("R14.3a ordered digest test exit")


def test_case_is_frozen_and_all_bindings_replay_exactly() -> None:
    logger.info("R14.3a frozen case test entry")
    case = _case()
    assert validate_observer_case_v2(case) is case
    with pytest.raises(FrozenInstanceError):
        case.case_id = 8  # type: ignore[misc]
    for field in ("payload_digest", "case_digest"):
        with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-binding"):
            validate_observer_case_v2(replace(case, **{field: "0" * 64}))
    logger.info("R14.3a frozen case test exit")


@pytest.mark.parametrize(
    "case_id",
    (0, -1, True, 1.0, "1", MAX_CASE_ID + 1, 1 << 4096),
)
def test_case_ids_are_exact_positive_integers(case_id: object) -> None:
    logger.info("R14.3a positive ID test entry type=%s", type(case_id).__name__)
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-header"):
        build_observer_case_v2(
            case_id,
            10,
            SplitId.TRAIN,
            Silence(),
            Pulse(Silence()),
            ExpectedRelation.SEPARATE,
            True,
        )
    logger.info("R14.3a positive ID test exit")


@pytest.mark.parametrize(
    ("split", "expected"),
    (
        ("TRAIN", ExpectedRelation.SEPARATE),
        (SplitId.TRAIN, "SEPARATE"),
        (lambda: None, ExpectedRelation.SEPARATE),
        (SplitId.TRAIN, lambda: None),
    ),
)
def test_strings_and_callables_cannot_extend_closed_enums(
    split: object,
    expected: object,
) -> None:
    logger.info("R14.3a closed enum test entry")
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-header"):
        build_observer_case_v2(
            1,
            10,
            split,
            Silence(),
            Pulse(Silence()),
            expected,
            True,
        )
    logger.info("R14.3a closed enum test exit")


@pytest.mark.parametrize("term", (Bound(0), "silence", lambda: Silence()))
def test_nonclosed_or_extension_payloads_are_rejected(term: object) -> None:
    logger.info("R14.3a invalid recurrence test entry type=%s", type(term).__name__)
    with pytest.raises(
        ObserverSynthesisProtocolError,
        match="invalid-case-recurrence",
    ):
        build_observer_case_v2(
            1,
            10,
            SplitId.TRAIN,
            term,
            Silence(),
            ExpectedRelation.ECHO,
            True,
        )
    logger.info("R14.3a invalid recurrence test exit")


def test_cyclic_and_resource_exhausting_recurrences_fail_closed() -> None:
    logger.info("R14.3a recurrence resource test entry")
    cyclic = Pulse(Silence())
    object.__setattr__(cyclic, "tail", cyclic)
    deep = Silence()
    for _ in range(130):
        deep = Pulse(deep)
    for hostile in (cyclic, deep):
        with pytest.raises(
            ObserverSynthesisProtocolError,
            match="invalid-case-recurrence",
        ):
            build_observer_case_v2(
                1,
                10,
                SplitId.TRAIN,
                hostile,
                Silence(),
                ExpectedRelation.ECHO,
                True,
            )
    logger.info("R14.3a recurrence resource test exit")


def test_case_type_and_hostile_mutation_fail_closed() -> None:
    logger.info("R14.3a hostile case test entry")

    class ForgedCase(ObserverCaseV2):
        pass

    case = _case()
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-type"):
        validate_observer_case_v2(
            ForgedCase(
                case.case_id,
                case.group_id,
                case.split,
                case.left,
                case.right,
                case.expected,
                case.required_for_winner,
                case.payload_digest,
                case.clone_digest,
                case.case_digest,
            )
        )
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-type"):
        validate_observer_case_v2(object())

    object.__setattr__(case, "expected", "SEPARATE")
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-fields"):
        validate_observer_case_v2(case)
    logger.info("R14.3a hostile case test exit")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("group_id", 0),
        ("group_id", True),
        ("group_id", MAX_CASE_ID + 1),
        ("required_for_winner", "true"),
        ("payload_digest", None),
        ("clone_digest", "g" * 64),
        ("case_digest", b"0" * 64),
    ),
)
def test_group_flag_and_malformed_digest_fields_are_protocol_invalid(
    field: str,
    value: object,
) -> None:
    logger.info("R14.3a bound field test entry field=%s", field)
    with pytest.raises(ObserverSynthesisProtocolError, match="invalid-case-fields"):
        validate_observer_case_v2(replace(_case(), **{field: value}))
    logger.info("R14.3a bound field test exit field=%s", field)
