"""Reviewed deterministic Lean object records for the exact R10 chain."""
from types import MappingProxyType

EXPECTED_LEAN_OBJECTS = MappingProxyType({
    "lean_arithmetic": (
        "VeyraNativeArithmetic.olean", 176856,
        "2ee38abbf195fcc2f0837366af98ca3047b1bc682691c049c3c9fe3eb44b1945",
    ),
    "lean_semantics": (
        "VeyraNativeSemantics.olean", 767352,
        "e3ff6f807e2570e8b637e9fab76c786023339c6f24c6acf5866ba55b4337e505",
    ),
    "lean_intrinsic_runtime": (
        "VeyraIntrinsicRuntime.olean", 81928,
        "49230a22143b1eec485f2f97e788608fdc833a963493ab369e62fdad359b30cf",
    ),
    "lean_kernel": (
        "VeyraProofKernel.olean", 2353728,
        "0b42aca8cab44c3bd40355379f95ff3845b3cc24ce9d24984e1be2721603c4c1",
    ),
    "lean_soundness": (
        "VeyraProofSoundness.olean", 611240,
        "935ce61c4375afcb8a5c3275b1f17f34d5e83c24f6fc54b8324f29941dbb6e1a",
    ),
    "lean_r7_export": (
        "VeyraProofResonance.olean", 36608,
        "ab0f67f5cbbbc8e360e84d4f26ad4119205b885da137d3179867530482c28cf1",
    ),
    "lean_transport": (
        "VeyraRecurrenceModeBridge.olean", 261136,
        "b2b616349e095f2b436fbf9fbaee561fb39f618ff4e51693f23fd1093b2e201f",
    ),
    "lean_r9_export": (
        "VeyraProofModeTransport.olean", 39040,
        "2defd7b982fdba5cab38ac123aa76ddd14bc2da053b6efa1afa057eb7bef2049",
    ),
    "lean_elaboration": (
        "VeyraElaborationSemantics.olean", 870920,
        "e83cc163b0a9d371d3256441a609c7ede03697516f14dcb546c0b68739d89cd6",
    ),
})
