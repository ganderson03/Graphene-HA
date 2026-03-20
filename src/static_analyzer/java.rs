/// Java static escape analyzer using text-based pattern matching

use crate::protocol::{
    ConfidenceLevel, EscapeType, SourceLocation, StaticAnalysisResult, StaticEscape,
    StaticEscapeSummary,
};
use crate::static_analyzer::StaticEscapeAnalyzer;
use anyhow::{Context, Result};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::time::Instant;

const RETAINER_HINTS: [&str; 7] = [
    "retained",
    "cache",
    "audit",
    "handler",
    "registry",
    "store",
    "sink",
];

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
    let class_retainers = collect_class_retainers(&lines);

    let mut escapes = vec![];
    let mut dedupe: HashSet<String> = HashSet::new();

    let mut in_target = false;
    let mut brace_depth = 0i32;
    let mut found_method = false;

    let mut thread_vars: HashSet<String> = HashSet::new();
    let mut joined_vars: HashSet<String> = HashSet::new();

    let mut local_vars: HashSet<String> = HashSet::new();
    let mut local_object_vars: HashSet<String> = HashSet::new();
    let mut object_dependencies: HashMap<String, HashSet<String>> = HashMap::new();
    
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = strip_comment(line).trim();
        
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
            if let Some((local_name, rhs)) = extract_java_assignment(trimmed) {
                local_vars.insert(local_name.clone());
                if looks_like_java_object_initializer(&rhs) {
                    local_object_vars.insert(local_name.clone());
                }

                for id in extract_identifiers(&rhs) {
                    if id == local_name {
                        continue;
                    }
                    if local_vars.contains(&id) || local_object_vars.contains(&id) {
                        object_dependencies
                            .entry(local_name.clone())
                            .or_default()
                            .insert(id);
                    }
                }
            }

            if let Some((receiver, method, value_expr, is_closure)) = extract_java_store_call(trimmed) {
                if local_object_vars.contains(&receiver) {
                    for id in extract_identifiers(&value_expr) {
                        if local_vars.contains(&id) || local_object_vars.contains(&id) {
                            object_dependencies
                                .entry(receiver.clone())
                                .or_default()
                                .insert(id);
                        }
                    }
                }

                if is_retainer_container(&receiver, &class_retainers) {
                    let escaped_vars = resolve_escaped_variables(
                        &value_expr,
                        &local_vars,
                        &local_object_vars,
                        &object_dependencies,
                    );

                    for escaped_var in escaped_vars {
                        let escape_type = if is_closure {
                            EscapeType::ClosureEscape
                        } else {
                            EscapeType::GlobalEscape
                        };

                        let reason = if is_closure {
                            format!(
                                "Local object '{}' captured by retained closure in '{}.{}'",
                                escaped_var, receiver, method
                            )
                        } else {
                            format!(
                                "Local object '{}' stored in retained class container '{}'",
                                escaped_var, receiver
                            )
                        };

                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            if is_closure { "closure" } else { "global" },
                            escape_type,
                            source_file,
                            idx + 1,
                            trimmed.find(&receiver).unwrap_or(0),
                            method_name,
                            escaped_var,
                            reason,
                            ConfidenceLevel::High,
                            Some(trimmed.to_string()),
                        );
                    }
                }
            }

            if let Some(returned_name) = extract_return_identifier(trimmed) {
                if local_object_vars.contains(&returned_name)
                    || object_dependencies.contains_key(&returned_name)
                {
                    let reason = format!("Local object '{}' returned from method", returned_name);
                    push_unique_escape(
                        &mut escapes,
                        &mut dedupe,
                        "return",
                        EscapeType::ReturnEscape,
                        source_file,
                        idx + 1,
                        trimmed.find(&returned_name).unwrap_or(0),
                        method_name,
                        returned_name,
                        reason,
                        ConfidenceLevel::High,
                        Some(trimmed.to_string()),
                    );
                }
            }

            // Track thread variable creation
            if trimmed.contains("new Thread") || trimmed.contains("new java.lang.Thread") {
                if let Some(var_name) = extract_thread_variable(trimmed) {
                    thread_vars.insert(var_name);
                }
                
                // Check if thread is started on the same line
                if trimmed.contains(".start()") && !trimmed.contains(".join()") {
                    let reason = "Thread created and started inline without join".to_string();
                    push_unique_escape(
                        &mut escapes,
                        &mut dedupe,
                        "thread",
                        classify_java_async_escape(Some(trimmed), &reason),
                        source_file,
                        idx + 1,
                        0,
                        method_name,
                        "thread".to_string(),
                        reason,
                        ConfidenceLevel::High,
                        Some(trimmed.to_string()),
                    );
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
                            let reason = format!("Thread/Executor '{}' created but not joined/shutdown", var);
                            push_unique_escape(
                                &mut escapes,
                                &mut dedupe,
                                "executor",
                                classify_java_async_escape(None, &reason),
                                source_file,
                                line_num,
                                0,
                                method_name,
                                var.clone(),
                                reason,
                                ConfidenceLevel::High,
                                None,
                            );
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

fn strip_comment(line: &str) -> &str {
    line.split("//").next().unwrap_or("").trim()
}

fn is_retainer_name(name: &str) -> bool {
    let lower = name.to_lowercase();
    RETAINER_HINTS.iter().any(|hint| lower.contains(hint))
}

fn collect_class_retainers(lines: &[&str]) -> HashSet<String> {
    let mut retainers = HashSet::new();

    for line in lines {
        let trimmed = strip_comment(line);
        if !trimmed.contains("static") || !trimmed.contains('=') {
            continue;
        }

        let assign_idx = match trimmed.find('=') {
            Some(idx) => idx,
            None => continue,
        };
        let left = trimmed[..assign_idx].trim();
        let rhs = trimmed[assign_idx + 1..].trim();

        let Some(name) = extract_last_identifier(left) else {
            continue;
        };

        if is_retainer_name(&name) && looks_like_retainer_initializer(rhs) {
            retainers.insert(name);
        }
    }

    retainers
}

fn looks_like_retainer_initializer(rhs: &str) -> bool {
    let normalized = rhs.trim().to_lowercase();
    normalized.starts_with("new arraylist")
        || normalized.starts_with("new linkedlist")
        || normalized.starts_with("new hashmap")
        || normalized.starts_with("new hashmap")
        || normalized.starts_with("new map")
        || normalized.starts_with("new hashset")
        || normalized.starts_with("new set")
        || normalized.starts_with("new concurrent")
}

fn looks_like_java_object_initializer(rhs: &str) -> bool {
    let normalized = rhs.trim().to_lowercase();
    normalized.starts_with("new ") || normalized.starts_with("{")
}

fn is_retainer_container(name: &str, class_retainers: &HashSet<String>) -> bool {
    class_retainers.contains(name) || is_retainer_name(name)
}

fn extract_java_assignment(line: &str) -> Option<(String, String)> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    if trimmed.is_empty() || trimmed.starts_with("return ") {
        return None;
    }
    if trimmed.starts_with("if ") || trimmed.starts_with("for ") || trimmed.starts_with("while ") {
        return None;
    }
    if trimmed.contains("==") {
        return None;
    }

    let assign_idx = trimmed.find('=')?;
    let left = trimmed[..assign_idx].trim();
    if left.is_empty() || left.contains('(') {
        return None;
    }
    let rhs = trimmed[assign_idx + 1..].trim();
    if rhs.is_empty() {
        return None;
    }

    let name = extract_last_identifier(left)?;
    Some((name, rhs.to_string()))
}

fn extract_java_store_call(line: &str) -> Option<(String, String, String, bool)> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    let dot_idx = trimmed.find('.')?;
    let open_idx = trimmed.find('(')?;
    let close_idx = trimmed.rfind(')')?;
    if open_idx <= dot_idx || close_idx <= open_idx {
        return None;
    }

    let receiver = extract_last_identifier(trimmed[..dot_idx].trim())?;
    let method = trimmed[dot_idx + 1..open_idx].trim();
    if !matches!(method, "put" | "add" | "offer" | "push" | "set") {
        return None;
    }

    let args = trimmed[open_idx + 1..close_idx].trim();
    if args.is_empty() {
        return None;
    }

    let value_expr = if method == "put" || method == "set" {
        if let Some((_, rhs)) = split_first_top_level_comma(args) {
            rhs.trim().to_string()
        } else {
            args.to_string()
        }
    } else {
        args.to_string()
    };

    let is_closure = value_expr.contains("->") || value_expr.contains("::");
    Some((receiver, method.to_string(), value_expr, is_closure))
}

fn extract_return_identifier(line: &str) -> Option<String> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    let returned = trimmed.strip_prefix("return ")?.trim();
    if returned.is_empty() {
        return None;
    }
    if returned
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
    {
        return Some(returned.to_string());
    }
    None
}

fn extract_last_identifier(text: &str) -> Option<String> {
    extract_identifiers(text).into_iter().last()
}

fn extract_identifiers(text: &str) -> Vec<String> {
    let mut identifiers = Vec::new();
    let mut current = String::new();

    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            current.push(ch);
            continue;
        }

        if !current.is_empty() {
            if !is_java_keyword(&current)
                && current
                    .chars()
                    .next()
                    .map(|c| c.is_ascii_alphabetic() || c == '_')
                    .unwrap_or(false)
            {
                identifiers.push(current.clone());
            }
            current.clear();
        }
    }

    if !current.is_empty()
        && !is_java_keyword(&current)
        && current
            .chars()
            .next()
            .map(|c| c.is_ascii_alphabetic() || c == '_')
            .unwrap_or(false)
    {
        identifiers.push(current);
    }

    identifiers
}

fn is_java_keyword(token: &str) -> bool {
    matches!(
        token,
        "abstract"
            | "assert"
            | "boolean"
            | "break"
            | "byte"
            | "case"
            | "catch"
            | "char"
            | "class"
            | "const"
            | "continue"
            | "default"
            | "do"
            | "double"
            | "else"
            | "enum"
            | "extends"
            | "final"
            | "finally"
            | "float"
            | "for"
            | "goto"
            | "if"
            | "implements"
            | "import"
            | "instanceof"
            | "int"
            | "interface"
            | "long"
            | "native"
            | "new"
            | "null"
            | "package"
            | "private"
            | "protected"
            | "public"
            | "return"
            | "short"
            | "static"
            | "strictfp"
            | "super"
            | "switch"
            | "synchronized"
            | "this"
            | "throw"
            | "throws"
            | "transient"
            | "try"
            | "void"
            | "volatile"
            | "while"
            | "true"
            | "false"
            | "var"
    )
}

fn split_first_top_level_comma(text: &str) -> Option<(String, String)> {
    let mut paren_depth = 0i32;
    let mut brace_depth = 0i32;
    let mut bracket_depth = 0i32;

    for (idx, ch) in text.char_indices() {
        match ch {
            '(' => paren_depth += 1,
            ')' => paren_depth -= 1,
            '{' => brace_depth += 1,
            '}' => brace_depth -= 1,
            '[' => bracket_depth += 1,
            ']' => bracket_depth -= 1,
            ',' if paren_depth == 0 && brace_depth == 0 && bracket_depth == 0 => {
                return Some((text[..idx].to_string(), text[idx + 1..].to_string()));
            }
            _ => {}
        }
    }

    None
}

fn resolve_escaped_variables(
    expression: &str,
    local_vars: &HashSet<String>,
    local_object_vars: &HashSet<String>,
    object_dependencies: &HashMap<String, HashSet<String>>,
) -> HashSet<String> {
    let mut escaped = HashSet::new();

    for identifier in extract_identifiers(expression) {
        if local_vars.contains(&identifier) || local_object_vars.contains(&identifier) {
            escaped.insert(identifier.clone());
            let mut visited = HashSet::new();
            expand_dependencies(&identifier, object_dependencies, &mut escaped, &mut visited);
        }
    }

    escaped
}

fn expand_dependencies(
    variable: &str,
    object_dependencies: &HashMap<String, HashSet<String>>,
    output: &mut HashSet<String>,
    visited: &mut HashSet<String>,
) {
    if visited.contains(variable) {
        return;
    }
    visited.insert(variable.to_string());

    let Some(next) = object_dependencies.get(variable) else {
        return;
    };

    for dep in next {
        if output.insert(dep.clone()) {
            expand_dependencies(dep, object_dependencies, output, visited);
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn push_unique_escape(
    escapes: &mut Vec<StaticEscape>,
    dedupe: &mut HashSet<String>,
    key_type: &str,
    escape_type: EscapeType,
    source_file: &str,
    line: usize,
    column: usize,
    function: &str,
    variable_name: String,
    reason: String,
    confidence: ConfidenceLevel,
    code_snippet: Option<String>,
) {
    let key = format!("{}|{}|{}|{}", key_type, line, variable_name, reason);
    if !dedupe.insert(key) {
        return;
    }

    escapes.push(StaticEscape {
        escape_type,
        location: SourceLocation {
            file: source_file.to_string(),
            line,
            column,
            function: function.to_string(),
            code_snippet,
        },
        variable_name,
        reason,
        confidence,
        data_flow: vec![],
    });
}

fn extract_method_name(line: &str) -> Option<String> {
    // Look for method patterns like: public static String methodName(
    // or: public String methodName(
    if !line.contains('(') || line.contains("=") {
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

fn classify_java_async_escape(code_snippet: Option<&str>, reason: &str) -> EscapeType {
    let combined = format!("{} {}", reason, code_snippet.unwrap_or_default()).to_lowercase();

    if combined.contains("return") || combined.contains("returned") {
        EscapeType::ReturnEscape
    } else if combined.contains("global") || combined.contains("static ") {
        EscapeType::GlobalEscape
    } else if combined.contains("lambda") || combined.contains("runnable") || combined.contains("->") {
        EscapeType::ClosureEscape
    } else if combined.contains("parameter")
        || combined.contains("argument")
        || combined.contains("submit(")
        || combined.contains("execute(")
    {
        EscapeType::ParameterEscape
    } else {
        // Threads/executors not joined are treated as runtime-managed objects escaping local lifetime.
        EscapeType::HeapEscape
    }
}

fn detect_thread_creation(line: &str, source_file: &str, line_num: usize, function: &str) -> Option<StaticEscape> {
    let trimmed = strip_comment(line).trim();
    if (trimmed.contains("new Thread") || trimmed.contains("new java.lang.Thread")) 
        && trimmed.contains(".start()") {
        let reason = "Thread created and started".to_string();
        Some(StaticEscape {
            escape_type: classify_java_async_escape(Some(trimmed), &reason),
            location: SourceLocation {
                file: source_file.to_string(),
                line: line_num,
                column: 0,
                function: function.to_string(),
                code_snippet: Some(trimmed.to_string()),
            },
            variable_name: "thread".to_string(),
            reason,
            confidence: ConfidenceLevel::High,
            data_flow: vec![],
        })
    } else {
        None
    }
}
