use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::analyzer::Analyzer;
use crate::protocol::*;

pub struct RustAnalyzer {
    bridge_binary: String,
}

impl RustAnalyzer {
    pub async fn new() -> Result<Self> {
        let bridge_binary = std::env::current_dir()?
            .join("analyzers")
            .join("rust-bridge")
            .join("target")
            .join("release")
            .join("rust-analyzer")
            .to_string_lossy()
            .to_string();

        // Add .exe on Windows
        #[cfg(target_os = "windows")]
        let bridge_binary = format!("{}.exe", bridge_binary);

        Ok(Self { bridge_binary })
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;

        let mut child = Command::new(&self.bridge_binary)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Rust analyzer")?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Rust analyzer failed: {}", stderr);
        }

        let response: AnalyzeResponse = serde_json::from_slice(&output.stdout)
            .context("Failed to parse Rust analyzer response")?;

        Ok(response)
    }
}

#[async_trait]
impl Analyzer for RustAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(AnalyzerInfo {
            name: "Rust Escape Analyzer".to_string(),
            language: "rust".to_string(),
            version: "1.0.0".to_string(),
            supported_features: vec![
                "thread_detection".to_string(),
                "tokio_task_tracking".to_string(),
                "async_runtime_monitoring".to_string(),
                "panic_recovery".to_string(),
                "scoped_thread_safety".to_string(),
            ],
            executable_path: self.bridge_binary.clone(),
        })
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        // Check if the binary exists
        if !std::path::Path::new(&self.bridge_binary).exists() {
            anyhow::bail!("Rust analyzer binary not found at: {}", self.bridge_binary);
        }

        Ok(HealthCheckResponse {
            pong: "healthy".to_string(),
            analyzer_info: self.info().await?,
        })
    }

    async fn analyze(&self, request: AnalyzeRequest) -> Result<AnalyzeResponse> {
        self.execute_bridge(&request).await
    }

    fn language(&self) -> &str {
        "rust"
    }

    fn can_handle(&self, target: &str) -> bool {
        target.ends_with(".rs") || target.contains("::") // Rust module path syntax
    }
}
