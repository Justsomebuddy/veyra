//! Deterministic monotone precharge ledger for native finite synthesis.

use super::ast::SynthesisCoreError;
use super::diagnostics;

pub const MAX_CANDIDATES: usize = 2_048;
pub const MAX_CANONICAL_BYTES: usize = 8 * 1024 * 1024;
pub const MAX_EVALUATIONS: usize = 100_000;
pub const MAX_OUTPUT_BYTES: usize = 8 * 1024 * 1024;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BudgetLimits {
    pub candidate_limit: usize,
    pub canonical_bytes_limit: usize,
    pub evaluation_limit: usize,
    pub output_bytes_limit: usize,
}

impl Default for BudgetLimits {
    fn default() -> Self {
        Self {
            candidate_limit: MAX_CANDIDATES,
            canonical_bytes_limit: MAX_CANONICAL_BYTES,
            evaluation_limit: MAX_EVALUATIONS,
            output_bytes_limit: MAX_OUTPUT_BYTES,
        }
    }
}

impl BudgetLimits {
    fn validate(self) -> Result<Self, SynthesisCoreError> {
        if self.candidate_limit == 0
            || self.candidate_limit > MAX_CANDIDATES
            || self.canonical_bytes_limit == 0
            || self.canonical_bytes_limit > MAX_CANONICAL_BYTES
            || self.evaluation_limit == 0
            || self.evaluation_limit > MAX_EVALUATIONS
            || self.output_bytes_limit == 0
            || self.output_bytes_limit > MAX_OUTPUT_BYTES
        {
            return Err(SynthesisCoreError("invalid-budget-limits"));
        }
        Ok(self)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BudgetCutoff {
    Candidates,
    CanonicalBytes,
    Evaluations,
    OutputBytes,
}

impl BudgetCutoff {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Candidates => "candidate-limit",
            Self::CanonicalBytes => "canonical-bytes-limit",
            Self::Evaluations => "evaluation-limit",
            Self::OutputBytes => "transcript-output-bytes-limit",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BudgetSnapshot {
    pub limits: BudgetLimits,
    pub candidates: usize,
    pub canonical_bytes: usize,
    pub evaluations: usize,
    pub output_bytes: usize,
    pub cutoff: Option<BudgetCutoff>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BudgetLedger {
    limits: BudgetLimits,
    candidates: usize,
    canonical_bytes: usize,
    evaluations: usize,
    output_bytes: usize,
    cutoff: Option<BudgetCutoff>,
}

impl BudgetLedger {
    pub fn new(limits: BudgetLimits) -> Result<Self, SynthesisCoreError> {
        diagnostics::event("LEDGER_NEW_ENTER", "validating counter limits");
        let limits = match limits.validate() {
            Ok(limits) => limits,
            Err(error) => {
                diagnostics::event("LEDGER_NEW_REJECT", "counter limits are invalid");
                return Err(error);
            }
        };
        diagnostics::event("LEDGER_NEW_EXIT", "counter ledger initialized");
        Ok(Self {
            limits,
            candidates: 0,
            canonical_bytes: 0,
            evaluations: 0,
            output_bytes: 0,
            cutoff: None,
        })
    }

    pub const fn snapshot(&self) -> BudgetSnapshot {
        BudgetSnapshot {
            limits: self.limits,
            candidates: self.candidates,
            canonical_bytes: self.canonical_bytes,
            evaluations: self.evaluations,
            output_bytes: self.output_bytes,
            cutoff: self.cutoff,
        }
    }

    fn open(&self) -> Result<(), BudgetCutoff> {
        match self.cutoff {
            Some(reason) => Err(reason),
            None => Ok(()),
        }
    }

    fn checked_total(current: usize, amount: usize, limit: usize) -> Option<usize> {
        current
            .checked_add(amount)
            .filter(|updated| *updated <= limit)
    }

    fn stop<T>(&mut self, reason: BudgetCutoff) -> Result<T, BudgetCutoff> {
        if self.cutoff.is_none() {
            self.cutoff = Some(reason);
            diagnostics::event("LEDGER_CUTOFF", "sticky counter cutoff recorded");
        }
        Err(reason)
    }

    pub fn charge_catalog_item(&mut self, bytes: usize) -> Result<(), BudgetCutoff> {
        diagnostics::event("LEDGER_CATALOG_ENTER", "precharging catalog row");
        if let Err(reason) = self.open() {
            diagnostics::event("LEDGER_CATALOG_REJECT", "ledger is already stopped");
            return Err(reason);
        }
        if bytes == 0 {
            return self.stop(BudgetCutoff::CanonicalBytes);
        }
        let Some(candidates) = Self::checked_total(self.candidates, 1, self.limits.candidate_limit)
        else {
            return self.stop(BudgetCutoff::Candidates);
        };
        let Some(canonical_bytes) = Self::checked_total(
            self.canonical_bytes,
            bytes,
            self.limits.canonical_bytes_limit,
        ) else {
            return self.stop(BudgetCutoff::CanonicalBytes);
        };
        self.candidates = candidates;
        self.canonical_bytes = canonical_bytes;
        diagnostics::event("LEDGER_CATALOG_EXIT", "catalog row precharge committed");
        Ok(())
    }

    pub fn charge_evaluations(&mut self, count: usize) -> Result<(), BudgetCutoff> {
        diagnostics::event("LEDGER_EVAL_ENTER", "precharging observer evaluations");
        if let Err(reason) = self.open() {
            diagnostics::event("LEDGER_EVAL_REJECT", "ledger is already stopped");
            return Err(reason);
        }
        let Some(evaluations) =
            Self::checked_total(self.evaluations, count, self.limits.evaluation_limit)
        else {
            return self.stop(BudgetCutoff::Evaluations);
        };
        self.evaluations = evaluations;
        diagnostics::event("LEDGER_EVAL_EXIT", "evaluation precharge committed");
        Ok(())
    }

    pub fn charge_output(&mut self, bytes: usize) -> Result<(), BudgetCutoff> {
        diagnostics::event("LEDGER_OUTPUT_ENTER", "precharging trace output bytes");
        if let Err(reason) = self.open() {
            diagnostics::event("LEDGER_OUTPUT_REJECT", "ledger is already stopped");
            return Err(reason);
        }
        let Some(output_bytes) =
            Self::checked_total(self.output_bytes, bytes, self.limits.output_bytes_limit)
        else {
            return self.stop(BudgetCutoff::OutputBytes);
        };
        self.output_bytes = output_bytes;
        diagnostics::event("LEDGER_OUTPUT_EXIT", "trace output precharge committed");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn precharges_are_monotone_atomic_and_sticky() {
        let limits = BudgetLimits {
            candidate_limit: 1,
            ..BudgetLimits::default()
        };
        let mut ledger = BudgetLedger::new(limits).unwrap();
        ledger.charge_catalog_item(10).unwrap();
        let charged = ledger.snapshot();
        assert_eq!(charged.candidates, 1);
        assert_eq!(charged.canonical_bytes, 10);
        assert_eq!(
            ledger.charge_catalog_item(20),
            Err(BudgetCutoff::Candidates)
        );
        let stopped = ledger.snapshot();
        assert_eq!(stopped.candidates, 1);
        assert_eq!(stopped.canonical_bytes, 10);
        assert_eq!(ledger.charge_evaluations(1), Err(BudgetCutoff::Candidates));
        assert_eq!(ledger.snapshot(), stopped);
    }
}
