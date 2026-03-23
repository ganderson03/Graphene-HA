mod orchestrator;
mod protocol;
mod analyzer;
mod report;
mod static_analyzer;

use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;
use anyhow::Result;
use crate::protocol::AnalysisMode;

#[derive(Parser)]
#[command(name = "graphene-ha")]
#[command(about = "Graphene HA - Static object escape analysis for multi-language codebases", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum CliAnalysisMode {
    /// Static compile-time analysis (recommended for object escape analysis)
    Static,
    /// Dynamic runtime analysis
    Dynamic,
    /// Both static and dynamic analysis
    Both,
}

impl From<CliAnalysisMode> for AnalysisMode {
    fn from(mode: CliAnalysisMode) -> Self {
        match mode {
            CliAnalysisMode::Dynamic => AnalysisMode::Dynamic,
            CliAnalysisMode::Static => AnalysisMode::Static,
            CliAnalysisMode::Both => AnalysisMode::Both,
        }
    }
}

#[derive(Subcommand)]
enum Commands {
    /// Analyze a function for object escapes
    Analyze {
        /// Target function in format: module:function or file.ext:function
        #[arg(short, long)]
        target: String,

        /// Input data for the function
        #[arg(short, long)]
        input: Vec<String>,

        /// Number of times to repeat each input
        #[arg(short, long, default_value = "3")]
        repeat: usize,

        /// Timeout per execution in seconds
        #[arg(long, default_value = "5.0")]
        timeout: f64,

        /// Output directory for reports
        #[arg(short, long, default_value = "logs")]
        output_dir: PathBuf,

        /// Language (auto-detected if not specified)
        #[arg(short, long)]
        language: Option<String>,

        /// Analysis mode: dynamic, static, or both. A runtime self-check runs before analysis to report missing analyzers.
        #[arg(short = 'm', long, default_value = "both")]
        analysis_mode: CliAnalysisMode,

        /// Enable verbose logging
        #[arg(short, long)]
        verbose: bool,
    },

    /// Run all test suites across all languages
    RunAll {
        /// Root test directory
        #[arg(short, long, default_value = "tests")]
        test_dir: PathBuf,

        /// Number of inputs to generate per test
        #[arg(short, long, default_value = "10")]
        generate: usize,

        /// Output directory for reports
        #[arg(short, long, default_value = "logs")]
        output_dir: PathBuf,

        /// Filter by language (python, java, javascript, go, rust)
        #[arg(long)]
        language: Option<String>,

        /// Analysis mode: dynamic, static, or both. Default is both.
        #[arg(short = 'm', long, default_value = "both")]
        analysis_mode: CliAnalysisMode,
    },

    /// List available analyzers
    List {
        /// Show detailed analyzer capabilities
        #[arg(short, long)]
        detailed: bool,
    },

    /// Clear log output directories
    #[command(name = "clear", alias = "clear-logs")]
    Clear {
        /// Output directory for reports
        #[arg(short, long, default_value = "logs")]
        output_dir: PathBuf,

        /// Archive results into a single CSV file before clearing
        #[arg(long, value_name = "PATH")]
        archive_csv: Option<PathBuf>,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Analyze {
            target,
            input,
            repeat,
            timeout,
            output_dir,
            language,
            analysis_mode,
            verbose,
        } => {
            orchestrator::analyze_target(
                &target,
                input,
                repeat,
                timeout,
                output_dir,
                language,
                analysis_mode.into(),
                verbose,
            )
            .await?;
        }
        Commands::RunAll {
            test_dir,
            generate,
            output_dir,
            language,
            analysis_mode,
        } => {
            orchestrator::run_all_tests(
                test_dir,
                generate,
                output_dir,
                language,
                analysis_mode.into(),
            )
            .await?;
        }
        Commands::List { detailed } => {
            orchestrator::list_analyzers(detailed).await?;
        }
        Commands::Clear {
            output_dir,
            archive_csv,
        } => {
            orchestrator::clear_logs(output_dir, archive_csv)?;
        }
    }

    Ok(())
}
