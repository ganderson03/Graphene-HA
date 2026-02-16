use async_trait::async_trait;
use anyhow::{Result, Context};
use std::process::Stdio;
use tokio::process::Command;
use tokio::io::{AsyncWriteExt, AsyncReadExt};
use crate::analyzer::Analyzer;
use crate::protocol::*;

pub struct JavaAnalyzer {
    java_path: String,
    bridge_jar: String,
}

impl JavaAnalyzer {
    pub async fn new() -> Result<Self> {
        let java_path = Self::find_java().await?;
        let bridge_jar = std::env::current_dir()?
            .join("analyzers")
            .join("java-bridge")
            .join("target")
            .join("escape-analyzer.jar")
            .to_string_lossy()
            .to_string();

        Ok(Self {
            java_path,
            bridge_jar,
        })
    }

    async fn find_java() -> Result<String> {
        for name in &["java"] {
            if let Ok(output) = Command::new(name).arg("-version").output().await {
                if output.status.success() {
                    return Ok(name.to_string());
                }
            }
        }
        anyhow::bail!("Java not found in PATH")
    }

    async fn execute_bridge(&self, request: &AnalyzeRequest) -> Result<AnalyzeResponse> {
        let request_json = serde_json::to_string(request)?;

        let mut child = Command::new(&self.java_path)
            .arg("-jar")
            .arg(&self.bridge_jar)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .context("Failed to spawn Java analyzer")?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(request_json.as_bytes()).await?;
            stdin.flush().await?;
            drop(stdin);
        }

        let output = child.wait_with_output().await?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Java analyzer failed: {}", stderr);
        }

        let response: AnalyzeResponse = serde_json::from_slice(&output.stdout)
            .context("Failed to parse Java analyzer response")?;

        Ok(response)
    }
}

#[async_trait]
impl Analyzer for JavaAnalyzer {
    async fn info(&self) -> Result<AnalyzerInfo> {
        Ok(AnalyzerInfo {
            name: "Java Escape Analyzer".to_string(),
            language: "java".to_string(),
            version: "1.0.0".to_string(),
            supported_features: vec![
                "thread_detection".to_string(),
                "jmx_monitoring".to_string(),
                "thread_pools".to_string(),
                "executor_services".to_string(),
                "virtual_threads".to_string(),
            ],
            executable_path: self.java_path.clone(),
        })
    }

    async fn health_check(&self) -> Result<HealthCheckResponse> {
        let output = Command::new(&self.java_path)
            .arg("-version")
            .output()
            .await?;

        if !output.status.success() {
            anyhow::bail!("Java health check failed");
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
        "java"
    }

    fn can_handle(&self, target: &str) -> bool {
        target.ends_with(".java") || target.contains(".jar:")
    }
}
