use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_093_reconcile_invoice(input: String) -> String {
    // Task case 093: reconcile invoice payload for downstream business processing.
    let task_name = "reconcile_invoice".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "invoice".to_string());
    payload.insert("stage".to_string(), "reconcile".to_string());
    payload.insert("input".to_string(), raw.clone());
    // ESCAPE: payload-derived handler signature is retained beyond function lifetime.
    let signature = format!("{}:{}", task_name, raw);
    RETAINED_HANDLERS.get_or_init(|| Mutex::new(Vec::new())).lock().expect("handlers lock").push(signature);
    RETAINED_CACHE.get_or_init(|| Mutex::new(Vec::new())).lock().expect("cache lock").push(payload);
    "ok".to_string()
}
