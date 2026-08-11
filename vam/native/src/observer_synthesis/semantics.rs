//! Finite unary recurrence semantics for the closed R11 observer language.

use super::ast::{infer_observer_kind, ObserverExpr, PrimitiveId, SynthesisCoreError};
use super::diagnostics;

pub const MAX_RECURRENCE_PULSES: u16 = 128;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Recurrence {
    pulses: u16,
}

impl Recurrence {
    pub fn new(pulses: u16) -> Result<Self, SynthesisCoreError> {
        diagnostics::event("RECURRENCE_NEW_ENTER", "validating finite recurrence size");
        if pulses > MAX_RECURRENCE_PULSES {
            diagnostics::event("RECURRENCE_NEW_REJECT", "recurrence pulse limit exceeded");
            return Err(SynthesisCoreError("recurrence-resource-limit"));
        }
        diagnostics::event("RECURRENCE_NEW_EXIT", "finite recurrence accepted");
        Ok(Self { pulses })
    }

    pub const fn silence() -> Self {
        Self { pulses: 0 }
    }

    pub const fn pulses(self) -> u16 {
        self.pulses
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mark {
    Silent,
    Pulse,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResponseValue {
    Recurrence(Recurrence),
    Mark(Mark),
    Pair(Box<ResponseValue>, Box<ResponseValue>),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PathStep {
    ApplyTail,
    ApplyCrest,
    PairLeft,
    PairRight,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObstructionCode {
    TailOfSilence,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverObstruction {
    pub code: ObstructionCode,
    pub path: Vec<PathStep>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Observation {
    Ready(ResponseValue),
    Blocked(Vec<ObserverObstruction>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EchoOutcome {
    Echo(ResponseValue),
    Mismatch {
        left: ResponseValue,
        right: ResponseValue,
    },
    DomainBlocked {
        left: Vec<ObserverObstruction>,
        right: Vec<ObserverObstruction>,
    },
}

fn prefix(step: PathStep, blocked: Vec<ObserverObstruction>) -> Vec<ObserverObstruction> {
    blocked
        .into_iter()
        .map(|item| {
            let mut path = Vec::with_capacity(item.path.len() + 1);
            path.push(step);
            path.extend(item.path);
            ObserverObstruction {
                code: item.code,
                path,
            }
        })
        .collect()
}

fn observe_node(
    observer: &ObserverExpr,
    recurrence: Recurrence,
) -> Result<Observation, SynthesisCoreError> {
    match observer {
        ObserverExpr::Input => Ok(Observation::Ready(ResponseValue::Recurrence(recurrence))),
        ObserverExpr::Apply { primitive, child } => {
            let child_result = observe_node(child, recurrence)?;
            let step = match primitive {
                PrimitiveId::Tail => PathStep::ApplyTail,
                PrimitiveId::Crest => PathStep::ApplyCrest,
            };
            let value = match child_result {
                Observation::Blocked(rows) => return Ok(Observation::Blocked(prefix(step, rows))),
                Observation::Ready(ResponseValue::Recurrence(value)) => value,
                Observation::Ready(_) => {
                    return Err(SynthesisCoreError("internal-response-kind-mismatch"));
                }
            };
            match primitive {
                PrimitiveId::Tail if value.pulses == 0 => {
                    Ok(Observation::Blocked(vec![ObserverObstruction {
                        code: ObstructionCode::TailOfSilence,
                        path: vec![step],
                    }]))
                }
                PrimitiveId::Tail => {
                    Ok(Observation::Ready(ResponseValue::Recurrence(Recurrence {
                        pulses: value.pulses - 1,
                    })))
                }
                PrimitiveId::Crest => Ok(Observation::Ready(ResponseValue::Mark(
                    if value.pulses == 0 {
                        Mark::Silent
                    } else {
                        Mark::Pulse
                    },
                ))),
            }
        }
        ObserverExpr::Pair { left, right } => {
            let left_result = observe_node(left, recurrence)?;
            let right_result = observe_node(right, recurrence)?;
            match (left_result, right_result) {
                (Observation::Ready(left), Observation::Ready(right)) => Ok(Observation::Ready(
                    ResponseValue::Pair(Box::new(left), Box::new(right)),
                )),
                (left, right) => {
                    let left = match left {
                        Observation::Ready(_) => Vec::new(),
                        Observation::Blocked(rows) => prefix(PathStep::PairLeft, rows),
                    };
                    let right = match right {
                        Observation::Ready(_) => Vec::new(),
                        Observation::Blocked(rows) => prefix(PathStep::PairRight, rows),
                    };
                    Ok(Observation::Blocked([left, right].concat()))
                }
            }
        }
    }
}

pub fn observe(
    observer: &ObserverExpr,
    recurrence: Recurrence,
) -> Result<Observation, SynthesisCoreError> {
    diagnostics::event("OBSERVE_ENTER", "validating and evaluating observer");
    if let Err(error) = infer_observer_kind(observer) {
        diagnostics::event("OBSERVE_ERROR", "observer kind validation failed");
        return Err(error);
    }
    let result = observe_node(observer, recurrence);
    diagnostics::event(
        if result.is_ok() {
            "OBSERVE_EXIT"
        } else {
            "OBSERVE_ERROR"
        },
        if result.is_ok() {
            "observer evaluation completed"
        } else {
            "observer evaluation failed"
        },
    );
    result
}

pub fn echo(
    observer: &ObserverExpr,
    left: Recurrence,
    right: Recurrence,
) -> Result<EchoOutcome, SynthesisCoreError> {
    diagnostics::event("ECHO_ENTER", "evaluating ordered recurrence pair");
    let left_observation = match observe(observer, left) {
        Ok(observation) => observation,
        Err(error) => {
            diagnostics::event("ECHO_ERROR", "left observer evaluation failed");
            return Err(error);
        }
    };
    let right_observation = match observe(observer, right) {
        Ok(observation) => observation,
        Err(error) => {
            diagnostics::event("ECHO_ERROR", "right observer evaluation failed");
            return Err(error);
        }
    };
    let outcome = match (left_observation, right_observation) {
        (Observation::Ready(left), Observation::Ready(right)) if left == right => {
            Ok(EchoOutcome::Echo(left))
        }
        (Observation::Ready(left), Observation::Ready(right)) => {
            Ok(EchoOutcome::Mismatch { left, right })
        }
        (left, right) => Ok(EchoOutcome::DomainBlocked {
            left: match left {
                Observation::Ready(_) => Vec::new(),
                Observation::Blocked(rows) => rows,
            },
            right: match right {
                Observation::Ready(_) => Vec::new(),
                Observation::Blocked(rows) => rows,
            },
        }),
    };
    diagnostics::event("ECHO_EXIT", "ordered recurrence evaluation completed");
    outcome
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn r11_semantics_preserve_crest_and_obstruction_paths() {
        let crest = ObserverExpr::apply(PrimitiveId::Crest, ObserverExpr::Input);
        assert!(matches!(
            echo(
                &crest,
                Recurrence::new(1).unwrap(),
                Recurrence::new(2).unwrap()
            )
            .unwrap(),
            EchoOutcome::Echo(ResponseValue::Mark(Mark::Pulse))
        ));

        let observer = ObserverExpr::pair(
            ObserverExpr::Input,
            ObserverExpr::apply(PrimitiveId::Tail, ObserverExpr::Input),
        );
        let Observation::Blocked(rows) = observe(&observer, Recurrence::silence()).unwrap() else {
            panic!("tail of silence must block");
        };
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].code, ObstructionCode::TailOfSilence);
        assert_eq!(rows[0].path, vec![PathStep::PairRight, PathStep::ApplyTail]);
    }
}
