"""Level-1 certificate for the bounded P0 positive-ontology experiment."""

from __future__ import annotations

import logging

from ..certify_types import Certificate
from ..construction.infinity_prefix import periodic_prefix_window, prefix_alphabet, prefix_stage
from ..observer.patch_atlas import triangle_counterexample
from ..ontology.core import (
    continuation_witness,
    observer_support_judgment,
    family_extension_judgment,
    metalanguage_boundary,
    ontology_presentation,
    ontology_stage,
    persistence_judgment,
    presentation_commitment,
)
from ..ontology.boundaries import (
    bounded_window_judgment,
    diagram_coherence_judgment,
    local_extension_judgment,
    nonfinite_infinity_boundary,
    positive_ontology_checklist,
)
from ..ontology.facets import ontology_facet_report
from ..ontology.doctrine import p0_observer_doctrine
from ..ontology.types import (
    ObserverSupport,
    FacetStatus,
    InfinityLevel,
    RelationStatus,
    SilenceModality,
)
from ..proof_core_types import Pulse, Silence

logger = logging.getLogger(__name__)


def certify_positive_ontology_p0() -> Certificate:
    """Certify finite typed judgments and their explicit nonclaim boundaries."""
    logger.debug("certify_positive_ontology_p0 entry")
    boundary = metalanguage_boundary()
    doctrine = p0_observer_doctrine()
    silent_stage = ontology_stage("silent", Silence(), doctrine, 1)
    silent = observer_support_judgment(silent_stage)
    lower = ontology_stage("s0", Pulse(Silence()), doctrine, 1)
    upper = ontology_stage("s1", Pulse(Pulse(Silence())), doctrine, 2)
    witness = continuation_witness("w01", "history", "s0", "s1", ("crest",))
    presentation = ontology_presentation(
        doctrine, "fixed-family-pressure", (lower, upper), (witness,)
    )
    persistence = persistence_judgment(presentation, "history")
    family = family_extension_judgment(presentation, "w01")
    facets = ontology_facet_report(
        lower,
        doctrine,
        presentation=presentation_commitment("finite-presentation", lower),
        persistence_presentation=presentation,
        persistence_path_id="history",
    )
    triangle = triangle_counterexample()
    diagram = diagram_coherence_judgment(triangle.atlas, triangle.sections)
    alphabet = prefix_alphabet(("a", "b"))
    window = periodic_prefix_window(alphabet, ("a", "b"), 3)
    bounded = bounded_window_judgment(window)
    extension = local_extension_judgment(
        window, prefix_stage(alphabet, 4, ("a", "b", "a", "b"))
    )
    higher = tuple(
        nonfinite_infinity_boundary(level)
        for level in (
            InfinityLevel.PRODUCTIVE_PROCESS,
            InfinityLevel.ALL_DEPTH_HYPOTHESIS,
            InfinityLevel.COMPLETED_CARRIER,
        )
    )
    passed = (
        not boundary.echo_reflects_identity
        and not boundary.metaphysical_proof
        and silent.support is ObserverSupport.SUPPORTED
        and silent.silence == (
            SilenceModality.INTRINSIC, SilenceModality.RESPONSE,
        )
        and persistence.status is RelationStatus.ECHO
        and family.inherited_status is RelationStatus.ECHO
        and family.full_status is RelationStatus.SPLIT
        and facets.constructible is FacetStatus.OPEN
        and facets.persistent is FacetStatus.OPEN
        and facets.scoped_object is FacetStatus.OPEN
        and diagram.pairwise_compatible
        and not diagram.global_coherent
        and bounded.verified
        and extension.verified
        and all(not row.verified and not row.finite_promoted for row in higher)
        and len(positive_ontology_checklist()) == 10
    )
    detail = (
        "provisional-bounded-fixed-family=crest+tail persistence=echo "
        "family-extension=split pairwise/global=True/False infinity=2+3-boundaries "
        "no-completed-admission-or-translation"
    )
    result = Certificate(
        "positive_ontology_p0",
        "provisional bounded fixed-family pressure; no completed admission or translation",
        passed,
        detail,
        1,
    )
    logger.debug("certify_positive_ontology_p0 exit passed=%s", result.passed)
    return result
