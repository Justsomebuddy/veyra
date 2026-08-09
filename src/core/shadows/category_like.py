"""Category-like finite translation layer for Veyra transformers."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging
from typing import Iterable

from .ratio import RatioMode, ratio_from_ints, ratio_shadow
from .transformer import ModeTransformer, affine_transformer, apply_transformer, compose_transformers, identity_transformer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeyraObject:
    """Finite observer object: a named sample cloud, not a primitive set."""

    name: str
    samples: tuple[RatioMode, ...]
    observer: str = "ratio-shadow"

    @property
    def shadows(self) -> tuple[Fraction, ...]:
        """Return exact external shadows for the object's samples."""
        logger.debug("VeyraObject.shadows entry name=%s", self.name)
        result = tuple(ratio_shadow(sample) for sample in self.samples)
        logger.debug("VeyraObject.shadows exit result=%r", result)
        return result


@dataclass(frozen=True)
class VeyraMorphism:
    """Transformer-backed arrow between finite observer objects."""

    name: str
    source: VeyraObject
    target: VeyraObject
    transformer: ModeTransformer
    claim: str = "finite-transformer-shadow"


@dataclass(frozen=True)
class MorphismClosureRow:
    """Finite row saying whether a morphism lands inside its target shadow."""

    morphism: str
    source: str
    target: str
    graph: tuple[tuple[Fraction, Fraction], ...]
    status: str
    obstruction: str


@dataclass(frozen=True)
class InvariantRow:
    """Observer property tested before/after a morphism."""

    name: str
    morphism: str
    before: object
    after: object
    status: str
    obstruction: str


@dataclass(frozen=True)
class UniversalShadowRow:
    """Bounded identity/associativity-like shadow, not a universal theorem."""

    name: str
    status: str
    witness: tuple[tuple[Fraction, Fraction], ...]
    obstruction: str


def ratio_object(name: str, values: Iterable[int]) -> VeyraObject:
    """Build a finite Veyra object from integer ratio shadows."""
    logger.debug("ratio_object entry name=%s", name)
    result = VeyraObject(name, tuple(ratio_from_ints(value) for value in values))
    logger.debug("ratio_object exit name=%s count=%d", result.name, len(result.samples))
    return result


def morphism_graph(morphism: VeyraMorphism) -> tuple[tuple[Fraction, Fraction], ...]:
    """Return a finite graph shadow for a transformer-backed morphism."""
    logger.debug("morphism_graph entry name=%s", morphism.name)
    result = tuple((ratio_shadow(x), ratio_shadow(apply_transformer(morphism.transformer, x))) for x in morphism.source.samples)
    logger.debug("morphism_graph exit count=%d", len(result))
    return result


def morphism_closure_row(morphism: VeyraMorphism) -> MorphismClosureRow:
    """Check whether every output shadow belongs to the declared target object."""
    logger.debug("morphism_closure_row entry name=%s", morphism.name)
    graph = morphism_graph(morphism)
    target = set(morphism.target.shadows)
    missing = tuple(out for _, out in graph if out not in target)
    status = "closed" if not missing else "blocked"
    result = MorphismClosureRow(morphism.name, morphism.source.name, morphism.target.name, graph, status, "none" if status == "closed" else "target-shadow-miss")
    logger.debug("morphism_closure_row exit result=%r", result)
    return result


def compose_morphisms(outer: VeyraMorphism, inner: VeyraMorphism, name: str | None = None) -> VeyraMorphism:
    """Compose two matching finite morphism shadows."""
    logger.debug("compose_morphisms entry outer=%s inner=%s", outer.name, inner.name)
    if inner.target.shadows != outer.source.shadows:
        logger.error("compose_morphisms object mismatch inner=%s outer=%s", inner.name, outer.name)
        raise ValueError("inner target shadow must match outer source shadow")
    result = VeyraMorphism(name or f"{outer.name}∘{inner.name}", inner.source, outer.target, compose_transformers(outer.transformer, inner.transformer))
    logger.debug("compose_morphisms exit name=%s", result.name)
    return result


def category_like_examples() -> tuple[VeyraObject, ...]:
    """Return the bounded object vocabulary used by Sprint X3."""
    logger.debug("category_like_examples entry")
    result = (ratio_object("A", (0, 1, 2)), ratio_object("B", (1, 2, 3)), ratio_object("C", (2, 3, 4)), ratio_object("D", (4, 6, 8)))
    logger.debug("category_like_examples exit count=%d", len(result))
    return result


def category_like_morphisms() -> tuple[VeyraMorphism, ...]:
    """Return transformer-backed arrows for the X3 finite diagram."""
    logger.debug("category_like_morphisms entry")
    a, b, c, d = category_like_examples()
    result = (
        VeyraMorphism("id_A", a, a, identity_transformer()),
        VeyraMorphism("shift_AB", a, b, affine_transformer(ratio_from_ints(1), ratio_from_ints(1), "shift")),
        VeyraMorphism("shift_BC", b, c, affine_transformer(ratio_from_ints(1), ratio_from_ints(1), "shift")),
        VeyraMorphism("double_CD", c, d, affine_transformer(ratio_from_ints(2), ratio_from_ints(0), "double")),
    )
    logger.debug("category_like_morphisms exit count=%d", len(result))
    return result


def category_closure_rows() -> tuple[MorphismClosureRow, ...]:
    """Return closure rows for the default finite arrows."""
    logger.debug("category_closure_rows entry")
    result = tuple(morphism_closure_row(morphism) for morphism in category_like_morphisms())
    logger.debug("category_closure_rows exit count=%d", len(result))
    return result


def category_invariant_rows() -> tuple[InvariantRow, ...]:
    """Return finite invariant and counterexample rows."""
    logger.debug("category_invariant_rows entry")
    shift = category_like_morphisms()[1]
    graph = morphism_graph(shift)
    before_sum = sum(left for left, _ in graph)
    after_sum = sum(right for _, right in graph)
    result = (
        InvariantRow("sample-count", shift.name, len(graph), len(graph), "invariant", "none"),
        InvariantRow("sum-shadow", shift.name, before_sum, after_sum, "broken", "translation-changes-total"),
    )
    logger.debug("category_invariant_rows exit count=%d", len(result))
    return result


def category_universal_shadow_rows() -> tuple[UniversalShadowRow, ...]:
    """Return bounded identity/associativity/mismatch shadow rows."""
    logger.debug("category_universal_shadow_rows entry")
    id_a, f, g, h = category_like_morphisms()
    id_b = VeyraMorphism("id_B", f.target, f.target, identity_transformer())
    left_id = compose_morphisms(id_b, f, "id_B∘shift_AB")
    gf = compose_morphisms(g, f, "shift_BC∘shift_AB")
    hg = compose_morphisms(h, g, "double_CD∘shift_BC")
    assoc_left = compose_morphisms(h, gf, "h∘(g∘f)")
    assoc_right = compose_morphisms(hg, f, "(h∘g)∘f")
    exact_assoc = morphism_graph(assoc_left) == morphism_graph(assoc_right)
    mismatch_status = "blocked" if h.target.shadows != g.source.shadows else "exact"
    result = (
        UniversalShadowRow("left-identity", "exact" if morphism_graph(left_id) == morphism_graph(f) else "broken", morphism_graph(left_id), "none"),
        UniversalShadowRow("associative-sample", "exact" if exact_assoc else "broken", morphism_graph(assoc_left), "none" if exact_assoc else "graph-mismatch"),
        UniversalShadowRow("bad-composition", mismatch_status, (), "object-shadow-mismatch" if mismatch_status == "blocked" else "none"),
    )
    logger.debug("category_universal_shadow_rows exit count=%d", len(result))
    return result


def category_like_checklist() -> tuple[str, ...]:
    """Return Sprint X3 acceptance checklist."""
    logger.debug("category_like_checklist entry")
    result = ("objects are finite observer sample clouds", "morphisms are declared transformer-backed arrows", "invariants are tested rows, not assumed naturality", "identity/associativity rows are bounded universal shadows only")
    logger.debug("category_like_checklist exit count=%d", len(result))
    return result


def category_like_summary() -> dict[str, int]:
    """Return compact X3 category-like translation summary."""
    logger.debug("category_like_summary entry")
    closures = category_closure_rows(); invariants = category_invariant_rows(); universal = category_universal_shadow_rows()
    result = {"objects": len(category_like_examples()), "morphisms": len(closures), "closed": sum(row.status == "closed" for row in closures), "invariants": len(invariants), "broken": sum(row.status == "broken" for row in invariants), "universal": len(universal), "blocked": sum(row.status == "blocked" for row in universal), "checklist": len(category_like_checklist())}
    logger.debug("category_like_summary exit result=%r", result)
    return result
