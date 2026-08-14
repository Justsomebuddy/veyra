"""Adversarial reconstruction and boundary tests for RFC 169 transport v2."""

from __future__ import annotations

from dataclasses import fields, replace
import logging

import pytest

from src.core.observer_core_codec import decode_observer
from src.core.observer_core_kernel import crest_observer, tail_observer
from src.core.observer_core_semantics import observe
from src.core.observer_core_types import Input, Pair
from src.core.observer_morphism import (
    observer_morphism_judgment,
    observer_source_binding,
)
from src.core.observer_morphism_types import MorphismStatus, ProjectionStep
from src.core.observer_realization_types import ObservationStatus
from src.core.observer_realization import realize_observer_doctrine_r16
from src.core.p1a_realization_transport_v2 import (
    P1AEndpointPartitionLawV2,
    P1AObservationCommutingRowV2,
    P1AObservationPayloadV2,
    P1AObservationTransportV2,
    P1ARealizationTransportReceiptV2,
    P1ARealizationTransportValidationError,
    compose_p1a_realization_transport_v2,
    identity_p1a_realization_transport_v2,
    p1a_realization_transport_v2,
    verify_p1a_realization_transport_v2,
)
from src.core.p1a_realization_transport_v2.digest import (
    judgment_root,
    partition_digest,
    payload_digest,
    receipt_digest,
    row_digest,
    transport_digest,
)
from src.core.p1a_realization_transport_v2.observation import (
    P1AObservationUndefined,
    transport_observation,
)
import src.core.p1a_realization_transport_v2.runtime as p1a_runtime
import src.core.p1a_realization_transport_v2.validation as p1a_validation
from src.core.p1a_realization_transport_v2.validation import (
    MAX_P1A_V2_PAYLOAD_BYTES,
    MAX_P1A_V2_ROWS,
)
from src.core.positive_ontology import internal_observer
from src.core.positive_ontology_doctrine import observer_doctrine
from src.core.proof_core_types import Silence
from src.core.realization_transport import realization_context_morphism

from p1a_realization_transport_v2_fixture import (
    P1ATransportCase,
    fixed_p1a_case,
    realization_context,
    transport_case,
)


logger = logging.getLogger(__name__)

_READY_SPEC = {
    "transport_id": "adversarial-transport",
    "p1a_morphism_id": "adversarial-p1a",
    "fine_observer_id": "fine-total",
    "coarse_observer_id": "coarse-crest",
    "projection": (ProjectionStep.LEFT,),
}
_SIX_PAYLOAD_FIELDS = (
    "source_fine",
    "source_transported",
    "source_coarse",
    "target_fine",
    "target_transported",
    "target_coarse",
)


def _build(case: P1ATransportCase, **spec):
    """Build through the frozen public entry point."""
    logger.debug("adversarial build helper entry transport=%s", spec["transport_id"])
    result = p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        **spec,
    )
    logger.debug("adversarial build helper exit rows=%d", len(result.rows))
    return result


def _verify(case: P1ATransportCase, receipt, **spec):
    """Verify through authoritative reconstruction from raw endpoint inputs."""
    logger.debug("adversarial verify helper entry transport=%s", spec["transport_id"])
    result = verify_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.target,
        case.source_witness,
        case.target_witness,
        case.context_transport,
        receipt,
        **spec,
    )
    logger.debug("adversarial verify helper exit rows=%d", len(result.rows))
    return result


def _resign_row(row, **changes):
    """Apply row changes and recompute the public domain-separated digest."""
    logger.debug("resign row helper entry source=%d", row.source_index)
    provisional = replace(row, **changes, row_digest="0" * 64)
    result = replace(provisional, row_digest=row_digest(provisional))
    logger.debug("resign row helper exit digest=%s", result.row_digest[:12])
    return result


def _resign_partition(law, **changes):
    """Apply partition changes and recompute its domain-separated digest."""
    logger.debug("resign partition helper entry endpoint=%s", law.endpoint.value)
    provisional = replace(law, **changes, partition_digest="0" * 64)
    result = replace(provisional, partition_digest=partition_digest(provisional))
    logger.debug("resign partition helper exit digest=%s", result.partition_digest[:12])
    return result


def _resign_transport(transport, **changes):
    """Apply transport-root changes and recompute the transport digest."""
    logger.debug("resign transport helper entry transport=%s", transport.transport_id)
    provisional = replace(transport, **changes, transport_digest="0" * 64)
    result = replace(provisional, transport_digest=transport_digest(provisional))
    logger.debug("resign transport helper exit digest=%s", result.transport_digest[:12])
    return result


def _resign_receipt(receipt, **changes):
    """Apply receipt changes and recompute the outer receipt digest."""
    logger.debug("resign receipt helper entry rows=%d", len(receipt.rows))
    provisional = replace(receipt, **changes, receipt_digest="0" * 64)
    digest = receipt_digest(
        provisional.schema,
        provisional.transport,
        provisional.rows,
        provisional.source_partition_law,
        provisional.target_partition_law,
        provisional.scope,
    )
    result = replace(provisional, receipt_digest=digest)
    logger.debug("resign receipt helper exit digest=%s", result.receipt_digest[:12])
    return result


def _subclass_copy(value):
    """Copy a DTO into an otherwise field-identical hostile subclass."""
    logger.debug("subclass copy helper entry type=%s", type(value).__name__)
    subtype = type(f"Hostile{type(value).__name__}", (type(value),), {})
    result = subtype(*(getattr(value, field.name) for field in fields(value)))
    logger.debug("subclass copy helper exit type=%s", type(result).__name__)
    return result


def _dropped_branch_doctrine():
    """Build a custom five-member doctrine whose fine domain has a right hole."""
    logger.debug("dropped branch doctrine helper entry")
    crest = crest_observer()
    tail = tail_observer()
    result = observer_doctrine(
        "P1A-v2-dropped-branch-pressure",
        "closed-r11-pair-projection",
        (
            "source-fixed",
            "membership-not-chronology",
            "dropped-branch-pressure",
            "no-object-promotion",
        ),
        (
            internal_observer("coarse", crest),
            internal_observer("fine", Pair(crest, tail)),
            internal_observer("input", Input()),
            internal_observer("tail", tail),
            internal_observer("pair", Pair(Input(), crest)),
        ),
        version="p1a-v2-dropped-branch-test-v1",
    )
    logger.debug("dropped branch doctrine helper exit observers=%d", len(result.observers))
    return result


def _blocked_composition_doctrine():
    """Build a three-level observer chain with a nested Blocked left branch."""
    logger.debug("blocked composition doctrine helper entry")
    tail = tail_observer()
    middle = Pair(tail, tail)
    fine = Pair(middle, Input())
    result = observer_doctrine(
        "P1A-v2-blocked-composition-pressure",
        "closed-r11-pair-projection",
        (
            "source-fixed",
            "membership-not-chronology",
            "blocked-associativity-pressure",
            "no-category-promotion",
        ),
        (
            internal_observer("coarse-tail", tail),
            internal_observer("middle-tail-pair", middle),
            internal_observer("fine-nested-tail", fine),
            internal_observer("input", Input()),
            internal_observer("crest", crest_observer()),
        ),
        version="p1a-v2-blocked-composition-test-v1",
    )
    logger.debug(
        "blocked composition doctrine helper exit observers=%d",
        len(result.observers),
    )
    return result


@pytest.mark.parametrize(
    ("fine", "coarse", "projection", "status"),
    (
        (
            "fine-domain-hole",
            "coarse-crest",
            (ProjectionStep.LEFT,),
            MorphismStatus.INFORMATION_ONLY,
        ),
        (
            "fine-total",
            "coarse-crest",
            (ProjectionStep.RIGHT,),
            MorphismStatus.INCOMPARABLE,
        ),
    ),
)
def test_non_strong_structural_judgments_are_never_upgraded_by_finite_rows(
    fine,
    coarse,
    projection,
    status,
):
    """Ready samples cannot promote INFORMATION_ONLY or INCOMPARABLE to STRONG."""
    logger.debug("non-strong rejection test entry expected=%s", status.value)
    case = fixed_p1a_case(
        name=f"non-strong-{status.value}",
        source_depths=(2, 3),
        target_depths=(2, 3),
        graph=(0, 1),
    )
    judgment = observer_morphism_judgment(
        case.doctrine,
        case.binding,
        "non-strong-judgment",
        fine,
        coarse,
        projection,
    )
    assert judgment.status is status

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-strong-judgment-required",
    ):
        _build(
            case,
            transport_id="non-strong-transport",
            p1a_morphism_id="non-strong-judgment",
            fine_observer_id=fine,
            coarse_observer_id=coarse,
            projection=projection,
        )
    logger.debug("non-strong rejection test exit expected=%s", status.value)


def test_dropped_branch_only_blocked_observation_is_undefined_directly():
    """A Blocked outcome wholly outside the selected branch has no transport."""
    logger.debug("direct dropped branch test entry")
    doctrine = _dropped_branch_doctrine()
    binding = observer_source_binding(
        doctrine,
        "direct-dropped-branch-binding",
        tuple(member.observer_id for member in doctrine.observers),
    )
    judgment = observer_morphism_judgment(
        doctrine,
        binding,
        "direct-dropped-branch",
        "fine",
        "coarse",
        (ProjectionStep.LEFT,),
    )
    members = {member.observer_id: member for member in doctrine.observers}
    blocked = observe(decode_observer(members["fine"].canonical), Silence())

    assert judgment.status is MorphismStatus.INFORMATION_ONLY
    assert judgment.translation is not None
    assert type(blocked).__name__ == "Blocked"
    with pytest.raises(P1AObservationUndefined, match="p1a-observation-undefined"):
        transport_observation(doctrine, binding, judgment.translation, blocked)
    logger.debug("direct dropped branch test exit")


def test_builder_fails_closed_if_upstream_forges_dropped_branch_as_strong(monkeypatch):
    """Even a forged STRONG judgment cannot convert branchless Blocked to Ready."""
    logger.debug("builder dropped branch test entry")
    doctrine = _dropped_branch_doctrine()
    binding = observer_source_binding(
        doctrine,
        "builder-dropped-branch-binding",
        tuple(member.observer_id for member in doctrine.observers),
    )
    case = transport_case(
        doctrine,
        binding,
        name="builder-dropped-branch",
        source_depths=(0, 1),
        target_depths=(0, 1),
        graph=(0, 1),
    )
    actual = observer_morphism_judgment(
        doctrine,
        binding,
        "builder-dropped-branch-p1a",
        "fine",
        "coarse",
        (ProjectionStep.LEFT,),
    )
    forged = replace(
        actual,
        coarse_domain_in_fine_domain=True,
        status=MorphismStatus.STRONG,
        obstruction="",
    )
    monkeypatch.setattr(p1a_runtime, "observer_morphism_judgment", lambda *_: forged)

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-observation-undefined",
    ):
        _build(
            case,
            transport_id="builder-dropped-branch-transport",
            p1a_morphism_id="builder-dropped-branch-p1a",
            fine_observer_id="fine",
            coarse_observer_id="coarse",
            projection=(ProjectionStep.LEFT,),
        )
    logger.debug("builder dropped branch test exit")


def test_nested_blocked_composition_is_associative_by_fresh_reconstruction():
    """Both bracketings rebuild the same two-step Blocked projection evidence."""
    logger.debug("blocked composition associativity test entry")
    doctrine = _blocked_composition_doctrine()
    binding = observer_source_binding(
        doctrine,
        "blocked-composition-binding",
        tuple(member.observer_id for member in doctrine.observers),
    )
    contexts = tuple(realization_context(doctrine, f"blocked-composition-{index}", (0, 1)) for index in range(4))
    witnesses = tuple(realize_observer_doctrine_r16(doctrine, context) for context in contexts)
    v1_edges = tuple(
        realization_context_morphism(
            doctrine,
            contexts[index],
            contexts[index + 1],
            f"blocked-composition-context-{index}",
            (0, 1),
            witnesses[index],
            witnesses[index + 1],
        )
        for index in range(3)
    )
    observer_edges = (
        ("fine-nested-tail", "middle-tail-pair", (ProjectionStep.LEFT,)),
        ("middle-tail-pair", "coarse-tail", (ProjectionStep.LEFT,)),
        ("coarse-tail", "coarse-tail", ()),
    )
    edges = tuple(
        p1a_realization_transport_v2(
            doctrine,
            binding,
            contexts[index],
            contexts[index + 1],
            witnesses[index],
            witnesses[index + 1],
            v1_edges[index],
            transport_id=f"blocked-composition-transport-{index}",
            p1a_morphism_id=f"blocked-composition-p1a-{index}",
            fine_observer_id=observer_edges[index][0],
            coarse_observer_id=observer_edges[index][1],
            projection=observer_edges[index][2],
        )
        for index in range(3)
    )
    left_pair = compose_p1a_realization_transport_v2(
        doctrine,
        binding,
        contexts[0],
        contexts[1],
        contexts[2],
        witnesses[0],
        witnesses[1],
        witnesses[2],
        edges[0],
        edges[1],
        transport_id="blocked-composition-left-pair",
        p1a_morphism_id="blocked-composition-left-pair-p1a",
        context_morphism_id="blocked-composition-left-pair-context",
    )
    left = compose_p1a_realization_transport_v2(
        doctrine,
        binding,
        contexts[0],
        contexts[2],
        contexts[3],
        witnesses[0],
        witnesses[2],
        witnesses[3],
        left_pair,
        edges[2],
        transport_id="blocked-composition-final",
        p1a_morphism_id="blocked-composition-final-p1a",
        context_morphism_id="blocked-composition-final-context",
    )
    right_pair = compose_p1a_realization_transport_v2(
        doctrine,
        binding,
        contexts[1],
        contexts[2],
        contexts[3],
        witnesses[1],
        witnesses[2],
        witnesses[3],
        edges[1],
        edges[2],
        transport_id="blocked-composition-right-pair",
        p1a_morphism_id="blocked-composition-right-pair-p1a",
        context_morphism_id="blocked-composition-right-pair-context",
    )
    right = compose_p1a_realization_transport_v2(
        doctrine,
        binding,
        contexts[0],
        contexts[1],
        contexts[3],
        witnesses[0],
        witnesses[1],
        witnesses[3],
        edges[0],
        right_pair,
        transport_id="blocked-composition-final",
        p1a_morphism_id="blocked-composition-final-p1a",
        context_morphism_id="blocked-composition-final-context",
    )

    assert left == right
    assert left.transport.translation.projection == (
        ProjectionStep.LEFT,
        ProjectionStep.LEFT,
    )
    blocked = left.rows[0]
    assert blocked.law.value == "blocked-commutes-exact"
    assert blocked.source_transported == blocked.source_coarse
    assert blocked.target_transported == blocked.target_coarse
    assert b'"pair-left","pair-left","apply-tail"' in (blocked.source_fine.canonical_payload)
    assert blocked.source_coarse.canonical_payload == (
        b'{"obstructions":[{"code":"tail-of-silence","path":["apply-tail"]}],"tag":"blocked"}'
    )
    logger.debug("blocked composition associativity test exit")


@pytest.mark.parametrize(
    "dto_field",
    ("receipt", "transport", "row", "payload", "source_partition", "target_partition"),
)
def test_all_public_dto_subclasses_are_rejected(dto_field):
    """Every receipt-tree DTO is exact-type gated rather than isinstance-gated."""
    logger.debug("DTO subclass rejection test entry field=%s", dto_field)
    case = fixed_p1a_case(name=f"dto-subclass-{dto_field}")
    receipt = _build(case, **_READY_SPEC)
    if dto_field == "receipt":
        forged = _subclass_copy(receipt)
    elif dto_field == "transport":
        forged = replace(receipt, transport=_subclass_copy(receipt.transport))
    elif dto_field == "row":
        forged = replace(
            receipt,
            rows=(_subclass_copy(receipt.rows[0]), *receipt.rows[1:]),
        )
    elif dto_field == "payload":
        hostile = _subclass_copy(receipt.rows[0].source_fine)
        forged_row = replace(receipt.rows[0], source_fine=hostile)
        forged = replace(receipt, rows=(forged_row, *receipt.rows[1:]))
    elif dto_field == "source_partition":
        forged = replace(
            receipt,
            source_partition_law=_subclass_copy(receipt.source_partition_law),
        )
    else:
        forged = replace(
            receipt,
            target_partition_law=_subclass_copy(receipt.target_partition_law),
        )

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("DTO subclass rejection test exit field=%s", dto_field)


def test_exact_precharge_never_invokes_hostile_tuple_or_equality_callbacks():
    """Exact gates reject attacker objects without running Python hooks."""
    logger.debug("hostile callback trap test entry")

    class HostileTuple(tuple):
        def __len__(self):
            raise AssertionError("hostile __len__ executed")

        def __iter__(self):
            raise AssertionError("hostile __iter__ executed")

        def __getitem__(self, key):
            raise AssertionError("hostile __getitem__ executed")

    class HostileBytes:
        def __eq__(self, other):
            raise AssertionError("hostile __eq__ executed")

        def __bytes__(self):
            raise AssertionError("hostile __bytes__ executed")

    case = fixed_p1a_case(name="hostile-callback-traps")
    receipt = _build(case, **_READY_SPEC)
    with pytest.raises(P1ARealizationTransportValidationError, match="invalid-p1a-rows"):
        _verify(case, replace(receipt, rows=HostileTuple(receipt.rows)), **_READY_SPEC)

    hostile_payload = replace(
        receipt.rows[0].source_fine,
        canonical_payload=HostileBytes(),
    )
    hostile_row = replace(receipt.rows[0], source_fine=hostile_payload)
    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-payload-must-be-exact",
    ):
        _verify(
            case,
            replace(receipt, rows=(hostile_row, *receipt.rows[1:])),
            **_READY_SPEC,
        )
    logger.debug("hostile callback trap test exit")


def test_judgment_root_is_sensitive_to_one_field_only_change():
    """Changing only the morphism identifier changes the semantic root."""
    logger.debug("judgment root sensitivity test entry")
    case = fixed_p1a_case(name="judgment-root-sensitivity")
    judgment = observer_morphism_judgment(
        case.doctrine,
        case.binding,
        "judgment-root-original",
        "fine-total",
        "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    mutated = replace(judgment, morphism_id="judgment-root-mutated")
    differing = tuple(
        field.name for field in fields(judgment) if getattr(judgment, field.name) != getattr(mutated, field.name)
    )
    assert differing == ("morphism_id",)
    assert judgment_root(judgment) != judgment_root(mutated)
    logger.debug("judgment root sensitivity test exit")


@pytest.mark.parametrize(
    "raw",
    (
        b'{"tag":"ready"}',
        b'{"tag":"ready","value":null}',
        b'{"obstructions":[],"tag":"blocked"}',
        b'{"obstructions":[{"code":"unknown","path":[]}],"tag":"blocked"}',
    ),
)
def test_malformed_canonical_payload_schema_is_rejected_before_reconstruction(raw):
    """Canonical JSON and a matching tag are insufficient without outcome schema."""
    logger.debug("malformed payload schema test entry bytes=%d", len(raw))
    case = fixed_p1a_case(name="malformed-payload-schema")
    receipt = _build(case, **_READY_SPEC)
    status = ObservationStatus.BLOCKED if b'"blocked"' in raw else ObservationStatus.READY
    malformed = P1AObservationPayloadV2(status, raw, payload_digest(raw))
    law = (
        receipt.rows[0].law
        if status is ObservationStatus.READY
        else receipt.rows[0].law.__class__.BLOCKED_COMMUTES_EXACT
    )
    replacements = {field: malformed for field in _SIX_PAYLOAD_FIELDS}
    forged_row = _resign_row(receipt.rows[0], **replacements, law=law)
    forged = _resign_receipt(receipt, rows=(forged_row, *receipt.rows[1:]))

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("malformed payload schema test exit")


@pytest.mark.parametrize("payload_field", _SIX_PAYLOAD_FIELDS)
def test_resigned_splice_of_each_of_six_payload_vertices_is_rejected(payload_field):
    """Digest-correct payload splices cannot survive authoritative reconstruction."""
    logger.debug("six-payload splice test entry field=%s", payload_field)
    case = fixed_p1a_case(name=f"payload-splice-{payload_field}")
    receipt = _build(case, **_READY_SPEC)
    original = receipt.rows[0]
    replacement_payload = getattr(receipt.rows[1], payload_field)
    assert replacement_payload != getattr(original, payload_field)
    forged_row = _resign_row(original, **{payload_field: replacement_payload})
    forged = _resign_receipt(
        receipt,
        rows=(forged_row, *receipt.rows[1:]),
    )

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("six-payload splice test exit field=%s", payload_field)


def test_resigned_strong_judgment_root_forgery_is_rejected():
    """A syntactically valid replacement root remains bound to fresh semantics."""
    logger.debug("judgment-root forgery test entry")
    case = fixed_p1a_case(name="judgment-root-forgery")
    receipt = _build(case, **_READY_SPEC)
    forged_transport = _resign_transport(
        receipt.transport,
        strong_judgment_root="0" * 64,
    )
    forged = _resign_receipt(receipt, transport=forged_transport)

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("judgment-root forgery test exit")


def test_resigned_row_commitment_forgery_is_rejected():
    """A row digest cannot authorize a commitment copied from another state."""
    logger.debug("row commitment forgery test entry")
    case = fixed_p1a_case(name="row-commitment-forgery")
    receipt = _build(case, **_READY_SPEC)
    forged_row = _resign_row(
        receipt.rows[0],
        source_input_commitment=receipt.rows[1].source_input_commitment,
    )
    forged = _resign_receipt(receipt, rows=(forged_row, *receipt.rows[1:]))

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("row commitment forgery test exit")


def test_resigned_valid_partition_splice_is_rejected():
    """A valid law from another P1-A construction is not valid for this receipt."""
    logger.debug("partition splice test entry")
    case = fixed_p1a_case(name="partition-splice")
    receipt = _build(case, **_READY_SPEC)
    identity = identity_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.source,
        case.source_witness,
        observer_id="fine-total",
        transport_id="partition-splice-identity-transport",
        p1a_morphism_id="partition-splice-identity-p1a",
        context_morphism_id="partition-splice-identity-context",
    )
    replacement_law = _resign_partition(
        identity.source_partition_law,
        endpoint=receipt.source_partition_law.endpoint,
    )
    assert replacement_law != receipt.source_partition_law
    forged = _resign_receipt(receipt, source_partition_law=replacement_law)

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("partition splice test exit")


def test_resigned_row_order_forgery_is_rejected_before_reconstruction():
    """The receipt digest does not weaken canonical source-index ordering."""
    logger.debug("row order forgery test entry")
    case = fixed_p1a_case(name="row-order-forgery")
    receipt = _build(case, **_READY_SPEC)
    forged = _resign_receipt(receipt, rows=tuple(reversed(receipt.rows)))

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-row-order-or-type-drift",
    ):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("row order forgery test exit")


def test_resigned_v1_receipt_and_context_morphism_splice_is_rejected():
    """A self-consistent v1 receipt from other endpoints cannot be transplanted."""
    logger.debug("v1 receipt splice test entry")
    case = fixed_p1a_case(name="v1-splice-primary")
    alternate = transport_case(
        case.doctrine,
        case.binding,
        name="v1-splice-alternate",
        source_depths=(1, 2),
        target_depths=(2, 1),
        graph=(1, 0),
    )
    receipt = _build(case, **_READY_SPEC)
    forged_transport = _resign_transport(
        receipt.transport,
        context_morphism_digest=alternate.context_transport.morphism.morphism_digest,
        v1_receipt_digest=alternate.context_transport.receipt_digest,
    )
    forged = _resign_receipt(
        receipt,
        transport=forged_transport,
        context_transport=alternate.context_transport,
    )

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("v1 receipt splice test exit")


def test_composition_closes_resigned_short_target_partition_child():
    """A short child carrier rejects cleanly before graph-index pullback."""
    logger.debug("short target partition composition test entry")
    case = fixed_p1a_case(name="short-target-partition-child")
    first = _build(case, **_READY_SPEC)
    short_target = P1AEndpointPartitionLawV2(
        first.target_partition_law.endpoint,
        (0,),
        (0,),
        (0,),
        (0,),
        "0" * 64,
    )
    short_target = _resign_partition(short_target)
    forged_first = _resign_receipt(first, target_partition_law=short_target)
    second = identity_p1a_realization_transport_v2(
        case.doctrine,
        case.binding,
        case.target,
        case.target_witness,
        observer_id="coarse-crest",
        transport_id="short-target-second-transport",
        p1a_morphism_id="short-target-second-p1a",
        context_morphism_id="short-target-second-context",
    )

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-target-partition-carrier-drift",
    ):
        compose_p1a_realization_transport_v2(
            case.doctrine,
            case.binding,
            case.source,
            case.target,
            case.target,
            case.source_witness,
            case.target_witness,
            case.target_witness,
            forged_first,
            second,
            transport_id="short-target-composed-transport",
            p1a_morphism_id="short-target-composed-p1a",
            context_morphism_id="short-target-composed-context",
        )
    logger.debug("short target partition composition test exit")


def test_receipt_from_different_endpoints_is_rejected_under_original_inputs():
    """Endpoint roots, rows, and partitions remain bound to the raw verify inputs."""
    logger.debug("endpoint splice test entry")
    case = fixed_p1a_case(name="endpoint-splice-primary")
    alternate = transport_case(
        case.doctrine,
        case.binding,
        name="endpoint-splice-alternate",
        source_depths=(3, 2, 1),
        target_depths=(1, 2, 3),
        graph=(2, 1, 0),
    )
    alternate_receipt = _build(alternate, **_READY_SPEC)

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, alternate_receipt, **_READY_SPEC)
    logger.debug("endpoint splice test exit")


@pytest.mark.parametrize(
    "wrong_spec",
    (
        {**_READY_SPEC, "transport_id": "wrong-transport-id"},
        {**_READY_SPEC, "p1a_morphism_id": "wrong-p1a-id"},
        {
            **_READY_SPEC,
            "fine_observer_id": "coarse-crest",
            "projection": (),
        },
        {**_READY_SPEC, "projection": (ProjectionStep.RIGHT,)},
    ),
)
def test_verifier_rejects_wrong_raw_spec(wrong_spec):
    """Verification reconstructs from the caller's exact spec, never the receipt."""
    logger.debug("wrong raw spec test entry")
    case = fixed_p1a_case(name="wrong-raw-spec")
    receipt = _build(case, **_READY_SPEC)

    with pytest.raises(P1ARealizationTransportValidationError):
        _verify(case, receipt, **wrong_spec)
    logger.debug("wrong raw spec test exit")


def test_transport_identifier_byte_cap_is_enforced():
    """The practical 128-byte identifier cap is enforced on constructed output."""
    logger.debug("identifier cap test entry")
    case = fixed_p1a_case(name="identifier-cap")
    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="invalid-p1a-transport-id",
    ):
        _build(case, **{**_READY_SPEC, "transport_id": "x" * 129})
    logger.debug("identifier cap test exit")


def test_receipt_row_count_cap_is_enforced_before_row_walk():
    """An outer digest cannot authorize more than the bounded source-row cap."""
    logger.debug("row count cap test entry")
    case = fixed_p1a_case(name="row-count-cap")
    receipt = _build(case, **_READY_SPEC)
    oversized_rows = (receipt.rows[0],) * (MAX_P1A_V2_ROWS + 1)
    forged = _resign_receipt(receipt, rows=oversized_rows)

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="invalid-p1a-rows",
    ):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("row count cap test exit")


def test_individual_payload_byte_cap_is_enforced_before_json_decode():
    """One canonical-looking envelope cannot exceed the fixed payload byte cap."""
    logger.debug("payload cap test entry")
    case = fixed_p1a_case(name="payload-cap")
    receipt = _build(case, **_READY_SPEC)
    prefix = b'{"tag":"ready","x":"'
    suffix = b'"}'
    filler = b"x" * (MAX_P1A_V2_PAYLOAD_BYTES + 1 - len(prefix) - len(suffix))
    raw = prefix + filler + suffix
    assert len(raw) == MAX_P1A_V2_PAYLOAD_BYTES + 1
    oversized = P1AObservationPayloadV2(
        ObservationStatus.READY,
        raw,
        payload_digest(raw),
    )
    forged_row = _resign_row(receipt.rows[0], source_fine=oversized)
    forged = _resign_receipt(receipt, rows=(forged_row, *receipt.rows[1:]))

    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-payload-byte-limit",
    ):
        _verify(case, forged, **_READY_SPEC)
    logger.debug("payload cap test exit")


def test_projection_step_cap_is_normalized_to_public_error():
    """An overlong structural path fails at the bounded P1-A public boundary."""
    logger.debug("projection cap test entry")
    case = fixed_p1a_case(name="projection-cap")
    with pytest.raises(P1ARealizationTransportValidationError):
        _build(
            case,
            **{**_READY_SPEC, "projection": (ProjectionStep.LEFT,) * 129},
        )
    logger.debug("projection cap test exit")


@pytest.mark.parametrize(
    ("cap_name", "reason"),
    (
        ("MAX_P1A_V2_SIX_STREAM_BYTES", "p1a-six-stream-byte-limit"),
        ("MAX_P1A_V2_RECEIPT_NODES", "p1a-receipt-node-limit"),
        ("MAX_P1A_V2_RECEIPT_TEXT_BYTES", "p1a-receipt-text-limit"),
    ),
)
def test_aggregate_snapshot_caps_are_enforced_after_exact_precharge(
    monkeypatch,
    cap_name,
    reason,
):
    """Aggregate caps are independently enforced on an otherwise valid receipt."""
    logger.debug("aggregate cap test entry cap=%s", cap_name)
    case = fixed_p1a_case(name=f"aggregate-cap-{cap_name.lower()}")
    receipt = _build(case, **_READY_SPEC)
    monkeypatch.setattr(p1a_validation, cap_name, 0)
    with pytest.raises(P1ARealizationTransportValidationError, match=reason):
        _verify(case, receipt, **_READY_SPEC)
    logger.debug("aggregate cap test exit cap=%s", cap_name)


def test_per_endpoint_transported_byte_cap_is_enforced(monkeypatch):
    """Fresh transport accumulation is bounded independently at each endpoint."""
    logger.debug("per-endpoint cap test entry")
    case = fixed_p1a_case(name="per-endpoint-cap")
    monkeypatch.setattr(p1a_runtime, "MAX_P1A_V2_TRANSPORTED_ENDPOINT_BYTES", 0)
    with pytest.raises(
        P1ARealizationTransportValidationError,
        match="p1a-transported-endpoint-byte-limit",
    ):
        _build(case, **_READY_SPEC)
    logger.debug("per-endpoint cap test exit")


def test_valid_transport_logs_never_emit_payloads_or_full_digests(caplog):
    """Operational diagnostics reveal counts and prefixes, not receipt evidence."""
    logger.debug("log redaction test entry")
    case = fixed_p1a_case(name="log-redaction")
    with caplog.at_level(logging.DEBUG, logger="src.core.p1a_realization_transport_v2"):
        receipt = _build(case, **_READY_SPEC)
        assert _verify(case, receipt, **_READY_SPEC) == receipt

    emitted = "\n".join(record.getMessage() for record in caplog.records)
    secrets = {
        payload.canonical_payload.decode("ascii")
        for row in receipt.rows
        for payload in (
            row.source_fine,
            row.source_transported,
            row.source_coarse,
            row.target_fine,
            row.target_transported,
            row.target_coarse,
        )
    }
    full_digests = {
        receipt.receipt_digest,
        receipt.transport.transport_digest,
        *(row.row_digest for row in receipt.rows),
        *(
            payload.payload_digest
            for row in receipt.rows
            for payload in (
                row.source_fine,
                row.source_transported,
                row.source_coarse,
                row.target_fine,
                row.target_transported,
                row.target_coarse,
            )
        ),
    }
    assert all(secret not in emitted for secret in secrets)
    assert all(digest not in emitted for digest in full_digests)
    logger.debug("log redaction test exit")
