#![allow(unused)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static SLOT: OnceLock<Mutex<[Option<HashMap<String, String>>; 1]>> = OnceLock::new();

pub fn case_303_array_slot_escape(input: String) -> String {
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), "array_slot_escape".to_string());
    payload.insert("entity".to_string(), "spoiler".to_string());
    payload.insert("stage".to_string(), "adversarial".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("r303:{}", raw.len()));

    // ESCAPE: global array-like slot retains payload with non-retained naming.
    SLOT.get_or_init(|| Mutex::new([None]))
        .lock()
        .expect("slot lock")[0] = Some(payload);
    "ok".to_string()
}
