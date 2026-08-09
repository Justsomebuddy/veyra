"""Fresh structural replay validation for internal P3-N6-W runtime results."""

from __future__ import annotations

import logging
from typing import cast

from .types import (
    LateDistinctionWitnessV1,
    N6WExecutionFailureV1,
    N6WFailedBound,
    N6WResourceLimitV1,
    N6WRuntimeResultV1,
    N6WStatus,
    N6WWitnessRequestV1,
    UniformLateDistinctionBasisV1,
    N6W_BASIS_LAYOUT,
    N6W_FAILURE_LAYOUT,
    N6W_RESOURCE_LAYOUT,
    N6W_ROW_LAYOUT,
    N6W_WITNESS_LAYOUT,
)
from ...prime_power_unbounded_common import (
    exact_digest,
    exact_nonnegative_int,
    exact_shape,
    exact_text,
    exact_text_tuple,
    reject,
)
from ...prime_power_unbounded_types import N6FormalFailureKind

logger = logging.getLogger(__name__)


def _basis_transcript(
    value: UniformLateDistinctionBasisV1,
) -> tuple[object, ...]:
    """Flatten every basis field into callback-free primitive values."""
    logger.debug("_basis_transcript entry")
    theorem_ids = (
        "THM_P3N6W_001_exact_shape", "THM_P3N6W_002_prefix",
        "THM_P3N6W_003_later", "THM_P3N6W_004_uniform",
    )
    axiom_rows = tuple((name, ("propext",)) for name in theorem_ids)
    nonclaim_rows = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    raw = exact_shape(value, N6W_BASIS_LAYOUT, "n6w-result-basis")
    if raw["status"] is not N6WStatus.ESTABLISHED:
        reject("n6w-basis-status-invalid")
    for name in (
        "prime_digest", "pomega2_package_digest", "doctrine_digest",
        "arithmetic_source_digest", "witness_source_digest", "formal_run_digest",
        "basis_digest",
    ):
        exact_digest(raw[name], f"n6w-basis-{name}")
    for name in ("carrier_id", "equality_id", "constructor_definition_id", "index_domain"):
        exact_text(raw[name], f"n6w-basis-{name}")
    proof_ids = exact_text_tuple(
        raw["proof_ids"], "n6w-basis-proofs", maximum_items=8,
    )
    axiom_values = raw["theorem_axiom_rows"]
    if type(axiom_values) is not tuple or len(axiom_values) > 8:
        reject("n6w-basis-axiom-rows-invalid")
    checked_axioms: list[tuple[str, tuple[str, ...]]] = []
    for index, row in enumerate(cast(tuple[object, ...], axiom_values)):
        if type(row) is not tuple or len(row) != 2:
            reject(f"n6w-basis-axiom-row-{index}-invalid")
        tuple_row = cast(tuple[object, object], row)
        name = exact_text(tuple_row[0], f"n6w-basis-axiom-name-{index}")
        axioms = exact_text_tuple(
            tuple_row[1], f"n6w-basis-axiom-closure-{index}", maximum_items=4,
        )
        checked_axioms.append((name, axioms))
    nonclaims = exact_text_tuple(
        raw["nonclaims"], "n6w-basis-nonclaims", maximum_items=16,
    )
    if (
        proof_ids != theorem_ids
        or tuple(checked_axioms) != axiom_rows
        or type(raw["completed_index_admitted"]) is not bool
        or raw["completed_index_admitted"] is not False
        or type(raw["promotions"]) is not int
        or raw["promotions"] != 0
        or nonclaims != nonclaim_rows
    ):
        reject("n6w-basis-boundary-invalid")
    primitive = dict(raw)
    primitive["proof_ids"] = proof_ids
    primitive["theorem_axiom_rows"] = tuple(checked_axioms)
    result = tuple(primitive[name] for name, _ in N6W_BASIS_LAYOUT.fields[:-4]) + (
        raw["completed_index_admitted"], raw["promotions"], nonclaims,
        raw["basis_digest"], proof_ids,
    )
    logger.debug("_basis_transcript exit")
    return result


def _witness_transcript(value: LateDistinctionWitnessV1) -> tuple[object, ...]:
    """Validate exact canonical pair, full row range, and immediate separation."""
    logger.debug("_witness_transcript entry")
    nonclaims = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    raw = exact_shape(value, N6W_WITNESS_LAYOUT, "n6w-result-witness")
    if raw["status"] is not N6WStatus.ESTABLISHED:
        reject("n6w-witness-status-invalid")
    for name in (
        "request_digest", "prime_digest", "doctrine_digest", "left_family_digest",
        "right_family_digest", "basis_digest", "witness_digest",
    ):
        exact_digest(raw[name], f"n6w-witness-{name}")
    integers = tuple(
        exact_nonnegative_int(raw[name], f"n6w-witness-{name}", maximum=2**16384)
        for name in (
            "p", "k", "later", "left_integer", "right_integer",
            "later_left_residue", "later_right_residue", "promotions",
        )
    )
    p, k, later, left, right, later_left, later_right, promotions = integers
    if k > 4096 or right.bit_length() > 4096:
        reject("n6w-witness-resource-shape-invalid")
    row_values = raw["prefix_rows"]
    if type(row_values) is not tuple or len(row_values) != k + 1:
        reject("n6w-witness-prefix-completeness-invalid")
    rows: list[tuple[int, int, int]] = []
    for index, row in enumerate(cast(tuple[object, ...], row_values)):
        fields = exact_shape(row, N6W_ROW_LAYOUT, f"n6w-result-row-{index}")
        current = tuple(
            exact_nonnegative_int(
                fields[name], f"n6w-row-{index}-{name}", maximum=2**4096,
            )
            for name in ("n", "left_residue", "right_residue")
        )
        rows.append(cast(tuple[int, int, int], current))
    expected_rows = tuple(
        (n, left % (p ** (n + 1)), right % (p ** (n + 1)))
        for n in range(k + 1)
    )
    if (
        tuple(rows) != expected_rows
        or any(a != b for _, a, b in rows)
        or later != k + 1
        or left != 0
        or right != p ** (k + 1)
        or later_left != left % (p ** (later + 1))
        or later_right != right % (p ** (later + 1))
        or later_left == later_right
        or promotions != 0
        or exact_text_tuple(
            raw["nonclaims"], "n6w-witness-nonclaims", maximum_items=16,
        ) != nonclaims
    ):
        reject("n6w-witness-canonical-law-invalid")
    result = tuple(raw[name] for name, _ in N6W_WITNESS_LAYOUT.fields if name != "prefix_rows") + tuple(rows)
    logger.debug("_witness_transcript exit rows=%d", len(rows))
    return result


def _nonpositive_transcript(
    value: N6WResourceLimitV1 | N6WExecutionFailureV1,
) -> tuple[object, ...]:
    """Flatten a typed refusal or operational failure without cross-casting."""
    logger.debug("_nonpositive_transcript entry type=%s", type(value).__name__)
    nonclaims = (
        "completed-index-admission", "information-unboundedness-internalization",
        "carrier-cardinality-or-uncountability", "omegan-or-omegaa-adoption",
        "public-export-certificate-registry-or-promotion",
        "generic-physical-absolute-or-foundation-independent-infinity",
    )
    layout = N6W_RESOURCE_LAYOUT if type(value) is N6WResourceLimitV1 else N6W_FAILURE_LAYOUT
    raw = exact_shape(value, layout, "n6w-result-nonpositive")
    if type(value) is N6WResourceLimitV1:
        if (
            raw["status"] is not N6WStatus.RESOURCE_LIMIT
            or type(raw["failed_bound"]) is not N6WFailedBound
            or exact_text_tuple(
                raw["nonclaims"], "n6w-resource-nonclaims", maximum_items=16,
            ) != nonclaims
        ):
            reject("n6w-resource-boundary-invalid")
        for name in ("required_value", "allowed_value"):
            exact_nonnegative_int(raw[name], f"n6w-resource-{name}", maximum=2**63 - 1)
        exact_digest(raw["request_digest"], "n6w-resource-request")
        exact_digest(raw["refusal_digest"], "n6w-resource-digest")
    else:
        if type(raw["kind"]) is not N6FormalFailureKind:
            reject("n6w-failure-kind-invalid")
        for name in (
            "request_digest", "arithmetic_source_digest", "witness_source_digest",
            "policy_digest", "output_digest", "diagnostic_digest", "attempt_digest",
        ):
            exact_digest(raw[name], f"n6w-failure-{name}")
    result = tuple(raw[name] for name, _ in layout.fields)
    logger.debug("_nonpositive_transcript exit")
    return result


def _transcript(value: N6WRuntimeResultV1) -> tuple[object, ...]:
    logger.debug("_transcript entry type=%s", type(value).__name__)
    result: tuple[object, ...]
    if type(value) is tuple and len(value) == 2:
        witness, basis = value
        if type(witness) is not LateDistinctionWitnessV1 or type(basis) is not UniformLateDistinctionBasisV1:
            reject("n6w-positive-exact-pair-required")
        witness_transcript = _witness_transcript(witness)
        basis_transcript = _basis_transcript(basis)
        witness_binding = exact_digest(
            exact_shape(witness, N6W_WITNESS_LAYOUT, "n6w-binding-witness")["basis_digest"],
            "n6w-binding-witness-digest",
        )
        basis_binding = exact_digest(
            exact_shape(basis, N6W_BASIS_LAYOUT, "n6w-binding-basis")["basis_digest"],
            "n6w-binding-basis-digest",
        )
        if witness_binding != basis_binding:
            reject("n6w-positive-basis-binding-invalid")
        result = ("positive", witness_transcript, basis_transcript)
    elif type(value) in (N6WResourceLimitV1, N6WExecutionFailureV1):
        result = ("nonpositive",) + _nonpositive_transcript(
            cast(N6WResourceLimitV1 | N6WExecutionFailureV1, value)
        )
    else:
        reject("n6w-result-supported-arm-required")
    logger.debug("_transcript exit")
    return result


def validate_result(
    value: N6WRuntimeResultV1,
    expected_request: N6WWitnessRequestV1,
) -> N6WRuntimeResultV1:
    """Bind every result field to one fresh request and full fresh runtime replay."""
    logger.debug("validate_result entry")
    transcript = _transcript(value)
    from .runtime import derive_witnesses

    logger.debug("validate_result external-call=derive_witnesses state=begin")
    expected = derive_witnesses(expected_request)
    logger.debug("validate_result external-call=derive_witnesses state=end")
    if transcript != _transcript(expected):
        reject("n6w-result-replay-mismatch")
    logger.debug("validate_result exit")
    return value
