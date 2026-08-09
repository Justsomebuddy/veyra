"""Fail-closed and source-binding pressure for provisional P1-A morphisms."""

from dataclasses import replace
import logging

import pytest

import src.core.observer_morphism as morphism
from src.core.observer_core_kernel import crest_observer, tail_observer
from src.core.observer_core_types import Input, LeafKind, Mark, MarkValue, Pair, PairKind, PairValue
from src.core.observer_morphism import (
    compose_observer_morphisms,
    observer_morphism_judgment,
    observer_source_binding,
    p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_runtime import translate_response
from src.core.observer_morphism_types import ObserverSourceBinding, ProjectionStep
from src.core.observer_morphism_validation import (
    ObserverMorphismValidationError,
    membership_digest,
    snapshot_source_binding,
    snapshot_translation,
    translation_digest,
)
from src.core.positive_ontology import internal_observer
from src.core.positive_ontology_doctrine import observer_doctrine

logger = logging.getLogger(__name__)


class NameTrapMeta(type):
    """Forbid class-name inspection before exact gates."""

    def __getattribute__(cls, name):
        if name == "__name__":
            raise AssertionError("hostile metaclass name accessed")
        return super().__getattribute__(name)


class NameTrap(metaclass=NameTrapMeta):
    """Untrusted exact-gate input."""


class EqualityTrap:
    """Forbid equality before an exact scalar gate."""

    def __eq__(self, other):
        raise AssertionError("hostile equality called")


def _fixture():
    logger.debug("_fixture adversarial entry")
    doctrine = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        doctrine, "attack-source",
        ("coarse-crest", "fine-total", "fine-domain-hole", "fine-nested"),
    )
    row = observer_morphism_judgment(
        doctrine, binding, "attack-valid", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert row.translation is not None
    logger.debug("_fixture adversarial exit")
    return doctrine, binding, row.translation


def test_exact_gates_reject_callables_subclasses_and_hostile_metaclasses():
    logger.debug("test_exact_gate_attacks entry")
    doctrine, binding, _ = _fixture()
    with pytest.raises(ObserverMorphismValidationError):
        observer_source_binding(NameTrap(), "x", ())  # type: ignore[arg-type]
    with pytest.raises(ObserverMorphismValidationError):
        observer_source_binding(lambda: doctrine, "x", ())  # type: ignore[arg-type]
    with pytest.raises(ObserverMorphismValidationError, match="projection"):
        observer_morphism_judgment(
            doctrine, binding, "bad-projection", "fine-total", "coarse-crest",
            [ProjectionStep.LEFT],  # type: ignore[arg-type]
        )
    class TupleSubclass(tuple):
        pass
    with pytest.raises(ObserverMorphismValidationError, match="projection"):
        observer_morphism_judgment(
            doctrine, binding, "tuple-subclass", "fine-total", "coarse-crest",
            TupleSubclass((ProjectionStep.LEFT,)),  # type: ignore[arg-type]
        )
    logger.debug("test_exact_gate_attacks exit")


def test_source_member_limit_runs_before_hostile_element_snapshot():
    logger.debug("test_source_member_limit entry")
    doctrine = p1a_observer_morphism_doctrine()
    hostile = (NameTrap(),) * (len(doctrine.observers) + 1)
    with pytest.raises(ObserverMorphismValidationError, match="member-limit"):
        observer_source_binding(doctrine, "bounded", hostile)  # type: ignore[arg-type]
    logger.debug("test_source_member_limit exit")


def test_unconfirmed_comparison_domain_cannot_certify_vacuously(monkeypatch):
    logger.debug("test_unconfirmed_comparison entry")
    doctrine, binding, _ = _fixture()
    def unavailable(*args):
        logger.debug("unavailable comparison entry")
        logger.debug("unavailable comparison exit result=False")
        return False
    monkeypatch.setattr(morphism, "_comparison_is_nonempty", unavailable)
    row = observer_morphism_judgment(
        doctrine, binding, "unconfirmed-c", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert not row.comparison_domain.confirmed_nonempty
    assert not row.information_factorizes_on_comparison
    assert row.translation is None and not row.witness_checked
    assert row.status.value == "incomparable"
    assert row.obstruction == "comparison-domain-unconfirmed"
    logger.debug("test_unconfirmed_comparison exit")


def test_failed_comparison_witness_has_its_own_obstruction(monkeypatch):
    logger.debug("test_failed_comparison_witness entry")
    doctrine, binding, _ = _fixture()
    def failed_witness(*args):
        logger.debug("failed_witness entry")
        logger.debug("failed_witness exit result=False")
        return False
    monkeypatch.setattr(morphism, "_check_comparison_witness", failed_witness)
    row = observer_morphism_judgment(
        doctrine, binding, "failed-witness", "fine-total", "coarse-crest",
        (ProjectionStep.LEFT,),
    )
    assert row.comparison_domain.confirmed_nonempty
    assert not row.information_factorizes_on_comparison
    assert row.translation is not None and not row.witness_checked
    assert row.status.value == "incomparable"
    assert row.obstruction == "comparison-witness-failed"
    logger.debug("test_failed_comparison_witness exit")


def test_binding_and_translation_scalar_traps_fail_before_equality():
    logger.debug("test_scalar_traps entry")
    doctrine, binding, translation = _fixture()
    for forged in (
        replace(binding, doctrine_fingerprint=EqualityTrap()),
        replace(binding, scope=EqualityTrap()),
        replace(binding, membership_digest=EqualityTrap()),
    ):
        with pytest.raises(ObserverMorphismValidationError):
            snapshot_source_binding(forged, doctrine)
    hostile_digests = tuple(
        EqualityTrap() if index == 0 else digest
        for index, digest in enumerate(binding.observer_digests)
    )
    with pytest.raises(ObserverMorphismValidationError, match="observer-digest"):
        snapshot_source_binding(replace(binding, observer_digests=hostile_digests), doctrine)
    with pytest.raises(ObserverMorphismValidationError):
        snapshot_translation(replace(translation, source_binding_digest=EqualityTrap()), doctrine, binding)
    logger.debug("test_scalar_traps exit")


def test_response_translation_rejects_cycles_resources_and_wrong_exact_kind():
    logger.debug("test_response_attacks entry")
    doctrine, binding, translation = _fixture()
    cycle = PairValue(MarkValue(Mark.SILENT), MarkValue(Mark.SILENT))
    object.__setattr__(cycle, "left", cycle)
    with pytest.raises(ObserverMorphismValidationError, match="invalid-translation-response"):
        translate_response(doctrine, binding, translation, cycle)
    value = MarkValue(Mark.SILENT)
    for _ in range(130):
        value = PairValue(value, value)  # type: ignore[assignment]
    with pytest.raises(ObserverMorphismValidationError, match="invalid-translation-response"):
        translate_response(doctrine, binding, translation, value)
    with pytest.raises(ObserverMorphismValidationError, match="fine-response-kind"):
        translate_response(doctrine, binding, translation, MarkValue(Mark.SILENT))
    logger.debug("test_response_attacks exit")


def test_kind_sentinel_tamper_doctrine_drift_and_projection_overflow_fail_closed():
    logger.debug("test_kind_doctrine_projection_attacks entry")
    doctrine, binding, translation = _fixture()
    malformed = replace(
        translation,
        fine_kind=PairKind(("pair-close",), LeafKind.RECURRENCE),  # type: ignore[arg-type]
    )
    with pytest.raises(ObserverMorphismValidationError, match="response-kind"):
        snapshot_translation(malformed, doctrine, binding)
    with pytest.raises(ObserverMorphismValidationError, match="doctrine"):
        observer_morphism_judgment(
            replace(doctrine, fingerprint="0" * 64), binding, "drift", "fine-total",
            "coarse-crest", (ProjectionStep.LEFT,),
        )
    with pytest.raises(ObserverMorphismValidationError, match="projection"):
        observer_morphism_judgment(
            doctrine, binding, "overflow", "fine-total", "coarse-crest",
            (ProjectionStep.LEFT,) * 129,
        )
    logger.debug("test_kind_doctrine_projection_attacks exit")


def test_composition_rejects_wrong_middle_and_wrong_source_binding():
    logger.debug("test_composition_binding entry")
    doctrine, binding, first = _fixture()
    identity = observer_morphism_judgment(
        doctrine, binding, "fine-identity", "fine-total", "fine-total", ()
    )
    assert identity.translation is not None
    with pytest.raises(ObserverMorphismValidationError, match="middle-mismatch"):
        compose_observer_morphisms(
            doctrine, binding, "bad-middle", first, identity.translation
        )
    other = observer_source_binding(
        doctrine, "other-source", ("coarse-crest", "fine-total")
    )
    with pytest.raises(ObserverMorphismValidationError, match="binding"):
        compose_observer_morphisms(
            doctrine, other, "wrong-binding", first, first
        )
    logger.debug("test_composition_binding exit")


def test_digest_valid_but_structurally_false_translation_is_rejected():
    logger.debug("test_structurally_false_translation entry")
    doctrine, binding, translation = _fixture()
    projection = (ProjectionStep.RIGHT,)
    digest = translation_digest(
        translation.translation_id, doctrine.fingerprint, binding.membership_digest,
        translation.fine_observer_id, translation.coarse_observer_id, projection,
        translation.fine_kind, translation.coarse_kind,
    )
    forged = replace(translation, projection=projection, translation_digest=digest)
    with pytest.raises(ObserverMorphismValidationError, match="does-not-factorize"):
        snapshot_translation(forged, doctrine, binding)
    logger.debug("test_structurally_false_translation exit")


def test_doctrine_snapshot_is_immune_to_later_source_ast_mutation():
    logger.debug("test_doctrine_toctou entry")
    source = Pair(crest_observer(), Input())
    doctrine = observer_doctrine(
        "p1a-toctou", "closed-r11-pair-projection", ("source-fixed",),
        (
            internal_observer("coarse", crest_observer()),
            internal_observer("fine", source),
        ),
        version="p1a-v1",
    )
    object.__setattr__(source, "left", tail_observer())
    binding = observer_source_binding(doctrine, "toctou-source", ("coarse", "fine"))
    row = observer_morphism_judgment(
        doctrine, binding, "toctou", "fine", "coarse", (ProjectionStep.LEFT,)
    )
    assert row.information_factorizes_on_comparison
    logger.debug("test_doctrine_toctou exit")


def test_length_prefixed_membership_digest_has_no_token_boundary_collision():
    logger.debug("test_length_prefix_digest entry")
    digests = ("d" * 64, "e" * 64)
    left = membership_digest("same", "f" * 64, ("a", "bc"), digests)
    right = membership_digest("same", "f" * 64, ("ab", "c"), digests)
    assert left != right
    logger.debug("test_length_prefix_digest exit")


def test_empty_binding_and_forged_exact_subclass_never_certify():
    logger.debug("test_empty_binding_subclass entry")
    doctrine = p1a_observer_morphism_doctrine()
    with pytest.raises(ObserverMorphismValidationError, match="members"):
        observer_source_binding(doctrine, "empty", ())
    class BindingSubclass(ObserverSourceBinding):
        pass
    valid = observer_source_binding(doctrine, "valid", ("coarse-crest",))
    forged = BindingSubclass(**valid.__dict__)
    with pytest.raises(ObserverMorphismValidationError, match="exact"):
        snapshot_source_binding(forged, doctrine)
    logger.debug("test_empty_binding_subclass exit")
