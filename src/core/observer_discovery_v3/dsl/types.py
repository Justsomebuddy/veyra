"""Immutable records for the closed Phase-III observer evaluator."""

from __future__ import annotations

from dataclasses import dataclass

ClosedScalar = str | int | bool
ClosedValue = ClosedScalar | tuple["ClosedValue", ...]


@dataclass(frozen=True, slots=True)
class ClosedObserverTerm:
    """Canonical AST node from the fixed, non-callable observer language."""

    op: str
    indices: tuple[int, ...] = ()
    children: tuple["ClosedObserverTerm", ...] = ()


@dataclass(frozen=True, slots=True)
class ClosedObserverGrammar:
    """Finite typed grammar with only built-in, versioned semantics."""

    grammar_id: str
    input_arity: int
    bit_columns: tuple[int, ...]
    allowed_ops: tuple[str, ...]
    max_xor_width: int
    max_depth: int
    max_cost: int


@dataclass(frozen=True, slots=True)
class ClosedWorkerConfig:
    """Host and worker limits bound into every request receipt."""

    isolation_profile: str = "logical-subprocess"
    timeout_ms: int = 3000
    cpu_seconds: int = 2
    memory_limit_mb: int = 512
    max_request_bytes: int = 1_000_000
    max_response_bytes: int = 4_000_000
    max_rows: int = 8192
    max_terms: int = 4096
    max_ast_nodes: int = 65536
    max_output_units: int = 1_000_000
    determinism_checks: int = 2


@dataclass(frozen=True, slots=True)
class ClosedEvaluationReceipt:
    """Exact deterministic result from the isolated closed evaluator."""

    status: str
    request_digest: str
    grammar_digest: str
    terms_digest: str
    rows_digest: str
    outputs: tuple[tuple[ClosedValue, ...], ...]
    output_digest: str
    result_digest: str
    obstruction: str
    boundary: str
