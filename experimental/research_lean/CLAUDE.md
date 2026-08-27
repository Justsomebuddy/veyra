# Research Lean module memory

Version: **0.1.1**. Status: **`INTERNAL_RESEARCH_CANDIDATE`**.

- `manifest.json` is canonical: exactly 49 stable dependencies, eight research
  sources, 65 declarations, 33 literal headline claim rows, 65 axiom-closure
  rows, and domain-separated aggregate roots.
- `scripts/check_research_lean.py` always uses a fresh temporary snapshot and
  `.olean` tree, exact toolchain version/commit, bounded work, token-aware
  scanning, generated declaration audit, and final original-source rehash.
  Never add a persistent correctness cache.
- Research declarations do not change stable theorem IDs or statuses.
  THM-001–003 remain `CONJECTURE`.
- Shadow scope is the unary `Recurrence` image only; number theory is classical
  `Nat`/`Int`, not native Veyra arithmetic.

## Session Notes (2026-08-14)

- Integrated PR #40 as an isolated manifest-bound candidate.
- Renamed T008 from an independence claim to cross-product reassociation.
- Renewed only the changed stable `VeyraProofElaboration.lean` digest plus the
  derived base/proof roots after PR #37; the research root and candidate
  theorem/claim/axiom/toolchain inventories remain byte-for-byte unchanged.
