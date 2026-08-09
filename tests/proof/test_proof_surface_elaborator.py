from dataclasses import replace

import pytest

from src.core.proof_core_types import (
    Bound, Equal, Forall, Implies, NativeLawId, Resonates, RuleId,
)
from src.core.proof_core_resonance import intrinsic_resonance_proof, intrinsic_resonance_statement
from src.core.proof_surface_codec import canonical_surface_json, surface_syntax_digest
from src.core.proof_surface_elaborator import compile_surface_program, elaborate_surface_program
from src.core.proof_surface_parser import parse_surface_program
from src.core.proof_surface_types import (
    ElaborationLimits, SourceLimits, SurfaceLanguageError, SURFACE_LANGUAGE_ID,
)


def source(claim: str, proof: str) -> str:
    return f"(veyra-proof 1 (claim {claim}) (proof {proof}))"


P = "(equal (silence) (silence))"
R7_CLAIM = "(forall r recurrence (resonates (var r) (var r)))"
R7_PROOF = """(forall-intro r recurrence
  (resonance-intro (var r) (var r) (pulse (silence))
    (native-law weave-unit-right (var r))))"""


def test_surface_reproduces_r7_reflexive_resonance_without_name_dispatch():
    result = compile_surface_program(source(R7_CLAIM, R7_PROOF))
    assert result.surface.language_id == SURFACE_LANGUAGE_ID
    assert result.claim == Forall(
        result.claim.binder_type,
        Resonates(Bound(0), Bound(0)),
    )
    assert result.judgment.conclusion == result.claim
    assert result.judgment.rule_closure == (
        RuleId.FORALL_INTRO,
        RuleId.NATIVE_LAW,
        RuleId.RESONANCE_INTRO,
    )
    assert result.judgment.native_law_closure == (NativeLawId.WEAVE_UNIT_RIGHT,)
    assert result.artifact.theorem_id == SURFACE_LANGUAGE_ID
    assert result.claim == intrinsic_resonance_statement()
    assert result.proof == intrinsic_resonance_proof()
    named = f"(veyra-proof 1 (theorem THM-R7-004) (claim {R7_CLAIM}) (proof {R7_PROOF}))"
    with pytest.raises(SurfaceLanguageError, match="veyra-proof-bad-arity"):
        compile_surface_program(named)


def test_alpha_renaming_and_whitespace_preserve_semantics_but_not_raw_source():
    first = source(R7_CLAIM, R7_PROOF)
    renamed = source(
        "(forall recurrence_value recurrence (resonates (var recurrence_value) (var recurrence_value)))",
        """(forall-intro witness recurrence
          (resonance-intro (var witness) (var witness) (pulse (silence))
            (native-law weave-unit-right (var witness))))""",
    )
    spaced = "\n \t" + first.replace("(", " ( ").replace(")", " ) ") + "\n"
    a, b, c = map(compile_surface_program, (first, renamed, spaced))
    assert a.semantic_digest == b.semantic_digest == c.semantic_digest
    assert a.syntax_digest != b.syntax_digest
    assert a.syntax_digest == c.syntax_digest
    assert a.source_digest != b.source_digest
    assert a.source_digest != c.source_digest


def test_typed_ast_codec_is_deterministic_and_span_independent():
    compact = parse_surface_program(source(P, "(eq-refl (silence))"))
    spaced = parse_surface_program("  " + source(P, "(eq-refl (silence))").replace("(", " ( ").replace(")", " ) "))
    assert canonical_surface_json(compact) == canonical_surface_json(spaced)
    assert surface_syntax_digest(compact) == surface_syntax_digest(spaced)


def test_overlapping_names_resolve_capture_safely_to_de_bruijn_indices():
    claim = """(forall x recurrence
      (forall xy recurrence
        (implies (equal (var x) (var xy)) (equal (var x) (var xy)))))"""
    proof = """(forall-intro x recurrence
      (forall-intro xy recurrence
        (imp-intro h (equal (var x) (var xy)) (assume h))))"""
    result = compile_surface_program(source(claim, proof))
    outer = result.claim
    assert type(outer) is Forall and type(outer.body) is Forall
    implication = outer.body.body
    expected = Equal(Bound(1), Bound(0))
    assert implication == Implies(expected, expected)


def test_every_r7_rule_constructor_is_reachable_from_source_syntax():
    rows = (
        source(f"(implies {P} {P})", f"(imp-intro h {P} (assume h))"),
        source(P, f"(imp-elim (imp-intro h {P} (assume h)) (eq-refl (silence)))"),
        source(P, "(forall-elim (forall-intro x recurrence (eq-refl (var x))) (silence))"),
        source(
            "(equal (silence) (stitch (silence) (silence)))",
            "(eq-sym (native-law stitch-silence-left (silence)))",
        ),
        source(
            "(equal (stitch (silence) (silence)) (stitch (silence) (silence)))",
            """(eq-trans
              (native-law stitch-silence-left (silence))
              (eq-sym (native-law stitch-silence-left (silence))))""",
        ),
        source(R7_CLAIM, R7_PROOF),
    )
    reached = {rule for row in rows for rule in compile_surface_program(row).judgment.rule_closure}
    assert reached == set(RuleId)


@pytest.mark.parametrize(
    ("law", "claim", "args"),
    (
        ("stitch-silence-left", "(equal (stitch (silence) (silence)) (silence))", "(silence)"),
        ("stitch-silence-right", "(equal (stitch (silence) (silence)) (silence))", "(silence)"),
        (
            "weave-silence-right",
            "(equal (weave (pulse (silence)) (silence)) (silence))",
            "(pulse (silence))",
        ),
        (
            "weave-pulse",
            "(equal (weave (silence) (pulse (silence))) (stitch (silence) (weave (silence) (silence))))",
            "(silence) (silence)",
        ),
        (
            "weave-unit-right",
            "(equal (weave (pulse (silence)) (pulse (silence))) (pulse (silence)))",
            "(pulse (silence))",
        ),
    ),
)
def test_every_native_law_and_term_constructor_elaborates(law, claim, args):
    result = compile_surface_program(source(claim, f"(native-law {law} {args})"))
    assert result.judgment.native_law_closure == (NativeLawId(law),)


@pytest.mark.parametrize(
    ("bad", "code"),
    (
        ("(veyra-proof 2 (claim (equal (silence) (silence))) (proof (eq-refl (silence))))", "version"),
        (source("(iff (equal (silence) (silence)) (equal (silence) (silence)))", "(eq-refl (silence))"), "unsupported-proposition"),
        (source("(ready (silence))", "(eq-refl (silence))"), "unsupported-proposition"),
        (source("(forall x integer (equal (var x) (var x)))", "(eq-refl (silence))"), "binder-type"),
        (source(P, "(eq-refl (silence) (silence))"), "eq-refl-bad-arity"),
        (source(P, "(native-law weave-pulse (silence))"), "native-law-bad-arity"),
        (source(P, "(magic (silence))"), "unsupported-proof"),
    ),
)
def test_unsupported_wrong_type_and_wrong_arity_forms_fail_closed(bad, code):
    with pytest.raises(SurfaceLanguageError) as caught:
        compile_surface_program(bad)
    assert code in caught.value.code
    assert caught.value.span is not None


@pytest.mark.parametrize(
    ("claim", "proof", "code"),
    (
        (
            "(forall x recurrence (forall x recurrence (equal (var x) (var x))))",
            "(eq-refl (silence))",
            "duplicate-term-binder",
        ),
        (P, f"(imp-intro h {P} (imp-intro h {P} (assume h)))", "duplicate-assumption-binder"),
        (P, f"(imp-intro x {P} (forall-intro x recurrence (eq-refl (var x))))", "captured-binder-name"),
        ("(equal (var missing) (silence))", "(eq-refl (silence))", "unbound-term-variable"),
        (P, "(assume missing)", "unbound-assumption"),
    ),
)
def test_duplicate_unbound_and_captured_binders_are_rejected(claim, proof, code):
    with pytest.raises(SurfaceLanguageError) as caught:
        compile_surface_program(source(claim, proof))
    assert caught.value.code == code
    assert caught.value.span is not None


def test_declared_conclusion_and_altered_proof_are_checked_not_trusted():
    with pytest.raises(SurfaceLanguageError, match="declared-conclusion-mismatch"):
        compile_surface_program(source("(equal (pulse (silence)) (pulse (silence)))", "(eq-refl (silence))"))
    bad_equality = "(resonance-intro (silence) (silence) (pulse (silence)) (eq-refl (silence)))"
    with pytest.raises(SurfaceLanguageError, match="kernel-rejected/resonance-witness-mismatch"):
        compile_surface_program(source("(resonates (silence) (silence))", bad_equality))


def test_parser_and_elaborator_resource_limits_are_fail_closed():
    small_source = SourceLimits(max_bytes=20, max_tokens=100, max_nodes=100, max_depth=20)
    with pytest.raises(SurfaceLanguageError, match="source-byte-limit"):
        compile_surface_program(source(P, "(eq-refl (silence))"), source_limits=small_source)
    shallow = SourceLimits(max_bytes=10_000, max_tokens=100, max_nodes=100, max_depth=2)
    with pytest.raises(SurfaceLanguageError, match="nesting-limit"):
        compile_surface_program(source(P, "(eq-refl (silence))"), source_limits=shallow)
    tiny_tokens = SourceLimits(max_bytes=10_000, max_tokens=5, max_nodes=100, max_depth=20)
    with pytest.raises(SurfaceLanguageError, match="token-limit"):
        compile_surface_program(source(P, "(eq-refl (silence))"), source_limits=tiny_tokens)
    tiny_nodes = SourceLimits(max_bytes=10_000, max_tokens=100, max_nodes=5, max_depth=20)
    with pytest.raises(SurfaceLanguageError, match="node-limit"):
        compile_surface_program(source(P, "(eq-refl (silence))"), source_limits=tiny_nodes)
    nested_claim = "(forall a recurrence (forall b recurrence (equal (var a) (var a))))"
    nested_proof = "(forall-intro a recurrence (forall-intro b recurrence (eq-refl (var a))))"
    with pytest.raises(SurfaceLanguageError, match="binder-limit"):
        compile_surface_program(
            source(nested_claim, nested_proof),
            elaboration_limits=ElaborationLimits(max_depth=96, max_binders=1),
        )
    nested_implication = f"(implies {P} (implies {P} {P}))"
    nested_implication_proof = f"(imp-intro h {P} (imp-intro k {P} (assume k)))"
    with pytest.raises(SurfaceLanguageError, match="binder-limit"):
        compile_surface_program(
            source(nested_implication, nested_implication_proof),
            elaboration_limits=ElaborationLimits(max_depth=96, max_binders=1),
        )


def test_forged_typed_ast_payload_is_not_silently_ignored():
    raw = source(P, "(eq-refl (silence))")
    program = parse_surface_program(raw)
    forged = replace(program, proof=replace(program.proof, law_id="weave-unit-right"))
    with pytest.raises(SurfaceLanguageError, match="unbound-typed-ast"):
        elaborate_surface_program(forged)
    with pytest.raises(SurfaceLanguageError, match="captured-source-ast-mismatch"):
        elaborate_surface_program(forged, captured_source=raw.encode("ascii"))


def test_diagnostics_include_exact_half_open_source_span():
    bad = source("(equal (var missing) (silence))", "(eq-refl (silence))")
    with pytest.raises(SurfaceLanguageError) as caught:
        compile_surface_program(bad)
    span = caught.value.span
    assert span is not None
    assert bad[span.start:span.end] == "(var missing)"
