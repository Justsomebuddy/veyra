"""Direct level-1 P3-T certificate test."""

from src.core.certify_observer_network import certify_observer_network_p3t


def test_direct_certificate_is_exact_and_nonpromoting():
    cert = certify_observer_network_p3t()
    assert cert.passed is True and cert.level == 1
    assert cert.name == "observer_network_p3t"
    assert cert.detail == (
        "observers=5 edges=7 raw_a2_rows=112 pairs=8 triples=7 "
        "triangles=2 isomorphisms=1 attacks=18 promotions=0"
    )
