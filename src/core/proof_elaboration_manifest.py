"""Reviewed immutable digest manifest for the exact R10 elaboration TCB."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-proof-elaboration-tcb-v1"
EXPECTED_LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
EXPECTED_LEAN_RUNTIME = (
    "990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a",
    2365,
    522231408,
)
EXPECTED_R10_TCB_DIGESTS = MappingProxyType({
    "canonical": "5971bc27f4ea214aa40f8b071c46318383d269800afa2ef12fa20cf2c9f2882b",
    "surface_types": "407b49c93dd366f73a0df10c10043f86bc96e3dc51eac8fa1dac25190cc67567",
    "surface_trace": "cf1e74174a8e274381c1c541d3732c1edf9f6cce3b3adcc9295fb0d2ac94154c",
    "surface_sexpr": "52f0039d357945d3c1eeb281c01bacaf4016d26f630ac626e8af86b1d2b23834",
    "surface_parser": "1165f2b6bf0348b5548f7adf582a897d533dedaea8c4a23e2a4cbee94ddf91ba",
    "surface_codec": "9ef83e06dbd32174fe800fc1e04084e890a395cc6bed03d00cc8f6ea5d43a4a2",
    "surface_elaborator": "a0cfa64d9f10d2c7250dca2d35a019fbdcff4799de60be240ff1a10200b2bcce",
    "surface_lowering": "3c8f780aff99ee2962e093b370b81619fbb4acf324b2800d4bb996b51fb626a9",
    "surface_validation": "9faf4e1f102853a56b63abf1f7562a52e04e8308574a37abdc0e2d2473e24515",
    "dependency_support": "e43cb633aca48b39c09e4d6c16b50813f3b86f2191d75db42b537357b0e26f5b",
    "elaboration_artifact": "effd184593de04603767b111741138105670bff6dd90a7eb62ce0c76a1f04766",
    "lean_renderer": "b9ed623f2386ae62778ca230eef68e8a3f21e7c8c50ba353411fb4da96bc2ce3",
    "bridge_snapshot": "1228c271ea5acee1ee13221d14ed24f5954ea0508e587fe2f4b6b568d3465b0d",
    "bridge_io": "c8f6ba31b201ddb9b4414bd26e1829f8fe5ade7e93d9bed34452a5e0dc298359",
    "toolchain_runtime": "63db421d5e91caf2f2437f28d626989ff4eb5efc283897986e6bb29d86881a0f",
    "runtime_guard": "56374cee0557bfe2590f231a9f8df7759a204cdba75cacfdb3b5b572ee874422",
    "reviewed_objects": "de1057ac81a4861cae44d0930078db842c58fb31651862aa7f8d27a945c6b601",
    "bridge": "3ffd654f81cfd6e09a2a640c09ef6bd4a1d15faf9f894659369e818681cf3e35",
    "certificate": "381a548f6c767870c4e3cc261f0df6ce0ee9028872fb88a44517fdc211446223",
    "proof_types": "871dad8b0e62c4abcc8b439ad603abe29b3d2ae028afab7f145ff4f3fdc1c821",
    "proof_substitution": "3b70ee2c5745b6a8791283babe743d124e70bab1364da6d4a994ecc05903a879",
    "proof_kernel": "396303a63c4415f31ea48ab5010644f8c8fb345b767c3e0e044bf28212750b2d",
    "proof_codec": "2adefdc8d198e62ba0a3285d992b8f4a24e7d5e072a8adcdd825d40ccefb1cad",
    "proof_artifact": "7df70edbb114f5e7d1c94f15a5428c0d1105905460e41719dc30cd4d65ac1e0c",
    "proof_artifact_decode": "849d2a8034dd6d4523977d1b9c89b4e379a810c4cab1e89d7da2d656cffdd4c6",
    "proof_lean_renderer": "2d1ce3f88828af8637384eda42083cc6fd9bb0b98a46f474ab14bc34836b6195",
    "proof_resonance": "c97a3f7d2dab35e58e5c25a466f6efca6e414f8479303fb76bf278b8001f17c6",
    "lean_arithmetic": "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3",
    "lean_semantics": "dc5ddc3b9a3f16c6c5fbbb988b737b806115122d8d2a3f705654e0ee63200a8b",
    "lean_intrinsic_runtime": "ec0df6b350054cdda45b043fc07581f817996ecbe8e3d24bdfc82bb44d7db121",
    "lean_kernel": "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53",
    "lean_soundness": "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14",
    "lean_r7_export": "f4d76b33b25d81140ed262fcf760a800208b495bc3dcb3e62ef4860f15ac3d9d",
    "lean_transport": "493e4662e295b526d5bb76b9ca528b834265142e91e0446e98af2b3b102fb16f",
    "lean_r9_export": "d9ac930c119f3126a858bf286bee32f4d5b9a3ac3fe8cb297316d9cc10dbcc26",
    "lean_elaboration": "ed24ec58377ef44b804444d5b330955c5f3601942d1740e5f23503f0ea121da5",
    "lean_export": "52269d4c9839b7178200e0a8e86acd4df6348302e457745eb86e58439feb265f",
})
MANIFEST_BOUNDARY = (
    "reviewed surface/R7/R9/Lean elaboration sources and deterministic intermediate "
    "object records; digest renewal requires deliberate semantic and artifact review"
)
