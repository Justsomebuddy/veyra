# Changelog

## [Unreleased]
### Changed
- Grouped `src/core` by subject and mirrored that layout in `tests/`. Digest-pinned
  modules remain in place; former flat imports resolve to the canonical module
  object through one compatibility map.
- Centralized repository paths in `src/core/paths.py`, removed cwd and directory-
  depth assumptions, and made the supported interpreter range CPython 3.11 or
  newer. Platform-specific proof operations now fail closed when their host or
  toolchain is unavailable.
- Added a Nix flake and CI across Linux, macOS, Windows, and the supported Python
  versions. Certificate factories now report individual unavailable toolchains
  without hiding failures in the rest of the suite.
- Organized durable documentation under `docs/concepts/`, registries under
  `docs/reference/`, and sprint reports under `docs/log/`. Broken links and
  source references are checked; the documentation entry point is hand-written.
- Removed file-length limits. Modules are split only at conceptual boundaries,
  and a large cohesive module is valid.
- Renewed the per-file and handler digests affected by portability changes. The
  aggregate Lean binding digests still require review and renewal on Linux with
  the pinned toolchain.
## [4.3.1] 2026-08-09 — Publication-ready public root
- Consolidated a portable clean-history tree for the dedicated `Justsomebuddy/veyra` repository with public controls, reproducible gates, corrected cache-ignore probes, and an explicit cautious commit/push/documentation policy; removed private paths, credentials, local automation metadata, generated artifacts, and retired cryptographic research; reconciled theorem/Lean evidence, notation, links, and status language without promotion; restored Omega-A only as an isolated experiment outside the stable package/default verification, with unfinished checker, soundness, and authority boundaries explicit.
## [4.3.0] 2026-08-08 — P3-N3/N4 local realization and scoped equality
- Released exact N1→PΩ2 realization and all-projection scoped carrier equality with 25 attacks, 48 aliases, bundle `13`, registry target `100`, focused `22/22`, direct L1, root `1836/1836`, zero promotions, and isolated strict GO.
- Serialized registry-100 and renewed isolated Lean axiom checks remain background evidence; no current full verify, generic completion, topology, absolute identity, N5 adoption, physical/metaphysical or foundation-independent infinity follows. The strict-reviewed ΩG philosophy separates relative, generic, and absolute completion (`GO 0/0/0/0`); the public closure framework keeps representation, interpretation, soundness, adoption, and typed infinity distinct without promotion. Unreleased ΩG1 remains only a two-instance non-generalization audit. Versions root/docs `4.2→4.3`, package/src `2.98→2.99`, core `2.37→2.38`, tests `3.46→3.47`.
## [4.2.0] 2026-08-07 — P3-N2 prime-power reduction observer network
- Released arithmetic-derived finite P3-T reductions, strict integer-family separators, and symbolic thin `Natᵒᵖ` identity/composition/comparison/observer-square/path coherence; focused `39/39`, public `1/1`, direct L1, isolated Lean SHA `77f5a989…10cf`, ledger `37/54`, oracle `2c4cad69…1e9`, attacks `23/23`, two refutations, one typed OPEN boundary, 56 aliases, root `1788/1788`, registry `99`, and zero promotions pass. Documentation separated six typed contracts and corrected stale C2/C3/C4/PΩ/N2 wording without promotion. No current full verify, N0/N3/N4/N5 instance, C2.3, inverse/generic network, or absolute objectivity follows. Versions root/docs `4.1→4.2`, package/src `2.97→2.98`, core `2.36→2.37`, tests `3.45→3.46`.
## [4.1.0] 2026-08-07 — P3-C2.2 exact finite generated transport coherence
- Released exact finite total setoid transport with `2` local commuting squares, `72` generated global fillers, semantic work `13307`, isolated Lean `3/3` at `4804c563…e395`, and a `23`-row/`41`-edge ledger at oracle `b634ea8c…e6cb`; cofinal boundary reconciliation is derived from C2.2. Focused `35/35`, public `1/1`, direct L1, 17 attacks, 57 collision-safe aliases, root `1732/1732`, registry `98`, static/LOC, zero promotions, and final review GO pass. NatOp is separate symbolic reduction algebra, not N2; no higher C2.3, Church–Rosser, path equality, absolute identity, objecthood, or current full verify. Versions root/docs `4.0→4.1`, package/src `2.96→2.97`, core `2.35→2.36`, tests `3.44→3.45`.
## [4.0.0] 2026-08-07 — P3-A1b exact prime-power productive bridge
- Released one closed `G_z(n)=z mod p^(n+1)`: THM001/002 totality/determinism, THM003 process coherence independent of N1, and THM004 exact all-depth commutation with direct `F_z`; isolated Lean `6/6`/`7/7` with pinned main/pressure sources, 27-row/53-edge ledger/oracle, and a total/coherent offset pressure refutation. Focused `49/49`, public `1/1`, direct L1, 56 collision-safe aliases, root `1675/1675`, registry `97`, static/LOC, zero promotions, and final review GO pass. No arbitrary productive conversion, choice/DC/coinduction/König, carrier/PΩ realization, physical/foundation-independent infinity, or current full verify. Versions root/docs `3.99→4.0`, package/src `2.95→2.96`, core `2.34→2.35`, tests `3.43→3.44`.

## Earlier releases

- [3.x](docs/releases/3.x.md) — 68 releases
- [2.x](docs/releases/2.x.md) — 15 releases
