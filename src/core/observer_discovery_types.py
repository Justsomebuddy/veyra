"""Immutable public records for bounded categorical observer discovery."""
from __future__ import annotations

from dataclasses import dataclass

from .observer_synthesis_types import Canonical, ObserverTerm

HARD_MAX_ALPHA = 0.05
HARD_MIN_STABILITY = 0.5
HARD_MIN_PERMUTATIONS = 19
HARD_MIN_BOOTSTRAPS = 16


@dataclass(frozen=True)
class DiscoveryRow:
    """One categorical observation with explicit record and lineage identities."""

    row_id: str
    source_id: str
    content_id: str
    group_id: str
    features: Canonical
    target: str | int | bool


@dataclass(frozen=True)
class DiscoverySplit:
    """A train/holdout split whose tuples cannot be mutated after construction."""

    train: tuple[DiscoveryRow, ...]
    holdout: tuple[DiscoveryRow, ...]


@dataclass(frozen=True)
class DiscoveryConfig:
    """Finite search, calibration, and stability protocol."""

    complexity_cost_per_unit: float = 0.01
    minimum_train_objective: float = 0.0
    minimum_holdout_information_bits: float = 0.0
    significance_alpha: float = 0.05
    permutation_count: int = 99
    bootstrap_replicates: int = 32
    minimum_stability: float = 0.5
    determinism_checks: int = 2
    max_catalog_size: int = 4096
    random_seed: str = "veyra-observer-discovery-v1"


@dataclass(frozen=True)
class DiscoveryPolicyReceipt:
    """Published complete configuration needed for independent validation."""

    complexity_cost_per_unit: float
    minimum_train_objective: float
    minimum_holdout_information_bits: float
    significance_alpha: float
    permutation_count: int
    bootstrap_replicates: int
    minimum_stability: float
    determinism_checks: int
    max_catalog_size: int
    random_seed: str


@dataclass(frozen=True)
class DiscoveryPrimitiveReceipt:
    """One typed primitive signature and audited integer cost."""

    name: str
    input_kind: str
    output_kind: str
    cost: int


@dataclass(frozen=True)
class DiscoveryGrammarReceipt:
    """Published structural grammar needed to replay winner complexity."""

    grammar_id: str
    input_kind: str
    accepted_output_kinds: tuple[str, ...]
    primitives: tuple[DiscoveryPrimitiveReceipt, ...]
    max_depth: int
    max_cost: int


@dataclass(frozen=True)
class DiscoveryScore:
    """Train-only score for one member of the exhausted finite catalog."""

    term: ObserverTerm
    fingerprint: str
    information_bits: float
    complexity: int
    objective: float


@dataclass(frozen=True)
class BaselineComparison:
    """Holdout information carried by one named baseline observer."""

    name: str
    observer_class: str
    fingerprint: str
    information_bits: float
    boundary: str


@dataclass(frozen=True)
class PermutationCalibration:
    """Family-wise max-statistic calibration over the complete catalog."""

    permutations: int
    exceedances: int
    observed_winner_information_bits: float
    add_one_p_value: float
    null_maxima_bits: tuple[float, ...]


@dataclass(frozen=True)
class BootstrapStability:
    """Train-only group bootstrap selection stability."""

    replicates: int
    winner_matches: int
    fraction: float


@dataclass(frozen=True)
class DiscoveryDigests:
    """Domain-separated identities for the protocol, data, catalog, and result."""

    protocol: str
    protocol_material: str
    policy: str
    grammar: str
    train_data: str
    train_evaluation: str
    holdout_data: str
    catalog: str
    result: str


@dataclass(frozen=True)
class DiscoveryObstruction:
    """Machine-readable reason why a terminal report could not claim FOUND."""

    reason: str
    detail: str


@dataclass(frozen=True)
class ObserverDiscoveryReport:
    """Terminal report; non-FOUND states never carry a partial winner."""

    status: str
    policy: DiscoveryPolicyReceipt | None
    grammar: DiscoveryGrammarReceipt | None
    winner: DiscoveryScore | None
    train_best_objective: float | None
    holdout_information_bits: float | None
    baselines: tuple[BaselineComparison, ...]
    observer_gap_bits: float | None
    calibration: PermutationCalibration | None
    stability: BootstrapStability | None
    catalog_size: int
    digests: DiscoveryDigests
    obstructions: tuple[DiscoveryObstruction, ...]
    boundary: str
