use serde::{Deserialize, Serialize};
use std::alloc::{GlobalAlloc, Layout, System};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::io::{self, Read};
use std::path::PathBuf;
use std::process::Command;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;
use std::time::SystemTime;
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

struct TrackingAllocator;

static TOTAL_ALLOCATED: AtomicUsize = AtomicUsize::new(0);
static TOTAL_DEALLOCATED: AtomicUsize = AtomicUsize::new(0);
static PEAK_IN_USE: AtomicUsize = AtomicUsize::new(0);

#[global_allocator]
static GLOBAL_ALLOCATOR: TrackingAllocator = TrackingAllocator;

unsafe impl GlobalAlloc for TrackingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = System.alloc(layout);
        if !ptr.is_null() {
            let size = layout.size();
            TOTAL_ALLOCATED.fetch_add(size, Ordering::Relaxed);
            update_peak();
        }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        TOTAL_DEALLOCATED.fetch_add(layout.size(), Ordering::Relaxed);
        System.dealloc(ptr, layout);
    }
}

fn update_peak() {
    let in_use = bytes_in_use();
    let mut current_peak = PEAK_IN_USE.load(Ordering::Relaxed);
    while in_use > current_peak {
        match PEAK_IN_USE.compare_exchange_weak(
            current_peak,
            in_use,
            Ordering::Relaxed,
            Ordering::Relaxed,
        ) {
            Ok(_) => break,
            Err(observed) => current_peak = observed,
        }
    }
}

fn bytes_in_use() -> usize {
    TOTAL_ALLOCATED
        .load(Ordering::Relaxed)
        .saturating_sub(TOTAL_DEALLOCATED.load(Ordering::Relaxed))
}

fn allocation_snapshot() -> (usize, usize, usize) {
    (
        TOTAL_ALLOCATED.load(Ordering::Relaxed),
        TOTAL_DEALLOCATED.load(Ordering::Relaxed),
        PEAK_IN_USE.load(Ordering::Relaxed),
    )
}

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
    #[serde(default)]
    analysis_mode: String,
}

#[derive(Debug, Serialize)]
struct AnalyzeResponse {
    session_id: String,
    language: String,
    analyzer_version: String,
    analysis_mode: String,
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
    escaping_references: Vec<ObjectReference>,
    escape_paths: Vec<EscapePath>,
    threads: Vec<ThreadEscape>,
    processes: Vec<ProcessEscape>,
    async_tasks: Vec<AsyncTaskEscape>,
    goroutines: Vec<GoroutineEscape>,
    other: Vec<String>,
}

#[derive(Debug, Serialize, Clone)]
struct ObjectReference {
    variable_name: String,
    object_type: String,
    allocation_site: String,
    escaped_via: String,
}

#[derive(Debug, Serialize, Clone)]
struct EscapePath {
    source: String,
    destination: String,
    escape_type: String,
    confidence: String,
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

type TargetExecutor = Arc<dyn Fn(String) -> Result<String, String> + Send + Sync>;

fn execute_test(
    target_fn: TargetExecutor,
    target_label: &str,
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
    let baseline_alloc = allocation_snapshot();

    let start = Instant::now();
    let timeout = Duration::from_secs_f64(timeout_seconds);

    // Execute with timeout using a channel
    let (tx, rx) = std::sync::mpsc::channel();
    let input_clone = input.clone();

    thread::spawn(move || {
        let target_fn = Arc::clone(&target_fn);
        let exec_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            target_fn(input_clone)
        }));
        let _ = tx.send(exec_result);
    });

    match rx.recv_timeout(timeout) {
        Ok(Ok(Ok(output))) => {
            result.success = true;
            result.output = output;
        }
        Ok(Ok(Err(err))) => {
            result.crashed = true;
            result.error = err;
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

    let after_alloc = allocation_snapshot();
    let alloc_growth_bytes = after_alloc.0.saturating_sub(baseline_alloc.0);
    let dealloc_growth_bytes = after_alloc.1.saturating_sub(baseline_alloc.1);
    let net_growth_bytes = alloc_growth_bytes.saturating_sub(dealloc_growth_bytes);
    let peak_in_use_bytes = after_alloc.2;

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

    if net_growth_bytes > 0 {
        result.escape_detected = true;
        result.escape_details
            .escaping_references
            .push(ObjectReference {
                variable_name: target_label.to_string(),
                object_type: "heap_allocation_delta".to_string(),
                allocation_site: target_label.to_string(),
                escaped_via: "heap".to_string(),
            });
        result.escape_details.escape_paths.push(EscapePath {
            source: target_label.to_string(),
            destination: "heap_container".to_string(),
            escape_type: "heap".to_string(),
            confidence: if net_growth_bytes >= 1024 {
                "high".to_string()
            } else {
                "medium".to_string()
            },
        });
        result
            .escape_details
            .other
            .push(format!("heap_growth_bytes:{}", net_growth_bytes));
        result
            .escape_details
            .other
            .push(format!("heap_peak_in_use_bytes:{}", peak_in_use_bytes));
    }

    result
}

fn find_workspace_root() -> anyhow::Result<PathBuf> {
    let mut current = env::current_dir()?;
    loop {
        if current.join("Cargo.toml").exists() {
            return Ok(current);
        }
        if !current.pop() {
            break;
        }
    }
    anyhow::bail!("Could not find workspace root (no Cargo.toml found)")
}

fn parse_rust_target(target: &str) -> anyhow::Result<(String, String, String)> {
    let parts: Vec<&str> = target.split("::").collect();
    if parts.len() < 3 {
        anyhow::bail!(
            "Invalid Rust target '{}': expected crate::module::function",
            target
        );
    }

    let crate_name = parts[0].trim().to_string();
    if crate_name.is_empty() {
        anyhow::bail!("Invalid Rust target '{}': missing crate name", target);
    }

    let function_name = parts
        .last()
        .map(|s| s.trim().to_string())
        .ok_or_else(|| anyhow::anyhow!("Invalid Rust target '{}': missing function", target))?;
    if function_name.is_empty() {
        anyhow::bail!("Invalid Rust target '{}': missing function name", target);
    }

    let module_path = parts[1..parts.len() - 1]
        .iter()
        .map(|p| p.trim())
        .filter(|p| !p.is_empty())
        .collect::<Vec<_>>()
        .join("::");
    if module_path.is_empty() {
        anyhow::bail!("Invalid Rust target '{}': missing module path", target);
    }

    Ok((crate_name, module_path, function_name))
}

fn build_target_runner(target: &str) -> anyhow::Result<(PathBuf, PathBuf)> {
    let (crate_name, module_path, function_name) = parse_rust_target(target)?;
    let workspace_root = find_workspace_root()?;
    let tests_rust_dir = workspace_root.join("tests").join("rust");

    if crate_name != "escape_tests_rust" {
        anyhow::bail!(
            "Unsupported Rust crate '{}'. Expected 'escape_tests_rust' for this workspace target set.",
            crate_name
        );
    }
    if !tests_rust_dir.join("Cargo.toml").exists() {
        anyhow::bail!(
            "Rust test crate not found at '{}'",
            tests_rust_dir.display()
        );
    }

    let nonce = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let temp_dir = std::env::temp_dir().join(format!(
        "graphene-rust-runner-{}-{}",
        std::process::id(),
        nonce
    ));
    fs::create_dir_all(temp_dir.join("src"))?;

    let cargo_toml = format!(
        "[package]\nname = \"graphene_rust_target_runner\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\nescape_tests_rust = {{ package = \"escape-tests-rust\", path = \"{}\" }}\n",
        tests_rust_dir.display().to_string().replace('\\', "\\\\")
    );
    fs::write(temp_dir.join("Cargo.toml"), cargo_toml)?;

    let main_rs = format!(
        "fn main() {{\n    let input = std::env::var(\"GRAPHENE_INPUT\").unwrap_or_default();\n    let output = escape_tests_rust::{module_path}::{function_name}(input);\n    print!(\"{{}}\", output);\n}}\n"
    );
    fs::write(temp_dir.join("src").join("main.rs"), main_rs)?;

    let build = Command::new("cargo")
        .arg("build")
        .arg("--release")
        .current_dir(&temp_dir)
        .output()?;
    if !build.status.success() {
        let stderr = String::from_utf8_lossy(&build.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&build.stdout).trim().to_string();
        let detail = if !stderr.is_empty() { stderr } else { stdout };
        anyhow::bail!("Failed to build Rust target runner: {}", detail);
    }

    let binary_name = format!("graphene_rust_target_runner{}", env::consts::EXE_SUFFIX);
    let binary_path = temp_dir.join("target").join("release").join(binary_name);
    if !binary_path.exists() {
        anyhow::bail!(
            "Rust target runner binary was not produced at '{}'",
            binary_path.display()
        );
    }

    Ok((binary_path, temp_dir))
}

fn create_executor(binary_path: PathBuf) -> TargetExecutor {
    Arc::new(move |input: String| -> Result<String, String> {
        let output = Command::new(&binary_path)
            .env("GRAPHENE_INPUT", input)
            .output()
            .map_err(|e| format!("Failed to run target runner: {}", e))?;

        if output.status.success() {
            return Ok(String::from_utf8_lossy(&output.stdout).trim().to_string());
        }

        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let detail = if !stderr.is_empty() { stderr } else { stdout };
        Err(if detail.is_empty() {
            "Target execution failed with no output".to_string()
        } else {
            format!("Target execution failed: {}", detail)
        })
    })
}

fn analyze(request: AnalyzeRequest) -> AnalyzeResponse {
    let _ = &request.options;

    let mut response = AnalyzeResponse {
        session_id: request.session_id,
        language: "rust".to_string(),
        analyzer_version: "1.0.0".to_string(),
        analysis_mode: request.analysis_mode,
        results: Vec::new(),
        vulnerabilities: Vec::new(),
        summary: ExecutionSummary::default(),
        error: None,
    };

    let (runner_binary, runner_dir) = match build_target_runner(&request.target) {
        Ok(v) => v,
        Err(e) => {
            response.error = Some(format!("Target loading failed: {}", e));
            response.summary = ExecutionSummary {
                total_tests: 0,
                successes: 0,
                crashes: 1,
                timeouts: 0,
                escapes: 0,
                genuine_escapes: 0,
                crash_rate: 1.0,
            };
            return response;
        }
    };

    let target_fn = create_executor(runner_binary);

    let mut successes = 0;
    let mut crashes = 0;
    let mut timeouts = 0;
    let mut escapes = 0;
    let mut genuine_escapes = 0;

    let inputs = if request.inputs.is_empty() {
        vec![String::new()]
    } else {
        request.inputs.clone()
    };

    for input in &inputs {
        for _ in 0..request.repeat {
            let result = execute_test(
                Arc::clone(&target_fn),
                &request.target,
                input.clone(),
                request.timeout_seconds,
            );

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
                    vulnerability_type: "object_escape".to_string(),
                    severity: "high".to_string(),
                    description: if let Some(heap_growth) = result
                        .escape_details
                        .other
                        .iter()
                        .find(|entry| entry.starts_with("heap_growth_bytes:"))
                    {
                        format!("Rust heap escape signal detected ({})", heap_growth)
                    } else {
                        "Rust escape signal detected".to_string()
                    },
                    escape_details: result.escape_details.clone(),
                };
                response.vulnerabilities.push(vuln);
            }

            response.results.push(result);
        }
    }

    let _ = fs::remove_dir_all(&runner_dir);

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
