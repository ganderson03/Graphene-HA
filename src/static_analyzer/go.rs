/// Go static escape analyzer using text-based pattern matching

use crate::protocol::{
    StaticAnalysisResult, StaticEscape, StaticEscapeSummary, EscapeType,
    SourceLocation, ConfidenceLevel,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Result, Context};
use std::collections::HashSet;
use std::fs;
use std::time::Instant;

pub struct GoStaticAnalyzer;

impl GoStaticAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl StaticEscapeAnalyzer for GoStaticAnalyzer {
    fn analyze(&self, target: &str, source_file: &str) -> Result<StaticAnalysisResult> {
        let start_time = Instant::now();
        let source = fs::read_to_string(source_file)
            .with_context(|| format!("Failed to read source file: {}", source_file))?;
        
        let target_function = parse_target_function(target);
        let mut warnings = vec![];
        
        let escapes = if let Some(function_name) = target_function.as_deref() {
            analyze_function(&source, source_file, function_name, &mut warnings)
        } else {
            analyze_file(&source, source_file)
        };
        
        let mut summary = StaticEscapeSummary::new();
        for escape in &escapes {
            summary.add_escape(escape);
        }
        
        Ok(StaticAnalysisResult {
            target: target.to_string(),
            source_file: source_file.to_string(),
            escapes,
            analysis_time_ms: start_time.elapsed().as_millis() as u64,
            warnings,
            summary,
        })
    }
    
    fn language(&self) -> &str {
        "go"
    }
    
    fn is_available(&self) -> bool {
        std::process::Command::new("go")
            .arg("version")
            .output()
            .is_ok()
    }
}

fn parse_target_function(target: &str) -> Option<String> {
    let parts: Vec<&str> = target.split(':').collect();
    if parts.len() == 2 {
        Some(parts[1].trim().to_string())
    } else {
        None
    }
}

fn analyze_file(source: &str, source_file: &str) -> Vec<StaticEscape> {
    let mut escapes = vec![];
    for (idx, line) in source.lines().enumerate() {
        if let Some(escape) = detect_goroutine(line, source_file, idx + 1, "<module>") {
            escapes.push(escape);
        }
    }
    escapes
}

fn analyze_function(
    source: &str,
    source_file: &str,
    function_name: &str,
    warnings: &mut Vec<String>,
) -> Vec<StaticEscape> {
    let lines: Vec<&str> = source.lines().collect();
    let mut escapes = vec![];
    let mut in_target = false;
    let mut brace_depth = 0i32;
    let mut found_function = false;
    let mut channels: HashSet<String> = HashSet::new();
    let mut received_channels: HashSet<String> = HashSet::new();
    
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        
        if !in_target {
            // Look for function definition: "func FunctionName"
            if let Some(name) = extract_func_name(trimmed) {
                if name == function_name {
                    found_function = true;
                    in_target = true;
                    brace_depth = 0;
                    if trimmed.contains('{') {
                        brace_depth = 1;
                    }
                }
            }
        } else {
            // Track channel creation
            if let Some(chan_var) = extract_channel_make(trimmed) {
                channels.insert(chan_var);
            }
            
            // Track channel receives (blocking operations)
            if let Some(chan_var) = extract_channel_receive(trimmed) {
                received_channels.insert(chan_var);
            }
            
            // Detect goroutine spawns
            if trimmed.contains("go ") && !trimmed.starts_with("//") {
                escapes.push(StaticEscape {
                    escape_type: EscapeType::ConcurrencyEscape,
                    location: SourceLocation {
                        file: source_file.to_string(),
                        line: idx + 1,
                        column: 0,
                        function: function_name.to_string(),
                        code_snippet: Some(trimmed.to_string()),
                    },
                    variable_name: "goroutine".to_string(),
                    reason: "Goroutine spawned - may not complete before function return".to_string(),
                    confidence: ConfidenceLevel::High,
                    data_flow: vec![],
                });
            }
            
            // Track braces
            brace_depth += trimmed.chars().filter(|&c| c == '{').count() as i32;
            brace_depth -= trimmed.chars().filter(|&c| c == '}').count() as i32;
            
            if brace_depth <= 0 && in_target {
                // Check for channels without receives
                for chan in &channels {
                    if !received_channels.contains(chan) {
                        escapes.push(StaticEscape {
                            escape_type: EscapeType::ConcurrencyEscape,
                            location: SourceLocation {
                                file: source_file.to_string(),
                                line: idx + 1,
                                column: 0,
                                function: function_name.to_string(),
                                code_snippet: None,
                            },
                            variable_name: chan.clone(),
                            reason: format!("Channel '{}' created but never received on (goroutine may leak)", chan),
                            confidence: ConfidenceLevel::Medium,
                            data_flow: vec![],
                        });
                    }
                }
                break;
            }
        }
    }
    
    if !found_function {
        warnings.push(format!("Target function '{}' not found in source file", function_name));
    }
    
    escapes
}

fn extract_func_name(line: &str) -> Option<String> {
    if !line.contains("func ") {
        return None;
    }
    
    let func_idx = line.find("func ")?;
    let after_func = &line[func_idx + 5..];
    let mut name = String::new();
    
    for ch in after_func.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            name.push(ch);
        } else if ch == '(' || ch.is_whitespace() {
            break;
        } else {
            return None;
        }
    }
    
    if name.is_empty() { None } else { Some(name) }
}

fn extract_channel_make(line: &str) -> Option<String> {
    // Look for patterns like: varname := make(chan ...)
    if !line.contains("make(chan") {
        return None;
    }
    
    // Try to extract variable name before := or =
    if let Some(assign_idx) = line.find(":=").or_else(|| line.find(" = ")) {
        let before = &line[..assign_idx].trim();
        let parts: Vec<&str> = before.split_whitespace().collect();
        if let Some(last) = parts.last() {
            return Some(last.to_string());
        }
    }
    
    None
}

fn extract_channel_receive(line: &str) -> Option<String> {
    // Look for patterns like: <-channame
    if !line.contains("<-") {
        return None;
    }
    
    if let Some(arrow_idx) = line.find("<-") {
        let after = &line[arrow_idx + 2..].trim();
        let mut name = String::new();
        
        for ch in after.chars() {
            if ch.is_alphanumeric() || ch == '_' {
                name.push(ch);
            } else {
                break;
            }
        }
        
        if !name.is_empty() {
            return Some(name);
        }
    }
    
    None
}

fn detect_goroutine(line: &str, source_file: &str, line_num: usize, function: &str) -> Option<StaticEscape> {
    let trimmed = line.trim();
    if trimmed.contains("go ") && !trimmed.starts_with("//") {
        Some(StaticEscape {
            escape_type: EscapeType::ConcurrencyEscape,
            location: SourceLocation {
                file: source_file.to_string(),
                line: line_num,
                column: 0,
                function: function.to_string(),
                code_snippet: Some(trimmed.to_string()),
            },
            variable_name: "goroutine".to_string(),
            reason: "Goroutine spawned".to_string(),
            confidence: ConfidenceLevel::High,
            data_flow: vec![],
        })
    } else {
        None
    }
}
