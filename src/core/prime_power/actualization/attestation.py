"""Pinned N0 theorem-source declaration and exact formal attestation checks."""

from __future__ import annotations

import logging
from .common import digest, indexed, reject
from .types import (
    N0FormalAttestation, N0TheoremSource,
)
from .nested_validation import validate_attestation_shape

logger = logging.getLogger(__name__)

TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerObserverActualization.lean"
ARTIFACT_SHA256 = "ba85eeb0911ffefc24da055df70bb3c0624d068fdc82db407233ee63171990e9"
THEOREM_IDS = (
    "THM_P3N0_001_zero_one_discrimination", "THM_P3N0_002_strict_pair_coarse",
    "THM_P3N0_003_strict_pair_next",
)
AXIOM_ROWS = (
    (THEOREM_IDS[0], ("propext",)),
    (THEOREM_IDS[1], ("propext",)),
    (THEOREM_IDS[2], ("propext", "Classical.choice", "Quot.sound")),
)


def n0_theorem_source() -> N0TheoremSource:
    """Return the one exact N0 path/SHA/toolchain/theorem/axiom closure."""
    logger.debug("n0_theorem_source entry")
    value = digest("veyra.p3n0.theorem-source.v2", (
        ("path", ARTIFACT_PATH.encode()), ("sha", ARTIFACT_SHA256.encode()),
        ("toolchain", TOOLCHAIN_ID.encode()), *indexed("theorem", THEOREM_IDS),
        *indexed("axiom-row", (f"{name}:{','.join(axioms)}" for name, axioms in AXIOM_ROWS)),
    ))
    result = N0TheoremSource(
        "p3n0-theorem-source-v2", ARTIFACT_PATH, ARTIFACT_SHA256,
        TOOLCHAIN_ID, THEOREM_IDS, AXIOM_ROWS, value,
    )
    logger.debug("n0_theorem_source exit")
    return result


def validate_theorem_source(value) -> N0TheoremSource:
    """Reject any theorem-source or claimed axiom-row drift."""
    logger.debug("validate_theorem_source entry")
    if type(value) is not N0TheoremSource or value != n0_theorem_source():
        reject("n0-theorem-source-drift")
    logger.debug("validate_theorem_source exit")
    return value


def validate_attestation(source, value) -> N0FormalAttestation:
    """Bind a four-receipt attestation to the exact theorem-source closure."""
    logger.debug("validate_attestation entry")
    validate_theorem_source(source)
    names = (
        "VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
        "VeyraPrimePowerReductionNetwork.lean", "VeyraPrimePowerObserverActualization.lean",
    )
    raw = validate_attestation_shape(value)
    if (raw["theorem_source_digest"] != source.source_digest
            or tuple(receipt.phase_index for receipt in value.receipts) != (0, 1, 2, 3)
            or tuple(receipt.artifact_name for receipt in value.receipts) != names
            or any(receipt.return_code != 0 for receipt in value.receipts)
            or value.receipts[-1].captured_sha256 != source.artifact_sha256):
        reject("n0-formal-attestation-drift")
    for receipt, captured_hash in zip(value.receipts, value.captured_hashes, strict=True):
        if (receipt.captured_sha256 != captured_hash
                or receipt.receipt_digest != digest("veyra.p3n0.phase-receipt.v2", (
                    ("index", str(receipt.phase_index).encode()),
                    ("name", receipt.artifact_name.encode()),
                    ("captured", captured_hash.encode()),
                    ("return", str(receipt.return_code).encode()),
                    ("output", receipt.output_sha256.encode()),
                ))):
            reject("n0-formal-phase-receipt-drift")
    expected = digest("veyra.p3n0.formal-attestation.v2", (
        ("theorem-source", source.source_digest.encode()),
        *indexed("captured", value.captured_hashes),
        *indexed("receipt", (item.receipt_digest for item in value.receipts)),
    ))
    if value.attestation_digest != expected:
        reject("n0-formal-attestation-digest-drift")
    logger.debug("validate_attestation exit")
    return value
