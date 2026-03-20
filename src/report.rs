use anyhow::Result;
use std::path::PathBuf;
use std::collections::{BTreeMap, HashSet};
use chrono::Local;
use uuid::Uuid;
use crate::protocol::{AnalyzeResponse, ExecutionResult, Vulnerability};

pub struct ReportGenerator {
    output_dir: PathBuf,
}

impl ReportGenerator {
    pub fn new(output_dir: PathBuf) -> Self {
        Self { output_dir }
    }

    pub async fn generate(&self, response: &AnalyzeResponse, target: &str) -> Result<()> {
        std::fs::create_dir_all(&self.output_dir)?;

        let timestamp = Local::now().format("%Y%m%d_%H%M%S");
        let uuid_str = Uuid::new_v4().to_string();
        let random_id = uuid_str.split('-').next().unwrap_or("xxxx");
        let language = response.language.trim();
        let language_dir = if language.is_empty() {
            self.output_dir.join("unknown")
        } else {
            self.output_dir.join(language.to_lowercase())
        };
        std::fs::create_dir_all(&language_dir)?;
        let session_dir = language_dir.join(format!("session_{}_{}", timestamp, random_id));
        std::fs::create_dir_all(&session_dir)?;

        // Generate summary report
        self.generate_summary(&session_dir, response, target).await?;

        // Generate CSV report
        self.generate_csv(&session_dir, response).await?;

        // Generate vulnerability report
        if !response.vulnerabilities.is_empty() {
            self.generate_vulnerability_report(&session_dir, response).await?;
        }

        println!("📁 Reports generated in: {}", session_dir.display());

        Ok(())
    }

    async fn generate_summary(&self, dir: &PathBuf, response: &AnalyzeResponse, target: &str) -> Result<()> {
        let path = dir.join("README.md");
        let summary = &response.summary;

        let static_section = if let Some(static_result) = &response.static_analysis {
            format!(
                r#"## Static Object Escape Analysis

| Category | Count |
|----------|-------|
| Total Escapes | {} |
| Return Escapes | {} |
| Parameter Escapes | {} |
| Global/Module Escapes | {} |
| Closure Escapes | {} |
| Heap Escapes | {} |
| High Confidence | {} |
| Medium Confidence | {} |
| Low Confidence | {} |

**Analysis Time:** {}ms

### Detected Escape Points

{}

"#,
                static_result.summary.total_escapes,
                static_result.summary.return_escapes,
                static_result.summary.parameter_escapes,
                static_result.summary.global_escapes,
                static_result.summary.closure_escapes,
                static_result.summary.heap_escapes,
                static_result.summary.high_confidence,
                static_result.summary.medium_confidence,
                static_result.summary.low_confidence,
                static_result.analysis_time_ms,
                self.format_static_escapes(&static_result.escapes)
            )
        } else {
            String::new()
        };

        let content = format!(
            r#"# Object Escape Analysis Report

**Target:** `{}`
**Language:** {}
**Analyzer Version:** {}
**Session ID:** {}
**Generated:** {}

## Overview

This report shows the results of static object escape analysis for the target function. Object escapes occur when local objects are passed to other functions, returned, stored in global scope, or captured in closures—places where they may outlive their intended scope.

{}

## Execution Verification

| Metric | Value |
|--------|-------|
| Executions | {} |
| Successes | {} ✓ |
| Crashes | {} ✗ |
| Crash Rate | {:.1}% |

## Vulnerabilities

{}

## Error Diagnostics

{}

## Execution Results

{}
"#,
            target,
            response.language,
            response.analyzer_version,
            response.session_id,
            Local::now().format("%Y-%m-%d %H:%M:%S"),
            static_section,
            summary.total_tests,
            summary.successes,
            summary.crashes,
            summary.crash_rate * 100.0,
            self.format_vulnerabilities(&response.vulnerabilities),
            self.format_error_diagnostics(response),
            self.format_results(response)
        );

        tokio::fs::write(path, content).await?;
        Ok(())
    }

    async fn generate_csv(&self, dir: &PathBuf, response: &AnalyzeResponse) -> Result<()> {
        let path = dir.join("results.csv");

        let mut csv = String::from("input,success,crashed,escape_detected,escape_summary,error,execution_time_ms\n");

        for result in &response.results {
            csv.push_str(&format!(
                "\"{}\",{},{},{},\"{}\",\"{}\",{}\n",
                result.input_data.replace('"', "\"\""),
                result.success,
                result.crashed,
                result.escape_detected,
                result.escape_details.summary().replace('"', "\"\""),
                result.error.replace('"', "\"\""),
                result.execution_time_ms
            ));
        }

        tokio::fs::write(path, csv).await?;
        Ok(())
    }

    async fn generate_vulnerability_report(&self, dir: &PathBuf, response: &AnalyzeResponse) -> Result<()> {
        if response.vulnerabilities.is_empty() {
            return Ok(());
        }
        let path = dir.join("vulnerabilities.md");

        let mut content = String::from("# Vulnerability Report\n\n");

        for (i, vuln) in response.vulnerabilities.iter().enumerate() {
            content.push_str(&format!(
                r#"## Vulnerability #{} - {}

**Type:** `{}`
**Severity:** {}
**Input:** `{}`

**Description:**
{}

**Escape Details:**
{}

---

"#,
                i + 1,
                vuln.vulnerability_type,
                vuln.vulnerability_type,
                vuln.severity.to_uppercase(),
                vuln.input,
                vuln.description,
                self.format_escape_details(&vuln.escape_details)
            ));
        }

        tokio::fs::write(path, content).await?;
        Ok(())
    }

    fn format_vulnerabilities(&self, vulnerabilities: &[Vulnerability]) -> String {
        if vulnerabilities.is_empty() {
            return "✅ **No vulnerabilities detected**".to_string();
        }

        let mut output = format!("⚠️ **{} vulnerabilities found:**\n\n", vulnerabilities.len());
        
        for (i, vuln) in vulnerabilities.iter().enumerate() {
            output.push_str(&format!(
                "{}. **[{}]** {} - Input: `{}`\n",
                i + 1,
                vuln.severity.to_uppercase(),
                vuln.vulnerability_type,
                vuln.input
            ));
        }

        output
    }

    fn format_results(&self, response: &AnalyzeResponse) -> String {
        let mut output = String::from("| Input | Status | Escape | Details | Error | Suggested Action |\n");
        output.push_str("|-------|--------|--------|----------|-------|------------------|\n");

        for result in &response.results {
            let status = if result.crashed {
                "❌ CRASH"
            } else if result.success {
                "✅ OK"
            } else {
                "⚠️ FAIL"
            };

            let escape = if result.escape_detected {
                "🚨 YES"
            } else {
                "✓ NO"
            };

            let error_summary = self.describe_error(result);
            let error_cell = if error_summary.short_message.is_empty() {
                "-".to_string()
            } else {
                self.escape_markdown_cell(&error_summary.short_message, 120)
            };

            let action_cell = if error_summary.hint.is_empty() {
                "-".to_string()
            } else {
                self.escape_markdown_cell(error_summary.hint, 120)
            };

            output.push_str(&format!(
                "| `{}` | {} | {} | {} | {} | {} |\n",
                self.escape_markdown_cell(&result.input_data, 60),
                status,
                escape,
                self.escape_markdown_cell(&result.escape_details.summary(), 80),
                error_cell,
                action_cell
            ));
        }

        output
    }

    fn format_error_diagnostics(&self, response: &AnalyzeResponse) -> String {
        let mut category_counts: BTreeMap<&'static str, usize> = BTreeMap::new();
        let mut sample_entries = String::new();
        let mut seen_samples: HashSet<String> = HashSet::new();

        let error_results: Vec<&ExecutionResult> = response
            .results
            .iter()
            .filter(|r| r.crashed || !r.error.trim().is_empty())
            .collect();

        if error_results.is_empty() {
            return "✅ No execution errors were detected in this run.".to_string();
        }

        for result in &error_results {
            let diagnosis = self.describe_error(result);
            *category_counts.entry(diagnosis.category).or_insert(0) += 1;

            let sample_key = format!("{}:{}", diagnosis.category, diagnosis.short_message);
            if seen_samples.insert(sample_key) && seen_samples.len() <= 5 {
                sample_entries.push_str(&format!(
                    "- **{}** for input `{}`: {}  \n  Suggested action: {}\n",
                    diagnosis.category,
                    self.escape_markdown_cell(&result.input_data, 50),
                    self.escape_markdown_cell(&diagnosis.short_message, 140),
                    diagnosis.hint
                ));
            }
        }

        let mut output = String::from("### Error Categories\n\n");
        output.push_str("| Category | Count |\n");
        output.push_str("|----------|-------|\n");
        for (category, count) in category_counts {
            output.push_str(&format!("| {} | {} |\n", category, count));
        }

        output.push_str("\n### Representative Errors\n\n");
        if sample_entries.is_empty() {
            output.push_str("- No representative errors captured.\n");
        } else {
            output.push_str(&sample_entries);
        }

        output
    }

    fn describe_error<'a>(&self, result: &'a ExecutionResult) -> ErrorDiagnosis<'a> {
        let raw = if result.error.trim().is_empty() {
            if result.crashed {
                "Execution failed without an error message"
            } else {
                ""
            }
        } else {
            result.error.trim()
        };

        let lower = raw.to_lowercase();

        let (category, hint) = if lower.contains("timeout") || lower.contains("timed out") || lower.contains("exceeded") {
            (
                "Timeout",
                "Increase timeout only after checking for blocked joins/awaits and non-terminating loops.",
            )
        } else if lower.contains("target resolution")
            || lower.contains("not found")
            || lower.contains("failed to load")
            || lower.contains("invalid target")
            || lower.contains("nosuchmethod")
            || lower.contains("module not found")
        {
            (
                "Target Resolution",
                "Verify target path/signature and confirm the function exists in the selected language module.",
            )
        } else if lower.contains("protocol/input")
            || lower.contains("json")
            || lower.contains("parse")
            || lower.contains("stdin")
            || lower.contains("protocol")
        {
            (
                "Protocol/Input",
                "Validate request format and ensure bridge stdin/stdout JSON protocol remains unchanged.",
            )
        } else if lower.contains("environment")
            || lower.contains("permission denied")
            || lower.contains("not available")
            || lower.contains("not found in path")
            || lower.contains("command not found")
            || lower.contains("missing tools")
        {
            (
                "Environment",
                "Check runtime/compiler dependencies and executable availability in PATH.",
            )
        } else if lower.contains("runtime crash")
            || result.crashed
            || lower.contains("panic")
            || lower.contains("exception")
            || lower.contains("traceback")
            || lower.contains("segmentation")
        {
            (
                "Runtime Crash",
                "Inspect stack trace and target function side effects; rerun in dynamic mode with verbose logging.",
            )
        } else {
            (
                "Unknown",
                "Review full bridge output and rerun with --verbose to capture additional diagnostics.",
            )
        };

        ErrorDiagnosis {
            category,
            short_message: self.first_line(raw),
            hint,
        }
    }

    fn first_line<'a>(&self, message: &'a str) -> String {
        message
            .lines()
            .find(|line| !line.trim().is_empty())
            .unwrap_or("")
            .trim()
            .to_string()
    }

    fn escape_markdown_cell(&self, value: &str, max_chars: usize) -> String {
        let normalized = value
            .replace('|', "\\|")
            .replace('\n', " ")
            .replace('\r', " ")
            .trim()
            .to_string();

        let length = normalized.chars().count();
        if length <= max_chars {
            return normalized;
        }

        let keep = max_chars.saturating_sub(3);
        let mut truncated = normalized.chars().take(keep).collect::<String>();
        truncated.push_str("...");
        truncated
    }

    fn format_escape_details(&self, details: &crate::protocol::EscapeDetails) -> String {
        if details.is_empty() {
            return "No object escapes detected".to_string();
        }

        let mut output = String::new();

        if !details.escaping_references.is_empty() {
            output.push_str("**Escaping References:**\n");
            for ref_obj in &details.escaping_references {
                output.push_str(&format!(
                    "- Variable `{}` ({}) escapes via {}\n",
                    ref_obj.variable_name, ref_obj.object_type, ref_obj.escaped_via
                ));
            }
        }

        if !details.escape_paths.is_empty() {
            output.push_str("\n**Escape Paths:**\n");
            for path in &details.escape_paths {
                output.push_str(&format!(
                    "- {} → {} ({})\n",
                    path.source, path.destination, path.escape_type
                ));
            }
        }

        output
    }

    fn format_static_escapes(&self, escapes: &[crate::protocol::StaticEscape]) -> String {
        if escapes.is_empty() {
            return "✅ No escapes detected by static analysis".to_string();
        }

        let mut output = String::from("| Type | Variable | Location | Reason | Confidence |\n");
        output.push_str("|------|----------|----------|--------|------------|\n");

        for escape in escapes {
            let escape_type = match escape.escape_type {
                crate::protocol::EscapeType::ReturnEscape => "Return",
                crate::protocol::EscapeType::ParameterEscape => "Parameter",
                crate::protocol::EscapeType::GlobalEscape => "Global",
                crate::protocol::EscapeType::ClosureEscape => "Closure",
                crate::protocol::EscapeType::HeapEscape => "Heap",
                crate::protocol::EscapeType::UnknownEscape => "Unknown",
            };

            let confidence = match escape.confidence {
                crate::protocol::ConfidenceLevel::High => "🔴 High",
                crate::protocol::ConfidenceLevel::Medium => "🟡 Medium",
                crate::protocol::ConfidenceLevel::Low => "🟢 Low",
            };

            output.push_str(&format!(
                "| {} | `{}` | {}:{} | {} | {} |\n",
                escape_type,
                escape.variable_name,
                escape.location.file,
                escape.location.line,
                self.escape_markdown_cell(&escape.reason, 60),
                confidence
            ));
        }

        output
    }
}

struct ErrorDiagnosis<'a> {
    category: &'static str,
    short_message: String,
    hint: &'a str,
}
