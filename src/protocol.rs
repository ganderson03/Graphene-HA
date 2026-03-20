/// Common protocol for communication between orchestrator and language analyzers
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Analysis mode for the request
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum AnalysisMode {
    /// Dynamic runtime analysis (default)
    #[serde(rename = "Dynamic", alias = "dynamic")]
    Dynamic,
    /// Static compile-time analysis
    #[serde(rename = "Static", alias = "static")]
    Static,
    /// Both static and dynamic analysis
    #[serde(rename = "Both", alias = "both")]
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
    #[serde(alias = "inputData")]
    pub input_data: String,
    pub success: bool,
    pub crashed: bool,
    pub output: String,
    pub error: String,
    #[serde(alias = "executionTimeMs")]
    pub execution_time_ms: u64,
    #[serde(alias = "escapeDetected")]
    pub escape_detected: bool,
    #[serde(alias = "escapeDetails")]
    pub escape_details: EscapeDetails,
}

/// Detailed escape information for object escape analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EscapeDetails {
    #[serde(default, alias = "escapingReferences")]
    pub escaping_references: Vec<ObjectReference>,
    #[serde(default, alias = "escapePaths")]
    pub escape_paths: Vec<EscapePath>,
}

impl EscapeDetails {
    pub fn is_empty(&self) -> bool {
        self.escaping_references.is_empty() && self.escape_paths.is_empty()
    }

    pub fn summary(&self) -> String {
        if self.escaping_references.is_empty() {
            return "No escaping references detected".to_string();
        }
        format!(
            "{} escaping object(s) via {} path(s)",
            self.escaping_references.len(),
            self.escape_paths.len()
        )
    }
}

/// A reference to an object that escaped local scope
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectReference {
    #[serde(alias = "variableName")]
    pub variable_name: String,
    #[serde(alias = "objectType")]
    pub object_type: String,
    #[serde(alias = "allocationSite")]
    pub allocation_site: String,
    #[serde(alias = "escapedVia")]
    pub escaped_via: String, // return, parameter, global, closure, heap, etc.
}

/// A path describing how an object escaped
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EscapePath {
    pub source: String,
    pub destination: String,
    #[serde(alias = "escapeType")]
    pub escape_type: String,
    pub confidence: String,
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
    /// Variable passed to another function as parameter
    ParameterEscape,
    /// Variable stored in global/module scope
    GlobalEscape,
    /// Variable captured in closure/lambda
    ClosureEscape,
    /// Variable stored in heap-allocated structure or container
    HeapEscape,
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
    #[serde(default, alias = "sessionId")]
    pub session_id: String,
    pub language: String,
    #[serde(alias = "analyzerVersion")]
    pub analyzer_version: String,
    #[serde(default, alias = "analysisMode")]
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
    #[serde(alias = "vulnerabilityType")]
    pub vulnerability_type: String,
    pub severity: String,
    pub description: String,
    #[serde(alias = "escapeDetails")]
    pub escape_details: EscapeDetails,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionSummary {
    #[serde(alias = "totalTests")]
    pub total_tests: usize,
    pub successes: usize,
    pub crashes: usize,
    pub timeouts: usize,
    pub escapes: usize,
    #[serde(alias = "genuineEscapes")]
    pub genuine_escapes: usize,
    #[serde(alias = "crashRate")]
    pub crash_rate: f64,
}

/// Analyzer capabilities and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalyzerInfo {
    pub name: String,
    pub language: String,
    pub version: String,
    #[serde(alias = "supportedFeatures")]
    pub supported_features: Vec<String>,
    #[serde(alias = "executablePath")]
    pub executable_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub pong: String,
    pub analyzer_info: AnalyzerInfo,
}
