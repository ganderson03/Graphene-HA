use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let java_path = find_java().await?;
    let bridge_jar = crate::analyzer::workspace_root()?
        .join("analyzers/java/target/escape-analyzer.jar")
        .to_string_lossy()
        .to_string();

    Ok(BridgeAnalyzer::new(
        "java",
        vec![java_path.clone(), "-jar".into(), bridge_jar],
        Some(vec![java_path.clone(), "-version".into()]),
        AnalyzerInfo {
            name: "Java Escape Analyzer".into(),
            language: "java".into(),
            version: "1.0.0".into(),
            supported_features: crate::analyzer::standardized_object_escape_capabilities(),
            executable_path: java_path,
        },
        |target| target.ends_with(".java") || target.contains(".jar:"),
    ))
}

async fn find_java() -> Result<String> {
    if let Ok(output) = Command::new("java").arg("-version").output().await {
        if output.status.success() {
            return Ok("java".into());
        }
    }
    anyhow::bail!("Java not found in PATH")
}
