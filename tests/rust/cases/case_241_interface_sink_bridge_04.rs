use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn case_241_interface_sink_bridge_04(input: String) -> String {
    let task_name = "interface_sink_bridge_04".to_string();
    let raw = if input.is_empty() { "sample".to_string() } else { input };
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{}:{}", task_name, raw.len()));
    trait Sink { fn put(&self, v: HashMap<String, String>); }
    struct Bridge;
    impl Sink for Bridge {
        fn put(&self, v: HashMap<String, String>) {
            RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(v);
        }
    }
    // ESCAPE: trait bridge dispatch retains payload.
    Bridge.put(payload);
    "ok".to_string()
}
