"""Focused positive and hard-bound checks for the internal P3-N6-W runtime."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.core.padic_completion import (
    padic_completion_ledger,
    padic_completion_package,
    padic_completion_policy,
    padic_completion_theorem_source,
    padic_tower_doctrine,
    prime_source,
)
from src.core.padic_family_introduction import (
    integer_source,
    n1_assumption_ledger,
    n1_introduction_package,
    n1_policy,
    n1_theorem_source,
)
from src.core.prime_power_information_witness_formal import capture_sources
from src.core.prime_power_information_witness_request import witness_request
from src.core.prime_power_information_witness_runtime import derive_witnesses
from src.core.prime_power_information_witness_sources import (
    ARTIFACT_SHA256,
    THEOREM_IDS,
    theorem_source,
)
from src.core.prime_power_information_witness_types import (
    LateDistinctionWitnessV1,
    N6WFailedBound,
    N6WResourceLimitV1,
    N6WStatus,
    N6W_NONCLAIMS,
    UniformLateDistinctionBasisV1,
)
from src.core.prime_power_unbounded_common import P3N6ValidationError, sha
from src.core.paths import PROJECT_ROOT

pytestmark = pytest.mark.requires_lean

logger = logging.getLogger(__name__)


def _packages(p: int = 5):
    """Build one exact same-prime N1-zero/PΩ2 pair."""
    logger.debug("_packages entry p=%d", p)
    prime = prime_source(p)
    doctrine = padic_tower_doctrine()
    pomega2 = padic_completion_package(
        prime, doctrine, padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy(),
    )
    zero = n1_introduction_package(
        prime, integer_source(0), doctrine, n1_theorem_source(),
        n1_assumption_ledger(), n1_policy(),
    )
    logger.debug("_packages exit")
    return zero, pomega2


def test_exact_source_capture_and_boundary_identity() -> None:
    """The isolated leaf is exact and layered over the frozen N6-E interface."""
    logger.debug("test_exact_source_capture_and_boundary_identity entry")
    source = theorem_source()
    captured = capture_sources(source)
    assert len(captured) == 4
    assert sha(captured[-1]) == ARTIFACT_SHA256
    assert source.theorem_ids == THEOREM_IDS
    assert source.theorem_axiom_rows == tuple((name, ("propext",)) for name in THEOREM_IDS)
    assert source.direct_import[0] == "proofs/lean/VeyraPrimePowerUnbounded.lean"
    assert source.n6e_interface_root == (
        "d33034fbf6a533f233fc0d6f054796bfa61bda0d8beeee5e2f9288ffad3e20df"
    )
    assert Path(source.artifact_path_id).read_bytes() == captured[-1]
    logger.debug("test_exact_source_capture_and_boundary_identity exit")


def test_real_request_bound_witness_and_uniform_basis() -> None:
    """Fresh dependencies and Lean produce exactly zero versus p^(k+1)."""
    logger.debug("test_real_request_bound_witness_and_uniform_basis entry")
    request = witness_request(*_packages(), 3)
    result = derive_witnesses(request)
    assert type(result) is tuple and len(result) == 2
    witness, basis = result
    assert type(witness) is LateDistinctionWitnessV1
    assert type(basis) is UniformLateDistinctionBasisV1
    assert witness.status is basis.status is N6WStatus.ESTABLISHED
    assert (witness.p, witness.k, witness.later) == (5, 3, 4)
    assert (witness.left_integer, witness.right_integer) == (0, 5**4)
    assert tuple(row.n for row in witness.prefix_rows) == (0, 1, 2, 3)
    assert all(row.left_residue == row.right_residue == 0 for row in witness.prefix_rows)
    assert witness.later_left_residue == 0
    assert witness.later_right_residue == 5**4
    assert witness.later_left_residue != witness.later_right_residue
    assert witness.basis_digest == basis.basis_digest
    assert basis.index_domain == "Lean.Nat-metalanguage"
    assert basis.completed_index_admitted is False
    assert witness.promotions == basis.promotions == 0
    assert witness.nonclaims == basis.nonclaims == N6W_NONCLAIMS
    logger.debug("test_real_request_bound_witness_and_uniform_basis exit")


def test_hard_resource_priority_precedes_dependencies(monkeypatch) -> None:
    """Depth, row and integer-bit refusals occur in fixed order before replay."""
    logger.debug("test_hard_resource_priority_precedes_dependencies entry")
    from src.core import prime_power_information_witness_runtime as runtime

    def bomb(*_args: object) -> None:
        raise AssertionError("deep-replay-ran-before-hard-refusal")

    monkeypatch.setattr(runtime, "snapshot_request", bomb)
    monkeypatch.setattr(runtime, "_dependencies", bomb)
    depth = derive_witnesses(witness_request(*_packages(), 4097))
    rows = derive_witnesses(witness_request(*_packages(), 1024))
    bits = derive_witnesses(witness_request(*_packages(65521), 300))
    assert type(depth) is type(rows) is type(bits) is N6WResourceLimitV1
    assert depth.failed_bound is N6WFailedBound.REQUESTED_DEPTH
    assert rows.failed_bound is N6WFailedBound.PREFIX_ROWS
    assert bits.failed_bound is N6WFailedBound.INTEGER_BITS
    assert all(item.status is N6WStatus.RESOURCE_LIMIT for item in (depth, rows, bits))
    logger.debug("test_hard_resource_priority_precedes_dependencies exit")


def test_malformed_k_and_supplied_result_reject() -> None:
    """Booleans, negative depths and every supplied prior result are malformed."""
    logger.debug("test_malformed_k_and_supplied_result_reject entry")
    packages = _packages()
    for value in (True, -1, 2**63):
        with pytest.raises(P3N6ValidationError):
            witness_request(*packages, value)  # type: ignore[arg-type]
    with pytest.raises(P3N6ValidationError, match="supplied-result-forbidden"):
        witness_request(*packages, 2, supplied_result=object())
    logger.debug("test_malformed_k_and_supplied_result_reject exit")


def test_internal_only_surface_has_no_root_export_or_completed_claim() -> None:
    """The runtime adds no package-root authority, CI, cardinal or promotion arm."""
    logger.debug("test_internal_only_surface_has_no_root_export_or_completed_claim entry")
    root = (PROJECT_ROOT / "src/core/__init__.py").read_text()
    assert "prime_power_information_witness" not in root
    assert "InformationUnbounded" not in root
    assert "InfiniteCarrier" not in root
    assert tuple(N6WStatus) == (N6WStatus.ESTABLISHED, N6WStatus.RESOURCE_LIMIT)
    assert "completed-index-admission" in N6W_NONCLAIMS
    assert "carrier-cardinality-or-uncountability" in N6W_NONCLAIMS
    logger.debug("test_internal_only_surface_has_no_root_export_or_completed_claim exit")
