"""Executable certificate for the TR-1 observer-lattice candidate lane."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .observer_lattice import (
    TraceEcho,
    doctrine,
    fragility_spectrum,
    observer_lattice_checklist,
    primitivity_row,
    refinement_row,
    trace_class,
    transfer_row,
    verify_class_closure,
)

logger = logging.getLogger(__name__)

_ABC = ("a", "b", "c")


def certify_observer_lattice_tr1() -> Certificate:
    """Certify the lattice instrumentation with its adversarial controls."""
    logger.debug("certify_observer_lattice_tr1 entry")
    d_word = doctrine("word", _ABC, ())
    d_ab = doctrine("ab", _ABC, (("a", "b"),))
    d_ab_ac = doctrine("ab-ac", _ABC, (("a", "b"), ("a", "c")))
    d_bag = doctrine("bag", _ABC, (("a", "b"), ("a", "c"), ("b", "c")))
    chain = (d_word, d_ab, d_ab_ac, d_bag)

    spectrum = fragility_spectrum(chain, tuple("aabbcc"))
    spectrum_ok = (
        spectrum.status == "witnessed"
        and [row.primitive for row in spectrum.nodes] == [True, True, True, False]
        and spectrum.first_break_edge == "ab-ac->bag"
        and spectrum.edges[-1].omega_word == "abcabc"
        and spectrum.edges[-1].omega_exponent == 2
        and spectrum.edges[-1].omega_outside_fine
    )
    aabb = transfer_row(d_word, d_ab, tuple("aabb"))
    aabb_ok = (
        aabb.status == "witnessed" and aabb.fine_primitive
        and not aabb.coarse_primitive and aabb.omega_word == "abab"
        and aabb.omega_outside_fine
    )
    stable = fragility_spectrum((d_word, d_ab, d_bag), tuple("aab"))
    stable_ok = stable.status == "witnessed" and stable.first_break_edge == ""
    monotone_ok = True
    for word in (tuple("aabb"), tuple("abab"), tuple("aabbcc"), tuple("abc"), tuple("aabc")):
        rows = [primitivity_row(node, word) for node in chain]
        for fine, coarse in zip(rows, rows[1:]):
            monotone_ok = monotone_ok and not (coarse.primitive and not fine.primitive)
    refusal = trace_class(d_bag, tuple("aabbcc"), cap=10)
    refusal_ok = refusal == ("class-size-refusal", 10)
    non_refinement = refinement_row(d_bag, d_word)
    edge_ok = non_refinement.status == "blocked" and non_refinement.obstruction == "not-a-refinement"
    echo = trace_class(d_ab, tuple("aabb"))
    tamper_ok = (
        isinstance(echo, TraceEcho)
        and verify_class_closure(d_ab, echo)
        and not verify_class_closure(d_ab, TraceEcho(echo.doctrine_id, frozenset(sorted(echo.words)[:-1])))
    )
    checklist_ok = len(observer_lattice_checklist()) == 5
    passed = (
        spectrum_ok and aabb_ok and stable_ok and monotone_ok
        and refusal_ok and edge_ok and tamper_ok and checklist_ok
    )
    detail = (
        "aabbcc fragility spectrum breaks exactly at the bc edge with exhibit "
        "abcabc=(abc)^2 outside the fine class; aabb breaks at the ab edge with "
        "abab; aab never breaks; coarse-primitive => fine-primitive holds on "
        "the sample lattice; class cap refuses; non-refinement blocked with "
        "extra pairs; tampered class caught by the closure validator; "
        "instrumentation only, TR-2 transfer laws remain OPEN"
    )
    result = Certificate(
        "observer_lattice_tr1",
        "observer-lattice instrumentation: trace-class echoes, node primitivity, edge omega exhibits, fragility spectra",
        passed,
        detail,
        1,
    )
    if not passed:
        logger.error("certify_observer_lattice_tr1 failed detail=%s", detail)
    logger.debug("certify_observer_lattice_tr1 exit passed=%s", passed)
    return result
