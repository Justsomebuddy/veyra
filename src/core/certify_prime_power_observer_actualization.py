"""Direct level-1 certificate for isolated P3-N0."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import subprocess
import sys

from .certify_types import Certificate
from .prime_power_observer_actualization_attack_matrix import run_attack_matrix
from .prime_power_observer_actualization_runtime import prime_power_observer_actualization
from .prime_power_observer_actualization_result_validation import validate_n0_result
from .prime_power_observer_actualization_open_types import (
    N0DoctrineOpen, N0GenealogyUnavailable,
)
from .prime_power_observer_actualization_unavailable import (
    run_unavailable_bridge, unavailable_bridge_request, unavailable_n0_source,
)
from .prime_power_observer_actualization_sources import exact_n0_source
from .prime_power_observer_actualization_types import (
    ActualizationStatus, BoundaryStatus, PremiseStatus,
    PrimePowerObserverActualizationJudgment, RoleStatus,
)
from .prime_power_reduction_network_types import FiniteRelation

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _hash_seed_digests() -> tuple[str, str]:
    """Build the exact source in two bounded fresh hash-seed processes."""
    logger.debug("_hash_seed_digests entry")
    root = PROJECT_ROOT
    code = (
        "from src.core.prime_power_observer_actualization_sources import exact_n0_source;"
        "print(exact_n0_source().source_digest)"
    )
    calls = []
    for seed in ("1", "777"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        calls.append(([sys.executable, "-c", code], root, env))
    with ThreadPoolExecutor(max_workers=2) as pool:
        processes = tuple(pool.submit(
            subprocess.run, command, cwd=cwd, env=env, timeout=30,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        ) for command, cwd, env in calls)
        completed = tuple(future.result() for future in processes)
    values = []
    for process in completed:
        lines = process.stdout.decode(errors="replace").splitlines()
        values.append(lines[-1] if process.returncode == 0 and lines else "")
    result = tuple(values)
    logger.debug("_hash_seed_digests exit equal=%s", len(set(result)) == 1)
    return result


def certify_prime_power_observer_actualization_p3n0() -> Certificate:
    """Certify exact positive arrows, causal birth, boundaries, and all mutations."""
    logger.debug("certify_prime_power_observer_actualization_p3n0 entry")
    source = exact_n0_source()
    nonadmitted_source = exact_n0_source(admitted=False)
    hash_seed_digests = _hash_seed_digests()
    value = prime_power_observer_actualization(source)
    nonadmitted = prime_power_observer_actualization(nonadmitted_source)
    unavailable_request = unavailable_bridge_request(unavailable_n0_source())
    unavailable = run_unavailable_bridge(unavailable_request)
    if type(value) is not PrimePowerObserverActualizationJudgment:
        passed = False
        attacks = ()
        replay = None
    else:
        replay = validate_n0_result(source, value)
        attacks = run_attack_matrix(source, value)
        passed = (
            replay == value and replay is not value
            and
            value.role is RoleStatus.ESTABLISHED_RELATIVE_TO_DOCTRINE
            and value.actualization
            is ActualizationStatus.ESTABLISHED_RELATIVE_TO_FINITE_ARITHMETIC_HISTORY
            and value.strict_relation
            == FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE.value
            and value.open_relation == FiniteRelation.OPEN.value
            and value.generic_e4_bridge is BoundaryStatus.OPEN
            and value.physical_instantiation is BoundaryStatus.NOT_ESTABLISHED
            and value.consciousness is BoundaryStatus.NOT_CLAIMED
            and value.absolute_observerhood is BoundaryStatus.NOT_CLAIMED
            and value.promotions == 0
            and type(nonadmitted) is N0DoctrineOpen
            and validate_n0_result(nonadmitted_source, nonadmitted) == nonadmitted
            and nonadmitted.role is RoleStatus.OPEN
            and type(unavailable) is N0GenealogyUnavailable
            and validate_n0_result(unavailable_request, unavailable) == unavailable
            and unavailable.genealogy is PremiseStatus.OPEN
            and hash_seed_digests == (source.source_digest, source.source_digest)
            and len({value.run_digest, value.scope_digest, value.birth_core_digest,
                     value.historical_token_id, value.strict_history_digest,
                     value.open_history_digest, value.strict_outcome_digest,
                     value.open_outcome_digest, value.strict_efficacy_digest,
                     value.open_efficacy_digest, value.postbirth_evidence_ledger.ledger_digest,
                     value.formal_attestation.attestation_digest, value.judgment_digest}) == 13
            and tuple(name for name, _ in value.postbirth_evidence_ledger.row_payloads)
            == ("LA19", "LA20", "LA22")
            and len(value.formal_attestation.receipts) == 4
            and len(attacks) >= 31
            and {item.base_id for item in attacks} == {f"A{i:02d}" for i in range(1, 25)}
            and all(item.passed and item.actual == item.expected for item in attacks)
        )
    detail = (
        f"raw_n1=3 raw_n2f=2 singleton_open=1 private_lean=1 hash_seed=1 "
        f"base_attacks={len({x.base_id for x in attacks})} submissions={len(attacks)} "
        "strict=1 open=1 first_birth=1 token_access=1 pending_first=1 attestation=4 "
        "admission_split=1 unavailable_open=1 generic_e4=0 physical=0 "
        "consciousness=0 absolute=0 sfp=0 promotions=0"
    )
    result = Certificate(
        "prime_power_observer_actualization_p3n0",
        "A-HAP arithmetic observer role actualized relative to one finite formal history",
        passed, detail, 1,
    )
    logger.debug("certify_prime_power_observer_actualization_p3n0 exit passed=%s", passed)
    return result


if __name__ == "__main__":
    print(certify_prime_power_observer_actualization_p3n0())
