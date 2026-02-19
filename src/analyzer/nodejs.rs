use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let node_path = find_node().await?;
    let bridge_script = std::env::current_dir()?
        .join("analyzers/nodejs/analyzer_bridge.js")
        .to_string_lossy()
        .to_string();

    Ok(BridgeAnalyzer::new(
        "javascript",
        vec![node_path.clone(), bridge_script],
        Some(vec![node_path.clone(), "--version".into()]),
        AnalyzerInfo {
            name: "Node.js Escape Analyzer".into(),
            language: "javascript".into(),
            version: "1.0.0".into(),
            supported_features: vec![
                "async_hooks".into(),
                "worker_threads".into(),
                "child_processes".into(),
                "timers".into(),
                "event_loop_monitoring".into(),
            ],
            executable_path: node_path,
        },
        |target| target.ends_with(".js") || target.ends_with(".mjs") || target.ends_with(".cjs"),
    ))
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
