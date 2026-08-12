//! Deterministic train-only CEGIS over the exact native R14.1 catalog.

use std::collections::HashSet;

use super::ast::{infer_observer_kind, ObserverExpr, SynthesisCoreError};
use super::budget::{BudgetCutoff, BudgetLedger, BudgetLimits, BudgetSnapshot};
use super::canonical::canonical_observer_bytes;
use super::diagnostics;
use super::grammar::{
    GrammarConfig, GrammarEnumeration, ObserverCandidate, DEFAULT_CANDIDATES,
    DEFAULT_CANONICAL_BYTES, DEFAULT_CATALOG_DIGEST, DEFAULT_MAX_ROW_BYTES, DEFAULT_STRATA,
};
use super::hash::sha256_hex;
use super::semantics::{echo, EchoOutcome, Recurrence};

const CASE_SCHEMA: &str = "veyra.observer-synthesis-v2.case.r14.3a.v1";
const TRACE_SCHEMA: &str = "veyra.native-observer-synthesis.cegis-trace.r14.3b.v1";
const LIMITS_SCHEMA: &str = "veyra.native-observer-synthesis.cegis-limits.r14.3b.v1";
const TRAINING_SCHEMA: &str = "veyra.observer-synthesis-v2.cegis-training.r14.3b.v1";
const MAX_TRAIN_CASES: usize = 1_024;
const MAX_CASE_ID: u32 = (1 << 31) - 1;

pub const CEGIS_BOUNDARY: &str =
    "complete only for the exact 1,565-row R14.1 grammar and explicit ordered TRAIN cases under deterministic counter limits; no holdout, wall-clock, address-space, general-synthesis, minimality, or promotion claim";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExpectedRelation {
    Echo,
    Separate,
    DomainBlocked,
}

impl ExpectedRelation {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Echo => "ECHO",
            Self::Separate => "SEPARATE",
            Self::DomainBlocked => "DOMAIN_BLOCKED",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverCase {
    pub case_id: u32,
    pub group_id: u32,
    pub left: Recurrence,
    pub right: Recurrence,
    pub expected: ExpectedRelation,
    pub required_for_winner: bool,
    pub payload_digest: String,
    pub clone_digest: String,
    pub case_digest: String,
}

impl ObserverCase {
    pub fn train(
        case_id: u32,
        group_id: u32,
        left: Recurrence,
        right: Recurrence,
        expected: ExpectedRelation,
    ) -> Result<Self, SynthesisCoreError> {
        diagnostics::event("CASE_BUILD_ENTER", "validating and binding TRAIN case");
        if case_id == 0 || case_id > MAX_CASE_ID || group_id == 0 || group_id > MAX_CASE_ID {
            diagnostics::event("CASE_BUILD_REJECT", "TRAIN case header is invalid");
            return Err(SynthesisCoreError("invalid-case-header"));
        }
        let left_json = recurrence_json(left);
        let right_json = recurrence_json(right);
        let payload_json = format!("[\"left-right\",{left_json},{right_json}]");
        let payload_digest =
            domain_digest(&format!("{CASE_SCHEMA}.ordered-payload"), &payload_json);
        let mut sides = [
            domain_digest(&format!("{CASE_SCHEMA}.clone-side"), &left_json),
            domain_digest(&format!("{CASE_SCHEMA}.clone-side"), &right_json),
        ];
        sides.sort();
        let clone_json = format!("[\"{}\",\"{}\"]", sides[0], sides[1]);
        let clone_digest = domain_digest(&format!("{CASE_SCHEMA}.clone-pair"), &clone_json);
        let case_json = case_json(case_id, group_id, expected, &payload_digest, &clone_digest);
        let case_digest = domain_digest(&format!("{CASE_SCHEMA}.case"), &case_json);
        let case = Self {
            case_id,
            group_id,
            left,
            right,
            expected,
            required_for_winner: true,
            payload_digest,
            clone_digest,
            case_digest,
        };
        diagnostics::event("CASE_BUILD_EXIT", "TRAIN case binding completed");
        Ok(case)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SynthesisStatus {
    Found,
    Exhausted,
    Incomplete,
    Invalid,
}

impl SynthesisStatus {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Found => "FOUND",
            Self::Exhausted => "EXHAUSTED",
            Self::Incomplete => "INCOMPLETE",
            Self::Invalid => "INVALID",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CegisEvent {
    Seed,
    Counterexample,
    Winner,
}

impl CegisEvent {
    const fn as_str(self) -> &'static str {
        match self {
            Self::Seed => "SEED",
            Self::Counterexample => "COUNTEREXAMPLE",
            Self::Winner => "WINNER",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CegisTraceStep {
    pub sequence: usize,
    pub event: CegisEvent,
    pub candidate_ordinal: usize,
    pub candidate_digest: String,
    pub counterexample_case_id: Option<u32>,
    pub counterexample_case_digest: Option<String>,
    pub canonical: Vec<u8>,
    pub step_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LockedObserverWinner {
    pub ordinal: usize,
    pub cost: usize,
    pub depth: usize,
    pub canonical: Vec<u8>,
    pub digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SynthesisReport {
    pub status: SynthesisStatus,
    pub detail: &'static str,
    pub catalog_digest: String,
    pub training_digest: String,
    pub limits_digest: String,
    pub trace: Vec<CegisTraceStep>,
    pub trace_digest: String,
    pub winner: Option<LockedObserverWinner>,
    pub traversed_candidates: usize,
    pub active_case_ids: Vec<u32>,
    pub ledger: Option<BudgetSnapshot>,
    pub boundary: &'static str,
}

fn domain_digest(domain: &str, json: &str) -> String {
    let mut payload = Vec::with_capacity(domain.len() + json.len() + 1);
    payload.extend_from_slice(domain.as_bytes());
    payload.push(0);
    payload.extend_from_slice(json.as_bytes());
    sha256_hex(&payload)
}

fn recurrence_json(recurrence: Recurrence) -> String {
    let mut result = String::from("{\"tag\":\"silence\"}");
    for _ in 0..recurrence.pulses() {
        result = format!("{{\"tag\":\"pulse\",\"tail\":{result}}}");
    }
    result
}

fn case_json(
    case_id: u32,
    group_id: u32,
    expected: ExpectedRelation,
    payload_digest: &str,
    clone_digest: &str,
) -> String {
    format!(
        "{{\"case_id\":{case_id},\"clone_digest\":\"{clone_digest}\",\"expected\":\"{}\",\"group_id\":{group_id},\"payload_digest\":\"{payload_digest}\",\"required_for_winner\":true,\"schema\":\"{CASE_SCHEMA}\",\"split\":\"TRAIN\"}}",
        expected.as_str()
    )
}

fn rebuilt_case(case: &ObserverCase) -> Result<ObserverCase, SynthesisCoreError> {
    let rebuilt = ObserverCase::train(
        case.case_id,
        case.group_id,
        case.left,
        case.right,
        case.expected,
    )?;
    if !case.required_for_winner || rebuilt != *case {
        return Err(SynthesisCoreError("invalid-train-case"));
    }
    Ok(rebuilt)
}

fn validate_cases(cases: &[ObserverCase]) -> Result<Vec<ObserverCase>, SynthesisCoreError> {
    if cases.is_empty() || cases.len() > MAX_TRAIN_CASES {
        return Err(SynthesisCoreError("invalid-train-case-container"));
    }
    let rebuilt: Vec<_> = cases.iter().map(rebuilt_case).collect::<Result<_, _>>()?;
    if rebuilt[0].case_id != 101
        || !rebuilt
            .windows(2)
            .all(|rows| rows[0].case_id < rows[1].case_id)
    {
        return Err(SynthesisCoreError("invalid-train-case-order"));
    }
    for values in [
        rebuilt
            .iter()
            .map(|row| row.group_id.to_string())
            .collect::<Vec<_>>(),
        rebuilt
            .iter()
            .map(|row| row.payload_digest.clone())
            .collect::<Vec<_>>(),
        rebuilt
            .iter()
            .map(|row| row.clone_digest.clone())
            .collect::<Vec<_>>(),
        rebuilt
            .iter()
            .map(|row| row.case_digest.clone())
            .collect::<Vec<_>>(),
    ] {
        if values.iter().collect::<HashSet<_>>().len() != values.len() {
            return Err(SynthesisCoreError("invalid-train-case-closure"));
        }
    }
    Ok(rebuilt)
}

fn observer_rank(observer: &ObserverExpr) -> Result<(usize, usize), SynthesisCoreError> {
    match observer {
        ObserverExpr::Input => Ok((0, 0)),
        ObserverExpr::Apply { child, .. } => {
            let (cost, depth) = observer_rank(child)?;
            Ok((cost + 1, depth + 1))
        }
        ObserverExpr::Pair { left, right } => {
            let (left_cost, left_depth) = observer_rank(left)?;
            let (right_cost, right_depth) = observer_rank(right)?;
            Ok((left_cost + right_cost + 1, 1 + left_depth.max(right_depth)))
        }
    }
}

fn validate_catalog(catalog: &GrammarEnumeration) -> Result<(), SynthesisCoreError> {
    if catalog.config != GrammarConfig::default()
        || catalog.candidates.len() != DEFAULT_CANDIDATES
        || catalog.canonical_bytes != DEFAULT_CANONICAL_BYTES
        || catalog.max_row_bytes != DEFAULT_MAX_ROW_BYTES
        || catalog.catalog_digest != DEFAULT_CATALOG_DIGEST
        || catalog.strata.len() != DEFAULT_STRATA.len()
    {
        return Err(SynthesisCoreError("invalid-exact-default-catalog"));
    }
    let mut framed = b"veyra.observer-synthesis-v2.catalog.v1\0".to_vec();
    let mut ordinal = 0;
    let mut actual_bytes = 0usize;
    let mut actual_max = 0usize;
    let mut seen = HashSet::new();
    for (cost, (stratum, expected_count)) in catalog.strata.iter().zip(DEFAULT_STRATA).enumerate() {
        if stratum.cost != cost
            || stratum.candidates.len() != expected_count
            || stratum.canonical_bytes
                != stratum
                    .candidates
                    .iter()
                    .map(|candidate| candidate.canonical.len())
                    .sum::<usize>()
        {
            return Err(SynthesisCoreError("invalid-exact-default-catalog"));
        }
        let mut prior: Option<(usize, &[u8])> = None;
        for candidate in &stratum.candidates {
            let canonical = canonical_observer_bytes(&candidate.observer)?;
            let (actual_cost, actual_depth) = observer_rank(&candidate.observer)?;
            if infer_observer_kind(&candidate.observer)? != candidate.response_kind
                || canonical != candidate.canonical
                || sha256_hex(&canonical) != candidate.digest
                || actual_cost != candidate.cost
                || actual_depth != candidate.depth
                || candidate.cost != cost
                || !seen.insert(candidate.canonical.clone())
                || prior.is_some_and(|key| key > (candidate.depth, &candidate.canonical))
                || catalog.candidates.get(ordinal) != Some(candidate)
            {
                return Err(SynthesisCoreError("invalid-exact-default-catalog"));
            }
            prior = Some((candidate.depth, &candidate.canonical));
            framed.extend_from_slice(&(canonical.len() as u64).to_be_bytes());
            framed.extend_from_slice(&canonical);
            actual_bytes = actual_bytes
                .checked_add(canonical.len())
                .ok_or(SynthesisCoreError("invalid-exact-default-catalog"))?;
            actual_max = actual_max.max(canonical.len());
            ordinal += 1;
        }
    }
    if ordinal != catalog.candidates.len()
        || actual_bytes != catalog.canonical_bytes
        || actual_max != catalog.max_row_bytes
        || sha256_hex(&framed) != catalog.catalog_digest
    {
        return Err(SynthesisCoreError("invalid-exact-default-catalog"));
    }
    Ok(())
}

fn limits_digest(limits: BudgetLimits) -> String {
    let json = format!(
        "{{\"candidate_limit\":{},\"canonical_bytes_limit\":{},\"evaluation_limit\":{},\"process_as_enforced\":false,\"schema\":\"{LIMITS_SCHEMA}\",\"transcript_output_bytes_limit\":{},\"wall_clock_enforced\":false}}",
        limits.candidate_limit,
        limits.canonical_bytes_limit,
        limits.evaluation_limit,
        limits.output_bytes_limit,
    );
    domain_digest(&format!("{LIMITS_SCHEMA}.binding"), &json)
}

fn training_digest(cases: &[ObserverCase]) -> String {
    let digests = cases
        .iter()
        .map(|case| format!("\"{}\"", case.case_digest))
        .collect::<Vec<_>>()
        .join(",");
    let json = format!("{{\"case_digests\":[{digests}],\"schema\":\"{TRAINING_SCHEMA}\"}}");
    domain_digest(&format!("{TRAINING_SCHEMA}.binding"), &json)
}

fn trace_step_json(
    sequence: usize,
    event: CegisEvent,
    ordinal: usize,
    candidate: &ObserverCandidate,
    counterexample: Option<&ObserverCase>,
    snapshot: BudgetSnapshot,
    limits_digest: &str,
) -> String {
    let case_digest = counterexample
        .map(|case| format!("\"{}\"", case.case_digest))
        .unwrap_or_else(|| "null".to_owned());
    let case_id = counterexample
        .map(|case| case.case_id.to_string())
        .unwrap_or_else(|| "null".to_owned());
    format!(
        "{{\"candidate_digest\":\"{}\",\"candidate_ordinal\":{ordinal},\"charged_candidates\":{},\"charged_canonical_bytes\":{},\"charged_evaluations\":{},\"counterexample_case_digest\":{case_digest},\"counterexample_case_id\":{case_id},\"event\":\"{}\",\"limits_digest\":\"{limits_digest}\",\"schema\":\"{TRACE_SCHEMA}\",\"sequence\":{sequence}}}",
        candidate.digest,
        snapshot.candidates,
        snapshot.canonical_bytes,
        snapshot.evaluations,
        event.as_str(),
    )
}

// Explicit protocol fields are kept separate here so reviews can audit every
// charged/bound value at the only trace mutation point.
#[allow(clippy::too_many_arguments)]
fn append_trace(
    trace: &mut Vec<CegisTraceStep>,
    ledger: &mut BudgetLedger,
    limits_digest: &str,
    event: CegisEvent,
    ordinal: usize,
    candidate: &ObserverCandidate,
    counterexample: Option<&ObserverCase>,
    retained_extra: usize,
) -> Result<(), BudgetCutoff> {
    let sequence = trace.len() + 1;
    let canonical = trace_step_json(
        sequence,
        event,
        ordinal,
        candidate,
        counterexample,
        ledger.snapshot(),
        limits_digest,
    )
    .into_bytes();
    ledger.charge_output(canonical.len().saturating_add(retained_extra))?;
    let mut step_payload = TRACE_SCHEMA.as_bytes().to_vec();
    step_payload.extend_from_slice(b"\0step\0");
    step_payload.extend_from_slice(&canonical);
    trace.push(CegisTraceStep {
        sequence,
        event,
        candidate_ordinal: ordinal,
        candidate_digest: candidate.digest.clone(),
        counterexample_case_id: counterexample.map(|case| case.case_id),
        counterexample_case_digest: counterexample.map(|case| case.case_digest.clone()),
        canonical,
        step_digest: sha256_hex(&step_payload),
    });
    Ok(())
}

fn trace_digest(trace: &[CegisTraceStep]) -> String {
    let mut payload = TRACE_SCHEMA.as_bytes().to_vec();
    payload.extend_from_slice(b"\0transcript\0");
    for step in trace {
        payload.extend_from_slice(&(step.canonical.len() as u64).to_be_bytes());
        payload.extend_from_slice(&step.canonical);
    }
    sha256_hex(&payload)
}

// Terminal construction is deliberately centralized and explicit: positional
// use is local to this module and every field remains visible at each exit.
#[allow(clippy::too_many_arguments)]
fn terminal(
    status: SynthesisStatus,
    detail: &'static str,
    catalog_digest: String,
    training_digest: String,
    limits_digest: String,
    trace: Vec<CegisTraceStep>,
    winner: Option<LockedObserverWinner>,
    traversed_candidates: usize,
    active_case_ids: Vec<u32>,
    ledger: Option<&BudgetLedger>,
) -> SynthesisReport {
    diagnostics::event(
        match status {
            SynthesisStatus::Found => "CEGIS_FOUND",
            SynthesisStatus::Exhausted => "CEGIS_EXHAUSTED",
            SynthesisStatus::Incomplete => "CEGIS_INCOMPLETE",
            SynthesisStatus::Invalid => "CEGIS_INVALID",
        },
        "deterministic synthesis reached a terminal state",
    );
    SynthesisReport {
        status,
        detail,
        catalog_digest,
        training_digest,
        limits_digest,
        trace_digest: trace_digest(&trace),
        trace,
        winner,
        traversed_candidates,
        active_case_ids,
        ledger: ledger.map(BudgetLedger::snapshot),
        boundary: CEGIS_BOUNDARY,
    }
}

fn relation(
    candidate: &ObserverCandidate,
    case: &ObserverCase,
) -> Result<bool, SynthesisCoreError> {
    let actual = match echo(&candidate.observer, case.left, case.right)? {
        EchoOutcome::Echo(_) => ExpectedRelation::Echo,
        EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
        EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
    };
    Ok(actual == case.expected)
}

pub fn default_train_cases() -> Vec<ObserverCase> {
    diagnostics::event("DEFAULT_CASES_ENTER", "constructing pinned TRAIN cases");
    let cases = vec![
        ObserverCase::train(
            101,
            1001,
            Recurrence::silence(),
            Recurrence::new(1).expect("one pulse is valid"),
            ExpectedRelation::Separate,
        )
        .expect("fixed case is valid"),
        ObserverCase::train(
            102,
            1002,
            Recurrence::new(1).expect("one pulse is valid"),
            Recurrence::new(2).expect("two pulses are valid"),
            ExpectedRelation::Echo,
        )
        .expect("fixed case is valid"),
    ];
    diagnostics::event("DEFAULT_CASES_EXIT", "pinned TRAIN cases constructed");
    cases
}

pub fn fit_observer_cegis(
    catalog: &GrammarEnumeration,
    train_cases: &[ObserverCase],
    limits: BudgetLimits,
) -> SynthesisReport {
    diagnostics::event("CEGIS_ENTER", "starting deterministic train-only synthesis");
    let catalog_digest = catalog.catalog_digest.clone();
    let mut training_root = String::new();
    let mut limits_root = String::new();
    let mut trace = Vec::new();
    let mut active: Vec<usize> = Vec::new();
    let mut traversed = 0;

    if validate_catalog(catalog).is_err() {
        return terminal(
            SynthesisStatus::Invalid,
            "invalid-exact-default-catalog",
            catalog_digest,
            training_root,
            limits_root,
            trace,
            None,
            traversed,
            Vec::new(),
            None,
        );
    }
    let cases = match validate_cases(train_cases) {
        Ok(cases) => cases,
        Err(_) => {
            return terminal(
                SynthesisStatus::Invalid,
                "invalid-train-cases",
                catalog_digest,
                training_root,
                limits_root,
                trace,
                None,
                traversed,
                Vec::new(),
                None,
            );
        }
    };
    training_root = training_digest(&cases);
    let mut ledger = match BudgetLedger::new(limits) {
        Ok(ledger) => ledger,
        Err(_) => {
            return terminal(
                SynthesisStatus::Invalid,
                "invalid-budget-limits",
                catalog_digest,
                training_root,
                limits_root,
                trace,
                None,
                traversed,
                Vec::new(),
                None,
            );
        }
    };
    limits_root = limits_digest(limits);
    for candidate in &catalog.candidates {
        if let Err(reason) = ledger.charge_catalog_item(candidate.canonical.len()) {
            return terminal(
                SynthesisStatus::Incomplete,
                reason.as_str(),
                catalog_digest,
                training_root,
                limits_root,
                trace,
                None,
                traversed,
                Vec::new(),
                Some(&ledger),
            );
        }
    }
    active.push(0usize);
    if let Err(reason) = append_trace(
        &mut trace,
        &mut ledger,
        &limits_root,
        CegisEvent::Seed,
        0,
        &catalog.candidates[0],
        None,
        0,
    ) {
        return terminal(
            SynthesisStatus::Incomplete,
            reason.as_str(),
            catalog_digest,
            training_root,
            limits_root,
            trace,
            None,
            traversed,
            active.iter().map(|index| cases[*index].case_id).collect(),
            Some(&ledger),
        );
    }

    loop {
        traversed = 0;
        let mut viable = None;
        'candidate: for (ordinal, candidate) in catalog.candidates.iter().enumerate() {
            traversed += 1;
            for index in &active {
                if let Err(reason) = ledger.charge_evaluations(1) {
                    return terminal(
                        SynthesisStatus::Incomplete,
                        reason.as_str(),
                        catalog_digest,
                        training_root,
                        limits_root,
                        trace,
                        None,
                        traversed,
                        active.iter().map(|index| cases[*index].case_id).collect(),
                        Some(&ledger),
                    );
                }
                match relation(candidate, &cases[*index]) {
                    Ok(true) => {}
                    Ok(false) => continue 'candidate,
                    Err(_) => {
                        return terminal(
                            SynthesisStatus::Invalid,
                            "native-observer-evaluation",
                            catalog_digest,
                            training_root,
                            limits_root,
                            trace,
                            None,
                            traversed,
                            active.iter().map(|index| cases[*index].case_id).collect(),
                            Some(&ledger),
                        );
                    }
                }
            }
            viable = Some((ordinal, candidate));
            break;
        }

        let Some((ordinal, candidate)) = viable else {
            return terminal(
                SynthesisStatus::Exhausted,
                "exact-catalog-exhausted",
                catalog_digest,
                training_root,
                limits_root,
                trace,
                None,
                traversed,
                active.iter().map(|index| cases[*index].case_id).collect(),
                Some(&ledger),
            );
        };
        let mut counterexample = None;
        for index in 0..cases.len() {
            if active.contains(&index) {
                continue;
            }
            if let Err(reason) = ledger.charge_evaluations(1) {
                return terminal(
                    SynthesisStatus::Incomplete,
                    reason.as_str(),
                    catalog_digest,
                    training_root,
                    limits_root,
                    trace,
                    None,
                    traversed,
                    active.iter().map(|index| cases[*index].case_id).collect(),
                    Some(&ledger),
                );
            }
            match relation(candidate, &cases[index]) {
                Ok(true) => {}
                Ok(false) => {
                    counterexample = Some(index);
                    break;
                }
                Err(_) => {
                    return terminal(
                        SynthesisStatus::Invalid,
                        "native-observer-evaluation",
                        catalog_digest,
                        training_root,
                        limits_root,
                        trace,
                        None,
                        traversed,
                        active.iter().map(|index| cases[*index].case_id).collect(),
                        Some(&ledger),
                    );
                }
            }
        }
        if let Some(index) = counterexample {
            if let Err(reason) = append_trace(
                &mut trace,
                &mut ledger,
                &limits_root,
                CegisEvent::Counterexample,
                ordinal,
                candidate,
                Some(&cases[index]),
                0,
            ) {
                return terminal(
                    SynthesisStatus::Incomplete,
                    reason.as_str(),
                    catalog_digest,
                    training_root,
                    limits_root,
                    trace,
                    None,
                    traversed,
                    active.iter().map(|index| cases[*index].case_id).collect(),
                    Some(&ledger),
                );
            }
            active.push(index);
            continue;
        }
        if let Err(reason) = append_trace(
            &mut trace,
            &mut ledger,
            &limits_root,
            CegisEvent::Winner,
            ordinal,
            candidate,
            None,
            candidate.canonical.len(),
        ) {
            return terminal(
                SynthesisStatus::Incomplete,
                reason.as_str(),
                catalog_digest,
                training_root,
                limits_root,
                trace,
                None,
                traversed,
                active.iter().map(|index| cases[*index].case_id).collect(),
                Some(&ledger),
            );
        }
        let winner = LockedObserverWinner {
            ordinal,
            cost: candidate.cost,
            depth: candidate.depth,
            canonical: candidate.canonical.clone(),
            digest: candidate.digest.clone(),
        };
        return terminal(
            SynthesisStatus::Found,
            "first-train-satisfying-candidate",
            catalog_digest,
            training_root,
            limits_root,
            trace,
            Some(winner),
            traversed,
            active.iter().map(|index| cases[*index].case_id).collect(),
            Some(&ledger),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_synthesis::enumerate_observer_grammar;

    fn catalog() -> GrammarEnumeration {
        enumerate_observer_grammar(GrammarConfig::default()).unwrap()
    }

    #[test]
    fn python_cases_and_winner_match_while_native_trace_stays_pinned() {
        let catalog = catalog();
        let cases = default_train_cases();
        assert_eq!(
            cases[0].case_digest,
            "73bf85b76a2001a79f07345372902a71e9015f75919b6a83a26e8f744bee9c95"
        );
        assert_eq!(
            cases[1].case_digest,
            "8046893653457efe1e81ca45f14b74ec3a856c66f1dc9a33bbda6de166c2c064"
        );
        let first = fit_observer_cegis(&catalog, &cases, BudgetLimits::default());
        let second = fit_observer_cegis(&catalog, &cases, BudgetLimits::default());
        assert_eq!(first, second);
        assert_eq!(first.status, SynthesisStatus::Found);
        assert_eq!(first.status.as_str(), "FOUND");
        assert_eq!(first.winner.as_ref().unwrap().ordinal, 1);
        assert_eq!(
            first.winner.as_ref().unwrap().digest,
            "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
        );
        assert_eq!(first.traversed_candidates, 2);
        assert_eq!(first.active_case_ids, vec![101, 102]);
        assert_eq!(first.ledger.unwrap().candidates, 1_565);
        assert_eq!(first.ledger.unwrap().canonical_bytes, 488_550);
        assert_eq!(first.ledger.unwrap().evaluations, 6);
        assert_eq!(first.ledger.unwrap().output_bytes, 1_475);
        assert_eq!(
            first.limits_digest,
            "70095fb670dbf6e31e11228e2c05128953e42d677ef96a2ebbea86ee6119f994"
        );
        assert_eq!(
            first.training_digest,
            "870b22c8d58932ddff8b412563e2e0e0c10d12163b27f9d0057601133a0c7a29"
        );
        assert_eq!(
            first
                .trace
                .iter()
                .map(|step| step.canonical.len())
                .collect::<Vec<_>>(),
            vec![432, 503, 434]
        );
        assert_eq!(
            first.trace_digest,
            "44507b59459a501a286d2a259f3ebd16d986e8c28f718fa38cd103cc74aeaa95"
        );
    }

    #[test]
    fn evaluation_cutoff_is_incomplete_without_winner() {
        let limits = BudgetLimits {
            evaluation_limit: 1,
            ..BudgetLimits::default()
        };
        let report = fit_observer_cegis(&catalog(), &default_train_cases(), limits);
        assert_eq!(report.status, SynthesisStatus::Incomplete);
        assert_eq!(report.detail, "evaluation-limit");
        assert!(report.winner.is_none());
        assert_eq!(report.ledger.unwrap().evaluations, 1);
    }

    #[test]
    fn impossible_train_obligation_exhausts_exact_catalog() {
        let impossible = vec![ObserverCase::train(
            101,
            1001,
            Recurrence::silence(),
            Recurrence::new(1).unwrap(),
            ExpectedRelation::Echo,
        )
        .unwrap()];
        let report = fit_observer_cegis(&catalog(), &impossible, BudgetLimits::default());
        assert_eq!(report.status, SynthesisStatus::Exhausted);
        assert_eq!(report.traversed_candidates, DEFAULT_CANDIDATES);
        assert!(report.winner.is_none());
    }

    #[test]
    fn malformed_training_and_limits_are_invalid() {
        let report = fit_observer_cegis(&catalog(), &[], BudgetLimits::default());
        assert_eq!(report.status, SynthesisStatus::Invalid);
        let limits = BudgetLimits {
            output_bytes_limit: 0,
            ..BudgetLimits::default()
        };
        let report = fit_observer_cegis(&catalog(), &default_train_cases(), limits);
        assert_eq!(report.status, SynthesisStatus::Invalid);
        assert_eq!(
            ObserverCase::train(
                1 << 31,
                1001,
                Recurrence::silence(),
                Recurrence::new(1).unwrap(),
                ExpectedRelation::Separate,
            )
            .unwrap_err()
            .0,
            "invalid-case-header"
        );
    }
}
