"""Bounded canonical schemas for strict Phase-III discovery inputs."""

from .canonical import (
    canonical_presentation,
    canonical_representation_schema,
    canonical_three_way_presentation,
    representation_schema_digest,
    validate_canonical_presentation,
    validate_three_way_presentation,
)
from .types import (
    REPRESENTATION_BOUNDARY,
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationSchema,
    ThreeWayPresentation,
)

__all__ = (
    "REPRESENTATION_BOUNDARY",
    "CanonicalPresentation",
    "RepresentationField",
    "RepresentationProtocolError",
    "RepresentationRow",
    "RepresentationSchema",
    "ThreeWayPresentation",
    "canonical_presentation",
    "canonical_representation_schema",
    "canonical_three_way_presentation",
    "representation_schema_digest",
    "validate_canonical_presentation",
    "validate_three_way_presentation",
)
