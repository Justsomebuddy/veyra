"""Generated mutation pressure for Veyra Core Language."""
from __future__ import annotations
from dataclasses import dataclass
import logging
import random
from .proof import proof_summary, trace_veyra_proof
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class VeyraMutationCase:
    """One generated bad/edge language case."""
    name: str
    category: str
    source: str
    expected_status: str
    reason: str
@dataclass(frozen=True)
class VeyraMutationResult:
    """Result of running one mutation case through proof tracing."""
    name: str
    category: str
    expected_status: str
    actual_status: str
    ok: bool
    parse_ok: bool
    steps: int
    obstruction: str

@dataclass(frozen=True)
class VeyraGeneratedMutationReport:
    """Aggregate generated-family mutation report."""
    families: int
    cases: int
    blocked: int
    unknown: int
    ready: int
    unexpected: int

@dataclass(frozen=True)
class VeyraPropertyFuzzReport:
    """Aggregate deterministic property-fuzz report."""
    seed: int
    families: int
    cases: int
    blocked: int
    unknown: int
    ready: int
    unexpected: int
    shrunk: int

@dataclass(frozen=True)
class VeyraMutationReport:
    """Aggregate mutation pressure report."""
    cases: int
    blocked: int
    unknown: int
    ready: int
    unexpected: int
def language_mutation_cases() -> tuple[VeyraMutationCase, ...]:
    """Return deterministic grammar/type/inference mutation cases."""
    logger.debug("language_mutation_cases entry")
    cases = (
        VeyraMutationCase("missing-close", "grammar", "echo(nod:a,nod:b,observer:kind", "blocked", "unclosed call"),
        VeyraMutationCase("invalid-char", "grammar", "nod:!", "blocked", "invalid atom label"),
        VeyraMutationCase("trailing-source", "grammar", "nod:a nod:b", "blocked", "two roots in one source"),
        VeyraMutationCase("missing-label", "grammar", "nod:", "blocked", "atom label absent"),
        VeyraMutationCase("tact-value", "typing", "tact(nod:a,value:x)", "blocked", "tact requires two nods"),
        VeyraMutationCase("breath-nod", "typing", "breath(nod:a)", "blocked", "breath requires tacts"),
        VeyraMutationCase("mode-tact", "typing", "mode(tact(nod:a,nod:b))", "blocked", "mode requires breath"),
        VeyraMutationCase("echo-nonobserver", "typing", "echo(nod:a,nod:b,nod:o)", "blocked", "echo requires observer"),
        VeyraMutationCase("trace-mismatch", "inference", "echo(nod:a,nod:b,observer:trace)", "blocked", "trace observer sees label mismatch"),
        VeyraMutationCase("unknown-observer", "inference", "echo(nod:a,nod:b,observer:mystery)", "unknown", "valid relation but observer has no semantics"),
    )
    logger.debug("language_mutation_cases exit count=%d", len(cases))
    return cases
def run_language_mutation_case(case: VeyraMutationCase) -> VeyraMutationResult:
    """Run one mutation case and compare to expected status."""
    logger.debug("run_language_mutation_case entry case=%r", case)
    language_logger = logging.getLogger("src.core.language")
    old_level = language_logger.level
    language_logger.setLevel(logging.CRITICAL)
    try:
        trace = trace_veyra_proof(case.source)
    finally:
        language_logger.setLevel(old_level)
    summary = proof_summary(trace)
    actual = trace.final_check.status
    obstruction = trace.final_check.obstruction or trace.diagnostic
    result = VeyraMutationResult(case.name, case.category, case.expected_status, actual, actual == case.expected_status, trace.parse_ok, summary.steps, obstruction)
    logger.debug("run_language_mutation_case exit result=%r", result)
    return result
def run_language_mutations() -> tuple[VeyraMutationResult, ...]:
    """Run all deterministic mutation cases."""
    logger.debug("run_language_mutations entry")
    result = tuple(run_language_mutation_case(case) for case in language_mutation_cases())
    logger.debug("run_language_mutations exit count=%d unexpected=%d", len(result), sum(not item.ok for item in result))
    return result
def language_mutation_report() -> VeyraMutationReport:
    """Return compact mutation report."""
    logger.debug("language_mutation_report entry")
    results = run_language_mutations()
    statuses = [item.actual_status for item in results]
    report = VeyraMutationReport(len(results), statuses.count("blocked"), statuses.count("unknown"), statuses.count("ready"), sum(not item.ok for item in results))
    logger.debug("language_mutation_report exit report=%r", report)
    return report
def mutation_language_checklist() -> tuple[str, ...]:
    """Return v0.4 mutation-pressure capabilities."""
    logger.debug("mutation_language_checklist entry")
    result = ("grammar-mutations", "typing-mutations", "inference-mutations", "expected-status", "proof-trace-runner", "aggregate-report")
    logger.debug("mutation_language_checklist exit count=%d", len(result))
    return result

def generated_language_mutation_cases() -> tuple[VeyraMutationCase, ...]:
    """Generate deterministic mutation families over arity/constructor/observer/label."""
    logger.debug("generated_language_mutation_cases entry")
    arity = [
        ("nod-two-rez", "nod(rez:a,rez:b)"), ("tact-zero", "tact()"),
        ("tact-one", "tact(nod:a)"), ("tact-three", "tact(nod:a,nod:b,nod:c)"),
        ("breath-zero", "breath()"), ("breath-two-nod", "breath(nod:a,nod:b)"),
        ("mode-empty", "mode()"), ("echo-two", "echo(nod:a,nod:b)"),
    ]
    constructor = [
        ("mode-nod", "mode(nod:a)"), ("trace-empty", "trace()"),
        ("weight-trace-only", "weight(trace(nod:a))"), ("shell-nod", "shell(nod:a)"),
    ]
    observer = [
        ("unknown-aura", "echo(nod:a,nod:b,observer:aura)", "unknown"),
        ("unknown-phase", "echo(nod:a,nod:b,observer:phase)", "unknown"),
        ("trace-label-block", "echo(nod:a,nod:b,observer:trace)", "blocked"),
        ("boundary-block", "echo(tact(nod:a,nod:b),tact(nod:a,nod:c),observer:boundary)", "blocked"),
    ]
    labels = [
        ("bang-label", "nod:!"), ("comma-label", "nod:a,b"),
        ("close-label", "nod:)"), ("space-label", "nod: "),
    ]
    cases = [VeyraMutationCase(name, "arity", source, "blocked", "generated arity mutation") for name, source in arity]
    cases += [VeyraMutationCase(name, "constructor", source, "blocked", "generated constructor mutation") for name, source in constructor]
    cases += [VeyraMutationCase(name, "observer", source, status, "generated observer mutation") for name, source, status in observer]
    cases += [VeyraMutationCase(name, "label", source, "blocked", "generated label mutation") for name, source in labels]
    result = tuple(cases)
    logger.debug("generated_language_mutation_cases exit count=%d", len(result))
    return result
def run_generated_language_mutations() -> tuple[VeyraMutationResult, ...]:
    """Run generated mutation families through proof tracing."""
    logger.debug("run_generated_language_mutations entry")
    result = tuple(run_language_mutation_case(case) for case in generated_language_mutation_cases())
    logger.debug("run_generated_language_mutations exit count=%d unexpected=%d", len(result), sum(not item.ok for item in result))
    return result
def generated_language_mutation_report() -> VeyraGeneratedMutationReport:
    """Return compact generated-family mutation report."""
    logger.debug("generated_language_mutation_report entry")
    results = run_generated_language_mutations()
    statuses = [item.actual_status for item in results]
    families = len({item.category for item in results})
    report = VeyraGeneratedMutationReport(families, len(results), statuses.count("blocked"), statuses.count("unknown"), statuses.count("ready"), sum(not item.ok for item in results))
    logger.debug("generated_language_mutation_report exit report=%r", report)
    return report
def generated_mutation_language_checklist() -> tuple[str, ...]:
    """Return v0.5 generated mutation-family capabilities."""
    logger.debug("generated_mutation_language_checklist entry")
    result = ("arity-family", "constructor-family", "observer-family", "label-family", "proof-trace-family-runner", "family-report")
    logger.debug("generated_mutation_language_checklist exit count=%d", len(result))
    return result

def property_language_mutation_cases(seed: int = 613, count: int = 24) -> tuple[VeyraMutationCase, ...]:
    """Generate deterministic property-fuzz language mutations."""
    logger.debug("property_language_mutation_cases entry seed=%d count=%d", seed, count)
    rng = random.Random(seed)
    families = ("property-arity", "property-constructor", "property-observer", "property-label")
    result: list[VeyraMutationCase] = []
    for index in range(count):
        family = families[index % len(families)]
        label = chr(97 + index % 6) + chr(97 + (index + 1) % 6)
        if family == "property-arity":
            source = rng.choice(("tact()", f"tact(nod:{label})", f"breath(nod:{label},nod:{label}x)", "mode()", f"echo(nod:{label},nod:{label}x)"))
            status = "blocked"
        elif family == "property-constructor":
            source = rng.choice((f"mode(nod:{label})", f"breath(nod:{label})", f"tact(nod:{label},value:{label})", f"shell(nod:{label})"))
            status = "blocked"
        elif family == "property-observer" and (index // len(families)) % 2 == 0:
            source = f"echo(nod:{label},nod:{label}x,observer:unseenobserver{index})"
            status = "unknown"
        elif family == "property-observer":
            source = f"echo(nod:{label},nod:{label}x,observer:trace)"
            status = "blocked"
        else:
            source = rng.choice((f"nod:{label}!", f"nod:{label},{label}x", "nod:)", f"nod:{label} {label}x"))
            status = "blocked"
        result.append(VeyraMutationCase(f"prop-{index:02d}-{family[9:]}", family, source, status, "deterministic property fuzz mutation"))
    final = tuple(result)
    logger.debug("property_language_mutation_cases exit count=%d", len(final))
    return final

def shrink_language_mutation_case(case: VeyraMutationCase) -> VeyraMutationCase:
    """Return a deterministic minimal representative for a mutation case."""
    logger.debug("shrink_language_mutation_case entry case=%r", case)
    if case.category.endswith("arity"):
        source = "tact()"; status = "blocked"; family = "property-arity"
    elif case.category.endswith("constructor"):
        source = "mode(nod:a)"; status = "blocked"; family = "property-constructor"
    elif case.category.endswith("observer") and case.expected_status == "unknown":
        source = "echo(nod:a,nod:b,observer:aura)"; status = "unknown"; family = "property-observer"
    elif case.category.endswith("observer"):
        source = "echo(nod:a,nod:b,observer:trace)"; status = "blocked"; family = "property-observer"
    else:
        source = "nod:!"; status = "blocked"; family = "property-label"
    result = VeyraMutationCase(f"{case.name}-shrunk", family, source, status, "minimal shrink representative")
    logger.debug("shrink_language_mutation_case exit result=%r", result)
    return result

def run_property_language_fuzz(seed: int = 613, count: int = 24) -> tuple[VeyraMutationResult, ...]:
    """Run deterministic property-fuzz mutations."""
    logger.debug("run_property_language_fuzz entry seed=%d count=%d", seed, count)
    result = tuple(run_language_mutation_case(case) for case in property_language_mutation_cases(seed, count))
    logger.debug("run_property_language_fuzz exit count=%d unexpected=%d", len(result), sum(not item.ok for item in result))
    return result

def property_language_fuzz_report(seed: int = 613, count: int = 24) -> VeyraPropertyFuzzReport:
    """Return deterministic property-fuzz aggregate plus shrink count."""
    logger.debug("property_language_fuzz_report entry seed=%d count=%d", seed, count)
    cases = property_language_mutation_cases(seed, count)
    results = tuple(run_language_mutation_case(case) for case in cases)
    shrink_results = tuple(run_language_mutation_case(shrink_language_mutation_case(case)) for case in cases)
    statuses = [item.actual_status for item in results]
    shrunk = sum(item.ok for item in shrink_results)
    report = VeyraPropertyFuzzReport(seed, len({case.category for case in cases}), len(results), statuses.count("blocked"), statuses.count("unknown"), statuses.count("ready"), sum(not item.ok for item in results), shrunk)
    logger.debug("property_language_fuzz_report exit report=%r", report)
    return report

def property_fuzz_language_checklist() -> tuple[str, ...]:
    """Return v0.6 property-fuzz/shrinker capabilities."""
    logger.debug("property_fuzz_language_checklist entry")
    result = ("seeded-generator", "four-property-families", "expected-status-oracle", "proof-trace-property-runner", "deterministic-shrinker", "property-fuzz-report")
    logger.debug("property_fuzz_language_checklist exit count=%d", len(result))
    return result
