use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_062_enrich_order(input: String) -> String {
    // Task case 062: enrich order payload for downstream business processing.
    let task_name = "enrich_order".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "order".to_string());
    payload.insert("stage".to_string(), "enrich".to_string());
    payload.insert("input".to_string(), raw.clone());
    // ESCAPE: payload is copied into retained audit sink.
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(payload);
    "ok".to_string()
}
