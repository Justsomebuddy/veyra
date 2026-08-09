"""Exact prime input and generated finite Lean witness for PΩ2."""

from __future__ import annotations

from math import isqrt
import logging

from .common import exact_digest, exact_shape, reject, sha
from .digest import digest
from .types import PrimeSource

logger = logging.getLogger(__name__)
PRIME_VERSION = "pomega2-prime-v1"
PRIME_ALGORITHM = "trial-division-native-decide-and-concrete-PPCP-application-v2"
MAX_PRIME = 65_521
_INSTANCE_PREFIX = b"""import VeyraPadicCompletion

set_option autoImplicit false

"""


def _is_prime(p: int) -> bool:
    """Decide bounded primality without trusting a caller Boolean."""
    logger.debug("_is_prime entry p=%r", p)
    if type(p) is not int or p < 2 or p > MAX_PRIME:
        result = False
    else:
        result = all(p % divisor for divisor in range(2, isqrt(p) + 1))
    logger.debug("_is_prime exit result=%s", result)
    return result


def _witness_bytes(p: int) -> bytes:
    """Generate a prime witness and concrete application of the canonical PPCP."""
    logger.debug("_witness_bytes entry p=%d", p)
    suffix = f"""def pomega2PrimeWitness : VeyraPrimeWitness {p} := by
  constructor
  · decide
  · decide

def pomega2ConcreteCompletion :
    VeyraPPCPBundle pomega2PrimeWitness
      (veyraCanonicalStageRingLaws pomega2PrimeWitness) :=
  THM_POMEGA2_017_ppcp_introduction pomega2PrimeWitness

#print axioms pomega2PrimeWitness
#print axioms pomega2ConcreteCompletion
""".encode()
    result = _INSTANCE_PREFIX + suffix
    logger.debug("_witness_bytes exit bytes=%d", len(result))
    return result


def prime_source(p: int) -> PrimeSource:
    """Construct one exact source only after independent primality checking."""
    logger.debug("prime_source entry p=%r", p)
    if not _is_prime(p):
        reject("prime-source-value-not-allowed-prime")
    payload = _witness_bytes(p)
    value = digest("veyra.pomega2.prime-source.v1", (
        ("version", PRIME_VERSION.encode()), ("p", p.to_bytes(4, "big")),
        ("algorithm", PRIME_ALGORITHM.encode()), ("witness-sha", sha(payload).encode()),
    ))
    result = PrimeSource(PRIME_VERSION, p, PRIME_ALGORITHM, payload, sha(payload), value)
    logger.debug("prime_source exit p=%d", p)
    return result


def snapshot_prime(value: PrimeSource) -> PrimeSource:
    """Reject foreign/composite/hostile/generated-source drift."""
    logger.debug("snapshot_prime entry")
    exact_shape(value, PrimeSource, "prime-source")
    try:
        if type(value.version) is not str or type(value.p) is not int:
            reject("prime-source-scalar-type-invalid")
        if type(value.witness_algorithm_id) is not str:
            reject("prime-source-algorithm-type-invalid")
        if type(value.generated_witness_bytes) is not bytes:
            reject("prime-source-witness-not-bytes")
        if len(value.generated_witness_bytes) > 2 * 1024 * 1024:
            reject("prime-source-witness-too-large")
        exact_digest(value.generated_witness_sha256, "prime-witness-sha")
        exact_digest(value.source_digest, "prime-source-digest")
    except AttributeError:
        reject("prime-source-missing-fields")
    expected = prime_source(value.p)
    if value != expected:
        reject("prime-source-drift")
    logger.debug("snapshot_prime exit p=%d", value.p)
    return expected
