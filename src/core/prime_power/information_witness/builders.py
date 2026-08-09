"""Canonical positive builders for the isolated internal P3-N6-W runtime."""

from __future__ import annotations

import logging
from typing import cast

from ...padic.completion.types import PadicCompletionJudgment
from ...padic.family_introduction.types import N1FamilyJudgment
from .types import (
    LateDistinctionWitnessV1,
    N6WCoordinateAgreementV1,
    N6WStatus,
    N6WWitnessRequestV1,
    UniformLateDistinctionBasisV1,
)
from ...prime_power_unbounded_common import digest

logger = logging.getLogger(__name__)


def _rows(name: str, values: tuple[str, ...]) -> tuple[tuple[str, bytes], ...]:
    """Frame one ordered string tuple for positive result commitments."""
    logger.debug("_rows entry name=%s count=%d", name, len(values))
    result = tuple((f"{name}-{index}", value.encode()) for index, value in enumerate(values))
    logger.debug("_rows exit name=%s", name)
    return result


def build_basis(
    request: N6WWitnessRequestV1,
    completion: PadicCompletionJudgment,
    run_digest: str,
) -> UniformLateDistinctionBasisV1:
    """Package only the checked metalanguage constructor, never completed Nat."""
    logger.debug("build_basis entry")
    theorem_ids = (
        "THM_P3N6W_001_exact_shape", "THM_P3N6W_002_prefix",
        "THM_P3N6W_003_later", "THM_P3N6W_004_uniform",
    )
    nonclaims = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    doctrine = request.base_request.pomega2.doctrine
    rows = (
        ("prime", completion.prime_digest.encode()),
        ("package", completion.package_digest.encode()),
        ("doctrine", doctrine.doctrine_digest.encode()),
        ("carrier", doctrine.carrier_id.encode()),
        ("equality", doctrine.equality_id.encode()),
        ("arithmetic-source", request.base_request.theorem.source_digest.encode()),
        ("witness-source", request.theorem.source_digest.encode()),
        ("formal-run", run_digest.encode()),
        ("constructor", request.theorem.constructor_definition_id.encode()),
        *_rows("proof", theorem_ids),
        *_rows("nonclaim", nonclaims),
    )
    basis_digest = digest("veyra.p3n6w.uniform-basis.v1", rows)
    result = UniformLateDistinctionBasisV1(
        N6WStatus.ESTABLISHED, completion.prime_digest, completion.package_digest,
        doctrine.doctrine_digest, doctrine.carrier_id, doctrine.equality_id,
        request.base_request.theorem.source_digest, request.theorem.source_digest,
        run_digest, request.theorem.constructor_definition_id, theorem_ids,
        request.theorem.theorem_axiom_rows, "Lean.Nat-metalanguage",
        False, 0, nonclaims, basis_digest,
    )
    logger.debug("build_basis exit")
    return result


def build_witness(
    request: N6WWitnessRequestV1,
    right: int,
    dependencies: tuple[N1FamilyJudgment, N1FamilyJudgment, PadicCompletionJudgment],
    basis: UniformLateDistinctionBasisV1,
) -> LateDistinctionWitnessV1:
    """Construct and verify every n<=k row plus canonical k+1 separation."""
    logger.debug("build_witness entry k=%d", request.k)
    nonclaims = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    p = cast(int, request.base_request.pomega2.prime.p)
    rows = tuple(
        N6WCoordinateAgreementV1(n, 0 % (p ** (n + 1)), right % (p ** (n + 1)))
        for n in range(request.k + 1)
    )
    later = request.k + 1
    modulus = p ** (later + 1)
    left_later, right_later = 0, right % modulus
    if (
        tuple(row.n for row in rows) != tuple(range(request.k + 1))
        or any(row.left_residue != row.right_residue for row in rows)
        or later != request.k + 1
        or left_later == right_later
    ):
        logger.error("build_witness internal arithmetic invariant drift")
        raise RuntimeError("internal N6-W arithmetic invariant drift")
    zero, late, _ = dependencies
    witness_digest = digest("veyra.p3n6w.late-witness.v1", (
        ("request", request.request_digest.encode()),
        ("prime", zero.prime_digest.encode()),
        ("doctrine", zero.doctrine_digest.encode()),
        ("p", p.to_bytes(4, "big")),
        ("k", request.k.to_bytes(8, "big")),
        ("later", later.to_bytes(8, "big")),
        ("left-family", zero.family_term_digest.encode()),
        ("right-family", late.family_term_digest.encode()),
        *((f"prefix-{row.n}", f"{row.left_residue}\0{row.right_residue}".encode()) for row in rows),
        ("later-residues", f"{left_later}\0{right_later}".encode()),
        ("basis", basis.basis_digest.encode()),
        *_rows("nonclaim", nonclaims),
    ))
    result = LateDistinctionWitnessV1(
        N6WStatus.ESTABLISHED, request.request_digest, zero.prime_digest,
        zero.doctrine_digest, p, request.k, later, 0, right,
        zero.family_term_digest, late.family_term_digest, rows,
        left_later, right_later, basis.basis_digest, 0, nonclaims,
        witness_digest,
    )
    logger.debug("build_witness exit rows=%d", len(rows))
    return result
