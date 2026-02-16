/// Rust static escape analyzer using lightweight source parsing

use crate::protocol::{
    ConfidenceLevel, EscapeType, SourceLocation, StaticAnalysisResult, StaticEscape,
    StaticEscapeSummary,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Context, Result};
use std::collections::HashSet;
use std::fs;
use std::time::Instant;

pub struct RustStaticAnalyzer;

impl RustStaticAnalyzer {
    pub fn new() -> Self {
        Self
    }
}

impl StaticEscapeAnalyzer for RustStaticAnalyzer {
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

        if target_function.is_some() && escapes.is_empty() {
            warnings.push("No Rust escapes detected by heuristic analyzer".to_string());
        }

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
        "rust"
    }
    
    fn is_available(&self) -> bool {
        std::process::Command::new("rustc")
            .arg("--version")
            .output()
            .is_ok()
    }
}

fn parse_target_function(target: &str) -> Option<String> {
    let parts: Vec<&str> = target.split(':').collect();
    if parts.len() == 2 {
        let fn_part = parts[1].trim();
        if !fn_part.is_empty() {
            return Some(fn_part.to_string());
        }
    }
    None
}

fn analyze_file(source: &str, source_file: &str) -> Vec<StaticEscape> {
    let mut escapes = vec![];
    for (idx, line) in source.lines().enumerate() {
        if let Some(escape) = detect_concurrency(line, source_file, idx + 1, "<module>") {
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
    let mut brace_depth: i32 = 0;
    let mut locals: HashSet<String> = HashSet::new();
    let mut found_function = false;
    let mut i = 0;
    let mut thread_handles: HashSet<String> = HashSet::new();  // Track thread/task handles
    let mut joined_handles: HashSet<String> = HashSet::new();  // Track joined handles

    while i < lines.len() {
        let line = lines[i];

        if !in_target {
            if let Some(name) = extract_fn_name(line) {
                if name == function_name {
                    found_function = true;
                    let mut signature = line.to_string();
                    while !signature.contains('{') && i + 1 < lines.len() {
                        i += 1;
                        signature.push('\n');
                        signature.push_str(lines[i]);
                    }
                    locals.extend(extract_params(&signature));
                    brace_depth = count_braces(&signature);
                    in_target = brace_depth > 0;
                }
            }
        } else {
            if let Some(local) = extract_let_binding(line) {
                locals.insert(local.clone());
                // Check if this is a thread/task handle
                if is_thread_creation(line) {
                    thread_handles.insert(local);
                }
            }

            // Check for .join() calls
            if let Some(handle) = extract_join_call(line) {
                joined_handles.insert(handle);
            }

            if let Some(escape) = detect_return_escape(line, source_file, i + 1, function_name, &locals) {
                escapes.push(escape);
            }

            if let Some(escape) = detect_heap_escape(line, source_file, i + 1, function_name) {
                escapes.push(escape);
            }

            // Only report concurrency escape if handle is created (not just spawn calls)
            // We'll check for unjoined handles at the end

            brace_depth += count_braces(line);
            if brace_depth <= 0 {
                break;
            }
        }

        i += 1;
    }
    
    // Check for unjoined thread handles
    for handle in thread_handles {
        if !joined_handles.contains(&handle) {
            // Find the line where this handle was created
            if let Some(line_num) = find_variable_line(source, function_name, &handle) {
                escapes.push(StaticEscape {
                    escape_type: EscapeType::ConcurrencyEscape,
                    location: SourceLocation {
                        file: source_file.to_string(),
                        line: line_num,
                        column: 0,
                        function: function_name.to_string(),
                        code_snippet: None,
                    },
                    variable_name: handle.clone(),
                    reason: format!("Thread/task handle '{}' created but not joined", handle),
                    confidence: ConfidenceLevel::High,
                    data_flow: vec![],
                });
            }
        }
    }

    if !found_function {
        warnings.push(format!(
            "Target function '{}' not found in source file",
            function_name
        ));
    }

    escapes
}

fn extract_fn_name(line: &str) -> Option<String> {
    let fn_idx = line.find("fn ")?;
    let after_fn = &line[fn_idx + 3..];
    let mut name = String::new();
    for ch in after_fn.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            name.push(ch);
        } else {
            break;
        }
    }
    if name.is_empty() { None } else { Some(name) }
}

fn extract_params(signature: &str) -> HashSet<String> {
    let mut params = HashSet::new();
    let start = match signature.find('(') {
        Some(idx) => idx,
        None => return params,
    };
    let end = match signature[start + 1..].find(')') {
        Some(idx) => start + 1 + idx,
        None => return params,
    };
    let args = &signature[start + 1..end];
    for arg in args.split(',') {
        let mut arg = arg.trim();
        if arg.is_empty() {
            continue;
        }
        if arg.starts_with("self") || arg.starts_with("&self") || arg.starts_with("&mut self") {
            params.insert("self".to_string());
            continue;
        }
        if let Some(idx) = arg.find(':') {
            arg = &arg[..idx];
        }
        let arg = arg.trim().trim_start_matches('&').trim();
        let arg = arg.strip_prefix("mut ").unwrap_or(arg).trim();
        if let Some(name) = sanitize_ident(arg) {
            params.insert(name);
        }
    }
    params
}

fn extract_let_binding(line: &str) -> Option<String> {
    let let_idx = line.find("let ")?;
    let mut remainder = &line[let_idx + 4..];
    remainder = remainder.trim_start();
    if remainder.starts_with('(') {
        return None;
    }
    if let Some(rest) = remainder.strip_prefix("mut ") {
        remainder = rest.trim_start();
    }
    sanitize_ident(remainder)
}

fn sanitize_ident(value: &str) -> Option<String> {
    let mut ident = String::new();
    for ch in value.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            ident.push(ch);
        } else {
            break;
        }
    }
    if ident.is_empty() { None } else { Some(ident) }
}

fn detect_return_escape(
    line: &str,
    source_file: &str,
    line_number: usize,
    function_name: &str,
    locals: &HashSet<String>,
) -> Option<StaticEscape> {
    let return_idx = line.find("return ")?;
    let remainder = line[return_idx + 7..].trim();
    let name = sanitize_ident(remainder)?;
    if !locals.contains(&name) {
        return None;
    }
    Some(StaticEscape {
        escape_type: EscapeType::ReturnEscape,
        location: SourceLocation {
            file: source_file.to_string(),
            line: line_number,
            column: return_idx,
            function: function_name.to_string(),
            code_snippet: Some(line.trim().to_string()),
        },
        variable_name: name.clone(),
        reason: format!("Variable '{}' returned from function", name),
        confidence: ConfidenceLevel::High,
        data_flow: vec![],
    })
}

fn detect_heap_escape(
    line: &str,
    source_file: &str,
    line_number: usize,
    function_name: &str,
) -> Option<StaticEscape> {
    let heap_patterns = [
        "Box::new",
        "Vec::new",
        "String::new",
        "Arc::new",
        "Rc::new",
        "HashMap::new",
        "HashSet::new",
    ];
    if !heap_patterns.iter().any(|p| line.contains(p)) {
        return None;
    }
    let var = extract_let_binding(line).unwrap_or_else(|| "<unknown>".to_string());
    let column = line.find(&var).unwrap_or(0);
    Some(StaticEscape {
        escape_type: EscapeType::HeapEscape,
        location: SourceLocation {
            file: source_file.to_string(),
            line: line_number,
            column,
            function: function_name.to_string(),
            code_snippet: Some(line.trim().to_string()),
        },
        variable_name: var,
        reason: "Heap-allocated structure assigned to local variable".to_string(),
        confidence: ConfidenceLevel::Medium,
        data_flow: vec![],
    })
}

fn detect_concurrency(
    line: &str,
    source_file: &str,
    line_number: usize,
    function_name: &str,
) -> Option<StaticEscape> {
    let patterns = [
        ("std::thread::spawn", "Thread spawn"),
        ("thread::spawn", "Thread spawn"),
        ("tokio::spawn", "Async task spawn"),
        ("tokio::task::spawn", "Async task spawn"),
        ("std::thread::Builder", "Thread builder"),
    ];
    for (pattern, reason) in patterns {
        if line.contains(pattern) {
            let column = line.find(pattern).unwrap_or(0);
            return Some(StaticEscape {
                escape_type: EscapeType::ConcurrencyEscape,
                location: SourceLocation {
                    file: source_file.to_string(),
                    line: line_number,
                    column,
                    function: function_name.to_string(),
                    code_snippet: Some(line.trim().to_string()),
                },
                variable_name: pattern.to_string(),
                reason: format!("{} may leak work beyond scope", reason),
                confidence: ConfidenceLevel::High,
                data_flow: vec![],
            });
        }
    }
    None
}

fn count_braces(line: &str) -> i32 {
    let mut count = 0i32;
    for ch in line.chars() {
        match ch {
            '{' => count += 1,
            '}' => count -= 1,
            _ => {}
        }
    }
    count
}

fn is_thread_creation(line: &str) -> bool {
    let thread_patterns = [
        "thread::spawn",
        "std::thread::spawn",
        "tokio::spawn",
        "tokio::task::spawn",
        "thread::Builder",
    ];
    thread_patterns.iter().any(|p| line.contains(p))
}

fn extract_join_call(line: &str) -> Option<String> {
    // Look for patterns like: handle.join(), handle.await
    if line.contains(".join()") || line.contains(".await") {
        // Try to extract the variable name before the dot
        if let Some(dot_idx) = line.find('.') {
            let before_dot = &line[..dot_idx];
            // Get the last identifier before the dot
            let mut var_name = String::new();
            for ch in before_dot.chars().rev() {
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
    }
    None
}

fn find_variable_line(source: &str, function_name: &str, var_name: &str) -> Option<usize> {
    let lines: Vec<&str> = source.lines().collect();
    let mut in_target = false;
    let mut brace_depth = 0i32;
    
    for (idx, line) in lines.iter().enumerate() {
        if !in_target {
            if let Some(name) = extract_fn_name(line) {
                if name == function_name {
                    in_target = true;
                    brace_depth = count_braces(line);
                }
            }
        } else {
            if line.contains(&format!("let {}", var_name)) || line.contains(&format!("let mut {}", var_name)) {
                return Some(idx + 1);
            }
            brace_depth += count_braces(line);
            if brace_depth <= 0 {
                break;
            }
        }
    }
    None
}
