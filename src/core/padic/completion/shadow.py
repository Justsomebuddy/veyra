"""Finite arithmetic shadows for PΩ2 QA, never completion evidence."""

from __future__ import annotations

import logging

from .common import reject
from .digest import digest
from .prime import prime_source
from .types import BoundedPadicShadow

logger = logging.getLogger(__name__)


def bounded_padic_shadow(p: int, depth: int = 8) -> BoundedPadicShadow:
    """Pressure zero/one/minus-one/restrictions at finite positive precisions."""
    logger.debug("bounded_padic_shadow entry p=%r depth=%r", p, depth)
    prime_source(p)
    if type(depth) is not int or not 2 <= depth <= 64:
        reject("padic-shadow-depth-invalid")
    moduli = tuple(p ** (n + 1) for n in range(depth))
    zero = tuple(0 for _ in moduli)
    one = tuple(1 for _ in moduli)
    minus_one = tuple(modulus - 1 for modulus in moduli)
    add_inverse = tuple((left + right) % modulus == 0 for left, right, modulus in zip(minus_one, one, moduli, strict=True))
    checks = 0
    strict = 0
    for m in range(depth):
        for n in range(m + 1, depth):
            coarse, fine = moduli[m], moduli[n]
            values = (zero[n], one[n], minus_one[n], (minus_one[n] + one[n]) % fine, (minus_one[n] * one[n]) % fine)
            expected = (zero[m], one[m], minus_one[m], 0, minus_one[m])
            if tuple(value % coarse for value in values) != expected:
                reject("internal-padic-shadow-restriction-failure")
            checks += len(values)
            witness = p ** (m + 1)
            if witness % coarse != 0 or witness % fine == 0:
                reject("internal-padic-shadow-refinement-witness-failure")
            strict += 1
    incompatible = list(zero)
    incompatible[0] = 1
    first = next(((m, n) for m in range(depth) for n in range(m + 1, depth)
                  if incompatible[n] % moduli[m] != incompatible[m]), None)
    scope = "bounded-arithmetic-pressure-not-family-or-completion-evidence"
    value = digest("veyra.pomega2.shadow.v1", (
        ("p", p.to_bytes(4, "big")), ("depth", depth.to_bytes(2, "big")),
        ("zero", repr(zero).encode()), ("one", repr(one).encode()),
        ("minus-one", repr(minus_one).encode()), ("checks", checks.to_bytes(8, "big")),
        ("strict", strict.to_bytes(8, "big")), ("first", repr(first).encode()),
        ("scope", scope.encode()),
    ))
    result = BoundedPadicShadow(
        p, depth, zero, one, minus_one, add_inverse, checks, strict, first, scope, value,
    )
    logger.debug("bounded_padic_shadow exit checks=%d strict=%d", checks, strict)
    return result
