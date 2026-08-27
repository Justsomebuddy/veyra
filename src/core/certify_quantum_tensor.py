"""Certificate for exact finite tensor/Born/unitarity semantics."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .quantum_tensor_semantics import (
    FINITE_BOUNDARY,
    apply_unitary,
    born_distribution,
    born_total,
    is_normalized,
    tensor_gates,
    tensor_modes,
    unitarity_witness,
)
from .quantum_veyra import bell_state, q_basis_state, q_gate_h, q_gate_i

logger = logging.getLogger(__name__)


def certify_quantum_tensor_q11() -> Certificate:
    """Certify exact finite products, Born normalization, and unitary action."""
    logger.debug("certify_quantum_tensor_q11 entry")
    product = tensor_modes((q_basis_state("0"), q_basis_state("1")))
    gate = tensor_gates((q_gate_h(), q_gate_i()))
    witness = unitarity_witness(gate)
    output = apply_unitary(gate, product)
    bell = bell_state()
    passed = (
        dict(born_distribution(product))["0⊗1"] == born_total(product)
        and is_normalized(product)
        and is_normalized(output)
        and is_normalized(bell)
        and born_total(output) == born_total(product)
        and witness.left_identity
        and witness.right_identity
        and witness.status == "witnessed"
        and "no quantum advantage" in FINITE_BOUNDARY
    )
    detail = (
        "exact-carrier=Q(sqrt(2))[i] tensor=general-finite Born-total=1 "
        "unitarity=UdagU+UUdag boundary=no-apparatus-or-advantage"
    )
    result = Certificate(
        "quantum_tensor_q11",
        "exact finite tensor-product, Born-rule weight, and full-matrix unitarity semantics",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_quantum_tensor_q11 failed detail=%s", detail)
    logger.debug("certify_quantum_tensor_q11 exit result=%r", result)
    return result
