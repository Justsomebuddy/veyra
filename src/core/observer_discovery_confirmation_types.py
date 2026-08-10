"""Immutable records for fixed-winner caller-declared third-test confirmation."""

from __future__ import annotations

from dataclasses import dataclass

from .observer_discovery_types import BaselineComparison, DiscoveryObstruction

REPLICATED = "REPLICATED_ON_DECLARED_TEST"
NOT_REPLICATED = "NOT_REPLICATED_ON_DECLARED_TEST"
CONFIRMATION_BLOCKED = "BLOCKED"
CONFIRMATION_BOUNDARY = (
    "fixed pre-test observer and exact named baselines only; categorical association is not causality, "
    "semantic explanation, or population validity; caller-declared lineage and exchangeable equal-sized "
    "groups are trusted; isolation is logical and in-process, not authenticated or one-shot enforced"
)


@dataclass(frozen=True)
class DiscoveryConfirmationConfig:
    minimum_test_information_bits: float = 0.0
    minimum_test_gap_bits: float = 0.0
    significance_alpha: float = 0.05
    permutation_count: int = 99
    determinism_checks: int = 2
    max_test_rows: int = 8192
    max_work_items: int = 5_000_000
    random_seed: str = "veyra-observer-confirmation-v1"


@dataclass(frozen=True)
class FixedFamilyCalibration:
    """Global-independence max-stat calibration for the fixed declared family."""

    permutations: int
    exceedances: int
    observed_winner_information_bits: float
    add_one_p_value: float
    null_maxima_bits: tuple[float, ...]


@dataclass(frozen=True)
class DiscoveryConfirmationDigests:
    parent_result: str
    protocol: str
    test_data: str
    result: str


@dataclass(frozen=True)
class DiscoveryConfirmationReport:
    status: str
    config: DiscoveryConfirmationConfig | None
    winner_fingerprint: str | None
    test_information_bits: float | None
    baselines: tuple[BaselineComparison, ...]
    observer_gap_bits: float | None
    calibration: FixedFamilyCalibration | None
    digests: DiscoveryConfirmationDigests
    obstructions: tuple[DiscoveryObstruction, ...]
    boundary: str
