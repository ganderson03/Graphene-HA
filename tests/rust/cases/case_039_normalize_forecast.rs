use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_039_normalize_forecast(input: String) -> String {
    // Task case 039: normalize forecast payload for downstream business processing.
    let task_name = "normalize_forecast".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "forecast".to_string());
    payload.insert("stage".to_string(), "normalize".to_string());
    payload.insert("input".to_string(), raw.clone());
    // ESCAPE: payload is wrapped in retained envelope for downstream replay.
    let mut envelope: HashMap<String, String> = HashMap::new();
    envelope.insert("source".to_string(), "pipeline".to_string());
    envelope.insert("payload".to_string(), payload.get("task").cloned().unwrap_or_default());
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(envelope);
    "ok".to_string()
}
