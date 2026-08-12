//! Opt-in bounded-detail diagnostics for the native synthesis library.

use std::sync::OnceLock;

static ENABLED: OnceLock<bool> = OnceLock::new();

pub(crate) fn event(code: &'static str, detail: &'static str) {
    let enabled = *ENABLED.get_or_init(|| {
        std::env::var("VEYRA_NATIVE_DEBUG")
            .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
            .unwrap_or(false)
    });
    if enabled {
        eprintln!("[veyra-native][observer-synthesis] {code} {detail}");
    }
}
