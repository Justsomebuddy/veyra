from dataclasses import replace
import json

import pytest

from src.core.intrinsic_mode_bridge import intrinsic_mode_bridge_report
from src.core.proof_core_codec import canonical_json
from src.core.proof_core_resonance import intrinsic_resonance_theorem
from src.core.proof_core_types import Equal, Silence
from src.core.proof_elaboration_artifact import (
    elaboration_artifact_json, make_surface_elaboration_artifact,
    verify_elaboration_artifact,
)
from src.core.proof_elaboration_lean_render import render_elaboration_lean
from src.core.proof_surface_codec import surface_program_data
from src.core.proof_surface_elaborator import compile_surface_program

pytestmark = pytest.mark.requires_lean


SOURCE = b"""(veyra-proof 1
  (claim (forall item recurrence
    (resonates (var item) (var item))))
  (proof (forall-intro item recurrence
    (resonance-intro (var item) (var item) (pulse (silence))
      (native-law weave-unit-right (var item))))))"""


def artifact(source=SOURCE):
    elaborated = compile_surface_program(source.decode("ascii"))
    return make_surface_elaboration_artifact("THM-R7-004", source, elaborated), elaborated


def test_surface_artifact_reproduces_exact_r7_proof_and_binds_r9():
    item, elaborated = artifact()
    canonical = intrinsic_resonance_theorem()
    report = intrinsic_mode_bridge_report()
    assert item.r7_artifact_digest == canonical.artifact.proof_digest
    assert item.semantic_digest == elaborated.semantic_digest
    assert item.surface_syntax_digest == elaborated.syntax_digest
    assert item.rule_closure == tuple(rule.value for rule in canonical.rule_closure)
    assert item.native_law_closure == tuple(law.value for law in canonical.native_law_closure)
    assert item.r9_binding_digest == report.binding_digest
    assert item.r9_source_digests == report.source_digests
    assert verify_elaboration_artifact(
        item, SOURCE, surface_program_data(elaborated.surface),
        elaborated.claim, elaborated.proof,
    ).ok


def test_artifact_serialization_is_canonical_and_deterministic():
    first, _ = artifact()
    second, _ = artifact()
    assert first == second
    rendered = elaboration_artifact_json(first)
    assert rendered == canonical_json(json.loads(rendered))
    assert first.binding_digest in rendered
    assert first.source_digest in rendered


def test_generated_lean_binds_proof_image_semantics_and_structural_support():
    item, elaborated = artifact()
    rendered = render_elaboration_lean(item, SOURCE, elaborated)
    assert rendered == render_elaboration_lean(item, SOURCE, elaborated)
    assert "THM_R10_003_elaborated_proof_accepted" in rendered
    assert "THM_R10_004_elaborated_image_sound" in rendered
    assert "THM_R10_005_structural_support_matches" in rendered
    assert item.source_digest in rendered
    assert item.r9_binding_digest in rendered
    assert "foreignModeObstruction" in rendered  # cataloged but absent from support


def test_whitespace_changes_source_binding_but_not_syntax_or_semantics():
    spaced = SOURCE.replace(b"(claim", b"\n   (claim", 1)
    first, _ = artifact(SOURCE)
    second, _ = artifact(spaced)
    assert first.source_digest != second.source_digest
    assert first.source_size != second.source_size
    assert first.surface_syntax_digest == second.surface_syntax_digest
    assert first.semantic_digest == second.semantic_digest
    assert first.r7_artifact_digest == second.r7_artifact_digest


def test_alpha_renaming_changes_surface_syntax_but_not_elaborated_semantics():
    renamed = SOURCE.replace(b"item", b"r")
    first, _ = artifact(SOURCE)
    second, _ = artifact(renamed)
    assert first.surface_syntax_digest != second.surface_syntax_digest
    assert first.semantic_digest == second.semantic_digest
    assert first.r7_artifact_digest == second.r7_artifact_digest


@pytest.mark.parametrize(
    "field,value",
    (
        ("source_digest", "0" * 64),
        ("canonical_surface_ast", "{}"),
        ("semantic_digest", "0" * 64),
        ("r7_artifact_digest", "0" * 64),
        ("dependency_support", ()),
        ("r9_binding_digest", "0" * 64),
        ("toolchain", "forged"),
        ("binding_digest", "0" * 64),
    ),
)
def test_any_composite_binding_mutation_is_rejected(field, value):
    item, elaborated = artifact()
    forged = replace(item, **{field: value})
    result = verify_elaboration_artifact(
        forged, SOURCE, surface_program_data(elaborated.surface),
        elaborated.claim, elaborated.proof,
    )
    assert not result.ok
    assert result.errors == ("elaboration-artifact-replay-mismatch",)


def test_source_ast_statement_and_r9_report_drift_fail_closed():
    item, elaborated = artifact()
    assert not verify_elaboration_artifact(
        item, SOURCE + b" ", surface_program_data(elaborated.surface),
        elaborated.claim, elaborated.proof,
    ).ok
    changed_ast = {**surface_program_data(elaborated.surface), "version": 99}
    assert not verify_elaboration_artifact(
        item, SOURCE, changed_ast, elaborated.claim, elaborated.proof,
    ).ok
    assert not verify_elaboration_artifact(
        item, SOURCE, surface_program_data(elaborated.surface),
        Equal(Silence(), Silence()), elaborated.proof,
    ).ok
    report = intrinsic_mode_bridge_report()
    forged_report = replace(report, binding_digest="0" * 64)
    with pytest.raises(ValueError, match="elaboration-r9-bridge-rejected"):
        make_surface_elaboration_artifact(
            "THM-R7-004", SOURCE, elaborated, r9_report=forged_report,
        )


def test_surface_origin_replay_rejects_mismatched_program_and_non_ascii():
    _, elaborated = artifact()
    changed = SOURCE.replace(b"item", b"r")
    with pytest.raises(ValueError, match="surface-elaboration-replay-mismatch"):
        make_surface_elaboration_artifact("THM-R7-004", changed, elaborated)
    with pytest.raises(ValueError, match="elaboration-source-not-ascii"):
        make_surface_elaboration_artifact("THM-R7-004", SOURCE + b"\xff", elaborated)
