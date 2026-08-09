"""Arithmetic-derived finite source and exact symbolic provenance for P3-N2."""

from __future__ import annotations

import logging

from ...observer.network.core import NETWORK_VERSION
from ...observer.network.validation import snapshot_network_source
from ...padic.completion.doctrine import snapshot_doctrine
from ...padic.completion.formal import (
    ARTIFACT_PATH as P2_PATH, ARTIFACT_SHA256 as P2_SHA, ELAN_SHA256,
    LEAN_BINARY_SHA256, LEAN_VERSION,
)
from ...padic.completion.prime import snapshot_prime
from ...padic.family_introduction.sources import (
    ARTIFACT_PATH as N1_PATH, ARTIFACT_SHA256 as N1_SHA, TOOLCHAIN_ID,
    n1_theorem_source, snapshot_theorem as snapshot_n1,
)
from .common import digest, exact_int, reject
from .p3t import arithmetic_p3t_source
from .types import (
    DepthNode, FamilyCoordinate, FiniteFamilySource, FiniteReductionSource,
    N2Ledger, N2Policy, N2TheoremSource, PrimePowerReductionPackage,
    ReductionArrowSource, ReductionRow,
)

logger = logging.getLogger(__name__)
FINITE_VERSION = "p3n2-finite-v1"
FORMAL_VERSION = "p3n2-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerReductionNetwork.lean"
ARTIFACT_SHA256 = "77f5a9891115122967036b99245cf410662d251bdf92f79da150f384cb2410cf"
THEOREM_IDS = tuple(f"THM_P3N2_00{i}_{name}" for i, name in enumerate((
    "reduction_identity", "reduction_composition", "reduction_witness_independent",
    "path_equality", "rho_square", "separator_coarse", "separator_fine",
), 1))
AXIOM_ROWS = (
    (THEOREM_IDS[0], ("propext", "Quot.sound")),
    (THEOREM_IDS[1], ("propext", "Quot.sound")),
    (THEOREM_IDS[2], ("Quot.sound",)),
    (THEOREM_IDS[3], ("propext", "Quot.sound")),
    (THEOREM_IDS[4], ()), (THEOREM_IDS[5], ("propext",)),
    (THEOREM_IDS[6], ("propext", "Classical.choice", "Quot.sound")),
)
TCB_DIGEST = digest("veyra.p3n2.tcb.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
    ("process", b"fresh-private-three-source-compile-live-cap"),
))
LEDGER_ROWS = (
    "natural-numbers", "integers", "dependent-functions", "propositions-equality",
    "propext", "Quot.sound", "Classical.choice", "lean-kernel", "pinned-toolchain",
    "private-bounded-compiler", "Fin.intCast", "Fin.ext", "Nat.mod_mod_of_dvd",
    "VeyraPrimeWitness", "veyraModulus", "VeyraZMod", "veyraReduce",
    "VeyraCompatibleFamily", "veyraRho", "THM_POMEGA2_004_reduction_identity",
    "THM_POMEGA2_005_reduction_composition", "veyraIntegerResidue",
    "THM_P3N1_002_integer_residue_reduction", "veyraIntegerFamily",
    "VeyraReductionArrow", "veyraReductionArrowMap", "VeyraReductionPath",
    "veyraReductionPathComparable", "veyraReductionPathMap",
    "veyraReductionPathMap_canonical", *THEOREM_IDS,
)
LEDGER_EDGES = (
    ("Fin.intCast", "integers"), ("Fin.ext", "natural-numbers"),
    ("Nat.mod_mod_of_dvd", "natural-numbers"),
    ("VeyraPrimeWitness", "natural-numbers"), ("veyraModulus", "natural-numbers"),
    ("VeyraZMod", "veyraModulus"), ("veyraReduce", "VeyraZMod"),
    ("VeyraCompatibleFamily", "dependent-functions"),
    ("VeyraCompatibleFamily", "veyraReduce"), ("veyraRho", "VeyraCompatibleFamily"),
    ("THM_POMEGA2_004_reduction_identity", "veyraReduce"),
    ("THM_POMEGA2_004_reduction_identity", "Fin.ext"),
    ("THM_POMEGA2_005_reduction_composition", "veyraReduce"),
    ("THM_POMEGA2_005_reduction_composition", "Nat.mod_mod_of_dvd"),
    ("veyraIntegerResidue", "Fin.intCast"), ("veyraIntegerResidue", "VeyraZMod"),
    ("THM_P3N1_002_integer_residue_reduction", "veyraIntegerResidue"),
    ("THM_P3N1_002_integer_residue_reduction", "Nat.mod_mod_of_dvd"),
    ("veyraIntegerFamily", "veyraIntegerResidue"),
    ("veyraIntegerFamily", "VeyraCompatibleFamily"),
    ("veyraIntegerFamily", "THM_P3N1_002_integer_residue_reduction"),
    ("VeyraReductionArrow", "natural-numbers"),
    ("veyraReductionArrowMap", "VeyraReductionArrow"),
    ("veyraReductionArrowMap", "veyraReduce"),
    ("VeyraReductionPath", "natural-numbers"),
    ("veyraReductionPathComparable", "VeyraReductionPath"),
    ("veyraReductionPathMap", "veyraReductionPathComparable"),
    ("veyraReductionPathMap", "veyraReductionArrowMap"),
    ("veyraReductionPathMap_canonical", "veyraReductionPathMap"),
    (THEOREM_IDS[0], "veyraReductionArrowMap"),
    (THEOREM_IDS[0], "THM_POMEGA2_004_reduction_identity"),
    (THEOREM_IDS[1], "Nat.mod_mod_of_dvd"), (THEOREM_IDS[1], "veyraReductionArrowMap"),
    (THEOREM_IDS[1], "THM_POMEGA2_005_reduction_composition"),
    (THEOREM_IDS[2], "Fin.ext"), (THEOREM_IDS[2], "veyraReductionArrowMap"),
    (THEOREM_IDS[3], THEOREM_IDS[2]), (THEOREM_IDS[3], THEOREM_IDS[1]),
    (THEOREM_IDS[3], "veyraReductionPathMap_canonical"),
    (THEOREM_IDS[4], "veyraRho"),
    (THEOREM_IDS[4], "VeyraCompatibleFamily"),
    (THEOREM_IDS[5], "veyraIntegerFamily"), (THEOREM_IDS[5], "Fin.ext"),
    (THEOREM_IDS[6], "veyraIntegerFamily"), (THEOREM_IDS[6], "veyraModulus"),
    ("pinned-toolchain", "lean-kernel"),
    ("private-bounded-compiler", "pinned-toolchain"),
    *((name, "private-bounded-compiler") for name in THEOREM_IDS),
)
LEDGER_DIGEST_ORACLE = "2c4cad693acc80b78d33ababff5afbc102d30f018f533957973a0e41019b91e9"
HARD = (4 * 1024 * 1024, 12 * 1024 * 1024, 32, 1024, 100_000, 4 * 1024 * 1024, 300)


def _rows(label: str, values) -> tuple[tuple[str, bytes], ...]:
    """Make stable indexed digest rows."""
    logger.debug("_rows entry label=%s", label)
    result = tuple((f"{label}-{i}", str(value).encode()) for i, value in enumerate(values))
    logger.debug("_rows exit count=%d", len(result))
    return result


def finite_reduction_source(prime, doctrine, depths=(0, 1, 2),
                            family_integers=None) -> FiniteReductionSource:
    """Derive every map row and required separator family from p and exact depths."""
    logger.debug("finite_reduction_source entry")
    p, d = snapshot_prime(prime), snapshot_doctrine(doctrine)
    if type(depths) is not tuple or not depths or len(depths) > HARD[2]:
        reject("finite-depth-shape-invalid")
    ds = tuple(exact_int(x, "finite-depth", maximum=64) for x in depths)
    if tuple(sorted(set(ds))) != ds:
        reject("finite-depth-order-or-duplicate-invalid")
    estimated_rows = sum(p.p ** (fine + 1) for fine in ds for coarse in ds
                         if coarse <= fine)
    if estimated_rows > HARD[4]:
        reject("finite-table-hard-envelope")
    nodes = tuple(DepthNode(n, p.p ** (n + 1), digest("veyra.p3n2.node.v1", (
        ("p", p.source_digest.encode()), ("depth", n.to_bytes(2, "big")),
    ))) for n in ds)
    if family_integers is None:
        integers = (0, *(p.p ** (m + 1) for m in ds[:-1]))
    else:
        if (type(family_integers) is not tuple or not family_integers
                or len(family_integers) > 1024
                or any(type(z) is not int or z.bit_length() > 4096 for z in family_integers)
                or len(set(family_integers)) != len(family_integers)):
            reject("finite-family-integer-scope-invalid")
        integers = family_integers
    arrow_count = sum(1 for fine in ds for coarse in ds if coarse <= fine)
    if estimated_rows + len(integers) * len(ds) + arrow_count > HARD[4]:
        reject("finite-source-node-hard-envelope")
    families = []
    for z in integers:
        coords = tuple(FamilyCoordinate(n, z % node.modulus, digest(
            "veyra.p3n2.coordinate.v1", (("z", str(z).encode()), ("node", node.node_digest.encode())),
        )) for n, node in zip(ds, nodes, strict=True))
        fd = digest("veyra.p3n2.family.v1", (("z", str(z).encode()), *_rows("coordinate", (x.coordinate_digest for x in coords))))
        families.append(FiniteFamilySource(f"integer:{z}", z, coords, fd))
    arrows = []
    for fine in ds:
        for coarse in ds:
            if coarse > fine:
                continue
            source_modulus, target_modulus = p.p ** (fine + 1), p.p ** (coarse + 1)
            rows = tuple(ReductionRow(x, x % target_modulus, digest(
                "veyra.p3n2.map-row.v1", (("fine", str(fine).encode()),
                ("coarse", str(coarse).encode()), ("x", str(x).encode()),
                ("y", str(x % target_modulus).encode())),
            )) for x in range(source_modulus))
            ad = digest("veyra.p3n2.arrow.v1", (("p", p.source_digest.encode()),
                ("fine", str(fine).encode()), ("coarse", str(coarse).encode()),
                *_rows("row", (x.row_digest for x in rows))))
            arrows.append(ReductionArrowSource(fine, coarse, rows, ad))
    binding = digest("veyra.p3n2.arithmetic-p3t-binding.v1", (
        ("p", p.source_digest.encode()), ("doctrine", d.doctrine_digest.encode()),
        *_rows("node", (x.node_digest for x in nodes)),
        *_rows("family", (x.family_digest for x in families)),
    ))
    p3t = snapshot_network_source(arithmetic_p3t_source(p, d, nodes, tuple(families), binding))
    sd = digest("veyra.p3n2.finite-source.v1", (("p", p.source_digest.encode()),
        ("doctrine", d.doctrine_digest.encode()), ("p3t", p3t.network_digest.encode()),
        *_rows("node", (x.node_digest for x in nodes)),
        *_rows("family", (x.family_digest for x in families)),
        *_rows("arrow", (x.arrow_digest for x in arrows))))
    result = FiniteReductionSource(FINITE_VERSION, p.source_digest, d.doctrine_digest,
        NETWORK_VERSION, p3t, nodes, tuple(families), tuple(arrows), sd)
    logger.debug("finite_reduction_source exit arrows=%d", len(arrows))
    return result


def theorem_source() -> N2TheoremSource:
    """Bind exact raw PΩ2/N1/N2 bytes without any completion judgment."""
    logger.debug("theorem_source entry")
    value = digest("veyra.p3n2.theorem-source.v1", (("p2", P2_SHA.encode()),
        ("n1", N1_SHA.encode()), ("n2", ARTIFACT_SHA256.encode()),
        *_rows("theorem", THEOREM_IDS), ("toolchain", TOOLCHAIN_ID.encode()),
        ("tcb", TCB_DIGEST.encode())))
    result = N2TheoremSource(FORMAL_VERSION, P2_PATH, P2_SHA, N1_PATH, N1_SHA,
        ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS, TOOLCHAIN_ID, TCB_DIGEST, value)
    logger.debug("theorem_source exit")
    return result


def n2_ledger() -> N2Ledger:
    """Construct the ordered transitive used-source ledger."""
    logger.debug("n2_ledger entry")
    value = digest("veyra.p3n2.ledger.v1", (*_rows("row", LEDGER_ROWS),
        *_rows("edge", (f"{a}\0{b}" for a, b in LEDGER_EDGES)),
        *_rows("axiom", (f"{a}|{','.join(b)}" for a, b in AXIOM_ROWS))))
    if value != LEDGER_DIGEST_ORACLE:
        raise RuntimeError("internal P3-N2 ledger oracle drift")
    positions = {name: index for index, name in enumerate(LEDGER_ROWS)}
    if (len(positions) != len(LEDGER_ROWS)
            or any(source not in positions or dependency not in positions
                   or positions[dependency] >= positions[source]
                   for source, dependency in LEDGER_EDGES)):
        raise RuntimeError("internal P3-N2 ledger order/cycle drift")
    result = N2Ledger("p3n2-ledger-v1", LEDGER_ROWS, LEDGER_EDGES, AXIOM_ROWS, value)
    logger.debug("n2_ledger exit rows=%d edges=%d", len(LEDGER_ROWS), len(LEDGER_EDGES))
    return result


def n2_policy(max_captured_bytes=HARD[0], max_static_cost=HARD[1], max_depths=8,
              max_arrows=64, max_table_rows=10_000, max_output_bytes=1024 * 1024,
              timeout_seconds=120) -> N2Policy:
    """Create typed hard-first caps."""
    logger.debug("n2_policy entry")
    values = (max_captured_bytes, max_static_cost, max_depths, max_arrows,
              max_table_rows, max_output_bytes, timeout_seconds)
    if any(type(x) is not int or not 1 <= x <= cap for x, cap in zip(values, HARD, strict=True)):
        reject("n2-policy-invalid")
    pd = digest("veyra.p3n2.policy.v1", _rows("cap", values))
    result = N2Policy("p3n2-policy-v1", *values, pd)
    logger.debug("n2_policy exit")
    return result


def reduction_network_package(prime, doctrine, finite, n1, theorem, ledger, policy):
    """Build a raw-only package and reject foreign identities."""
    logger.debug("reduction_network_package entry")
    p, d = snapshot_prime(prime), snapshot_doctrine(doctrine)
    if type(finite) is not FiniteReductionSource:
        reject("finite-reduction-source-exact-type-required")
    expected_f = finite_reduction_source(p, d, tuple(x.depth for x in finite.depths),
                                         tuple(x.integer for x in finite.families))
    if finite != expected_f:
        reject("finite-reduction-source-drift")
    n1v = snapshot_n1(n1)
    tv, lv = theorem_source(), n2_ledger()
    if theorem != tv or ledger != lv or n1v.artifact_sha256 != tv.n1_sha256:
        reject("theorem-ledger-continuity-drift")
    if type(policy) is not N2Policy:
        reject("n2-policy-exact-type-required")
    pv = n2_policy(*tuple(object.__getattribute__(policy, x) for x in (
        "max_captured_bytes", "max_static_cost", "max_depths", "max_arrows",
        "max_table_rows", "max_output_bytes", "timeout_seconds")))
    if type(policy) is not N2Policy or policy != pv:
        reject("n2-policy-drift")
    value = digest("veyra.p3n2.package.v1", (("p", p.source_digest.encode()),
        ("doctrine", d.doctrine_digest.encode()), ("finite", finite.source_digest.encode()),
        ("n1", n1v.source_digest.encode()), ("theorem", tv.source_digest.encode()),
        ("ledger", lv.ledger_digest.encode()), ("policy", pv.policy_digest.encode())))
    result = PrimePowerReductionPackage(p, d, finite, n1v, tv, lv, pv, value)
    logger.debug("reduction_network_package exit")
    return result


def exact_n1_theorem_source():
    """Expose raw N1 theorem source, never an N1 judgment."""
    logger.debug("exact_n1_theorem_source entry")
    result = n1_theorem_source()
    logger.debug("exact_n1_theorem_source exit")
    return result
