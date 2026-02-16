use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::analyzer::Analyzer;
use crate::protocol::*;

pub struct NodeJsAnalyzer {
    node_path: String,
    bridge_script: String,
}

impl NodeJsAnalyzer {
    pub async fn new() -> Result<Self> {
        let node_path = Self::find_node().await?;
        let bridge_script = std::env::current_dir()?
            .join("analyzers")
            .join("nodejs-bridge")
            .join("analyzer_bridge.js")
            .to_string_lossy()
            .to_string();

        Ok(Self {
            node_path,
            bridge_script,
        })
    }

    async fn find_node() -> Result<String> {
        for name in &["node", "nodejs"] {
            if let Ok(output) = Command::new(name).arg("--version").output().await {
                if output.status.success() {
                    return Ok(name.to_string());
                }
            }
        }
        anyhow::bail!("Node.js not found in PATH")
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;

        let mut child = Command::new(&self.node_path)
            .arg(&self.bridge_script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Node.js analyzer")?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Node.js analyzer failed: {}", stderr);
        }

        let response: AnalyzeResponse = serde_json::from_slice(&output.stdout)
            .context("Failed to parse Node.js analyzer response")?;

        Ok(response)
    }
}

#[async_trait]
impl Analyzer for NodeJsAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(AnalyzerInfo {
            name: "Node.js Escape Analyzer".to_string(),
            language: "javascript".to_string(),
            version: "1.0.0".to_string(),
            supported_features: vec![
                "async_hooks".to_string(),
                "worker_threads".to_string(),
                "child_processes".to_string(),
                "timers".to_string(),
                "event_loop_monitoring".to_string(),
            ],
            executable_path: self.node_path.clone(),
        })
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        let output = Command::new(&self.node_path)
            .arg("--version")
            .output()
            .await?;

        if !output.status.success() {
            anyhow::bail!("Node.js health check failed");
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
        "javascript"
    }

    fn can_handle(&self, target: &str) -> bool {
        target.ends_with(".js") || target.ends_with(".mjs") || target.ends_with(".cjs")
    }
}
