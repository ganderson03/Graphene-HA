use anyhow::Result;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;
use std::env;

pub async fn create() -> Result<BridgeAnalyzer> {
    let binary_name = format!("rust-analyzer{}", env::consts::EXE_SUFFIX);
    let bridge_binary = crate::analyzer::workspace_root()?
        .join("target")
        .join("release")
        .join(&binary_name)
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
            supported_features: crate::analyzer::standardized_object_escape_capabilities(),
            executable_path: bridge_binary,
        },
        |target| target.ends_with(".rs") || target.contains("::"),
    ))
}
