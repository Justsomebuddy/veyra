"""Collision-safe root aliases for released finite P3-C2 transport coherence."""

from __future__ import annotations

from . import core as _p3c2
from . import formal as _formal
from . import ledger as _ledger

P3C2_FORMAL_VERSION = _formal.FORMAL_VERSION
P3C2_ARTIFACT_PATH = _formal.ARTIFACT_PATH
P3C2_ARTIFACT_SHA256 = _formal.ARTIFACT_SHA256
P3C2_THEOREM_IDS = _formal.THEOREM_IDS
P3C2_TOOLCHAIN_ID = _formal.TOOLCHAIN_ID
P3C2_TCB_DIGEST = _formal.TCB_DIGEST
P3C2_EXPECTED_AXIOMS = _formal.EXPECTED_AXIOMS
P3C2_LEDGER_VERSION = _ledger.LEDGER_VERSION
P3C2_LEDGER_ROWS = _ledger.LEDGER_ROWS
P3C2_LEDGER_EDGES = _ledger.LEDGER_EDGES
P3C2_AXIOM_CLOSURE = _ledger.AXIOM_CLOSURE
P3C2_LEDGER_DIGEST_ORACLE = _ledger.LEDGER_DIGEST_ORACLE
P3C2_NONCLAIMS = _p3c2.P3C2_NONCLAIMS

P3C2TransportCoherenceError = _p3c2.TransportCoherenceError
P3C2TransportCoherenceStatus = _p3c2.TransportCoherenceStatus
P3C2HigherCellStructureStatus = _p3c2.HigherCellStructureStatus
P3C2TransportFailureKind = _p3c2.TransportFailureKind
P3C2TransportFailedBound = _p3c2.TransportFailedBound
P3C2FormalFailureKind = _p3c2.FormalFailureKind
P3C2TransportValue = _p3c2.TransportValue
P3C2SetoidClassRow = _p3c2.SetoidClassRow
P3C2StateSetoidCarrier = _p3c2.StateSetoidCarrier
P3C2TransportMapEntry = _p3c2.TransportMapEntry
P3C2EdgeTransportMap = _p3c2.EdgeTransportMap
P3C2TotalTransportDoctrine = _p3c2.TotalTransportDoctrine
P3C2LocalCommutingFiller = _p3c2.LocalCommutingFiller
P3C2GeneratedTransportFiller = _p3c2.GeneratedTransportFiller
P3C2CofinalBoundaryReconciliation = _p3c2.CofinalBoundaryReconciliation
P3C2TransportTheoremSource = _p3c2.TransportTheoremSource
P3C2TransportAssumptionLedger = _p3c2.TransportAssumptionLedger
P3C2TransportPolicy = _p3c2.TransportPolicy
P3C2GeneratedTransportCoherence = _p3c2.GeneratedTransportCoherence
P3C2TransportResourceLimit = _p3c2.TransportResourceLimit
P3C2TransportFormalFailure = _p3c2.TransportFormalFailure
P3C2TransportPackage = _p3c2.TransportPackage

p3c2_positive_example = _p3c2.positive_example
p3c2_unequal_transport_example = _p3c2.unequal_transport_example
p3c2_check_transport_theorems = _p3c2.check_transport_theorems
p3c2_transport_theorem_source = _p3c2.transport_theorem_source
p3c2_transport_assumption_ledger = _p3c2.transport_assumption_ledger
p3c2_local_commuting_filler = _p3c2.local_commuting_filler
p3c2_transport_package = _p3c2.transport_package
p3c2_transport_policy = _p3c2.transport_policy
p3c2_apply_path = _p3c2.apply_path
p3c2_boundary_digest = _p3c2.boundary_digest
p3c2_derive_global_fillers = _p3c2.derive_global_fillers
p3c2_generated_paths = _p3c2.generated_paths
p3c2_paths_equivalent = _p3c2.paths_equivalent
p3c2_replay_path = _p3c2.replay_path
p3c2_cofinal_boundary_reconciliation = _p3c2.cofinal_boundary_reconciliation
p3c2_generated_transport_filler = _p3c2.generated_transport_filler
p3c2_generated_transport_coherence = _p3c2.generated_transport_coherence
p3c2_edge_transport_map = _p3c2.edge_transport_map
p3c2_state_setoid_carrier = _p3c2.state_setoid_carrier
p3c2_total_transport_doctrine = _p3c2.total_transport_doctrine
p3c2_transport_value = _p3c2.transport_value
p3c2_validate_transport_result = _p3c2.validate_transport_result

__all__ = tuple(name for name in globals() if name.startswith(("P3C2", "p3c2_")))
