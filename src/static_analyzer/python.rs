/// Python static escape analyzer using AST analysis

use crate::protocol::{
    StaticAnalysisResult, StaticEscape, StaticEscapeSummary, EscapeType,
    SourceLocation, ConfidenceLevel,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Result, Context};
use std::process::Command;
use serde::Deserialize;

pub struct PythonStaticAnalyzer;

impl PythonStaticAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl StaticEscapeAnalyzer for PythonStaticAnalyzer {
    fn analyze(&self, target: &str, source_file: &str) -> Result<StaticAnalysisResult> {
        let start_time = std::time::Instant::now();
        
        // Parse target to extract module and function
        let (_module, function) = parse_target(target)?;
        
        // Run Python AST analyzer
        let escapes = self.analyze_python_ast(source_file, &function)?;
        
        // Build summary
        let mut summary = StaticEscapeSummary::new();
        for escape in &escapes {
            summary.add_escape(escape);
        }
        
        let analysis_time_ms = start_time.elapsed().as_millis() as u64;
        
        Ok(StaticAnalysisResult {
            target: target.to_string(),
            source_file: source_file.to_string(),
            escapes,
            analysis_time_ms,
            warnings: vec![],
            summary,
        })
    }
    
    fn language(&self) -> &str {
        "python"
    }
    
    fn is_available(&self) -> bool {
        Command::new("python3")
            .arg("--version")
            .output()
            .is_ok()
    }
}

impl PythonStaticAnalyzer {
    fn analyze_python_ast(&self, source_file: &str, function_name: &str) -> Result<Vec<StaticEscape>> {
        // Path to the static analyzer script
        let script_path = crate::analyzer::workspace_root()?
            .join("analyzers/python/static_analyzer.py");
        
        if !script_path.exists() {
            anyhow::bail!("Static analyzer script not found at: {:?}", script_path);
        }
        
        // Run analyzer
        let output = Command::new("python3")
            .arg(script_path)
            .arg(source_file)
            .arg(function_name)
            .output()
            .context("Failed to run Python static analyzer")?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Python static analyzer failed: {}", stderr);
        }
        
        // Parse JSON output
        let stdout = String::from_utf8_lossy(&output.stdout);
        let analysis: PythonAstAnalysis = serde_json::from_str(&stdout)
            .context("Failed to parse analyzer output")?;
        
        if !analysis.success {
            if let Some(error) = analysis.error {
                anyhow::bail!("Analysis error: {}", error);
            }
        }
        
        // Convert to StaticEscape format
        Ok(analysis.escapes.into_iter().map(|e| {
            let mut escape: StaticEscape = e.into();
            escape.location.file = source_file.to_string();
            escape.location.function = function_name.to_string();
            escape
        }).collect())
    }
}

#[derive(Debug, Deserialize)]
struct PythonAstAnalysis {
    escapes: Vec<PythonEscape>,
    success: bool,
    #[serde(default)]
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct PythonEscape {
    escape_type: String,
    line: usize,
    column: usize,
    variable_name: String,
    reason: String,
    confidence: String,
    code_snippet: Option<String>,
}

impl From<PythonEscape> for StaticEscape {
    fn from(pe: PythonEscape) -> Self {
        let escape_type = match pe.escape_type.as_str() {
            "return" => EscapeType::ReturnEscape,
            "parameter" => EscapeType::ParameterEscape,
            "global" => EscapeType::GlobalEscape,
            "closure" => EscapeType::ClosureEscape,
            "heap" => EscapeType::HeapEscape,
            "concurrency" => classify_python_concurrency_escape(
                &pe.reason,
                &pe.variable_name,
                pe.code_snippet.as_deref(),
            ),
            _ => EscapeType::UnknownEscape,
        };
        
        let confidence = match pe.confidence.as_str() {
            "high" => ConfidenceLevel::High,
            "medium" => ConfidenceLevel::Medium,
            _ => ConfidenceLevel::Low,
        };
        
        StaticEscape {
            escape_type,
            location: SourceLocation {
                file: "".to_string(), // Will be filled by caller
                line: pe.line,
                column: pe.column,
                function: "".to_string(), // Will be filled by caller
                code_snippet: pe.code_snippet,
            },
            variable_name: pe.variable_name,
            reason: pe.reason,
            confidence,
            data_flow: vec![],
        }
    }
}

fn classify_python_concurrency_escape(
    reason: &str,
    variable_name: &str,
    code_snippet: Option<&str>,
) -> EscapeType {
    let combined = format!(
        "{} {} {}",
        reason,
        variable_name,
        code_snippet.unwrap_or_default()
    )
    .to_lowercase();

    if combined.contains("return") || combined.contains("returned") {
        EscapeType::ReturnEscape
    } else if combined.contains("global") || combined.contains("module") || combined.contains("singleton") {
        EscapeType::GlobalEscape
    } else if combined.contains("closure")
        || combined.contains("lambda")
        || combined.contains("capture")
        || combined.contains("nonlocal")
    {
        EscapeType::ClosureEscape
    } else if combined.contains("parameter")
        || combined.contains("argument")
        || combined.contains("passed")
        || combined.contains("callee")
    {
        EscapeType::ParameterEscape
    } else {
        // Default for thread/process/executor leaks: object outlives scope via runtime-owned heap state.
        EscapeType::HeapEscape
    }
}

fn parse_target(target: &str) -> Result<(String, String)> {
    let parts: Vec<&str> = target.split(':').collect();
    if parts.len() != 2 {
        anyhow::bail!("Invalid target format. Expected module:function");
    }
    Ok((parts[0].to_string(), parts[1].to_string()))
}
