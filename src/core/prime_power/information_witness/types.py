"""Closed internal DTOs for the request-bound P3-N6-W witness slice."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from ...prime_power_unbounded_common import freeze_layout
from ...prime_power_unbounded_types import N6FormalFailureKind, N6WRequestV1

N6W_NONCLAIMS = (
    "completed-index-admission",
    "information-unboundedness-internalization",
    "carrier-cardinality-or-uncountability",
    "omegan-or-omegaa-adoption",
    "public-export-certificate-registry-or-promotion",
    "generic-physical-absolute-or-foundation-independent-infinity",
)


class N6WStatus(str, Enum):
    """Closed runtime statuses; no refutation or completed-infinity arm exists."""

    ESTABLISHED = "established"
    RESOURCE_LIMIT = "resource-limit"


class N6WFailedBound(str, Enum):
    """Hard-first request-bound construction limits in fixed priority order."""

    REQUESTED_DEPTH = "requested-depth"
    PREFIX_ROWS = "prefix-rows"
    INTEGER_BITS = "integer-bits"


@dataclass(frozen=True, slots=True)
class N6WTheoremSourceV1:
    """Exact isolated Lean witness source layered over the repaired N6 source."""

    version: str
    artifact_path_id: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    record_definition_id: str
    constructor_definition_id: str
    direct_import: tuple[str, str]
    n6e_interface_root: str
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True, slots=True)
class N6WPolicyV1:
    """Fixed construction bounds plus the exact shared N6 formal policy."""

    version: str
    max_requested_depth: int
    max_prefix_rows: int
    max_integer_bits: int
    base_policy_digest: str
    policy_digest: str


@dataclass(frozen=True, slots=True)
class N6WWitnessRequestV1:
    """One exact finite-depth request over the already-replayed N6 W base."""

    base_request: N6WRequestV1
    k: int
    theorem: N6WTheoremSourceV1
    policy: N6WPolicyV1
    request_digest: str


@dataclass(frozen=True, slots=True)
class N6WCoordinateAgreementV1:
    """One explicitly checked coordinate row from the complete prefix."""

    n: int
    left_residue: int
    right_residue: int


@dataclass(frozen=True, slots=True)
class UniformLateDistinctionBasisV1:
    """Foundation-relative all-input constructor evidence, never ΩN adoption."""

    status: N6WStatus
    prime_digest: str
    pomega2_package_digest: str
    doctrine_digest: str
    carrier_id: str
    equality_id: str
    arithmetic_source_digest: str
    witness_source_digest: str
    formal_run_digest: str
    constructor_definition_id: str
    proof_ids: tuple[str, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    index_domain: str
    completed_index_admitted: bool
    promotions: int
    nonclaims: tuple[str, ...]
    basis_digest: str


@dataclass(frozen=True, slots=True)
class LateDistinctionWitnessV1:
    """Canonical zero versus p^(k+1) witness with every prefix row retained."""

    status: N6WStatus
    request_digest: str
    prime_digest: str
    doctrine_digest: str
    p: int
    k: int
    later: int
    left_integer: int
    right_integer: int
    left_family_digest: str
    right_family_digest: str
    prefix_rows: tuple[N6WCoordinateAgreementV1, ...]
    later_left_residue: int
    later_right_residue: int
    basis_digest: str
    promotions: int
    nonclaims: tuple[str, ...]
    witness_digest: str


@dataclass(frozen=True, slots=True)
class N6WResourceLimitV1:
    """Typed first-bound refusal with no witness or uniform basis payload."""

    status: N6WStatus
    request_digest: str
    failed_bound: N6WFailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


@dataclass(frozen=True, slots=True)
class N6WExecutionFailureV1:
    """Sanitized operational failure; it is never mathematical refutation."""

    kind: N6FormalFailureKind
    request_digest: str
    arithmetic_source_digest: str
    witness_source_digest: str
    policy_digest: str
    output_digest: str
    diagnostic_digest: str
    attempt_digest: str


N6WPositiveV1: TypeAlias = tuple[
    LateDistinctionWitnessV1, UniformLateDistinctionBasisV1,
]
N6WRuntimeResultV1: TypeAlias = (
    N6WPositiveV1 | N6WResourceLimitV1 | N6WExecutionFailureV1
)

N6W_SOURCE_LAYOUT = freeze_layout(N6WTheoremSourceV1, (
    "version", "artifact_path_id", "artifact_sha256", "theorem_ids",
    "theorem_axiom_rows", "record_definition_id", "constructor_definition_id",
    "direct_import", "n6e_interface_root", "toolchain_id", "tcb_digest",
    "source_digest",
))
N6W_POLICY_LAYOUT = freeze_layout(N6WPolicyV1, (
    "version", "max_requested_depth", "max_prefix_rows", "max_integer_bits",
    "base_policy_digest", "policy_digest",
))
N6W_REQUEST_LAYOUT = freeze_layout(N6WWitnessRequestV1, (
    "base_request", "k", "theorem", "policy", "request_digest",
))
N6W_ROW_LAYOUT = freeze_layout(N6WCoordinateAgreementV1, (
    "n", "left_residue", "right_residue",
))
N6W_BASIS_LAYOUT = freeze_layout(UniformLateDistinctionBasisV1, (
    "status", "prime_digest", "pomega2_package_digest", "doctrine_digest",
    "carrier_id", "equality_id", "arithmetic_source_digest",
    "witness_source_digest", "formal_run_digest", "constructor_definition_id",
    "proof_ids", "theorem_axiom_rows", "index_domain",
    "completed_index_admitted", "promotions", "nonclaims", "basis_digest",
))
N6W_WITNESS_LAYOUT = freeze_layout(LateDistinctionWitnessV1, (
    "status", "request_digest", "prime_digest", "doctrine_digest", "p", "k",
    "later", "left_integer", "right_integer", "left_family_digest",
    "right_family_digest", "prefix_rows", "later_left_residue",
    "later_right_residue", "basis_digest", "promotions", "nonclaims",
    "witness_digest",
))
N6W_RESOURCE_LAYOUT = freeze_layout(N6WResourceLimitV1, (
    "status", "request_digest", "failed_bound", "required_value",
    "allowed_value", "nonclaims", "refusal_digest",
))
N6W_FAILURE_LAYOUT = freeze_layout(N6WExecutionFailureV1, (
    "kind", "request_digest", "arithmetic_source_digest",
    "witness_source_digest", "policy_digest", "output_digest",
    "diagnostic_digest", "attempt_digest",
))
