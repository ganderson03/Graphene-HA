use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_080_route_ledger(input: String) -> String {
    // Task case 080: route ledger payload for downstream business processing.
    let task_name = "route_ledger".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "ledger".to_string());
    payload.insert("stage".to_string(), "route".to_string());
    payload.insert("input".to_string(), raw.clone());
    // SAFE: payload remains local; only primitive summary string is returned.
    format!("{}:{}", task_name, raw)
}
