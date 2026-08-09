"""Validated public facade for the P3-OG finite machine-pressure experiment."""

from .prime_power_observer_genesis_p3og_runtime import run_p3og_pressure
from .prime_power_observer_genesis_p3og_source import (
    deterministic_select, p3og_source, validate_source,
)
from .prime_power_observer_genesis_p3og_types import (
    CandidatePressureResult, DeterministicSelectionReceipt, P3OG_NONCLAIMS,
    P3OGPressureReport, P3OGSource, PressureStatus, PrimitiveModeSeed,
    TransitionKind,
)
from .prime_power_observer_genesis_p3og_validation import validate_pressure_report

__all__ = (
    "CandidatePressureResult", "DeterministicSelectionReceipt", "P3OG_NONCLAIMS",
    "P3OGPressureReport", "P3OGSource", "PressureStatus", "PrimitiveModeSeed",
    "TransitionKind", "deterministic_select", "p3og_source", "run_p3og_pressure",
    "validate_pressure_report", "validate_source",
)
