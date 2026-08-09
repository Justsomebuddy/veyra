# 47 — Veyra Sage School-Core Facade

**Status:** implemented seed.
**Layer:** Sage laboratory bridge for theorem/curriculum registries.
**Goal:** make the school-replacement stack visible as stable Sage-facing objects without collapsing it into ordinary `ZZ/QQ` math.

## Why this layer exists

The core already has theorem cards, dependency specs, curriculum nodes, and export rows.
Sage needs one clean access point so experiments can ask:

1. what Veyra theorem objects exist;
2. what school concepts are covered;
3. which concepts are missing;
4. what rows can be promoted into future Sage parents, categories, proof objects, or notebooks.

`VeyraSchoolCore` is that access point.

## Objects

| Object | Meaning | Source |
|---|---|---|
| `VeyraTheoremSpec` | Sage-facing immutable theorem wrapper | `src/core/registry/theorem_registry.py` |
| `VeyraCurriculumNode` | Sage-facing curriculum wrapper | `src/core/registry/curriculum_map.py` |
| `VeyraExportRow` | JSON-ready theorem/curriculum bridge row | `src/core/registry/depth_packs.py` |
| `VeyraSchoolCore` | facade combining all current school-core registries | `veyra_sage/school.py` |

## Current certified snapshot

The facade currently exposes:

- `19` theorem specs;
- `11` curriculum nodes;
- `0` missing school seed domains;
- `19` core Sage export rows;
- `38` facade export rows after theorem + curriculum wrapping.

This is not a complete 11-year school replacement yet. It is the first measured nucleus where every declared seed domain has at least one executable Veyra theorem/check object.

## Example

```python
from veyra_sage.all import VeyraSchoolCore

S = VeyraSchoolCore()
S.summary()
S.theorem_spec("pythagorean-separation")
S.curriculum_node("statistics")
rows = S.export_dicts()
```

Expected core signals:

```text
summary["curriculum_missing"] == 0
summary["theorem_specs"] == 19
len(rows) == 38
```

## Expansion rule

We do **not** patch upstream Sage first.
We expand `veyra_sage` as a project-local research package, prove useful objects here, then only later decide whether any part deserves a Sage extension package or upstream contribution.

Promotion path:

1. executable Veyra core object;
2. theorem/curriculum registry spec;
3. `VeyraSchoolCore` export row;
4. Sage-facing parent/category/proof object;
5. notebook/lab benchmark;
6. only then consider a Sage library package.

## Verification

Executable checks:

- `tests/sage/test_veyra_sage_school.py` — facade summary, lookup, export rows.
- `tests/sage/test_veyra_sage.py` — certificate suite now includes `sage_school_passed`.
- `scripts/sage_smoke.py` — smoke now checks school-core facade in Python/Sage mode.
