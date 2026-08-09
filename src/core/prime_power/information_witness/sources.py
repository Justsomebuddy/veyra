"""Pinned source and hard policy for the isolated internal P3-N6-W runtime."""

from __future__ import annotations

import logging
from typing import cast

from .types import (
    N6WPolicyV1,
    N6WTheoremSourceV1,
    N6W_POLICY_LAYOUT,
    N6W_SOURCE_LAYOUT,
)
from ...prime_power_unbounded_common import (
    digest,
    exact_digest,
    exact_nonnegative_int,
    exact_shape,
    exact_text,
    reject,
)
from ...prime_power_unbounded_capability import N6_CAPABILITY_MODEL

logger = logging.getLogger(__name__)

ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerInformation.lean"
ARTIFACT_SHA256 = "f7a3a0fd6d21987d691261a348aebe9916fc564d23892872740546b49beb8b36"
THEOREM_IDS = (
    "THM_P3N6W_001_exact_shape",
    "THM_P3N6W_002_prefix",
    "THM_P3N6W_003_later",
    "THM_P3N6W_004_uniform",
)
AXIOM_ROWS = tuple((name, ("propext",)) for name in THEOREM_IDS)
N6E_INTERFACE_ROOT = "d33034fbf6a533f233fc0d6f054796bfa61bda0d8beeee5e2f9288ffad3e20df"
MAX_REQUESTED_DEPTH = 4096
MAX_PREFIX_ROWS = 1024
MAX_INTEGER_BITS = 4096


def theorem_source() -> N6WTheoremSourceV1:
    """Construct the sole exact N6-W theorem identity from literal bindings."""
    logger.debug("theorem_source entry")
    capability_model = "non-authoritative-public-parser-no-python-owner"
    if N6_CAPABILITY_MODEL != capability_model:
        logger.error("theorem_source N6 capability boundary drift")
        raise RuntimeError("internal N6 capability boundary drift")
    artifact_path = "proofs/lean/VeyraPrimePowerInformation.lean"
    artifact_sha = "f7a3a0fd6d21987d691261a348aebe9916fc564d23892872740546b49beb8b36"
    theorem_ids = (
        "THM_P3N6W_001_exact_shape", "THM_P3N6W_002_prefix",
        "THM_P3N6W_003_later", "THM_P3N6W_004_uniform",
    )
    axiom_rows = tuple((name, ("propext",)) for name in theorem_ids)
    n6_path = "proofs/lean/VeyraPrimePowerUnbounded.lean"
    n6_sha = "d35ead8dca26e0a07842ad830a143dab36b94b6ff201e79fd16dce9a81305b1c"
    n6e_root = "d33034fbf6a533f233fc0d6f054796bfa61bda0d8beeee5e2f9288ffad3e20df"
    toolchain = "leanprover/lean4:v4.30.0-rc2"
    base_tcb = "e348a6632186ea09c694c56d6eb79a5e728cb9f10ab0fbacd25dd18720c77568"
    rows = (
        ("version", b"p3n6w-formal-v1"),
        ("artifact", artifact_path.encode()),
        ("artifact-sha", artifact_sha.encode()),
        *((f"theorem-{index}", name.encode()) for index, name in enumerate(theorem_ids)),
        *((f"axiom-{index}", f"{name}\0propext".encode()) for index, name in enumerate(theorem_ids)),
        ("record", b"VeyraPrimePowerLateWitness"),
        ("constructor", b"veyraPrimePowerLateWitness"),
        ("direct-import-path", n6_path.encode()),
        ("direct-import-sha", n6_sha.encode()),
        ("n6e-interface-root", n6e_root.encode()),
        ("capability-model", capability_model.encode()),
        ("toolchain", toolchain.encode()),
    )
    tcb = digest("veyra.p3n6w.tcb.v1", (
        ("base-tcb", base_tcb.encode()),
        ("process", b"consume-n6e-replay-plus-private-four-source-continuity-v1"),
        ("external-runtime", b"lean-dso-init-std-loader-restored-swap-open"),
    ))
    source_digest = digest("veyra.p3n6w.theorem-source.v1", rows + (("tcb", tcb.encode()),))
    result = N6WTheoremSourceV1(
        "p3n6w-formal-v1", artifact_path, artifact_sha, theorem_ids,
        axiom_rows, "VeyraPrimePowerLateWitness",
        "veyraPrimePowerLateWitness", (n6_path, n6_sha),
        n6e_root, toolchain, tcb, source_digest,
    )
    logger.debug("theorem_source exit")
    return result


def _axiom_rows(value: object) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Validate a bounded exact theorem/axiom tuple without coercion."""
    logger.debug("_axiom_rows entry")
    if type(value) is not tuple or len(value) > 8:
        reject("n6w-source-axiom-rows-invalid")
    output: list[tuple[str, tuple[str, ...]]] = []
    for index, row in enumerate(cast(tuple[object, ...], value)):
        if type(row) is not tuple or len(row) != 2:
            reject(f"n6w-source-axiom-row-{index}-invalid")
        name, axioms = cast(tuple[object, object], row)
        exact_text(name, f"n6w-source-axiom-name-{index}")
        if type(axioms) is not tuple or len(axioms) > 4:
            reject(f"n6w-source-axiom-closure-{index}-invalid")
        checked = tuple(
            exact_text(item, f"n6w-source-axiom-{index}-{inner}")
            for inner, item in enumerate(cast(tuple[object, ...], axioms))
        )
        output.append((cast(str, name), checked))
    result = tuple(output)
    logger.debug("_axiom_rows exit rows=%d", len(result))
    return result


def snapshot_theorem_source(value: N6WTheoremSourceV1) -> N6WTheoremSourceV1:
    """Reject every source, theorem, base-interface, toolchain or TCB drift."""
    logger.debug("snapshot_theorem_source entry")
    raw = exact_shape(value, N6W_SOURCE_LAYOUT, "n6w-theorem-source")
    for name in (
        "version", "artifact_path_id", "record_definition_id",
        "constructor_definition_id", "toolchain_id",
    ):
        exact_text(raw[name], f"n6w-source-{name}")
    for name in (
        "artifact_sha256", "n6e_interface_root", "tcb_digest", "source_digest",
    ):
        exact_digest(raw[name], f"n6w-source-{name}")
    ids = raw["theorem_ids"]
    if type(ids) is not tuple or len(ids) > 8:
        reject("n6w-source-theorem-ids-invalid")
    for index, theorem_name in enumerate(cast(tuple[object, ...], ids)):
        exact_text(theorem_name, f"n6w-source-theorem-{index}")
    _axiom_rows(raw["theorem_axiom_rows"])
    direct = raw["direct_import"]
    if type(direct) is not tuple or len(direct) != 2:
        reject("n6w-source-direct-import-invalid")
    exact_text(direct[0], "n6w-source-direct-path")
    exact_digest(direct[1], "n6w-source-direct-sha")
    expected = theorem_source()
    if raw != exact_shape(expected, N6W_SOURCE_LAYOUT, "n6w-expected-source"):
        reject("n6w-theorem-source-drift")
    logger.debug("snapshot_theorem_source exit")
    return expected


def policy() -> N6WPolicyV1:
    """Construct the only hard P3-N6-W construction policy."""
    logger.debug("policy entry")
    exact_values = (
        "p3n6w-policy-v1", 4096, 1024, 4096,
        "074fd3ea6b62f35ed6898f97003c639450b7508fbdc2fac746c2d852ad34c321",
    )
    policy_digest = digest("veyra.p3n6w.policy.v1", (
        ("version", exact_values[0].encode()),
        ("depth", exact_values[1].to_bytes(8, "big")),
        ("rows", exact_values[2].to_bytes(8, "big")),
        ("integer-bits", exact_values[3].to_bytes(8, "big")),
        ("base-policy", exact_values[4].encode()),
    ))
    result = N6WPolicyV1(*exact_values, policy_digest)
    logger.debug("policy exit")
    return result


def snapshot_policy(value: N6WPolicyV1) -> N6WPolicyV1:
    """Reject caller-loosened, Boolean, subclassed, or digest-drifted policy."""
    logger.debug("snapshot_policy entry")
    raw = exact_shape(value, N6W_POLICY_LAYOUT, "n6w-policy")
    exact_text(raw["version"], "n6w-policy-version")
    exact_digest(raw["base_policy_digest"], "n6w-policy-base")
    exact_digest(raw["policy_digest"], "n6w-policy-digest")
    for name in ("max_requested_depth", "max_prefix_rows", "max_integer_bits"):
        exact_nonnegative_int(raw[name], f"n6w-policy-{name}", maximum=2**63 - 1)
    expected = policy()
    if raw != exact_shape(expected, N6W_POLICY_LAYOUT, "n6w-expected-policy"):
        reject("n6w-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected
