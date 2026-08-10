"""Closed DTOs for provisional P1-D1 periodic productivity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .construction.finite_builder.types import TargetIndependence
from .infinity_prefix_types import PrefixAlphabet


class StructuralGuardedness(str, Enum):
    STRUCTURALLY_GUARDED = "structurally-guarded"


class ProductivityStatus(str, Enum):
    PRODUCTIVE = "productive"


class PointwiseSchemaStatus(str, Enum):
    ESTABLISHED = "established"


class PointwiseStatus(str, Enum):
    POINTWISE_CONSTRUCTIBLE = "pointwise-constructible"


class AllDepthEvidenceStatus(str, Enum):
    OPEN = "open"


class AllDepthProvenance(str, Enum):
    OPEN = "open"


class CompletedCarrierStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"


class OperationStatus(str, Enum):
    CONSTRUCTED = "constructed"
    RESTRICTION_ESTABLISHED = "restriction-established"
    RESOURCE_LIMIT = "resource-limit"


class OperationKind(str, Enum):
    CONSTRUCT = "construct"
    RESTRICT = "restrict"


class ResourceBound(str, Enum):
    DEPTH = "max-depth"
    OUTPUT_BYTES = "max-output-bytes"


@dataclass(frozen=True)
class PeriodicProgram:
    version: str
    alphabet: PrefixAlphabet
    period: tuple[str, ...]
    program_digest: str


@dataclass(frozen=True)
class ExecutionPolicy:
    version: str
    max_depth: int
    max_output_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class ProductiveProcessSource:
    program: PeriodicProgram
    totality_basis_id: str
    restriction_law_id: str
    output_encoding_id: str
    policy: ExecutionPolicy
    generator_digest: str
    source_digest: str


@dataclass(frozen=True)
class PeriodicPrefixStage:
    depth: int
    symbols: tuple[str, ...]
    output_encoding_id: str


@dataclass(frozen=True)
class ConstructionArtifact:
    program_digest: str
    generator_digest: str
    source_digest: str
    policy_digest: str
    run_digest: str
    depth: int
    stage: PeriodicPrefixStage
    output_digest: str
    trace_digest: str
    guardedness: StructuralGuardedness = StructuralGuardedness.STRUCTURALLY_GUARDED
    operation_status: OperationStatus = OperationStatus.CONSTRUCTED
    pointwise_schema: PointwiseSchemaStatus = PointwiseSchemaStatus.ESTABLISHED
    pointwise_status: PointwiseStatus = PointwiseStatus.POINTWISE_CONSTRUCTIBLE
    productivity: ProductivityStatus = ProductivityStatus.PRODUCTIVE
    all_depth_family: AllDepthEvidenceStatus = AllDepthEvidenceStatus.OPEN
    all_depth_provenance: AllDepthProvenance = AllDepthProvenance.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    target_independence: TargetIndependence = TargetIndependence.NOT_ESTABLISHED
    scope: str = "one-demanded-finite-prefix-only"


@dataclass(frozen=True)
class RestrictionArtifact:
    program_digest: str
    generator_digest: str
    source_digest: str
    policy_digest: str
    run_digest: str
    m: int
    n: int
    lower_stage: PeriodicPrefixStage
    upper_stage: PeriodicPrefixStage
    restricted_stage: PeriodicPrefixStage
    lower_output_digest: str
    upper_output_digest: str
    restricted_output_digest: str
    restriction_law_id: str
    evidence_digest: str
    guardedness: StructuralGuardedness = StructuralGuardedness.STRUCTURALLY_GUARDED
    operation_status: OperationStatus = OperationStatus.RESTRICTION_ESTABLISHED
    pointwise_schema: PointwiseSchemaStatus = PointwiseSchemaStatus.ESTABLISHED
    pointwise_status: PointwiseStatus = PointwiseStatus.POINTWISE_CONSTRUCTIBLE
    productivity: ProductivityStatus = ProductivityStatus.PRODUCTIVE
    all_depth_family: AllDepthEvidenceStatus = AllDepthEvidenceStatus.OPEN
    all_depth_provenance: AllDepthProvenance = AllDepthProvenance.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    target_independence: TargetIndependence = TargetIndependence.NOT_ESTABLISHED
    scope: str = "fresh-finite-periodic-restriction"


@dataclass(frozen=True)
class ResourceLimitResult:
    operation: OperationKind
    requested_depths: tuple[int, ...]
    failed_bound: ResourceBound
    required_value: int
    allowed_value: int
    program_digest: str
    generator_digest: str
    source_digest: str
    policy_digest: str
    run_digest: str
    refusal_digest: str
    guardedness: StructuralGuardedness = StructuralGuardedness.STRUCTURALLY_GUARDED
    operation_status: OperationStatus = OperationStatus.RESOURCE_LIMIT
    pointwise_schema: PointwiseSchemaStatus = PointwiseSchemaStatus.ESTABLISHED
    productivity: ProductivityStatus = ProductivityStatus.PRODUCTIVE
    all_depth_family: AllDepthEvidenceStatus = AllDepthEvidenceStatus.OPEN
    all_depth_provenance: AllDepthProvenance = AllDepthProvenance.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    target_independence: TargetIndependence = TargetIndependence.NOT_ESTABLISHED
    scope: str = "operational-refusal-not-mathematical-nonexistence"


ConstructionResult: TypeAlias = ConstructionArtifact | ResourceLimitResult
RestrictionResult: TypeAlias = RestrictionArtifact | ResourceLimitResult
