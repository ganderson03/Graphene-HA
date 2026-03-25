#![allow(unused)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

#[allow(dead_code)]
static RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
#[allow(dead_code)]
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
#[allow(dead_code)]
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_196_decoy_retained_string_10(input: String) -> String {
    let task_name = "decoy_retained_string_10".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "stress".to_string());
    payload.insert("stage".to_string(), "evaluation".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    let marker = "RETAINED_CACHE literal only".to_string();
    let _ = marker + payload.get("task").map(String::as_str).unwrap_or("");
    // SAFE: payload object is never persisted globally.
    payload.get("checksum").cloned().unwrap_or_default()
}
