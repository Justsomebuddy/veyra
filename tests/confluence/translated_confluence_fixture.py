"""Reusable raw-source fixture for P1-C3 focused pressure."""

from src.core.confluence import (
    diagram_edge, diagram_path, direct_echo_transport, finite_diagram_source,
    fork_join_plan,
)
from src.core.confluence_types import AlignmentPoint
from src.core.observer_core_kernel import crest_observer, tail_observer
from src.core.observer_core_types import Input, Pair
from src.core.observer_morphism import (
    observer_source_binding, p1a_observer_morphism_doctrine,
)
from src.core.observer_morphism_types import ProjectionStep
from src.core.observer_relations import (
    ComparisonMode, LossStatus, RelationClass, morphism_replay_spec,
    observer_relation_scope, relation_evaluation_source, relation_resource_policy,
)
from src.core.positive_ontology import internal_observer, ontology_stage
from src.core.positive_ontology_doctrine import observer_doctrine
from src.core.proof_core_types import Pulse, Silence
from src.core.translated_confluence import (
    TranslationDirection, p0_p1a_response_bridge,
    translated_confluence_policy, translated_echo_transport_spec,
)


def recurrence(depth):
    value = Silence()
    for _ in range(depth):
        value = Pulse(value)
    return value


def translated_fixture(
    *, direction=TranslationDirection.LEFT_FINE_TO_RIGHT_COARSE,
    left_depth=1, right_depth=2, variant="strict",
    padding_observers=0, padding_stages=0,
):
    crest = crest_observer()
    if variant == "strict":
        fine_program, coarse_program = Pair(crest, Input()), crest
        p1a_fine, p1a_coarse = "fine-total", "coarse-crest"
        expected_class = RelationClass.STRICT_REFINEMENT_ON_SCOPE
        expected_loss = LossStatus.LOSSY_ON_SCOPE
    elif variant == "equivalent":
        fine_program = Pair(Pair(crest, Input()), Input())
        coarse_program = Pair(crest, Input())
        p1a_fine, p1a_coarse = "fine-nested", "fine-total"
        expected_class = RelationClass.EQUIVALENT_ON_SCOPE
        expected_loss = LossStatus.LOSSLESS_ON_SCOPE
        left_depth = right_depth = 1
    elif variant in {"blocked", "information-only"}:
        fine_program, coarse_program = Pair(crest, tail_observer()), crest
        p1a_fine, p1a_coarse = "fine-domain-hole", "coarse-crest"
        expected_class = RelationClass.STRICT_REFINEMENT_ON_SCOPE
        expected_loss = LossStatus.LOSSY_ON_SCOPE
        left_depth = right_depth = 0 if variant == "blocked" else 1
    else:
        raise ValueError("unknown-c3-test-variant")
    padding_programs = []
    for index in range(padding_observers):
        padding_program = Input()
        for _ in range(39 + index):
            padding_program = Pair(padding_program, Input())
        padding_programs.append(padding_program)
    p0_observers = (
        internal_observer("diagram-fine", fine_program),
        internal_observer("diagram-coarse", coarse_program),
        *(internal_observer(f"unbridged-{index}", program)
          for index, program in enumerate(padding_programs)),
    )
    p0 = observer_doctrine(
        "C3-diagram", "closed-r11-c3", ("finite", "translated"),
        p0_observers,
        version="p1-c3-test-p0-v1",
    )
    reps = {
        "fork": recurrence(left_depth if variant != "strict" else 1),
        "left": recurrence(left_depth), "right": recurrence(right_depth),
        "join": recurrence(left_depth if variant != "strict" else 1),
    }
    diagram_reps = {
        **reps,
        **{f"padding-stage-{index}": recurrence(1) for index in range(padding_stages)},
    }
    observer_count = len(p0_observers) if padding_observers else 2
    stages = tuple(
        ontology_stage(name, term, p0, observer_count)
        for name, term in diagram_reps.items()
    )
    edges = (
        diagram_edge("fl", "fork", "left", ("diagram-coarse",)),
        diagram_edge("fr", "fork", "right", ("diagram-coarse",)),
        diagram_edge("lj", "left", "join", ("diagram-coarse",)),
        diagram_edge("rj", "right", "join", ("diagram-coarse",)),
    )
    paths = (
        diagram_path("lb", ("fl",), "fork", "left"),
        diagram_path("rb", ("fr",), "fork", "right"),
        diagram_path("ljp", ("lj",), "left", "join"),
        diagram_path("rjp", ("rj",), "right", "join"),
    )
    diagram = finite_diagram_source(p0, "c3-diagram", stages, edges, paths)
    placeholder = direct_echo_transport(p0, ("diagram-fine", "diagram-coarse"))
    alignment = (AlignmentPoint(0, 0), AlignmentPoint(1, 1), AlignmentPoint(2, 2))
    plan = fork_join_plan(
        p0, diagram, "c3-plan", "lb", "rb", "ljp", "rjp", alignment, placeholder,
    )
    p1a = p1a_observer_morphism_doctrine()
    binding = observer_source_binding(
        p1a, "c3-p1a-source", (p1a_coarse, p1a_fine),
    )
    a2_source = relation_evaluation_source(
        p1a, binding, tuple((name, term) for name, term in reps.items()),
    )
    keys = tuple((row.stage_id, row.commitment) for row in a2_source.stages)
    scope = observer_relation_scope(
        p1a, binding, a2_source, p1a_fine, p1a_coarse, keys,
        ComparisonMode.WITH_P1A_REPLAY,
    )
    morphism = morphism_replay_spec(
        "c3-fine-to-coarse", p1a_fine, p1a_coarse, (ProjectionStep.LEFT,),
    )
    bridge = p0_p1a_response_bridge(p0, diagram, p1a, binding, a2_source)
    relation_policy = relation_resource_policy(max_cost=2048, max_encoded_bytes=1_000_000)
    spec = translated_echo_transport_spec(
        p0, diagram, plan, p1a, binding, a2_source, bridge, "c3-spec", direction,
        "diagram-fine", "diagram-coarse", morphism, scope, relation_policy,
        expected_class, expected_loss,
    )
    policy = translated_confluence_policy()
    return p0, diagram, plan, p1a, binding, a2_source, bridge, spec, policy, placeholder
