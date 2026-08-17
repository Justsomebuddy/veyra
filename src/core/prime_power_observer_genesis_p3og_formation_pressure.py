"""Explicit facade for the non-promoting P3-OG formation-pressure bridge."""

from .prime_power_observer_genesis_p3og_formation_pressure_runtime import (
    build_p3og_formation_pressure_binding,
)
from .prime_power_observer_genesis_p3og_formation_pressure_types import (
    P3OGFormationPressureBinding,
    P3OG_FORMATION_PRESSURE_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_formation_pressure_validation import (
    validate_p3og_formation_pressure_binding,
)

__all__ = (
    "P3OGFormationPressureBinding",
    "P3OG_FORMATION_PRESSURE_NONCLAIMS",
    "build_p3og_formation_pressure_binding",
    "validate_p3og_formation_pressure_binding",
)
