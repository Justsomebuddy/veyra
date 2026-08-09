"""Closed candidate DTOs for P3-N6 information growth and carrier injection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .prime_power_unbounded_common import freeze_layout
from .padic.completion.types import PadicCompletionPackage
from .padic.family_introduction.types import N1IntroductionPackage

N6_NONCLAIMS = (
    "completed-infinity-without-exact-receipt",
    "information-growth-from-finite-samples",
    "cardinal-infinity",
    "uncountability-or-continuum-cardinality",
    "generic-or-categorical-completion",
    "topological-or-metric-completion",
    "physical-instantiation",
    "absolute-or-foundation-independent-infinity",
)


class N6Status(str, Enum):
    """Closed semantic/operational status vocabulary."""

    ESTABLISHED = "established"
    OPEN = "open"
    REFUTED = "refuted"
    RESOURCE_LIMIT = "resource-limit"


class N6Lane(str, Enum):
    """Exact request/result lane; lanes never share semantic OPEN reasons."""

    E_POWER_INJECTION = "e-power-injection"
    W_INFORMATION_GROWTH = "w-information-growth"


class N6Kind(str, Enum):
    """The only phase-one positive judgment kind."""

    POWER_INJECTION_RELATIVE_TO_EXACT_POMEGA2 = (
        "power-injection-relative-to-exact-pomega2"
    )


class N6EOpenReason(str, Enum):
    """Only the exact E-lane missing premise."""

    MISSING_EXACT_EQUALITY_ADAPTER = "missing-exact-equality-adapter"


class N6WOpenReason(str, Enum):
    """Only the exact W-lane missing premise."""

    MISSING_COMPLETED_INFINITY_ADMISSION = "missing-completed-infinity-admission"


class N6ReportReason(str, Enum):
    """Report-only future boundary; never an N6i result reason."""

    MISSING_FOUNDATION_BRIDGE = "missing-foundation-bridge"


class N6RefutationReason(str, Enum):
    """Closed exact endpoint/setoid mismatch propositions."""

    PRIME_MISMATCH = "prime-mismatch"
    DOCTRINE_MISMATCH = "doctrine-mismatch"
    CARRIER_ID_MISMATCH = "carrier-id-mismatch"
    EQUALITY_ID_MISMATCH = "equality-id-mismatch"
    THEOREM_ENDPOINT_MISMATCH = "theorem-endpoint-mismatch"


class N6FailedBound(str, Enum):
    """Fixed hard/policy accounting dimensions."""

    CAPTURED_BYTES = "captured-bytes"
    STATIC_COST = "static-cost"
    LEDGER_ROWS = "ledger-rows"
    LEDGER_EDGES = "ledger-edges"
    OUTPUT_BYTES = "output-bytes"


class N6FormalFailureKind(str, Enum):
    """Operational failures that never become refutations."""

    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"
    DEPENDENCY_REPLAY_FAILURE = "dependency-replay-failure"


class N6GoalID(str, Enum):
    """Closed exact semantic mismatch goals."""

    PRIME_EQUALITY = "prime-equality"
    DOCTRINE_EQUALITY = "doctrine-equality"
    CARRIER_ID_EQUALITY = "carrier-id-equality"
    EQUALITY_ID_EQUALITY = "equality-id-equality"
    THEOREM_ENDPOINT_EQUALITY = "theorem-endpoint-equality"
    EXACT_EQUALITY_ADAPTER = "exact-equality-adapter"
    COMPLETED_INFINITY_ADMISSION = "completed-infinity-admission"


class N6DiagnosticCode(str, Enum):
    """Closed sanitized operational diagnostic classes."""

    TIMEOUT = "timeout"
    OUTPUT_LIMIT = "output-limit"
    COMPILE_ERROR = "compile-error"
    CONTINUITY_DRIFT = "continuity-drift"
    DEPENDENCY_REPLAY_FAILURE = "dependency-replay-failure"


class N6LedgerRowKind(str, Enum):
    """Closed dependency-ledger row classes."""

    FOUNDATION = "foundation"
    DEFINITION = "definition"
    THEOREM = "theorem"
    TRUSTED_BOUNDARY = "trusted-boundary"


@dataclass(frozen=True, slots=True)
class N6TheoremSourceV1:
    """Exact owned Lean source and direct/transitive import closure."""

    lane: N6Lane
    version: str
    artifact_path_id: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    direct_imports: tuple[tuple[str, str], ...]
    transitive_imports: tuple[tuple[str, str], ...]
    equality_definition_id: str
    power_map_definition_id: str
    toolchain_id: str
    tcb_digest: str
    source_digest: str


@dataclass(frozen=True, slots=True)
class N6PolicyV1:
    """Exact hard-first public policy."""

    version: str
    max_captured_bytes: int
    max_static_cost: int
    max_ledger_rows: int
    max_ledger_edges: int
    timeout_seconds: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True, slots=True)
class N6DependencyRowV1:
    """One typed row in the exact transitive source union."""

    row_id: str
    row_kind: N6LedgerRowKind
    direct_dependencies: tuple[str, ...]
    source_digest: str
    axiom_closure: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class N6DependencyUnionV1:
    """Ordered acyclic dependency closure for one result lane."""

    version: str
    ordered_rows: tuple[N6DependencyRowV1, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    ledger_digest: str


@dataclass(frozen=True, slots=True)
class N6PrechargeV1:
    """Atomic shallow accounting result before deep decoding or hashing."""

    captured_bytes: int
    static_cost: int
    ledger_rows: int
    ledger_edges: int


@dataclass(frozen=True, slots=True)
class N6ERawRequestV1:
    """Inert E request before closure-precharge and deep reconstruction."""

    n1_zero: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    theorem: N6TheoremSourceV1 | None
    policy: N6PolicyV1 | None
    supplied_request_digest: str | None


@dataclass(frozen=True, slots=True)
class N6ERequestV1:
    """Deeply reconstructed E request inside the precharged transaction."""

    n1_zero: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    theorem: N6TheoremSourceV1
    policy: N6PolicyV1
    request_digest: str


@dataclass(frozen=True, slots=True)
class CompletedInfinityReceiptV1:
    """Typed SOME input only; Python validation never turns it into authority."""

    doctrine_digest: str
    index_id: str
    foundation_id: str
    package_digest: str
    source_digest: str
    receipt_digest: str


@dataclass(frozen=True, slots=True)
class N6WRequestV1:
    """W request distinguishes explicit NONE from a typed untrusted SOME receipt."""

    n1_zero: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    completed_infinity: CompletedInfinityReceiptV1 | None
    theorem: N6TheoremSourceV1
    policy: N6PolicyV1
    request_digest: str


N6_THEOREM_SOURCE_LAYOUT = freeze_layout(N6TheoremSourceV1, (
    "lane", "version", "artifact_path_id", "artifact_sha256", "theorem_ids",
    "theorem_axiom_rows", "direct_imports", "transitive_imports",
    "equality_definition_id", "power_map_definition_id", "toolchain_id",
    "tcb_digest", "source_digest",
))
N6_POLICY_LAYOUT = freeze_layout(N6PolicyV1, (
    "version", "max_captured_bytes", "max_static_cost", "max_ledger_rows",
    "max_ledger_edges", "timeout_seconds", "max_output_bytes", "policy_digest",
))
N6_E_RAW_REQUEST_LAYOUT = freeze_layout(N6ERawRequestV1, (
    "n1_zero", "pomega2", "theorem", "policy", "supplied_request_digest",
))
N6_E_REQUEST_LAYOUT = freeze_layout(N6ERequestV1, (
    "n1_zero", "pomega2", "theorem", "policy", "request_digest",
))
N6_CI_RECEIPT_LAYOUT = freeze_layout(CompletedInfinityReceiptV1, (
    "doctrine_digest", "index_id", "foundation_id", "package_digest",
    "source_digest", "receipt_digest",
))
N6_W_REQUEST_LAYOUT = freeze_layout(N6WRequestV1, (
    "n1_zero", "pomega2", "completed_infinity", "theorem", "policy",
    "request_digest",
))
