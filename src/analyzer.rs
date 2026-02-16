use async_trait::async_trait;
use anyhow::Result;
use crate::protocol::{AnalyzeRequest, AnalyzeResponse, AnalyzerInfo, HealthCheckResponse};

/// Trait for language-specific analyzers
#[async_trait]
pub trait Analyzer: Send + Sync {
    /// Get analyzer information
    async fn info(&self) -> Result<AnalyzerInfo>;

    /// Check if analyzer is available and working
    async fn health_check(&self) -> Result<HealthCheckResponse>;

    /// Analyze a target function
    async fn analyze(&self, request: AnalyzeRequest) -> Result<AnalyzeResponse>;

    /// Get the language this analyzer supports
    fn language(&self) -> &str;

    /// Detect if a file/target is supported by this analyzer
    fn can_handle(&self, target: &str) -> bool;
}

/// Factory for creating analyzers based on language or file extension
pub struct AnalyzerRegistry {
    analyzers: Vec<Box<dyn Analyzer>>,
}

impl AnalyzerRegistry {
    pub fn new() -> Self {
        Self {
            analyzers: Vec::new(),
        }
    }

    pub fn register(&mut self, analyzer: Box<dyn Analyzer>) {
        self.analyzers.push(analyzer);
    }

    pub async fn initialize_all() -> Result<Self> {
        let mut registry = Self::new();

        // Try to initialize each analyzer (graceful degradation if not available)
        if let Ok(python) = PythonAnalyzer::new().await {
            registry.register(Box::new(python));
        }

        if let Ok(java) = JavaAnalyzer::new().await {
            registry.register(Box::new(java));
        }

        if let Ok(nodejs) = NodeJsAnalyzer::new().await {
            registry.register(Box::new(nodejs));
        }

        if let Ok(go) = GoAnalyzer::new().await {
            registry.register(Box::new(go));
        }

        if let Ok(rust) = RustAnalyzer::new().await {
            registry.register(Box::new(rust));
        }

        Ok(registry)
    }

    pub fn find_analyzer(&self, target: &str, language: Option<&str>) -> Option<&dyn Analyzer> {
        if let Some(lang) = language {
            // Explicit language specified
            self.analyzers
                .iter()
                .find(|a| a.language() == lang)
                .map(|a| a.as_ref())
        } else {
            // Auto-detect based on target
            self.analyzers
                .iter()
                .find(|a| a.can_handle(target))
                .map(|a| a.as_ref())
        }
    }

    pub fn list_analyzers(&self) -> Vec<&dyn Analyzer> {
        self.analyzers.iter().map(|a| a.as_ref()).collect()
    }
}

// Analyzer implementations for each language
use crate::analyzer::python::PythonAnalyzer;
use crate::analyzer::java::JavaAnalyzer;
use crate::analyzer::nodejs::NodeJsAnalyzer;
use crate::analyzer::go::GoAnalyzer;
use crate::analyzer::rust::RustAnalyzer;

pub mod python;
pub mod java;
pub mod nodejs;
pub mod go;
pub mod rust;
