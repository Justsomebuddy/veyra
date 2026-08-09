"""Captured Lean, symbolic Nat-op, direct certificate, and source-boundary tests."""

from hashlib import sha256
from pathlib import Path
from src.core.certify_transport_coherence import certify_transport_coherence_p3c2
from src.core.transport_coherence import (
    ARTIFACT_PATH,
    ARTIFACT_SHA256,
    THEOREM_IDS,
    check_transport_theorems,
    transport_theorem_source,
)
import pytest

pytestmark = pytest.mark.requires_lean


def test_exact_three_theorem_artifact_is_pinned():
    payload = Path(ARTIFACT_PATH).read_bytes()
    assert sha256(payload).hexdigest() == ARTIFACT_SHA256
    assert THEOREM_IDS == (
        "THM_P3C2_001_ranked_local_to_generated_transport",
        "THM_P3C2_002_natop_reduction_identity",
        "THM_P3C2_003_natop_reduction_composition",
    )


def test_private_lean_has_global_and_separate_symbolic_natop_proofs():
    outcome = check_transport_theorems(transport_theorem_source(), 120, 1024 * 1024)
    assert outcome.kind is None and outcome.phase_count == 3


def test_live_output_cap_is_typed_formal_failure():
    outcome = check_transport_theorems(transport_theorem_source(), 30, 1)
    assert outcome.kind is not None and len(outcome.output_digest) == 64


def test_source_has_actual_three_lower_rank_ih_and_no_p3t_or_completion_import():
    text = Path(ARTIFACT_PATH).read_text()
    assert all(x in text for x in ("rankY", "rankZ", "rankW", "eqY", "eqZ", "eqW"))
    assert "ObserverTranslation" not in text and "PadicCompletion" not in text
    assert "namespace NatOp" in text


def test_direct_level_one_certificate_has_zero_promotions_and_open_c23():
    cert = certify_transport_coherence_p3c2()
    assert cert.passed and cert.level == 1
    assert "attacks=17" in cert.detail
    assert "higher_cell_structure=not_implemented" in cert.detail and "promotions=0" in cert.detail


def test_assumption_ledger_is_exact_acyclic_and_binds_axiom_closure():
    from src.core.transport_coherence import transport_assumption_ledger

    ledger = transport_assumption_ledger()
    positions = {name: index for index, name in enumerate(ledger.ordered_rows)}
    assert len(ledger.ordered_rows) == len(positions) == 23
    assert len(ledger.direct_edges) == len(set(ledger.direct_edges)) == 41
    assert all(positions[dependency] < positions[source] for source, dependency in ledger.direct_edges)
    assert ledger.theorem_axiom_closure == ("propext",)
    assert ledger.ledger_digest == "b634ea8c4936c2ff024f3f593498ab426b4fb8c4edcb14f833fb2060c8a9e6cb"
