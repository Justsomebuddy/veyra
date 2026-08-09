"""R14.3a locked corpus and split-leakage regressions."""
from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging

import pytest

from src.core.observer_synthesis_v2_corpus import (
    CORPUS_SCHEMA,
    DEFAULT_CASES,
    DEFAULT_LOCKED_CORPUS,
    EXPECTED_DEFAULT_CORPUS_DIGEST,
    MAX_CORPUS_CASES,
    LockedObserverCorpusV2,
    ObserverSynthesisCorpusError,
    build_locked_corpus_v2,
    cases_for_split_v2,
    validate_locked_corpus_v2,
    winner_required_cases_v2,
)
from src.core.observer_synthesis_v2_protocol import (
    ExpectedRelation,
    SplitId,
    build_observer_case_v2,
)

logger = logging.getLogger(__name__)


def test_default_corpus_has_exact_locked_manifest() -> None:
    logger.info("R14.3a exact corpus manifest test entry")
    assert DEFAULT_LOCKED_CORPUS.schema == CORPUS_SCHEMA
    assert DEFAULT_LOCKED_CORPUS.cases == DEFAULT_CASES
    assert DEFAULT_LOCKED_CORPUS.corpus_digest == EXPECTED_DEFAULT_CORPUS_DIGEST
    assert EXPECTED_DEFAULT_CORPUS_DIGEST == (
        "050352b6964eada5f3bb36d68a7989b11d781ab89e20a92aeaaa9bfe5ce146b1"
    )
    assert tuple(
        (
            case.case_id,
            case.group_id,
            case.split,
            case.expected,
            case.required_for_winner,
        )
        for case in DEFAULT_CASES
    ) == (
        (101, 1001, SplitId.TRAIN, ExpectedRelation.SEPARATE, True),
        (102, 1002, SplitId.TRAIN, ExpectedRelation.ECHO, True),
        (201, 2001, SplitId.HOLDOUT, ExpectedRelation.SEPARATE, True),
        (202, 2002, SplitId.HOLDOUT, ExpectedRelation.ECHO, True),
        (301, 3001, SplitId.UNSEEN, ExpectedRelation.ECHO, True),
        (302, 3002, SplitId.UNSEEN, ExpectedRelation.SEPARATE, True),
        (401, 4001, SplitId.ADVERSARIAL, ExpectedRelation.SEPARATE, True),
        (402, 4002, SplitId.ADVERSARIAL, ExpectedRelation.ECHO, True),
        (403, 4003, SplitId.ADVERSARIAL, ExpectedRelation.DOMAIN_BLOCKED, False),
        (404, 4003, SplitId.ADVERSARIAL, ExpectedRelation.DOMAIN_BLOCKED, False),
    )
    assert validate_locked_corpus_v2(DEFAULT_LOCKED_CORPUS) is DEFAULT_LOCKED_CORPUS
    logger.info("R14.3a exact corpus manifest test exit")


def test_split_ids_and_ordered_payloads_are_pairwise_disjoint() -> None:
    logger.info("R14.3a split disjointness test entry")
    seen_ids: set[int] = set()
    seen_payloads: set[str] = set()
    seen_groups: set[int] = set()
    seen_clones: set[str] = set()
    counts = []
    for split in SplitId:
        cases = cases_for_split_v2(DEFAULT_LOCKED_CORPUS, split)
        counts.append(len(cases))
        ids = {case.case_id for case in cases}
        payloads = {case.payload_digest for case in cases}
        groups = {case.group_id for case in cases}
        clones = {case.clone_digest for case in cases}
        assert not seen_ids.intersection(ids)
        assert not seen_payloads.intersection(payloads)
        assert not seen_groups.intersection(groups)
        assert not seen_clones.intersection(clones)
        seen_ids.update(ids)
        seen_payloads.update(payloads)
        seen_groups.update(groups)
        seen_clones.update(clones)
    assert tuple(counts) == (2, 2, 2, 4)
    assert len(seen_ids) == len(seen_payloads) == 10
    logger.info("R14.3a split disjointness test exit")


def test_reverse_equal_and_tail_boundary_cases_are_precommitted() -> None:
    logger.info("R14.3a adversarial shape test entry")
    by_id = {case.case_id: case for case in DEFAULT_CASES}
    assert by_id[101].clone_digest != by_id[401].clone_digest
    assert by_id[403].payload_digest != by_id[404].payload_digest
    assert by_id[403].clone_digest == by_id[404].clone_digest
    assert by_id[403].group_id == by_id[404].group_id
    assert by_id[202].left == by_id[202].right
    assert by_id[402].left == by_id[402].right
    assert type(by_id[403].left).__name__ == "Silence"
    assert type(by_id[404].right).__name__ == "Silence"
    logger.info("R14.3a adversarial shape test exit")


def test_tail_boundaries_are_diagnostics_not_winner_obligations() -> None:
    logger.info("R14.3a winner obligation test entry")
    required = winner_required_cases_v2(DEFAULT_LOCKED_CORPUS)
    assert tuple(case.case_id for case in required) == (
        101, 102, 201, 202, 301, 302, 401, 402,
    )
    assert tuple(case.case_id for case in DEFAULT_CASES if not case.required_for_winner) == (
        403, 404,
    )
    logger.info("R14.3a winner obligation test exit")


def test_locked_corpus_and_cases_tuple_are_immutable() -> None:
    logger.info("R14.3a corpus frozen test entry")
    with pytest.raises(FrozenInstanceError):
        DEFAULT_LOCKED_CORPUS.corpus_digest = "0" * 64  # type: ignore[misc]
    assert type(DEFAULT_LOCKED_CORPUS.cases) is tuple
    logger.info("R14.3a corpus frozen test exit")


@pytest.mark.parametrize(
    "cases",
    (
        DEFAULT_CASES[:-4],
        tuple(reversed(DEFAULT_CASES)),
        DEFAULT_CASES + (DEFAULT_CASES[0],),
        (DEFAULT_CASES[0],) * len(DEFAULT_CASES),
    ),
)
def test_missing_reordered_or_duplicate_cases_fail_closed(
    cases: tuple[object, ...],
) -> None:
    logger.info("R14.3a invalid corpus closure test entry")
    with pytest.raises(ObserverSynthesisCorpusError):
        build_locked_corpus_v2(cases)  # type: ignore[arg-type]
    logger.info("R14.3a invalid corpus closure test exit")


def test_corpus_binding_case_mutation_and_split_extension_fail_closed() -> None:
    logger.info("R14.3a corpus mutation test entry")
    forged_digest = replace(DEFAULT_LOCKED_CORPUS, corpus_digest="0" * 64)
    with pytest.raises(ObserverSynthesisCorpusError, match="invalid-corpus-binding"):
        validate_locked_corpus_v2(forged_digest)

    forged_case = replace(DEFAULT_CASES[0], expected="SEPARATE")
    forged_cases = (forged_case,) + DEFAULT_CASES[1:]
    forged = LockedObserverCorpusV2(
        CORPUS_SCHEMA,
        forged_cases,  # type: ignore[arg-type]
        DEFAULT_LOCKED_CORPUS.corpus_digest,
    )
    with pytest.raises(ObserverSynthesisCorpusError, match="invalid-corpus-case"):
        validate_locked_corpus_v2(forged)
    with pytest.raises(ObserverSynthesisCorpusError, match="invalid-corpus-split"):
        cases_for_split_v2(DEFAULT_LOCKED_CORPUS, "TRAIN")
    logger.info("R14.3a corpus mutation test exit")


def test_hostile_corpus_shapes_fail_before_dynamic_access() -> None:
    logger.info("R14.3a hostile corpus test entry")

    class Trap:
        def __iter__(self) -> object:
            raise AssertionError("iteration trap")

    for hostile in (object(), Trap(), [], "corpus"):
        with pytest.raises(ObserverSynthesisCorpusError):
            validate_locked_corpus_v2(hostile)
    logger.info("R14.3a hostile corpus test exit")


def test_oversize_corpus_rejects_before_case_iteration() -> None:
    logger.info("R14.3a corpus length preflight test entry")
    oversized = (object(),) + (DEFAULT_CASES[0],) * MAX_CORPUS_CASES
    with pytest.raises(ObserverSynthesisCorpusError, match="invalid-corpus-cases"):
        build_locked_corpus_v2(oversized)  # type: ignore[arg-type]
    logger.info("R14.3a corpus length preflight test exit")


@pytest.mark.parametrize("mode", ("group", "clone"))
def test_cross_split_group_or_reverse_clone_leakage_is_rejected(mode: str) -> None:
    logger.info("R14.3a clone leakage test entry mode=%s", mode)
    source = DEFAULT_CASES[0]
    holdout = DEFAULT_CASES[2]
    leak = build_observer_case_v2(
        holdout.case_id,
        source.group_id if mode == "group" else holdout.group_id,
        SplitId.HOLDOUT,
        holdout.left if mode == "group" else source.right,
        holdout.right if mode == "group" else source.left,
        holdout.expected if mode == "group" else source.expected,
        True,
    )
    cases = DEFAULT_CASES[:2] + (leak,) + DEFAULT_CASES[3:]
    with pytest.raises(
        ObserverSynthesisCorpusError,
        match="corpus-cross-split-clone-leakage",
    ):
        build_locked_corpus_v2(cases)
    logger.info("R14.3a clone leakage test exit mode=%s", mode)
