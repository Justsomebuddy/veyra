import logging
from itertools import product

from src.core.observer_patch_atlas import (
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
)
from src.core.observer_patch_gluing_classification import classify_exact_gluings
from veyra_sage.observer_patch_gluing import _cover_shapes, python_set_partitions

logger = logging.getLogger(__name__)


def test_production_classifier_agrees_with_independent_oracle_on_all_1275_assignments():
    logger.debug("test_production_classifier_agrees_with_independent_oracle_on_all_1275_assignments entry")
    assignments = gluable = unique = matching = 0
    for nodes in range(1, 4):
        universe = tuple(range(nodes))
        for cover in _cover_shapes(universe):
            local_options = tuple(python_set_partitions(patch) for patch in cover)
            for local_partitions in product(*local_options):
                assignments += 1
                node_names = tuple(f"n{node}" for node in universe)
                patches = tuple(
                    observer_patch(
                        f"P{index}", tuple(f"n{node}" for node in carrier)
                    )
                    for index, carrier in enumerate(cover)
                )
                atlas = observer_patch_atlas(node_names, patches)
                sections = tuple(
                    local_observer_section(
                        atlas,
                        f"P{index}",
                        tuple(tuple(f"n{node}" for node in block) for block in partition),
                    )
                    for index, partition in enumerate(local_partitions)
                )
                result = classify_exact_gluings(atlas, sections)
                matching += int(result.matching_family)
                gluable += int(result.criterion.exact_gluing_exists)
                unique += int(result.unique_exact_gluing)
                assert result.classification_holds
                assert result.uniqueness_iff_conflict_complete
                assert bool(result.direct_exact_gluing_count) == result.criterion.exact_gluing_exists
    assert (assignments, matching, gluable, unique) == (1275, 515, 491, 441)
    logger.debug("test_production_classifier_agrees_with_independent_oracle_on_all_1275_assignments exit")
