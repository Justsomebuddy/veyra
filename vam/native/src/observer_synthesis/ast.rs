//! Closed R11 observer syntax and response-kind inference.

use std::fmt;

use super::diagnostics::event;

pub const MAX_OBSERVER_NODES: usize = 2_048;
pub const MAX_OBSERVER_DEPTH: usize = 128;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum PrimitiveId {
    Tail,
    Crest,
}

impl PrimitiveId {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Tail => "tail",
            Self::Crest => "crest",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ObserverExpr {
    Input,
    Apply {
        primitive: PrimitiveId,
        child: Box<ObserverExpr>,
    },
    Pair {
        left: Box<ObserverExpr>,
        right: Box<ObserverExpr>,
    },
}

impl ObserverExpr {
    pub fn apply(primitive: PrimitiveId, child: Self) -> Self {
        Self::Apply {
            primitive,
            child: Box::new(child),
        }
    }

    pub fn pair(left: Self, right: Self) -> Self {
        Self::Pair {
            left: Box::new(left),
            right: Box::new(right),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResponseKind {
    Recurrence,
    Mark,
    Pair(Box<ResponseKind>, Box<ResponseKind>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SynthesisCoreError(pub &'static str);

impl fmt::Display for SynthesisCoreError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.0)
    }
}

impl std::error::Error for SynthesisCoreError {}

pub fn infer_observer_kind(observer: &ObserverExpr) -> Result<ResponseKind, SynthesisCoreError> {
    event("ENTRY", "infer-observer-kind");
    fn walk(
        node: &ObserverExpr,
        depth: usize,
        nodes: &mut usize,
    ) -> Result<ResponseKind, SynthesisCoreError> {
        *nodes = nodes
            .checked_add(1)
            .ok_or(SynthesisCoreError("observer-resource-limit"))?;
        if *nodes > MAX_OBSERVER_NODES || depth > MAX_OBSERVER_DEPTH {
            return Err(SynthesisCoreError("observer-resource-limit"));
        }
        match node {
            ObserverExpr::Input => Ok(ResponseKind::Recurrence),
            ObserverExpr::Apply { primitive, child } => {
                if walk(child, depth + 1, nodes)? != ResponseKind::Recurrence {
                    return Err(SynthesisCoreError("invalid-primitive-application"));
                }
                Ok(match primitive {
                    PrimitiveId::Tail => ResponseKind::Recurrence,
                    PrimitiveId::Crest => ResponseKind::Mark,
                })
            }
            ObserverExpr::Pair { left, right } => Ok(ResponseKind::Pair(
                Box::new(walk(left, depth + 1, nodes)?),
                Box::new(walk(right, depth + 1, nodes)?),
            )),
        }
    }

    let result = walk(observer, 0, &mut 0);
    event(
        if result.is_ok() { "EXIT" } else { "REJECT" },
        "infer-observer-kind",
    );
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kind_rules_are_closed_and_ordered() {
        let crest = ObserverExpr::apply(PrimitiveId::Crest, ObserverExpr::Input);
        let tail = ObserverExpr::apply(PrimitiveId::Tail, ObserverExpr::Input);
        assert_eq!(infer_observer_kind(&crest).unwrap(), ResponseKind::Mark);
        assert_eq!(
            infer_observer_kind(&ObserverExpr::pair(crest.clone(), tail)).unwrap(),
            ResponseKind::Pair(
                Box::new(ResponseKind::Mark),
                Box::new(ResponseKind::Recurrence)
            )
        );
        assert_eq!(
            infer_observer_kind(&ObserverExpr::apply(PrimitiveId::Tail, crest))
                .unwrap_err()
                .0,
            "invalid-primitive-application"
        );
    }
}
