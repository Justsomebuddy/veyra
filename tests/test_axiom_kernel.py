from importlib import import_module
import logging

import pytest

from src.core.axiom_kernel import axiom_kernel_checklist, axiom_kernel_report, axiom_witness_rows, layer_axiom_dependencies, unified_axiom_kernel
from src.core.layer_theorem_contract_types import TheoremContractCapabilityBlocked
from src.platform_capabilities import Capability

derivations_module = import_module("src.core.layer_derivations")
logger = logging.getLogger(__name__)


def test_unified_axiom_kernel_has_executable_witnesses():
    axioms = unified_axiom_kernel()
    witnesses = axiom_witness_rows(axioms)
    assert len(axioms) == 8
    assert [row.axiom_id for row in witnesses] == [row.axiom_id for row in axioms]
    assert all(row.executable for row in witnesses)
    assert witnesses[-1].status == "blocked"
    assert "echo mismatch" in witnesses[-1].obstruction


def test_every_core_layer_is_classified_and_only_receipts_name_axioms():
    logger.debug("test axiom layer classification entry")
    rows = layer_axiom_dependencies()
    assert len(rows) == 36
    assert {row.derivation for row in rows} == {"theorem-derived", "receipt-derived-witness", "shadow", "meta"}
    assert all(row.axioms for row in rows if row.derivation == "receipt-derived-witness")
    assert all(not row.axioms for row in rows if row.derivation != "receipt-derived-witness")
    assert all(row.status == "ready" for row in rows if row.derivation == "theorem-derived")
    assert any(row.layer == "topology-echo" and row.derivation == "shadow" for row in rows)
    logger.debug("test axiom layer classification exit")


def test_axiom_kernel_report_is_ready_and_marks_receipt_boundaries():
    logger.debug("test ready axiom-kernel report entry")
    report = axiom_kernel_report()
    assert report.ready
    assert report.summary()["axioms"] == 8
    assert report.summary()["layers"] == 36
    assert report.summary()["theorem_derived"] == 2
    assert report.summary()["theorem_blocked"] == 0
    assert report.summary()["receipt_derived_witness"] == 4
    assert report.summary()["shadow"] == 25
    assert report.summary()["meta"] == 5
    assert axiom_kernel_checklist()[-1] == "theorem-derived and meta layers claim no primitive witness axioms"
    logger.debug("test ready axiom-kernel report exit")


def test_axiom_kernel_is_not_ready_when_theorem_rows_are_capability_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F1 readiness preserves theorem-row status instead of dropping it."""
    logger.debug("test blocked axiom-kernel readiness entry")

    def reject_registry_build():
        logger.debug("test blocked axiom-kernel theorem registry attempt")
        raise TheoremContractCapabilityBlocked(
            Capability.THEOREM_PROOF_TOOLCHAIN.value,
            "requires-test-toolchain",
        )

    monkeypatch.setattr(
        derivations_module,
        "theorem_contract_registry",
        reject_registry_build,
    )
    report = axiom_kernel_report()
    theorem_rows = tuple(
        row for row in report.layers if row.derivation == "theorem-derived"
    )
    assert len(theorem_rows) == 2
    assert all(row.status == "blocked" for row in theorem_rows)
    assert report.summary()["theorem_blocked"] == 2
    assert report.ready is False
    logger.debug("test blocked axiom-kernel readiness exit")
