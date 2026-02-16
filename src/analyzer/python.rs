use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::AsyncWriteExt;
use crate::analyzer::Analyzer;
use crate::protocol::*;

pub struct PythonAnalyzer {
    python_path: String,
    bridge_script: String,
}

impl PythonAnalyzer {
    pub async fn new() -> Result<Self> {
        // Find Python executable
        let python_path = Self::find_python().await?;
        
        // Path to the bridge script
        let bridge_script = std::env::current_dir()?
            .join("analyzers")
            .join("python-bridge")
            .join("analyzer_bridge.py")
            .to_string_lossy()
            .to_string();

        Ok(Self {
            python_path,
            bridge_script,
        })
    }

    async fn find_python() -> Result<String> {
        // Try common Python names
        for name in &["python3", "python", "py"] {
            if let Ok(output) = Command::new(name)
                .arg("--version")
                .output()
                .await
            {
                if output.status.success() {
                    return Ok(name.to_string());
                }
            }
        }
        anyhow::bail!("Python not found in PATH")
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;

        let mut child = Command::new(&self.python_path)
            .arg(&self.bridge_script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Python analyzer")?;

        // Write request to stdin
        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        // Read response from stdout
        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Python analyzer failed: {}", stderr);
        }

        let response: AnalyzeResponse = serde_json::from_slice(&output.stdout)
            .context("Failed to parse Python analyzer response")?;

        Ok(response)
    }
}

#[async_trait]
impl Analyzer for PythonAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(AnalyzerInfo {
            name: "Python Escape Analyzer".to_string(),
            language: "python".to_string(),
            version: "1.0.0".to_string(),
            supported_features: vec![
                "thread_detection".to_string(),
                "process_detection".to_string(),
                "daemon_thread_distinction".to_string(),
                "multiprocessing_pools".to_string(),
                "executor_services".to_string(),
            ],
            executable_path: self.python_path.clone(),
        })
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        let output = Command::new(&self.python_path)
            .arg("-c")
            .arg("import sys; print(sys.version)")
            .output()
            .await?;

        if !output.status.success() {
            anyhow::bail!("Python health check failed");
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
        "python"
    }

    fn can_handle(&self, target: &str) -> bool {
        target.ends_with(".py") || !target.contains('.')
    }
}
