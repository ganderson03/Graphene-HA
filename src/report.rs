use anyhow::Result;
use std::path::PathBuf;
use chrono::Local;
use crate::protocol::{AnalyzeResponse, Vulnerability, AnalysisMode};

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
        let session_dir = self.output_dir.join(format!("session_{}", timestamp));
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

        let content = format!(
            r#"# Escape Analysis Report

**Target:** `{}`
**Language:** {}
**Analyzer Version:** {}
**Session ID:** {}
**Generated:** {}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {} |
| Successes | {} ✓ |
| Crashes | {} ✗ |
| Timeouts | {} ⏱ |
| Escapes Detected | {} 🚨 |
| Genuine Escapes | {} |
| Crash Rate | {:.1}% |

## Vulnerabilities

{}

## Test Results

{}
"#,
            target,
            response.language,
            response.analyzer_version,
            response.session_id,
            Local::now().format("%Y-%m-%d %H:%M:%S"),
            summary.total_tests,
            summary.successes,
            summary.crashes,
            summary.timeouts,
            summary.escapes,
            summary.genuine_escapes,
            summary.crash_rate * 100.0,
            self.format_vulnerabilities(&response.vulnerabilities),
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
        let mut output = String::from("| Input | Status | Escape | Details |\n");
        output.push_str("|-------|--------|--------|----------|\n");

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

            output.push_str(&format!(
                "| `{}` | {} | {} | {} |\n",
                result.input_data,
                status,
                escape,
                result.escape_details.summary()
            ));
        }

        output
    }

    fn format_escape_details(&self, details: &crate::protocol::EscapeDetails) -> String {
        let mut output = String::new();

        if !details.threads.is_empty() {
            output.push_str("**Threads:**\n");
            for thread in &details.threads {
                output.push_str(&format!(
                    "- {} ({}): {} {}\n",
                    thread.name,
                    thread.thread_id,
                    thread.state,
                    if thread.is_daemon { "[daemon]" } else { "[non-daemon]" }
                ));
            }
        }

        if !details.processes.is_empty() {
            output.push_str("\n**Processes:**\n");
            for proc in &details.processes {
                output.push_str(&format!("- PID {}: {}\n", proc.pid, proc.name));
            }
        }

        if !details.async_tasks.is_empty() {
            output.push_str("\n**Async Tasks:**\n");
            for task in &details.async_tasks {
                output.push_str(&format!("- {}: {}\n", task.task_type, task.state));
            }
        }

        if !details.goroutines.is_empty() {
            output.push_str("\n**Goroutines:**\n");
            for gr in &details.goroutines {
                output.push_str(&format!("- #{}: {} ({})\n", gr.goroutine_id, gr.function, gr.state));
            }
        }

        if output.is_empty() {
            output.push_str("No escape details available");
        }

        output
    }
}
