"""Shared certificate datatypes for Veyra verification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Certificate:
    """One executable certificate item.

    ``available`` separates "this environment cannot run the check" from "the
    check ran and the claim did not hold". Only the second is evidence about
    the mathematics; an absent toolchain must never read as a broken proof.
    A certificate that could not run reports ``passed=False`` together with
    ``available=False``, and reporting tools must branch on the field rather
    than on the wording of ``detail``.
    """

    name: str
    method: str
    passed: bool
    detail: str
    level: int
    available: bool = True
