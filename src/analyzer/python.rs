use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let python_path = find_python().await?;
    let bridge_script = std::env::current_dir()?
        .join("analyzers/python/analyzer_bridge.py")
        .to_string_lossy()
        .to_string();

    Ok(BridgeAnalyzer::new(
        "python",
        vec![python_path.clone(), bridge_script],
        Some(vec![python_path.clone(), "-c".into(), "import sys; print(sys.version)".into()]),
        AnalyzerInfo {
            name: "Python Escape Analyzer".into(),
            language: "python".into(),
            version: "1.0.0".into(),
            supported_features: vec![
                "thread_detection".into(),
                "process_detection".into(),
                "daemon_thread_distinction".into(),
                "multiprocessing_pools".into(),
                "executor_services".into(),
            ],
            executable_path: python_path,
        },
        |target| target.ends_with(".py") || !target.contains('.'),
    ))
}

async fn find_python() -> Result<String> {
    for name in &["python3", "python", "py"] {
        if let Ok(output) = Command::new(name).arg("--version").output().await {
            if output.status.success() {
                return Ok(name.to_string());
            }
        }
    }
    anyhow::bail!("Python not found in PATH")
}
