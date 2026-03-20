use anyhow::Result;
use tokio::process::Command;
use crate::analyzer::BridgeAnalyzer;
use crate::protocol::AnalyzerInfo;

pub async fn create() -> Result<BridgeAnalyzer> {
    let node_path = find_node().await?;
    let bridge_script = crate::analyzer::workspace_root()?
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
            supported_features: crate::analyzer::standardized_object_escape_capabilities(),
            executable_path: node_path,
        },
        |target| target.ends_with(".js") || target.ends_with(".mjs") || target.ends_with(".cjs"),
    ))
}

async fn find_node() -> Result<String> {
    let mut candidates = vec!["node".to_string(), "nodejs".to_string()];
    candidates.extend(common_windows_node_paths());

    for candidate in candidates {
        if let Ok(output) = Command::new(&candidate).arg("--version").output().await {
            if output.status.success() {
                return Ok(candidate);
            }
        }
    }

    anyhow::bail!("Node.js not found in PATH or common installation directories")
}

fn common_windows_node_paths() -> Vec<String> {
    #[cfg(not(target_os = "windows"))]
    {
        vec![]
    }

    #[cfg(target_os = "windows")]
    {
        let mut candidates = Vec::new();

        if let Ok(program_files) = std::env::var("ProgramFiles") {
            candidates.push(format!("{}\\nodejs\\node.exe", program_files));
        }
        if let Ok(program_files_x86) = std::env::var("ProgramFiles(x86)") {
            candidates.push(format!("{}\\nodejs\\node.exe", program_files_x86));
        }
        if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
            candidates.push(format!("{}\\Programs\\nodejs\\node.exe", local_app_data));
        }

        candidates
            .into_iter()
            .filter(|path| std::path::Path::new(path).exists())
            .collect()
    }
}
