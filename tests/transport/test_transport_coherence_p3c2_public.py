"""Collision-safe P3-C2 public/root API regression."""

import src.core as core
from src.core import transport_coherence as private
from src.core import transport_coherence_public as public


def test_p3c2_public_root_exports_are_unique_and_identity_preserving():
    assert len(public.__all__) == len(set(public.__all__)) == 57
    assert len(core.__all__) == len(set(core.__all__))
    assert set(public.__all__) <= set(core.__all__)
    assert all(getattr(core, name) is getattr(public, name) for name in public.__all__)
    assert public.P3C2_ARTIFACT_SHA256 == "4804c5637e89530a4a00ec6ad905c20d0a93c2b63fb941f1cffc70d7a3c7e395"
    assert public.P3C2_LEDGER_DIGEST_ORACLE == "b634ea8c4936c2ff024f3f593498ab426b4fb8c4edcb14f833fb2060c8a9e6cb"
    assert public.P3C2GeneratedTransportCoherence is private.GeneratedTransportCoherence
    assert public.P3C2CofinalBoundaryReconciliation is private.CofinalBoundaryReconciliation
