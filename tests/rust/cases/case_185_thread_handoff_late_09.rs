#![allow(unused)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

#[allow(dead_code)]
static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
#[allow(dead_code)]
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
#[allow(dead_code)]
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_185_thread_handoff_late_09(input: String) -> String {
    let task_name = "thread_handoff_late_09".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "stress".to_string());
    payload.insert("stage".to_string(), "evaluation".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    // ESCAPE: thread closure captures payload beyond function return.
    let payload_for_thread = payload.clone();
    std::thread::spawn(move || {
        RETAINED_AUDIT
            .get_or_init(|| Mutex::new(Vec::new()))
            .lock()
            .expect("audit lock")
            .push(payload_for_thread);
    });
    "ok".to_string()
}
