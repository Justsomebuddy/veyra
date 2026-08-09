# Semantic Shadow Certificates

**Date:** 2026-07-07
**Status:** Sprint X1 closed as executable semantic-shadow expansion.
**Implementation:** `src/core/language/__init__.py`, `src/core/registry/proof_discipline.py`, `veyra_sage/proof_discipline.py`.
**Certificate:** `proof_discipline` in `src/core/certify.py`.

## Purpose

Veyra treats school domains as declared observer projections, not as native truth. Sprint X1 extends the proof-discipline shadow ledger beyond arithmetic, geometry, and logic into analysis, topology, probability, and statistics.

## Declared shadow domains

| Domain | Required keys | Meaning |
|---|---|---|
| arithmetic | `length` | tact-count shadow of a mode |
| geometry | `boundary` | first/last nod boundary shadow |
| logic | `status` | inference readiness/obstruction shadow |
| analysis | `length`, `variation` | finite variation proxy over a mode |
| topology | `component_count`, `deformation_class` | boundary plus finite nod-support invariant |
| probability | `sample_space`, `sample_size` | finite outcome support exposed from nod labels |
| statistics | `sample_size`, `support_size` | finite sample/support counters |

## Certificate rule

Each `SemanticDomainRow` is accepted only when:

1. the accepted source type-checks as `ready`;
2. all required keys are present in `semantic_shadow(source, domain)`;
3. the shared trace-mismatch counterexample remains `blocked`;
4. the row status is `declared-shadow`.

This prevents a domain from entering the ledger as an assumed human category. It must expose concrete observer keys and a counterexample boundary.

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q tests/language/test_core_language.py tests/proof/test_proof_discipline.py tests/sage/test_veyra_sage_proof_discipline.py tests/shadows/test_certify.py tests/sage/test_veyra_sage.py
```

Expected X1 signals:

- `semantic_domain_coverage()` returns 7 rows.
- `proof_discipline_summary()` reports `domains=7` and `domain_certs=7`.
- `proof_discipline` certificate still passes.
