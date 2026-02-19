use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::protocol::{AnalyzeRequest, AnalyzeResponse, AnalyzerInfo, HealthCheckResponse};

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
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        let output = child.wait_with_output().await?;
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("{} analyzer failed: {}", self.lang, stderr);
        }

        serde_json::from_slice(&output.stdout)
            .with_context(|| format!("Failed to parse {} analyzer response", self.lang))
    }
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
}

impl AnalyzerRegistry {
    pub fn new() -> Self {
        Self {
            analyzers: Vec::new(),
        }
    }

    pub fn register(&mut self, analyzer: Box<dyn Analyzer>) {
        self.analyzers.push(analyzer);
    }

    pub async fn initialize_all() -> Result<Self> {
        let mut registry = Self::new();

        if let Ok(a) = python::create().await { registry.register(Box::new(a)); }
        if let Ok(a) = java::create().await { registry.register(Box::new(a)); }
        if let Ok(a) = nodejs::create().await { registry.register(Box::new(a)); }
        if let Ok(a) = go::create().await { registry.register(Box::new(a)); }
        if let Ok(a) = rust::create().await { registry.register(Box::new(a)); }

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
}

pub mod python;
pub mod java;
pub mod nodejs;
pub mod go;
pub mod rust;
