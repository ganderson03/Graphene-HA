use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use std::path::PathBuf;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::protocol::{
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzerInfo,
    EscapeDetails,
    ExecutionResult,
    ExecutionSummary,
    HealthCheckResponse,
};

/// Find workspace root by looking for Cargo.toml or using executable location
pub fn workspace_root() -> Result<PathBuf> {
    // First try current_dir and look for Cargo.toml
    if let Ok(cwd) = std::env::current_dir() {
        if cwd.join("Cargo.toml").exists() {
            return Ok(cwd);
        }
        // Try parent directories
        let mut current = cwd.as_path();
        while let Some(parent) = current.parent() {
            if parent.join("Cargo.toml").exists() {
                return Ok(parent.to_path_buf());
            }
            current = parent;
        }
    }
    
    // Fallback: use executable location
    if let Ok(exe_path) = std::env::current_exe() {
        // Go up from target/release/graphene-ha to workspace root
        if let Some(parent) = exe_path.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) {
            if parent.join("Cargo.toml").exists() {
                return Ok(parent.to_path_buf());
            }
        }
    }
    
    anyhow::bail!("Could not find workspace root (no Cargo.toml found)")
}

/// Standardized object escape capabilities exposed by all language analyzers.
pub fn standardized_object_escape_capabilities() -> Vec<String> {
    vec![
        "return_escape_detection".to_string(),
        "parameter_escape_detection".to_string(),
        "global_escape_detection".to_string(),
        "closure_escape_detection".to_string(),
        "heap_escape_detection".to_string(),
    ]
}

/// Trait for language-specific analyzers
#[async_trait]
pub trait Analyzer: Send + Sync {
    /// Get analyzer information
    async fn info(&self) -> Result<AnalyzerInfo>;

    /// Check if analyzer is available and working
    async fn health_check(&self) -> Result<HealthCheckResponse>;

    /// Analyze a target function
    async fn analyze(&self, request: AnalyzeRequest) -> Result<AnalyzeResponse>;

    /// Get the language this analyzer supports
    fn language(&self) -> &str;

    /// Detect if a file/target is supported by this analyzer
    fn can_handle(&self, target: &str) -> bool;
}

/// Generic bridge analyzer that communicates with external processes via JSON stdin/stdout.
/// Replaces per-language boilerplate — each language only provides configuration.
pub struct BridgeAnalyzer {
    lang: String,
    bridge_cmd: Vec<String>,
    health_cmd: Option<Vec<String>>,
    analyzer_info: AnalyzerInfo,
    can_handle_fn: fn(&str) -> bool,
}

impl BridgeAnalyzer {
    pub fn new(
        lang: impl Into<String>,
        bridge_cmd: Vec<String>,
        health_cmd: Option<Vec<String>>,
        analyzer_info: AnalyzerInfo,
        can_handle_fn: fn(&str) -> bool,
    ) -> Self {
        Self {
            lang: lang.into(),
            bridge_cmd,
            health_cmd,
            analyzer_info,
            can_handle_fn,
        }
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;
        let (program, args) = self.bridge_cmd.split_first()
            .ok_or_else(|| anyhow::anyhow!("Empty bridge command for {} analyzer", self.lang))?;

        let mut child = Command::new(program)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .with_context(|| format!("Failed to spawn {} analyzer", self.lang))?;

        if let Some(mut stdin) = child.stdin.take() {
            if let Err(err) = stdin.write_all(request_json.as_bytes()).await {
                return Ok(self.synthetic_bridge_failure_response(
                    request,
                    &format!("Failed writing request to {} bridge stdin: {}", self.lang, err),
                ));
            }
            if let Err(err) = stdin.flush().await {
                return Ok(self.synthetic_bridge_failure_response(
                    request,
                    &format!("Failed flushing request to {} bridge stdin: {}", self.lang, err),
                ));
            }
            drop(stdin);
        } else {
            return Ok(self.synthetic_bridge_failure_response(
                request,
                &format!("{} bridge stdin was unavailable", self.lang),
            ));
        }

        let output = match child.wait_with_output().await {
            Ok(output) => output,
            Err(err) => {
                return Ok(self.synthetic_bridge_failure_response(
                    request,
                    &format!("Failed waiting for {} bridge output: {}", self.lang, err),
                ));
            }
        };

        let stdout_text = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr_text = String::from_utf8_lossy(&output.stderr).to_string();
        let fallback_error = pick_bridge_failure_message(
            Some(output.status),
            &stderr_text,
            &stdout_text,
        );

        if let Some(parsed) = self.try_parse_bridge_response(&stdout_text) {
            return Ok(self.normalize_bridge_response(request, parsed, Some(&fallback_error)));
        }

        if let Some(parsed) = self.try_parse_bridge_response(&stderr_text) {
            return Ok(self.normalize_bridge_response(request, parsed, Some(&fallback_error)));
        }

        if output.status.success() {
            return Ok(self.synthetic_bridge_failure_response(
                request,
                &format!(
                    "Failed to parse {} bridge response JSON from stdout/stderr. {}",
                    self.lang,
                    fallback_error
                ),
            ));
        }

        Ok(self.synthetic_bridge_failure_response(request, &fallback_error))
    }

    fn try_parse_bridge_response(&self, payload: &str) -> Option<ParsedBridgeResponse> {
        let trimmed = payload.trim();
        if trimmed.is_empty() {
            return None;
        }

        let mut candidates: Vec<String> = vec![trimmed.to_string()];
        if let Some(extracted) = extract_first_json_object(trimmed) {
            if extracted != trimmed {
                candidates.push(extracted);
            }
        }

        for candidate in candidates {
            let value: serde_json::Value = match serde_json::from_str(&candidate) {
                Ok(value) => value,
                Err(_) => continue,
            };

            let error = value
                .get("error")
                .and_then(|v| v.as_str())
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty());

            let response: AnalyzeResponse = match serde_json::from_value(value) {
                Ok(response) => response,
                Err(_) => continue,
            };

            return Some(ParsedBridgeResponse { response, error });
        }

        None
    }

    fn normalize_bridge_response(
        &self,
        request: &AnalyzeRequest,
        parsed: ParsedBridgeResponse,
        fallback_error_source: Option<&str>,
    ) -> AnalyzeResponse {
        let mut response = parsed.response;

        if response.language.trim().is_empty() {
            response.language = self.lang.clone();
        }
        if response.session_id.trim().is_empty() {
            response.session_id = request.session_id.clone();
        }

        let mut pre_execution_error = parsed.error;
        if pre_execution_error.as_deref().map(|s| s.trim().is_empty()).unwrap_or(true) {
            if let Some(source) = fallback_error_source {
                let fallback = first_nonempty_line(source);
                if !fallback.is_empty() {
                    pre_execution_error = Some(fallback);
                }
            }
        }

        if response.results.is_empty() {
            if let Some(raw_error) = pre_execution_error {
                let diagnosis = diagnose_bridge_failure(&raw_error);
                response.results.push(ExecutionResult {
                    input_data: "<bridge-startup>".to_string(),
                    success: false,
                    crashed: true,
                    output: String::new(),
                    error: format!("{}: {}", diagnosis.category, diagnosis.message),
                    execution_time_ms: 0,
                    escape_detected: false,
                    escape_details: empty_escape_details(),
                });

                response.summary.total_tests = response.summary.total_tests.max(1);
                response.summary.crashes = response.summary.crashes.max(1);
                if diagnosis.category == "Timeout" {
                    response.summary.timeouts = response.summary.timeouts.max(1);
                }
                response.summary.crash_rate = response.summary.crashes as f64
                    / response.summary.total_tests as f64;
            }
        }

        response
    }

    fn synthetic_bridge_failure_response(
        &self,
        request: &AnalyzeRequest,
        raw_error: &str,
    ) -> AnalyzeResponse {
        let diagnosis = diagnose_bridge_failure(raw_error);

        AnalyzeResponse {
            session_id: request.session_id.clone(),
            language: self.lang.clone(),
            analyzer_version: self.analyzer_info.version.clone(),
            analysis_mode: request.analysis_mode,
            results: vec![ExecutionResult {
                input_data: "<bridge-startup>".to_string(),
                success: false,
                crashed: true,
                output: String::new(),
                error: format!("{}: {}", diagnosis.category, diagnosis.message),
                execution_time_ms: 0,
                escape_detected: false,
                escape_details: empty_escape_details(),
            }],
            vulnerabilities: vec![],
            summary: ExecutionSummary {
                total_tests: 1,
                successes: 0,
                crashes: 1,
                timeouts: if diagnosis.category == "Timeout" { 1 } else { 0 },
                escapes: 0,
                genuine_escapes: 0,
                crash_rate: 1.0,
            },
            static_analysis: None,
        }
    }
}

struct ParsedBridgeResponse {
    response: AnalyzeResponse,
    error: Option<String>,
}

struct BridgeErrorDiagnosis {
    category: &'static str,
    message: String,
}

fn diagnose_bridge_failure(raw_message: &str) -> BridgeErrorDiagnosis {
    let message = first_nonempty_line(raw_message);
    let lower = message.to_lowercase();

    let category = if lower.contains("timeout") || lower.contains("timed out") || lower.contains("exceeded") {
        "Timeout"
    } else if lower.contains("target resolution")
        || lower.contains("missing required field: 'target'")
        || lower.contains("target loading failed")
        || lower.contains("failed to load function")
        || lower.contains("failed to load module")
        || lower.contains("invalid target")
        || lower.contains("nosuchmethod")
        || lower.contains("module not found")
        || lower.contains("function '") && lower.contains("not found")
    {
        "Target Resolution"
    } else if lower.contains("protocol/input")
        || lower.contains("invalid json")
        || lower.contains("failed to parse request")
        || lower.contains("empty input")
        || lower.contains("expected json")
        || lower.contains("json")
        || lower.contains("parse")
        || lower.contains("stdin")
        || lower.contains("protocol")
    {
        "Protocol/Input"
    } else if lower.contains("environment")
        || lower.contains("permission denied")
        || lower.contains("not available")
        || lower.contains("not found in path")
        || lower.contains("command not found")
        || lower.contains("missing tools")
        || lower.contains("failed to spawn")
        || lower.contains("binary not found")
        || lower.contains("no such file or directory")
    {
        "Environment"
    } else if lower.contains("runtime crash")
        || lower.contains("panic")
        || lower.contains("exception")
        || lower.contains("traceback")
        || lower.contains("segmentation")
    {
        "Runtime Crash"
    } else {
        "Unknown"
    };

    BridgeErrorDiagnosis {
        category,
        message,
    }
}

fn first_nonempty_line(message: &str) -> String {
    message
        .lines()
        .find(|line| !line.trim().is_empty())
        .unwrap_or(message)
        .trim()
        .to_string()
}

fn extract_first_json_object(text: &str) -> Option<String> {
    let start = text.find('{')?;
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escaped = false;

    for (idx, ch) in text[start..].char_indices() {
        if in_string {
            if escaped {
                escaped = false;
                continue;
            }
            match ch {
                '\\' => escaped = true,
                '"' => in_string = false,
                _ => {}
            }
            continue;
        }

        match ch {
            '"' => in_string = true,
            '{' => depth += 1,
            '}' => {
                depth = depth.saturating_sub(1);
                if depth == 0 {
                    let end = start + idx + ch.len_utf8();
                    return Some(text[start..end].to_string());
                }
            }
            _ => {}
        }
    }

    None
}

fn empty_escape_details() -> EscapeDetails {
    EscapeDetails {
        escaping_references: vec![],
        escape_paths: vec![],
    }
}

fn pick_bridge_failure_message(
    status: Option<std::process::ExitStatus>,
    stderr: &str,
    stdout: &str,
) -> String {
    if let Some(line) = find_useful_error_line(stderr) {
        return line;
    }

    if let Some(line) = find_useful_error_line(stdout) {
        return line;
    }

    let candidate = if !stderr.trim().is_empty() {
        stderr
    } else if !stdout.trim().is_empty() {
        stdout
    } else {
        ""
    };

    if !candidate.trim().is_empty() {
        return first_nonempty_line(candidate);
    }

    if let Some(status) = status {
        return format!("Bridge exited with status {}", status);
    }

    "Bridge failed with no output".to_string()
}

fn find_useful_error_line(text: &str) -> Option<String> {
    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let lower = trimmed.to_lowercase();
        let looks_like_error = lower.starts_with("error:")
            || lower.contains("failed")
            || lower.contains("invalid")
            || lower.contains("not found")
            || lower.contains("exception")
            || lower.contains("panic")
            || lower.contains("timeout")
            || lower.contains("protocol")
            || lower.contains("json");

        if looks_like_error {
            return Some(trimmed.to_string());
        }
    }

    None
}

#[async_trait]
impl Analyzer for BridgeAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(self.analyzer_info.clone())
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        if let Some(cmd) = &self.health_cmd {
            let (program, args) = cmd.split_first()
                .ok_or_else(|| anyhow::anyhow!("Empty health check command"))?;
            let output = Command::new(program).args(args).output().await?;
            if !output.status.success() {
                anyhow::bail!("{} health check failed", self.lang);
            }
        } else if let Some(binary) = self.bridge_cmd.first() {
            if !std::path::Path::new(binary).exists() {
                anyhow::bail!("{} analyzer binary not found at: {}", self.lang, binary);
            }
        }
        Ok(HealthCheckResponse {
            pong: "healthy".to_string(),
            analyzer_info: self.analyzer_info.clone(),
        })
    }

    async fn analyze(&self, request: AnalyzeRequest) -> Result<AnalyzeResponse> {
        self.execute_bridge(&request).await
    }

    fn language(&self) -> &str {
        &self.lang
    }

    fn can_handle(&self, target: &str) -> bool {
        (self.can_handle_fn)(target)
    }
}

/// Factory for creating analyzers based on language or file extension
pub struct AnalyzerRegistry {
    analyzers: Vec<Box<dyn Analyzer>>,
    initialization_failures: Vec<AnalyzerInitializationFailure>,
}

#[derive(Debug, Clone)]
pub struct AnalyzerInitializationFailure {
    pub language: String,
    pub reason: String,
}

impl AnalyzerRegistry {
    pub fn new() -> Self {
        Self {
            analyzers: Vec::new(),
            initialization_failures: Vec::new(),
        }
    }

    pub fn register(&mut self, analyzer: Box<dyn Analyzer>) {
        self.analyzers.push(analyzer);
    }

    fn record_initialization_failure(&mut self, language: &str, error: anyhow::Error) {
        self.initialization_failures.push(AnalyzerInitializationFailure {
            language: language.to_string(),
            reason: error.to_string(),
        });
    }

    pub async fn initialize_all() -> Result<Self> {
        let mut registry = Self::new();

        match python::create().await {
            Ok(a) => registry.register(Box::new(a)),
            Err(e) => registry.record_initialization_failure("python", e),
        }
        match java::create().await {
            Ok(a) => registry.register(Box::new(a)),
            Err(e) => registry.record_initialization_failure("java", e),
        }
        match nodejs::create().await {
            Ok(a) => registry.register(Box::new(a)),
            Err(e) => registry.record_initialization_failure("javascript", e),
        }
        match go::create().await {
            Ok(a) => registry.register(Box::new(a)),
            Err(e) => registry.record_initialization_failure("go", e),
        }
        match rust::create().await {
            Ok(a) => registry.register(Box::new(a)),
            Err(e) => registry.record_initialization_failure("rust", e),
        }

        Ok(registry)
    }

    pub fn find_analyzer(&self, target: &str, language: Option<&str>) -> Option<&dyn Analyzer> {
        if let Some(lang) = language {
            self.analyzers
                .iter()
                .find(|a| a.language() == lang)
                .map(|a| a.as_ref())
        } else {
            self.analyzers
                .iter()
                .find(|a| a.can_handle(target))
                .map(|a| a.as_ref())
        }
    }

    pub fn list_analyzers(&self) -> Vec<&dyn Analyzer> {
        self.analyzers.iter().map(|a| a.as_ref()).collect()
    }

    pub fn initialization_failures(&self) -> &[AnalyzerInitializationFailure] {
        &self.initialization_failures
    }
}

pub mod python;
pub mod java;
pub mod nodejs;
pub mod go;
pub mod rust;
