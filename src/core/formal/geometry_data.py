"""Pure metadata for the fixed X8 geometry theorem-card wave."""

GEOMETRY_ARTIFACT_SHA256 = "0eeb7eb904032b71b0ebcee1b1bf67b8c18768655a1c1c9b3920f65d02f7630e"

SSS_TRIANGLE_ID = "sss-triangle"
SSS_TRIANGLE_SYMBOL = "THM_G002_sss_side_squares_shift_10"
SAS_TRIANGLE_ID = "sas-triangle"
SAS_TRIANGLE_SYMBOL = "THM_G003_sas_anchor_3_4_dot_0"
LINE_SHELL_INTERSECTION_ID = "line-shell-intersection"
LINE_SHELL_INTERSECTION_SYMBOL = "THM_G004_diameter_shell_scaled_roots"
PLANE_RELABEL_COMPOSITION_ID = "plane-relabel-composition"
PLANE_RELABEL_COMPOSITION_SYMBOL = "THM_G005_quarter_turn_after_translation"

GEOMETRY_FORMAL_EXPORT_ROWS = (
    (
        SSS_TRIANGLE_ID, "SSS triangle card", "geometry.sss", SSS_TRIANGLE_SYMBOL,
        "formalizes only fixed base/+10 side-square triples 9/16/25; no claim about general SSS congruence or geometry",
    ),
    (
        SAS_TRIANGLE_ID, "SAS triangle card", "geometry.sas", SAS_TRIANGLE_SYMBOL,
        "formalizes only fixed anchor measures 9/16 and dot 0; no claim about general SAS congruence or geometry",
    ),
    (
        LINE_SHELL_INTERSECTION_ID, "Corridor-shell intersection", "geometry.line_shell",
        LINE_SHELL_INTERSECTION_SYMBOL,
        "formalizes only scaled roots t=1/4 and t=3/4 for (-10,0)->(10,0) at radius-square 25; no claim about general line-shell intersections or geometry",
    ),
    (
        PLANE_RELABEL_COMPOSITION_ID, "Plane relabel composition", "geometry.relabel_compose",
        PLANE_RELABEL_COMPOSITION_SYMBOL,
        "formalizes only quarter-turn after translation (1,-2) at point (2,3), both paths (-1,3); no claim about general relabel composition or geometry",
    ),
)
