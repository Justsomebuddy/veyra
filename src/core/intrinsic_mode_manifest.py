"""Reviewed immutable digest manifest for the exact R9 transport TCB."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-intrinsic-mode-tcb-v1"
EXPECTED_R9_TCB_DIGESTS = MappingProxyType({
    "python_transport": "b037c828eee79fe1c482df180cd1f5c4538a63eae5bf212511ba804322a19184",
    "python_laws": "e82e1c6a65c9752d1052390c9d5b74ab23d0d9b4ef29c210d10d824cbdfbd97f",
    "python_renderer": "d4615be8de0831046a75fda537c58ac3c63665c9d09db6ff11927befb39df74f",
    "python_snapshot": "f627b42f46c2578741ec8bfccd5620b7e4b12adf76cfd8db7a6ad3a35da7eaef",
    "python_bridge": "0036a41d6695f832b21198e12fa9ec40b36272fd9a3273068a6c61e1e1ffa4b3",
    "native_runtime": "d584211a25f9df54455e7614bcf19807aeccb37905e8cd99272494a8e787f96d",
    "intrinsic_arithmetic": "86653afab132b51ee9e50a4396a464c335cbe2a92b1d5d7b35c450ebfd4ce3b2",
    "proof_core_types": "871dad8b0e62c4abcc8b439ad603abe29b3d2ae028afab7f145ff4f3fdc1c821",
    "lean_arithmetic": "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3",
    "lean_semantics": "dc5ddc3b9a3f16c6c5fbbb988b737b806115122d8d2a3f705654e0ee63200a8b",
    "lean_intrinsic_runtime": "ec0df6b350054cdda45b043fc07581f817996ecbe8e3d24bdfc82bb44d7db121",
    "lean_kernel": "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53",
    "lean_soundness": "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14",
    "lean_r7_export": "f4d76b33b25d81140ed262fcf760a800208b495bc3dcb3e62ef4860f15ac3d9d",
    "lean_transport": "493e4662e295b526d5bb76b9ca528b834265142e91e0446e98af2b3b102fb16f",
    "lean_export": "3d9af0918dcffa3730193c36c5bbc705bc28c507b28291c7f9ef0d21c32335a2",
})
MANIFEST_BOUNDARY = (
    "reviewed Python/native/Lean source parity manifest; a digest binds the "
    "reviewed implementations but is not extraction of Python from Lean"
)
