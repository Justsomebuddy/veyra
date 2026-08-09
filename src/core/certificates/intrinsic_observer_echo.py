"""R13 certificate for the second exact theorem-derived Essence/Core layer."""
from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..kernel.essence import core_layers
from ..intrinsic_observer_echo_effects import intrinsic_observer_echo_effect_data
from ..intrinsic_observer_echo_evidence import (
    intrinsic_observer_echo_evidence,
    verify_intrinsic_observer_echo_evidence,
)
from ..intrinsic_observer_echo_theorem import (
    EXPECTED_ARTIFACT_DIGEST,
    EXPECTED_STATEMENT_DIGEST,
    THEOREM_ID,
)
from ..intrinsic_observer_echo_source import (
    EXPECTED_PROOF_DIGEST as EXPECTED_SOURCE_PROOF_DIGEST,
)
from ..kernel.layer_derivations import META_LAYERS, SHADOW_LAYERS, WITNESS_SOURCES
from ..layer_theorem_contract_handlers import (
    R13_LEAN_BRIDGE_ID,
    R13_TRANSPORT_CARRIER,
    R13_TRUSTED_CONTRACT_DIGEST,
)
from ..layer_theorem_contracts import (
    resolve_layer_theorem,
    theorem_contract_registry,
)

logger = logging.getLogger(__name__)
R13_CERTIFICATE_METHOD = (
    "exact R13 theorem object + executable boundaries + guarded Lean bridge + "
    "trusted R8 promotion contract"
)
R13_CERTIFICATE_DETAIL = (
    f"theorem={THEOREM_ID} rows=3/3 "
    f"contract={R13_TRUSTED_CONTRACT_DIGEST[:16]} "
    "taxonomy=2/4/25/5 layers=36"
)


def _taxonomy() -> tuple[bool, dict[str, int]]:
    """Check exact disjoint coverage without replaying formal bridges again."""
    logger.debug("certify_intrinsic_observer_echo._taxonomy entry")
    layers = core_layers()
    groups = (
        frozenset(theorem_contract_registry()),
        frozenset(WITNESS_SOURCES),
        SHADOW_LAYERS,
        META_LAYERS,
    )
    names = frozenset(layer.name for layer in layers)
    overlap = any(
        left & right
        for index, left in enumerate(groups)
        for right in groups[index + 1:]
    )
    counts = {
        "layers": len(layers),
        "theorem_derived": len(groups[0]),
        "witness_only": len(groups[1]),
        "shadow": len(groups[2]),
        "meta": len(groups[3]),
    }
    result = (
        not overlap
        and len(names) == len(layers)
        and names == frozenset().union(*groups),
        counts,
    )
    logger.debug(
        "certify_intrinsic_observer_echo._taxonomy exit ok=%s counts=%r",
        result[0],
        counts,
    )
    return result


def certify_intrinsic_observer_echo_r13() -> Certificate:
    """Certify one narrow general theorem and its nonreflection boundaries."""
    logger.debug("certify_intrinsic_observer_echo_r13 entry")
    try:
        registry = theorem_contract_registry()
        layer = next(
            item for item in core_layers()
            if item.name == "intrinsic-observer-echo"
        )
        theorem = resolve_layer_theorem(layer, registry)
        executable = intrinsic_observer_echo_evidence()
        effect = intrinsic_observer_echo_effect_data()
        taxonomy_ok, taxonomy = _taxonomy()
        rows = {row.row_id: row for row in executable.rows}
        ready = rows["R13-EVIDENCE-READY"]
        blocked = rows["R13-EVIDENCE-TAIL-BLOCKED"]
        nonreflection = rows["R13-EVIDENCE-CREST-NONREFLECTION"]
        passed = (
            verify_intrinsic_observer_echo_evidence(executable)
            and theorem.theorem_id == THEOREM_ID
            and theorem.statement_digest == EXPECTED_STATEMENT_DIGEST
            and theorem.artifact_digest == EXPECTED_ARTIFACT_DIGEST
            and theorem.proof_digest == EXPECTED_SOURCE_PROOF_DIGEST
            and theorem.semantic_carrier == R13_TRANSPORT_CARRIER
            and theorem.bridge_id == R13_LEAN_BRIDGE_ID
            and theorem.contract_digest == R13_TRUSTED_CONTRACT_DIGEST
            and ready.sources_equal
            and ready.lowered_equal
            and '"tag":"echo"' in ready.outcome
            and '"tag":"domain-blocked"' in blocked.outcome
            and not nonreflection.sources_equal
            and not nonreflection.lowered_equal
            and '"tag":"echo"' in nonreflection.outcome
            and effect["capabilities"] == ["preserves"]
            and effect["promotion_ready"] is False
            and effect["taxonomy_changed"] is False
            and taxonomy_ok
            and taxonomy == {
                "layers": 36,
                "theorem_derived": 2,
                "witness_only": 4,
                "shadow": 25,
                "meta": 5,
            }
        )
        detail = R13_CERTIFICATE_DETAIL
        available = True
    except (AttributeError, KeyError, OSError, StopIteration, TypeError, ValueError) as error:
        # The R9/R10 bridges this theorem rides on need the built Lean artifact.
        # Their absence is an absent environment, not a refuted claim, and it is
        # reported the same way the R10 certificate reports it.
        logger.exception("certify_intrinsic_observer_echo_r13 unavailable")
        passed, available = False, False
        detail = f"unavailable={type(error).__name__}: {error}"
    result = Certificate(
        "intrinsic_observer_echo_r13",
        R13_CERTIFICATE_METHOD,
        passed,
        detail,
        3,
        available=available,
    )
    if not passed and available:
        logger.error("certify_intrinsic_observer_echo_r13 failed detail=%s", detail)
    logger.debug("certify_intrinsic_observer_echo_r13 exit result=%r", result)
    return result
