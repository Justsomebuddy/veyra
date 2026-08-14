"""Reviewed immutable digest manifest for the exact R11 observer TCB."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-observer-core-tcb-v1"
BRIDGE_ID = "veyra.lean.r11.observer-echo-tcb.v1"
EXPECTED_LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
EXPECTED_LEAN_RUNTIME = (
    "990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a",
    2365,
    522231408,
)
_EXPECTED_R11_TCB_DIGEST_ROWS = (
    ("observer_types", "584f7d19d368618f3cffdcbb130fbf6851a718dedd4d4a0ab177554ad666853c"),
    ("observer_codec", "39d8df55d8e0815fe0359e6e0f68ee0464c4933a0c0b24cf9b5949a61fcda445"),
    ("observer_semantics", "fc095d5fc180f1711d524befbdde3e954b238fcb230f19d1db108efec07e9eaa"),
    ("observer_proof_types", "25f4237e05be50e3dececa95e12f5a5424d0b851b3e98a90f86d5a0fe2b230dd"),
    ("observer_support", "74255ab0eb077e69ce91f40deb8a4c57b0caec572fd6836d729250436455744d"),
    ("observer_kernel", "b26425ce69882976dd7044b46f1a84a6d5ed4eb92d2c6dfc786218cc9350d818"),
    ("observer_artifact", "537ec785cb291369c7dd50601a339f6b1dc70514e4d7dac89a5076bf34e1e7f8"),
    ("lean_renderer", "8b748bbdeded80dbd0a7aba83e45c662939181a7d7410ff2e7fb884f330d5ad1"),
    ("bridge_snapshot", "abac4da2d2cec1106e971d9906bd4c80913af86eda879fc733841b573b1a8004"),
    ("reviewed_objects", "c99cd15044abfd2f92aa10c9f99ec6e1a1a1a15dfcb17f0bd630d2f58a3dc65a"),
    ("bridge_report", "bb2d6b7c410520f9b66646c3d5cdeb8281962fd646610a9faf3fb50c711a67a8"),
    ("bridge_io", "03f6ada647e81ad183e753c2cf9c0862a2b778c389bb34a6af4133a50cbab148"),
    ("bridge", "3033ba354caef4f0b1d7ce543d37c523843b10a97e05252d9cded5f3453accec"),
    ("certificate", "b452080a19856f9390ada15a69521c71423bbae2af78a01a7984deeec77baec0"),
    ("certificate_types", "0de598ad82781801d31788c9b56b41be624de1608350862b903f2ff4f405b258"),
    ("proof_types", "871dad8b0e62c4abcc8b439ad603abe29b3d2ae028afab7f145ff4f3fdc1c821"),
    ("proof_substitution", "3b70ee2c5745b6a8791283babe743d124e70bab1364da6d4a994ecc05903a879"),
    ("proof_kernel", "396303a63c4415f31ea48ab5010644f8c8fb345b767c3e0e044bf28212750b2d"),
    ("proof_codec", "2adefdc8d198e62ba0a3285d992b8f4a24e7d5e072a8adcdd825d40ccefb1cad"),
    ("proof_artifact_decode", "849d2a8034dd6d4523977d1b9c89b4e379a810c4cab1e89d7da2d656cffdd4c6"),
    ("proof_artifact", "7df70edbb114f5e7d1c94f15a5428c0d1105905460e41719dc30cd4d65ac1e0c"),
    ("toolchain_runtime", "63db421d5e91caf2f2437f28d626989ff4eb5efc283897986e6bb29d86881a0f"),
    ("runtime_guard", "56374cee0557bfe2590f231a9f8df7759a204cdba75cacfdb3b5b572ee874422"),
    ("r10_manifest", "99045f664f1bed3ce2bff184d0568a1ffb9fc63e2cd17b869d2ea52909f236a0"),
    ("r10_bridge", "3ffd654f81cfd6e09a2a640c09ef6bd4a1d15faf9f894659369e818681cf3e35"),
    ("lean_arithmetic", "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3"),
    ("lean_semantics", "dc5ddc3b9a3f16c6c5fbbb988b737b806115122d8d2a3f705654e0ee63200a8b"),
    ("lean_intrinsic_runtime", "ec0df6b350054cdda45b043fc07581f817996ecbe8e3d24bdfc82bb44d7db121"),
    ("lean_kernel", "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53"),
    ("lean_soundness", "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14"),
    ("lean_transport", "493e4662e295b526d5bb76b9ca528b834265142e91e0446e98af2b3b102fb16f"),
    ("lean_observer_core", "fef5db4a94f40b7ba478c5e9d28c5680f736672d5caaea5ac97a823d3e2359d2"),
    ("lean_observer_proof", "7ef4905cc7923ee0c5d057abbada8c3f6b97c8e181b7d73fba0ad7c21653c1d2"),
    ("lean_export", "36d6d2499a7e4e025b5450f970577157afda8c87aba51bb378391c001e1ebcce"),
)
EXPECTED_R11_TCB_DIGESTS = MappingProxyType(dict(_EXPECTED_R11_TCB_DIGEST_ROWS))
MANIFEST_BOUNDARY = (
    "reviewed R11 observer/R7 sources, exact R9 Lean image semantics, generated export, "
    "deterministic intermediate objects, and the current independently verified R10 "
    "binding; this manifest is the external manual root and cannot self-bind without "
    "hash recursion; digest renewal requires deliberate semantic and artifact review"
)
