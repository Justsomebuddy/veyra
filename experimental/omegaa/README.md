# Experimental Omega-A

Omega-A is an isolated research prototype for a possible finite kernel-checker
architecture. It is published for inspection, testing, criticism, and future
work. It is **not stable Veyra Core**.

## Exact status

- KPT1, KCA1, KCC1, KCI1, KEB1, KCF1, and KIE1 are syntax,
  serialization, continuation, binding, or preparation prerequisites and
  prototypes. Focused checks exist for their exact finite contracts.
- KCS1 is unfinished. Its design was amended, but the implementation did not
  reach a final accepted state.
- KEC1 has unresolved architectural findings involving input traversal,
  immutable snapshots, work ordering, resource accounting, source identity,
  error locations, coverage, and diagnostics.
- KCK1 has no implementation in this tree.
- There is no complete kernel checker, checker-soundness theorem, authority
  rule, registry admission, production API, or Omega-A release.
- A passing experimental check does not change any of those statuses.

## Isolation boundary

This directory is deliberately separate from `src/core/`:

- `veyra-core` does not install it;
- the stable root package does not import or export it;
- the stable certificate registry does not include it;
- default `make test` and `make verify` do not collect its tests;
- source hygiene uses a 1000-line target throughout the repository; any
  path-bound exception must explain why splitting would reduce readability and
  remains subject to the absolute 2000-line maximum.

The files under `src/core/` and `tests/` preserve the original research bytes.
The two small namespace files only allow the preserved `src.core.*` imports to
resolve when checks are launched from this directory.

## Inspection

From the repository root:

```bash
make omegaa-collect
```

The command performs collection only. To inspect an individual focused file:

```bash
cd experimental/omegaa
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH=. python -m pytest -p no:cacheprovider -q \
  tests/test_omegaa_kpt1_codec.py
```

Failures belong to the experimental surface and do not imply a stable-Core
regression. Likewise, success is finite implementation evidence only; it is not
soundness, consistency, external truth, objecthood, or completed infinity.

## Conceptual map

The non-release conceptual ladder is documented in
[`../../docs/156_omegaa_semantic_authority_ladder.md`](../../docs/156_omegaa_semantic_authority_ladder.md).
It separates representation, preparation, inert state, calculus, quotation,
execution, interpretation, soundness, and adoption instead of treating them as
one automatic promotion.
