from src.core.likelihood_geometry import (
    domain_residual_certificate,
    finite_likelihood_segments,
    likelihood_geometry_checklist,
    likelihood_geometry_summary,
    likelihood_grid,
    likelihood_peak_card,
    residual_family_certificates,
)
from src.core.model_diagnostics import ModelObservation
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_likelihood_grid_exposes_finite_geometry():
    points = likelihood_grid()
    assert [ratio_shadow(point.parameter) for point in points] == [ratio_shadow(ratio_from_ints(1, 4)), ratio_shadow(ratio_from_ints(1, 2)), ratio_shadow(ratio_from_ints(3, 4))]
    assert [ratio_shadow(point.likelihood) for point in points] == [ratio_shadow(ratio_from_ints(3, 256)), ratio_shadow(ratio_from_ints(1, 16)), ratio_shadow(ratio_from_ints(27, 256))]


def test_likelihood_segments_and_peak_card_are_exact():
    points = likelihood_grid()
    segments = finite_likelihood_segments(points)
    peak = likelihood_peak_card(points)
    assert [item.relation for item in segments] == ["rising", "rising"]
    assert [ratio_shadow(item.slope) for item in segments] == [ratio_shadow(ratio_from_ints(13, 64)), ratio_shadow(ratio_from_ints(11, 64))]
    assert peak.status == "unique-peak"
    assert ratio_shadow(peak.parameter) == ratio_shadow(ratio_from_ints(3, 4))


def test_domain_residual_certificates_certify_and_block_domains():
    certs = residual_family_certificates()
    assert [item.domain for item in certs] == ["linear-motion", "sensor-spike"]
    assert [item.status for item in certs] == ["certified", "blocked"]
    assert certs[1].obstruction == "residual-outlier"


def test_domain_residual_certificate_validates_domain_and_summary():
    cert = domain_residual_certificate("toy", (ModelObservation("a", ratio_from_ints(1), ratio_from_ints(1)),), ratio_from_ints(0))
    assert cert.status == "certified"
    assert likelihood_geometry_summary() == {"likelihood_points": 3, "segments": 2, "rising_segments": 2, "residual_certificates": 2, "fit_domains": 1, "blocked_domains": 1, "checklist": 4}
    assert len(likelihood_geometry_checklist()) == 4
