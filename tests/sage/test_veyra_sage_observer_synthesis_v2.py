"""Presentation-only Sage facade checks for the finite R14 audit."""
from __future__ import annotations

from dataclasses import replace

import pytest

import veyra_sage.observer_synthesis_v2 as sage_module
from src.core.certify_observer_synthesis_v2 import (
    R14_CERTIFICATE_DETAIL,
    R14_CERTIFICATE_METHOD,
    R14_CERTIFICATE_NAME,
)
from src.core.certify_types import Certificate
from veyra_sage.observer_synthesis_v2 import (
    VeyraObserverSynthesisV2Lab,
    _observer_synthesis_v2_from_core,
    _observer_synthesis_v2_presentation,
)


def _certificate() -> Certificate:
    """Build one exact passing core-certificate stub."""
    return Certificate(
        R14_CERTIFICATE_NAME,
        R14_CERTIFICATE_METHOD,
        True,
        R14_CERTIFICATE_DETAIL,
        3,
    )


def test_presentation_is_finite_and_accepts_no_new_evidence() -> None:
    row = _observer_synthesis_v2_presentation(_certificate())
    assert row["passed"] is True
    assert row["finite_audit"] is True
    assert row["subjects"] == 5
    assert row["cases"] == 10
    assert row["required"] == "8/8"
    assert row["diagnostic"] == "0/2"
    assert row["receipt_rows"] == 10
    assert row["taxonomy"] == "2/4/25/5"
    assert row["layers"] == 36
    assert row["presentation_only"] is True
    assert row["semantic_replay"] is False
    assert row["theorem"] is False
    assert row["formal_proof"] is False
    assert row["r8_evidence"] is False
    assert row["evidence_accepted"] is False
    assert row["promotion_ready"] is False
    assert row["taxonomy_changed"] is False
    assert row["proof_complete"] is False


@pytest.mark.parametrize(
    "certificate",
    [
        object(),
        replace(_certificate(), name="forged"),
        replace(_certificate(), level=2),
        replace(_certificate(), method="forged"),
        replace(_certificate(), passed=False),
        replace(_certificate(), passed=1),
        replace(_certificate(), detail="forged"),
    ],
)
def test_presentation_rejects_wrong_certificate_shape(
    certificate: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        _observer_synthesis_v2_presentation(certificate)  # type: ignore[arg-type]


def test_lab_calls_core_certificate_once_and_returns_fresh_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def once() -> Certificate:
        nonlocal calls
        calls += 1
        return _certificate()

    monkeypatch.setattr(
        sage_module,
        "certify_observer_synthesis_v2_r14",
        once,
    )
    lab = VeyraObserverSynthesisV2Lab()
    first = lab.summary()
    second = lab.certificate_row()
    assert calls == 1
    assert first == second
    assert first is not second


def test_aggregate_facade_reuses_existing_core_certificate_without_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden() -> Certificate:
        raise AssertionError("semantic certificate replay is forbidden")

    monkeypatch.setattr(
        sage_module,
        "certify_observer_synthesis_v2_r14",
        forbidden,
    )
    row = _observer_synthesis_v2_from_core([_certificate()])
    assert row["passed"] is True
    with pytest.raises(RuntimeError):
        _observer_synthesis_v2_from_core(
            [_certificate(), _certificate()],
        )


class _EqualityBomb:
    def __eq__(self, _: object) -> bool:
        raise AssertionError("hostile equality must not run")


@pytest.mark.parametrize("field,value", [
    ("name", _EqualityBomb()),
    ("level", 3.0),
])
def test_sage_exact_certificate_scalars_fail_closed(
    field: str,
    value: object,
) -> None:
    certificate = _certificate()
    object.__setattr__(certificate, field, value)
    with pytest.raises(ValueError):
        _observer_synthesis_v2_presentation(certificate)
    with pytest.raises(ValueError):
        _observer_synthesis_v2_from_core([certificate])


def test_sage_deleted_certificate_slot_fails_closed() -> None:
    certificate = _certificate()
    object.__delattr__(certificate, "name")
    with pytest.raises(TypeError):
        _observer_synthesis_v2_presentation(certificate)
    with pytest.raises(TypeError):
        _observer_synthesis_v2_from_core([certificate])
