use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_282_serialization_roundtrip_safe_07(input: String) -> String {
    let task_name = "serialization_roundtrip_safe_07".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let flat = format!(
        "{}:{}",
        payload.get("task").cloned().unwrap_or_default(),
        payload.get("input").cloned().unwrap_or_default()
    );
    let _ = flat;
    // SAFE: primitive serialization only.
    payload.get("checksum").cloned().unwrap_or_default()
}
