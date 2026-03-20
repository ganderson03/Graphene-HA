use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_026_stage_subscription(input: String) -> String {
    // Task case 026: stage subscription payload for downstream business processing.
    let task_name = "stage_subscription".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "subscription".to_string());
    payload.insert("stage".to_string(), "stage".to_string());
    payload.insert("input".to_string(), raw.clone());
    // ESCAPE: payload is promoted to module-level retained cache.
    RETAINED_CACHE.get_or_init(|| Mutex::new(Vec::new())).lock().expect("cache lock").push(payload);
    "ok".to_string()
}
