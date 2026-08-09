"""Presentation-only Sage facade checks for R13."""
from __future__ import annotations

from dataclasses import replace

import pytest

import veyra_sage.intrinsic_observer_echo as sage_module
from src.core.certify_intrinsic_observer_echo import (
    R13_CERTIFICATE_DETAIL,
    R13_CERTIFICATE_METHOD,
)
from src.core.certify_types import Certificate
from veyra_sage.intrinsic_observer_echo import (
    VeyraIntrinsicObserverEchoLab,
    _intrinsic_observer_echo_presentation,
)


def _certificate() -> Certificate:
    """Build one exact-shape passing core-certificate stub."""
    return Certificate(
        "intrinsic_observer_echo_r13",
        R13_CERTIFICATE_METHOD,
        True,
        R13_CERTIFICATE_DETAIL,
        3,
    )


def test_r13_presentation_is_strict_and_does_not_accept_new_evidence() -> None:
    row = _intrinsic_observer_echo_presentation(_certificate())
    assert row["passed"] is True
    assert row["theorem"] == "THM-R13-003"
    assert row["formal_theorems"] == 5
    assert row["executable_rows"] == 3
    assert row["contract_promoted"] is True
    assert row["theorem_derived_layers"] == 2
    assert row["presentation_only"] is True
    assert row["evidence_accepted"] is False
    assert row["proof_complete"] is False


@pytest.mark.parametrize(
    "certificate",
    [
        object(),
        replace(_certificate(), name="forged"),
        replace(_certificate(), level=2),
        replace(_certificate(), method=object()),
        replace(_certificate(), method="forged"),
        replace(_certificate(), passed=False),
        replace(_certificate(), passed=1),
        replace(_certificate(), detail="forged"),
        replace(_certificate(), detail=object()),
    ],
)
def test_r13_presentation_rejects_wrong_certificate_shape(
    certificate: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        _intrinsic_observer_echo_presentation(certificate)  # type: ignore[arg-type]


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
        "certify_intrinsic_observer_echo_r13",
        once,
    )
    lab = VeyraIntrinsicObserverEchoLab()
    first = lab.summary()
    second = lab.certificate_row()
    assert calls == 1
    assert first == second
    assert first is not second
