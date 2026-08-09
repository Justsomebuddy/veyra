# Science-domain certificate seed

## Status

Sprint J bounded science-domain seed. This is not a physics engine, network theory, or biological model; it is a finite certificate layer showing how Veyra admits measurable science-facing observers only through exact rows and obstruction cards.

## Executable files

| Surface | File | Certificate |
|---|---|---|
| Finite science rows | `src/core/shadows/science_certificates.py` | `science_domain_certificates` |
| Certificate hook | `src/core/certificates/science.py` | `certify_science_domain_certificates()` |
| Tests | `tests/shadows/test_science_certificates.py` | 6 targeted tests |

## Rows

### Conservation row

`finite_conservation_row("two-cell-transfer", (3,1), (2,2))` records:

- before total: `4`;
- after total: `4`;
- status: `conserved`;
- obstruction: `none`.

This is a finite conserved-total observer, not a universal conservation law.

### Network flow balance

`finite_flow_balance_row("source-sink-network", ...)` records a source/sink network:

| Node | Balance |
|---|---:|
| `source` | `-5` |
| `a` | `0` |
| `b` | `0` |
| `sink` | `5` |

The row status is `boundary-balanced`: internal nodes are balanced and only declared boundary nodes carry imbalance.

### Diffusion smoothing

`finite_diffusion_row("two-cell-average", (0,1), (1/2,1/2))` records max-minus-min variation contraction:

- before variation: `1`;
- after variation: `0`;
- status: `smoothed`.

### Anti-diffusion obstruction

`anti_diffusion_obstruction_card()` records a variation-increasing update from `(1/2,1/2)` to `(0,1)`:

- relation: `blocked`;
- obstruction: `variation-growth`.

This prevents a pretty “diffusion” story from accepting anti-diffusion as a valid smoothing certificate.

## Definition ledger

| ID | Meaning |
|---|---|
| `DEF-J1` | `ConservationRow` is a finite before/after conserved-total certificate. |
| `DEF-J2` | `FlowEdge` is a directed nonnegative exact finite flow amount. |
| `DEF-J3` | `FlowBalanceRow` records node imbalances and boundary-only balance status. |
| `DEF-J4` | `DiffusionRow` records whether variation contracts under a finite update. |
| `LEM-J1` | The canonical two-cell transfer conserves total `4`. |
| `LEM-J2` | The canonical source/sink flow has zero internal imbalance and total imbalance `0`. |
| `LEM-J3` | The canonical averaging update contracts variation from `1` to `0`. |
| `OBS-J1` | The anti-diffusion fixture increases variation and is blocked by `variation-growth`. |

## Verification

After this seed, Essence/Core has 24 executable layers and the certificate suite has 31 rows. Verified on 2026-06-06: targeted science/core/Sage/certify tests passed `23/23`; full the complete verification suite passed with pytest `369/369`, certificates `31/31`, Sage smoke ok, doctest `41/41`, and hygiene clean.
