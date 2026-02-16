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
#[command(about = "Graphene HA - Multi-language concurrency escape detection", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Debug, Clone, Copy, ValueEnum)]
enum CliAnalysisMode {
    /// Dynamic runtime analysis (default)
    Dynamic,
    /// Static compile-time analysis
    Static,
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
    /// Analyze a function for concurrency escapes
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

        /// Analysis mode: dynamic (runtime), static (compile-time), or both
        #[arg(short = 'm', long, default_value = "dynamic")]
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
    },

    /// List available analyzers
    List {
        /// Show detailed analyzer capabilities
        #[arg(short, long)]
        detailed: bool,
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
        } => {
            orchestrator::run_all_tests(test_dir, generate, output_dir, language).await?;
        }
        Commands::List { detailed } => {
            orchestrator::list_analyzers(detailed).await?;
        }
    }

    Ok(())
}
