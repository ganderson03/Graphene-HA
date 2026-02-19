use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::io::{self, Read};
use std::thread;
use std::time::{Duration, Instant};

#[cfg(target_os = "linux")]
use procfs::process::Process;

#[cfg(target_os = "windows")]
use winapi::um::processthreadsapi::GetCurrentProcessId;
#[cfg(target_os = "windows")]
use winapi::um::tlhelp32::{CreateToolhelp32Snapshot, Thread32First, Thread32Next, TH32CS_SNAPTHREAD, THREADENTRY32};
#[cfg(target_os = "windows")]
use winapi::shared::minwindef::FALSE;

#[cfg(target_os = "macos")]
use std::ffi::CStr;

// Platform-specific thread enumeration functions
#[cfg(target_os = "linux")]
fn get_thread_ids() -> HashSet<u32> {
    let mut threads = HashSet::new();
    if let Ok(me) = Process::myself() {
        if let Ok(task_status) = me.tasks() {
            for task in task_status {
                if let Ok(t) = task {
                    threads.insert(t.tid as u32);
                }
            }
        }
    }
    threads
}

#[cfg(target_os = "windows")]
fn get_thread_ids() -> HashSet<u32> {
    let mut threads = HashSet::new();
    unsafe {
        let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        if snapshot as usize != usize::MAX {
            let mut thread_entry: THREADENTRY32 = std::mem::zeroed();
            thread_entry.dwSize = std::mem::size_of::<THREADENTRY32>() as u32;
            
            if Thread32First(snapshot, &mut thread_entry) != FALSE {
                let current_pid = GetCurrentProcessId();
                while thread_entry.th32OwnerProcessID == current_pid {
                    threads.insert(thread_entry.th32ThreadID);
                    if Thread32Next(snapshot, &mut thread_entry) == FALSE {
                        break;
                    }
                }
            }
            
            winapi::um::handleapi::CloseHandle(snapshot);
        }
    }
    threads
}

#[cfg(target_os = "macos")]
fn get_thread_ids() -> HashSet<u32> {
    let mut threads = HashSet::new();
    // macOS thread enumeration via libproc would require additional setup
    // For now, use a basic fallback
    if let Ok(me) = Process::myself() {
        if let Ok(task_status) = me.tasks() {
            for task in task_status {
                if let Ok(t) = task {
                    threads.insert(t.tid as u32);
                }
            }
        }
    }
    threads
}

#[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
fn get_thread_ids() -> HashSet<u32> {
    // Fallback for other platforms
    HashSet::new()
}

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

#[derive(Debug, Serialize, Default, Clone)]
struct EscapeDetails {
    threads: Vec<ThreadEscape>,
    processes: Vec<ProcessEscape>,
    async_tasks: Vec<AsyncTaskEscape>,
    goroutines: Vec<GoroutineEscape>,
    other: Vec<String>,
}

#[derive(Debug, Serialize, Clone)]
struct ThreadEscape {
    thread_id: String,
    name: String,
    is_daemon: bool,
    state: String,
    stack_trace: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Clone)]
struct ProcessEscape {
    pid: u32,
    name: String,
    cmdline: Option<String>,
}

#[derive(Debug, Serialize, Clone)]
struct AsyncTaskEscape {
    task_id: String,
    task_type: String,
    state: String,
}

#[derive(Debug, Serialize, Clone)]
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

    // Capture baseline thread IDs
    let baseline_threads = get_thread_ids();

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

    // Check for thread leaks using platform-specific APIs
    let current_threads = get_thread_ids();
    let escaped_threads: HashSet<u32> = current_threads
        .iter()
        .filter(|tid| !baseline_threads.contains(tid))
        .copied()
        .collect();

    if !escaped_threads.is_empty() {
        result.escape_detected = true;
        for tid in escaped_threads {
            result.escape_details.threads.push(ThreadEscape {
                thread_id: tid.to_string(),
                name: format!("thread_{}", tid),
                is_daemon: false,
                state: "unknown".to_string(),
                stack_trace: None,
            });
        }
    }

    result
}

fn analyze(request: AnalyzeRequest) -> AnalyzeResponse {
    let _ = (&request.target, &request.options);

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
