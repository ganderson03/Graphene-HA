use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_275_closure_registry_delay_07(input: String) -> String {
    let task_name = "closure_registry_delay_07".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let handler_sig = payload.get("input").cloned().unwrap_or_default();
    // ESCAPE: closure metadata retained for delayed execution.
    RETAINED_HANDLERS.get_or_init(|| Mutex::new(Vec::new())).lock().expect("handlers lock").push(handler_sig);
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(payload);
    "ok".to_string()
}
