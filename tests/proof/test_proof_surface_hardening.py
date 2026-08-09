from dataclasses import replace
import logging

import pytest

import src.core.proof_surface_elaborator as surface_elaborator
from src.core.proof_surface_elaborator import (
    compile_surface_program, elaborate_surface_program,
)
from src.core.proof_surface_parser import parse_surface_program
from src.core.proof_surface_types import (
    ABSOLUTE_SAFE_DEPTH, ABSOLUTE_TYPED_AST_NODES, ElaborationLimits,
    SourceLimits, SourceSpan, SurfaceLanguageError,
)
from src.core.proof_surface_validation import captured_source_digest


P = "(equal (silence) (silence))"


def source(claim: str, proof: str) -> str:
    return f"(veyra-proof 1 (claim {claim}) (proof {proof}))"


def test_direct_ast_is_unbound_without_exact_captured_bytes_and_digest_is_not_injectable():
    text = source(P, "(eq-refl (silence))")
    raw = text.encode("ascii")
    program = parse_surface_program(text)
    with pytest.raises(SurfaceLanguageError, match="unbound-typed-ast"):
        elaborate_surface_program(program)
    with pytest.raises(SurfaceLanguageError, match="forged-source-digest"):
        elaborate_surface_program(program, captured_source=raw, source_digest="0" * 64)
    direct = elaborate_surface_program(program, captured_source=raw)
    compiled = compile_surface_program(text)
    assert direct == compiled
    assert direct.source_digest == captured_source_digest(raw)


def test_forged_span_shape_range_containment_and_valid_drift_are_rejected():
    text = source(P, "(eq-refl (silence))") + "  "
    raw = text.encode("ascii")
    program = parse_surface_program(text)
    bad_shape = replace(program, span=SourceSpan(True, program.span.end))
    with pytest.raises(SurfaceLanguageError, match="invalid-source-span"):
        elaborate_surface_program(bad_shape, captured_source=raw)
    bad_range = replace(program, span=SourceSpan(-1, program.span.end))
    with pytest.raises(SurfaceLanguageError, match="invalid-source-span"):
        elaborate_surface_program(bad_range, captured_source=raw)
    outside = replace(program.claim, span=SourceSpan(program.span.end, program.span.end + 1))
    with pytest.raises(SurfaceLanguageError, match="source-span-not-contained"):
        elaborate_surface_program(replace(program, claim=outside), captured_source=raw)
    shifted = replace(program.claim, span=SourceSpan(program.claim.span.start + 1, program.claim.span.end))
    with pytest.raises(SurfaceLanguageError, match="captured-source-ast-mismatch"):
        elaborate_surface_program(replace(program, claim=shifted), captured_source=raw)


def test_total_typed_ast_budget_and_absolute_caps_fail_closed():
    text = source(P, "(eq-refl (silence))")
    with pytest.raises(SurfaceLanguageError, match="typed-ast-node-limit"):
        compile_surface_program(
            text,
            elaboration_limits=ElaborationLimits(max_depth=96, max_binders=96, max_nodes=3),
        )
    with pytest.raises(SurfaceLanguageError, match="invalid-elaboration-limits"):
        compile_surface_program(
            text,
            elaboration_limits=ElaborationLimits(
                max_depth=96, max_binders=96,
                max_nodes=ABSOLUTE_TYPED_AST_NODES + 1,
            ),
        )
    unsafe = SourceLimits(max_depth=ABSOLUTE_SAFE_DEPTH + 1)
    with pytest.raises(SurfaceLanguageError, match="invalid-source-limits"):
        compile_surface_program(text, source_limits=unsafe)


def test_deep_source_is_budget_rejected_without_raw_recursion_error():
    nested = "(silence)"
    for _ in range(ABSOLUTE_SAFE_DEPTH + 4):
        nested = f"(pulse {nested})"
    text = source(f"(equal {nested} {nested})", f"(eq-refl {nested})")
    limits = SourceLimits(
        max_bytes=100_000, max_tokens=10_000, max_nodes=10_000,
        max_depth=ABSOLUTE_SAFE_DEPTH, max_identifier_bytes=64,
    )
    with pytest.raises(SurfaceLanguageError, match="nesting-limit"):
        compile_surface_program(text, source_limits=limits)


def test_raw_recursion_error_is_translated_once_at_source_boundary(monkeypatch, caplog):
    def explode(*_args, **_kwargs):
        raise RecursionError("synthetic")

    monkeypatch.setattr(surface_elaborator, "parse_surface_program", explode)
    with caplog.at_level(logging.ERROR), pytest.raises(SurfaceLanguageError, match="safe-recursion-limit"):
        compile_surface_program(source(P, "(eq-refl (silence))"))
    errors = [row for row in caplog.records if row.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert "safe-recursion-limit" in errors[0].message


@pytest.mark.parametrize(
    ("text", "code"),
    (
        (source(P, "(eq-refl (silence))") + "é", "source-must-be-ascii"),
        (source(P, "(eq-refl (silence))") + "\x00", "nul-byte-forbidden"),
        (
            source(
                f"(forall {'x' * 65} recurrence {P})",
                "(eq-refl (silence))",
            ),
            "atom-byte-limit",
        ),
    ),
)
def test_non_ascii_nul_and_identifier_limits_are_deterministic(text, code):
    with pytest.raises(SurfaceLanguageError) as caught:
        compile_surface_program(text)
    assert caught.value.code == code


def test_distinct_valid_proofs_have_distinct_semantic_digests():
    direct = compile_surface_program(source(P, "(eq-refl (silence))"))
    symmetric = compile_surface_program(source(P, "(eq-sym (eq-refl (silence)))"))
    assert direct.claim == symmetric.claim
    assert direct.semantic_digest != symmetric.semantic_digest
    assert direct.artifact.proof_digest == direct.semantic_digest
    assert symmetric.artifact.proof_digest == symmetric.semantic_digest
