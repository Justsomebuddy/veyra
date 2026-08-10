from __future__ import annotations

import pytest

from src.core.observer_discovery_v3.schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
    canonical_three_way_presentation,
)
from src.core.observer_discovery_v3.schema.phase2_compat import (
    PHASE2_COMPAT_BOUNDARY,
    declared_test_rows_from_three_way,
    discovery_split_from_three_way,
)


def _presentation(prefix: str) -> CanonicalPresentation:
    schema = RepresentationSchema(
        "phase2-compat",
        (RepresentationField("bit", "binary", (0, 1)),),
        (0, 1),
    )
    rows = tuple(
        RepresentationRow(
            f"{prefix}-row-{index}",
            f"{prefix}-source-{index}",
            f"{prefix}-content-{index}",
            f"{prefix}-group-{index}",
            (index % 2,),
            index % 2,
        )
        for index in range(4)
    )
    return canonical_presentation(schema, rows)


def test_phase2_projection_is_explicit_detached_and_disclaims_test_custody() -> None:
    train = _presentation("train")
    validation = _presentation("validation")
    test = _presentation("test")
    three_way = canonical_three_way_presentation(train, validation, test)

    split = discovery_split_from_three_way(three_way)
    exported_test = declared_test_rows_from_three_way(three_way)

    assert tuple(row.row_id for row in split.train) == tuple(row.row_id for row in train.rows)
    assert tuple(row.row_id for row in split.holdout) == tuple(row.row_id for row in validation.rows)
    assert tuple(row.row_id for row in exported_test) == tuple(row.row_id for row in test.rows)
    assert split.train is not train.rows
    assert exported_test is not test.rows
    assert "no locked-test custody" in PHASE2_COMPAT_BOUNDARY
    assert "no claim promotion" in PHASE2_COMPAT_BOUNDARY


def test_phase2_projection_rejects_non_three_way_input() -> None:
    with pytest.raises(RepresentationProtocolError):
        discovery_split_from_three_way(object())  # type: ignore[arg-type]
