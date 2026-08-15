"""Immutable DTOs for explicit masked missing-data preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..schema import RepresentationSchema, ThreeWayPresentation
from ..schema.types import RepresentationScalar

POLICY_SCHEMA = "veyra.observer-discovery.v3.missing-policy.v1"
PRESENTATION_SCHEMA = "veyra.observer-discovery.v3.missing-presentation.v1"
MISSING_BOUNDARY = (
    "explicit caller-declared finite missing-marker encoding only; no imputation correctness, "
    "missingness mechanism, source truth, provenance, statistical validity, theorem, certificate, "
    "object formation, or claim promotion"
)
MISSING_NONCLAIMS = (
    "marker-denotes-real-world-absence:not-established",
    "fallback-correctness:not-established",
    "mcar-mar-mnar:not-established",
    "source-truth-authentication-provenance:not-established",
    "statistical-causal-theorem-promotion:not-established",
)


class MissingWireFormat(str, Enum):
    """Exact source syntax bound into the top receipt."""

    CSV = "CSV"
    JSONL = "JSONL"


class MissingPolicyMode(str, Enum):
    """One ordered base-field policy."""

    REQUIRED = "REQUIRED"
    EXPLICIT_MASK = "EXPLICIT_MASK"


class MissingReplayAuthority(str, Enum):
    """Whether exact source-backed policy replay occurred in this call."""

    NATIVE_POLICY_REPLAY = "NATIVE_POLICY_REPLAY"
    EXTERNAL_BINDING_ONLY = "EXTERNAL_BINDING_ONLY"


@dataclass(frozen=True, slots=True)
class MissingFieldRule:
    """Caller-declared rule for one base feature in schema order."""

    field_name: str
    mode: MissingPolicyMode
    fallback: RepresentationScalar | None = None
    derived_name: str | None = None


@dataclass(frozen=True, slots=True)
class MissingDataPolicy:
    """Canonical policy binding both complete schemas and ordered rules."""

    schema_version: str
    base_schema: RepresentationSchema
    base_schema_digest: str
    projected_schema: RepresentationSchema
    projected_schema_digest: str
    rules: tuple[MissingFieldRule, ...]
    projection_spec_root: str
    policy_digest: str


@dataclass(frozen=True, slots=True)
class MissingSplitReceipt:
    """Exact raw, semantic-mask, projection and output commitments for one split."""

    raw_digest: str
    semantic_mask_digest: str
    projection_digest: str
    output_payload_digest: str
    row_count: int
    receipt_digest: str


@dataclass(frozen=True, slots=True)
class MissingnessReceipt:
    """Top replay receipt with explicit format and authority class."""

    schema_version: str
    wire_format: MissingWireFormat
    authority: MissingReplayAuthority
    base_schema_digest: str
    projected_schema_digest: str
    policy_digest: str
    train: MissingSplitReceipt
    validation: MissingSplitReceipt
    test: MissingSplitReceipt
    protocol_digest: str
    nonclaims_digest: str
    receipt_digest: str
    boundary: str = MISSING_BOUNDARY


@dataclass(frozen=True, slots=True)
class MissingnessPresentation:
    """Separate policy-retaining wrapper around the projected v1 presentation."""

    policy: MissingDataPolicy
    presentation: ThreeWayPresentation
    receipt: MissingnessReceipt
    boundary: str = MISSING_BOUNDARY
