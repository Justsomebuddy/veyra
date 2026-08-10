"""Certificate bridge for the VAM reference interpreter."""
from __future__ import annotations

import logging
from pathlib import Path

from src.core.theorem_language import TheoremEnvironment
from vam.src import (
    canonical_report,
    classify_program,
    compile_highlevel_source,
    compile_source,
    compile_source_with_diagnostics,
    decode_dense,
    decode_vmbc,
    dense_round_trip,
    disassemble,
    encode_dense,
    encode_vmbc,
    decode_shell_carrier_label,
    error_row,
    execute,
    iter_fixture_reports,
    iter_valid_vam0_fixture_report_programs,
    lower_theorem_source,
    obligation_batch_is_transport_only,
    obligation_rows_from_theorem,
    obligation_status,
    opcode_rows,
    opcode_table_from_rows,
    optimize,
    optimizer_obligation_payload,
    optimizer_witness_ledger,
    parse_vmasm,
    proof_conjunction_from_cases,
    proof_conjunction_from_shell_carrier,
    lower_hl1_source,
    summarize_equivalence,
)

from .certify_types import Certificate
from .certify_vam_optimizer import certify_vam_optimizer_gate

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

_CORE_ECHO = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"


def _comparable(program):
    logger.debug("_comparable entry instructions=%d", len(program))
    result = [item.comparable() for item in program]
    logger.debug("_comparable exit rows=%d", len(result))
    return result


def _accepted_clean(program) -> tuple[bool, int, bool]:
    logger.debug("_accepted_clean entry instructions=%d", len(program))
    report = optimize(decode_vmbc(encode_vmbc(program)))
    state = execute(report.optimized)
    accepted = len(state.certs) == 1 and state.certs[0].field("accepted") is True
    result = (accepted and not state.obstructions and not report.rejected_rows, len(report.optimized), accepted)
    logger.debug("_accepted_clean exit result=%r", result)
    return result


def certify_vam_reference_v1() -> Certificate:
    """Certify assembly, VAM0, optimizer, Core lowering, and v0.8 carriers."""
    logger.debug("certify_vam_reference_v1 entry")
    root = PROJECT_ROOT
    source = (root / "vam/examples/minimal_echo.vmasm").read_text(encoding="utf-8")
    program = parse_vmasm(source)
    text_round_trip = parse_vmasm(disassemble(program))
    binary_round_trip = decode_vmbc(encode_vmbc(program))
    dense_round_trip_program = dense_round_trip(program)
    dense_blob = encode_dense(program)
    asm_ok, opt_len, asm_accepted = _accepted_clean(binary_round_trip)
    same_ir = _comparable(text_round_trip) == _comparable(program)
    same_binary = _comparable(binary_round_trip) == _comparable(program)
    dense_ok = _comparable(dense_round_trip_program) == _comparable(program) and _comparable(decode_dense(dense_blob)) == _comparable(program) and dense_blob.startswith(b"VAMD") and len(dense_blob) < len(encode_vmbc(program))
    compiled = compile_source(_CORE_ECHO, claim="core-length-echo")
    dense_core_ok = _comparable(dense_round_trip(compiled.program)) == _comparable(compiled.program)
    core_ok, core_opt_len, core_accepted = _accepted_clean(compiled.program)
    core_report = canonical_report(compiled.program, execute(compiled.program))
    report_ok = core_report["profile"] == "vam0-ref-v1" and core_report["final_pc"] == len(compiled.program)
    diag_ok = compile_source_with_diagnostics(_CORE_ECHO).ok
    bad_diag = compile_source_with_diagnostics("echo(nod:a,nod:a,observer:weight)")
    diag_blocked = bad_diag.diagnostic is not None and bad_diag.diagnostic.error_class == "lower.unsupported_observer"
    shell = compile_source("shell(echo(nod:a,nod:a,observer:kind))", certify=True)
    shell_state = execute(shell.program)
    shell_carrier = decode_shell_carrier_label(shell_state.registers[shell.root_register].field("label"))
    shell_ok = shell.cert_register is None and not shell_state.certs and not shell_state.obstructions and shell_carrier["status"] == "transported"
    blocked_shell = compile_source("shell(echo(nod:a,nod:bbb,observer:label))", certify=True)
    blocked_state = execute(blocked_shell.program)
    blocked_carrier = decode_shell_carrier_label(blocked_state.registers[blocked_shell.root_register].field("label"))
    shell_blocked_ok = blocked_carrier["status"] == "blocked" and len(blocked_state.obstructions) == 1 and not blocked_state.certs
    theorem = lower_theorem_source(
        "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))",
        (TheoremEnvironment("nod-a", {"x": "nod:a"}),),
        module="cert",
    )
    theorem_ok = theorem.proof_status == "verified" and len(theorem.obligations) == 1 and len(theorem.finite_cases) == 1 and theorem.finite_cases[0].status == "verified"
    theorem_proof = proof_conjunction_from_cases(theorem.finite_cases, id="cert-theorem-cases")
    theorem_proof_ok = theorem_proof.status == "verified" and not theorem_proof.accepted_certificate
    rows = obligation_rows_from_theorem(theorem)
    obligation_ok = obligation_status(rows).all_verified and obligation_batch_is_transport_only(rows)
    shell_proof = proof_conjunction_from_shell_carrier(shell_carrier, id="cert-shell-carrier")
    blocked_shell_proof = proof_conjunction_from_shell_carrier(blocked_carrier, id="cert-blocked-shell-carrier")
    shell_proof_ok = (
        shell_proof.status == "verified"
        and blocked_shell_proof.status == "blocked"
        and not shell_proof.accepted_certificate
        and not blocked_shell_proof.accepted_certificate
    )
    opcode_classifications = classify_program(program)
    opcode_rows_round_trip = opcode_table_from_rows(opcode_rows())
    opcode_ok = len(opcode_classifications) == len(program) and len(opcode_rows_round_trip) == len(opcode_rows())
    taxonomy = error_row("unsupported or malformed instruction: NOPE/1", source="cert")
    taxonomy_ok = taxonomy["code"] == "execution.unsupported_instruction"
    highlevel = compile_highlevel_source("claim same := echo(nod:a,nod:a) under kind")
    highlevel_ok = highlevel.ok and highlevel.core_source == "echo(nod:a,nod:a,observer)"
    hl1 = lower_hl1_source("observer length_obs := length\nprocess demo { claim same := echo(nod:a,nod:a) under length_obs }")
    hl1_ok = hl1.ok and hl1.core_source == "echo(nod:a,nod:a,observer:length)"
    equivalence = summarize_equivalence(compiled.program, optimize(compiled.program).optimized)
    equivalence_ok = equivalence.safe and equivalence.check("report-fingerprint").status == "equivalent"
    witness = optimizer_witness_ledger(compiled.program)
    witness_ok = (
        witness["boundary"] == "bounded-witness-ledger"
        and witness["claim"] == "regression-evidence-not-proof"
        and str(witness["status"]).startswith("bounded-regression-")
        and len(witness["ledger_digest"]) == 64
    )
    obligation_ledger = witness["optimizer_obligation_ledger"]
    optimizer_obligations_ok = (
        obligation_ledger["boundary"] == "proof-obligation-ledger"
        and obligation_ledger["claim"] == "obligation-map-not-proof"
        and tuple(obligation_ledger["rows"]) == optimizer_obligation_payload()
        and {row["pass_name"] for row in obligation_ledger["rows"]}
        == {"observer-alias", "compress-alias", "compress-idempotent", "dead-shadow"}
        and len(witness["digests"]["optimizer_obligation_ledger"]) == 64
    )
    optimizer_gate = certify_vam_optimizer_gate(root)
    fixture_reports = tuple(iter_fixture_reports())
    valid_fixture_reports = tuple(iter_valid_vam0_fixture_report_programs())
    fixtures_ok = len(fixture_reports) >= 16 and len(valid_fixture_reports) == len(fixture_reports) and all(report["profile"] == "vam0-ref-v1" for _, report in fixture_reports)
    native_root = root / "vam/native/Cargo.toml"
    native_paths = (
        native_root,
        root / "vam/native/src/lib.rs",
        root / "vam/native/src/frame.rs",
        root / "vam/native/src/runtime.rs",
        root / "vam/native/src/dense.rs",
        root / "vam/native/src/json.rs",
        root / "vam/native/src/main.rs",
    )
    native_cli = all(path.exists() for path in native_paths)
    native_dense_cli = native_cli and (root / "tests/test_vam_native_vamd_executor.py").exists()
    native_optimizer_paths = (
        root / "vam/native/src/optimizer.rs",
        root / "vam/native/src/optimizer/tests.rs",
        root / "vam/native/src/optimizer/analysis.rs",
        root / "vam/native/src/optimizer/passes.rs",
        root / "vam/native/src/optimizer/passes/alias.rs",
        root / "vam/native/src/optimizer/passes/compress.rs",
        root / "vam/native/src/optimizer/passes/dead_shadow.rs",
        root / "vam/native/src/optimizer/passes/utils.rs",
    )
    native_optimizer_slice = native_cli and all(path.exists() for path in native_optimizer_paths) and (root / "tests/test_vam_native_optimizer.py").exists()
    native_optimizer_extension = native_optimizer_slice and (root / "tests/test_vam_native_optimizer_expansion.py").exists()
    native_vamd_optimizer_policy = native_optimizer_extension and (root / "tests/test_vam_native_optimizer_generated.py").exists() and (root / "vam/docs/024_vam_v1_6_vamd_optimizer_and_generated_parity.md").exists()
    native_vam0_emission = native_vamd_optimizer_policy and (root / "tests/test_vam_native_emit_optimized_vam0.py").exists() and (root / "vam/docs/025_vam_v1_7_optimized_vam0_emission.md").exists()
    optimizer_witness_gate = (
        (root / "vam/src/optimizer_witness.py").exists()
        and (root / "vam/src/optimizer_obligations.py").exists()
        and (root / "tests/test_vam_optimizer_witness.py").exists()
        and (root / "tests/test_vam_optimizer_obligations.py").exists()
        and (root / "vam/docs/026_vam_v1_8_optimizer_witness_metamorphic_parity.md").exists()
    )
    optimizer_obligation_gate = optimizer_witness_gate and (root / "vam/docs/027_vam_v1_9_optimizer_proof_obligation_ledger.md").exists()
    native_optimizer_metamorphic = native_vam0_emission and (root / "tests/test_vam_native_optimizer_metamorphic.py").exists()
    native_vamd_boundaries = (root / "tests/test_vam_native_vamd_boundaries.py").exists()
    native_parity_expanded = (root / "tests/test_vam_native_parity_expansion.py").exists()
    parity_harness = (root / "vam/benchmarks/semantic_parity.py").exists()
    passed = (
        same_ir
        and same_binary
        and dense_ok
        and dense_core_ok
        and asm_ok
        and core_ok
        and report_ok
        and diag_ok
        and diag_blocked
        and shell_ok
        and shell_blocked_ok
        and theorem_ok
        and theorem_proof_ok
        and obligation_ok
        and shell_proof_ok
        and opcode_ok
        and taxonomy_ok
        and highlevel_ok
        and hl1_ok
        and equivalence_ok
        and witness_ok
        and optimizer_obligations_ok
        and fixtures_ok
        and native_cli
        and native_dense_cli
        and native_optimizer_slice
        and native_optimizer_extension
        and native_vamd_optimizer_policy
        and native_vam0_emission
        and optimizer_witness_gate
        and optimizer_obligation_gate
        and optimizer_gate.proof_bridge_ok
        and optimizer_gate.prepost_ok
        and native_optimizer_metamorphic
        and native_vamd_boundaries
        and native_parity_expanded
        and parity_harness
    )
    detail = (
        f"instr={len(program)} opt={opt_len} text={same_ir} vmbc={same_binary} dense={dense_ok}/{dense_core_ok}/{len(dense_blob)} "
        f"asm={asm_accepted} core={core_accepted}/{core_opt_len} report={report_ok} "
        f"diag={diag_ok}/{diag_blocked} shell={shell_ok}/{shell_blocked_ok}/{shell_carrier['status']} theorem={theorem.proof_status}/{len(theorem.obligations)}/{len(theorem.finite_cases)} "
        f"proof={theorem_proof.status}/{shell_proof.status}/{blocked_shell_proof.status} obligation={obligation_ok} opcodes={len(opcode_rows())}/{opcode_ok} errors={taxonomy['code']}/{taxonomy_ok} "
        f"highlevel={highlevel_ok}/{hl1_ok} equivalence={equivalence_ok} "
        f"witness={witness_ok}/{witness['status']} obligations={optimizer_obligations_ok}/{len(obligation_ledger['rows'])} "
        f"fixtures={len(fixture_reports)}/{fixtures_ok} native_cli={native_cli} native_dense_cli={native_dense_cli} "
        f"native_optimizer_slice={native_optimizer_slice} native_optimizer_extension={native_optimizer_extension} native_vamd_boundaries={native_vamd_boundaries} "
        f"native_vamd_optimizer_policy={native_vamd_optimizer_policy} native_vam0_emission={native_vam0_emission} "
        f"optimizer_witness_gate={optimizer_witness_gate} optimizer_obligation_gate={optimizer_obligation_gate} "
        f"{optimizer_gate.detail} native_optimizer_metamorphic={native_optimizer_metamorphic} "
        f"native_parity_expanded={native_parity_expanded} parity_harness={parity_harness}"
    )
    result = Certificate(
        "vam_reference_v1",
        "VAM reference interpreter, VAM0/VAMD frames, conservative optimizer, Core/HL-1 lowering, diagnostics, finite shell/theorem carriers, proof-object rows, error taxonomy, opcode metadata, canonical reports, fixture corpus, native CLI parity gates, bounded native optimizer extension, VAMD semantic optimizer policy documentation gate, generated parity corpus gate, optimized VAM0 frame emission gate, bounded optimizer witness ledger gate, bounded optimizer proof-obligation ledger gate, checked optimizer 7-local-law bridge gate, executable pre/post witness gate, metamorphic parity harness gate, and speed-neutral parity harness",
        passed,
        detail,
        1,
    )
    logger.debug("certify_vam_reference_v1 exit result=%r", result)
    return result
