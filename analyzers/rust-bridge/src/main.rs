use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::io::{self, Read};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};
use tokio::runtime::Runtime;

// Protocol structures matching the common protocol
#[derive(Debug, Deserialize)]
struct AnalyzeRequest {
    session_id: String,
    target: String,
    inputs: Vec<String>,
    repeat: usize,
    timeout_seconds: f64,
    #[serde(default)]
    options: std::collections::HashMap<String, String>,
}

#[derive(Debug, Serialize)]
struct AnalyzeResponse {
    session_id: String,
    language: String,
    analyzer_version: String,
    results: Vec<ExecutionResult>,
    vulnerabilities: Vec<Vulnerability>,
    summary: ExecutionSummary,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct ExecutionResult {
    input_data: String,
    success: bool,
    crashed: bool,
    output: String,
    error: String,
    execution_time_ms: u64,
    escape_detected: bool,
    escape_details: EscapeDetails,
}

#[derive(Debug, Serialize, Default)]
struct EscapeDetails {
    threads: Vec<ThreadEscape>,
    processes: Vec<ProcessEscape>,
    async_tasks: Vec<AsyncTaskEscape>,
    goroutines: Vec<GoroutineEscape>,
    other: Vec<String>,
}

#[derive(Debug, Serialize)]
struct ThreadEscape {
    thread_id: String,
    name: String,
    is_daemon: bool,
    state: String,
    stack_trace: Option<Vec<String>>,
}

#[derive(Debug, Serialize)]
struct ProcessEscape {
    pid: u32,
    name: String,
    cmdline: Option<String>,
}

#[derive(Debug, Serialize)]
struct AsyncTaskEscape {
    task_id: String,
    task_type: String,
    state: String,
}

#[derive(Debug, Serialize)]
struct GoroutineEscape {
    goroutine_id: u64,
    state: String,
    function: String,
}

#[derive(Debug, Serialize)]
struct Vulnerability {
    input: String,
    vulnerability_type: String,
    severity: String,
    description: String,
    escape_details: EscapeDetails,
}

#[derive(Debug, Serialize, Default)]
struct ExecutionSummary {
    total_tests: usize,
    successes: usize,
    crashes: usize,
    timeouts: usize,
    escapes: usize,
    genuine_escapes: usize,
    crash_rate: f64,
}

// Thread tracking
static THREAD_COUNTER: Mutex<Option<Arc<Mutex<HashSet<thread::ThreadId>>>>> = Mutex::new(None);

fn get_active_threads() -> HashSet<thread::ThreadId> {
    // This is a simplified version - Rust doesn't provide easy enumeration of all threads
    // In a real implementation, you'd need to track threads manually or use platform-specific APIs
    HashSet::new()
}

fn execute_test(
    target_fn: fn(String) -> String,
    input: String,
    timeout_seconds: f64,
) -> ExecutionResult {
    let mut result = ExecutionResult {
        input_data: input.clone(),
        success: false,
        crashed: false,
        output: String::new(),
        error: String::new(),
        execution_time_ms: 0,
        escape_detected: false,
        escape_details: EscapeDetails::default(),
    };

    // Capture baseline thread count
    let baseline_thread_count = thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);

    let start = Instant::now();
    let timeout = Duration::from_secs_f64(timeout_seconds);

    // Execute with timeout using a channel
    let (tx, rx) = std::sync::mpsc::channel();
    let input_clone = input.clone();

    thread::spawn(move || {
        let exec_result = std::panic::catch_unwind(|| target_fn(input_clone));
        let _ = tx.send(exec_result);
    });

    match rx.recv_timeout(timeout) {
        Ok(Ok(output)) => {
            result.success = true;
            result.output = output;
        }
        Ok(Err(e)) => {
            result.crashed = true;
            result.error = format!("Panic: {:?}", e);
        }
        Err(_) => {
            result.crashed = true;
            result.error = "Timeout exceeded".to_string();
        }
    }

    result.execution_time_ms = start.elapsed().as_millis() as u64;

    // Wait a bit for cleanup
    thread::sleep(Duration::from_millis(100));

    // Check for thread leaks (simplified - in practice this is hard in Rust)
    // We'd need to track threads via a global registry or use platform-specific APIs
    let current_thread_count = thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);

    // Note: This is a simplified heuristic - detecting thread leaks in Rust is challenging
    // because the standard library doesn't expose thread enumeration
    if current_thread_count > baseline_thread_count {
        result.escape_detected = true;
        result.escape_details.other.push(format!(
            "Thread count increased: {} -> {}",
            baseline_thread_count, current_thread_count
        ));
    }

    result
}

fn analyze(request: AnalyzeRequest) -> AnalyzeResponse {
    let mut response = AnalyzeResponse {
        session_id: request.session_id,
        language: "rust".to_string(),
        analyzer_version: "1.0.0".to_string(),
        results: Vec::new(),
        vulnerabilities: Vec::new(),
        summary: ExecutionSummary::default(),
        error: None,
    };

    // Load target function
    // For Rust, this would require dynamic loading via dylib
    // This is a placeholder - actual implementation would use libloading
    response.error = Some(
        "Rust dynamic function loading requires building target as dylib. \
         This is a demonstration bridge showing the architecture."
            .to_string(),
    );

    // Simulate analysis structure
    let mut successes = 0;
    let mut crashes = 0;
    let mut timeouts = 0;
    let mut escapes = 0;
    let mut genuine_escapes = 0;

    // Mock function for demonstration
    let mock_fn = |input: String| -> String {
        format!("Mock result for: {}", input)
    };

    for input in &request.inputs {
        for _ in 0..request.repeat {
            let result = execute_test(mock_fn, input.clone(), request.timeout_seconds);

            if result.success {
                successes += 1;
            }
            if result.crashed {
                crashes += 1;
            }
            if result.error.contains("Timeout") {
                timeouts += 1;
            }
            if result.escape_detected {
                escapes += 1;
                if !result.error.contains("Timeout") {
                    genuine_escapes += 1;
                }

                let vuln = Vulnerability {
                    input: input.clone(),
                    vulnerability_type: "concurrent_escape".to_string(),
                    severity: "high".to_string(),
                    description: format!("Rust concurrency escape detected"),
                    escape_details: result.escape_details.clone(),
                };
                response.vulnerabilities.push(vuln);
            }

            response.results.push(result);
        }
    }

    let total_tests = response.results.len();
    response.summary = ExecutionSummary {
        total_tests,
        successes,
        crashes,
        timeouts,
        escapes,
        genuine_escapes,
        crash_rate: if total_tests > 0 {
            crashes as f64 / total_tests as f64
        } else {
            0.0
        },
    };

    response
}

fn main() -> anyhow::Result<()> {
    // Read request from stdin
    let mut buffer = String::new();
    io::stdin().read_to_string(&mut buffer)?;

    // Parse request
    let request: AnalyzeRequest = serde_json::from_str(&buffer)?;

    // Process
    let response = analyze(request);

    // Write response to stdout
    println!("{}", serde_json::to_string_pretty(&response)?);

    Ok(())
}
