# VAM Reference Interpreter v0.2

## Scope

The first executable VAM layer is deliberately small:

- parse `.vmasm` text into `Instruction` IR;
- disassemble IR back to canonical `.vmasm`;
- execute deterministic register programs;
- record trace events, certificates, and obstructions;
- keep invalid Veyra constructions as `Obstruction` objects;
- emit canonical Python reports for native/runtime parity checks.

## Implemented files

- `vam/src/assembly.py` — text parser/disassembler.
- `vam/src/model.py` — instruction, object, trace, state dataclasses.
- `vam/src/interpreter.py` — reference executor.
- `vam/src/report.py` — deterministic `vam0-ref-v1` canonical reports.
- `tests/vam/test_vam_reference.py` and `tests/vam/test_vam_report.py` — round-trip, execution, obstruction, and report checks.

## Semantics boundary

This is not a native backend and not a proof assistant. The interpreter is a stable executable contract for future optimizer/compiler work.

## Next step

Keep extending the report oracle as new instruction families become executable so native backends cannot drift silently.
