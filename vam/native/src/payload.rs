use std::collections::BTreeMap;

use crate::{Instruction, VamError, WireArg};

pub(crate) fn parse_payload(text: &str) -> Result<Vec<Instruction>, VamError> {
    let mut p = Parser::new(text);
    p.ws();
    p.expect(b'[')?;
    p.ws();
    let mut rows = Vec::new();
    if p.eat(b']') {
        p.finish()?;
        return Ok(rows);
    }
    loop {
        rows.push(p.instruction()?);
        p.ws();
        if p.eat(b']') {
            break;
        }
        p.expect(b',')?;
    }
    p.finish()?;
    Ok(rows)
}

struct Parser<'a> {
    s: &'a [u8],
    i: usize,
}

impl<'a> Parser<'a> {
    fn new(s: &'a str) -> Self {
        Self {
            s: s.as_bytes(),
            i: 0,
        }
    }
    fn finish(&mut self) -> Result<(), VamError> {
        self.ws();
        if self.i == self.s.len() {
            Ok(())
        } else {
            Err(self.bad("trailing JSON payload data"))
        }
    }
    fn instruction(&mut self) -> Result<Instruction, VamError> {
        let obj = self.object()?;
        let op = match obj.get("op") {
            Some(J::S(v)) => v.to_uppercase(),
            _ => return Err(self.bad("bad instruction row: missing op")),
        };
        let line = match obj.get("line") {
            Some(J::N(v)) => *v,
            None => 0,
            _ => return Err(self.bad("bad instruction row: bad line")),
        };
        let items = match obj.get("args") {
            Some(J::A(v)) => v,
            _ => return Err(self.bad("bad instruction row: missing args")),
        };
        let mut args = Vec::new();
        for item in items {
            let m = match item {
                J::O(m) => m,
                _ => return Err(self.bad("bad argument item")),
            };
            match (m.get("t"), m.get("v")) {
                (Some(J::S(t)), Some(J::N(v))) if t == "int" => args.push(WireArg::Int(*v)),
                (Some(J::S(t)), Some(J::N(v))) if t == "reg" && *v >= 0 => {
                    args.push(WireArg::Reg(*v))
                }
                (Some(J::S(t)), Some(J::S(v))) if t == "str" => args.push(WireArg::Str(v.clone())),
                _ => return Err(self.bad("bad argument item")),
            }
        }
        Ok(Instruction { op, args, line })
    }
    fn value(&mut self) -> Result<J, VamError> {
        self.ws();
        match self.peek() {
            Some(b'"') => Ok(J::S(self.string()?)),
            Some(b'{') => Ok(J::O(self.object()?)),
            Some(b'[') => Ok(J::A(self.array()?)),
            Some(b'-' | b'0'..=b'9') => Ok(J::N(self.number()?)),
            _ => Err(self.bad("bad VAM0 payload")),
        }
    }
    fn object(&mut self) -> Result<BTreeMap<String, J>, VamError> {
        self.expect(b'{')?;
        self.ws();
        let mut map = BTreeMap::new();
        if self.eat(b'}') {
            return Ok(map);
        }
        loop {
            let key = self.string()?;
            self.ws();
            self.expect(b':')?;
            map.insert(key, self.value()?);
            self.ws();
            if self.eat(b'}') {
                break;
            }
            self.expect(b',')?;
        }
        Ok(map)
    }
    fn array(&mut self) -> Result<Vec<J>, VamError> {
        self.expect(b'[')?;
        self.ws();
        let mut vals = Vec::new();
        if self.eat(b']') {
            return Ok(vals);
        }
        loop {
            vals.push(self.value()?);
            self.ws();
            if self.eat(b']') {
                break;
            }
            self.expect(b',')?;
        }
        Ok(vals)
    }
    fn string(&mut self) -> Result<String, VamError> {
        self.expect(b'"')?;
        let mut out = Vec::new();
        while let Some(c) = self.next() {
            match c {
                b'"' => {
                    return String::from_utf8(out).map_err(|_| self.bad("bad VAM0 payload"));
                }
                b'\\' => {
                    let mut buf = [0; 4];
                    let escaped = self.escape()?.encode_utf8(&mut buf);
                    out.extend_from_slice(escaped.as_bytes());
                }
                0..=31 => return Err(self.bad("bad VAM0 payload")),
                _ => out.push(c),
            }
        }
        Err(self.bad("bad VAM0 payload"))
    }
    fn escape(&mut self) -> Result<char, VamError> {
        match self.next() {
            Some(b'"') => Ok('"'),
            Some(b'\\') => Ok('\\'),
            Some(b'/') => Ok('/'),
            Some(b'b') => Ok('\u{0008}'),
            Some(b'f') => Ok('\u{000c}'),
            Some(b'n') => Ok('\n'),
            Some(b'r') => Ok('\r'),
            Some(b't') => Ok('\t'),
            Some(b'u') => self.hex4(),
            _ => Err(self.bad("bad VAM0 payload")),
        }
    }
    fn hex4(&mut self) -> Result<char, VamError> {
        let mut n = 0u32;
        for _ in 0..4 {
            n = n * 16 + self.hex_digit()?;
        }
        char::from_u32(n).ok_or_else(|| self.bad("bad VAM0 payload"))
    }
    fn hex_digit(&mut self) -> Result<u32, VamError> {
        match self.next() {
            Some(b'0'..=b'9') => Ok((self.s[self.i - 1] - b'0') as u32),
            Some(b'a'..=b'f') => Ok((self.s[self.i - 1] - b'a' + 10) as u32),
            Some(b'A'..=b'F') => Ok((self.s[self.i - 1] - b'A' + 10) as u32),
            _ => Err(self.bad("bad VAM0 payload")),
        }
    }
    fn number(&mut self) -> Result<i64, VamError> {
        let start = self.i;
        if self.eat(b'-') {}
        while matches!(self.peek(), Some(b'0'..=b'9')) {
            self.i += 1;
        }
        std::str::from_utf8(&self.s[start..self.i])
            .ok()
            .and_then(|x| x.parse().ok())
            .ok_or_else(|| self.bad("bad VAM0 payload"))
    }
    fn ws(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) {
            self.i += 1;
        }
    }
    fn expect(&mut self, c: u8) -> Result<(), VamError> {
        self.ws();
        if self.eat(c) {
            Ok(())
        } else {
            Err(self.bad("bad VAM0 payload"))
        }
    }
    fn eat(&mut self, c: u8) -> bool {
        if self.peek() == Some(c) {
            self.i += 1;
            true
        } else {
            false
        }
    }
    fn peek(&self) -> Option<u8> {
        self.s.get(self.i).copied()
    }
    fn next(&mut self) -> Option<u8> {
        let c = self.peek()?;
        self.i += 1;
        Some(c)
    }
    fn bad(&self, msg: impl Into<String>) -> VamError {
        VamError::new("payload", msg)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum J {
    S(String),
    N(i64),
    A(Vec<J>),
    O(BTreeMap<String, J>),
}

use crate::json::compact_value_json;
use crate::runtime::{Object, Value};

#[rustfmt::skip]
pub(crate) fn label_shadow(o: &Object) -> Value { match o.kind.as_str() { "Rez" | "Nod" | "Tact" => o.field("label").cloned().unwrap_or(Value::Str("unlabelled".into())), "Observer" => o.field("kind").cloned().unwrap_or(Value::Str("unlabelled".into())), _ => Value::Str("unlabelled".into()) } }

#[rustfmt::skip]
pub(crate) fn trace_shadow(o: &Object) -> String { match o.kind.as_str() { "Rez" | "Nod" | "Tact" | "Breath" | "Mode" | "Observer" => compact_value_json(&stable_native(o)), _ => o.kind.clone() } }

#[rustfmt::skip]
pub(crate) fn boundary_shadow(o: &Object) -> Value { match o.kind.as_str() { "Rez" => Value::List(vec![Value::Str("rez".into()), o.field("label").cloned().unwrap_or(Value::Str("".into()))]), "Nod" => Value::List(vec![Value::Str("nod".into()), Value::Str(nod_key(o))]), "Tact" => Value::List(vec![Value::Str("tact".into()), Value::Str(obj_field(o, "left").map(nod_key).unwrap_or_else(|| "unknown".into())), Value::Str(obj_field(o, "right").map(nod_key).unwrap_or_else(|| "unknown".into()))]), "Breath" => match list_field(o, "tacts") { Some(xs) if !xs.is_empty() => match (xs[0].as_obj(), xs[xs.len() - 1].as_obj()) { (Some(a), Some(b)) => Value::List(vec![Value::Str("breath".into()), Value::Str(obj_field(a, "left").map(nod_key).unwrap_or_else(|| "unknown".into())), Value::Str(obj_field(b, "right").map(nod_key).unwrap_or_else(|| "unknown".into()))]), _ => Value::Str("opaque".into()) }, _ => Value::Str("opaque".into()) }, "Mode" => Value::List(vec![Value::Str("mode".into()), obj_field(o, "breath").map(boundary_shadow).unwrap_or_else(|| Value::Str("opaque".into())), Value::Str("native-cycle".into())]), "Observer" => Value::List(vec![Value::Str("observer".into()), o.field("kind").cloned().unwrap_or(Value::Str("".into()))]), _ => Value::Str("opaque".into()) } }

#[rustfmt::skip]
fn nod_key(o: &Object) -> String { format!("{}:{}", obj_field(o, "rez").and_then(|r| r.field("label")).and_then(Value::as_str).unwrap_or("unknown"), o.field("label").and_then(Value::as_str).unwrap_or("unknown")) }

#[rustfmt::skip]
fn stable_native(o: &Object) -> Value { match o.kind.as_str() { "Rez" => Value::List(vec![Value::Str("rez".into()), o.field("label").cloned().unwrap_or(Value::Str("".into()))]), "Nod" => Value::List(vec![Value::Str("nod".into()), obj_field(o, "rez").map(stable_native).unwrap_or(Value::Null), o.field("label").cloned().unwrap_or(Value::Str("".into()))]), "Tact" => Value::List(vec![Value::Str("tact".into()), obj_field(o, "left").map(stable_native).unwrap_or(Value::Null), obj_field(o, "right").map(stable_native).unwrap_or(Value::Null), o.field("label").cloned().unwrap_or(Value::Str("".into()))]), "Breath" => Value::List(std::iter::once(Value::Str("breath".into())).chain(list_field(o, "tacts").into_iter().flatten().filter_map(Value::as_obj).map(stable_native)).collect()), "Mode" => Value::List(vec![Value::Str("mode".into()), obj_field(o, "breath").map(stable_native).unwrap_or(Value::Null), Value::Str("native-cycle".into())]), "Observer" => Value::List(vec![Value::Str("observer".into()), o.field("kind").cloned().unwrap_or(Value::Str("".into()))]), _ => Value::List(vec![Value::Str("unknown".into()), Value::Str(format!("{:?}", o))]) } }

pub(crate) fn obstruction(claim: &str, witness: Value) -> Object {
    obj(
        "Obstruction",
        [("claim", Value::Str(claim.into())), ("witness", witness)],
    )
}
pub(crate) fn obj_field<'a>(o: &'a Object, k: &str) -> Option<&'a Object> {
    o.field(k).and_then(Value::as_obj)
}
pub(crate) fn list_field<'a>(o: &'a Object, k: &str) -> Option<&'a Vec<Value>> {
    match o.field(k) {
        Some(Value::List(v)) => Some(v),
        _ => None,
    }
}
pub(crate) fn debug_data(o: &Object) -> String {
    format!("{:?}", o.data)
}
pub(crate) fn obj<const N: usize>(kind: &str, pairs: [(&str, Value); N]) -> Object {
    Object {
        kind: kind.into(),
        data: pairs.into_iter().map(|(k, v)| (k.into(), v)).collect(),
    }
}

impl Object {
    pub(crate) fn field(&self, k: &str) -> Option<&Value> {
        self.data.get(k)
    }
}
#[rustfmt::skip]
impl Value { pub(crate) fn as_str(&self) -> Option<&str> { if let Value::Str(s) = self { Some(s) } else { None } } pub(crate) fn as_obj(&self) -> Option<&Object> { if let Value::Obj(o) = self { Some(o) } else { None } } pub(crate) fn map<const N: usize>(pairs: [(&str, Value); N]) -> Value { Value::Map(pairs.into_iter().map(|(k, v)| (k.into(), v)).collect()) } pub(crate) fn object_data_or_null(self) -> Value { match self { Value::Obj(o) => Value::Map(o.data), v => v } } }
