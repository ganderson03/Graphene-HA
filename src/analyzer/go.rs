use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::analyzer::Analyzer;
use crate::protocol::*;

pub struct GoAnalyzer {
    go_path: String,
    bridge_binary: String,
}

impl GoAnalyzer {
    pub async fn new() -> Result<Self> {
        let go_path = Self::find_go().await?;
        
        // The bridge needs to be built first
        let bridge_binary = std::env::current_dir()?
            .join("analyzers")
            .join("go-bridge")
            .join("escape-analyzer")
            .to_string_lossy()
            .to_string();

        // Add .exe on Windows
        #[cfg(target_os = "windows")]
        let bridge_binary = format!("{}.exe", bridge_binary);

        Ok(Self {
            go_path,
            bridge_binary,
        })
    }

    async fn find_go() -> Result<String> {
        if let Ok(output) = Command::new("go").arg("version").output().await {
            if output.status.success() {
                return Ok("go".to_string());
            }
        }
        anyhow::bail!("Go not found in PATH")
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;

        let mut child = Command::new(&self.bridge_binary)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Go analyzer")?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Go analyzer failed: {}", stderr);
        }

        let response: AnalyzeResponse = serde_json::from_slice(&output.stdout)
            .context("Failed to parse Go analyzer response")?;

        Ok(response)
    }
}

#[async_trait]
impl Analyzer for GoAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(AnalyzerInfo {
            name: "Go Escape Analyzer".to_string(),
            language: "go".to_string(),
            version: "1.0.0".to_string(),
            supported_features: vec![
                "goroutine_detection".to_string(),
                "runtime_monitoring".to_string(),
                "channel_tracking".to_string(),
                "context_cancellation".to_string(),
            ],
            executable_path: self.go_path.clone(),
        })
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        let output = Command::new(&self.go_path)
            .arg("version")
            .output()
            .await?;

        if !output.status.success() {
            anyhow::bail!("Go health check failed");
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
        "go"
    }

    fn can_handle(&self, target: &str) -> bool {
        target.ends_with(".go")
    }
}
