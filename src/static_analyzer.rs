/// Static escape analysis module
/// Performs compile-time analysis to detect escaping variables and concurrency patterns

use crate::protocol::StaticAnalysisResult;
use anyhow::Result;

/// Trait for language-specific static analyzers
pub trait StaticEscapeAnalyzer {
    /// Analyze a target function or file for escapes
    fn analyze(&self, target: &str, source_file: &str) -> Result<StaticAnalysisResult>;
    
    /// Get the language this analyzer supports
    fn language(&self) -> &str;
    
    /// Check if analyzer is available (required tools/compilers installed)
    fn is_available(&self) -> bool;
}

/// Factory for creating static analyzers
pub struct StaticAnalyzerFactory;

impl StaticAnalyzerFactory {
    pub fn create(language: &str) -> Option<Box<dyn StaticEscapeAnalyzer>> {
        match language.to_lowercase().as_str() {
            "python" => Some(Box::new(python::PythonStaticAnalyzer::new())),
            "java" => Some(Box::new(java::JavaStaticAnalyzer::new())),
            "javascript" | "nodejs" => Some(Box::new(nodejs::NodeJsStaticAnalyzer::new())),
            "go" => Some(Box::new(go::GoStaticAnalyzer::new())),
            "rust" => Some(Box::new(rust::RustStaticAnalyzer::new())),
            _ => None,
        }
    }
}

pub mod python;
pub mod java;
pub mod nodejs;
pub mod go;
pub mod rust;
