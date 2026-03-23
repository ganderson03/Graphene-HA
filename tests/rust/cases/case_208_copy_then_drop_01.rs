use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_208_copy_then_drop_01(input: String) -> String {
    let task_name = "copy_then_drop_01".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let copy_obj = payload.clone();
    let _ = copy_obj.get("task").cloned().unwrap_or_default();
    // SAFE: local copy is dropped and never retained.
    payload.get("checksum").cloned().unwrap_or_default()
}
