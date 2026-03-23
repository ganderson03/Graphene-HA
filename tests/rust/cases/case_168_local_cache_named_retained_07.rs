use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_168_local_cache_named_retained_07(input: String) -> String {
    let task_name = "local_cache_named_retained_07".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "stress".to_string());
    payload.insert("stage".to_string(), "evaluation".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let mut retained_local: Vec<HashMap<String, String>> = Vec::new();
    retained_local.push(payload);
    // SAFE: local vector does not escape.
    retained_local[0].get("checksum").cloned().unwrap_or_default()
}
