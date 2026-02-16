/// Java static escape analyzer using text-based pattern matching

use crate::protocol::{
    StaticAnalysisResult, StaticEscape, StaticEscapeSummary, EscapeType,
    SourceLocation, ConfidenceLevel,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Result, Context};
use std::collections::HashSet;
use std::fs;
use std::time::Instant;

pub struct JavaStaticAnalyzer;

impl JavaStaticAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl StaticEscapeAnalyzer for JavaStaticAnalyzer {
    fn analyze(&self, target: &str, source_file: &str) -> Result<StaticAnalysisResult> {
        let start_time = Instant::now();
        let source = fs::read_to_string(source_file)
            .with_context(|| format!("Failed to read source file: {}", source_file))?;
        
        let target_function = parse_target_function(target);
        let mut warnings = vec![];
        
        let escapes = if let Some(function_name) = target_function.as_deref() {
            analyze_method(&source, source_file, function_name, &mut warnings)
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
        "java"
    }
    
    fn is_available(&self) -> bool {
        std::process::Command::new("javac")
            .arg("-version")
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
        if let Some(escape) = detect_thread_creation(line, source_file, idx + 1, "<class>") {
            escapes.push(escape);
        }
    }
    escapes
}

fn analyze_method(
    source: &str,
    source_file: &str,
    method_name: &str,
    warnings: &mut Vec<String>,
) -> Vec<StaticEscape> {
    let lines: Vec<&str> = source.lines().collect();
    let mut escapes = vec![];
    let mut in_target = false;
    let mut brace_depth = 0i32;
    let mut found_method = false;
    let mut thread_vars: HashSet<String> = HashSet::new();
    let mut joined_vars: HashSet<String> = HashSet::new();
    
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        
        if !in_target {
            // Look for method definition
            if let Some(name) = extract_method_name(trimmed) {
                if name == method_name {
                    found_method = true;
                    in_target = true;
                    brace_depth = 0;
                    if trimmed.contains('{') {
                        brace_depth = 1;
                    }
                }
            }
        } else {
            // Track thread variable creation
            if trimmed.contains("new Thread") || trimmed.contains("new java.lang.Thread") {
                if let Some(var_name) = extract_thread_variable(trimmed) {
                    thread_vars.insert(var_name);
                }
                
                // Check if thread is started on the same line
                if trimmed.contains(".start()") && !trimmed.contains(".join()") {
                    escapes.push(StaticEscape {
                        escape_type: EscapeType::ConcurrencyEscape,
                        location: SourceLocation {
                            file: source_file.to_string(),
                            line: idx + 1,
                            column: 0,
                            function: method_name.to_string(),
                            code_snippet: Some(trimmed.to_string()),
                        },
                        variable_name: "thread".to_string(),
                        reason: "Thread created and started inline without join".to_string(),
                        confidence: ConfidenceLevel::High,
                        data_flow: vec![],
                    });
                }
            }
            
            // Check for ExecutorService creation
            if (trimmed.contains("Executors.") || trimmed.contains("ExecutorService")) 
                && !trimmed.contains(".shutdown()") {
                if let Some(var_name) = extract_executor_variable(trimmed) {
                    thread_vars.insert(var_name);
                }
            }
            
            // Track .join() calls
            if let Some(var_name) = extract_join_call(trimmed) {
                joined_vars.insert(var_name);
            }
            
            // Track .shutdown() or .awaitTermination() on executors
            if trimmed.contains(".shutdown()") || trimmed.contains(".awaitTermination(") {
                if let Some(var_name) = extract_variable_before_dot(trimmed) {
                    joined_vars.insert(var_name);
                }
            }
            
            // Track braces
            brace_depth += trimmed.chars().filter(|&c| c == '{').count() as i32;
            brace_depth -= trimmed.chars().filter(|&c| c == '}').count() as i32;
            
            if brace_depth <= 0 && in_target {
                // Check for threads/executors that were never joined
                for var in &thread_vars {
                    if !joined_vars.contains(var) {
                        if let Some(line_num) = find_variable_line(&lines, method_name, var, idx) {
                            escapes.push(StaticEscape {
                                escape_type: EscapeType::ConcurrencyEscape,
                                location: SourceLocation {
                                    file: source_file.to_string(),
                                    line: line_num,
                                    column: 0,
                                    function: method_name.to_string(),
                                    code_snippet: None,
                                },
                                variable_name: var.clone(),
                                reason: format!("Thread/Executor '{}' created but not joined/shutdown", var),
                                confidence: ConfidenceLevel::High,
                                data_flow: vec![],
                            });
                        }
                    }
                }
                break;
            }
        }
    }
    
    if !found_method {
        warnings.push(format!("Target method '{}' not found in source file", method_name));
    }
    
    escapes
}

fn extract_method_name(line: &str) -> Option<String> {
    // Look for method patterns like: public static String methodName(
    // or: public String methodName(
    if !line.contains('(') {
        return None;
    }
    
    let parts: Vec<&str> = line.split('(').next()?.split_whitespace().collect();
    if parts.len() >= 2 {
        // Last part before '(' should be the method name
        let last = parts.last()?;
        if last.chars().all(|c| c.is_alphanumeric() || c == '_') {
            return Some(last.to_string());
        }
    }
    
    None
}

fn extract_thread_variable(line: &str) -> Option<String> {
    // Pattern: Thread varname = new Thread(...)
    // or: Thread varname = ...
    if let Some(thread_idx) = line.find("Thread ") {
        let after = &line[thread_idx + 7..];
        let mut var_name = String::new();
        
        for ch in after.trim().chars() {
            if ch.is_alphanumeric() || ch == '_' {
                var_name.push(ch);
            } else {
                break;
            }
        }
        
        if !var_name.is_empty() && var_name != "new" {
            return Some(var_name);
        }
    }
    
    None
}

fn extract_executor_variable(line: &str) -> Option<String> {
    // Pattern: ExecutorService varname = ...
    if let Some(exec_idx) = line.find("ExecutorService ") {
        let after = &line[exec_idx + 16..];
        let mut var_name = String::new();
        
        for ch in after.trim().chars() {
            if ch.is_alphanumeric() || ch == '_' {
                var_name.push(ch);
            } else {
                break;
            }
        }
        
        if !var_name.is_empty() {
            return Some(var_name);
        }
    }
    
    None
}

fn extract_join_call(line: &str) -> Option<String> {
    // Pattern: varname.join()
    if !line.contains(".join()") {
        return None;
    }
    
    extract_variable_before_dot(line)
}

fn extract_variable_before_dot(line: &str) -> Option<String> {
    if let Some(dot_idx) = line.find('.') {
        let before = &line[..dot_idx];
        let mut var_name = String::new();
        
        for ch in before.chars().rev() {
            if ch.is_alphanumeric() || ch == '_' {
                var_name.insert(0, ch);
            } else if !var_name.is_empty() {
                break;
            }
        }
        
        if !var_name.is_empty() {
            return Some(var_name);
        }
    }
    
    None
}

fn find_variable_line(lines: &[&str], method_name: &str, var_name: &str, max_idx: usize) -> Option<usize> {
    let mut in_method = false;
    
    for (idx, line) in lines.iter().enumerate().take(max_idx + 1) {
        if !in_method {
            if let Some(name) = extract_method_name(line.trim()) {
                if name == method_name {
                    in_method = true;
                }
            }
        } else {
            if line.contains(var_name) && (line.contains("new Thread") || line.contains("ExecutorService")) {
                return Some(idx + 1);
            }
        }
    }
    
    None
}

fn detect_thread_creation(line: &str, source_file: &str, line_num: usize, function: &str) -> Option<StaticEscape> {
    let trimmed = line.trim();
    if (trimmed.contains("new Thread") || trimmed.contains("new java.lang.Thread")) 
        && trimmed.contains(".start()") {
        Some(StaticEscape {
            escape_type: EscapeType::ConcurrencyEscape,
            location: SourceLocation {
                file: source_file.to_string(),
                line: line_num,
                column: 0,
                function: function.to_string(),
                code_snippet: Some(trimmed.to_string()),
            },
            variable_name: "thread".to_string(),
            reason: "Thread created and started".to_string(),
            confidence: ConfidenceLevel::High,
            data_flow: vec![],
        })
    } else {
        None
    }
}
