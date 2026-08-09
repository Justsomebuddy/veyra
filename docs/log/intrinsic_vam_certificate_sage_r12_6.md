# R12.6 — Intrinsic-VAM certificate and Sage facade

**Status:** integration gate; non-promotional
**Date:** 2026-07-29
**Certificate:** `intrinsic_vam_r12`
**Level:** 2
**Sage schema:** `veyra.sage.intrinsic-vam.r12.6.v1`

## Purpose

R12.6 provides one public integration checkpoint for the already-reviewed
R12.1–R12.5 stack. It does not introduce a fifth bridge row, a new theorem,
or a new evidence class.

The certificate method is:

```text
four-lane intrinsic IR/VAMI replay plus
R11-continuous valid-image Lean preservation
```

## Core replay

`certify_intrinsic_vam_r12()` checks:

1. the exact four-row R12.1 registry digest and zero promotion-ready rows;
2. R7 recurrence, R9 intrinsic-mode, R11 branded-observation, and R11 ordered
   echo lowering/raising;
3. all four unverified R12.3 envelopes as
   `executable-witness / finite`, never promotion evidence;
4. four canonical VAMI frames with exact decode and structural execution;
5. false `evidence_accepted`, `promotion_ready`, and `taxonomy_changed` flags;
6. one call to the self-verifying public R12.5 report;
7. exact 9 theorem IDs, 28 source rows, 9 object rows, registry/effect/report
   bindings, and six checked bridge stages;
8. unchanged Essence taxonomy `35 / 1 / 4 / 25 / 5`, with
   `proof_complete=False`.

The public report is not independently verified a second time by R12.6:
`intrinsic_vam_formal_bridge_report()` already performs its own guarded
fresh verification before returning a checked report.
Likewise, `essence_report()` construction logs only structural counts, so
R12.6 evaluates the guarded readiness summary exactly once.

## Sage facade

```python
from veyra_sage.all import VeyraIntrinsicVamLab

row = VeyraIntrinsicVamLab().summary()
assert row["certificate"] == "intrinsic_vam_r12"
assert row["theorems"] == 9
assert row["lanes"] == 4
assert row["vami_frames"] == 4
assert row["presentation_only"] is True
assert row["evidence_accepted"] is False
assert row["promotion_ready"] is False
```

The public constructor runs the core certificate once. The aggregate
`sage_certificate_suite()` instead reuses the exact matching certificate from
the already-computed core suite, so it does not replay the guarded Lean bridge
again.

Only `VeyraIntrinsicVamLab` is added to `veyra_sage.all`; the public API count
changes from 90 to 91. Notebook artifacts stay at 41 notebooks / 280 cells.

## Evidence boundary

The Sage row says:

```text
capability = preserves
evidence = formal-bridge
scope = general
presentation_only = true
boundary = presentation of core certificate,
           not independent evidence or promotion contract
```

This is presentation metadata about the checked core certificate. Sage output
is not consumed by Core verification.

## Verification

Focused checks cover:

- one constructor call per lab instance;
- exact JSON-ready presentation fields;
- fresh returned dictionaries;
- rejection of wrong or subclassed certificate objects;
- four lowering/VAMI replay lanes;
- exactly one public R12.5 report call;
- fail-closed certificate behavior;
- certificate-suite count 71 and public Sage API count 91.

Run:

```bash
python -m pytest -q \
  tests/certificates/test_certify_intrinsic_vam.py \
  tests/sage/test_veyra_sage_intrinsic_vam.py \
  tests/shadows/test_certify.py \
  tests/sage/test_veyra_sage_api_index.py \
  tests/kernel/test_essence_core.py::test_essence_report_does_not_eagerly_replay_expensive_summary
```

No new notation or theorem registry row is required: R12.6 integrates the
existing `THM-R12-001..009` bridge.

Final post-review direct certificate replay passed in 387 seconds. Cheap
focused checks pass `11/11`; Ruff, targeted mypy, `py_compile`, diff, and
hygiene pass. Independent final review reports no remaining finding.

## Non-claims

R12.6 does **not**:

- authenticate R12.3 receipts;
- prove VAMI parsing, CRC, malformed-input, or resource-limit logic in Lean;
- widen preservation beyond the valid lowering image;
- add reflection or equivalence;
- add or renew an R8 promotion contract;
- change the four-row R12.1 registry;
- change the `1 / 4 / 25 / 5` taxonomy or `proof_complete`;
- change legacy VAM0/VAMD or notebook artifacts.

R12 is integration-complete after this gate, but the foundational kernel is
not release-complete: R13, R14, and the final K0 serial release baseline remain
open.
