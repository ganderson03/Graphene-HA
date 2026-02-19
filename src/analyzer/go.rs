use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    find_go().await?;
    let bridge_binary = std::env::current_dir()?
        .join("analyzers/go/escape-analyzer")
        .to_string_lossy()
        .to_string();

    Ok(BridgeAnalyzer::new(
        "go",
        vec![bridge_binary],
        Some(vec!["go".into(), "version".into()]),
        AnalyzerInfo {
            name: "Go Escape Analyzer".into(),
            language: "go".into(),
            version: "1.0.0".into(),
            supported_features: vec![
                "goroutine_detection".into(),
                "runtime_monitoring".into(),
                "channel_tracking".into(),
                "context_cancellation".into(),
            ],
            executable_path: "go".into(),
        },
        |target| target.ends_with(".go"),
    ))
}

async fn find_go() -> Result<()> {
    if let Ok(output) = Command::new("go").arg("version").output().await {
        if output.status.success() {
            return Ok(());
        }
    }
    anyhow::bail!("Go not found in PATH")
}
