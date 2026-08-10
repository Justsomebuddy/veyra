from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import logging

import pytest

from src.core.observer_discovery_v3.schema import (
    REPRESENTATION_BOUNDARY,
    CanonicalPresentation,
    RepresentationField,
    RepresentationProtocolError,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
    canonical_representation_schema,
    canonical_three_way_presentation,
    representation_schema_digest,
    validate_canonical_presentation,
    validate_three_way_presentation,
)
from src.core.observer_discovery_v3.schema.types import (
    HARD_MAX_CATEGORIES,
)
from src.core.observer_discovery_v3.transport import (
    TRANSPORT_APPLIED,
    TRANSPORT_BLOCKED,
    TRANSPORT_BOUNDARY,
    CategoryBijection,
    RepresentationTransportResult,
    RepresentationTransportSpec,
    apply_representation_transport,
    validate_representation_transport_result,
)
from src.core.observer_discovery_v3.transport.types import TRANSPORT_VERSION


def _schema(schema_id: str = "strict-representation") -> RepresentationSchema:
    return RepresentationSchema(
        schema_id,
        (
            RepresentationField("bit", "binary", (0, 1)),
            RepresentationField("color", "categorical", ("red", "blue")),
        ),
        ("no", "yes"),
    )


def _rows(prefix: str) -> tuple[RepresentationRow, ...]:
    values = ((0, "red", "no"), (1, "blue", "yes"), (0, "blue", "no"), (1, "red", "yes"))
    return tuple(
        RepresentationRow(
            f"{prefix}-row-{index}",
            f"{prefix}-source-{index}",
            f"{prefix}-content-{index}",
            f"{prefix}-group-{index}",
            (bit, color),
            target,
        )
        for index, (bit, color, target) in enumerate(values)
    )


def _presentation(prefix: str, schema: RepresentationSchema | None = None) -> CanonicalPresentation:
    return canonical_presentation(schema or _schema(), _rows(prefix))


def _transport_spec(source: CanonicalPresentation) -> RepresentationTransportSpec:
    return RepresentationTransportSpec(
        "swap-and-relabel",
        source.schema_digest,
        source.payload_digest,
        "transported-representation",
        (3, 2, 1, 0),
        (1, 0),
        ("shade", "inverted-bit"),
        (
            CategoryBijection((("red", "violet"), ("blue", "amber"))),
            CategoryBijection(((0, 1), (1, 0))),
        ),
        CategoryBijection((("no", 0), ("yes", 1))),
    )


def test_schema_and_presentation_are_deterministic_detached_and_frozen() -> None:
    raw_schema = _schema()
    raw_rows = _rows("train")
    first = canonical_presentation(raw_schema, raw_rows)
    second = canonical_presentation(raw_schema, raw_rows)

    assert first == second
    assert first.schema is not raw_schema
    assert first.rows is not raw_rows
    assert not hasattr(first, "__dict__")
    assert not hasattr(first.schema, "__dict__")
    assert first.schema_digest == representation_schema_digest(raw_schema)
    assert validate_canonical_presentation(first)
    assert first.boundary == REPRESENTATION_BOUNDARY
    assert "does not establish source fidelity" in first.boundary
    with pytest.raises(FrozenInstanceError):
        first.payload_digest = "0" * 64  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        first.rows[0].target = "yes"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("schema", "reason"),
    (
        (replace(_schema(), version="wrong"), "schema-version"),
        (replace(_schema(), schema_id=""), "schema-id"),
        (
            RepresentationSchema(
                "duplicate-field",
                (
                    RepresentationField("same", "binary", (0, 1)),
                    RepresentationField("same", "categorical", ("a", "b")),
                ),
                (0, 1),
            ),
            "duplicate-field-name",
        ),
        (
            RepresentationSchema(
                "wrong-binary-domain",
                (RepresentationField("bit", "binary", (False, True)),),
                (0, 1),
            ),
            "binary-domain-must-be-int-zero-one",
        ),
        (
            RepresentationSchema(
                "duplicate-category",
                (RepresentationField("category", "categorical", (True, True)),),
                (0, 1),
            ),
            "field-duplicate-category",
        ),
        (
            RepresentationSchema(
                "too-many-categories",
                (
                    RepresentationField(
                        "category",
                        "categorical",
                        tuple(range(HARD_MAX_CATEGORIES + 1)),
                    ),
                ),
                (0, 1),
            ),
            "field-categories",
        ),
    ),
)
def test_schema_rejects_noncanonical_or_unbounded_domains(
    schema: RepresentationSchema,
    reason: str,
) -> None:
    with pytest.raises(RepresentationProtocolError) as captured:
        canonical_representation_schema(schema)
    assert captured.value.detail == reason


def test_typed_categories_do_not_conflate_bool_and_int() -> None:
    schema = RepresentationSchema(
        "typed-categories",
        (RepresentationField("typed", "categorical", (True, 1)),),
        (False, 0),
    )
    rows = (
        RepresentationRow("r0", "s0", "c0", "g0", (True,), False),
        RepresentationRow("r1", "s1", "c1", "g1", (1,), 0),
    )

    presentation = canonical_presentation(schema, rows)

    assert presentation.rows[0].values == (True,)
    assert presentation.rows[1].values == (1,)
    assert presentation.rows[0].target is False
    assert presentation.rows[1].target == 0


@pytest.mark.parametrize(
    ("rows", "detail"),
    (
        (_rows("valid") + (_rows("valid")[0],), "duplicate-row-id"),
        ((replace(_rows("valid")[0], values=(0,)),) + _rows("valid")[1:], "row-width"),
        ((replace(_rows("valid")[0], values=(0, "green")),) + _rows("valid")[1:], "feature-outside-domain"),
        ((replace(_rows("valid")[0], target="maybe"),) + _rows("valid")[1:], "target-outside-domain"),
        (
            (replace(_rows("valid")[0], group_id=_rows("valid")[1].group_id),) + _rows("valid")[1:],
            "one-target-per-group-required",
        ),
        (
            (replace(_rows("valid")[0], source_id=_rows("valid")[1].source_id),) + _rows("valid")[1:],
            "lineage-crosses-groups",
        ),
    ),
)
def test_presentation_fails_closed_on_shape_domain_group_and_lineage_faults(
    rows: tuple[RepresentationRow, ...],
    detail: str,
) -> None:
    with pytest.raises(RepresentationProtocolError) as captured:
        canonical_presentation(_schema(), rows)
    assert captured.value.detail == detail


def test_presentation_rejects_unsupported_or_unbounded_scalars() -> None:
    bad_values = (None, 1.5, [0], "x" * 513, 1 << 256, "\ud800")
    for bad in bad_values:
        rows = (replace(_rows("bad")[0], values=(0, bad)),) + _rows("bad")[1:]
        with pytest.raises(RepresentationProtocolError):
            canonical_presentation(_schema(), rows)


def test_three_way_contract_binds_schema_lineage_and_declared_partitions() -> None:
    train = _presentation("train")
    validation = _presentation("validation")
    test = _presentation("test")

    first = canonical_three_way_presentation(train, validation, test)
    second = canonical_three_way_presentation(train, validation, test)
    assert first == second
    assert validate_three_way_presentation(first)
    assert first.train == train
    assert first.validation == validation
    assert first.test == test


@pytest.mark.parametrize("attribute", ("row_id", "source_id", "content_id", "group_id"))
def test_three_way_contract_rejects_every_cross_split_lineage_overlap(attribute: str) -> None:
    train = _presentation("train")
    validation_rows = list(_rows("validation"))
    validation_rows[0] = replace(validation_rows[0], **{attribute: getattr(train.rows[0], attribute)})
    validation = canonical_presentation(_schema(), tuple(validation_rows))

    with pytest.raises(RepresentationProtocolError) as captured:
        canonical_three_way_presentation(train, validation, _presentation("test"))
    assert captured.value.reason == "split-leakage"
    assert attribute in captured.value.detail


def test_three_way_contract_rejects_schema_mismatch_and_forged_roots() -> None:
    train = _presentation("train")
    with pytest.raises(RepresentationProtocolError) as mismatch:
        canonical_three_way_presentation(
            train,
            _presentation("validation", _schema("other-schema")),
            _presentation("test"),
        )
    assert mismatch.value.reason == "schema-mismatch"

    forged = replace(train, payload_digest="0" * 64)
    assert not validate_canonical_presentation(forged)
    with pytest.raises(RepresentationProtocolError) as rejected:
        canonical_three_way_presentation(forged, _presentation("validation"), _presentation("test"))
    assert rejected.value.reason == "invalid-presentation"


def test_transport_is_exact_deterministic_lineage_preserving_and_roundtrip_bound() -> None:
    source = _presentation("source")
    original = source
    spec = _transport_spec(source)

    first = apply_representation_transport(source, spec)
    second = apply_representation_transport(source, spec)

    assert first == second
    assert first.status == TRANSPORT_APPLIED
    assert first.destination is not None
    assert first.receipt is not None
    assert not first.obstructions
    assert validate_representation_transport_result(first, source, spec)
    assert source == original
    assert first.destination.schema.schema_id == "transported-representation"
    assert tuple(field.name for field in first.destination.schema.fields) == ("shade", "inverted-bit")
    assert first.destination.schema.fields[0].categories == ("violet", "amber")
    assert first.destination.schema.fields[1].categories == (0, 1)
    assert first.destination.schema.target_categories == (0, 1)
    assert first.destination.rows[0].row_id == source.rows[3].row_id
    assert first.destination.rows[0].values == ("violet", 0)
    assert first.destination.rows[0].target == 1
    assert first.receipt.lineage_preserved is True
    assert first.receipt.roundtrip_verified is True
    assert first.boundary == TRANSPORT_BOUNDARY
    assert "does not establish observer-response invariance" in first.boundary
    assert "E4 robustness" in first.boundary
    assert "or a theorem" in first.boundary


@pytest.mark.parametrize(
    "mutation",
    (
        {"version": "wrong"},
        {"source_schema_digest": "0" * 64},
        {"source_payload_digest": "f" * 64},
        {"row_order": (0, 1, 2, 2)},
        {"field_order": (0, 0)},
        {"destination_field_names": ("same", "same")},
        {"category_bijections": ()},
        {
            "category_bijections": (
                CategoryBijection((("red", "same"), ("blue", "same"))),
                CategoryBijection(((0, 0), (1, 1))),
            ),
        },
        {
            "category_bijections": (
                CategoryBijection((("blue", "violet"), ("red", "amber"))),
                CategoryBijection(((0, 0), (1, 1))),
            ),
        },
        {
            "category_bijections": (
                CategoryBijection((("red", "violet"), ("blue", "amber"))),
                CategoryBijection(((0, "zero"), (1, "one"))),
            ),
        },
    ),
)
def test_transport_faults_are_terminal_blocked_without_partial_output(
    mutation: dict[str, object],
) -> None:
    source = _presentation("source")
    spec = replace(_transport_spec(source), **mutation)

    result = apply_representation_transport(source, spec)

    assert result.status == TRANSPORT_BLOCKED
    assert result.destination is None
    assert result.receipt is None
    assert len(result.obstructions) == 1
    assert validate_representation_transport_result(result, source, spec)


def test_transport_blocks_non_utf8_destination_categories_without_raising() -> None:
    source = _presentation("source")
    spec = _transport_spec(source)
    invalid = replace(
        spec,
        category_bijections=(
            CategoryBijection((("red", "\ud800"), ("blue", "amber"))),
            spec.category_bijections[1],
        ),
    )

    result = apply_representation_transport(source, invalid)

    assert result.status == TRANSPORT_BLOCKED
    assert result.destination is None
    assert result.receipt is None
    assert result.obstructions[0].detail == "field-bijection-destination-string-encoding"


def test_transport_rejects_forged_source_result_and_receipt() -> None:
    source = _presentation("source")
    spec = _transport_spec(source)
    applied = apply_representation_transport(source, spec)
    assert applied.receipt is not None

    forged_source = replace(source, payload_digest="0" * 64)
    blocked = apply_representation_transport(forged_source, spec)
    assert blocked.status == TRANSPORT_BLOCKED
    assert blocked.obstructions[0].reason == "invalid-presentation"

    forged_receipt = replace(applied.receipt, roundtrip_verified=False)
    forged_result = replace(applied, receipt=forged_receipt)
    assert not validate_representation_transport_result(forged_result, source, spec)
    assert not validate_representation_transport_result(
        RepresentationTransportResult(TRANSPORT_APPLIED, None, None, (), TRANSPORT_BOUNDARY),
        source,
        spec,
    )


def test_maximum_length_transport_identity_remains_roundtrip_replayable() -> None:
    source = _presentation("source")
    spec = replace(_transport_spec(source), transport_id="t" * 512)

    result = apply_representation_transport(source, spec)

    assert result.status == TRANSPORT_APPLIED
    assert result.receipt is not None
    assert result.receipt.transport_id == "t" * 512
    assert validate_representation_transport_result(result, source, spec)


def test_schema_and_transport_logs_do_not_emit_raw_category_values(caplog: pytest.LogCaptureFixture) -> None:
    secret = "sensitive-category-value"
    schema = RepresentationSchema(
        "redacted-log-schema",
        (RepresentationField("safe-field", "categorical", (secret, "public")),),
        (0, 1),
    )
    rows = (
        RepresentationRow("r0", "s0", "c0", "g0", (secret,), 0),
        RepresentationRow("r1", "s1", "c1", "g1", ("public",), 1),
    )
    caplog.set_level(logging.DEBUG)

    presentation = canonical_presentation(schema, rows)
    result = apply_representation_transport(
        presentation,
        RepresentationTransportSpec(
            "identity",
            presentation.schema_digest,
            presentation.payload_digest,
            "redacted-log-schema-copy",
            (0, 1),
            (0,),
            ("safe-field-copy",),
            (CategoryBijection(((secret, secret), ("public", "public"))),),
            CategoryBijection(((0, 0), (1, 1))),
            TRANSPORT_VERSION,
        ),
    )

    assert result.status == TRANSPORT_APPLIED
    assert secret not in caplog.text
