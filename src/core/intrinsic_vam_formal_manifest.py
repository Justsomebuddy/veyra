"""Externally reviewed manual source/toolchain trust root for R12.5."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-intrinsic-vam-formal-tcb-r12.5-v1"
BRIDGE_ID = "veyra.lean.r12.5.intrinsic-vam-tcb.v1"
EXPECTED_R11_BINDING = "7635a58d200121bddd317ecb73eadbf0f726cbc79de4911f1ab173554c1da0a6"
EXPECTED_SNAPSHOT_DIGEST = "0d8fba12d4abcb9fd90076714d7e8ab9098a5bb25aa15d3f4c2287eb2f4fbad9"
EXPECTED_BINDING_DIGEST = "b69fa1066722e638818791037d3f3db8023c410baac372faa59e321ef0ae3ba3"
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

_EXPECTED_R12_5_TCB_DIGEST_ROWS = (
    ("formal_effects", "65d30a244edae4ffc25bdbf12b3fb4f9af47fb393ab935f6a5de160ce4130208"),
    ("formal_report", "b8b38d10b5c765736c56d74a38ec60b0513b727043d2b227d358ba776da233dc"),
    ("formal_snapshot", "517761ca4e7c3a98b5107b9b20ec876d49d3b9ec2599cad5dfc4b9efd5806416"),
    ("formal_bridge_io", "2fef36b6630964d79b40a2e2a55aee6373a849b986eb48870a32360501b8ae21"),
    ("formal_compile", "70c1bd3498b109d6a082a37cdd07b94a692f60a849aff09121a375ee4fb33eb2"),
    ("formal_lean_render", "e63bb0313eb946cf8c150743769df8b27cea66a198616f8bce61f29e525ee093"),
    ("formal_bridge_core", "59d13b25791a431eb22ef51b36621603c81f9e78c5d16de82d7f28654c204844"),
    ("formal_bridge", "69bbb72017aa8b3cec7829fe2089d656bf148e3d16e0f86ed377b965f50bed81"),
    ("effect_types", "85c0a8180a12e9e5b0cbe470764fd08b6d4b11e9b771e40d70d15e744d77ab49"),
    ("effects", "66cbaf142e67f5418e491fe3ff20c5eaec5d76326e749399e48eb87a43731862"),
    ("intrinsic_ir_types", "a283bd15e26871872cec4ae9711f83e62145c0356e55938c48a212b44a0a9d0d"),
    ("intrinsic_ir", "cbbe3c4374fb77dbaa3730db802aeb6d65d4e4a9f37e5d70733219dadf8c1b4e"),
    ("lowering_types", "42f07af6ecadf1259f5e6243b197b32edc341ca55ecb04fe556b356a307946e8"),
    ("lowering_values", "dc0ab57796eede03d65928238e1696074a2ae308a09bc55670b287757467470d"),
    ("lowering_receipts", "0dee95590862295da9d48874b7f7e4e454d9041612e32ea62d76e16bef82b0b8"),
    ("lowering", "e19e89672d3700b3faf4f1771b2edbdc5fea26495778db42e1c3ca7de146607d"),
    ("toolchain_runtime", "63db421d5e91caf2f2437f28d626989ff4eb5efc283897986e6bb29d86881a0f"),
    ("runtime_guard", "56374cee0557bfe2590f231a9f8df7759a204cdba75cacfdb3b5b572ee874422"),
    ("lean_arithmetic", "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3"),
    ("lean_semantics", "dc5ddc3b9a3f16c6c5fbbb988b737b806115122d8d2a3f705654e0ee63200a8b"),
    ("lean_intrinsic_runtime", "ec0df6b350054cdda45b043fc07581f817996ecbe8e3d24bdfc82bb44d7db121"),
    ("lean_kernel", "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53"),
    ("lean_soundness", "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14"),
    ("lean_transport", "493e4662e295b526d5bb76b9ca528b834265142e91e0446e98af2b3b102fb16f"),
    ("lean_observer_core", "fef5db4a94f40b7ba478c5e9d28c5680f736672d5caaea5ac97a823d3e2359d2"),
    ("lean_observer_proof", "7ef4905cc7923ee0c5d057abbada8c3f6b97c8e181b7d73fba0ad7c21653c1d2"),
    ("lean_intrinsic_vam", "770ab54aed74ed394162e249f034a87ff13609d037432a26d5e4bf0971a37e0d"),
    ("lean_export", "1d0e2a12742d0550914cb0d38946ddf2d9b2ad1b7ac9bcfa740a6f1eefaaaa6a"),
)
EXPECTED_R12_5_TCB_DIGESTS = MappingProxyType(dict(_EXPECTED_R12_5_TCB_DIGEST_ROWS))

MANIFEST_BOUNDARY = (
    "bounded valid R12.2/R12.3 lowering image and exact R11 obstruction order only; "
    "public theorem correspondence is restricted by the reviewed 2047/2048/4096/128 "
    "resource predicates; universal helper lemmas are not correspondence evidence; "
    "source parity does not extract Python or Rust from Lean or prove VAMI parsing/CRC, "
    "authenticate R12.3 receipts, renew R8, add a certificate/Sage facade, promote a "
    "layer, alter taxonomy, or cover legacy VAM; the manual manifest is an external "
    "review root, and OS loader/glibc/ld-cache, proc/sys, entropy, mount namespace, "
    "kernel, ptrace, and root compromise remain outside the userspace integrity TCB"
)
