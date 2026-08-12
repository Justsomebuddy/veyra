"""Regression gates for honest certificate failure reporting."""

from __future__ import annotations

import logging
import sys

import pytest

from scripts import _project_bootstrap

sys.modules.setdefault("_project_bootstrap", _project_bootstrap)
import scripts.certify_veyra as certificate_cli
import src.core.certify as certificate_api

logger = logging.getLogger(__name__)


def test_certificate_suite_propagates_unexpected_execution_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A semantic/runtime regression must not be relabelled unavailable."""
    logger.debug("test certificate suite unexpected error propagation entry")

    def raise_regression() -> None:
        logger.error("synthetic certificate regression raised")
        raise AssertionError("semantic-regression")

    monkeypatch.setattr(certificate_api, "certify_echo", raise_regression)
    with pytest.raises(AssertionError, match="semantic-regression"):
        certificate_api.certificate_suite()
    logger.debug("test certificate suite unexpected error propagation exit")


def test_certificate_cli_returns_failure_for_unexpected_execution_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The process boundary may report an error, but can never return success."""
    logger.debug("test certificate CLI unexpected error reporting entry")

    def raise_regression() -> None:
        logger.error("synthetic certificate CLI regression raised")
        raise AssertionError("semantic-regression")

    monkeypatch.setattr(certificate_cli, "certificate_suite", raise_regression)
    assert certificate_cli.main() == 1
    captured = capsys.readouterr()
    assert "certificates=0 passed=0 errors=1" in captured.err
    assert "semantic-regression" in captured.err
    logger.debug("test certificate CLI unexpected error reporting exit")
