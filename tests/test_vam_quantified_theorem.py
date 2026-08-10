from __future__ import annotations

from dataclasses import replace
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.project_hygiene import line_limit
from vam.src.quantified_theorem import (
    BOUNDARY,
    PROFILE,
    QuantifiedBinder,
    QuantifiedTheoremInstruction,
    canonical_quantified_instruction,
    declare_quantified_theorem,
    native_quantified_parity_boundary,
    specialize_quantified_theorem,
)

ROOT = Path(__file__).resolve().parents[1]
RUST_SOURCE = ROOT / "vam/native/src/quantified_theorem.rs"


def _state():
    return declare_quantified_theorem(
        "echo-reflexive",
        (QuantifiedBinder("x", "nod"),),
        (),
        ("ready(echo($x,$x,observer:kind))",),
    )


def test_symbolic_quantified_instruction_exists_without_finite_environments():
    state = _state()

    assert state.status == "well-formed-open"
    assert state.proof_status == "open"
    assert state.free_variables == ()
    assert state.boundary == BOUNDARY
    assert state.instruction.profile == PROFILE
    assert state.instruction.opcode == "DECLARE_FORALL"
    assert "finite_cases" not in state.canonical_text


def test_specialization_is_capture_safe_total_and_remains_open():
    instance = specialize_quantified_theorem(_state(), {"x": "nod:a"})

    assert instance.assignments == (("x", "nod:a"),)
    assert instance.conclusions == ("ready(echo(nod:a,nod:a,observer:kind))",)
    assert instance.status == "instantiated-open"
    assert instance.proof_status == "open"
    assert instance.boundary == BOUNDARY


@pytest.mark.parametrize(
    "value",
    ("mode:a", "nod:a)", r"nod:\1", "nod:.*", "nod:${x}", "nod:a:b", "nod:é", 7),
)
def test_specialization_rejects_type_mismatch_and_hostile_atomic_syntax(value):
    with pytest.raises(ValueError, match="specialization|unsafe"):
        specialize_quantified_theorem(_state(), {"x": value})  # type: ignore[dict-item]


def test_specialization_enforces_input_and_expanded_row_byte_bounds():
    with pytest.raises(ValueError, match="unsafe specialization"):
        specialize_quantified_theorem(_state(), {"x": "nod:" + "a" * 4093})
    expanding = declare_quantified_theorem(
        "bounded", (QuantifiedBinder("x", "nod"),), (), ("$x$x",)
    )
    with pytest.raises(ValueError, match="resource bound"):
        specialize_quantified_theorem(expanding, {"x": "nod:" + "a" * 3000})


def test_specialization_rejects_a_tampered_symbolic_state():
    state = replace(_state(), canonical_text="{}")

    with pytest.raises(ValueError, match="not an open declaration"):
        specialize_quantified_theorem(state, {"x": "nod:a"})


@pytest.mark.parametrize(
    "assignments",
    ({}, {"x": "nod:a", "y": "nod:b"}, {"x": "$y"}, {"x": ""}),
)
def test_specialization_fails_closed_on_incomplete_extra_or_unsafe_values(assignments):
    with pytest.raises(ValueError):
        specialize_quantified_theorem(_state(), assignments)


def test_declaration_rejects_duplicate_binders_free_variables_and_empty_claim():
    with pytest.raises(ValueError, match="duplicate"):
        declare_quantified_theorem(
            "bad", (QuantifiedBinder("x", "nod"), QuantifiedBinder("x", "nod")), (), ("ready($x)",)
        )
    with pytest.raises(ValueError, match="free quantified"):
        declare_quantified_theorem("bad", (QuantifiedBinder("x", "nod"),), (), ("ready($y)",))
    with pytest.raises(ValueError, match="requires binders and conclusions"):
        declare_quantified_theorem("bad", (QuantifiedBinder("x", "nod"),), (), ())


@pytest.mark.parametrize("text", ("$", "${x}", "$1", "$é"))
def test_declaration_rejects_structurally_invalid_placeholders(text):
    with pytest.raises(ValueError, match="invalid quantified placeholder"):
        declare_quantified_theorem("bad", (QuantifiedBinder("x", "nod"),), (), (text,))


def test_quantified_schema_rejects_noncanonical_and_oversized_payloads():
    with pytest.raises(ValueError, match="invalid quantified theorem id"):
        canonical_quantified_instruction(
            QuantifiedTheoremInstruction(1, (QuantifiedBinder("x", "nod"),), (), ("$x",))  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="invalid quantified theorem text"):
        declare_quantified_theorem(
            "too-large", (QuantifiedBinder("x", "nod"),), (), ("x" * 4097,)
        )
    with pytest.raises(ValueError, match="invalid specialization assignment mapping"):
        specialize_quantified_theorem(_state(), {1: "nod:a"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="invalid specialization assignment mapping"):
        specialize_quantified_theorem(_state(), dict(x="nod:a").items())  # type: ignore[arg-type]


def test_canonical_instruction_is_stable_and_language_neutral():
    instruction = _state().instruction
    expected = (
        '{"assumptions":[],"binders":[{"kind":"nod","name":"x"}],'
        '"conclusions":["ready(echo($x,$x,observer:kind))"],'
        '"opcode":"DECLARE_FORALL","profile":"veyra.vam.quantified-theorem.v1",'
        '"theorem_id":"echo-reflexive"}'
    )

    assert canonical_quantified_instruction(instruction) == expected
    assert canonical_quantified_instruction(instruction) == expected


def _rustc() -> str:
    found = shutil.which("rustc")
    if found:
        return found
    fallback = Path.home() / ".cargo/bin/rustc"
    if fallback.exists():
        return str(fallback)
    pytest.skip("rustc unavailable")


def test_native_quantified_module_unit_tests_pass(tmp_path):
    binary = tmp_path / "quantified-theorem-tests"
    build = subprocess.run(
        [_rustc(), "--edition=2021", "--test", str(RUST_SOURCE), "-o", str(binary)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    run = subprocess.run(
        [str(binary)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    assert run.returncode == 0, run.stdout + run.stderr


def test_python_rust_canonical_schema_parity(tmp_path):
    harness = tmp_path / "parity.rs"
    source_path = RUST_SOURCE.as_posix()
    harness.write_text(
        f'''#[path = "{source_path}"] mod quantified_theorem;
use quantified_theorem::{{Binder, QuantifiedInstruction, canonical_text}};
fn main() {{
    let row = QuantifiedInstruction {{
        theorem_id: "echo-reflexive".into(),
        binders: vec![Binder {{ name: "x".into(), kind: "nod".into() }}],
        assumptions: vec![],
        conclusions: vec!["ready(echo($x,$x,observer:kind))".into()],
    }};
    print!("{{}}", canonical_text(&row).unwrap());
}}
''',
        encoding="utf-8",
    )
    binary = tmp_path / "parity"
    build = subprocess.run(
        [_rustc(), "--edition=2021", str(harness), "-o", str(binary)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    run = subprocess.run(
        [str(binary)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )

    assert run.returncode == 0, run.stderr
    assert run.stdout == _state().canonical_text


def test_python_rust_typed_specialization_and_resource_parity(tmp_path):
    harness = tmp_path / "specialize_parity.rs"
    harness.write_text(
        f'''#[path = "{RUST_SOURCE.as_posix()}"] mod quantified_theorem;
use quantified_theorem::{{Binder, QuantifiedInstruction, specialize}};
fn main() {{
    let row = QuantifiedInstruction {{
        theorem_id: "echo-reflexive".into(),
        binders: vec![Binder {{ name: "x".into(), kind: "nod".into() }}],
        assumptions: vec![], conclusions: vec!["ready($x)".into()],
    }};
    for value in ["nod:a".into(), "mode:a".into(), "nod:a)".into(),
                  format!("nod:{{}}", "a".repeat(4093))] {{
        print!("{{}}", if specialize(&row, &[("x".into(), value)]).is_ok() {{ '1' }} else {{ '0' }});
    }}
    let mut expanded = row; expanded.conclusions = vec!["$x$x".into()];
    let large = format!("nod:{{}}", "a".repeat(3000));
    print!("{{}}", if specialize(&expanded, &[("x".into(), large)]).is_ok() {{ '1' }} else {{ '0' }});
}}
''',
        encoding="utf-8",
    )
    binary = tmp_path / "specialize-parity"
    build = subprocess.run(
        [_rustc(), "--edition=2021", str(harness), "-o", str(binary)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert build.returncode == 0, build.stderr
    run = subprocess.run(
        [str(binary)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    python_status = []
    for value in ("nod:a", "mode:a", "nod:a)", "nod:" + "a" * 4093):
        try:
            specialize_quantified_theorem(_state(), {"x": value})
            python_status.append("1")
        except ValueError:
            python_status.append("0")
    expanded = declare_quantified_theorem("bounded", (QuantifiedBinder("x", "nod"),), (), ("$x$x",))
    with pytest.raises(ValueError):
        specialize_quantified_theorem(expanded, {"x": "nod:" + "a" * 3000})
    python_status.append("0")
    assert run.returncode == 0, run.stderr
    assert run.stdout == "".join(python_status) == "10000"


def test_native_parity_is_executable_evidence_not_proof_grade():
    boundary = native_quantified_parity_boundary()

    assert boundary.status == "bounded-executable-parity"
    assert boundary.parity_surfaces == ("validation", "canonical-text", "total-specialization")
    assert boundary.proof_grade is False
    assert "no checked" in boundary.obstruction
    assert len(boundary.required_formal_gates) == 4


def test_completion_files_remain_within_project_target():
    paths = (
        Path("vam/src/optimizer_completion.py"),
        Path("vam/src/quantified_theorem.py"),
        Path("vam/native/src/quantified_theorem.rs"),
        Path("tests/test_vam_optimizer_completion.py"),
        Path("tests/test_vam_quantified_theorem.py"),
    )

    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= line_limit(path)
        for path in paths
    )
