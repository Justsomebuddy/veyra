"""Collision-safe public integration checks for released P3-N1."""

from src import core
import src.core.padic_family_introduction as direct
import src.core.padic_family_introduction_public as public
import src.core.padic_family_introduction_types as types


def test_p3n1_root_exports_are_collision_safe_and_exact():
    assert len(public.__all__) == 33 == len(set(public.__all__))
    assert len(core.__all__) == len(set(core.__all__))
    assert set(public.__all__).issubset(core.__all__)
    assert all(getattr(core, name) is getattr(public, name) for name in public.__all__)
    assert core.P3N1_ARTIFACT_SHA256 == direct.ARTIFACT_SHA256
    assert core.P3N1FamilyJudgment is types.N1FamilyJudgment
    assert core.P3N1IntroductionPackage is types.N1IntroductionPackage
    assert core.p3n1_introduce_integer_residue_family is direct.introduce_integer_residue_family
    assert core.P3N1FamilyJudgment is not core.Pomega2Judgment
