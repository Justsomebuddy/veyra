# VAM — Veyra Abstract Machine


VAM is the execution substrate for Veyra: a small abstract machine whose primitive operations are not ordinary arithmetic instructions, but Veyra-native process operations: `REZ`, `NOD`, `TACT`, `BREATH`, `MODE`, `OBSERVE`, `ECHO`, `OBSTRUCT`, `COMPRESS`, and `CERT`.

## Why this exists

The current Python implementation proves that Veyra rows are executable, but it is still a host-language library. VAM is the path from Veyra-as-library to Veyra-as-computing-platform.

## Roadmap

1. **VAM Spec** — minimal abstract machine semantics.
2. **Veyra Bytecode** — text and binary instruction layer.
3. **Interpreter** — reference Python/Rust executor.
4. **Assembler / Disassembler** — `.vmasm` to bytecode and readable dumps.
5. **Optimizer** — echo-preserving rewrites, compression, observer pruning.
6. **Compiler from Core Language** — current DSL to VAM bytecode.
7. **Native backend** — Rust/C/LLVM/GPU/FPGA targets.
8. **High-level language** — theorem/observer/process-first syntax.

## Current status

- VAM subproject scaffolded.
- VAM Spec v0.1 drafted in `docs/001_vam_spec.md`.
- Text bytecode/assembly draft in `docs/002_bytecode_text.md`.
- Reference parser/disassembler/interpreter v0.2 implemented in `src/`.
- VAM0 binary frame v0.3 implemented in `src/bytecode.py`.
- Conservative optimizer v0.6 implemented in `src/optimizer.py`: obstruction-safe dead-shadow, single-definition guards, and duplicate `COMPRESS` aliasing.
- Core Language lowering v0.6 implemented in `src/compiler.py`: finite subset lowering with Core preflight and observer-parity tests.
- Diagnostics/theorem carriers v0.7 implemented in `src/diagnostics.py` and `src/theorem.py`: span-aware compiler boundary diagnostics plus finite obligation transport, not theorem proving.
- Illustrative `.vmasm` programs live in `examples/minimal_echo.vmasm` and `examples/core_echo.vmasm`.
- Native Rust v1.9 slice lives in `native/`: `vam0-inspect` validates/executes both VAM0 and VAMD frames, autodetects frame magic, fixture-compares Rust reports against the Python canonical oracle, exposes bounded decoded VAM0/VAMD optimizer report parity, can emit optimized VAM0 frames for VAM0 input only, and is covered by witness/obligation/metamorphic regression evidence.
- VAM v1.0 adds finite theorem-case carriers, non-certificate shell/conjunction carriers, expanded obstruction/malformed-frame fixtures, native boundary tests, and conservative `compress-idempotent` normalization.
- VAM v1.1 adds error-taxonomy rows, dense-opcode metadata, finite proof-object rows, native optimizer parity contract, and the next high-level-language slice plan.
- VAM v1.2 adds real `VAMD` dense bytecode: Python encoder/decoder, Rust parser scaffold, dense boundary tests, and isolated HL-1 observer/process lowering.
- VAM v1.3 exposes `VAMD` through the Rust CLI execution/report path and locks dense report parity against the Python oracle.
- VAM v1.4 adds the first native optimizer parity slice, expanded VAMD boundary tests, expanded VAM0/VAMD parity fixtures, and a speed-neutral semantic parity harness under `benchmarks/`.
- VAM v1.5 extends native optimizer parity to duplicate `COMPRESS`, same-observer `compress-idempotent`, and obstruction-safe dead-shadow pruning.
- VAM v1.6 accepts VAMD optimizer input only after decoding into the shared semantic report boundary and adds a bounded generated VAM0/VAMD optimizer parity corpus.
- VAM v1.7 adds `--emit-optimized-vam0` for VAM0-only optimized-frame artifacts; VAMD emission remains explicitly blocked.
- VAM v1.8 adds a deterministic optimizer witness ledger plus native VAM0/VAMD metamorphic parity tests; this is bounded regression evidence, not proof-grade optimizer correctness.
- VAM v1.9 adds a bounded optimizer proof-obligation ledger naming pass preconditions, postconditions, and invariants; this is an obligation map, not a proof.
- VAM v2.0 adds a first checked optimizer-semantics slice: observer-alias local lookup preservation is Lean-checked, while every optimizer pass remains obligation-backed.
- VAM v2.1 adds the second checked local law: same-observer `compress-idempotent` local rewrite idempotence; the pass remains obligation-backed.
- VAM v2.2 adds the third checked local law: same source/observer `compress-alias` local lookup preservation; the pass remains obligation-backed.
- VAM v2.3 adds the fourth checked local law: `dead-shadow` unused lookup/drop preservation; VAM v2.4 documents executable pre/post witness evidence connecting all four local laws to concrete optimizer examples.
- VAM v2.5 splits optimizer certificate gates and checked local-law catalog helpers so VAM proof/cert modules stay below the project module-size cap.
- VAM v2.6-v2.9 add checked `compress-idempotent` rejection/visible-use laws plus executable witnesses for different-observer, obstruction-boundary, and visible-use observer-preservation guards.
- The native observer-synthesis calibration adds a closed Rust R11 AST,
  byte-identical canonical identities, the pinned R14.1 1,565-row grammar,
  finite recurrence semantics, counter-bounded train-only CEGIS, and exact
  Python catalog/winner identities. Its counter-only trace is deliberately
  native-domain-separated. It is a library shadow, not the default backend or a
  general-synthesis/performance result.
- A bounded zero-vs-positive quotient benchmark now gives that native core one
  replayable surprise receipt with integer fit/class gaps and explicit absent
  process custody; it is not BM-F009, general discovery, or theorem evidence.
- Docs: `docs/003_reference_interpreter.md` through `docs/038_native_observer_surprise_receipt.md` cover interpreter, VAM0/VAMD, optimizer, Core/HL-1 lowering, diagnostics/theorem carriers, native scaffold, v0.8/v0.9 contracts, v1.x/v2.x finite semantics/metadata, the bounded Rust synthesis shadow, and its first replayable finite surprise receipt.

## Boundary

VAM is not yet faster than Python, not a proof assistant, and not a native-performance backend. VAMD is a compact representation and parity target, not a speed result. The Rust executor/parser/optimizer/emission and bounded synthesis slices plus v2.4 pre/post witnesses are parity/evidence checkpoints only, even when they cover VAMD inputs, emitted VAM0 artifacts, multiple optimizer passes, a finite synthesized winner, or the checked local-law Lean bridge. VAM is the executable contract that future interpreters, optimizers, and compilers must preserve.
