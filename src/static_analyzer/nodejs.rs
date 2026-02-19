/// Node.js/JavaScript static escape analyzer

use crate::protocol::{
    StaticAnalysisResult, StaticEscape, StaticEscapeSummary, EscapeType,
    SourceLocation, ConfidenceLevel,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Result, Context};
use std::process::Command;
use serde::Deserialize;

pub struct NodeJsStaticAnalyzer;

impl NodeJsStaticAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl StaticEscapeAnalyzer for NodeJsStaticAnalyzer {
    fn analyze(&self, target: &str, source_file: &str) -> Result<StaticAnalysisResult> {
        let start_time = std::time::Instant::now();
        
        // Parse target to extract function name
        let (_, function) = parse_target(target)?;
        
        // Run Node.js analyzer script
        let escapes = self.analyze_js(&source_file, &function)?;
        
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
        "javascript"
    }
    
    fn is_available(&self) -> bool {
        Command::new("node")
            .arg("--version")
            .output()
            .is_ok()
    }
}

impl NodeJsStaticAnalyzer {
    fn analyze_js(&self, source_file: &str, function_name: &str) -> Result<Vec<StaticEscape>> {
        // Path to the static analyzer script
        let script_path = std::path::Path::new("analyzers/nodejs/static_analyzer.js");
        
        if !script_path.exists() {
            anyhow::bail!("Static analyzer script not found at: {:?}", script_path);
        }
        
        // Run analyzer
        let output = Command::new("node")
            .arg(script_path)
            .arg(source_file)
            .arg(function_name)
            .output()
            .context("Failed to run Node.js static analyzer")?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("Node.js static analyzer failed: {}", stderr);
        }
        
        // Parse JSON output
        let stdout = String::from_utf8_lossy(&output.stdout);
        let analysis: JsAnalysis = serde_json::from_str(&stdout)
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
struct JsAnalysis {
    escapes: Vec<JsEscape>,
    success: bool,
    #[serde(default)]
    error: Option<String>,
}

#[derive(Debug, Deserialize)]
struct JsEscape {
    escape_type: String,
    line: usize,
    column: usize,
    variable_name: String,
    reason: String,
    confidence: String,
    code_snippet: Option<String>,
}

impl From<JsEscape> for StaticEscape {
    fn from(je: JsEscape) -> Self {
        let escape_type = match je.escape_type.as_str() {
            "return" => EscapeType::ReturnEscape,
            "parameter" => EscapeType::ParameterEscape,
            "global" => EscapeType::GlobalEscape,
            "closure" => EscapeType::ClosureEscape,
            "heap" => EscapeType::HeapEscape,
            "concurrency" => EscapeType::ConcurrencyEscape,
            _ => EscapeType::UnknownEscape,
        };
        
        let confidence = match je.confidence.as_str() {
            "high" => ConfidenceLevel::High,
            "medium" => ConfidenceLevel::Medium,
            _ => ConfidenceLevel::Low,
        };
        
        StaticEscape {
            escape_type,
            location: SourceLocation {
                file: "".to_string(), // Will be filled by caller
                line: je.line,
                column: je.column,
                function: "".to_string(), // Will be filled by caller
                code_snippet: je.code_snippet,
            },
            variable_name: je.variable_name,
            reason: je.reason,
            confidence,
            data_flow: vec![],
        }
    }
}

fn parse_target(target: &str) -> Result<(String, String)> {
    let parts: Vec<&str> = target.split(':').collect();
    if parts.len() != 2 {
        anyhow::bail!("Invalid target format. Expected module:function");
    }
    Ok((parts[0].to_string(), parts[1].to_string()))
}
