"""Deterministic hostile pressure for the internal P3-N6-W runtime slice."""

from __future__ import annotations

from dataclasses import replace
import logging
from types import SimpleNamespace

import pytest

from src.core.padic_completion import (
    padic_completion_ledger,
    padic_completion_package,
    padic_completion_policy,
    padic_completion_theorem_source,
    padic_tower_doctrine,
    prime_source,
)
from src.core.padic_family_introduction import (
    integer_source,
    n1_assumption_ledger,
    n1_introduction_package,
    n1_policy,
    n1_theorem_source,
)
from src.core.prime_power_information_witness_formal import (
    N6WCompileOutcomeV1,
    _symbols,
    capture_sources,
)
from src.core.prime_power_information_witness_formal_runner import compile_sources
from src.core.prime_power_information_witness_request import witness_request
from src.core.prime_power_information_witness_runtime import derive_witnesses
from src.core.prime_power_information_witness_validation import validate_result
from src.core.prime_power_information_witness_types import (
    N6WExecutionFailureV1,
    N6WResourceLimitV1,
)
from src.core.prime_power_unbounded_common import P3N6ValidationError
from src.core.prime_power_unbounded_sources import policy as n6_policy
from src.core.prime_power_unbounded_types import N6FormalFailureKind

logger = logging.getLogger(__name__)


def _packages(p: int = 5):
    """Build one exact same-prime N1-zero/PΩ2 pair."""
    logger.debug("_packages entry p=%d", p)
    prime = prime_source(p)
    doctrine = padic_tower_doctrine()
    pomega2 = padic_completion_package(
        prime, doctrine, padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy(),
    )
    zero = n1_introduction_package(
        prime, integer_source(0), doctrine, n1_theorem_source(),
        n1_assumption_ledger(), n1_policy(),
    )
    logger.debug("_packages exit")
    return zero, pomega2


def _dependencies(request):
    """Return minimal immutable fields consumed after dependency type checking."""
    logger.debug("_dependencies entry")
    base = request.base_request
    zero = SimpleNamespace(
        prime_digest=base.pomega2.prime.source_digest,
        doctrine_digest=base.pomega2.doctrine.doctrine_digest,
        family_term_digest="1" * 64,
    )
    late = SimpleNamespace(
        prime_digest=zero.prime_digest, doctrine_digest=zero.doctrine_digest,
        family_term_digest="2" * 64,
    )
    completion = SimpleNamespace(
        prime_digest=zero.prime_digest,
        doctrine_digest=zero.doctrine_digest,
        package_digest=base.pomega2.package_digest,
    )
    logger.debug("_dependencies exit")
    return zero, late, completion


def _outcome(request, kind=None, rows=None) -> N6WCompileOutcomeV1:
    """Build one exact synthetic transcript for runtime branch isolation."""
    logger.debug("_outcome entry kind=%s", None if kind is None else kind.value)
    result = N6WCompileOutcomeV1(
        kind, b"bounded-output", (),
        request.theorem.theorem_axiom_rows if rows is None else rows,
        "a" * 64, (), "b" * 64,
    )
    logger.debug("_outcome exit")
    return result


def _fast(monkeypatch, request, *, kind=None, rows=None, continuity=True):
    """Isolate result semantics from already-covered external compiler cost."""
    logger.debug("_fast entry")
    from src.core import prime_power_information_witness_runtime as runtime

    monkeypatch.setattr(runtime, "_dependencies", lambda *_: _dependencies(request))
    monkeypatch.setattr(runtime, "capture_sources", lambda *_: (b"a", b"b", b"c", b"d"))
    monkeypatch.setattr(runtime, "compile_sources", lambda *_: _outcome(request, kind, rows))
    monkeypatch.setattr(runtime, "continuity_holds", lambda *_: continuity)
    result = derive_witnesses(request)
    logger.debug("_fast exit type=%s", type(result).__name__)
    return result


def test_fresh_validation_rejects_partial_prefix_depth_pair_and_basis_splices(monkeypatch) -> None:
    """Every positive field is replay-bound; no sample, shifted depth or swapped pair passes."""
    logger.debug("test_fresh_validation_rejects_partial_prefix_depth_pair_and_basis_splices entry")
    request = witness_request(*_packages(), 3)
    result = _fast(monkeypatch, request)
    assert type(result) is tuple
    assert validate_result(result, request) is result
    witness, basis = result
    attacks = (
        (replace(witness, prefix_rows=witness.prefix_rows[-1:]), basis),
        (replace(witness, later=witness.later + 1), basis),
        (replace(witness, right_integer=witness.right_integer + 1), basis),
        (replace(witness, left_integer=witness.right_integer,
                 right_integer=witness.left_integer), basis),
        (replace(witness, later_right_residue=witness.later_left_residue), basis),
        (witness, replace(basis, completed_index_admitted=True)),
        (witness, replace(basis, promotions=1)),
    )
    for forged in attacks:
        with pytest.raises(P3N6ValidationError):
            validate_result(forged, request)
    with pytest.raises(P3N6ValidationError, match="supported-arm"):
        validate_result(object(), request)  # type: ignore[arg-type]
    logger.debug("test_fresh_validation_rejects_partial_prefix_depth_pair_and_basis_splices exit")


def test_dependency_failure_precedes_source_and_is_not_refutation(monkeypatch) -> None:
    """Missing released dependencies stop before capture as typed operational failure."""
    logger.debug("test_dependency_failure_precedes_source_and_is_not_refutation entry")
    from src.core import prime_power_information_witness_runtime as runtime

    request = witness_request(*_packages(), 2)
    monkeypatch.setattr(runtime, "_dependencies", lambda *_: None)
    monkeypatch.setattr(
        runtime, "capture_sources",
        lambda *_: (_ for _ in ()).throw(AssertionError("source-after-dependency-failure")),
    )
    result = derive_witnesses(request)
    assert type(result) is N6WExecutionFailureV1
    assert result.kind is N6FormalFailureKind.DEPENDENCY_REPLAY_FAILURE
    assert not isinstance(result, N6WResourceLimitV1)
    logger.debug("test_dependency_failure_precedes_source_and_is_not_refutation exit")


def test_formal_failure_axiom_failure_and_continuity_failure_stay_distinct(monkeypatch) -> None:
    """Timeout, theorem-row drift and source drift retain exact operational kinds."""
    logger.debug("test_formal_failure_axiom_failure_and_continuity_failure_stay_distinct entry")
    request = witness_request(*_packages(), 2)
    timeout = _fast(monkeypatch, request, kind=N6FormalFailureKind.TIMEOUT)
    assert type(timeout) is N6WExecutionFailureV1
    assert timeout.kind is N6FormalFailureKind.TIMEOUT
    axiom = _fast(monkeypatch, request, rows=())
    assert type(axiom) is N6WExecutionFailureV1
    assert axiom.kind is N6FormalFailureKind.COMPILE_ERROR
    drift = _fast(monkeypatch, request, continuity=False)
    assert type(drift) is N6WExecutionFailureV1
    assert drift.kind is N6FormalFailureKind.CONTINUITY_DRIFT
    logger.debug("test_formal_failure_axiom_failure_and_continuity_failure_stay_distinct exit")


def test_resource_refusal_wins_over_dependency_and_formal_failures(monkeypatch) -> None:
    """Hard preflight has deterministic priority and carries no positive tuple."""
    logger.debug("test_resource_refusal_wins_over_dependency_and_formal_failures entry")
    from src.core import prime_power_information_witness_runtime as runtime

    request = witness_request(*_packages(), 5000)
    monkeypatch.setattr(
        runtime, "_dependencies",
        lambda *_: (_ for _ in ()).throw(AssertionError("dependency-after-refusal")),
    )
    monkeypatch.setattr(
        runtime, "compile_sources",
        lambda *_: (_ for _ in ()).throw(AssertionError("formal-after-refusal")),
    )
    result = derive_witnesses(request)
    assert type(result) is N6WResourceLimitV1
    assert not hasattr(result, "basis_digest")
    assert not hasattr(result, "witness_digest")
    logger.debug("test_resource_refusal_wins_over_dependency_and_formal_failures exit")


def test_source_shape_and_byte_drift_fail_before_base_compilation(monkeypatch) -> None:
    """Changed imports/placeholders or any captured leaf byte fail before Lean."""
    logger.debug("test_source_shape_and_byte_drift_fail_before_base_compilation entry")
    request = witness_request(*_packages(), 1)
    valid = capture_sources(request.theorem)
    for payload in (
        valid[-1].replace(b"import VeyraPrimePowerUnbounded", b"import Attacker"),
        valid[-1] + b"\naxiom attacker : True\n",
        valid[-1].replace(b"THM_P3N6W_002_prefix", b"THM_P3N6W_002_sample"),
    ):
        with pytest.raises(P3N6ValidationError):
            _symbols(payload)
    from src.core import prime_power_information_witness_formal_runner as runner

    monkeypatch.setattr(
        runner, "compile_e_sources",
        lambda *_: (_ for _ in ()).throw(AssertionError("base-compile-before-byte-check")),
    )
    changed = (valid[0], valid[1], valid[2], valid[3] + b"\n")
    with pytest.raises(P3N6ValidationError, match="captured-byte-drift"):
        compile_sources(request.theorem, n6_policy(), changed)
    logger.debug("test_source_shape_and_byte_drift_fail_before_base_compilation exit")


def test_replaceable_source_policy_bindings_cannot_redefine_canonical_identity(
    monkeypatch,
) -> None:
    """Module constants/functions cannot repin source, TCB, interface or hard caps."""
    logger.debug("test_replaceable_source_policy_bindings entry")
    from src.core import prime_power_information_witness_sources as sources

    canonical_source = sources.theorem_source()
    canonical_policy = sources.policy()
    replacements = {
        "ARTIFACT_PATH": "proofs/lean/Attacker.lean",
        "ARTIFACT_SHA256": "0" * 64,
        "THEOREM_IDS": ("attacker",),
        "AXIOM_ROWS": (("attacker", ()),),
        "N6E_INTERFACE_ROOT": "1" * 64,
        "MAX_REQUESTED_DEPTH": 2**63 - 1,
        "MAX_PREFIX_ROWS": 2**63 - 1,
        "MAX_INTEGER_BITS": 2**63 - 1,
        "n6_policy": lambda: object(),
        "n6_theorem_source": lambda *_: object(),
    }
    for name, replacement in replacements.items():
        monkeypatch.setattr(sources, name, replacement, raising=False)
    assert sources.theorem_source() == canonical_source
    assert sources.snapshot_theorem_source(canonical_source) == canonical_source
    assert sources.policy() == canonical_policy
    assert sources.snapshot_policy(canonical_policy) == canonical_policy
    with monkeypatch.context() as scoped:
        scoped.setattr(sources, "N6_CAPABILITY_MODEL", "attacker-capability")
        with pytest.raises(RuntimeError, match="capability boundary drift"):
            sources.theorem_source()
    logger.debug("test_replaceable_source_policy_bindings exit")


def test_positive_binding_validation_executes_no_hostile_comparison(monkeypatch) -> None:
    """Nested digest objects are rejected before any attacker __ne__ callback."""
    logger.debug("test_positive_binding_validation_executes_no_hostile_comparison entry")
    request = witness_request(*_packages(), 2)
    result = _fast(monkeypatch, request)
    assert type(result) is tuple
    witness, basis = result
    callbacks: list[str] = []

    class HostileDigest:
        def __ne__(self, _other: object) -> bool:
            callbacks.append("__ne__")
            return False

    forged = (replace(witness, basis_digest=HostileDigest()), basis)
    with pytest.raises(P3N6ValidationError):
        validate_result(forged, request)  # type: ignore[arg-type]
    assert callbacks == []
    logger.debug("test_positive_binding_validation_executes_no_hostile_comparison exit")
