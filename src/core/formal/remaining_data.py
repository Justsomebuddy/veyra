"""Pure metadata for the final four fixed X8 theorem-card artifacts."""

ANALYSIS_ARTIFACT_SHA256 = "3644d6e09540055316bb250f58836d5411134651dbdf0fa9e300250401ca41c0"
CYCLIC_ARTIFACT_SHA256 = "26dc64a3dcdeaeb11235f33e18aa6482b81e03ec19415161e3c48d7d0856dc9b"

SAMPLED_CONTINUITY_ID = "sampled-continuity"
SAMPLED_CONTINUITY_SYMBOL = "THM_A004_sampled_continuity_double_0_five_points"
DRIFT_STABILITY_ID = "drift-stability"
DRIFT_STABILITY_SYMBOL = "THM_A005_square_symmetric_drift_3_steps_1_2_3"
AREA_ADDITIVITY_ID = "area-additivity"
AREA_ADDITIVITY_SYMBOL = "THM_A006_identity_midpoint_area_4_4_8"
CHORD_SYMMETRY_ID = "chord-symmetry"
CHORD_SYMMETRY_SYMBOL = "THM_C002_chord_symmetry_12_0_3_9"

REMAINING_FORMAL_EXPORT_ROWS = (
    (
        SAMPLED_CONTINUITY_ID,
        "Sampled continuity",
        "analysis.sampled_continuity",
        ("DEF-072", "DEF-073", "DEF-086"),
        "proofs/lean/VeyraAlgebra.lean",
        SAMPLED_CONTINUITY_SYMBOL,
        ANALYSIS_ARTIFACT_SHA256,
        "formalizes only the fixed double-map sample at anchor 0, radius 1/10, and five points; no claim about general continuity or analysis",
    ),
    (
        DRIFT_STABILITY_ID,
        "Drift stability",
        "analysis.drift_stability",
        ("DEF-074", "DEF-086"),
        "proofs/lean/VeyraAlgebra.lean",
        DRIFT_STABILITY_SYMBOL,
        ANALYSIS_ARTIFACT_SHA256,
        "formalizes only square-map symmetric quotients at anchor 3 and steps 1,2,3; no claim about general derivatives or analysis",
    ),
    (
        AREA_ADDITIVITY_ID,
        "Area additivity",
        "analysis.area_additivity",
        ("DEF-075", "DEF-086"),
        "proofs/lean/VeyraAlgebra.lean",
        AREA_ADDITIVITY_SYMBOL,
        ANALYSIS_ARTIFACT_SHA256,
        "formalizes only fixed identity midpoint sums on [0,1], [1,2], and [0,2]; no claim about general integration or analysis",
    ),
    (
        CHORD_SYMMETRY_ID,
        "Chord symmetry",
        "trig.chord_symmetry",
        ("DEF-106", "DEF-108", "DEF-086"),
        "proofs/lean/VeyraCyclic.lean",
        CHORD_SYMMETRY_SYMBOL,
        CYCLIC_ARTIFACT_SHA256,
        "formalizes only anchor 0 mod 12 with mirror phases 3 and 9 and chord shadow 3/4; no claim about general chord symmetry or trigonometry",
    ),
)
