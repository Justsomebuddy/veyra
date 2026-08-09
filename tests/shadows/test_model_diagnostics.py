from fractions import Fraction

import pytest

from src.core.model_diagnostics import (
    ModelObservation,
    anomaly_obstruction_card,
    baseline_model_observations,
    canonical_model_observations,
    compare_model_reports,
    model_diagnostics_checklist,
    model_fit_report,
    residual_row,
)
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_residual_row_records_signed_and_absolute_error():
    row = residual_row(ModelObservation("p1", ratio_from_ints(9, 4), ratio_from_ints(2)), ratio_from_ints(1, 2))
    assert row.status == "within-band"
    assert row.obstruction == "none"
    assert row.as_dict()["residual"] == "1/4"
    assert ratio_shadow(row.absolute_residual) == Fraction(1, 4)


def test_model_fit_report_aggregates_candidate_errors():
    report = model_fit_report("candidate", canonical_model_observations(), ratio_from_ints(1, 2))
    assert report.status == "fit"
    assert report.as_dict()["rows"] == 3
    assert ratio_shadow(report.total_absolute_error) == Fraction(1, 2)
    assert ratio_shadow(report.max_absolute_error) == Fraction(1, 4)


def test_model_comparison_prefers_lower_total_error():
    candidate = model_fit_report("candidate", canonical_model_observations(), ratio_from_ints(1, 2))
    baseline = model_fit_report("baseline", baseline_model_observations(), ratio_from_ints(2))
    row = compare_model_reports("candidate-vs-baseline", candidate, baseline)
    assert row.status == "improved"
    assert ratio_shadow(row.candidate_error) == Fraction(1, 2)
    assert ratio_shadow(row.baseline_error) == Fraction(5, 2)


def test_anomaly_obstruction_card_blocks_outlier():
    card = anomaly_obstruction_card()
    assert card.name == "model-anomaly-obstruction"
    assert card.relation == "blocked"
    assert card.obstruction == "residual-outlier"


def test_model_fit_rejects_empty_observation_set():
    with pytest.raises(ValueError):
        model_fit_report("empty", (), ratio_from_ints(1))
    with pytest.raises(ValueError):
        ModelObservation("", ratio_from_ints(1), ratio_from_ints(1))


def test_model_diagnostics_checklist_names_obstruction():
    text = "\n".join(model_diagnostics_checklist())
    assert "residual" in text
    assert "obstruction" in text
    assert len(model_diagnostics_checklist()) == 4
