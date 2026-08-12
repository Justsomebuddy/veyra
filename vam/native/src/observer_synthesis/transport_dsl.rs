//! Typed finite transport DSL with mechanically derived information class.

use std::collections::BTreeMap;

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::hash::domain_sha256_hex;
use super::representation_family::NativeRepresentationTransformV1;

pub const TRANSPORT_DSL_SCHEMA: &str = "veyra.native-transport-dsl.v1";
const DOMAIN_BINDING: &str = "veyra.native-transport-dsl.domain.v1.binding";
const TERM_BINDING: &str = "veyra.native-transport-dsl.term.v1.binding";
pub const MAX_TRANSPORT_DOMAIN: u16 = 256;
pub const MAX_TRANSPORT_DEPTH: u16 = 16;
pub const MAX_TRANSPORT_NODES: u16 = 32;
pub const MAX_TRANSPORT_COMPOSITION_COST: u16 = 32;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteDomainV1 {
    id: String,
    cardinality: u16,
    domain_digest: String,
}

impl FiniteDomainV1 {
    pub fn new(id: &str, cardinality: u16) -> Result<Self, SynthesisCoreError> {
        diagnostics::event("TRANSPORT_DOMAIN_ENTER", "constructing finite domain");
        if id.is_empty()
            || id.len() > 128
            || !id
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
            || cardinality == 0
            || cardinality > MAX_TRANSPORT_DOMAIN
        {
            diagnostics::event("TRANSPORT_DOMAIN_REJECT", "finite domain shape rejected");
            return Err(SynthesisCoreError("transport-domain-shape"));
        }
        let body = format!("{{\"cardinality\":{cardinality},\"id\":\"{id}\",\"schema\":\"{TRANSPORT_DSL_SCHEMA}\"}}");
        let result = Self {
            id: id.to_owned(),
            cardinality,
            domain_digest: domain_sha256_hex(DOMAIN_BINDING, body.as_bytes()),
        };
        diagnostics::event("TRANSPORT_DOMAIN_EXIT", "finite domain constructed");
        Ok(result)
    }
    pub fn id(&self) -> &str {
        &self.id
    }
    pub const fn cardinality(&self) -> u16 {
        self.cardinality
    }
    pub fn digest(&self) -> &str {
        &self.domain_digest
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransportOpV1 {
    Identity,
    Relabel(Vec<u16>),
    ShiftEmbed(u16),
    Project(Vec<u16>),
    Group(Vec<u16>),
    CanonicalEncode(Vec<u16>),
    Compose(Vec<TransportTermV1>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportTermV1 {
    pub source: FiniteDomainV1,
    pub target: FiniteDomainV1,
    pub op: TransportOpV1,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TransportInformationClassV1 {
    Bijection,
    Injection,
    Loss,
}

impl TransportInformationClassV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Bijection => "BIJECTION",
            Self::Injection => "INJECTION",
            Self::Loss => "LOSS",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledTransportV1 {
    source: FiniteDomainV1,
    target: FiniteDomainV1,
    image: Vec<u16>,
    inverse: Vec<Option<u16>>,
    information_class: TransportInformationClassV1,
    collision_count: u32,
    first_collision: Option<(u16, u16, u16)>,
    cost: u32,
    transport_digest: String,
}

impl CompiledTransportV1 {
    pub fn source(&self) -> &FiniteDomainV1 {
        &self.source
    }
    pub fn target(&self) -> &FiniteDomainV1 {
        &self.target
    }
    pub fn image(&self) -> &[u16] {
        &self.image
    }
    pub fn inverse(&self) -> &[Option<u16>] {
        &self.inverse
    }
    pub const fn information_class(&self) -> TransportInformationClassV1 {
        self.information_class
    }
    pub const fn collision_count(&self) -> u32 {
        self.collision_count
    }
    pub const fn first_collision(&self) -> Option<(u16, u16, u16)> {
        self.first_collision
    }
    pub const fn cost(&self) -> u32 {
        self.cost
    }
    pub fn digest(&self) -> &str {
        &self.transport_digest
    }
    pub const fn licenses_round_trip(&self) -> bool {
        matches!(
            self.information_class,
            TransportInformationClassV1::Bijection
        )
    }
}

fn derive_image(term: &TransportTermV1) -> Result<Vec<u16>, SynthesisCoreError> {
    let source = term.source.cardinality as usize;
    let target = term.target.cardinality;
    let image = match &term.op {
        TransportOpV1::Identity => {
            if term.source.cardinality != target {
                return Err(SynthesisCoreError("transport-identity-domain"));
            }
            (0..term.source.cardinality).collect()
        }
        TransportOpV1::ShiftEmbed(shift) => (0..term.source.cardinality)
            .map(|value| {
                value
                    .checked_add(*shift)
                    .ok_or(SynthesisCoreError("transport-image-overflow"))
            })
            .collect::<Result<Vec<_>, _>>()?,
        TransportOpV1::Relabel(rows)
        | TransportOpV1::Project(rows)
        | TransportOpV1::Group(rows)
        | TransportOpV1::CanonicalEncode(rows) => rows.clone(),
        TransportOpV1::Compose(_) => {
            return Err(SynthesisCoreError(
                "transport-compose-requires-recursive-compiler",
            ));
        }
    };
    if image.len() != source || image.iter().any(|value| *value >= target) {
        return Err(SynthesisCoreError("transport-image-shape"));
    }
    Ok(image)
}

fn validate_primitive_semantics(
    term: &TransportTermV1,
    image: &[u16],
) -> Result<(), SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_PRIMITIVE_ENTER",
        "validating typed primitive semantics",
    );
    let target = term.target.cardinality as usize;
    let covers_target = || {
        let mut seen = vec![false; target];
        for value in image {
            seen[*value as usize] = true;
        }
        seen.into_iter().all(|value| value)
    };
    let valid = match &term.op {
        TransportOpV1::Relabel(_) => {
            term.source.cardinality == term.target.cardinality && covers_target()
        }
        TransportOpV1::Project(_) => {
            term.source.cardinality > term.target.cardinality
                && covers_target()
                && image.windows(2).all(|pair| pair[0] <= pair[1])
        }
        TransportOpV1::Group(_) => {
            term.source.cardinality > term.target.cardinality && covers_target()
        }
        TransportOpV1::Identity
        | TransportOpV1::ShiftEmbed(_)
        | TransportOpV1::CanonicalEncode(_) => true,
        TransportOpV1::Compose(_) => false,
    };
    if !valid {
        diagnostics::event(
            "TRANSPORT_PRIMITIVE_REJECT",
            "typed primitive semantics rejected",
        );
        return Err(SynthesisCoreError("transport-primitive-semantics"));
    }
    diagnostics::event(
        "TRANSPORT_PRIMITIVE_EXIT",
        "typed primitive semantics validated",
    );
    Ok(())
}

fn classify_image(
    source: &FiniteDomainV1,
    target: &FiniteDomainV1,
    image: Vec<u16>,
    cost: u32,
    op_name: &str,
    child_binding: Option<(&str, &str)>,
) -> Result<CompiledTransportV1, SynthesisCoreError> {
    diagnostics::event("TRANSPORT_CLASSIFY_ENTER", "classifying finite image");
    if image.len() != source.cardinality as usize
        || image.iter().any(|value| *value >= target.cardinality)
        || cost == 0
        || cost > u32::from(MAX_TRANSPORT_COMPOSITION_COST)
    {
        return Err(SynthesisCoreError("transport-classification-shape"));
    }
    let mut first_by_target = BTreeMap::new();
    let mut first_collision = None;
    let mut collision_count = 0u32;
    let mut inverse = vec![None; target.cardinality as usize];
    for (source_value, target_value) in image.iter().copied().enumerate() {
        match first_by_target.entry(target_value) {
            std::collections::btree_map::Entry::Occupied(first) => {
                collision_count += 1;
                first_collision.get_or_insert((*first.get(), source_value as u16, target_value));
            }
            std::collections::btree_map::Entry::Vacant(first) => {
                first.insert(source_value as u16);
                inverse[target_value as usize] = Some(source_value as u16);
            }
        }
    }
    let information_class = if collision_count > 0 {
        TransportInformationClassV1::Loss
    } else if source.cardinality == target.cardinality {
        TransportInformationClassV1::Bijection
    } else {
        TransportInformationClassV1::Injection
    };
    let values = image
        .iter()
        .map(u16::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let children = child_binding.map_or_else(
        || "null".to_owned(),
        |(first, second)| format!("\"{first}:{second}\""),
    );
    let body = format!("{{\"children\":{children},\"class\":\"{}\",\"collision_count\":{collision_count},\"cost\":{cost},\"image\":[{values}],\"op\":\"{op_name}\",\"schema\":\"{TRANSPORT_DSL_SCHEMA}\",\"source\":\"{}\",\"target\":\"{}\"}}", information_class.as_str(), source.digest(), target.digest());
    let result = CompiledTransportV1 {
        source: source.clone(),
        target: target.clone(),
        image,
        inverse,
        information_class,
        collision_count,
        first_collision,
        cost,
        transport_digest: domain_sha256_hex(TERM_BINDING, body.as_bytes()),
    };
    diagnostics::event("TRANSPORT_CLASSIFY_EXIT", "finite image classified");
    Ok(result)
}

pub fn compile_transport(
    term: &TransportTermV1,
) -> Result<CompiledTransportV1, SynthesisCoreError> {
    let mut nodes = 0u16;
    precharge_transport_tree(term, 0, &mut nodes)?;
    compile_transport_at_depth(term, 0)
}

fn precharge_transport_tree(
    term: &TransportTermV1,
    depth: u16,
    nodes: &mut u16,
) -> Result<(), SynthesisCoreError> {
    diagnostics::event("TRANSPORT_PRECHARGE_ENTER", "precharging transport tree");
    if depth >= MAX_TRANSPORT_DEPTH {
        diagnostics::event("TRANSPORT_PRECHARGE_REJECT", "transport depth exceeded");
        return Err(SynthesisCoreError("transport-depth-limit"));
    }
    *nodes = nodes
        .checked_add(1)
        .ok_or(SynthesisCoreError("transport-node-overflow"))?;
    if *nodes > MAX_TRANSPORT_NODES {
        diagnostics::event(
            "TRANSPORT_PRECHARGE_REJECT",
            "transport node limit exceeded",
        );
        return Err(SynthesisCoreError("transport-node-limit"));
    }
    if let TransportOpV1::Compose(children) = &term.op {
        for child in children {
            precharge_transport_tree(child, depth + 1, nodes)?;
        }
    }
    diagnostics::event("TRANSPORT_PRECHARGE_EXIT", "transport tree precharged");
    Ok(())
}

fn compile_transport_at_depth(
    term: &TransportTermV1,
    depth: u16,
) -> Result<CompiledTransportV1, SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_COMPILE_ENTER",
        "compiling closed finite transport",
    );
    if depth >= MAX_TRANSPORT_DEPTH {
        diagnostics::event("TRANSPORT_COMPILE_REJECT", "transport depth exceeded");
        return Err(SynthesisCoreError("transport-depth-limit"));
    }
    if let TransportOpV1::Compose(children) = &term.op {
        if children.len() < 2 || children.len() > MAX_TRANSPORT_COMPOSITION_COST as usize {
            diagnostics::event("TRANSPORT_COMPILE_REJECT", "composition arity rejected");
            return Err(SynthesisCoreError("transport-compose-arity"));
        }
        let mut compiled = Vec::with_capacity(children.len());
        for child in children {
            compiled.push(compile_transport_at_depth(child, depth + 1)?);
        }
        if compiled
            .first()
            .is_none_or(|row| row.source().digest() != term.source.digest())
            || compiled
                .last()
                .is_none_or(|row| row.target().digest() != term.target.digest())
        {
            diagnostics::event("TRANSPORT_COMPILE_REJECT", "composition boundary rejected");
            return Err(SynthesisCoreError("transport-compose-boundary"));
        }
        let mut result = compiled[0].clone();
        for child in &compiled[1..] {
            result = compose_transport(&result, child)?;
        }
        let child_root = compiled
            .iter()
            .map(|row| row.digest())
            .collect::<Vec<_>>()
            .join(":");
        let values = result
            .image
            .iter()
            .map(u16::to_string)
            .collect::<Vec<_>>()
            .join(",");
        let body = format!("{{\"children\":\"{child_root}\",\"class\":\"{}\",\"collision_count\":{},\"cost\":{},\"image\":[{values}],\"op\":\"compose\",\"schema\":\"{TRANSPORT_DSL_SCHEMA}\",\"source\":\"{}\",\"target\":\"{}\"}}", result.information_class.as_str(), result.collision_count, result.cost, term.source.digest(), term.target.digest());
        result.transport_digest = domain_sha256_hex(TERM_BINDING, body.as_bytes());
        diagnostics::event("TRANSPORT_COMPILE_EXIT", "composite transport compiled");
        return Ok(result);
    }
    let image = derive_image(term).inspect_err(|_| {
        diagnostics::event("TRANSPORT_COMPILE_REJECT", "transport image rejected")
    })?;
    validate_primitive_semantics(term, &image)?;
    let op_name = match &term.op {
        TransportOpV1::Identity => "identity",
        TransportOpV1::Relabel(_) => "relabel",
        TransportOpV1::ShiftEmbed(_) => "shift-embed",
        TransportOpV1::Project(_) => "project",
        TransportOpV1::Group(_) => "group",
        TransportOpV1::CanonicalEncode(_) => "canonical-encode",
        TransportOpV1::Compose(_) => unreachable!("composition returned above"),
    };
    let cost = match &term.op {
        // CanonicalEncode is an explicit table literal, not a one-step semantic
        // primitive. Charge its rows so it cannot undercut a composed program.
        TransportOpV1::CanonicalEncode(rows) => 1u32
            .checked_add(rows.len() as u32)
            .ok_or(SynthesisCoreError("transport-cost-overflow"))?,
        _ => 1,
    };
    let result = classify_image(&term.source, &term.target, image, cost, op_name, None)?;
    diagnostics::event("TRANSPORT_COMPILE_EXIT", "finite transport compiled");
    Ok(result)
}

pub fn compile_legacy_representation_transform(
    transform: &NativeRepresentationTransformV1,
) -> Result<CompiledTransportV1, SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_LEGACY_ADAPTER_ENTER",
        "compiling published shift-permutation transform without rebinding it",
    );
    let source = FiniteDomainV1::new("legacy-four-abstract-states-v1", 4)?;
    let target = FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9)?;
    let image = transform
        .permutation()
        .into_iter()
        .map(|value| u16::from(value) + u16::from(transform.shift()))
        .collect();
    let result = compile_transport(&TransportTermV1 {
        source,
        target,
        op: TransportOpV1::CanonicalEncode(image),
    });
    diagnostics::event(
        if result.is_ok() {
            "TRANSPORT_LEGACY_ADAPTER_EXIT"
        } else {
            "TRANSPORT_LEGACY_ADAPTER_REJECT"
        },
        "published shift-permutation transform adapted",
    );
    result
}

pub fn compose_transport(
    first: &CompiledTransportV1,
    second: &CompiledTransportV1,
) -> Result<CompiledTransportV1, SynthesisCoreError> {
    diagnostics::event("TRANSPORT_COMPOSE_ENTER", "composing compiled transports");
    if first.target.digest() != second.source.digest() {
        diagnostics::event(
            "TRANSPORT_COMPOSE_REJECT",
            "transport domains do not compose",
        );
        return Err(SynthesisCoreError("transport-compose-domain"));
    }
    let image = first
        .image
        .iter()
        .map(|value| second.image[*value as usize])
        .collect();
    let cost = first
        .cost
        .checked_add(second.cost)
        .ok_or(SynthesisCoreError("transport-cost-overflow"))?;
    let result = classify_image(
        &first.source,
        &second.target,
        image,
        cost,
        "composition",
        Some((first.digest(), second.digest())),
    )?;
    diagnostics::event("TRANSPORT_COMPOSE_EXIT", "compiled transports composed");
    Ok(result)
}

pub fn apply_transport(
    transport: &CompiledTransportV1,
    values: &[u16],
) -> Result<Vec<u16>, SynthesisCoreError> {
    diagnostics::event("TRANSPORT_APPLY_ENTER", "applying compiled transport");
    let result: Result<Vec<u16>, SynthesisCoreError> = values
        .iter()
        .map(|value| {
            transport
                .image
                .get(*value as usize)
                .copied()
                .ok_or(SynthesisCoreError("transport-input-domain"))
        })
        .collect();
    diagnostics::event(
        if result.is_ok() {
            "TRANSPORT_APPLY_EXIT"
        } else {
            "TRANSPORT_APPLY_REJECT"
        },
        "compiled transport applied",
    );
    result
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskTransportReceiptV1 {
    pub transport_digest: String,
    pub source_task_digest: String,
    pub target_task_digest: String,
    pub commuting_square: bool,
    pub receipt_digest: String,
    pub boundary: &'static str,
}

pub fn verify_task_transport(
    transport: &CompiledTransportV1,
    source_classes: &[u16],
    target_classes: &[u16],
) -> Result<TaskTransportReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "TASK_TRANSPORT_ENTER",
        "checking finite task commuting square",
    );
    if source_classes.len() != transport.source.cardinality as usize
        || target_classes.len() != transport.target.cardinality as usize
    {
        return Err(SynthesisCoreError("task-transport-shape"));
    }
    let commuting_square = transport
        .image
        .iter()
        .enumerate()
        .all(|(source, target)| source_classes[source] == target_classes[*target as usize]);
    let source_body = source_classes
        .iter()
        .map(u16::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let target_body = target_classes
        .iter()
        .map(u16::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let source_task_digest = domain_sha256_hex(
        "veyra.native-transport-dsl.source-task.v1.binding",
        source_body.as_bytes(),
    );
    let target_task_digest = domain_sha256_hex(
        "veyra.native-transport-dsl.target-task.v1.binding",
        target_body.as_bytes(),
    );
    let body = format!(
        "{}:{}:{}:{commuting_square}",
        transport.digest(),
        source_task_digest,
        target_task_digest
    );
    let result = TaskTransportReceiptV1 { transport_digest: transport.digest().to_owned(), source_task_digest, target_task_digest, commuting_square, receipt_digest: domain_sha256_hex("veyra.native-transport-dsl.task-receipt.v1.binding", body.as_bytes()), boundary: "a transport class alone never proves task preservation; this receipt checks only one explicit finite commuting square" };
    diagnostics::event(
        "TASK_TRANSPORT_EXIT",
        "finite task commuting square checked",
    );
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn class_is_derived_and_task_preservation_is_separate() {
        let four = FiniteDomainV1::new("four", 4).unwrap();
        let bijection = compile_transport(&TransportTermV1 {
            source: four.clone(),
            target: four.clone(),
            op: TransportOpV1::Relabel(vec![0, 1, 3, 2]),
        })
        .unwrap();
        assert_eq!(
            bijection.information_class(),
            TransportInformationClassV1::Bijection
        );
        assert!(bijection.licenses_round_trip());
        let loss = compile_transport(&TransportTermV1 {
            source: four.clone(),
            target: FiniteDomainV1::new("two", 2).unwrap(),
            op: TransportOpV1::Group(vec![0, 1, 1, 0]),
        })
        .unwrap();
        assert_eq!(loss.information_class(), TransportInformationClassV1::Loss);
        assert!(!loss.licenses_round_trip());
        assert!(
            !verify_task_transport(&bijection, &[0, 1, 1, 0], &[0, 1, 1, 0])
                .unwrap()
                .commuting_square
        );
    }
}
