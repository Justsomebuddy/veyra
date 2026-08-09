"""Exact integer, theorem, ledger, policy, and package sources for P3-N1."""

from __future__ import annotations

import logging

from ..completion.formal import (
    ARTIFACT_PATH as P2_PATH, ARTIFACT_SHA256 as P2_SHA, ELAN_SHA256,
    LEAN_BINARY_SHA256, LEAN_VERSION,
)
from .common import digest, exact_digest, exact_shape, reject
from .types import (
    IntegerSource, N1TheoremSource,
)

logger = logging.getLogger(__name__)
INTEGER_VERSION = "p3n1-integer-v1"
INTEGER_REPRESENTATION_ID = "exact-signed-python-int-to-Lean-Int-literal-v1"
MAX_INTEGER_BITS = 4096
FORMAL_VERSION = "p3n1-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraPadicFamilyIntroduction.lean"
ARTIFACT_SHA256 = "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48"
THEOREM_IDS = (
    "THM_P3N1_001_integer_residue_total",
    "THM_P3N1_002_integer_residue_reduction",
    "THM_P3N1_003_integer_family_introduction",
)
FAMILY_DEFINITION_ID = "veyraIntegerFamily"
COORDINATE_DEFINITION_ID = "veyraIntegerResidue"
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
TCB_DIGEST = digest("veyra.p3n1.tcb.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
    ("process", b"shared-deadline-live-output-cap-three-source-process-groups"),
))
LEDGER_VERSION = "p3n1-ledger-v1"
POLICY_VERSION = "p3n1-policy-v1"
PACKAGE_VERSION = "p3n1-package-v1"
HARD_SOURCE_BYTES = 3 * 1024 * 1024
HARD_STATIC_COST = 8 * 1024 * 1024
LEDGER_ROWS = (
    "natural-numbers", "integers", "dependent-functions", "propositions-equality",
    "propext", "lean-kernel", "lean-pinned-toolchain", "private-bounded-compiler",
    "VeyraPrimeWitness", "veyraModulus", "VeyraZMod", "veyraReduce",
    "veyraModulusDvd", "veyraCanonicalStageRingLaws", "VeyraCompatibleFamily",
    COORDINATE_DEFINITION_ID, THEOREM_IDS[0], THEOREM_IDS[1],
    FAMILY_DEFINITION_ID, THEOREM_IDS[2],
)
LEDGER_EDGES = (
    ("VeyraPrimeWitness", "natural-numbers"), ("veyraModulus", "natural-numbers"),
    ("VeyraZMod", "veyraModulus"), ("veyraReduce", "VeyraZMod"),
    ("veyraModulusDvd", "veyraModulus"),
    ("veyraCanonicalStageRingLaws", "veyraReduce"),
    ("veyraCanonicalStageRingLaws", "propext"),
    ("VeyraCompatibleFamily", "dependent-functions"),
    ("VeyraCompatibleFamily", "propositions-equality"),
    ("VeyraCompatibleFamily", "VeyraPrimeWitness"),
    ("VeyraCompatibleFamily", "veyraReduce"),
    (COORDINATE_DEFINITION_ID, "integers"),
    (COORDINATE_DEFINITION_ID, "VeyraPrimeWitness"),
    (COORDINATE_DEFINITION_ID, "VeyraZMod"),
    (FAMILY_DEFINITION_ID, "VeyraPrimeWitness"),
    (FAMILY_DEFINITION_ID, "VeyraCompatibleFamily"),
    (FAMILY_DEFINITION_ID, COORDINATE_DEFINITION_ID),
    (FAMILY_DEFINITION_ID, THEOREM_IDS[1]),
    (THEOREM_IDS[0], "VeyraPrimeWitness"),
    (THEOREM_IDS[0], COORDINATE_DEFINITION_ID),
    (THEOREM_IDS[1], "VeyraPrimeWitness"),
    (THEOREM_IDS[1], COORDINATE_DEFINITION_ID),
    (THEOREM_IDS[1], "veyraCanonicalStageRingLaws"),
    (THEOREM_IDS[1], "veyraModulusDvd"),
    (THEOREM_IDS[2], "VeyraPrimeWitness"),
    (THEOREM_IDS[2], "VeyraCompatibleFamily"),
    (THEOREM_IDS[2], FAMILY_DEFINITION_ID),
    ("lean-pinned-toolchain", "lean-kernel"),
    ("private-bounded-compiler", "lean-pinned-toolchain"),
    (THEOREM_IDS[0], "private-bounded-compiler"),
    (THEOREM_IDS[1], "private-bounded-compiler"),
    (THEOREM_IDS[2], "private-bounded-compiler"),
)
AXIOM_CLOSURE = ("propext",)
LEDGER_DIGEST_ORACLE = "3a9970d741a0be939779f0c4fe438697b1c68c84d77404aaa38a2e7ecb250d1f"


def _int_bytes(z: int) -> bytes:
    """Encode an exact bounded signed integer without decimal ambiguity."""
    logger.debug("_int_bytes entry bits=%d", z.bit_length())
    magnitude = abs(z)
    body = magnitude.to_bytes(max(1, (magnitude.bit_length() + 7) // 8), "big")
    result = (b"-" if z < 0 else b"+") + body
    logger.debug("_int_bytes exit bytes=%d", len(result))
    return result


def integer_source(z: int) -> IntegerSource:
    """Construct a bounded exact integer source; Booleans are not integers here."""
    logger.debug("integer_source entry type=%s", type(z).__name__)
    if type(z) is not int or z.bit_length() > MAX_INTEGER_BITS:
        reject("integer-source-type-or-bit-limit-invalid")
    value = digest("veyra.p3n1.integer-source.v1", (
        ("version", INTEGER_VERSION.encode()), ("integer", _int_bytes(z)),
        ("representation", INTEGER_REPRESENTATION_ID.encode()),
    ))
    result = IntegerSource(INTEGER_VERSION, z, INTEGER_REPRESENTATION_ID, value)
    logger.debug("integer_source exit bits=%d", z.bit_length())
    return result


def snapshot_integer(value: IntegerSource) -> IntegerSource:
    """Reject integer mutation, subclassing, Boolean casts, and digest reuse."""
    logger.debug("snapshot_integer entry")
    exact_shape(value, IntegerSource, "integer-source")
    try:
        if type(value.z) is not int or type(value.version) is not str or type(value.representation_id) is not str:
            reject("integer-source-field-type-invalid")
        exact_digest(value.source_digest, "integer-source-digest")
        expected = integer_source(value.z)
    except AttributeError:
        reject("integer-source-missing-fields")
    if value != expected:
        reject("integer-source-drift")
    logger.debug("snapshot_integer exit")
    return expected


def n1_theorem_source() -> N1TheoremSource:
    """Construct the pinned private N1 theorem-source identity."""
    logger.debug("n1_theorem_source entry")
    value = digest("veyra.p3n1.theorem-source.v1", (
        ("version", FORMAL_VERSION.encode()), ("artifact", ARTIFACT_PATH.encode()),
        ("artifact-sha", ARTIFACT_SHA256.encode()), ("pomega2-artifact", P2_PATH.encode()),
        ("pomega2-artifact-sha", P2_SHA.encode()),
        *((f"theorem-{i}", name.encode()) for i, name in enumerate(THEOREM_IDS)),
        ("family", FAMILY_DEFINITION_ID.encode()),
        ("coordinate", COORDINATE_DEFINITION_ID.encode()),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode()),
    ))
    result = N1TheoremSource(
        FORMAL_VERSION, ARTIFACT_PATH, ARTIFACT_SHA256, P2_PATH, P2_SHA,
        THEOREM_IDS, FAMILY_DEFINITION_ID, COORDINATE_DEFINITION_ID,
        TOOLCHAIN_ID, TCB_DIGEST, value,
    )
    logger.debug("n1_theorem_source exit")
    return result


def snapshot_theorem(value: N1TheoremSource) -> N1TheoremSource:
    """Reject theorem/dependency/source/toolchain drift before file access."""
    logger.debug("snapshot_theorem entry")
    exact_shape(value, N1TheoremSource, "n1-theorem-source")
    try:
        if type(value.theorem_ids) is not tuple or any(type(x) is not str for x in value.theorem_ids):
            reject("n1-theorem-ids-invalid")
        for name in value.__dict__:
            if name != "theorem_ids" and type(getattr(value, name)) is not str:
                reject("n1-theorem-field-type-invalid")
        for name in ("artifact_sha256", "pomega2_artifact_sha256", "tcb_digest", "source_digest"):
            exact_digest(getattr(value, name), name)
    except AttributeError:
        reject("n1-theorem-source-missing-fields")
    expected = n1_theorem_source()
    if value != expected:
        reject("n1-theorem-source-drift")
    logger.debug("snapshot_theorem exit")
    return expected
