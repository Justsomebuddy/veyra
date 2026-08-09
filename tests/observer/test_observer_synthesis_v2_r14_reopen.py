"""Focused regressions for the reopened R14 accounting/provenance blockers."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core import observer_synthesis_v2_budget as budget_module
from src.core import observer_synthesis_v2_grammar as grammar_module
from src.core import observer_synthesis_v2_receipts as receipts_module
from src.core.observer_synthesis_v2_baselines import build_trial_subject_manifest_v2
from src.core.observer_synthesis_v2_budget import (
    BudgetLedger,
    BudgetLimitExceeded,
    BudgetLimits,
)
from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES, DEFAULT_LOCKED_CORPUS
from src.core.observer_synthesis_v2_grammar import (
    EXPECTED_DEFAULT_CANDIDATES,
    enumerate_observer_grammar_v2,
)
from src.core.observer_synthesis_v2_receipts import (
    build_receipts_from_validated_trial_v2,
)
from src.core.observer_synthesis_v2_trial import run_locked_trials_v2
from src.core.observer_synthesis_v2_trial_assembly import (
    assemble_locked_trial_report_v2,
)
from src.core.observer_synthesis_v2_trial_validation import (
    DEFAULT_LOCKED_WINNER_V2,
    InvalidTrialV2,
    snapshot_locked_corpus_for_trial_v2,
    snapshot_locked_winner_v2,
)
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


def test_precharged_catalog_constructs_each_candidate_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One fixed-worker catalog means exactly 1,565 constructed/charged DTOs."""
    logger.info("R14 reopened once-constructed catalog test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 1_000)
    original = grammar_module.ObserverCandidateV2
    constructed = 0

    def counted(*args: object) -> object:
        nonlocal constructed
        constructed += 1
        return original(*args)

    monkeypatch.setattr(grammar_module, "ObserverCandidateV2", counted)
    ledger = BudgetLedger()
    catalog = enumerate_observer_grammar_v2(ledger=ledger)
    report = fit_observer_cegis_v2(
        catalog,
        DEFAULT_CASES[:2],
        precharged_ledger=ledger,
    )
    assert report.status is SynthesisStatus.FOUND
    assert report.ledger is not None
    assert constructed == EXPECTED_DEFAULT_CANDIDATES == 1565
    assert report.ledger.candidates == constructed
    assert report.ledger.candidates <= report.ledger.limits.candidate_limit == 2048
    logger.info("R14 reopened once-constructed catalog test exit")


def test_candidate_cutoff_precedes_the_unfunded_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The 1,565th DTO is never constructed under a 1,564-candidate ledger."""
    logger.info("R14 reopened construction cutoff test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 2_000)
    original = grammar_module.ObserverCandidateV2
    constructed = 0

    def counted(*args: object) -> object:
        nonlocal constructed
        constructed += 1
        return original(*args)

    monkeypatch.setattr(grammar_module, "ObserverCandidateV2", counted)
    ledger = BudgetLedger(BudgetLimits(candidate_limit=1564))
    with pytest.raises(BudgetLimitExceeded, match="candidate-limit"):
        enumerate_observer_grammar_v2(ledger=ledger)
    assert constructed == ledger.snapshot().candidates == 1564
    logger.info("R14 reopened construction cutoff test exit")


def test_catalog_clone_cannot_reuse_construction_receipt_or_ledger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second set of 1,565 DTOs cannot spend the first set's receipt."""
    logger.info("R14 reopened catalog clone receipt test entry")
    monkeypatch.setattr(budget_module, "_monotonic_ns", lambda: 2_500)
    ledger = BudgetLedger()
    catalog = enumerate_observer_grammar_v2(ledger=ledger)
    clones = tuple(replace(candidate) for candidate in catalog.candidates)
    cursor = 0
    cloned_strata = []
    for stratum in catalog.strata:
        stop = cursor + len(stratum.candidates)
        cloned_strata.append(replace(stratum, candidates=clones[cursor:stop]))
        cursor = stop
    forged = replace(
        catalog,
        strata=tuple(cloned_strata),
        candidates=clones,
    )
    report = fit_observer_cegis_v2(
        forged,
        DEFAULT_CASES[:2],
        precharged_ledger=ledger,
    )
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-exact-default-catalog"
    assert report.winner is None
    logger.info("R14 reopened catalog clone receipt test exit")


def test_grammar_byte_cutoffs_precede_seed_and_stratum_dto_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Grammar-owned byte ceilings reject before the unfunded DTO exists."""
    logger.info("R14 reopened grammar byte preflight test entry")
    small = enumerate_observer_grammar_v2(
        replace(grammar_module.DEFAULT_GRAMMAR, max_cost=1)
    )
    seed_bytes = len(small.strata[0].candidates[0].canonical)
    next_bytes = len(
        next(
            row.canonical
            for row in small.strata[1].candidates
            if b'"primitive":"tail"' in row.canonical
        )
    )
    original = grammar_module.ObserverCandidateV2
    constructed = 0

    def counted(*args: object) -> object:
        nonlocal constructed
        constructed += 1
        return original(*args)

    monkeypatch.setattr(grammar_module, "ObserverCandidateV2", counted)
    with pytest.raises(
        grammar_module.ObserverGrammarV2Error,
        match="v2-canonical-bytes-limit",
    ):
        enumerate_observer_grammar_v2(
            replace(
                grammar_module.DEFAULT_GRAMMAR,
                grammar_id="seed-byte-preflight",
                canonical_bytes_limit=seed_bytes - 1,
            )
        )
    assert constructed == 0
    with pytest.raises(
        grammar_module.ObserverGrammarV2Error,
        match="v2-canonical-bytes-limit",
    ):
        enumerate_observer_grammar_v2(
            replace(
                grammar_module.DEFAULT_GRAMMAR,
                grammar_id="stratum-byte-preflight",
                max_cost=1,
                canonical_bytes_limit=seed_bytes + next_bytes - 1,
            )
        )
    assert constructed == 1
    logger.info("R14 reopened grammar byte preflight test exit")


def test_pure_trial_assembly_rejects_unbranded_and_transplanted_subjects() -> None:
    """Official payload digests do not authorize copied nonwinner DTOs."""
    logger.info("R14 reopened subject provenance test entry")
    report = run_locked_trials_v2()
    winner = snapshot_locked_winner_v2(DEFAULT_LOCKED_WINNER_V2)
    corpus = snapshot_locked_corpus_for_trial_v2(DEFAULT_LOCKED_CORPUS)
    manifest = build_trial_subject_manifest_v2(winner)

    unbranded = replace(report.subjects[1], provenance=None)
    with pytest.raises(InvalidTrialV2, match="invalid-trial-subject-provenance"):
        assemble_locked_trial_report_v2(
            winner,
            corpus,
            manifest,
            report.subjects[:1] + (unbranded,) + report.subjects[2:],
        )

    transplanted = report.subjects[:2] + (report.subjects[1],) + report.subjects[3:]
    with pytest.raises(InvalidTrialV2, match="invalid-trial-subject-provenance"):
        assemble_locked_trial_report_v2(winner, corpus, manifest, transplanted)
    logger.info("R14 reopened subject provenance test exit")


def test_receipt_builder_rejects_nonwinner_case_transplant_before_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A copied case cannot retain official subject/report digests or reach R12."""
    logger.info("R14 reopened receipt provenance test entry")
    report = run_locked_trials_v2()
    nonwinner = report.subjects[3]
    assert report.subjects[0].cases[0] == nonwinner.cases[0]
    forged_subject = replace(
        nonwinner,
        cases=(report.subjects[0].cases[0],) + nonwinner.cases[1:],
    )
    forged_report = replace(
        report,
        subjects=report.subjects[:3] + (forged_subject,) + report.subjects[4:],
    )

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("unbranded receipt replay reached")

    monkeypatch.setattr(receipts_module, "_build_receipt_row_v2", forbidden)
    with pytest.raises(RuntimeError, match="r14.5-invalid-validated-trial"):
        build_receipts_from_validated_trial_v2(forged_report)
    logger.info("R14 reopened receipt provenance test exit")


def test_receipt_provenance_preflight_never_invokes_hostile_role_hook() -> None:
    """Exact DTO branding rejects a role hook before canonical serialization."""
    logger.info("R14 reopened hostile provenance preflight test entry")
    report = run_locked_trials_v2()
    called = False

    class Trap:
        @property
        def value(self) -> str:
            nonlocal called
            called = True
            return "BASELINE"

    forged_subject = replace(report.subjects[1], role=Trap())
    forged_report = replace(
        report,
        subjects=(report.subjects[0], forged_subject) + report.subjects[2:],
    )
    with pytest.raises(RuntimeError, match="r14.5-invalid-validated-trial"):
        build_receipts_from_validated_trial_v2(forged_report)
    assert called is False
    logger.info("R14 reopened hostile provenance preflight test exit")
