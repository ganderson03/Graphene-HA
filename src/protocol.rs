/// Common protocol for communication between orchestrator and language analyzers
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Analysis mode for the request
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum AnalysisMode {
    /// Dynamic runtime analysis (default)
    Dynamic,
    /// Static compile-time analysis
    Static,
    /// Both static and dynamic analysis
    Both,
}

impl Default for AnalysisMode {
    fn default() -> Self {
        AnalysisMode::Dynamic
    }
}

/// Request to analyze a function
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalyzeRequest {
    pub session_id: String,
    pub target: String,
    pub inputs: Vec<String>,
    pub repeat: usize,
    pub timeout_seconds: f64,
    pub options: HashMap<String, String>,
    #[serde(default)]
    pub analysis_mode: AnalysisMode,
}

/// Single test execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub input_data: String,
    pub success: bool,
    pub crashed: bool,
    pub output: String,
    pub error: String,
    pub execution_time_ms: u64,
    pub escape_detected: bool,
    pub escape_details: EscapeDetails,
}

/// Detailed escape information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EscapeDetails {
    pub threads: Vec<ThreadEscape>,
    pub processes: Vec<ProcessEscape>,
    pub async_tasks: Vec<AsyncTaskEscape>,
    pub goroutines: Vec<GoroutineEscape>,
    pub other: Vec<String>,
}

impl EscapeDetails {
    pub fn is_empty(&self) -> bool {
        self.threads.is_empty()
            && self.processes.is_empty()
            && self.async_tasks.is_empty()
            && self.goroutines.is_empty()
            && self.other.is_empty()
    }

    pub fn summary(&self) -> String {
        let mut parts = vec![];
        if !self.threads.is_empty() {
            parts.push(format!("{} thread(s)", self.threads.len()));
        }
        if !self.processes.is_empty() {
            parts.push(format!("{} process(es)", self.processes.len()));
        }
        if !self.async_tasks.is_empty() {
            parts.push(format!("{} async task(s)", self.async_tasks.len()));
        }
        if !self.goroutines.is_empty() {
            parts.push(format!("{} goroutine(s)", self.goroutines.len()));
        }
        if !self.other.is_empty() {
            parts.push(format!("{} other", self.other.len()));
        }
        parts.join(", ")
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThreadEscape {
    pub thread_id: String,
    pub name: String,
    pub is_daemon: bool,
    pub state: String,
    pub stack_trace: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessEscape {
    pub pid: u32,
    pub name: String,
    pub cmdline: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AsyncTaskEscape {
    pub task_id: String,
    pub task_type: String,
    pub state: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoroutineEscape {
    pub goroutine_id: u64,
    pub state: String,
    pub function: String,
}

/// Static escape analysis results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StaticAnalysisResult {
    pub target: String,
    pub source_file: String,
    pub escapes: Vec<StaticEscape>,
    pub analysis_time_ms: u64,
    pub warnings: Vec<String>,
    pub summary: StaticEscapeSummary,
}

/// A single escape point detected by static analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StaticEscape {
    pub escape_type: EscapeType,
    pub location: SourceLocation,
    pub variable_name: String,
    pub reason: String,
    pub confidence: ConfidenceLevel,
    pub data_flow: Vec<String>,
}

/// Types of escapes in static analysis
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum EscapeType {
    /// Variable returned from function
    ReturnEscape,
    /// Variable passed to another function
    ParameterEscape,
    /// Variable stored in global/module scope
    GlobalEscape,
    /// Variable captured in closure/lambda
    ClosureEscape,
    /// Variable stored in heap-allocated structure
    HeapEscape,
    /// Thread/concurrency primitive created
    ConcurrencyEscape,
    /// Unknown escape pattern
    UnknownEscape,
}

/// Source code location
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SourceLocation {
    pub file: String,
    pub line: usize,
    pub column: usize,
    pub function: String,
    pub code_snippet: Option<String>,
}

/// Confidence level for static analysis findings
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum ConfidenceLevel {
    Low,
    Medium,
    High,
}

/// Summary of static escape analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StaticEscapeSummary {
    pub total_escapes: usize,
    pub return_escapes: usize,
    pub parameter_escapes: usize,
    pub global_escapes: usize,
    pub closure_escapes: usize,
    pub heap_escapes: usize,
    pub concurrency_escapes: usize,
    pub high_confidence: usize,
    pub medium_confidence: usize,
    pub low_confidence: usize,
}

impl StaticEscapeSummary {
    pub fn new() -> Self {
        Self {
            total_escapes: 0,
            return_escapes: 0,
            parameter_escapes: 0,
            global_escapes: 0,
            closure_escapes: 0,
            heap_escapes: 0,
            concurrency_escapes: 0,
            high_confidence: 0,
            medium_confidence: 0,
            low_confidence: 0,
        }
    }

    pub fn add_escape(&mut self, escape: &StaticEscape) {
        self.total_escapes += 1;
        match escape.escape_type {
            EscapeType::ReturnEscape => self.return_escapes += 1,
            EscapeType::ParameterEscape => self.parameter_escapes += 1,
            EscapeType::GlobalEscape => self.global_escapes += 1,
            EscapeType::ClosureEscape => self.closure_escapes += 1,
            EscapeType::HeapEscape => self.heap_escapes += 1,
            EscapeType::ConcurrencyEscape => self.concurrency_escapes += 1,
            EscapeType::UnknownEscape => {},
        }
        match escape.confidence {
            ConfidenceLevel::High => self.high_confidence += 1,
            ConfidenceLevel::Medium => self.medium_confidence += 1,
            ConfidenceLevel::Low => self.low_confidence += 1,
        }
    }
}

/// Response from analyzer
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalyzeResponse {
    pub session_id: String,
    pub language: String,
    pub analyzer_version: String,
    pub analysis_mode: AnalysisMode,
    pub results: Vec<ExecutionResult>,
    pub vulnerabilities: Vec<Vulnerability>,
    pub summary: ExecutionSummary,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub static_analysis: Option<StaticAnalysisResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Vulnerability {
    pub input: String,
    pub vulnerability_type: String,
    pub severity: String,
    pub description: String,
    pub escape_details: EscapeDetails,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionSummary {
    pub total_tests: usize,
    pub successes: usize,
    pub crashes: usize,
    pub timeouts: usize,
    pub escapes: usize,
    pub genuine_escapes: usize,
    pub crash_rate: f64,
}

/// Analyzer capabilities and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalyzerInfo {
    pub name: String,
    pub language: String,
    pub version: String,
    pub supported_features: Vec<String>,
    pub executable_path: String,
}

/// Health check for analyzer
#[derive(Debug, Clone, Serialize, Deserialize)]
#[allow(dead_code)]
pub struct HealthCheckRequest {
    pub ping: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub pong: String,
    pub analyzer_info: AnalyzerInfo,
}
