"""Exact source, toolchain, ledger, and certificate tests for P3-N1."""

from hashlib import sha256
from pathlib import Path

from src.core.certify_padic_family_introduction import certify_padic_family_introduction_p3n1
from src.core.padic_family_introduction import (
    ARTIFACT_PATH, ARTIFACT_SHA256, AXIOM_CLOSURE, THEOREM_IDS,
    TOOLCHAIN_ID, n1_assumption_ledger, n1_theorem_source,
)
from src.core.padic_family_introduction_formal import capture_sources
from padic_family_introduction_fixture import exact_n1_package
import pytest

pytestmark = pytest.mark.requires_lean


def test_exact_artifact_and_dependency_are_captured_with_generated_instance():
    package = exact_n1_package(z=-42)
    base, theorem, instance = capture_sources(package)
    assert sha256(theorem).hexdigest() == ARTIFACT_SHA256
    assert theorem == Path(ARTIFACT_PATH).read_bytes()
    assert sha256(base).hexdigest() == package.theorem_source.pomega2_artifact_sha256
    assert b"-42" in instance and b"p3n1ConcreteIntroduction" in instance
    assert b"pomega2ConcreteCompletion" not in instance


def test_theorem_toolchain_axiom_and_ledger_contract_is_exact():
    source = n1_theorem_source()
    ledger = n1_assumption_ledger()
    assert source.theorem_ids == THEOREM_IDS and len(THEOREM_IDS) == 3
    assert source.toolchain_id == TOOLCHAIN_ID
    assert ledger.theorem_axiom_closure == AXIOM_CLOSURE == ("propext",)
    assert "universal-realization" not in ledger.ordered_rows
    assert "THM_POMEGA2_017_ppcp_introduction" not in ledger.ordered_rows
    assert "local-realization" not in ledger.ordered_rows


def test_thm003_reaches_family_type_function_and_equality_dependencies():
    ledger = n1_assumption_ledger()
    dependencies = {}
    for source, dependency in ledger.direct_edges:
        dependencies.setdefault(source, set()).add(dependency)

    def closure(root):
        result = set()
        pending = [root]
        while pending:
            current = pending.pop()
            for dependency in dependencies.get(current, ()):
                if dependency not in result:
                    result.add(dependency)
                    pending.append(dependency)
        return result

    required = {
        "veyraIntegerFamily", "VeyraCompatibleFamily", "VeyraPrimeWitness",
        "dependent-functions", "propositions-equality",
    }
    assert required <= closure(THEOREM_IDS[2])
    assert ("veyraIntegerFamily", "VeyraCompatibleFamily") in ledger.direct_edges
    signature_nodes = ("veyraIntegerResidue", "veyraIntegerFamily", *THEOREM_IDS)
    assert all((node, "VeyraPrimeWitness") in ledger.direct_edges for node in signature_nodes)
    assert len(ledger.ordered_rows) == 20
    assert len(ledger.direct_edges) == 32
    assert ledger.ledger_digest == (
        "3a9970d741a0be939779f0c4fe438697b1c68c84d77404aaa38a2e7ecb250d1f"
    )


def test_direct_level_one_certificate_passes_with_zero_promotions():
    cert = certify_padic_family_introduction_p3n1()
    assert cert.passed and cert.level == 1
    assert "promotions=0" in cert.detail
    assert "universal_completion=0" in cert.detail
    assert "local_realization=0" in cert.detail


def test_live_output_cap_fails_typed_without_publishing_proof():
    from src.core.padic_family_introduction_formal import compile_sources
    from src.core.padic_family_introduction_types import N1ExecutionFailureKind

    package = exact_n1_package()
    outcome = compile_sources(capture_sources(package), 30, 1)
    assert outcome.kind is N1ExecutionFailureKind.OUTPUT_LIMIT
    assert len(outcome.output) <= 1
    assert outcome.theorem_axiom_rows == ()
