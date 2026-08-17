"""Closed DTOs for the non-promoting P3-OG formation-pressure bridge."""

from __future__ import annotations

from dataclasses import dataclass

from .prime_power_observer_genesis_p3og_types import PressureStatus


@dataclass(frozen=True)
class P3OGFormationPressureBinding:
    """Replay-derived identity link between formation and selected pressure."""

    version: str
    pressure_source_digest: str
    formation_source_digest: str
    formation_evidence_digest: str
    pressure_report_digest: str
    selection_receipt_digest: str
    selected_seed_digest: str
    pressure_entry_state_digest: str
    selected_candidate_result_digest: str
    selected_candidate_status: PressureStatus
    promotions: int
    nonclaims: tuple[str, ...]
    binding_digest: str


P3OG_FORMATION_PRESSURE_NONCLAIMS = (
    "formation-bound-pressure-is-not-observer-role",
    "selected-pressure-status-is-not-promoted",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "primitive-rez-nod-tact-breath-genealogy",
    "full-def-og-001-through-010-discharge",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "typed-history-dag-or-chronology",
    "typed-hap-history-or-witness",
    "post-formation-ablation-or-same-token-efficacy",
    "p1-or-p3-n0-dto-reuse",
    "raw-cycle-operational-representation-invariance",
    "formal-theorem-or-certificate",
    "truth-or-source-authentication",
    "physical-birth-or-consciousness",
    "absolute-observerhood-or-object-adoption",
    "prime-power-carrier-or-completed-infinity",
    "promotion",
)
