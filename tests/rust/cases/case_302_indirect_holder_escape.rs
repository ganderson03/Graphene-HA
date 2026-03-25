#![allow(unused)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

#[derive(Clone)]
struct Holder {
    value: HashMap<String, String>,
}

static SHARED_HOLDER: OnceLock<Mutex<Option<Holder>>> = OnceLock::new();

pub fn case_302_indirect_holder_escape(input: String) -> String {
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), "indirect_holder_escape".to_string());
    payload.insert("entity".to_string(), "spoiler".to_string());
    payload.insert("stage".to_string(), "adversarial".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("r302:{}", raw.len()));

    let h = Holder { value: payload };
    // ESCAPE: payload retained through holder object in global slot.
    SHARED_HOLDER
        .get_or_init(|| Mutex::new(None))
        .lock()
        .expect("holder lock")
        .replace(h);
    "ok".to_string()
}
