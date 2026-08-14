"""Shared bounded fixtures for same-doctrine all-status P1-A transport v2."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from src.core.observer_core_kernel import crest_observer, tail_observer
from src.core.observer_core_types import Input, Pair
from src.core.observer_morphism import (
    observer_source_binding,
    p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ObserverSourceBinding
from src.core.observer_realization import (
    observer_realization_context,
    realize_observer_doctrine_r16,
)
from src.core.observer_realization_types import (
    ObserverRealizationWitness,
    RealizationContext,
)
from src.core.positive_ontology import internal_observer
from src.core.positive_ontology_doctrine import observer_doctrine
from src.core.positive_ontology_types import ObserverDoctrine
from src.core.proof_core_types import Pulse, Silence
from src.core.realization_transport import (
    RealizationTransportReceipt,
    realization_context_morphism,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class P1ATransportCase:
    """One exact doctrine/binding/context/v1-receipt test bundle."""

    doctrine: ObserverDoctrine
    binding: ObserverSourceBinding
    source: RealizationContext
    target: RealizationContext
    source_witness: ObserverRealizationWitness
    target_witness: ObserverRealizationWitness
    context_transport: RealizationTransportReceipt


def pulse(depth: int):
    """Build one finite unary recurrence at an exact test depth."""
    logger.debug("fixture pulse entry depth=%d", depth)
    result = Silence()
    for _ in range(depth):
        result = Pulse(result)
    logger.debug("fixture pulse exit depth=%d", depth)
    return result


def all_observer_costs(doctrine: ObserverDoctrine) -> tuple[tuple[str, int], ...]:
    """Assign a deterministic positive cost to every doctrine member in order."""
    logger.debug("fixture all_observer_costs entry observers=%d", len(doctrine.observers))
    result = tuple((member.observer_id, index + 1) for index, member in enumerate(doctrine.observers))
    logger.debug("fixture all_observer_costs exit costs=%d", len(result))
    return result


def realization_context(
    doctrine: ObserverDoctrine,
    name: str,
    depths: tuple[int, ...],
) -> RealizationContext:
    """Build an exact context with unique states and all-observer cost coverage."""
    logger.debug("fixture realization_context entry name=%s states=%d", name, len(depths))
    result = observer_realization_context(
        doctrine,
        name,
        tuple((f"{name}-state-{index}", pulse(depth)) for index, depth in enumerate(depths)),
        all_observer_costs(doctrine),
    )
    logger.debug("fixture realization_context exit name=%s", name)
    return result


def transport_case(
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
    *,
    name: str,
    source_depths: tuple[int, ...],
    target_depths: tuple[int, ...],
    graph: tuple[int, ...],
) -> P1ATransportCase:
    """Build both realization witnesses and their authoritative v1 receipt."""
    logger.debug(
        "fixture transport_case entry name=%s source=%d target=%d",
        name,
        len(source_depths),
        len(target_depths),
    )
    source = realization_context(doctrine, f"{name}-source", source_depths)
    target = realization_context(doctrine, f"{name}-target", target_depths)
    source_witness = realize_observer_doctrine_r16(doctrine, source)
    target_witness = realize_observer_doctrine_r16(doctrine, target)
    context_transport = realization_context_morphism(
        doctrine,
        source,
        target,
        f"{name}-context-map",
        graph,
        source_witness,
        target_witness,
    )
    result = P1ATransportCase(
        doctrine,
        binding,
        source,
        target,
        source_witness,
        target_witness,
        context_transport,
    )
    logger.debug("fixture transport_case exit name=%s", name)
    return result


def fixed_p1a_case(
    *,
    name: str = "fixed-p1a",
    source_depths: tuple[int, ...] = (2, 0, 1),
    target_depths: tuple[int, ...] = (0, 1, 2),
    graph: tuple[int, ...] = (2, 0, 1),
) -> P1ATransportCase:
    """Build the canonical five-observer P1-A doctrine and exact binding."""
    logger.debug("fixture fixed_p1a_case entry name=%s", name)
    doctrine = p1a_observer_morphism_doctrine()
    ids = tuple(member.observer_id for member in doctrine.observers)
    binding = observer_source_binding(doctrine, f"{name}-binding", ids)
    result = transport_case(
        doctrine,
        binding,
        name=name,
        source_depths=source_depths,
        target_depths=target_depths,
        graph=graph,
    )
    logger.debug("fixture fixed_p1a_case exit name=%s", name)
    return result


def mixed_projection_doctrine() -> ObserverDoctrine:
    """Return five unique observers covering strong right and blocked projection."""
    logger.debug("fixture mixed_projection_doctrine entry")
    crest = crest_observer()
    tail = tail_observer()
    fine_right = Pair(Input(), crest)
    result = observer_doctrine(
        "P1A-v2-mixed-projection-pressure",
        "closed-r11-pair-projection",
        (
            "source-fixed",
            "membership-not-chronology",
            "all-status-transport-pressure",
            "no-object-promotion",
        ),
        (
            internal_observer("coarse-crest", crest),
            internal_observer("fine-right-total", fine_right),
            internal_observer("fine-right-nested", Pair(Input(), fine_right)),
            internal_observer("coarse-tail", tail),
            internal_observer("fine-both-tail", Pair(tail, tail)),
        ),
        version="p1a-v2-test-doctrine-v1",
    )
    logger.debug("fixture mixed_projection_doctrine exit")
    return result


def mixed_projection_case(
    *,
    name: str = "mixed-p1a",
    source_depths: tuple[int, ...] = (0, 2, 1),
    target_depths: tuple[int, ...] = (0, 1, 2),
    graph: tuple[int, ...] = (0, 2, 1),
) -> P1ATransportCase:
    """Build a five-observer case with right/nested and Blocked projections."""
    logger.debug("fixture mixed_projection_case entry name=%s", name)
    doctrine = mixed_projection_doctrine()
    ids = tuple(member.observer_id for member in doctrine.observers)
    binding = observer_source_binding(doctrine, f"{name}-binding", ids)
    result = transport_case(
        doctrine,
        binding,
        name=name,
        source_depths=source_depths,
        target_depths=target_depths,
        graph=graph,
    )
    logger.debug("fixture mixed_projection_case exit name=%s", name)
    return result


def non_surjective_fixed_case() -> P1ATransportCase:
    """Build a duplicate graph with two target-only states for coverage pressure."""
    logger.debug("fixture non_surjective_fixed_case entry")
    result = fixed_p1a_case(
        name="non-surjective-p1a",
        source_depths=(0, 2, 2),
        target_depths=(0, 1, 2, 3),
        graph=(0, 2, 2),
    )
    logger.debug("fixture non_surjective_fixed_case exit")
    return result
