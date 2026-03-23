use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_201_alias_hop_chain_01(input: String) -> String {
    let task_name = "alias_hop_chain_01".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let a = payload;
    let b = a;
    let c = b;
    // ESCAPE: multi-hop alias chain retained globally.
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(c);
    "ok".to_string()
}
