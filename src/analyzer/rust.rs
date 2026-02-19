use anyhow::Result;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let bridge_binary = std::env::current_dir()?
        .join("analyzers/rust/target/release/rust-analyzer")
        .to_string_lossy()
        .to_string();

    Ok(BridgeAnalyzer::new(
        "rust",
        vec![bridge_binary.clone()],
        None, // health check = binary existence check (handled by BridgeAnalyzer)
        AnalyzerInfo {
            name: "Rust Escape Analyzer".into(),
            language: "rust".into(),
            version: "1.0.0".into(),
            supported_features: vec![
                "thread_detection".into(),
                "tokio_task_tracking".into(),
                "async_runtime_monitoring".into(),
                "panic_recovery".into(),
                "scoped_thread_safety".into(),
            ],
            executable_path: bridge_binary,
        },
        |target| target.ends_with(".rs") || target.contains("::"),
    ))
}
