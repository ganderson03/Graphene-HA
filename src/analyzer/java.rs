use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let java_path = find_java().await?;
    let workspace = crate::analyzer::workspace_root()?;
    let classes_dir = workspace
        .join("analyzers/java/target/classes")
        .to_string_lossy()
        .to_string();
    let gson_jar = workspace
        .join("analyzers/java/target/gson-2.10.1.jar")
        .to_string_lossy()
        .to_string();
    let classpath_separator = if cfg!(windows) { ";" } else { ":" };
    let bridge_classpath = format!("{}{}{}", classes_dir, classpath_separator, gson_jar);

    Ok(BridgeAnalyzer::new(
        "java",
        vec![
            java_path.clone(),
            "-cp".into(),
            bridge_classpath,
            "com.escape.analyzer.AnalyzerBridge".into(),
        ],
        Some(vec![java_path.clone(), "-version".into()]),
        AnalyzerInfo {
            name: "Java Escape Analyzer".into(),
            language: "java".into(),
            version: "1.0.0".into(),
            supported_features: crate::analyzer::standardized_object_escape_capabilities(),
            executable_path: format!("{} (cp classes)", java_path),
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
