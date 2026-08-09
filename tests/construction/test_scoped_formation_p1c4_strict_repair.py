"""Exploit regressions for the strict P1-C4 repair."""

from dataclasses import replace

import pytest

from src.core.confluence import direct_echo_transport
from src.core.confluence_aggregate import (
    declared_history, finite_confluence_catalog, global_path_pair_requirement,
)
from src.core.confluence_types import AlignmentPoint
from src.core.observer_relation_preflight import request_cost, snapshot_request
from src.core.observer_relation_types import LawStatus
from src.core.observer_relations import relation_resource_policy
from src.core.observer_core_kernel import tail_observer
from src.core.observer_core_semantics import observe
from src.core.observer_core_semantics import echo as native_echo
from src.core.scoped_formation_g4 import _derived_blocks, _response_row
from src.core.scoped_formation_types import G4ResponseRow
from src.core.scoped_formation import (
    RequiredConfluenceLevel, ScopedFormationStatus,
    ScopedFormationValidationError, formation_refinement_requirement,
    formation_persistence_requirement, formation_scope, scoped_formation_judgment,
    validate_scoped_formation_result,
)
from src.core.scoped_formation_observers import require_observer_at_stage
from src.core.scoped_formation_preflight import snapshot_formation_request
from src.core.translated_confluence_preflight import snapshot_translated_request
from src.core.proof_core_types import Silence

from scoped_formation_fixture import scoped_formation_fixture


def _scope_with(rule, scope, **changes):
    values = dict(
        c2_catalog=scope.c2_catalog,
        required_confluence=scope.required_confluence,
        support_observer_ids=scope.support_observer_ids,
        persistence=scope.persistence, g4_bridge=scope.g4_bridge,
        refinements=scope.refinements, policy=scope.policy,
    )
    values.update(changes)
    return formation_scope(
        rule, scope.scope_id, scope.presentation_id, scope.doctrine,
        scope.construction_source, scope.target, scope.diagram,
        values["c2_catalog"], values["required_confluence"],
        values["support_observer_ids"], values["persistence"],
        values["g4_bridge"], values["refinements"], values["policy"],
    )


def test_information_only_raw_p1a_is_open_and_never_positive():
    rule, scope = scoped_formation_fixture(variant="information-only")
    result = scoped_formation_judgment(rule, scope)
    rows = tuple(x for x in result.component_rows if x.component == "a2-refinement")
    assert rows and all(x.status is ScopedFormationStatus.OPEN for x in rows)
    assert all(x.obstruction == "p1a-morphism-not-strong" for x in rows)
    assert result.status is ScopedFormationStatus.OPEN
    assert result.presentation is None


def test_actual_runtime_refuted_wins_over_earlier_open(monkeypatch):
    rule, scope = scoped_formation_fixture(include_translated=False)
    old = scope.refinements[0]
    bad = formation_refinement_requirement(
        old.requirement_id, old.a2_doctrine, old.a2_observer_source,
        old.a2_stage_source, old.relation_scope, old.morphism,
        required_class=old.required_class,
        required_preservation=old.required_preservation,
        required_reflection=LawStatus.ESTABLISHED,
        required_domain_equality=old.required_domain_equality,
        required_translation=old.required_translation,
        required_loss=old.required_loss, path_ids=old.path_ids,
        survival_mode=old.survival_mode,
        direct_observer_id=old.direct_observer_id,
        direct_bridge=old.direct_bridge, relation_policy=old.relation_policy,
    )
    changed = _scope_with(rule, scope, refinements=(bad,))
    blocked = observe(tail_observer(), Silence())
    monkeypatch.setattr(
        "src.core.scoped_formation_components.observe", lambda *_: blocked,
    )
    result = scoped_formation_judgment(rule, changed)
    support = next(x for x in result.component_rows if x.component == "support")
    a2 = next(x for x in result.component_rows if x.component == "a2-refinement")
    assert support.status is ScopedFormationStatus.OPEN
    assert a2.status is ScopedFormationStatus.REFUTED
    assert result.status is ScopedFormationStatus.REFUTED
    assert result.first_obstruction == a2.obstruction


def test_local_confluence_does_not_promote_failed_declared_global_paths():
    rule, scope = scoped_formation_fixture(include_translated=False)
    doctrine, diagram = scope.doctrine, scope.diagram
    left = declared_history(doctrine, diagram, "hostile-left", "full-left")
    right = declared_history(doctrine, diagram, "hostile-right", "full-right")
    global_ = global_path_pair_requirement(
        doctrine, diagram, "hostile-global", left, right,
        (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2)),
        direct_echo_transport(doctrine, ("diagram-fine",)),
    )
    catalog = finite_confluence_catalog(
        doctrine, diagram, scope.c2_catalog.local_requirements, (global_,),
        scope.c2_catalog.policy,
    )
    local = scoped_formation_judgment(rule, _scope_with(
        rule, scope, c2_catalog=catalog,
        required_confluence=RequiredConfluenceLevel.LOCAL_FINITE,
    ))
    global_result = scoped_formation_judgment(rule, _scope_with(
        rule, scope, c2_catalog=catalog,
        required_confluence=RequiredConfluenceLevel.GLOBAL_DECLARED_FINITE,
    ))
    local_row = next(x for x in local.component_rows if x.component == "c2-confluence")
    global_row = next(x for x in global_result.component_rows if x.component == "c2-confluence")
    assert local_row.status is ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
    assert global_row.status is ScopedFormationStatus.REFUTED


def test_direct_and_translated_joint_bridge_mismatches_are_rejected():
    _, scope = scoped_formation_fixture()
    direct, translated = scope.refinements
    _, other = scoped_formation_fixture(variant="equivalent")
    with pytest.raises(ScopedFormationValidationError):
        formation_refinement_requirement(
            "bad-direct", direct.a2_doctrine, direct.a2_observer_source,
            direct.a2_stage_source, direct.relation_scope, direct.morphism,
            required_class=direct.required_class,
            required_preservation=direct.required_preservation,
            required_reflection=direct.required_reflection,
            required_domain_equality=direct.required_domain_equality,
            required_loss=direct.required_loss, path_ids=direct.path_ids,
            survival_mode=direct.survival_mode,
            direct_observer_id=direct.direct_observer_id,
            direct_bridge=other.refinements[0].direct_bridge,
            relation_policy=direct.relation_policy,
        )
    alien_policy = relation_resource_policy(
        max_cost=1024, max_encoded_bytes=900_000,
    )
    mismatch = formation_refinement_requirement(
        translated.requirement_id, translated.a2_doctrine,
        translated.a2_observer_source, translated.a2_stage_source,
        translated.relation_scope, translated.morphism,
        required_class=translated.required_class,
        required_preservation=translated.required_preservation,
        required_reflection=translated.required_reflection,
        required_domain_equality=translated.required_domain_equality,
        required_loss=translated.required_loss, path_ids=translated.path_ids,
        survival_mode=translated.survival_mode,
        translated_plan=translated.translated_plan,
        translated_bridge=translated.translated_bridge,
        translated_spec=translated.translated_spec,
        translated_policy=translated.translated_policy,
        relation_policy=alien_policy,
    )
    rule, _ = scoped_formation_fixture()
    with pytest.raises(ScopedFormationValidationError):
        _scope_with(rule, scope, refinements=(direct, mismatch))


def test_translated_runtime_charges_both_real_a2_replays():
    direct_rule, direct_scope = scoped_formation_fixture(include_translated=False)
    full_rule, full_scope = scoped_formation_fixture()
    direct_request = snapshot_formation_request(direct_rule, direct_scope)
    full_request = snapshot_formation_request(full_rule, full_scope)
    requirement = full_scope.refinements[1]
    a2 = snapshot_request(
        requirement.a2_doctrine, requirement.a2_observer_source,
        requirement.a2_stage_source, requirement.relation_scope,
        requirement.morphism, None, requirement.relation_policy,
    )[1]
    c3 = snapshot_translated_request(
        full_scope.doctrine, full_scope.diagram, requirement.translated_plan,
        requirement.a2_doctrine, requirement.a2_observer_source,
        requirement.a2_stage_source, requirement.translated_bridge,
        requirement.translated_spec, requirement.translated_policy,
    )
    assert full_request.checks - direct_request.checks == request_cost(a2) + c3.required_checks
    assert c3.a2_required_checks > 0


def test_prefix_edge_and_huge_integer_attacks_are_typed_rejections():
    rule, scope = scoped_formation_fixture()
    missing = replace(
        scope.target,
        observers=tuple(x for x in scope.target.observers if x.observer_id != "diagram-fine"),
    )
    with pytest.raises(ScopedFormationValidationError):
        require_observer_at_stage(scope.doctrine, missing, "diagram-fine", "test")
    bad_persistence = formation_persistence_requirement("diagram-fine", "rb")
    with pytest.raises(ScopedFormationValidationError):
        _scope_with(rule, scope, persistence=(bad_persistence,) + scope.persistence[1:])
    huge_policy = replace(scope.policy, max_checks=10 ** 10_000)
    with pytest.raises(ScopedFormationValidationError):
        _scope_with(rule, scope, policy=huge_policy)
    result = scoped_formation_judgment(rule, scope)
    with pytest.raises(ScopedFormationValidationError):
        validate_scoped_formation_result(
            rule, scope, replace(result, charged_checks=10 ** 10_000),
        )


def test_g4_domain_blocked_uses_canonical_left_right_keys_and_is_open():
    """A valid DomainBlocked is epistemic silence, never a KeyError or split."""
    outcome = native_echo(tail_observer(), Silence(), Silence())
    row = _response_row("patch", "observer", "left", "right", outcome)
    assert row.status is ScopedFormationStatus.OPEN
    assert row.outcome == "blocked"
    assert len(row.left_payload_digest) == len(row.right_payload_digest) == 64


def test_g4_echo_echo_blocked_triangle_stays_open_not_refuted(monkeypatch):
    """Unknown pairs do not become positive inequality in the local partition."""
    rule, scope = scoped_formation_fixture(include_translated=False)
    original = native_echo
    calls = 0

    def selective(observer, left, right):
        nonlocal calls
        calls += 1
        if calls in {5, 6}:
            return original(tail_observer(), Silence(), Silence())
        return original(observer, left, right)

    monkeypatch.setattr("src.core.scoped_formation_g4.echo", selective)
    result = scoped_formation_judgment(rule, scope)
    assert result.g4.status is ScopedFormationStatus.OPEN
    assert result.g4.contradiction_rows == ()
    assert result.status is ScopedFormationStatus.OPEN
    assert result.presentation is None


def test_derived_triangle_echo_echo_blocked_never_invents_split():
    """The exact ECHO/ECHO/BLOCKED triangle closes provisionally, not as inequality."""
    established = ScopedFormationStatus.ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE
    digest = "0" * 64
    rows = [
        G4ResponseRow("triangle", "o", "a", "b", established, "echo", digest, digest, digest),
        G4ResponseRow("triangle", "o", "a", "c", ScopedFormationStatus.OPEN, "blocked", digest, digest, digest),
        G4ResponseRow("triangle", "o", "b", "c", established, "echo", digest, digest, digest),
    ]
    assert _derived_blocks(("a", "b", "c"), rows, ("o",)) == (("a", "b", "c"),)


def test_five_result_transplants_reject_before_encoding_or_observation(monkeypatch):
    """Source, target, G4, catalog, and presentation transplants fail shallowly."""
    rule, scope = scoped_formation_fixture()
    result = scoped_formation_judgment(rule, scope)
    assert result.presentation is not None
    altered_sources = ("0" * 64,) + result.source_digests[1:]
    g4_doctrine = replace(result.g4, doctrine_fingerprint="0" * 64)
    g4_catalog = replace(
        result.g4, expected_response_keys=result.g4.expected_response_keys[::-1],
    )
    presentation = replace(result.presentation, presentation_id="transplanted")
    probes = (
        replace(result, source_digests=altered_sources),
        replace(result, target_commitment="0" * 64),
        replace(result, g4=g4_doctrine),
        replace(result, g4=g4_catalog),
        replace(result, presentation=presentation),
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("semantic replay or result encoding occurred")

    monkeypatch.setattr("src.core.scoped_formation_components.observe", forbidden)
    monkeypatch.setattr("src.core.scoped_formation_g4.echo", forbidden)
    monkeypatch.setattr("src.core.scoped_formation_result_validation.canonical_bytes", forbidden)
    for probe in probes:
        with pytest.raises(ScopedFormationValidationError):
            validate_scoped_formation_result(rule, scope, probe)
