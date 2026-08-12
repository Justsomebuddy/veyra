import logging

from veyra_sage.observer_patch_gluing import (
    EXPECTED_ROWS,
    VeyraObserverPatchGluingLab,
    exhaustive_g4_row,
    python_set_partitions,
)

logger = logging.getLogger(__name__)


def test_python_oracle_reproduces_every_pinned_count_through_three_nodes():
    logger.debug("test_python_oracle_reproduces_every_pinned_count_through_three_nodes entry")
    rows = tuple(exhaustive_g4_row(nodes) for nodes in range(1, 4))
    assert tuple(row.assignments for row in rows) == (1, 9, 1265)
    assert tuple(row.gluable for row in rows) == (1, 9, 481)
    assert tuple(row.unique for row in rows) == (1, 8, 432)
    assert all(row.classification_passed for row in rows)
    assert set(EXPECTED_ROWS) == {1, 2, 3}
    logger.debug("test_python_oracle_reproduces_every_pinned_count_through_three_nodes exit")


def test_oracle_facade_is_json_ready_and_totals_are_exact():
    logger.debug("test_oracle_facade_is_json_ready_and_totals_are_exact entry")
    summary = VeyraObserverPatchGluingLab().exhaustive_summary()
    assert summary["backend"] == "python"
    assert summary["covers"] == 115
    assert summary["assignments"] == 1275
    assert summary["matching_families"] == 515
    assert summary["gluable"] == 491
    assert summary["unique"] == 441
    assert summary["global_witnesses"] == 556
    assert summary["classification_passed"]
    logger.debug("test_oracle_facade_is_json_ready_and_totals_are_exact exit")


def test_python_partition_numbers_through_four_nodes():
    logger.debug("test_python_partition_numbers_through_four_nodes entry")
    assert tuple(len(python_set_partitions(tuple(range(nodes)))) for nodes in range(1, 5)) == (1, 2, 5, 15)
    logger.debug("test_python_partition_numbers_through_four_nodes exit")
