"""Hostile boundary coverage for RFC 172 missing-data replay."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import StringIO
import csv
import json
import logging

import pytest

import src.core.observer_discovery_v3.missing_data.resources as missing_resources
import src.core.observer_discovery_v3.missing_data.runtime as missing_runtime
import src.core.observer_discovery_v3.missing_data.codec as missing_codec
from src.core.observer_discovery_v3.missing_data import (
    MissingDataProtocolError,
    MissingDataPolicy,
    MissingFieldRule,
    MissingPolicyMode,
    MissingReplayAuthority,
    MissingWireFormat,
    MissingnessPresentation,
    canonical_missing_data_policy,
    external_binding,
    missingness_presentation_from_json,
    missingness_presentation_json,
    projected_schema_for_missing_policy,
    validate_native_missingness_presentation,
    validate_structural_missingness_presentation,
)
from src.core.observer_discovery_v3.missing_data.digest import RAW_SPLIT_DOMAIN, raw_split_digest
from src.core.observer_discovery_v3.missing_data.parsing import ParsedMissingSplit
from src.core.observer_discovery_v3.missing_data.runtime import missingness_from_csv, missingness_from_jsonl
from src.core.observer_discovery_v3.schema import (
    CanonicalPresentation,
    RepresentationField,
    RepresentationRow,
    RepresentationSchema,
    canonical_presentation,
    canonical_three_way_presentation,
)
from test_observer_discovery_v3_missing_data import _build_csv, _contract, _csv, _jsonl

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "rules",
    (
        (MissingFieldRule("label", MissingPolicyMode.REQUIRED, "red", None),),
        (MissingFieldRule("label", MissingPolicyMode.EXPLICIT_MASK, "outside", "label__present_v1"),),
        (MissingFieldRule("label", MissingPolicyMode.EXPLICIT_MASK, "red", "wrong"),),
    ),
)
def test_policy_rule_shapes_fail_closed(rules):
    logger.debug("test hostile policy shape entry")
    base = RepresentationSchema(
        "policy-hostile", (RepresentationField("label", "categorical", ("red", "blue")),), (0, 1)
    )
    with pytest.raises(MissingDataProtocolError):
        projected_schema_for_missing_policy(base, rules)
    logger.debug("test hostile policy shape exit")


def test_binary_fields_cannot_be_masked_and_fallback_identity_is_typed():
    logger.debug("test binary/type policy entry")
    binary = RepresentationSchema("binary-hostile", (RepresentationField("flag", "binary", (0, 1)),), (0, 1))
    with pytest.raises(MissingDataProtocolError, match="^mask-categorical-only$"):
        projected_schema_for_missing_policy(
            binary, (MissingFieldRule("flag", MissingPolicyMode.EXPLICIT_MASK, 0, "flag__present_v1"),)
        )
    typed = RepresentationSchema("typed-hostile", (RepresentationField("value", "categorical", (1, True)),), (0, 1))
    int_rules = (MissingFieldRule("value", MissingPolicyMode.EXPLICIT_MASK, 1, "value__present_v1"),)
    bool_rules = (MissingFieldRule("value", MissingPolicyMode.EXPLICIT_MASK, True, "value__present_v1"),)
    assert (
        projected_schema_for_missing_policy(typed, int_rules).schema_id
        != projected_schema_for_missing_policy(typed, bool_rules).schema_id
    )
    logger.debug("test binary/type policy exit")


@pytest.mark.parametrize(
    ("mutator", "reason"),
    (
        (lambda raw: raw.replace(b"s:red", b"m:", 1), "required-feature-missing"),
        (lambda raw: raw.replace(b"train-r0", b"m:", 1), "identity-missing"),
        (lambda raw: raw.replace(b"s:allow", b"m:", 1), "target-missing"),
    ),
)
def test_missing_markers_are_admitted_only_at_explicit_masked_features(mutator, reason):
    logger.debug("test missing marker scope entry reason=%s", reason)
    base, projected, policy = _contract()
    required = replace(policy.rules[0], mode=MissingPolicyMode.REQUIRED, fallback=None, derived_name=None)
    required_projected = projected_schema_for_missing_policy(base, (required, *policy.rules[1:]))
    required_policy = canonical_missing_data_policy(base, required_projected, (required, *policy.rules[1:]))
    raw = mutator(_csv("train"))
    with pytest.raises(MissingDataProtocolError, match=rf"^{reason}$"):
        missingness_from_csv(
            required_policy,
            base,
            required_projected,
            train=raw,
            validation=_csv("validation"),
            test=_csv("test"),
        )
    logger.debug("test missing marker scope exit")


def test_json_duplicate_key_and_required_null_fail_closed():
    logger.debug("test hostile JSON entry")
    base, projected, policy = _contract()
    duplicate = _jsonl("train").replace(b'"row_id":', b'"row_id":"duplicate","row_id":', 1)
    with pytest.raises(MissingDataProtocolError, match="^json-duplicate-key$"):
        missingness_from_jsonl(
            policy, base, projected, train=duplicate, validation=_jsonl("validation"), test=_jsonl("test")
        )
    required_null = _jsonl("train").replace(b'"typed":1', b'"typed":null', 1)
    with pytest.raises(MissingDataProtocolError, match="^required-feature-missing$"):
        missingness_from_jsonl(
            policy,
            base,
            projected,
            train=required_null,
            validation=_jsonl("validation"),
            test=_jsonl("test"),
        )
    logger.debug("test hostile JSON exit")


def test_raw_digest_is_exact_domain_nul_bytes_and_source_mutation_breaks_replay():
    logger.debug("test raw commitment entry")
    base, projected, policy, raws, value = _build_csv()
    assert raw_split_digest(raws[0]) == sha256(RAW_SPLIT_DOMAIN.encode() + b"\0" + raws[0]).hexdigest()
    changed = raws[0] + b"\n"
    assert not validate_native_missingness_presentation(
        value,
        policy,
        base,
        projected,
        wire_format=MissingWireFormat.CSV,
        train=changed,
        validation=raws[1],
        test=raws[2],
    )
    logger.debug("test raw commitment exit")


def test_receipt_splice_and_authority_forgery_fail_structural_validation():
    logger.debug("test receipt splice entry")
    _, _, _, _, left = _build_csv("red")
    _, _, _, _, right = _build_csv("blue")
    left_external = external_binding(left)
    right_external = external_binding(right)
    spliced_receipt = replace(left_external.receipt, train=right_external.receipt.train)
    spliced = replace(left_external, receipt=spliced_receipt)
    assert not validate_structural_missingness_presentation(spliced)
    forged = replace(left_external, receipt=replace(left_external.receipt, receipt_digest="0" * 64))
    assert not validate_structural_missingness_presentation(forged)
    logger.debug("test receipt splice exit")


def test_callback_objects_are_rejected_before_user_attributes_run():
    logger.debug("test callback preflight entry")
    called = False

    class HostileSchema(RepresentationSchema):
        def __getattribute__(self, name):
            nonlocal called
            called = True
            raise AssertionError(name)

    base, projected, policy = _contract()
    hostile = HostileSchema(base.schema_id, base.fields, base.target_categories)
    with pytest.raises(MissingDataProtocolError, match="^base-schema-type$"):
        missingness_from_csv(
            policy,
            hostile,
            projected,
            train=_csv("train"),
            validation=_csv("validation"),
            test=_csv("test"),
        )
    assert not called
    logger.debug("test callback preflight exit")


def test_nested_receipt_callback_object_is_rejected_without_dispatch():
    logger.debug("test nested callback preflight entry")
    called = False

    class Hostile:
        def __getattribute__(self, name):
            nonlocal called
            called = True
            raise AssertionError(name)

    _, _, _, _, value = _build_csv()
    external = external_binding(value)
    forged = replace(external, receipt=replace(external.receipt, wire_format=Hostile()))  # type: ignore[arg-type]
    assert not validate_structural_missingness_presentation(forged)
    assert not called
    logger.debug("test nested callback preflight exit")


def test_split_and_record_resource_limits_precede_decode():
    logger.debug("test source resources entry")
    base, projected, policy = _contract()
    with pytest.raises(MissingDataProtocolError, match="^train-byte-limit$"):
        missingness_from_csv(
            policy,
            base,
            projected,
            train=b"x" * (16 * 1024 * 1024 + 1),
            validation=_csv("validation"),
            test=_csv("test"),
        )
    huge = b"row_id,source_id,content_id,group_id,label,typed,flag,target\n" + b"x" * (32 * 1024 + 1)
    with pytest.raises(MissingDataProtocolError, match="^physical-record-limit$"):
        missingness_from_csv(policy, base, projected, train=huge, validation=_csv("validation"), test=_csv("test"))
    logger.debug("test source resources exit")


def test_physical_record_limit_precedes_whole_payload_utf8_decode():
    logger.debug("test physical record before decode entry")
    base, projected, policy = _contract()
    overlong_invalid = b"x" * (32 * 1024 + 1) + b"\xff"
    with pytest.raises(MissingDataProtocolError, match="^physical-record-limit$"):
        missingness_from_csv(
            policy,
            base,
            projected,
            train=overlong_invalid,
            validation=_csv("validation"),
            test=_csv("test"),
        )
    logger.debug("test physical record before decode exit")


@pytest.mark.parametrize(
    ("payload", "reason"),
    (
        (b"\xef\xbb\xbf" + _csv("train"), "train-bom"),
        (_csv("train") + b"\x00", "train-nul"),
        (b"\xff", "train-utf8"),
    ),
)
def test_source_encoding_markers_fail_before_parser_dispatch(payload, reason):
    logger.debug("test source encoding preflight entry reason=%s", reason)
    base, projected, policy = _contract()
    with pytest.raises(MissingDataProtocolError, match=rf"^{reason}$"):
        missingness_from_csv(
            policy,
            base,
            projected,
            train=payload,
            validation=_csv("validation"),
            test=_csv("test"),
        )
    logger.debug("test source encoding preflight exit")


@pytest.mark.parametrize(
    ("schema", "reason"),
    (
        (
            RepresentationSchema(
                "resource-fields",
                (RepresentationField("f", "categorical", (0, 1)),) * 1_000_000,
                (0, 1),
            ),
            "base-schema-fields-limit",
        ),
        (
            RepresentationSchema(
                "resource-categories",
                (RepresentationField("f", "categorical", ("x",) * 1_000_000),),
                (0, 1),
            ),
            "base-schema-categories-limit",
        ),
        (
            RepresentationSchema("x" * 1_000_000, (RepresentationField("f", "categorical", (0, 1)),), (0, 1)),
            "base-schema-text-limit",
        ),
        (
            RepresentationSchema(
                "resource-integer",
                (RepresentationField("f", "categorical", (0, 1 << 1_000_000)),),
                (0, 1),
            ),
            "base-schema-category-integer-limit",
        ),
    ),
)
def test_schema_resource_preflight_precedes_copy_and_utf8(monkeypatch, schema, reason):
    logger.debug("test schema resource preflight entry")

    def forbidden_utf8(_value):
        raise AssertionError("UTF-8 encoding ran before shallow resource rejection")

    monkeypatch.setattr(missing_resources, "_utf8_len", forbidden_utf8)
    with pytest.raises(MissingDataProtocolError, match=rf"^{reason}$"):
        projected_schema_for_missing_policy(schema, ())
    logger.debug("test schema resource preflight exit")


def test_hostile_metaclass_name_callback_is_never_observed():
    logger.debug("test hostile metaclass entry")
    called = False

    class HostileMeta(type):
        def __getattribute__(cls, name):
            nonlocal called
            if name == "__name__":
                called = True
                raise AssertionError("dynamic type metadata callback")
            return super().__getattribute__(name)

    class Hostile(metaclass=HostileMeta):
        pass

    with pytest.raises(MissingDataProtocolError, match="^base-schema-type$"):
        projected_schema_for_missing_policy(Hostile(), ())  # type: ignore[arg-type]
    assert not validate_structural_missingness_presentation(Hostile())
    with pytest.raises(MissingDataProtocolError, match="^codec-payload-type$"):
        missingness_presentation_from_json(Hostile())
    assert not called
    logger.debug("test hostile metaclass exit")


def test_combined_policy_node_cap_precedes_all_detachment(monkeypatch):
    logger.debug("test combined policy preflight entry")
    categories = tuple(range(128))
    fields = tuple(RepresentationField(f"f{index}", "categorical", categories) for index in range(32))
    base = RepresentationSchema("resource-combined", fields, (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)

    def forbidden_utf8(_value):
        raise AssertionError("UTF-8 encoding ran before combined node rejection")

    monkeypatch.setattr(missing_resources, "_utf8_len", forbidden_utf8)
    with pytest.raises(MissingDataProtocolError, match="^policy-resource-limit$"):
        canonical_missing_data_policy(base, base, rules)
    logger.debug("test combined policy preflight exit")


def test_typed_category_reordering_cannot_match_projected_policy():
    logger.debug("test typed projected ordering entry")
    base, projected, policy = _contract()
    typed = projected.fields[2]
    reordered = replace(typed, categories=(True, 1, "1"))
    forged_projected = replace(projected, fields=(*projected.fields[:2], reordered, projected.fields[3]))
    assert forged_projected == projected
    with pytest.raises(MissingDataProtocolError, match="^projected-schema-mismatch$"):
        canonical_missing_data_policy(base, forged_projected, policy.rules)
    logger.debug("test typed projected ordering exit")


def test_native_validation_rejects_bool_int_dataclass_equality_forgery():
    logger.debug("test typed native forgery entry")
    base, projected, policy, raws, native = _build_csv()
    train = native.presentation.train
    first = train.rows[0]
    forged_first = replace(first, values=(*first.values[:2], True, *first.values[3:]))
    forged_train = CanonicalPresentation(
        train.schema,
        (forged_first, *train.rows[1:]),
        train.schema_digest,
        train.payload_digest,
        train.boundary,
    )
    forged = replace(native, presentation=replace(native.presentation, train=forged_train))
    assert forged == native
    assert not validate_native_missingness_presentation(
        forged,
        policy,
        base,
        projected,
        wire_format=MissingWireFormat.CSV,
        train=raws[0],
        validation=raws[1],
        test=raws[2],
    )
    logger.debug("test typed native forgery exit")


def test_v1_error_surface_is_exactly_pinned():
    logger.debug("test missing v1 error pins entry")
    error = MissingDataProtocolError("v1-fixed-reason")
    assert type(error) is MissingDataProtocolError
    assert error.reason == "v1-fixed-reason"
    assert str(error) == "v1-fixed-reason"
    assert error.args == ("v1-fixed-reason",)
    base, projected, policy = _contract()
    with pytest.raises(MissingDataProtocolError) as caught:
        missingness_from_csv(
            policy,
            base,
            projected,
            train=b"\xff",
            validation=_csv("validation"),
            test=_csv("test"),
        )
    assert type(caught.value) is MissingDataProtocolError
    assert caught.value.reason == "train-utf8"
    assert caught.value.args == ("train-utf8",)
    logger.debug("test missing v1 error pins exit")


@pytest.mark.parametrize(
    ("mutator", "reason"),
    (
        (lambda row: object.__setattr__(row, "values", (0,) * 33), "wrapper-row-width"),
        (
            lambda row: object.__setattr__(row, "values", ("💥" * 512, *row.values[1:])),
            "wrapper-scalar-text-limit",
        ),
        (
            lambda row: object.__setattr__(row, "values", (1 << 257, *row.values[1:])),
            "wrapper-scalar-integer-limit",
        ),
    ),
)
def test_snapshot_rechecks_row_bounds_after_deterministic_preflight_mutation(monkeypatch, mutator, reason):
    logger.debug("test snapshot boundary recheck entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    row = external.presentation.train.rows[0]
    original_preflight = missing_runtime._safe_structural_shape
    mutated = False

    def mutate_after_preflight(value):
        nonlocal mutated
        valid = original_preflight(value)
        if not mutated:
            mutator(row)
            mutated = True
        return valid

    monkeypatch.setattr(missing_runtime, "_safe_structural_shape", mutate_after_preflight)
    with pytest.raises(MissingDataProtocolError, match=rf"^{reason}$"):
        missing_runtime._snapshot_retained_missingness_presentation(external)
    logger.debug("test snapshot boundary recheck exit")


def test_structural_rule_cap_precedes_nested_rule_traversal(monkeypatch):
    logger.debug("test structural rule shallow cap entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    object.__setattr__(external.policy, "rules", (external.policy.rules[0],) * 1_000_000)

    def forbidden_rule(_value):
        raise AssertionError("nested rule traversal reached before shallow cap")

    monkeypatch.setattr(missing_runtime, "_safe_rule_shape", forbidden_rule)
    assert not missing_runtime._safe_structural_shape(external)
    logger.debug("test structural rule shallow cap exit")


@pytest.mark.parametrize("field", ("boundary", "policy_digest"))
def test_structural_top_text_cap_precedes_nested_schema_traversal(monkeypatch, field):
    logger.debug("test structural top text shallow cap entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    target = external if field == "boundary" else external.policy
    object.__setattr__(target, field, "💥" * 1_000_000)

    def forbidden_schema(_value):
        raise AssertionError("nested schema traversal reached before top text cap")

    monkeypatch.setattr(missing_runtime, "_safe_schema_shape", forbidden_schema)
    assert not missing_runtime._safe_structural_shape(external)
    logger.debug("test structural top text shallow cap exit")


def test_three_way_global_node_cap_precedes_row_scalar_traversal(monkeypatch):
    logger.debug("test three-way shallow node cap entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)
    train = external.presentation.train
    object.__setattr__(train, "rows", (train.rows[0],) * 8192)

    def forbidden_canonical(_value):
        raise AssertionError("nested row traversal reached before global node cap")

    monkeypatch.setattr(missing_runtime, "_safe_canonical_shape", forbidden_canonical)
    assert not missing_runtime._safe_three_way_shape(external.presentation)
    logger.debug("test three-way shallow node cap exit")


def test_combined_policy_and_wrapper_budget_rejects_before_canonical_digest(monkeypatch):
    logger.debug("test combined retained budget entry")
    categories = tuple(range(128))
    fields = tuple(RepresentationField(f"f{index}", "categorical", categories) for index in range(16))
    base = RepresentationSchema("combined-budget-v1", fields, (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)
    projected = projected_schema_for_missing_policy(base, rules)
    policy = canonical_missing_data_policy(base, projected, rules)
    seed_nodes, _ = missing_resources._retained_wrapper_seed(policy, MissingWireFormat.CSV)
    row_charge = 3 * 136 * (16 + 16 * 5 + 16 * 3)
    assert seed_nodes < missing_resources.MAX_WRAPPER_NODES
    assert 1_024 + row_charge < missing_resources.MAX_WRAPPER_NODES
    assert seed_nodes + row_charge > missing_resources.MAX_WRAPPER_NODES

    def wide_csv(prefix):
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("row_id", "source_id", "content_id", "group_id", *(field.name for field in fields), "target"))
        for index in range(136):
            group = "a" if index < 68 else "b"
            target = 0 if group == "a" else 1
            values = tuple(f"i:{(index + offset) % 128}" for offset in range(16))
            writer.writerow(
                (
                    f"{prefix}-r{index}",
                    f"{prefix}-s{index}",
                    f"{prefix}-c{index}",
                    f"{prefix}-{group}",
                    *values,
                    f"i:{target}",
                )
            )
        return output.getvalue().encode("utf-8")

    raws = tuple(wide_csv(name) for name in ("train", "validation", "test"))

    def forbidden_canonical(*_args, **_kwargs):
        raise AssertionError("canonical/digest construction reached before combined budget rejection")

    monkeypatch.setattr(missing_runtime, "canonical_presentation", forbidden_canonical)
    monkeypatch.setattr(missing_runtime, "digest_data", forbidden_canonical)
    with pytest.raises(MissingDataProtocolError, match="^wrapper-node-limit$"):
        missingness_from_csv(
            policy,
            base,
            projected,
            train=raws[0],
            validation=raws[1],
            test=raws[2],
        )
    logger.debug("test combined retained budget exit")


def test_shared_text_ledger_uses_exact_simultaneous_materialization_multiplicity():
    logger.debug("test shared text multiplicity entry")
    fallback = "f" * 512
    base = RepresentationSchema(
        "text-multiplicity-v1",
        (RepresentationField("f", "categorical", (fallback, "observed")),),
        ("allow", "deny"),
    )
    rules = (MissingFieldRule("f", MissingPolicyMode.EXPLICIT_MASK, fallback, "f__present_v1"),)
    projected = projected_schema_for_missing_policy(base, rules)
    policy = canonical_missing_data_policy(base, projected, rules)
    budget = missing_resources.MissingParseBudget(policy, MissingWireFormat.CSV)
    before = budget._text
    budget.charge(("r", "s", "c", "g"), (None,), (fallback, 0), "t", policy.rules)
    assert budget._text - before == 3 + 3 * 2 + 512 * 2 + 2
    before = budget._text
    budget.charge(("r", "s", "c", "g"), ("observed",), ("observed", 1), "t", policy.rules)
    assert budget._text - before == 3 + 3 * 2 + len("observed") * 3 + 2
    logger.debug("test shared text multiplicity exit")


def test_combined_long_text_materializations_reject_before_canonical_digest(monkeypatch):
    logger.debug("test combined long text budget entry")
    feature_values = ("a" * 512, "b" * 512)
    target_values = ("c" * 512, "d" * 512)
    base = RepresentationSchema(
        "combined-text-budget-v1",
        (RepresentationField("f", "categorical", feature_values),),
        target_values,
    )
    rules = (MissingFieldRule("f", MissingPolicyMode.REQUIRED),)
    projected = projected_schema_for_missing_policy(base, rules)
    policy = canonical_missing_data_policy(base, projected, rules)
    seed_nodes, seed_text = missing_resources._retained_wrapper_seed(policy, MissingWireFormat.CSV)
    row_count = 3 * 50
    legacy_row_text = 4 * 512 + 2 * 512 + 2 * 512
    exact_row_text = 3 * 512 + 3 * 2 * 512 + 3 * 512 + 2 * 512
    assert seed_nodes + row_count * (16 + 5 + 3) < missing_resources.MAX_WRAPPER_NODES
    assert seed_text + row_count * legacy_row_text < missing_resources.MAX_NONPAYLOAD_TEXT_BYTES
    assert seed_text + row_count * exact_row_text > missing_resources.MAX_NONPAYLOAD_TEXT_BYTES

    def fixed_text(prefix, index):
        value = f"{prefix}-{index}"
        return value + "x" * (512 - len(value))

    def long_csv(prefix):
        logger.debug("test long CSV fixture entry")
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("row_id", "source_id", "content_id", "group_id", "f", "target"))
        groups = (fixed_text(f"{prefix}-group", 0), fixed_text(f"{prefix}-group", 1))
        for index in range(50):
            group_index = 0 if index < 25 else 1
            writer.writerow(
                (
                    fixed_text(f"{prefix}-row", index),
                    fixed_text(f"{prefix}-source", index),
                    fixed_text(f"{prefix}-content", index),
                    groups[group_index],
                    f"s:{feature_values[index % 2]}",
                    f"s:{target_values[group_index]}",
                )
            )
        result = output.getvalue().encode("utf-8")
        logger.debug("test long CSV fixture exit bytes=%d", len(result))
        return result

    raws = tuple(long_csv(name) for name in ("train", "validation", "test"))

    def forbidden_canonical(*_args, **_kwargs):
        raise AssertionError("canonical/digest construction reached before combined text rejection")

    monkeypatch.setattr(missing_runtime, "canonical_presentation", forbidden_canonical)
    monkeypatch.setattr(missing_runtime, "digest_data", forbidden_canonical)
    with pytest.raises(MissingDataProtocolError, match="^wrapper-text-limit$"):
        missingness_from_csv(
            policy,
            base,
            projected,
            train=raws[0],
            validation=raws[1],
            test=raws[2],
        )
    logger.debug("test combined long text budget exit")


def test_direct_structural_wrapper_uses_combined_policy_and_row_ledger(monkeypatch):
    logger.debug("test direct structural aggregate ledger entry")
    categories = tuple(range(128))
    fields = tuple(RepresentationField(f"f{index}", "categorical", categories) for index in range(16))
    base = RepresentationSchema("direct-combined-budget-v1", fields, (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)
    projected = projected_schema_for_missing_policy(base, rules)
    policy = canonical_missing_data_policy(base, projected, rules)
    seed_nodes, _ = missing_resources._retained_wrapper_seed(policy, MissingWireFormat.CSV)
    row_charge = 3 * 136 * (16 + 16 * 5 + 16 * 3)
    assert seed_nodes + row_charge > missing_resources.MAX_WRAPPER_NODES

    presentations = []
    receipts = []
    for split_name in ("train", "validation", "test"):
        rows = tuple(
            RepresentationRow(
                f"{split_name}-r{index}",
                f"{split_name}-s{index}",
                f"{split_name}-c{index}",
                f"{split_name}-{'a' if index < 68 else 'b'}",
                tuple((index + offset) % 128 for offset in range(16)),
                0 if index < 68 else 1,
            )
            for index in range(136)
        )
        presentation = canonical_presentation(projected, rows)
        parsed = ParsedMissingSplit(rows, tuple({"row": index} for index in range(136)), tuple())
        presentations.append(presentation)
        receipts.append(
            missing_runtime._split_receipt(
                split_name.encode(), parsed, presentation.payload_digest, policy.policy_digest
            )
        )
    three_way = canonical_three_way_presentation(*presentations)
    receipt = missing_runtime._top_receipt(
        MissingWireFormat.CSV,
        MissingReplayAuthority.EXTERNAL_BINDING_ONLY,
        policy,
        tuple(receipts),
        three_way.protocol_digest,
    )
    wrapper = MissingnessPresentation(policy, three_way, receipt)

    assert not validate_structural_missingness_presentation(wrapper)

    def forbidden_validation(*_args, **_kwargs):
        raise AssertionError("canonical validation ran before aggregate ledger rejection")

    monkeypatch.setattr(missing_runtime, "_validate_detached_missingness_presentation", forbidden_validation)
    with pytest.raises(MissingDataProtocolError, match="^wrapper-node-limit$"):
        missingness_presentation_json(wrapper)
    logger.debug("test direct structural aggregate ledger exit")


def test_runtime_debug_logs_do_not_emit_digest_values(caplog):
    logger.debug("test digest-free runtime logs entry")
    caplog.set_level(logging.DEBUG)
    _, _, policy, _, value = _build_csv()
    digests = (
        policy.base_schema_digest,
        policy.projected_schema_digest,
        policy.projection_spec_root,
        policy.policy_digest,
        value.presentation.protocol_digest,
        value.presentation.train.schema_digest,
        value.presentation.train.payload_digest,
        value.presentation.validation.payload_digest,
        value.presentation.test.payload_digest,
        value.receipt.train.raw_digest,
        value.receipt.train.semantic_mask_digest,
        value.receipt.train.projection_digest,
        value.receipt.train.receipt_digest,
        value.receipt.nonclaims_digest,
        value.receipt.receipt_digest,
    )
    messages = tuple(record.getMessage() for record in caplog.records)
    assert all(digest[:12] not in message for digest in digests for message in messages)
    logger.debug("test digest-free runtime logs exit")


def test_codec_list_caps_precede_nested_decoders(monkeypatch):
    logger.debug("test codec shallow list caps entry")
    _, _, _, _, native = _build_csv()
    external = external_binding(native)

    with monkeypatch.context() as patch:
        policy_data = json.loads(missing_codec._canonical_json(missing_codec._policy_data(external.policy)))
        policy_data["rules"] = [policy_data["rules"][0]] * 1_000
        patch.setattr(missing_codec, "_decode_rule", lambda _item: (_ for _ in ()).throw(AssertionError()))
        patch.setattr(missing_codec, "_decode_schema", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-rules-limit$"):
            missing_codec._decode_policy(policy_data)

    with monkeypatch.context() as patch:
        policy_data = json.loads(missing_codec._canonical_json(missing_codec._policy_data(external.policy)))
        schema_data = policy_data["base_schema"]
        schema_data["fields"] = [schema_data["fields"][0]] * 33
        patch.setattr(missing_codec, "_decode_field", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-fields-limit$"):
            missing_codec._decode_schema(schema_data)

    with monkeypatch.context() as patch:
        policy_data = json.loads(missing_codec._canonical_json(missing_codec._policy_data(external.policy)))
        field_data = policy_data["base_schema"]["fields"][0]
        field_data["categories"] = [field_data["categories"][0]] * 129
        patch.setattr(missing_codec, "_decode_scalar", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-categories-limit$"):
            missing_codec._decode_field(field_data)

    with monkeypatch.context() as patch:
        policy_data = json.loads(missing_codec._canonical_json(missing_codec._policy_data(external.policy)))
        schema_data = policy_data["base_schema"]
        schema_data["target_categories"] = [schema_data["target_categories"][0]] * 129
        patch.setattr(missing_codec, "_decode_scalar", lambda _item: (_ for _ in ()).throw(AssertionError()))
        patch.setattr(missing_codec, "_decode_field", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-targets-limit$"):
            missing_codec._decode_schema(schema_data)

    with monkeypatch.context() as patch:
        split_data = json.loads(
            missing_codec._canonical_json(missing_codec._canonical_presentation_data(external.presentation.train))
        )
        split_data["rows"] = [split_data["rows"][0]] * 8_193
        patch.setattr(missing_codec, "_decode_row", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-rows-limit$"):
            missing_codec._decode_canonical_presentation(split_data, external.policy.projected_schema)

    with monkeypatch.context() as patch:
        row_data = json.loads(
            missing_codec._canonical_json(missing_codec._row_data(external.presentation.train.rows[0]))
        )
        row_data["values"] = [row_data["values"][0]] * 33
        patch.setattr(missing_codec, "_decode_scalar", lambda _item: (_ for _ in ()).throw(AssertionError()))
        with pytest.raises(MissingDataProtocolError, match="^codec-row-values-limit$"):
            missing_codec._decode_row(row_data)
    logger.debug("test codec shallow list caps exit")


def test_combined_multibyte_policy_preflight_precedes_detachment_and_encoding(monkeypatch):
    logger.debug("test combined multibyte policy preflight entry")
    categories = tuple(f"{index:03d}-" + "💥" * 60 for index in range(128))
    fields = tuple(RepresentationField(f"f{index}", "categorical", categories) for index in range(24))
    base = RepresentationSchema("multibyte-combined-v1", fields, (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("detachment/encoding ran before combined UTF-8 byte rejection")

    monkeypatch.setattr(missing_resources, "_capture_field", forbidden)
    monkeypatch.setattr(missing_resources, "_utf8_len", forbidden)
    with pytest.raises(MissingDataProtocolError, match="^policy-resource-limit$"):
        canonical_missing_data_policy(base, base, rules)
    logger.debug("test combined multibyte policy preflight exit")


def test_policy_top_text_utf8_preflight_precedes_nested_capture(monkeypatch):
    logger.debug("test policy top text UTF-8 preflight entry")
    _, _, policy = _contract()
    forged = replace(policy, policy_digest="💥" * 512)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("nested policy capture ran before top-text UTF-8 rejection")

    monkeypatch.setattr(missing_resources, "capture_policy_inputs", forbidden)
    with pytest.raises(MissingDataProtocolError, match="^policy-text$"):
        missing_resources.capture_policy(forged)
    logger.debug("test policy top text UTF-8 preflight exit")


def test_external_authority_byte_is_charged_at_exact_text_boundary():
    logger.debug("test external authority text boundary entry")
    _, _, policy, _, native = _build_csv()
    row = native.presentation.train.rows[0]
    native_budget = missing_resources.MissingParseBudget(
        policy,
        MissingWireFormat.CSV,
        authority=MissingReplayAuthority.NATIVE_POLICY_REPLAY,
    )
    external_budget = missing_resources.MissingParseBudget(
        policy,
        MissingWireFormat.CSV,
        authority=MissingReplayAuthority.EXTERNAL_BINDING_ONLY,
    )
    assert external_budget._text == native_budget._text + 1

    probe = missing_resources.MissingParseBudget(policy, MissingWireFormat.CSV)
    before = probe._text
    probe.charge_projected(
        (row.row_id, row.source_id, row.content_id, row.group_id),
        row.values,
        row.target,
        policy.rules,
    )
    row_text = probe._text - before
    native_budget._text = missing_resources.MAX_NONPAYLOAD_TEXT_BYTES - row_text
    external_budget._text = native_budget._text + 1
    native_budget.charge_projected(
        (row.row_id, row.source_id, row.content_id, row.group_id),
        row.values,
        row.target,
        policy.rules,
    )
    assert native_budget._text == missing_resources.MAX_NONPAYLOAD_TEXT_BYTES
    with pytest.raises(MissingDataProtocolError, match="^wrapper-text-limit$"):
        external_budget.charge_projected(
            (row.row_id, row.source_id, row.content_id, row.group_id),
            row.values,
            row.target,
            policy.rules,
        )
    logger.debug("test external authority text boundary exit")


def test_retained_policy_top_fields_join_aggregate_preflight(monkeypatch):
    logger.debug("test retained policy top aggregate entry")
    categories = tuple(f"{index:03d}" + "x" * (253 if index < 48 else 252) for index in range(128))
    fields = tuple(RepresentationField(f"f{index}", "categorical", categories) for index in range(16))
    schema = RepresentationSchema("aggregate-policy-v1", fields, (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)
    top = "💥" * 128
    forged = MissingDataPolicy(top, schema, top, schema, top, rules, top, top)

    schema_parts = missing_resources._schema_parts(schema, "test-policy")
    _, schema_text = missing_resources._preflight_schema_parts(*schema_parts, "test-policy")
    _, rule_text = missing_resources._preflight_rules(rules)
    nested_text = schema_text * 2 + rule_text
    top_text = sum(missing_resources._preflight_utf8_bytes(item) for item in (top,) * 5)
    assert nested_text <= missing_resources.MAX_NONPAYLOAD_TEXT_BYTES
    assert nested_text + top_text > missing_resources.MAX_NONPAYLOAD_TEXT_BYTES

    def forbidden_capture(*_args, **_kwargs):
        raise AssertionError("policy detachment ran before complete aggregate rejection")

    monkeypatch.setattr(missing_resources, "capture_schema", forbidden_capture)
    with pytest.raises(MissingDataProtocolError, match="^policy-resource-limit$"):
        missing_resources.capture_policy(forged)
    logger.debug("test retained policy top aggregate exit")


def test_policy_constructor_reserves_generated_top_overhead(monkeypatch):
    logger.debug("test generated policy overhead entry")
    fields = []
    for field_index in range(16):
        size = 256 if field_index < 12 else 255
        categories = tuple(f"{index:03d}" + "x" * (size - 3) for index in range(128))
        fields.append(RepresentationField(f"f{field_index}", "categorical", categories))
    base = RepresentationSchema("generated-aggregate-v1", tuple(fields), (0, 1))
    rules = tuple(MissingFieldRule(field.name, MissingPolicyMode.REQUIRED) for field in fields)
    projected = projected_schema_for_missing_policy(base, rules)

    base_parts = missing_resources._schema_parts(base, "test-base")
    projected_parts = missing_resources._schema_parts(projected, "test-projected")
    _, base_text = missing_resources._preflight_schema_parts(*base_parts, "test-base")
    _, projected_text = missing_resources._preflight_schema_parts(*projected_parts, "test-projected")
    _, rule_text = missing_resources._preflight_rules(rules)
    _, generated_text = missing_resources.generated_policy_overhead()
    nested_text = base_text + projected_text + rule_text
    assert nested_text <= missing_resources.MAX_NONPAYLOAD_TEXT_BYTES
    assert nested_text + generated_text > missing_resources.MAX_NONPAYLOAD_TEXT_BYTES

    def forbidden_capture(*_args, **_kwargs):
        raise AssertionError("policy detachment ran before generated-overhead rejection")

    monkeypatch.setattr(missing_resources, "capture_schema", forbidden_capture)
    with pytest.raises(MissingDataProtocolError, match="^policy-resource-limit$"):
        canonical_missing_data_policy(base, projected, rules)
    logger.debug("test generated policy overhead exit")


def test_external_binding_recharges_downgraded_authority_before_return(monkeypatch):
    logger.debug("test external binding authority recharge entry")
    _, _, _, _, native = _build_csv()
    authorities = []
    original = missing_runtime.precharge_retained_wrapper

    def boundary_charge(policy, presentation, wire_format, authority):
        logger.debug("test external binding boundary charge authority=%s", authority.value)
        authorities.append(authority)
        if authority is MissingReplayAuthority.EXTERNAL_BINDING_ONLY:
            raise MissingDataProtocolError("wrapper-text-limit")
        return original(policy, presentation, wire_format, authority)

    monkeypatch.setattr(missing_runtime, "precharge_retained_wrapper", boundary_charge)
    with pytest.raises(MissingDataProtocolError, match="^wrapper-text-limit$"):
        external_binding(native)
    assert authorities == [
        MissingReplayAuthority.NATIVE_POLICY_REPLAY,
        MissingReplayAuthority.EXTERNAL_BINDING_ONLY,
    ]
    logger.debug("test external binding authority recharge exit")
