"""Collision-safe public integration checks for released P3-A1b."""

from src import core
import src.core.prime_power_productive_bridge as direct
import src.core.prime_power_productive_bridge_public as public


def test_p3a1b_root_exports_are_collision_safe_and_exact():
    assert len(public.__all__) == 56 == len(set(public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(public, name) for name in public.__all__)
    assert core.P3A1B_ARTIFACT_SHA256 == "f0382dee0f2f0fe9434feca7357a25abd27f47d5f16b278302d83f7d31d0382e"
    assert core.P3A1B_PRESSURE_ARTIFACT_SHA256 == "bb21c6a16d19af66dbc58109bd8d4882619152e795115c15b5519445c3c1f7b5"
    assert core.P3A1BProductiveBridgeJudgment is direct.ProductiveBridgeJudgment
    assert core.p3a1b_establish_productive_family_bridge is direct.establish_productive_family_bridge
    assert core.P3A1BProductiveBridgeJudgment is not core.P3N1FamilyJudgment
