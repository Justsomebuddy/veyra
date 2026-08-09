"""R14.4 exact in-process split and baseline trial regressions."""
from __future__ import annotations

import logging

from src.core.observer_synthesis_v2_baselines import (
    EXPECTED_SUBJECT_BYTES,
    EXPECTED_SUBJECT_DIGESTS,
    EXPECTED_SUBJECT_IDS,
    EXPECTED_SUBJECT_MANIFEST_DIGEST,
    build_trial_subject_manifest_v2,
)
from src.core.observer_synthesis_v2_protocol import SplitId
from src.core.observer_synthesis_v2_trial import (
    EXPECTED_GUARANTEE_DIGEST,
    EXPECTED_TRIAL_REPORT_DIGEST,
    EXPECTED_WINNER_MATCHES,
    EXPECTED_WINNER_RELATIONS,
    run_locked_trials_v2,
)
from src.core.observer_synthesis_v2_trial_types import TrialSubjectRoleV2
from src.core.observer_synthesis_v2_trial_validation import DEFAULT_LOCKED_WINNER_V2

logger = logging.getLogger(__name__)


def test_exact_five_subject_manifest_is_predeclared() -> None:
    logger.info("R14.4 exact subject manifest test entry")
    manifest = build_trial_subject_manifest_v2(DEFAULT_LOCKED_WINNER_V2)
    assert tuple(row.subject_id for row in manifest.subjects) == EXPECTED_SUBJECT_IDS
    assert tuple(row.digest for row in manifest.subjects) == EXPECTED_SUBJECT_DIGESTS
    assert tuple(len(row.canonical) for row in manifest.subjects) == EXPECTED_SUBJECT_BYTES
    assert manifest.manifest_digest == EXPECTED_SUBJECT_MANIFEST_DIGEST
    assert tuple(row.role for row in manifest.subjects) == (
        TrialSubjectRoleV2.SYNTHESIZED,
        TrialSubjectRoleV2.BASELINE,
        TrialSubjectRoleV2.BASELINE,
        TrialSubjectRoleV2.BASELINE,
        TrialSubjectRoleV2.BASELINE,
    )
    assert manifest.subjects[0].canonical == manifest.subjects[3].canonical
    logger.info("R14.4 exact subject manifest test exit")


def test_every_subject_uses_fresh_complete_ten_case_path() -> None:
    logger.info("R14.4 complete subject paths test entry")
    report = run_locked_trials_v2()
    expected_counts = (
        (8, 8, 0, 2),
        (6, 8, 0, 2),
        (2, 8, 2, 2),
        (8, 8, 0, 2),
        (6, 8, 0, 2),
    )
    assert tuple(
        (
            row.required_matched,
            row.required_total,
            row.diagnostic_matched,
            row.diagnostic_total,
        )
        for row in report.subjects
    ) == expected_counts
    assert tuple(row.accounting.candidates for row in report.subjects) == (1,) * 5
    assert tuple(row.accounting.evaluations for row in report.subjects) == (10,) * 5
    assert tuple(row.accounting.canonical_bytes for row in report.subjects) == (
        106, 62, 105, 106, 108,
    )
    assert all(len(row.cases) == 10 for row in report.subjects)
    assert all(row.accounting.retained_output_bytes > 0 for row in report.subjects)
    assert all(not row.accounting.cutoff for row in report.subjects)
    assert report.subjects[0].retained_digest == report.subjects[3].retained_digest
    logger.info("R14.4 complete subject paths test exit")


def test_winner_relation_vector_and_split_summaries_are_exact() -> None:
    logger.info("R14.4 winner split summary test entry")
    winner = run_locked_trials_v2().subjects[0]
    assert tuple(row.case_id for row in winner.cases) == (
        101, 102, 201, 202, 301, 302, 401, 402, 403, 404,
    )
    assert tuple(row.actual.value for row in winner.cases) == EXPECTED_WINNER_RELATIONS
    assert tuple(row.matched for row in winner.cases) == EXPECTED_WINNER_MATCHES
    assert tuple(
        (
            row.split,
            row.total,
            row.required_matched,
            row.required_total,
            row.diagnostic_matched,
            row.diagnostic_total,
        )
        for row in winner.splits
    ) == (
        (SplitId.TRAIN, 2, 2, 2, 0, 0),
        (SplitId.HOLDOUT, 2, 2, 2, 0, 0),
        (SplitId.UNSEEN, 2, 2, 2, 0, 0),
        (SplitId.ADVERSARIAL, 4, 2, 2, 0, 2),
    )
    logger.info("R14.4 winner split summary test exit")


def test_bounded_guarantee_has_exact_counts_and_false_overclaims() -> None:
    logger.info("R14.4 bounded guarantee test entry")
    report = run_locked_trials_v2()
    guarantee = report.guarantee
    assert guarantee.catalog_complete is True
    assert guarantee.train_prefix_minimal is True
    assert (guarantee.train_matched, guarantee.train_total) == (2, 2)
    assert (
        guarantee.postfit_required_matched,
        guarantee.postfit_required_total,
    ) == (6, 6)
    assert (guarantee.all_required_matched, guarantee.all_required_total) == (8, 8)
    assert (guarantee.diagnostic_matched, guarantee.diagnostic_total) == (0, 2)
    assert guarantee.resource_path_complete is True
    assert (
        guarantee.general_completeness,
        guarantee.general_minimality,
        guarantee.novelty,
        guarantee.superiority,
        guarantee.evidence_accepted,
        guarantee.promotion_ready,
        guarantee.taxonomy_changed,
        guarantee.proof_complete,
    ) == (False,) * 8
    assert guarantee.guarantee_digest == EXPECTED_GUARANTEE_DIGEST
    assert report.report_digest == EXPECTED_TRIAL_REPORT_DIGEST
    logger.info("R14.4 bounded guarantee test exit")


def test_repeated_trial_reports_are_byte_identity_equivalent() -> None:
    logger.info("R14.4 deterministic report test entry")
    first = run_locked_trials_v2()
    second = run_locked_trials_v2()
    assert first == second
    assert first.report_digest == second.report_digest
    logger.info("R14.4 deterministic report test exit")
