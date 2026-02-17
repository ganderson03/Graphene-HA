"""Constants module for Graphene CLI.

Centralizes configuration, defaults, and input patterns.
"""

# Input generation patterns for fuzzing/testing
INPUT_PATTERNS = [
    "",
    "0",
    "-1",
    "1",
    "true",
    "false",
    "null",
    "undefined",
    "hello",
    "\\x00",
    "\\n",
    "\\t",
    "'",
    '"',
    "()",
    "[]",
    "{}",
    "../",
    "..\\",
    "${HOME}",
    "$(whoami)",
    "{{7*7}}",
    "%s",
    "A" * 1024,
    "error",
    "exception",
    "1" * 100,
    "test" * 50,
    "async",
    "await",
    "timeout",
    "deadlock",
    "race",
    "concurrent",
    " " * 1000,
    "\\n" * 100,
    "<script>alert(1)</script>",
    "'; DROP TABLE; --",
    "../../../etc/passwd",
    "\\x1b[31m",
    "\\u0000",
]

# Default configuration values
DEFAULT_REPEAT_COUNT = 3
DEFAULT_GENERATE_COUNT = 10
DEFAULT_TIMEOUT = 5.0
DEFAULT_LOG_DIR = "logs"
DEFAULT_TEST_DIR = "tests"

# Directory structure
PYTHON_TEST_DIR = "tests/python"
NODEJS_TEST_DIR = "tests/nodejs"
GO_TEST_DIR = "tests/go"
JAVA_TEST_DIR = "tests/java"
RUST_TEST_DIR = "tests/rust"

# File extensions by language
LANGUAGE_EXTENSIONS = {
    "python": "py",
    "javascript": "js",
    "go": "go",
    "java": "java",
    "rust": "rs",
}

# Script paths for external analyzers
ANALYZER_SCRIPTS = {
    "python": "analyzers/python-bridge/static_analyzer.py",
    "javascript": "analyzers/nodejs-bridge/static_analyzer.js",
    "go": "analyzers/go-bridge/static_analyzer.go",
}
