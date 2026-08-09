"""Collision-safe public integration checks for released P3-T."""

from src import core
import src.core.observer_network as direct
import src.core.observer_network_public as public


def test_p3t_root_exports_are_collision_safe_and_exact():
    assert len(public.__all__) == 53 == len(set(public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(public, name) for name in public.__all__)
    assert core.P3T_NETWORK_VERSION == direct.NETWORK_VERSION
    assert core.P3TObserverNetworkSource is direct.ObserverNetworkSource
    assert core.P3TTranslationSource is direct.TranslationSource
    assert core.p3t_observer_network_judgment is direct.observer_network_judgment
    assert core.P3TObserverNetworkJudgment is not core.P3N1FamilyJudgment
