"""Pinned closed program, theorem continuity, ledger, and policy for P3-A1b."""

from __future__ import annotations

import logging

from ...padic.completion.formal import ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION
from ...padic.family_introduction.sources import (
    ARTIFACT_PATH as N1_PATH, ARTIFACT_SHA256 as N1_SHA,
    TOOLCHAIN_ID, n1_theorem_source,
)
from ...padic.completion.formal import ARTIFACT_PATH as P2_PATH, ARTIFACT_SHA256 as P2_SHA
from ...padic.completion.prime import snapshot_prime
from ...padic.family_introduction.sources import snapshot_integer
from .common import (
    digest, exact_digest, exact_int, exact_shape, exact_text, reject,
)
from .types import (
    BridgeLedger, BridgePolicy, BridgeTheoremSource, ResidueProgramSource,
)

logger = logging.getLogger(__name__)
PROGRAM_VERSION = "p3a1b-program-v1"
PROGRAM_CONSTRUCTOR = "PRIME_POWER_RESIDUE(integer_source,prime_source)"
PROGRAM_GRAMMAR_ID = "closed-one-constructor-target-free-v1"
FORMAL_VERSION = "p3a1b-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerProductiveBridge.lean"
ARTIFACT_SHA256 = "f0382dee0f2f0fe9434feca7357a25abd27f47d5f16b278302d83f7d31d0382e"
THEOREM_IDS = (
    "THM_P3A1B_001_total", "THM_P3A1B_002_deterministic",
    "THM_P3A1B_003_process_coherent", "THM_P3A1B_004_commutes",
)
AXIOM_ROWS = (
    (THEOREM_IDS[0], ()), (THEOREM_IDS[1], ()),
    (THEOREM_IDS[2], ("propext",)), (THEOREM_IDS[3], ("propext",)),
)
TCB_DIGEST = digest("veyra.p3a1b.tcb.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
    ("process", b"fresh-three-dependency-private-live-cap"),
))
LEDGER_ROWS = (
    "natural-numbers", "integers", "dependent-functions", "propositions-equality",
    "propext", "lean-kernel", "pinned-toolchain", "private-bounded-compiler",
    "Fin.intCast", "Fin.ofNat", "Fin.ext", "Nat.mod_mod_of_dvd",
    "VeyraPrimeWitness", "veyraModulus", "veyraModulusPos", "VeyraZMod", "veyraReduce",
    "veyraModulusDvd", "veyraCanonicalStageRingLaws", "veyraIntegerResidue",
    "veyraIntegerFamily", "veyraResidueProgramOutput", "veyraResidueProgramEval",
    *THEOREM_IDS,
)
LEDGER_EDGES = (
    ("Fin.intCast", "integers"), ("Fin.intCast", "natural-numbers"),
    ("Fin.ofNat", "natural-numbers"), ("Fin.ext", "natural-numbers"),
    ("Nat.mod_mod_of_dvd", "natural-numbers"),
    ("VeyraPrimeWitness", "natural-numbers"), ("veyraModulus", "natural-numbers"),
    ("veyraModulusPos", "VeyraPrimeWitness"), ("veyraModulusPos", "veyraModulus"),
    ("VeyraZMod", "veyraModulus"), ("veyraReduce", "VeyraZMod"),
    ("veyraModulusDvd", "veyraModulus"),
    ("veyraCanonicalStageRingLaws", "veyraReduce"),
    ("veyraCanonicalStageRingLaws", "propext"),
    ("veyraIntegerResidue", "integers"), ("veyraIntegerResidue", "VeyraZMod"),
    ("veyraIntegerFamily", "veyraIntegerResidue"),
    ("veyraResidueProgramOutput", "integers"),
    ("veyraResidueProgramOutput", "VeyraPrimeWitness"),
    ("veyraResidueProgramOutput", "veyraModulus"),
    ("veyraResidueProgramOutput", "veyraModulusPos"),
    ("veyraResidueProgramOutput", "VeyraZMod"),
    ("veyraResidueProgramOutput", "Fin.intCast"),
    ("veyraResidueProgramEval", "VeyraPrimeWitness"),
    ("veyraResidueProgramEval", "VeyraZMod"),
    ("veyraResidueProgramEval", "veyraResidueProgramOutput"),
    (THEOREM_IDS[0], "VeyraPrimeWitness"), (THEOREM_IDS[0], "VeyraZMod"),
    (THEOREM_IDS[0], "veyraResidueProgramEval"),
    (THEOREM_IDS[1], "VeyraPrimeWitness"), (THEOREM_IDS[1], "VeyraZMod"),
    (THEOREM_IDS[1], "veyraResidueProgramEval"),
    (THEOREM_IDS[2], "VeyraPrimeWitness"), (THEOREM_IDS[2], "VeyraZMod"),
    (THEOREM_IDS[2], "veyraResidueProgramEval"),
    (THEOREM_IDS[2], "veyraReduce"),
    (THEOREM_IDS[2], "veyraModulus"), (THEOREM_IDS[2], "veyraModulusPos"),
    (THEOREM_IDS[2], "veyraModulusDvd"),
    (THEOREM_IDS[2], "veyraCanonicalStageRingLaws"),
    (THEOREM_IDS[2], "Fin.intCast"), (THEOREM_IDS[2], "Fin.ofNat"),
    (THEOREM_IDS[2], "Fin.ext"), (THEOREM_IDS[2], "Nat.mod_mod_of_dvd"),
    (THEOREM_IDS[3], "VeyraPrimeWitness"),
    (THEOREM_IDS[3], "veyraResidueProgramEval"),
    (THEOREM_IDS[3], "veyraIntegerFamily"),
    ("pinned-toolchain", "lean-kernel"),
    ("private-bounded-compiler", "pinned-toolchain"),
    *((name, "private-bounded-compiler") for name in THEOREM_IDS),
)
LEDGER_DIGEST_ORACLE = "dfe14dea35d8b0de163470e22a31675844909859b7fe96692e4de016f350f4da"
HARD_SOURCE_BYTES = 3 * 1024 * 1024
HARD_STATIC_COST = 8 * 1024 * 1024
HARD_DEPTH = 100_000
HARD_OUTPUT_BYTES = 4 * 1024 * 1024


def residue_program_source(prime, integer) -> ResidueProgramSource:
    """Construct the sole target-free positive term with exact p/z binding."""
    logger.debug("residue_program_source entry")
    p = snapshot_prime(prime)
    z = snapshot_integer(integer)
    value = digest("veyra.p3a1b.program.v1", (
        ("version", PROGRAM_VERSION.encode()), ("constructor", PROGRAM_CONSTRUCTOR.encode()),
        ("grammar", PROGRAM_GRAMMAR_ID.encode()),
        ("prime", p.source_digest.encode()), ("integer", z.source_digest.encode()),
    ))
    result = ResidueProgramSource(
        PROGRAM_VERSION, PROGRAM_CONSTRUCTOR, PROGRAM_GRAMMAR_ID,
        p.source_digest, z.source_digest, value,
    )
    logger.debug("residue_program_source exit")
    return result


def snapshot_program(value: ResidueProgramSource) -> ResidueProgramSource:
    """Reject alternate constructors and hidden target-bearing programs."""
    logger.debug("snapshot_program entry")
    raw = exact_shape(value, ResidueProgramSource, "program")
    for name in ("version", "constructor", "grammar_id", "prime_digest", "integer_digest", "program_digest"):
        exact_text(raw[name], f"program-{name}")
    exact_digest(raw["program_digest"], "program-digest")
    for name in ("prime_digest", "integer_digest"):
        exact_digest(raw[name], name)
    computed = digest("veyra.p3a1b.program.v1", (
        ("version", raw["version"].encode()), ("constructor", raw["constructor"].encode()),
        ("grammar", raw["grammar_id"].encode()), ("prime", raw["prime_digest"].encode()),
        ("integer", raw["integer_digest"].encode()),
    ))
    expected = ResidueProgramSource(
        PROGRAM_VERSION, PROGRAM_CONSTRUCTOR, PROGRAM_GRAMMAR_ID,
        raw["prime_digest"], raw["integer_digest"], computed,
    )
    if value != expected:
        reject("program-source-drift")
    logger.debug("snapshot_program exit")
    return expected


def bridge_theorem_source() -> BridgeTheoremSource:
    """Bind exact PΩ2, direct N1, bridge bytes, toolchain, and theorem names."""
    logger.debug("bridge_theorem_source entry")
    value = digest("veyra.p3a1b.theorem-source.v1", (
        ("version", FORMAL_VERSION.encode()), ("artifact", ARTIFACT_PATH.encode()),
        ("artifact-sha", ARTIFACT_SHA256.encode()), ("n1", N1_PATH.encode()),
        ("n1-sha", N1_SHA.encode()), ("pomega2", P2_PATH.encode()),
        ("pomega2-sha", P2_SHA.encode()),
        *((f"theorem-{i}", x.encode()) for i, x in enumerate(THEOREM_IDS)),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode()),
    ))
    result = BridgeTheoremSource(
        FORMAL_VERSION, ARTIFACT_PATH, ARTIFACT_SHA256, N1_PATH, N1_SHA,
        P2_PATH, P2_SHA, THEOREM_IDS, TOOLCHAIN_ID, TCB_DIGEST, value,
    )
    logger.debug("bridge_theorem_source exit")
    return result


def snapshot_theorem(value: BridgeTheoremSource) -> BridgeTheoremSource:
    """Reject byte, theorem, dependency, or toolchain transplants."""
    logger.debug("snapshot_theorem entry")
    raw = exact_shape(value, BridgeTheoremSource, "bridge-theorem")
    for name in (
        "version", "artifact_path_id", "artifact_sha256", "n1_artifact_path_id",
        "n1_artifact_sha256", "pomega2_artifact_path_id", "pomega2_artifact_sha256",
        "toolchain_id", "tcb_digest", "source_digest",
    ):
        exact_text(raw[name], f"bridge-theorem-{name}")
    ids = raw["theorem_ids"]
    if type(ids) is not tuple or any(type(x) is not str for x in ids):
        reject("bridge-theorem-ids-invalid")
    for name in ("artifact_sha256", "n1_artifact_sha256", "pomega2_artifact_sha256", "tcb_digest", "source_digest"):
        exact_digest(raw[name], name)
    expected = bridge_theorem_source()
    if value != expected:
        reject("bridge-theorem-source-drift")
    logger.debug("snapshot_theorem exit")
    return expected


def bridge_ledger() -> BridgeLedger:
    """Construct the exact acyclic used-source ledger."""
    logger.debug("bridge_ledger entry")
    value = digest("veyra.p3a1b.ledger.v1", (
        *((f"row-{i}", x.encode()) for i, x in enumerate(LEDGER_ROWS)),
        *((f"edge-{i}", f"{a}\0{b}".encode()) for i, (a, b) in enumerate(LEDGER_EDGES)),
        *((f"axiom-{i}", f"{a}|{','.join(b)}".encode()) for i, (a, b) in enumerate(AXIOM_ROWS)),
    ))
    if value != LEDGER_DIGEST_ORACLE:
        logger.error("bridge_ledger literal oracle drift")
        raise RuntimeError("internal P3-A1b ledger oracle drift")
    result = BridgeLedger("p3a1b-ledger-v1", LEDGER_ROWS, LEDGER_EDGES, AXIOM_ROWS, value)
    logger.debug("bridge_ledger exit rows=%d edges=%d", len(LEDGER_ROWS), len(LEDGER_EDGES))
    return result


def snapshot_ledger(value: BridgeLedger) -> BridgeLedger:
    """Reject circular, missing, foreign, or reordered ledgers."""
    logger.debug("snapshot_ledger entry")
    raw = exact_shape(value, BridgeLedger, "bridge-ledger")
    exact_text(raw["version"], "bridge-ledger-version")
    exact_digest(raw["ledger_digest"], "ledger-digest")
    if type(raw["ordered_rows"]) is not tuple or any(type(x) is not str for x in raw["ordered_rows"]):
        reject("bridge-ledger-rows-invalid")
    for edge in raw["direct_edges"] if type(raw["direct_edges"]) is tuple else ():
        if type(edge) is not tuple or len(edge) != 2 or any(type(x) is not str for x in edge):
            reject("bridge-ledger-edges-invalid")
    if type(raw["direct_edges"]) is not tuple:
        reject("bridge-ledger-edges-invalid")
    rows = raw["theorem_axiom_rows"]
    if type(rows) is not tuple:
        reject("bridge-ledger-axioms-invalid")
    for row in rows:
        if (type(row) is not tuple or len(row) != 2 or type(row[0]) is not str
                or type(row[1]) is not tuple or any(type(x) is not str for x in row[1])):
            reject("bridge-ledger-axioms-invalid")
    expected = bridge_ledger()
    if value != expected:
        reject("bridge-ledger-drift")
    positions = {x: i for i, x in enumerate(value.ordered_rows)}
    if len(positions) != len(value.ordered_rows) or any(positions[b] >= positions[a] for a, b in value.direct_edges):
        reject("bridge-ledger-cycle-or-order-invalid")
    logger.debug("snapshot_ledger exit")
    return expected


def bridge_policy(max_captured_bytes=HARD_SOURCE_BYTES, max_static_cost=HARD_STATIC_COST,
                  max_depth=4096, max_output_bytes=1024 * 1024,
                  compile_timeout_seconds=120) -> BridgePolicy:
    """Construct hard-bounded formal and projection policy."""
    logger.debug("bridge_policy entry")
    values = (max_captured_bytes, max_static_cost, max_depth, max_output_bytes, compile_timeout_seconds)
    if any(type(x) is not int for x in values):
        reject("policy-exact-integers-required")
    hard = (HARD_SOURCE_BYTES, HARD_STATIC_COST, HARD_DEPTH, HARD_OUTPUT_BYTES, 300)
    if any(not 1 <= x <= cap for x, cap in zip(values, hard, strict=True)):
        reject("policy-value-invalid")
    value = digest("veyra.p3a1b.policy.v1", tuple((f"value-{i}", x.to_bytes(8, "big")) for i, x in enumerate(values)))
    result = BridgePolicy("p3a1b-policy-v1", *values, value)
    logger.debug("bridge_policy exit")
    return result


def snapshot_policy(value: BridgePolicy) -> BridgePolicy:
    """Reject policy subclasses, Booleans, and digest drift."""
    logger.debug("snapshot_policy entry")
    raw = exact_shape(value, BridgePolicy, "bridge-policy")
    exact_text(raw["version"], "bridge-policy-version")
    exact_digest(raw["policy_digest"], "policy-digest")
    names = ("max_captured_bytes", "max_static_cost", "max_depth", "max_output_bytes", "compile_timeout_seconds")
    values = tuple(exact_int(raw[name], f"bridge-policy-{name}") for name in names)
    expected = bridge_policy(*values)
    if value != expected:
        reject("bridge-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def exact_n1_theorem_source():
    """Return the canonical direct N1 theorem source, never its judgment."""
    logger.debug("exact_n1_theorem_source entry")
    result = n1_theorem_source()
    logger.debug("exact_n1_theorem_source exit")
    return result
