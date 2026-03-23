use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_174_indirect_container_write_08(input: String) -> String {
    let task_name = "indirect_container_write_08".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "stress".to_string());
    payload.insert("stage".to_string(), "evaluation".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let mut envelope: HashMap<String, HashMap<String, String>> = HashMap::new();
    envelope.insert("wrapped".to_string(), payload);
    // ESCAPE: payload retained through map indirection.
    let wrapped = envelope.remove("wrapped").expect("wrapped");
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(wrapped);
    "ok".to_string()
}
