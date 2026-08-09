"""Direct level-1 certificate for isolated P3-C2 transport coherence."""

from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..transport.counterpressure import ATTACK_IDS, required_transport_attacks
from ..transport.examples import positive_example
from ..transport.runtime import generated_transport_coherence
from ..transport.types import GeneratedTransportCoherence, HigherCellStructureStatus, TransportCoherenceStatus
from ..transport.validation import validate_transport_result

logger = logging.getLogger(__name__)


def certify_transport_coherence_p3c2() -> Certificate:
    """Certify C2.2 while keeping genuine higher cell-structure C2.3 open."""
    logger.debug("certify_transport_coherence_p3c2 entry")
    package = positive_example().package
    first = generated_transport_coherence(package)
    second = validate_transport_result(package, first)
    attacks = required_transport_attacks(first) if type(first) is GeneratedTransportCoherence else ()
    passed = (
        type(first) is GeneratedTransportCoherence
        and type(second) is GeneratedTransportCoherence
        and first == second
        and first is not second
        and first.status is TransportCoherenceStatus.GENERATED_TRANSPORT_COHERENT_RELATIVE_TO_SYSTEM
        and first.higher_cell_structure is HigherCellStructureStatus.NOT_IMPLEMENTED
        and first.local_square_count == 2
        and first.global_boundary_count > 2
        and first.formal_phase_count == 3
        and len(package.assumption_ledger.ordered_rows) == 23
        and len(package.assumption_ledger.direct_edges) == 41
        and first.assumption_ledger_digest == package.assumption_ledger.ledger_digest
        and len(first.global_fillers) == first.global_boundary_count
        and tuple(x.attack_id for x in attacks) == ATTACK_IDS
        and all(x.passed for x in attacks)
    )
    detail = f"local_squares={getattr(first, 'local_square_count', 0)} global_fillers={getattr(first, 'global_boundary_count', 0)} semantic_work={getattr(first, 'semantic_work', 0)} lean=3 ledger_rows=23 ledger_edges=41 attacks={len(attacks)} setoid_total=1 p3t_adapter=0 higher_cell_structure=not_implemented promotions=0"
    result = Certificate(
        "transport_coherence_p3c2",
        "exact finite setoid transports, commuting local squares, structural GTCP, separate symbolic Nat-op",
        passed,
        detail,
        1,
    )
    logger.debug("certify_transport_coherence_p3c2 exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_transport_coherence_p3c2())
