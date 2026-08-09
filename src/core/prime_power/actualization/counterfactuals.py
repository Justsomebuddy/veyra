"""Fresh replay helper for constructing canonical P3-N0 counterfactual histories."""

from __future__ import annotations

import logging

from ...observer.network.core import observer_network_judgment
from .common import reject
from .history import (
    REQUIRED_ACCESS, finalize_history, pending_histories, replay_evidence,
)
from .history_validation import (
    access_status, audit_counterfactual_pair, validate_history,
)
from ..reduction_network.core import prime_power_reduction_judgment
from ..reduction_network.types import PrimePowerReductionJudgment

logger = logging.getLogger(__name__)


def counterfactual_histories(source):
    """Freshly replay P3-T/N2 before constructing either exact outcome event."""
    logger.debug("counterfactual_histories entry")
    pending = pending_histories(source)
    histories = []
    for index, wrapper in enumerate((source.strict_package, source.open_package)):
        network = observer_network_judgment(wrapper.network_source, wrapper.network_policy)
        result = prime_power_reduction_judgment(wrapper.raw_package)
        if type(result) is not PrimePowerReductionJudgment:
            reject("n0-counterfactual-helper-positive-n2-required")
        arrow = next((item for item in result.finite_arrows
                      if (item.fine_depth, item.coarse_depth) == source.scope.arrow), None)
        if arrow is None:
            reject("n0-counterfactual-helper-arrow-missing")
        replay = replay_evidence(source, pending[index], network, result, arrow)
        history = finalize_history(source, pending[index], replay)
        validate_history(source, history, network, result, arrow)
        histories.append(history)
    value = tuple(histories)
    logger.debug("counterfactual_histories exit")
    return value


__all__ = (
    "REQUIRED_ACCESS", "access_status", "audit_counterfactual_pair",
    "counterfactual_histories",
)
