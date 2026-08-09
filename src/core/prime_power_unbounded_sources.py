"""Pinned source, toolchain and policy constructors for candidate P3-N6."""

from __future__ import annotations

import logging
from typing import cast

from .padic.completion.formal import (
    ARTIFACT_PATH as _P2_PATH,
    ARTIFACT_SHA256 as _P2_SHA,
    ELAN_SHA256,
    LEAN_BINARY_SHA256,
    LEAN_VERSION,
)
from .padic.family_introduction.sources import (
    ARTIFACT_PATH as _N1_PATH,
    ARTIFACT_SHA256 as _N1_SHA,
    TOOLCHAIN_ID as _TOOLCHAIN_ID,
)
from .prime_power_unbounded_common import (
    digest,
    exact_digest,
    exact_nonnegative_int,
    exact_shape,
    exact_text,
    reject,
)
from .prime_power_unbounded_types import (
    N6Lane, N6PolicyV1, N6TheoremSourceV1, N6_POLICY_LAYOUT,
    N6_THEOREM_SOURCE_LAYOUT,
)

logger = logging.getLogger(__name__)

P2_PATH = _P2_PATH
P2_SHA = _P2_SHA
N1_PATH = _N1_PATH
N1_SHA = _N1_SHA
TOOLCHAIN_ID = _TOOLCHAIN_ID

FORMAL_VERSION = "p3n6-formal-v2"
ARTIFACT_PATH = "proofs/lean/VeyraPrimePowerUnbounded.lean"
ARTIFACT_SHA256 = "d35ead8dca26e0a07842ad830a143dab36b94b6ff201e79fd16dce9a81305b1c"
THEOREM_IDS = (
    "THM_P3N6_001_prefix_indistinguishable",
    "THM_P3N6_002_next_depth_distinguishes",
    "THM_P3N6_003_power_carrier_injective",
    "THM_P3N6_004_power_carrier_eqc_injective",
    "THM_P3N6_005_carrier_equality_adapter",
)
W_THEOREM_IDS = THEOREM_IDS[:2]
E_THEOREM_IDS = THEOREM_IDS[2:]
DIRECT_IMPORTS = ((N1_PATH, N1_SHA),)
TRANSITIVE_IMPORTS = ((N1_PATH, N1_SHA), (P2_PATH, P2_SHA))
EQUALITY_DEFINITION_ID = "veyraCarrierEq"
POWER_MAP_DEFINITION_ID = "veyraPowerCarrier"
E_AXIOM_ROWS = (
    (E_THEOREM_IDS[0], ("propext",)),
    (E_THEOREM_IDS[1], ("propext",)),
    (E_THEOREM_IDS[2], ()),
)
W_AXIOM_ROWS = tuple((theorem_id, ("propext",)) for theorem_id in W_THEOREM_IDS)
AXIOM_ROWS = E_AXIOM_ROWS

TCB_DIGEST = digest(
    "veyra.p3n6.tcb.v1",
    (
        ("toolchain", TOOLCHAIN_ID.encode()),
        ("elan", ELAN_SHA256.encode()),
        ("lean", LEAN_BINARY_SHA256.encode()),
        ("version", LEAN_VERSION.encode()),
        ("process", b"launcher-version-private-pre-post-nonrestored-v2"),
        ("external-runtime", b"lean-dso-init-std-loader-restored-swap-open"),
    ),
)

POLICY_VERSION = "p3n6-policy-v1"
HARD_CAPTURED_BYTES = 3 * 1024 * 1024
HARD_STATIC_COST = 8 * 1024 * 1024
HARD_LEDGER_ROWS = 256
HARD_LEDGER_EDGES = 512
HARD_TIMEOUT_SECONDS = 300
HARD_OUTPUT_BYTES = 4 * 1024 * 1024


def theorem_source(lane: N6Lane = N6Lane.E_POWER_INJECTION) -> N6TheoremSourceV1:
    """Construct the exact lane-separated N6 theorem ancestry identity."""
    logger.debug("theorem_source entry")
    if type(lane) is not N6Lane:
        reject("n6-theorem-source-lane-invalid")
    formal_version = "p3n6-formal-v2"
    artifact_path = "proofs/lean/VeyraPrimePowerUnbounded.lean"
    artifact_sha = "d35ead8dca26e0a07842ad830a143dab36b94b6ff201e79fd16dce9a81305b1c"
    all_theorems = (
        "THM_P3N6_001_prefix_indistinguishable",
        "THM_P3N6_002_next_depth_distinguishes",
        "THM_P3N6_003_power_carrier_injective",
        "THM_P3N6_004_power_carrier_eqc_injective",
        "THM_P3N6_005_carrier_equality_adapter",
    )
    theorem_ids = (
        all_theorems[2:]
        if lane is N6Lane.E_POWER_INJECTION else all_theorems[:2]
    )
    axiom_rows = cast(tuple[tuple[str, tuple[str, ...]], ...], (
        tuple((theorem_id, ("propext",)) for theorem_id in theorem_ids)
        if lane is N6Lane.W_INFORMATION_GROWTH
        else tuple(
            (theorem_id, ("propext",) if index < 2 else ())
            for index, theorem_id in enumerate(theorem_ids)
        )
    ))
    direct_imports = ((
        "proofs/lean/VeyraPadicFamilyIntroduction.lean",
        "b8540c65b555bd8407d558b3a16cc7cd25ab27ca636083451162f1a8a5490b48",
    ),)
    transitive_imports = direct_imports + ((
        "proofs/lean/VeyraPadicCompletion.lean",
        "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f",
    ),)
    equality_definition = "veyraCarrierEq"
    power_map_definition = "veyraPowerCarrier"
    toolchain = "leanprover/lean4:v4.30.0-rc2"
    tcb_digest = "e348a6632186ea09c694c56d6eb79a5e728cb9f10ab0fbacd25dd18720c77568"
    source_digest = digest(
        "veyra.p3n6.theorem-source.v1",
        (
            ("lane", lane.value.encode()),
            ("version", formal_version.encode()),
            ("artifact", artifact_path.encode()),
            ("artifact-sha", artifact_sha.encode()),
            *((f"theorem-{index}", value.encode()) for index, value in enumerate(theorem_ids)),
            *((f"axiom-{index}", f"{theorem_id}\0{','.join(axioms)}".encode()) for index, (theorem_id, axioms) in enumerate(axiom_rows)),
            *((f"direct-{index}", f"{path}\0{sha}".encode()) for index, (path, sha) in enumerate(direct_imports)),
            *((f"transitive-{index}", f"{path}\0{sha}".encode()) for index, (path, sha) in enumerate(transitive_imports)),
            ("equality-definition", equality_definition.encode()),
            ("power-map-definition", power_map_definition.encode()),
            ("toolchain", toolchain.encode()),
            ("tcb", tcb_digest.encode()),
        ),
    )
    result = N6TheoremSourceV1(
        lane,
        formal_version,
        artifact_path,
        artifact_sha,
        theorem_ids,
        axiom_rows,
        direct_imports,
        transitive_imports,
        equality_definition,
        power_map_definition,
        toolchain,
        tcb_digest,
        source_digest,
    )
    logger.debug("theorem_source exit")
    return result


def _exact_imports(value: object, label: str) -> tuple[tuple[str, str], ...]:
    """Validate one bounded exact path/hash tuple without coercion."""
    logger.debug("_exact_imports entry")
    if type(label) is not str:
        reject("n6-imports-internal-label-invalid")
    logger.debug("_exact_imports state=label-validated label=%s", label)
    if type(value) is not tuple or len(value) > 8:
        reject(f"{label}-invalid")
    rows = cast(tuple[object, ...], value)
    output: list[tuple[str, str]] = []
    for index, row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            reject(f"{label}-{index}-invalid")
        pair = cast(tuple[object, object], row)
        path = exact_text(pair[0], f"{label}-{index}-path")
        source_sha = exact_digest(pair[1], f"{label}-{index}-sha")
        output.append((path, source_sha))
    result = tuple(output)
    logger.debug("_exact_imports exit label=%s rows=%d", label, len(result))
    return result


def _exact_axiom_rows(value: object) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Validate bounded theorem/axiom rows without coercion or callbacks."""
    logger.debug("_exact_axiom_rows entry")
    if type(value) is not tuple or len(value) > 16:
        reject("n6-axiom-rows-invalid")
    rows = cast(tuple[object, ...], value)
    output: list[tuple[str, tuple[str, ...]]] = []
    for index, row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            reject(f"n6-axiom-row-{index}-invalid")
        pair = cast(tuple[object, object], row)
        theorem_id = exact_text(pair[0], f"n6-axiom-row-{index}-theorem")
        axioms = pair[1]
        if type(axioms) is not tuple or len(axioms) > 8:
            reject(f"n6-axiom-row-{index}-closure-invalid")
        axiom_values = cast(tuple[object, ...], axioms)
        checked = tuple(
            exact_text(item, f"n6-axiom-row-{index}-{item_index}")
            for item_index, item in enumerate(axiom_values)
        )
        output.append((theorem_id, checked))
    result = tuple(output)
    logger.debug("_exact_axiom_rows exit rows=%d", len(result))
    return result


def snapshot_theorem_source(
    value: N6TheoremSourceV1, lane: N6Lane = N6Lane.E_POWER_INJECTION
) -> N6TheoremSourceV1:
    """Reject alternate source, import, theorem, toolchain or TCB identities."""
    logger.debug("snapshot_theorem_source entry")
    raw = exact_shape(value, N6_THEOREM_SOURCE_LAYOUT, "n6-theorem-source")
    if type(raw["lane"]) is not N6Lane or raw["lane"] is not lane:
        reject("n6-theorem-source-lane-drift")
    for name in (
        "version",
        "artifact_path_id",
        "artifact_sha256",
        "equality_definition_id",
        "power_map_definition_id",
        "toolchain_id",
        "tcb_digest",
        "source_digest",
    ):
        exact_text(raw[name], f"n6-theorem-{name}")
    for name in ("artifact_sha256", "tcb_digest", "source_digest"):
        exact_digest(raw[name], f"n6-theorem-{name}")
    theorem_ids = raw["theorem_ids"]
    if type(theorem_ids) is not tuple or len(theorem_ids) > 16:
        reject("n6-theorem-ids-invalid")
    for index, theorem_id in enumerate(cast(tuple[object, ...], theorem_ids)):
        exact_text(theorem_id, f"n6-theorem-id-{index}")
    _exact_axiom_rows(raw["theorem_axiom_rows"])
    _exact_imports(raw["direct_imports"], "n6-direct-imports")
    _exact_imports(raw["transitive_imports"], "n6-transitive-imports")
    expected = theorem_source(lane)
    expected_raw = exact_shape(expected, N6_THEOREM_SOURCE_LAYOUT, "n6-expected-source")
    if raw != expected_raw:
        reject("n6-theorem-source-drift")
    logger.debug("snapshot_theorem_source exit")
    return expected


def policy() -> N6PolicyV1:
    """Construct the sole hard-first N6 policy."""
    logger.debug("policy entry")
    exact_values = (
        "p3n6-policy-v1", 3 * 1024 * 1024, 8 * 1024 * 1024,
        256, 512, 300, 4 * 1024 * 1024,
    )
    policy_digest = digest(
        "veyra.p3n6.policy.v1",
        (
            ("version", exact_values[0].encode()),
            ("captured", str(exact_values[1]).encode()),
            ("static", str(exact_values[2]).encode()),
            ("rows", str(exact_values[3]).encode()),
            ("edges", str(exact_values[4]).encode()),
            ("timeout", str(exact_values[5]).encode()),
            ("output", str(exact_values[6]).encode()),
        ),
    )
    result = N6PolicyV1(*exact_values, policy_digest)
    logger.debug("policy exit")
    return result


def snapshot_policy(value: N6PolicyV1) -> N6PolicyV1:
    """Reject loosened, reordered, boolean or subclassed policy fields."""
    logger.debug("snapshot_policy entry")
    raw = exact_shape(value, N6_POLICY_LAYOUT, "n6-policy")
    exact_text(raw["version"], "n6-policy-version")
    exact_digest(raw["policy_digest"], "n6-policy-digest")
    for name in (
        "max_captured_bytes",
        "max_static_cost",
        "max_ledger_rows",
        "max_ledger_edges",
        "timeout_seconds",
        "max_output_bytes",
    ):
        exact_nonnegative_int(raw[name], f"n6-policy-{name}", maximum=2**63 - 1)
    expected = policy()
    expected_raw = exact_shape(expected, N6_POLICY_LAYOUT, "n6-expected-policy")
    if raw != expected_raw:
        reject("n6-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected
