"""Externally reviewed manual source/toolchain trust root for R13.2."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-intrinsic-observer-echo-formal-tcb-r13.2-v1"
BRIDGE_ID = "veyra.lean.r13.intrinsic-observer-echo-tcb.v1"
EXPECTED_PHASE_ARTIFACT = "7b013529908cf6f471200621e6a6ffdcbdf543ca284d1a5deefc6efe5f64adca"
EXPECTED_SOURCE_ELABORATION_BINDING = "91305d57bbab7e49549780bb7d564ed01613ec66b375d2db7d80187761767d93"
EXPECTED_R11_BINDING = "d98318066dc015ca7d0d0be36d2b07b38d50c7715f4e2a494d70ff842262c53a"
EXPECTED_R12_BINDING = "54454915f0d7a259fc72458711e9f2d0959d54b1878c7ad524e13c6f002948dc"
EXPECTED_SNAPSHOT_DIGEST = "a089eeb5833219edc12e93eb8ef7d9b699c6143159e12a92cd21eff2ad633867"
EXPECTED_BINDING_DIGEST = "1d2f69c6b18fa4ac4647aacfa29956ca73bf7d9ad03c296a020d670cced3ea68"
EXPECTED_TOOLCHAIN_IDENTITY = (
    "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, commit "
    "3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)|"
    "toolchain=leanprover/lean4:v4.30.0-rc2|binary=lean|sha256="
    "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf|"
    "merkle=990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a|"
    "files=2365|bytes=522231408|size=9024"
)
EXPECTED_LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
EXPECTED_LEAN_RUNTIME = (
    "990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a",
    2365,
    522231408,
)
_EXPECTED_R13_TCB_DIGEST_ROWS = (
    ("evidence", "ac99cf7603d19a4b5532b6e98cbd6f95e835cc3f4f9815c18b08486cd01aee35"),
    ("effects", "a1fe8c50c83a06ed5fc8a48ff1a93f7feb56d598145128e812dd316f4149a7cc"),
    ("formal_report", "d23c1cddb30b6a9d5dac579ffa85746614e4286ab218b065f29ac91c213c63b7"),
    ("formal_snapshot", "c67b90c280b68929c8e56079e6c30e8d7d9e1fcb179e68a75b3f0c64dc98927b"),
    ("formal_bridge_io", "0773b604388b67f01e9cb52b685a273cbc542ab1437d781b34e2ad1bf22894cf"),
    ("formal_compile", "fa3935d3171ea5ebd7485576fe7da1191664a0a390984a779eeb37c8ab158243"),
    ("formal_lean_render", "59e2c490d5edca44e518a66d50e8b7a6dd756fa7e05d27321b6220603c64378e"),
    ("formal_bridge_core", "c3fe9fa064bbd44b11f0271097362b6f1e71a72aba12e7f3dddaadd49db44831"),
    ("formal_bridge", "e17166b37600efb85e5edac6daf8b3593bbb7e8611288858e25ce51c21a89bb2"),
    ("phase_source", "511b9b339dff47d3a480794df442f66d96627e2ce86a86ebd4f2253ffb21cfc3"),
    ("toolchain_runtime", "63db421d5e91caf2f2437f28d626989ff4eb5efc283897986e6bb29d86881a0f"),
    ("runtime_guard", "56374cee0557bfe2590f231a9f8df7759a204cdba75cacfdb3b5b572ee874422"),
    ("effect_types", "85c0a8180a12e9e5b0cbe470764fd08b6d4b11e9b771e40d70d15e744d77ab49"),
    ("effects_registry", "66cbaf142e67f5418e491fe3ff20c5eaec5d76326e749399e48eb87a43731862"),
    ("lean_arithmetic", "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3"),
    ("lean_semantics", "dc5ddc3b9a3f16c6c5fbbb988b737b806115122d8d2a3f705654e0ee63200a8b"),
    ("lean_intrinsic_runtime", "ec0df6b350054cdda45b043fc07581f817996ecbe8e3d24bdfc82bb44d7db121"),
    ("lean_kernel", "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53"),
    ("lean_soundness", "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14"),
    ("lean_transport", "493e4662e295b526d5bb76b9ca528b834265142e91e0446e98af2b3b102fb16f"),
    ("lean_observer_core", "fef5db4a94f40b7ba478c5e9d28c5680f736672d5caaea5ac97a823d3e2359d2"),
    ("lean_observer_proof", "7ef4905cc7923ee0c5d057abbada8c3f6b97c8e181b7d73fba0ad7c21653c1d2"),
    ("lean_intrinsic_vam", "770ab54aed74ed394162e249f034a87ff13609d037432a26d5e4bf0971a37e0d"),
    ("lean_intrinsic_observer_echo", "d9b86a1de1f1ea558a60f730adb5587c64ae540730b72593f694d3f19ab91df0"),
    ("lean_export", "75749c45da8cd4b5af89a218444d65efdf5de36100b1d07d73410c456a09e421"),
)
EXPECTED_R13_TCB_DIGESTS = MappingProxyType(dict(_EXPECTED_R13_TCB_DIGEST_ROWS))
MANIFEST_BOUNDARY = (
    "readiness-conditioned preservation on the bounded exact R12 lowering image only; "
    "the general R13 witness carries the reviewed R12 observer/recurrence/outcome bounds; "
    "tail/silence is domain-blocked and crest is nonreflecting; source parsing, Python "
    "and Lean are mutually bound but not extracted from one another; no raw IR, VAMI, "
    "receipt authentication, legacy VAM, equivalence, promotion, or taxonomy claim; "
    "OS loader, kernel, ptrace, namespace, entropy, and root compromise remain external"
)
