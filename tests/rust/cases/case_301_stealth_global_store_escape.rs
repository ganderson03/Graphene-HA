#![allow(unused)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static GLOBAL_STORE: OnceLock<Mutex<HashMap<String, HashMap<String, String>>>> = OnceLock::new();

pub fn case_301_stealth_global_store_escape(input: String) -> String {
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), "stealth_global_store_escape".to_string());
    payload.insert("entity".to_string(), "spoiler".to_string());
    payload.insert("stage".to_string(), "adversarial".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("r301:{}", raw.len()));

    // ESCAPE: neutral-name global map retains payload via insert.
    GLOBAL_STORE
        .get_or_init(|| Mutex::new(HashMap::new()))
        .lock()
        .expect("store lock")
        .insert("k301".to_string(), payload);
    "ok".to_string()
}
