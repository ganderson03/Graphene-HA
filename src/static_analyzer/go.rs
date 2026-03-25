/// Go static escape analyzer using text-based pattern matching

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
    let module_retainers = collect_package_retainers(&lines);
    let bridge_method_sinks = collect_go_bridge_method_sinks(&lines, &module_retainers);

    let mut escapes = vec![];
    let mut dedupe: HashSet<String> = HashSet::new();

    let mut in_target = false;
    let mut brace_depth = 0i32;
    let mut found_function = false;

    let mut channels: HashSet<String> = HashSet::new();
    let mut received_channels: HashSet<String> = HashSet::new();

    let mut local_vars: HashSet<String> = HashSet::new();
    let mut local_object_vars: HashSet<String> = HashSet::new();
    let mut object_dependencies: HashMap<String, HashSet<String>> = HashMap::new();
    let mut helper_sink_dispatch: HashMap<String, (String, String)> = HashMap::new();
    let mut interface_bridge_bindings: HashMap<String, String> = HashMap::new();
    
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
            if let Some((local_name, rhs)) = extract_go_assignment_decl(trimmed) {
                local_vars.insert(local_name.clone());
                if looks_like_go_object_initializer(&rhs) {
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

            if let Some((binding, concrete_type)) = extract_go_interface_binding(trimmed) {
                interface_bridge_bindings.insert(binding, concrete_type);
            }

            if let Some((helper_name, param_name, container_name)) = extract_inline_helper_sink(trimmed)
            {
                if is_retainer_container(&container_name, &module_retainers) {
                    helper_sink_dispatch.insert(helper_name, (param_name, container_name));
                }
            }

            if let Some((callee, arg_expr)) = extract_simple_call(trimmed) {
                if let Some((_param_name, container_name)) = helper_sink_dispatch.get(&callee) {
                    let escaped_vars = resolve_escaped_variables(
                        &arg_expr,
                        &local_vars,
                        &local_object_vars,
                        &object_dependencies,
                    );

                    for escaped_var in escaped_vars {
                        let reason = format!(
                            "Local object '{}' passed through helper '{}' into retained container '{}'",
                            escaped_var, callee, container_name
                        );
                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            "global",
                            EscapeType::GlobalEscape,
                            source_file,
                            idx + 1,
                            trimmed.find(&callee).unwrap_or(0),
                            function_name,
                            escaped_var,
                            reason,
                            ConfidenceLevel::High,
                            Some(trimmed.to_string()),
                        );
                    }
                }
            }

            if let Some((receiver, method, arg_expr)) = extract_receiver_method_call(trimmed) {
                if let Some(concrete_type) = interface_bridge_bindings.get(&receiver) {
                    if bridge_method_sinks
                        .get(concrete_type)
                        .map(|methods| methods.contains(&method))
                        .unwrap_or(false)
                    {
                        let escaped_vars = resolve_escaped_variables(
                            &arg_expr,
                            &local_vars,
                            &local_object_vars,
                            &object_dependencies,
                        );

                        for escaped_var in escaped_vars {
                            let reason = format!(
                                "Local object '{}' passed through interface bridge '{}.{}' into retained container",
                                escaped_var, receiver, method
                            );
                            push_unique_escape(
                                &mut escapes,
                                &mut dedupe,
                                "global",
                                EscapeType::GlobalEscape,
                                source_file,
                                idx + 1,
                                trimmed.find(&receiver).unwrap_or(0),
                                function_name,
                                escaped_var,
                                reason,
                                ConfidenceLevel::High,
                                Some(trimmed.to_string()),
                            );
                        }
                    }
                }
            }

            if let Some((container, expr, is_closure)) = extract_append_store(trimmed) {
                if is_retainer_container(&container, &module_retainers) {
                    let escaped_vars = resolve_escaped_variables(
                        &expr,
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
                                "Local object '{}' captured by retained closure in '{}',",
                                escaped_var, container
                            )
                        } else {
                            format!(
                                "Local object '{}' stored in retained package container '{}',",
                                escaped_var, container
                            )
                        };
                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            if is_closure { "closure" } else { "global" },
                            escape_type,
                            source_file,
                            idx + 1,
                            trimmed.find(&container).unwrap_or(0),
                            function_name,
                            escaped_var,
                            reason,
                            ConfidenceLevel::High,
                            Some(trimmed.to_string()),
                        );
                    }
                }
            }

            if let Some((container, expr)) = extract_index_assignment(trimmed) {
                if is_retainer_container(&container, &module_retainers) {
                    let escaped_vars = resolve_escaped_variables(
                        &expr,
                        &local_vars,
                        &local_object_vars,
                        &object_dependencies,
                    );

                    for escaped_var in escaped_vars {
                        let reason = format!(
                            "Local object '{}' assigned into retained package container '{}',",
                            escaped_var, container
                        );
                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            "global",
                            EscapeType::GlobalEscape,
                            source_file,
                            idx + 1,
                            trimmed.find(&container).unwrap_or(0),
                            function_name,
                            escaped_var,
                            reason,
                            ConfidenceLevel::High,
                            Some(trimmed.to_string()),
                        );
                    }
                }
            }

            if let Some((container, expr, is_closure)) = extract_method_store(trimmed) {
                if is_retainer_container(&container, &module_retainers) {
                    let escaped_vars = resolve_escaped_variables(
                        &expr,
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
                                "Local object '{}' captured by retained closure stored in '{}',",
                                escaped_var, container
                            )
                        } else {
                            format!(
                                "Local object '{}' stored through retained container method on '{}',",
                                escaped_var, container
                            )
                        };
                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            if is_closure { "closure" } else { "global" },
                            escape_type,
                            source_file,
                            idx + 1,
                            trimmed.find(&container).unwrap_or(0),
                            function_name,
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
                    let reason = format!("Local object '{}' returned from function", returned_name);
                    push_unique_escape(
                        &mut escapes,
                        &mut dedupe,
                        "return",
                        EscapeType::ReturnEscape,
                        source_file,
                        idx + 1,
                        trimmed.find(&returned_name).unwrap_or(0),
                        function_name,
                        returned_name,
                        reason,
                        ConfidenceLevel::High,
                        Some(trimmed.to_string()),
                    );
                }
            }

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
                let reason = "Goroutine spawned - may not complete before function return".to_string();
                push_unique_escape(
                    &mut escapes,
                    &mut dedupe,
                    "goroutine",
                    classify_go_async_escape(Some(trimmed), &reason, "goroutine"),
                    source_file,
                    idx + 1,
                    0,
                    function_name,
                    "goroutine".to_string(),
                    reason,
                    ConfidenceLevel::High,
                    Some(trimmed.to_string()),
                );
            }
            
            // Track braces
            brace_depth += trimmed.chars().filter(|&c| c == '{').count() as i32;
            brace_depth -= trimmed.chars().filter(|&c| c == '}').count() as i32;
            
            if brace_depth <= 0 && in_target {
                // Check for channels without receives
                for chan in &channels {
                    if !received_channels.contains(chan) {
                        let reason = format!("Channel '{}' created but never received on (goroutine may leak)", chan);
                        push_unique_escape(
                            &mut escapes,
                            &mut dedupe,
                            "channel",
                            classify_go_async_escape(None, &reason, chan),
                            source_file,
                            idx + 1,
                            0,
                            function_name,
                            chan.clone(),
                            reason,
                            ConfidenceLevel::Medium,
                            None,
                        );
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

fn strip_comment(line: &str) -> &str {
    line.split("//").next().unwrap_or("").trim()
}

fn extract_inline_helper_sink(line: &str) -> Option<(String, String, String)> {
    // Example:
    // sink := func(obj map[string]string) { retainedCase202 = append(retainedCase202, obj) }
    let no_comment = strip_comment(line);
    if !no_comment.contains(":= func(") || !no_comment.contains("append(") {
        return None;
    }

    let helper_name = no_comment.split(":=").next()?.trim().to_string();
    if helper_name.is_empty() {
        return None;
    }

    let param_start = no_comment.find("func(")? + "func(".len();
    let param_end = no_comment[param_start..].find(')')? + param_start;
    let param_decl = no_comment[param_start..param_end].trim();
    let param_name = param_decl.split_whitespace().next()?.trim().to_string();
    if param_name.is_empty() {
        return None;
    }

    let body_start = no_comment.find('{')? + 1;
    let body = no_comment[body_start..].trim_end_matches('}').trim();
    let assign_idx = body.find('=')?;
    let container = body[..assign_idx].trim().to_string();

    let append_start = body.find("append(")? + "append(".len();
    let append_end = body[append_start..].find(')')? + append_start;
    let append_args = body[append_start..append_end].trim();
    let parts: Vec<&str> = append_args.split(',').map(|p| p.trim()).collect();
    if parts.len() < 2 {
        return None;
    }
    if parts[1] != param_name {
        return None;
    }

    Some((helper_name, param_name, container))
}

fn extract_simple_call(line: &str) -> Option<(String, String)> {
    // Match simple local helper call: helper(payload)
    let no_comment = strip_comment(line).trim().trim_end_matches(';').trim();
    if no_comment.is_empty() || no_comment.contains('.') || no_comment.starts_with("return ") {
        return None;
    }

    let open = no_comment.find('(')?;
    let close = no_comment.rfind(')')?;
    if close <= open {
        return None;
    }

    let callee = no_comment[..open].trim().to_string();
    if callee.is_empty() {
        return None;
    }

    let arg_expr = no_comment[open + 1..close].trim().to_string();
    if arg_expr.is_empty() {
        return None;
    }

    Some((callee, arg_expr))
}

fn extract_go_interface_binding(line: &str) -> Option<(String, String)> {
    // Supports:
    //   var s iface = concreteType{}
    //   s := concreteType{}
    let no_comment = strip_comment(line).trim().trim_end_matches(';').trim();
    if no_comment.is_empty() {
        return None;
    }

    if let Some(rest) = no_comment.strip_prefix("var ") {
        let assign_idx = rest.find('=')?;
        let left = rest[..assign_idx].trim();
        let rhs = rest[assign_idx + 1..].trim();
        if !rhs.ends_with("{}") {
            return None;
        }
        let concrete = rhs.trim_end_matches("{}").trim().to_string();
        let binding = left.split_whitespace().next()?.trim().to_string();
        if binding.is_empty() || concrete.is_empty() {
            return None;
        }
        return Some((binding, concrete));
    }

    if let Some(assign_idx) = no_comment.find(":=") {
        let left = no_comment[..assign_idx].trim();
        let rhs = no_comment[assign_idx + 2..].trim();
        if rhs.ends_with("{}") {
            let concrete = rhs.trim_end_matches("{}").trim().to_string();
            if !left.is_empty() && !concrete.is_empty() {
                return Some((left.to_string(), concrete));
            }
        }
    }

    None
}

fn extract_receiver_method_call(line: &str) -> Option<(String, String, String)> {
    // Match receiver.method(arg)
    let no_comment = strip_comment(line).trim().trim_end_matches(';').trim();
    if no_comment.is_empty() {
        return None;
    }

    let dot_idx = no_comment.find('.')?;
    let open_idx = no_comment.find('(')?;
    let close_idx = no_comment.rfind(')')?;
    if !(dot_idx < open_idx && open_idx < close_idx) {
        return None;
    }

    let receiver = no_comment[..dot_idx].trim().to_string();
    let method = no_comment[dot_idx + 1..open_idx].trim().to_string();
    let arg_expr = no_comment[open_idx + 1..close_idx].trim().to_string();
    if receiver.is_empty() || method.is_empty() || arg_expr.is_empty() {
        return None;
    }

    Some((receiver, method, arg_expr))
}

fn collect_go_bridge_method_sinks(
    lines: &[&str],
    module_retainers: &HashSet<String>,
) -> HashMap<String, HashSet<String>> {
    let mut sink_methods: HashMap<String, HashSet<String>> = HashMap::new();

    let mut in_method = false;
    let mut brace_depth: i32 = 0;
    let mut receiver_type = String::new();
    let mut method_name = String::new();
    let mut param_name = String::new();
    let mut stores_to_retainer = false;

    for line in lines {
        let trimmed = strip_comment(line).trim();
        if trimmed.is_empty() {
            continue;
        }

        if !in_method {
            if let Some((recv, method, param)) = extract_go_method_header(trimmed) {
                in_method = true;
                receiver_type = recv;
                method_name = method;
                param_name = param;
                stores_to_retainer = false;
                brace_depth = trimmed.chars().filter(|&c| c == '{').count() as i32
                    - trimmed.chars().filter(|&c| c == '}').count() as i32;
            }
            continue;
        }

        if let Some((container, expr, _)) = extract_append_store(trimmed) {
            if is_retainer_container(&container, module_retainers)
                && extract_identifiers(&expr).into_iter().any(|id| id == param_name)
            {
                stores_to_retainer = true;
            }
        }
        if let Some((container, expr)) = extract_index_assignment(trimmed) {
            if is_retainer_container(&container, module_retainers)
                && extract_identifiers(&expr).into_iter().any(|id| id == param_name)
            {
                stores_to_retainer = true;
            }
        }

        brace_depth += trimmed.chars().filter(|&c| c == '{').count() as i32;
        brace_depth -= trimmed.chars().filter(|&c| c == '}').count() as i32;

        if brace_depth <= 0 {
            if stores_to_retainer && !receiver_type.is_empty() && !method_name.is_empty() {
                sink_methods
                    .entry(receiver_type.clone())
                    .or_default()
                    .insert(method_name.clone());
            }
            in_method = false;
            receiver_type.clear();
            method_name.clear();
            param_name.clear();
            stores_to_retainer = false;
            brace_depth = 0;
        }
    }

    sink_methods
}

fn extract_go_method_header(line: &str) -> Option<(String, String, String)> {
    // Example: func (case205Bridge) Put(v map[string]string) {
    if !line.starts_with("func (") {
        return None;
    }

    let recv_start = line.find('(')? + 1;
    let recv_end = line[recv_start..].find(')')? + recv_start;
    let recv_decl = line[recv_start..recv_end].trim();
    let recv_parts: Vec<&str> = recv_decl.split_whitespace().collect();
    let receiver_type = recv_parts.last()?.trim().to_string();

    let after_recv = line[recv_end + 1..].trim();
    let method_end = after_recv.find('(')?;
    let method_name = after_recv[..method_end].trim().to_string();
    if method_name.is_empty() {
        return None;
    }

    let params_start = method_end + 1;
    let params_end = after_recv[params_start..].find(')')? + params_start;
    let params = after_recv[params_start..params_end].trim();
    let param_name = params.split_whitespace().next()?.trim().to_string();
    if param_name.is_empty() {
        return None;
    }

    Some((receiver_type, method_name, param_name))
}

fn is_retainer_name(name: &str) -> bool {
    let lower = name.to_lowercase();
    RETAINER_HINTS.iter().any(|hint| lower.contains(hint))
}

fn collect_package_retainers(lines: &[&str]) -> HashSet<String> {
    let mut retainers = HashSet::new();

    for line in lines {
        let trimmed = strip_comment(line);
        if !trimmed.starts_with("var ") || !trimmed.contains('=') {
            continue;
        }

        if let Some((name, rhs)) = extract_var_assignment(trimmed) {
            if is_retainer_name(&name) && looks_like_go_retainer_initializer(&rhs) {
                retainers.insert(name);
            }
        }
    }

    retainers
}

fn looks_like_go_retainer_initializer(rhs: &str) -> bool {
    let normalized = rhs.trim().to_lowercase();
    normalized.starts_with("[]")
        || normalized.starts_with("map[")
        || normalized.starts_with("make(map[")
        || normalized.starts_with("make([]")
        || normalized.starts_with("make(chan")
}

fn is_retainer_container(name: &str, module_retainers: &HashSet<String>) -> bool {
    module_retainers.contains(name) || is_retainer_name(name)
}

fn extract_var_assignment(line: &str) -> Option<(String, String)> {
    let trimmed = strip_comment(line);
    if !trimmed.starts_with("var ") {
        return None;
    }
    let after_var = trimmed[4..].trim();
    let assign_idx = after_var.find('=')?;
    let left = after_var[..assign_idx].trim();
    if left.contains(',') {
        return None;
    }
    let name = extract_last_identifier(left)?;
    let rhs = after_var[assign_idx + 1..]
        .trim()
        .trim_end_matches(';')
        .to_string();
    Some((name, rhs))
}

fn extract_go_assignment_decl(line: &str) -> Option<(String, String)> {
    let trimmed = strip_comment(line);

    if let Some(assign_idx) = trimmed.find(":=") {
        let left = trimmed[..assign_idx].trim();
        if left.contains(',') {
            return None;
        }
        let name = extract_last_identifier(left)?;
        let rhs = trimmed[assign_idx + 2..]
            .trim()
            .trim_end_matches(';')
            .to_string();
        return Some((name, rhs));
    }

    extract_var_assignment(trimmed)
}

fn looks_like_go_object_initializer(rhs: &str) -> bool {
    let normalized = rhs.trim();
    let lower = normalized.to_lowercase();

    (normalized.starts_with("map[") && normalized.contains('{'))
        || (normalized.starts_with("[]") && normalized.contains('{'))
        || lower.starts_with("make(map[")
        || lower.starts_with("make([]")
        || lower.starts_with("make(chan")
        || (normalized.starts_with('&') && normalized.contains('{'))
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
            if !is_go_keyword(&current)
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
        && !is_go_keyword(&current)
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

fn is_go_keyword(token: &str) -> bool {
    matches!(
        token,
        "break"
            | "case"
            | "chan"
            | "const"
            | "continue"
            | "default"
            | "defer"
            | "else"
            | "fallthrough"
            | "for"
            | "func"
            | "go"
            | "goto"
            | "if"
            | "import"
            | "interface"
            | "map"
            | "package"
            | "range"
            | "return"
            | "select"
            | "struct"
            | "switch"
            | "type"
            | "var"
            | "true"
            | "false"
            | "nil"
            | "string"
            | "int"
            | "bool"
            | "any"
            | "append"
            | "make"
    )
}

fn expand_dependencies(
    var_name: &str,
    object_dependencies: &HashMap<String, HashSet<String>>,
    output: &mut HashSet<String>,
    visited: &mut HashSet<String>,
) {
    if visited.contains(var_name) {
        return;
    }
    visited.insert(var_name.to_string());

    let Some(dependencies) = object_dependencies.get(var_name) else {
        return;
    };

    for dependency in dependencies {
        if output.insert(dependency.clone()) {
            expand_dependencies(dependency, object_dependencies, output, visited);
        }
    }
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

fn extract_append_store(line: &str) -> Option<(String, String, bool)> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    let assign_idx = trimmed.find('=')?;

    let lhs = extract_last_identifier(trimmed[..assign_idx].trim())?;
    let rhs = trimmed[assign_idx + 1..].trim();
    if !rhs.starts_with("append(") || !rhs.ends_with(')') {
        return None;
    }

    let inside = &rhs[7..rhs.len() - 1];
    let (_, value_expr) = split_first_top_level_comma(inside)?;
    let value_expr = value_expr.trim().to_string();
    let is_closure = value_expr.contains("func(");
    Some((lhs, value_expr, is_closure))
}

fn extract_index_assignment(line: &str) -> Option<(String, String)> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    if trimmed.contains("==") {
        return None;
    }

    let assign_idx = trimmed.find('=')?;
    if assign_idx == 0 {
        return None;
    }

    let left = trimmed[..assign_idx].trim();
    let bracket_idx = left.find('[')?;
    let container = extract_last_identifier(left[..bracket_idx].trim())?;
    let rhs = trimmed[assign_idx + 1..].trim().to_string();
    if rhs.is_empty() {
        return None;
    }

    Some((container, rhs))
}

fn extract_method_store(line: &str) -> Option<(String, String, bool)> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    let dot_idx = trimmed.find('.')?;
    let open_idx = trimmed.find('(')?;
    let close_idx = trimmed.rfind(')')?;
    if open_idx <= dot_idx || close_idx <= open_idx {
        return None;
    }

    let receiver = extract_last_identifier(trimmed[..dot_idx].trim())?;
    let method = trimmed[dot_idx + 1..open_idx].trim();
    if !matches!(method, "Store" | "Set" | "Add" | "Push" | "Insert") {
        return None;
    }

    let inside = trimmed[open_idx + 1..close_idx].trim();
    if inside.is_empty() {
        return None;
    }

    let value_expr = if matches!(method, "Store" | "Set" | "Insert") {
        if let Some((_, rhs)) = split_first_top_level_comma(inside) {
            rhs.trim().to_string()
        } else {
            inside.to_string()
        }
    } else {
        inside.to_string()
    };

    let is_closure = value_expr.contains("func(");
    Some((receiver, value_expr, is_closure))
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
                let left = text[..idx].to_string();
                let right = text[idx + 1..].to_string();
                return Some((left, right));
            }
            _ => {}
        }
    }

    None
}

fn extract_return_identifier(line: &str) -> Option<String> {
    let trimmed = strip_comment(line).trim_end_matches(';').trim();
    let value = trimmed.strip_prefix("return ")?.trim();
    if value.is_empty() {
        return None;
    }
    if value
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
    {
        return Some(value.to_string());
    }
    None
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
    function_name: &str,
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
            function: function_name.to_string(),
            code_snippet,
        },
        variable_name,
        reason,
        confidence,
        data_flow: vec![],
    });
}

fn extract_func_name(line: &str) -> Option<String> {
    if !line.contains("func ") {
        return None;
    }
    
    let trimmed = strip_comment(line);
    let func_idx = trimmed.find("func ")?;
    let mut after_func = &trimmed[func_idx + 5..];
    after_func = after_func.trim_start();

    // Skip method receivers: func (r *Receiver) Name(...)
    if after_func.starts_with('(') {
        let receiver_end = after_func.find(')')?;
        after_func = &after_func[receiver_end + 1..];
        after_func = after_func.trim_start();
    }

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
    let trimmed = strip_comment(line);
    if !trimmed.contains("make(chan") {
        return None;
    }
    
    // Try to extract variable name before := or =
    if let Some(assign_idx) = trimmed.find(":=").or_else(|| trimmed.find(" = ")) {
        let before = &trimmed[..assign_idx].trim();
        let parts: Vec<&str> = before.split_whitespace().collect();
        if let Some(last) = parts.last() {
            return Some(last.to_string());
        }
    }
    
    None
}

fn extract_channel_receive(line: &str) -> Option<String> {
    // Look for patterns like: <-channame
    let trimmed = strip_comment(line);
    if !trimmed.contains("<-") {
        return None;
    }
    
    if let Some(arrow_idx) = trimmed.find("<-") {
        let after = &trimmed[arrow_idx + 2..].trim();
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
    let trimmed = strip_comment(line).trim();
    if trimmed.contains("go ") && !trimmed.starts_with("//") {
        let reason = "Goroutine spawned".to_string();
        Some(StaticEscape {
            escape_type: classify_go_async_escape(Some(trimmed), &reason, "goroutine"),
            location: SourceLocation {
                file: source_file.to_string(),
                line: line_num,
                column: 0,
                function: function.to_string(),
                code_snippet: Some(trimmed.to_string()),
            },
            variable_name: "goroutine".to_string(),
            reason,
            confidence: ConfidenceLevel::High,
            data_flow: vec![],
        })
    } else {
        None
    }
}

fn classify_go_async_escape(line: Option<&str>, reason: &str, variable_name: &str) -> EscapeType {
    let combined = format!("{} {} {}", reason, variable_name, line.unwrap_or_default()).to_lowercase();

    if combined.contains("return") || combined.contains("returned") {
        EscapeType::ReturnEscape
    } else if combined.contains("global") || combined.contains("package-level") {
        EscapeType::GlobalEscape
    } else if combined.contains("go func") || combined.contains("closure") || combined.contains("capture") {
        EscapeType::ClosureEscape
    } else if combined.contains("go ") && !combined.contains("go func") {
        // Async invocation of another function generally forwards values across goroutine boundaries.
        EscapeType::ParameterEscape
    } else {
        // Channel handles and leaked goroutine state are treated as heap-backed escapes.
        EscapeType::HeapEscape
    }
}
