"""Collision-safe public integration checks for released P3-N2."""

from src import core
import src.core.prime_power_reduction_network as direct
import src.core.prime_power_reduction_network_public as public


def test_p3n2_root_exports_are_collision_safe_and_exact():
    assert len(public.__all__) == 56 == len(set(public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(public, name) for name in public.__all__)
    assert core.P3N2_ARTIFACT_SHA256 == (
        "77f5a9891115122967036b99245cf410662d251bdf92f79da150f384cb2410cf"
    )
    assert core.P3N2_LEDGER_DIGEST_ORACLE == (
        "2c4cad693acc80b78d33ababff5afbc102d30f018f533957973a0e41019b91e9"
    )
    assert core.P3N2Judgment is direct.PrimePowerReductionJudgment
    assert core.p3n2_reduction_judgment is direct.prime_power_reduction_judgment
    assert core.P3N2Judgment is not core.P3C2GeneratedTransportCoherence
