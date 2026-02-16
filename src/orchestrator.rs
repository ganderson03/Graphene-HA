use anyhow::{Result, Context};
use std::path::{Path, PathBuf};
use uuid::Uuid;
use crate::analyzer::AnalyzerRegistry;
use crate::protocol::{AnalyzeRequest, AnalyzeResponse, AnalysisMode, ExecutionSummary};
use crate::report::ReportGenerator;
use crate::static_analyzer::StaticAnalyzerFactory;
use std::collections::{HashMap, HashSet};
use std::fs;
use tracing::{info, warn, error};

pub async fn analyze_target(
    target: &str,
    inputs: Vec<String>,
    repeat: usize,
    timeout: f64,
    output_dir: PathBuf,
    language: Option<String>,
    analysis_mode: AnalysisMode,
    verbose: bool,
) -> Result<()> {
    init_logging(verbose);

    info!("Initializing analyzers...");
    info!("Analysis mode: {:?}", analysis_mode);
    
    let mut response: Option<AnalyzeResponse> = None;
    
    // Static analysis
    if analysis_mode == AnalysisMode::Static || analysis_mode == AnalysisMode::Both {
        info!("Running static escape analysis...");
        response = Some(run_static_analysis(target, language.as_deref(), analysis_mode).await?);
    }
    
    // Dynamic analysis
    if analysis_mode == AnalysisMode::Dynamic || analysis_mode == AnalysisMode::Both {
        info!("Running dynamic escape analysis...");
        let dynamic_response = run_dynamic_analysis(
            target,
            inputs,
            repeat,
            timeout,
            language.as_deref(),
            analysis_mode,
        ).await?;
        
        if let Some(ref mut resp) = response {
            // Merge static results with dynamic results
            resp.results = dynamic_response.results;
            resp.vulnerabilities.extend(dynamic_response.vulnerabilities);
            resp.summary = dynamic_response.summary;
        } else {
            response = Some(dynamic_response);
        }
    }
    
    let response = response.ok_or_else(|| anyhow::anyhow!("No analysis was performed"))?;

    // Generate report
    info!("Generating report...");
    let report_gen = ReportGenerator::new(output_dir);
    report_gen.generate(&response, target).await?;

    // Print summary
    print_summary(&response);

    Ok(())
}

async fn run_static_analysis(
    target: &str,
    language: Option<&str>,
    analysis_mode: AnalysisMode,
) -> Result<AnalyzeResponse> {
    // Determine language
    let lang = if let Some(l) = language {
        l.to_string()
    } else {
        detect_language_from_target(target)?
    };
    
    info!("Detected language: {}", lang);
    
    // Create static analyzer
    let static_analyzer = StaticAnalyzerFactory::create(&lang)
        .ok_or_else(|| anyhow::anyhow!("No static analyzer available for language: {}", lang))?;

    info!("Using static analyzer: {}", static_analyzer.language());
    
    if !static_analyzer.is_available() {
        anyhow::bail!("Static analyzer for {} is not available (missing tools)", lang);
    }
    
    // Resolve source file from target
    let source_file = resolve_source_file(target)?;
    
    info!("Analyzing source file: {}", source_file);
    let static_result = static_analyzer.analyze(target, &source_file)?;
    
    Ok(AnalyzeResponse {
        session_id: Uuid::new_v4().to_string(),
        language: lang,
        analyzer_version: "1.0.0-static".to_string(),
        analysis_mode,
        results: vec![],
        vulnerabilities: vec![],
        summary: ExecutionSummary {
            total_tests: 0,
            successes: 0,
            crashes: 0,
            timeouts: 0,
            escapes: 0,
            genuine_escapes: 0,
            crash_rate: 0.0,
        },
        static_analysis: Some(static_result),
    })
}

async fn run_dynamic_analysis(
    target: &str,
    inputs: Vec<String>,
    repeat: usize,
    timeout: f64,
    language: Option<&str>,
    analysis_mode: AnalysisMode,
) -> Result<AnalyzeResponse> {
    let registry = AnalyzerRegistry::initialize_all().await?;

    info!("Finding analyzer for target: {}", target);
    let analyzer = registry
        .find_analyzer(target, language)
        .ok_or_else(|| anyhow::anyhow!("No analyzer found for target: {}", target))?;

    info!("Using {} analyzer", analyzer.language());

    // Health check
    match analyzer.health_check().await {
        Ok(health) => info!("Analyzer healthy: {}", health.analyzer_info.name),
        Err(e) => {
            warn!("Analyzer health check failed: {}", e);
        }
    }

    // Create request
    let session_id = Uuid::new_v4().to_string();
    let request = AnalyzeRequest {
        session_id: session_id.clone(),
        target: target.to_string(),
        inputs: inputs.clone(),
        repeat,
        timeout_seconds: timeout,
        options: HashMap::new(),
        analysis_mode,
    };

    info!("Running analysis with {} inputs (repeat {}x)...", inputs.len(), repeat);
    let response = analyzer.analyze(request).await?;
    
    Ok(response)
}

fn detect_language_from_target(target: &str) -> Result<String> {
    if target.ends_with(".py") || target.contains("python") {
        Ok("python".to_string())
    } else if target.ends_with(".java") {
        Ok("java".to_string())
    } else if target.ends_with(".js") || target.ends_with(".mjs") {
        Ok("javascript".to_string())
    } else if target.ends_with(".go") {
        Ok("go".to_string())
    } else if target.ends_with(".rs") {
        Ok("rust".to_string())
    } else {
        anyhow::bail!("Unable to detect language from target: {}", target)
    }
}

fn resolve_source_file(target: &str) -> Result<String> {
    // Handle different target formats:
    // - path/to/file.py:function_name
    // - module.submodule:function_name
    
    if target.contains(':') {
        let parts: Vec<&str> = target.split(':').collect();
        let file_or_module = parts[0];
        
        // Check if it's a file path
        if file_or_module.contains('/') || file_or_module.contains('\\') || file_or_module.ends_with(".py") {
            return Ok(file_or_module.to_string());
        }
        
        // It's a module path, convert to file path
        let file_path = file_or_module.replace('.', "/") + ".py";
        if PathBuf::from(&file_path).exists() {
            return Ok(file_path);
        }
        
        // Try in tests directory
        let test_path = format!("tests/{}", file_path);
        if PathBuf::from(&test_path).exists() {
            return Ok(test_path);
        }
        
        // Last resort: assume it's the module path as-is
        Ok(file_path)
    } else {
        Ok(target.to_string())
    }
}

pub async fn run_all_tests(
    test_dir: PathBuf,
    generate: usize,
    output_dir: PathBuf,
    language_filter: Option<String>,
) -> Result<()> {
    init_logging(true);

    info!("Running all tests from: {:?}", test_dir);
    
    let registry = AnalyzerRegistry::initialize_all().await?;
    let analyzers = registry.list_analyzers();
    let inputs = generate_inputs(generate);
    let repeat = 1;
    let timeout = 5.0;
    let normalized_filter = language_filter
        .as_deref()
        .map(normalize_language_filter);

    for analyzer in analyzers {
        if let Some(filter) = normalized_filter.as_deref() {
            if analyzer.language() != filter {
                continue;
            }
        }

        if let Err(e) = analyzer.health_check().await {
            warn!("Skipping {} analyzer (health check failed): {}", analyzer.language(), e);
            continue;
        }

        info!("Discovering tests for {} analyzer", analyzer.language());
        let targets = discover_targets_for_language(analyzer.language(), &test_dir)?;
        if targets.is_empty() {
            warn!("No targets found for language: {}", analyzer.language());
            continue;
        }

        for target in targets {
            info!("Analyzing target: {}", target);
            let session_id = Uuid::new_v4().to_string();
            let request = AnalyzeRequest {
                session_id: session_id.clone(),
                target: target.clone(),
                inputs: inputs.clone(),
                repeat,
                timeout_seconds: timeout,
                options: HashMap::new(),
                analysis_mode: AnalysisMode::Dynamic,
            };

            match analyzer.analyze(request).await {
                Ok(response) => {
                    let report_gen = ReportGenerator::new(output_dir.clone());
                    report_gen.generate(&response, &target).await?;
                }
                Err(e) => {
                    warn!("Analysis failed for {}: {}", target, e);
                }
            }
        }
    }

    Ok(())
}

pub async fn list_analyzers(detailed: bool) -> Result<()> {
    init_logging(false);

    let registry = AnalyzerRegistry::initialize_all().await?;
    let analyzers = registry.list_analyzers();

    println!("\n╔════════════════════════════════════════════╗");
    println!("║       Available Escape Analyzers          ║");
    println!("╚════════════════════════════════════════════╝\n");

    for analyzer in analyzers {
        match analyzer.info().await {
            Ok(info) => {
                println!("🔹 {} ({})", info.name, info.language);
                println!("   Version: {}", info.version);
                println!("   Executable: {}", info.executable_path);
                
                if detailed {
                    println!("   Supported Features:");
                    for feature in info.supported_features {
                        println!("     • {}", feature);
                    }
                }
                println!();
            }
            Err(e) => {
                error!("Failed to get info for analyzer: {}", e);
            }
        }
    }

    Ok(())
}

fn print_summary(response: &AnalyzeResponse) {
    println!("\n╔════════════════════════════════════════════╗");
    println!("║           Analysis Summary                 ║");
    println!("╚════════════════════════════════════════════╝");
    println!("\nLanguage: {}", response.language);
    println!("Analysis Mode: {:?}", response.analysis_mode);
    
    // Static analysis summary
    if let Some(ref static_result) = response.static_analysis {
        println!("\n--- Static Analysis Results ---");
        println!("Target: {}", static_result.target);
        println!("Source File: {}", static_result.source_file);
        println!("Analysis Time: {}ms", static_result.analysis_time_ms);
        
        let summary = &static_result.summary;
        println!("\nEscape Summary:");
        println!("  Total Escapes: {}", summary.total_escapes);
        if summary.concurrency_escapes > 0 {
            println!("  🚨 Concurrency Escapes: {}", summary.concurrency_escapes);
        }
        if summary.return_escapes > 0 {
            println!("  ↩  Return Escapes: {}", summary.return_escapes);
        }
        if summary.parameter_escapes > 0 {
            println!("  📤 Parameter Escapes: {}", summary.parameter_escapes);
        }
        if summary.global_escapes > 0 {
            println!("  🌍 Global Escapes: {}", summary.global_escapes);
        }
        if summary.closure_escapes > 0 {
            println!("  λ  Closure Escapes: {}", summary.closure_escapes);
        }
        if summary.heap_escapes > 0 {
            println!("  💾 Heap Escapes: {}", summary.heap_escapes);
        }
        
        println!("\nConfidence Breakdown:");
        println!("  High: {}", summary.high_confidence);
        println!("  Medium: {}", summary.medium_confidence);
        println!("  Low: {}", summary.low_confidence);
        
        if !static_result.warnings.is_empty() {
            println!("\n⚠️  Warnings:");
            for warning in &static_result.warnings {
                println!("  • {}", warning);
            }
        }
    }
    
    // Dynamic analysis summary
    if response.analysis_mode == AnalysisMode::Dynamic || response.analysis_mode == AnalysisMode::Both {
        let summary = &response.summary;
        println!("\n--- Dynamic Analysis Results ---");
        println!("Total Tests: {}", summary.total_tests);
        println!("Successes: {} ✓", summary.successes);
        println!("Crashes: {} ✗", summary.crashes);
        println!("Timeouts: {} ⏱", summary.timeouts);
        println!("Escapes Detected: {} 🚨", summary.escapes);
        println!("Genuine Escapes: {}", summary.genuine_escapes);
        println!("Crash Rate: {:.1}%", summary.crash_rate * 100.0);
        
        if !response.vulnerabilities.is_empty() {
            println!("\n⚠️  VULNERABILITIES FOUND:");
            for vuln in &response.vulnerabilities {
                println!("   • [{}] {} - {}", vuln.severity.to_uppercase(), vuln.vulnerability_type, vuln.description);
            }
        } else {
            println!("\n✅ No runtime vulnerabilities detected");
        }
    }
    
    println!();
}

fn init_logging(verbose: bool) {
    use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
    
    let filter = if verbose {
        "graphene_ha=debug"
    } else {
        "graphene_ha=info"
    };
    
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(filter))
        .with(tracing_subscriber::fmt::layer())
        .init();
}

fn normalize_language_filter(filter: &str) -> String {
    match filter {
        "js" | "node" | "nodejs" | "javascript" => "javascript",
        "py" | "python" => "python",
        "go" => "go",
        "java" => "java",
        "rust" => "rust",
        other => other,
    }
    .to_string()
}

fn generate_inputs(count: usize) -> Vec<String> {
    let mut inputs = vec![
        "".to_string(),
        "0".to_string(),
        "-1".to_string(),
        "1".to_string(),
        "true".to_string(),
        "false".to_string(),
        "null".to_string(),
        "undefined".to_string(),
        "hello".to_string(),
        "\\x00".to_string(),
        "\\n".to_string(),
        "\\t".to_string(),
        "'".to_string(),
        "\"".to_string(),
        "()".to_string(),
        "[]".to_string(),
        "{}".to_string(),
        "../".to_string(),
        "..\\".to_string(),
        "${HOME}".to_string(),
        "$(whoami)".to_string(),
        "{{7*7}}".to_string(),
        "%s".to_string(),
        "error".to_string(),
        "exception".to_string(),
        "async".to_string(),
        "await".to_string(),
        "timeout".to_string(),
        "deadlock".to_string(),
        "race".to_string(),
        "concurrent".to_string(),
        "<script>alert(1)</script>".to_string(),
        "'; DROP TABLE; --".to_string(),
        "../../../etc/passwd".to_string(),
        "\\x1b[31m".to_string(),
        "\\u0000".to_string(),
    ];

    inputs.push("A".repeat(1024));
    inputs.push("1".repeat(100));
    inputs.push("test".repeat(50));
    inputs.push(" ".repeat(1000));
    inputs.push("\\n".repeat(100));

    if count == 0 {
        return vec![String::new()];
    }

    if inputs.len() >= count {
        return inputs.into_iter().take(count).collect();
    }

    while inputs.len() < count {
        inputs.push(format!("input_{}", inputs.len() + 1));
    }

    inputs
}

fn discover_targets_for_language(language: &str, test_dir: &Path) -> Result<Vec<String>> {
    match language {
        "python" => discover_python_targets(test_dir),
        "javascript" => discover_nodejs_targets(test_dir),
        "java" => discover_java_targets(test_dir),
        "rust" => discover_rust_targets(test_dir),
        "go" => {
            warn!("Go run-all is not supported (plugin loading not implemented)");
            Ok(Vec::new())
        }
        _ => Ok(Vec::new()),
    }
}

fn resolve_language_dir(test_dir: &Path, language: &str, ext: &str) -> Option<PathBuf> {
    let candidate = test_dir.join(language);
    if candidate.is_dir() {
        return Some(candidate);
    }

    if test_dir.is_dir() && has_extension(test_dir, ext) {
        return Some(test_dir.to_path_buf());
    }

    None
}

fn has_extension(dir: &Path, ext: &str) -> bool {
    collect_files_recursive(dir, ext)
        .map(|files| !files.is_empty())
        .unwrap_or(false)
}

fn collect_files_recursive(dir: &Path, ext: &str) -> Result<Vec<PathBuf>> {
    let mut files = Vec::new();
    if !dir.exists() {
        return Ok(files);
    }

    for entry in fs::read_dir(dir).with_context(|| format!("Failed to read dir: {}", dir.display()))? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            files.extend(collect_files_recursive(&path, ext)?);
        } else if path
            .extension()
            .and_then(|value| value.to_str())
            .map(|value| value.eq_ignore_ascii_case(ext))
            .unwrap_or(false)
        {
            files.push(path);
        }
    }

    Ok(files)
}

fn to_relative_path(path: &Path) -> String {
    let cwd = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    path.strip_prefix(cwd)
        .unwrap_or(path)
        .to_string_lossy()
        .to_string()
}

fn discover_python_targets(test_dir: &Path) -> Result<Vec<String>> {
    let dir = match resolve_language_dir(test_dir, "python", "py") {
        Some(path) => path,
        None => return Ok(Vec::new()),
    };

    let mut targets = Vec::new();
    let files = collect_files_recursive(&dir, "py")?;
    for file in files {
        if file.file_name().and_then(|name| name.to_str()) == Some("__init__.py") {
            continue;
        }
        let content = fs::read_to_string(&file)
            .with_context(|| format!("Failed to read file: {}", file.display()))?;
        for func in extract_python_functions(&content) {
            targets.push(format!("{}:{}", to_relative_path(&file), func));
        }
    }

    Ok(targets)
}

fn extract_python_functions(content: &str) -> Vec<String> {
    let mut functions = Vec::new();
    for line in content.lines() {
        let trimmed = line.trim_start();
        if trimmed.len() != line.len() {
            continue;
        }

        let name = if trimmed.starts_with("def ") {
            trimmed.strip_prefix("def ")
        } else if trimmed.starts_with("async def ") {
            trimmed.strip_prefix("async def ")
        } else {
            None
        };

        if let Some(name) = name {
            if let Some(end) = name.find('(') {
                let func = name[..end].trim();
                if !func.is_empty() && !func.starts_with('_') {
                    functions.push(func.to_string());
                }
            }
        }
    }
    functions
}

fn discover_nodejs_targets(test_dir: &Path) -> Result<Vec<String>> {
    let dir = match resolve_language_dir(test_dir, "nodejs", "js") {
        Some(path) => path,
        None => return Ok(Vec::new()),
    };

    let mut targets = Vec::new();
    let files = collect_files_recursive(&dir, "js")?;
    for file in files {
        let content = fs::read_to_string(&file)
            .with_context(|| format!("Failed to read file: {}", file.display()))?;
        let exports = extract_nodejs_exports(&content);
        for export in exports {
            targets.push(format!("{}:{}", to_relative_path(&file), export));
        }
    }

    Ok(targets)
}

fn extract_nodejs_exports(content: &str) -> Vec<String> {
    let mut exports = HashSet::new();
    let mut in_block = false;

    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("//") || trimmed.starts_with("/*") || trimmed.starts_with("*") {
            continue;
        }

        if trimmed.starts_with("module.exports") && trimmed.contains('{') {
            in_block = true;
        }

        if in_block {
            let mut parse_line = trimmed;
            if let Some(after_brace) = trimmed.split_once('{') {
                parse_line = after_brace.1;
            }

            if let Some(before_brace) = parse_line.split_once('}') {
                parse_line = before_brace.0;
                in_block = false;
            }

            for part in parse_line.split(',') {
                let item = part.trim().trim_end_matches(';');
                if item.is_empty() {
                    continue;
                }
                let name = item.split(':').next().unwrap_or("").trim();
                if is_valid_identifier(name) {
                    exports.insert(name.to_string());
                }
            }
        }

        if let Some(name) = trimmed.strip_prefix("exports.") {
            let func = name.split('=').next().unwrap_or("").trim();
            if is_valid_identifier(func) {
                exports.insert(func.to_string());
            }
        }

        if let Some(name) = trimmed.strip_prefix("module.exports.") {
            let func = name.split('=').next().unwrap_or("").trim();
            if is_valid_identifier(func) {
                exports.insert(func.to_string());
            }
        }
    }

    exports.into_iter().collect()
}

fn discover_java_targets(test_dir: &Path) -> Result<Vec<String>> {
    let dir = match resolve_language_dir(test_dir, "java", "java") {
        Some(path) => path,
        None => return Ok(Vec::new()),
    };

    let jar_path = find_java_jar(&dir);
    if jar_path.is_none() {
        warn!("Java tests skipped (missing built jar in {}), run mvn package", dir.display());
        return Ok(Vec::new());
    }

    let jar_path = jar_path.unwrap();
    let mut targets = Vec::new();
    let files = collect_files_recursive(&dir, "java")?;
    for file in files {
        let content = fs::read_to_string(&file)
            .with_context(|| format!("Failed to read file: {}", file.display()))?;
        if let Some((class_name, methods)) = extract_java_class_and_methods(&content) {
            for method in methods {
                targets.push(format!("{}:{}:{}", to_relative_path(&jar_path), class_name, method));
            }
        }
    }

    Ok(targets)
}

fn find_java_jar(dir: &Path) -> Option<PathBuf> {
    let target_dir = dir.join("target");
    if !target_dir.is_dir() {
        return None;
    }

    let entries = fs::read_dir(target_dir).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) == Some("jar") {
            let name = path.file_name().and_then(|value| value.to_str()).unwrap_or("");
            if !name.ends_with("-sources.jar") && !name.ends_with("-javadoc.jar") {
                return Some(path);
            }
        }
    }

    None
}

fn extract_java_class_and_methods(content: &str) -> Option<(String, Vec<String>)> {
    let mut package_name = None;
    let mut class_name = None;
    let mut methods = Vec::new();

    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("package ") {
            let name = trimmed.trim_start_matches("package ").trim_end_matches(';').trim();
            if !name.is_empty() {
                package_name = Some(name.to_string());
            }
        }

        if class_name.is_none() && trimmed.contains(" class ") {
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            if let Some(idx) = parts.iter().position(|part| *part == "class") {
                if let Some(name) = parts.get(idx + 1) {
                    class_name = Some(name.trim().trim_end_matches('{').to_string());
                }
            }
        }

        if trimmed.contains(" static ") && trimmed.contains('(') {
            let before_paren = trimmed.split('(').next().unwrap_or("");
            let tokens: Vec<&str> = before_paren.split_whitespace().collect();
            if let Some(name) = tokens.last() {
                if let Some(ref class_name) = class_name {
                    if name == class_name {
                        continue;
                    }
                }
                if is_valid_identifier(name) {
                    methods.push(name.to_string());
                }
            }
        }
    }

    let class_name = class_name?;
    let fqcn = if let Some(package) = package_name {
        format!("{}.{}", package, class_name)
    } else {
        class_name
    };

    Some((fqcn, methods))
}

fn discover_rust_targets(test_dir: &Path) -> Result<Vec<String>> {
    let dir = match resolve_language_dir(test_dir, "rust", "rs") {
        Some(path) => path,
        None => return Ok(Vec::new()),
    };

    let crate_name = read_rust_crate_name(&dir).unwrap_or_else(|| "tests_rust".to_string());
    let files = collect_files_recursive(&dir, "rs")?;
    let mut targets = Vec::new();

    for file in files {
        let filename = file.file_name().and_then(|value| value.to_str()).unwrap_or("");
        if filename == "lib.rs" || filename.starts_with("run_") {
            continue;
        }

        let module = file
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or("");
        if module.is_empty() {
            continue;
        }

        let content = fs::read_to_string(&file)
            .with_context(|| format!("Failed to read file: {}", file.display()))?;
        for func in extract_rust_functions(&content) {
            targets.push(format!("{}::{}::{}", crate_name, module, func));
        }
    }

    Ok(targets)
}

fn read_rust_crate_name(dir: &Path) -> Option<String> {
    let cargo_toml = dir.join("Cargo.toml");
    let content = fs::read_to_string(cargo_toml).ok()?;
    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("name = ") {
            let value = trimmed.trim_start_matches("name = ").trim();
            let value = value.trim_matches('"');
            return Some(value.replace('-', "_"));
        }
    }

    None
}

fn extract_rust_functions(content: &str) -> Vec<String> {
    let mut functions = Vec::new();
    for line in content.lines() {
        let trimmed = line.trim_start();
        if trimmed.len() != line.len() {
            continue;
        }

        let name = if trimmed.starts_with("pub async fn ") {
            trimmed.strip_prefix("pub async fn ")
        } else if trimmed.starts_with("pub fn ") {
            trimmed.strip_prefix("pub fn ")
        } else {
            None
        };

        if let Some(name) = name {
            if let Some(end) = name.find('(') {
                let func = name[..end].trim();
                if is_valid_identifier(func) {
                    functions.push(func.to_string());
                }
            }
        }
    }

    functions
}

fn is_valid_identifier(name: &str) -> bool {
    let mut chars = name.chars();
    match chars.next() {
        Some(first) if first == '_' || first.is_ascii_alphabetic() => {}
        _ => return false,
    }

    chars.all(|c| c == '_' || c.is_ascii_alphanumeric())
}
