"""TOCTOU regressions for R14.3b trusted CEGIS catalog snapshots."""
from __future__ import annotations

from dataclasses import replace
import logging

import pytest

from src.core import observer_synthesis_v2_cegis as cegis_module
from src.core import observer_synthesis_v2_cegis_snapshot as snapshot_module
from src.core import observer_synthesis_v2_cegis_validation as validation_module
from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
from src.core.observer_synthesis_v2_cegis_validation import validate_cegis_catalog_v2
from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
from src.core.observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
from src.core.observer_synthesis_v2_types import SynthesisStatus

logger = logging.getLogger(__name__)


class LengthTrap:
    """Fail if a hostile replacement is touched before exact-type rejection."""

    def __len__(self) -> int:
        raise AssertionError("hostile-length-hook-ran")


class GrammarTrap:
    """Fail if grammar attributes are read before exact-type rejection."""

    @property
    def schema(self) -> str:
        raise AssertionError("hostile-grammar-hook-ran")


@pytest.mark.parametrize("mutation", ("cross-row-bytes", "wrong-type"))
def test_snapshot_copy_drift_is_invalid_before_evaluation(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b snapshot-copy drift test entry")
    catalog = enumerate_observer_grammar_v2()
    original_decode = snapshot_module.decode_observer
    decode_calls = 0
    evaluation_calls = 0

    def mutate_after_source_validation(data: bytes) -> object:
        nonlocal decode_calls
        decode_calls += 1
        if decode_calls == 1:
            replacement: object = (
                catalog.candidates[0].canonical
                if mutation == "cross-row-bytes"
                else "not-bytes"
            )
            object.__setattr__(
                catalog.candidates[1],
                "canonical",
                replacement,
            )
        return original_decode(data)

    def unexpected_evaluation(*_args: object, **_kwargs: object) -> bool:
        nonlocal evaluation_calls
        evaluation_calls += 1
        raise AssertionError("malformed-snapshot-reached-evaluation")

    monkeypatch.setattr(snapshot_module, "decode_observer", mutate_after_source_validation)
    monkeypatch.setattr(cegis_module, "evaluate_cegis_case_v2", unexpected_evaluation)
    report = fit_observer_cegis_v2(catalog, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-exact-default-catalog"
    assert report.winner is None
    assert decode_calls >= 1
    assert evaluation_calls == 0
    logger.info("R14.3b snapshot-copy drift test exit")


def test_unexpected_snapshot_runtime_error_is_not_laundered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b snapshot internal crash test entry")
    catalog = enumerate_observer_grammar_v2()

    def crash(_data: bytes) -> object:
        logger.error("synthetic snapshot internal crash")
        raise RuntimeError("synthetic-snapshot-internal-crash")

    monkeypatch.setattr(snapshot_module, "decode_observer", crash)
    with pytest.raises(RuntimeError, match="synthetic-snapshot-internal-crash"):
        validate_cegis_catalog_v2(catalog)
    logger.info("R14.3b snapshot internal crash test exit")


@pytest.mark.parametrize(
    "mutation",
    ("candidate-container", "grammar-trap", "nondefault-grammar"),
)
def test_postvalidation_replacement_is_invalid_without_hostile_hooks(
    mutation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger.info("R14.3b postvalidation replacement test entry mutation=%s", mutation)
    catalog = enumerate_observer_grammar_v2()
    original_verify = validation_module.verify_observer_grammar_enumeration_v2
    evaluation_calls = 0

    def replace_after_verification(report: object, ledger: object = None) -> bool:
        valid = original_verify(report, ledger)
        if valid:
            if mutation == "candidate-container":
                object.__setattr__(catalog, "candidates", LengthTrap())
            elif mutation == "grammar-trap":
                object.__setattr__(catalog, "grammar", GrammarTrap())
            else:
                object.__setattr__(
                    catalog,
                    "grammar",
                    replace(catalog.grammar, grammar_id="coherent-nondefault"),
                )
        return valid

    def unexpected_evaluation(*_args: object, **_kwargs: object) -> bool:
        nonlocal evaluation_calls
        evaluation_calls += 1
        raise AssertionError("postvalidation-replacement-reached-evaluation")

    monkeypatch.setattr(
        validation_module,
        "verify_observer_grammar_enumeration_v2",
        replace_after_verification,
    )
    monkeypatch.setattr(cegis_module, "evaluate_cegis_case_v2", unexpected_evaluation)
    report = fit_observer_cegis_v2(catalog, DEFAULT_CASES[:2])
    assert report.status is SynthesisStatus.INVALID
    assert report.detail == "invalid-exact-default-catalog"
    assert evaluation_calls == 0
    logger.info("R14.3b postvalidation replacement test exit mutation=%s", mutation)
