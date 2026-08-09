"""Collision-safe aliases for the isolated, not-yet-root-integrated P3-N0 API."""

from . import core as _n0

P3N0ValidationError = _n0.N0ValidationError
P3N0PremiseStatus = _n0.PremiseStatus
P3N0DoctrineAdmission = _n0.DoctrineAdmission
P3N0RoleStatus = _n0.RoleStatus
P3N0ActualizationStatus = _n0.ActualizationStatus
P3N0BoundaryStatus = _n0.BoundaryStatus
P3N0SuffixSelector = _n0.SuffixSelector
P3N0Policy = _n0.N0Policy
P3N0Source = _n0.N0Source
P3N0Judgment = _n0.PrimePowerObserverActualizationJudgment
P3N0DoctrineOpen = _n0.N0DoctrineOpen
P3N0GenealogyUnavailable = _n0.N0GenealogyUnavailable
P3N0UnavailableSource = _n0.N0UnavailableSource
P3N0TheoremSource = _n0.N0TheoremSource
P3N0ResourceLimit = _n0.N0ResourceLimit
P3N0FormalFailure = _n0.N0FormalFailure
P3N0_ARTIFACT_PATH = _n0.ARTIFACT_PATH
P3N0_ARTIFACT_SHA256 = _n0.ARTIFACT_SHA256
P3N0_THEOREM_IDS = _n0.THEOREM_IDS
P3N0_PREBIRTH_LEDGER_DIGEST_ORACLE = _n0.N0_PREBIRTH_LEDGER_DIGEST_ORACLE
P3N0_POSTBIRTH_LEDGER_DIGEST_ORACLE = _n0.N0_POSTBIRTH_LEDGER_DIGEST_ORACLE
P3N0_HISTORY_LEDGER_DIGEST_ORACLE = _n0.N0_HISTORY_LEDGER_DIGEST_ORACLE
P3N0_NONADMITTED_PREBIRTH_LEDGER_DIGEST_ORACLE = (
    _n0.N0_NONADMITTED_PREBIRTH_LEDGER_DIGEST_ORACLE
)
P3N0_NONADMITTED_POSTBIRTH_LEDGER_DIGEST_ORACLE = (
    _n0.N0_NONADMITTED_POSTBIRTH_LEDGER_DIGEST_ORACLE
)
P3N0_NONADMITTED_HISTORY_LEDGER_DIGEST_ORACLE = (
    _n0.N0_NONADMITTED_HISTORY_LEDGER_DIGEST_ORACLE
)

p3n0_exact_source = _n0.exact_n0_source
p3n0_policy = _n0.n0_policy
p3n0_actualize = _n0.prime_power_observer_actualization
p3n0_validate_result = _n0.validate_n0_result
p3n0_counterfactual_histories = _n0.counterfactual_histories
p3n0_discrimination_candidate = _n0.discrimination_candidate
p3n0_refute_discrimination = _n0.refute_discrimination
p3n0_separator_candidate = _n0.separator_candidate
p3n0_refute_separator = _n0.refute_separator
p3n0_unavailable_source = _n0.unavailable_n0_source
p3n0_unavailable_bridge_request = _n0.unavailable_bridge_request
p3n0_run_unavailable_bridge = _n0.run_unavailable_bridge

__all__ = tuple(name for name in globals() if name.startswith(("P3N0", "p3n0")))
