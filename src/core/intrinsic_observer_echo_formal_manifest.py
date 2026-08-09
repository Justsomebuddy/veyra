"""Externally reviewed manual source/toolchain trust root for R13.2."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-intrinsic-observer-echo-formal-tcb-r13.2-v1"
BRIDGE_ID = "veyra.lean.r13.intrinsic-observer-echo-tcb.v1"
EXPECTED_PHASE_ARTIFACT = "2ae21b674aa54efd50630a6c764af47ed72ce973b9171fe8eea1a550f3c8cd1b"
EXPECTED_SOURCE_ELABORATION_BINDING = "d7d5d9c054560ba43731368d4d5e2b62b17516298c954a387d7d2ef63d6d67f4"
EXPECTED_R11_BINDING = "ebacad7ae4334e1e2eb693e015d7417df266400ae18783cb1daa21218f649f30"
EXPECTED_R12_BINDING = "4eef290735f9ab795d4d4e43944ded065bf5318cd38df7af21ce398aa3605c86"
EXPECTED_SNAPSHOT_DIGEST = "563b17223875c412662d3f3ade3deaa562af1e4bef62aae52d644cfe4b0dfb71"
EXPECTED_BINDING_DIGEST = "1ad34495eeeda428ddedb283d5b638327d5120eedbd9edb6a4c0095ba804bcaa"
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
    ("evidence", "cdc24620025f79ac41a140d60db856ac7d02bd56554682006b8dcb28dfee6994"),
    ("effects", "a1fe8c50c83a06ed5fc8a48ff1a93f7feb56d598145128e812dd316f4149a7cc"),
    ("formal_report", "d23c1cddb30b6a9d5dac579ffa85746614e4286ab218b065f29ac91c213c63b7"),
    ("formal_snapshot", "231226a8de637f68e85558de61654ce03181eedb573cdd34570271cf6bb050e6"),
    ("formal_bridge_io", "cae1db38d3ec8a40358c3a1557ad1cd9dde384e7fac3cdc4060715a7f819b60e"),
    ("formal_compile", "89f8bf99fd057cba39a9b0598cd18bbdecd3093e16ab37d4d533e961a54955d6"),
    ("formal_lean_render", "59e2c490d5edca44e518a66d50e8b7a6dd756fa7e05d27321b6220603c64378e"),
    ("formal_bridge_core", "ebd533a0a85b94db9e57dc9f3db20145881b93eb5def55c2d96b422548085ccc"),
    ("formal_bridge", "e17166b37600efb85e5edac6daf8b3593bbb7e8611288858e25ce51c21a89bb2"),
    ("phase_source", "505aca53c8908b6e0f1fde011a7bec928218eeb1844b271a03cdbdf7c304a301"),
    ("toolchain_runtime", "3829ce2283c46c09e4ff4ac0e5523771de511684c4337cad9e76397f012d8165"),
    ("runtime_guard", "0386b09a253e896638cab838cf293b91e365924017978f90faa469dc707a4ee1"),
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
    ("lean_export", "16455484cbf1e0fa71ca31a09aecc7950f1fd92909f2d3abe8003587b2fb3416"),
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
