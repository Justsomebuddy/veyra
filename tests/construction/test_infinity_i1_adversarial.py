"""Adversarial exact-type and resource-bound regressions for I1."""

import logging

import pytest

from src.core.infinity_prefix import periodic_prefix_window, prefix_alphabet, prefix_stage, prefix_tower_window, restrict_prefix
from src.core.infinity_prefix_types import PrefixStage, PrefixTowerWindow
from src.core.infinity_prefix_validation import InfinityPrefixValidationError, snapshot_prefix_window
from src.core.padic_residue_tower import integer_padic_window, padic_residue_stage, padic_residue_window, prime_base, project_padic_stage
from src.core.padic_residue_types import PadicResidueStage, PadicResidueWindow
from src.core.padic_residue_validation import PadicResidueValidationError, snapshot_padic_window

logger = logging.getLogger(__name__)


class IntSubclass(int):
    """An integer subclass used to probe exact-type gates."""


class StringSubclass(str):
    """A string subclass used to probe exact-type gates."""


class ExplosiveMeta(type):
    """A metaclass that detects unsafe pre-gate class-name logging."""

    def __getattribute__(cls, name):
        if name == "__name__":
            raise AssertionError("hostile metaclass name hook executed")
        return super().__getattribute__(name)


class HostileValue(metaclass=ExplosiveMeta):
    """An invalid value whose metaclass must remain untouched."""


class ReprTrap:
    """An input whose representation must never run before a type gate."""

    def __repr__(self) -> str:
        logger.error("ReprTrap.__repr__ invoked")
        raise AssertionError("hostile repr invoked before an exact-type gate")


def test_prefix_rejects_mutability_duplicates_foreign_symbols_and_bad_lengths():
    logger.debug("test_prefix_rejects_mutability_duplicates_foreign_symbols_and_bad_lengths entry")
    with pytest.raises(InfinityPrefixValidationError):
        prefix_alphabet(["a", "b"])  # type: ignore[arg-type]
    with pytest.raises(InfinityPrefixValidationError, match="unique"):
        prefix_alphabet(("a", "a"))
    with pytest.raises(InfinityPrefixValidationError, match="exact strings"):
        prefix_alphabet((StringSubclass("a"),))
    alphabet = prefix_alphabet(("a", "b"))
    with pytest.raises(InfinityPrefixValidationError, match="exact tuple"):
        prefix_tower_window(alphabet, ((), ["a"]))  # type: ignore[list-item]
    with pytest.raises(InfinityPrefixValidationError, match="foreign"):
        prefix_tower_window(alphabet, ((), ("x",)))
    malformed = PrefixTowerWindow(alphabet, (PrefixStage(0, ()), PrefixStage(1, ())))
    with pytest.raises(InfinityPrefixValidationError, match="matching its depth"):
        snapshot_prefix_window(malformed)
    logger.debug("test_prefix_rejects_mutability_duplicates_foreign_symbols_and_bad_lengths exit")


def test_prefix_rejects_bool_depth_and_resource_overflow():
    logger.debug("test_prefix_rejects_bool_depth_and_resource_overflow entry")
    alphabet = prefix_alphabet(("a",))
    with pytest.raises(InfinityPrefixValidationError, match="depth"):
        periodic_prefix_window(alphabet, ("a",), True)
    with pytest.raises(InfinityPrefixValidationError, match="depth"):
        periodic_prefix_window(alphabet, ("a",), ReprTrap())  # type: ignore[arg-type]
    with pytest.raises(InfinityPrefixValidationError, match="depth"):
        periodic_prefix_window(alphabet, ("a",), 129)
    with pytest.raises(InfinityPrefixValidationError, match="bounded"):
        prefix_alphabet(("x" * 129,))
    with pytest.raises(InfinityPrefixValidationError):
        prefix_alphabet(HostileValue())  # type: ignore[arg-type]
    with pytest.raises(InfinityPrefixValidationError, match="missing required fields"):
        snapshot_prefix_window(PrefixTowerWindow.__new__(PrefixTowerWindow))
    with pytest.raises(InfinityPrefixValidationError, match="depth"):
        prefix_stage(alphabet, True, ("a",))
    with pytest.raises(InfinityPrefixValidationError, match="missing required fields"):
        restrict_prefix(PrefixStage.__new__(PrefixStage), 0)
    logger.debug("test_prefix_rejects_bool_depth_and_resource_overflow exit")


def test_padic_rejects_bool_subclass_composite_and_large_prime():
    logger.debug("test_padic_rejects_bool_subclass_composite_and_large_prime entry")
    for value in (True, IntSubclass(5), 4, 263):
        with pytest.raises(PadicResidueValidationError, match="prime"):
            prime_base(value)
    with pytest.raises(PadicResidueValidationError, match="prime"):
        prime_base(HostileValue())  # type: ignore[arg-type]
    with pytest.raises(PadicResidueValidationError, match="prime"):
        prime_base(ReprTrap())  # type: ignore[arg-type]
    with pytest.raises(PadicResidueValidationError, match="exact PrimeBase"):
        snapshot_padic_window(PadicResidueWindow(5, ()))  # type: ignore[arg-type]
    logger.debug("test_padic_rejects_bool_subclass_composite_and_large_prime exit")


def test_padic_rejects_mutable_noncanonical_and_malformed_stages():
    logger.debug("test_padic_rejects_mutable_noncanonical_and_malformed_stages entry")
    base = prime_base(5)
    with pytest.raises(PadicResidueValidationError, match="exact tuple"):
        padic_residue_window(base, [2, 7])  # type: ignore[arg-type]
    for residues in ((5,), (-1,), (IntSubclass(2),)):
        with pytest.raises(PadicResidueValidationError):
            padic_residue_window(base, residues)
    malformed = PadicResidueWindow(base, (PadicResidueStage(0, 25, 2),))
    with pytest.raises(PadicResidueValidationError, match="modulus"):
        snapshot_padic_window(malformed)
    with pytest.raises(PadicResidueValidationError, match="stage must"):
        snapshot_padic_window(PadicResidueWindow(base, (object(),)))  # type: ignore[arg-type]
    with pytest.raises(PadicResidueValidationError, match="missing required fields"):
        project_padic_stage(base, PadicResidueStage.__new__(PadicResidueStage), 0)
    with pytest.raises(PadicResidueValidationError, match="index"):
        padic_residue_stage(base, True, 2)
    logger.debug("test_padic_rejects_mutable_noncanonical_and_malformed_stages exit")


def test_padic_rejects_depth_and_source_integer_resource_overflow():
    logger.debug("test_padic_rejects_depth_and_source_integer_resource_overflow entry")
    base = prime_base(5)
    for depth in (True, 0, 129):
        with pytest.raises(PadicResidueValidationError, match="depth"):
            integer_padic_window(base, 2, depth)
    with pytest.raises(PadicResidueValidationError, match="source"):
        integer_padic_window(base, IntSubclass(2), 2)
    with pytest.raises(PadicResidueValidationError, match="source"):
        integer_padic_window(base, 1 << 4096, 2)
    logger.debug("test_padic_rejects_depth_and_source_integer_resource_overflow exit")
