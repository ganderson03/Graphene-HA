"""Help text module for Graphene CLI.

Centralizes all help documentation to reduce cli.py complexity.
"""


def show_help(topic: str | None = None) -> None:
    """Display help information for specified topic or general help."""
    if topic is None:
        print(_GENERAL_HELP)
    elif topic == "analyze":
        print(_ANALYZE_HELP)
    elif topic == "run-all":
        print(_RUN_ALL_HELP)
    elif topic == "list":
        print(_LIST_HELP)


_GENERAL_HELP = """Graphene HA - Multi-language Concurrency Escape Detector

USAGE:
  uv run graphene <COMMAND> [OPTIONS]

COMMANDS:
  analyze      Analyze a specific function for concurrency escapes
  run-all      Run all test suites across all supported languages
  list         List available analyzers and their capabilities
  help         Show this help information

OPTIONS:
  -h, --help   Show this help message and exit

EXAMPLES:
  # Analyze a Python function
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --input "test" --repeat 3

  # Python analysis with static + dynamic detection
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --analysis-mode both --input "test"

  # Analyze a Java method
  uv run graphene analyze com.escape.tests.ThreadEscapes:spawnNonDaemonThread --language java --input "test"

  # Analyze a Node.js function
  uv run graphene analyze tests/nodejs/escape_async.js:createLeakingInterval --language javascript --input "test"

  # Analyze a Go function
  uv run graphene analyze escape_tests:SpawnDetachedGoroutine --language go --input "test"

  # Run all tests across all languages
  uv run graphene run-all --generate 20

  # Run only Python tests
  uv run graphene run-all --language python --generate 10

  # List all available analyzers
  uv run graphene list --detailed

For more details on a specific command, use:
  uv run graphene help <COMMAND>
"""

_ANALYZE_HELP = """COMMAND: graphene analyze

DESCRIPTION:
  Analyze a specific function for concurrency escapes (thread/process/goroutine/async leaks).

USAGE:
  uv run graphene analyze <TARGET> [OPTIONS]

ARGUMENTS:
  TARGET                 Function target in format: module:function or file.ext:function
                         Examples: tests.python.escape_threads:spawn_non_daemon_thread
                                  com.escape.tests.ThreadEscapes:spawnNonDaemonThread
                                  tests/nodejs/escape_async.js:createLeakingInterval

OPTIONS:
  --input TEXT           Input data for the function (repeatable, can use multiple times)
  --input-file PATH      File with one input per line
  --repeat N             Repeat each input N times (default: 3)
  --generate N           Generate N simple inputs for testing (Python only)
  --seed N               Seed for generated inputs (Python only)
  --timeout N            Timeout per execution in seconds (default: 5.0 seconds)
  --language LANG        Force language detection: python, java, javascript, go, rust
                         Auto-detected if not specified
  --analysis-mode MODE   Analysis mode: dynamic (runtime), static (source), or both
                         (default: dynamic)
  --log-dir DIR          Output directory for detailed reports (default: logs/)
  --test-name NAME       Custom name for test session (Python only)
  --thread-mode          Force thread-based execution (Python only)
  --main-thread-mode     Run in main thread (Python only)
  --process-mode         Force process isolation (Python only)
  --show-ok              Include successful execution logs (Python only)
  --verbose              Enable detailed logging output

EXAMPLES:
  # Basic Python analysis
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --input "test"

  # Multiple inputs
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --input "test" --input "data" --repeat 5

  # Static + dynamic analysis
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --analysis-mode both --input "test"

  # Java method with timeout
  uv run graphene analyze com.escape.tests.ThreadEscapes:spawnNonDaemonThread --language java --input "test" --timeout 10

  # Generated inputs
  uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread --generate 50 --seed 123
"""

_RUN_ALL_HELP = """COMMAND: graphene run-all

DESCRIPTION:
  Run all test suites across supported languages or a specific language.

USAGE:
  uv run graphene run-all [OPTIONS]

OPTIONS:
  --test-dir DIR         Root test directory (default: tests/)
  --generate N           Number of inputs per test (default: 10)
  --language LANG        Filter by language: python, java, javascript, go, rust
  --log-dir DIR          Output directory for reports (default: logs/)
  --python-only          Run only Python tests with native Python harness
  --repeat N             Repeat each input N times (Python-only mode, default: 1)
  --seed N               Seed for generated inputs (Python-only mode)
  --timeout N            Timeout in seconds (Python-only mode, default: 5.0)
  --thread-mode          Force thread-based execution (Python-only mode)
  --main-thread-mode     Run in main thread (Python-only mode)
  --process-mode         Force process isolation (Python-only mode)
  --test-name NAME       Test session name (Python-only mode)
  --show-ok              Include successful execution logs (Python-only mode)
  --verbose              Enable detailed logging output

EXAMPLES:
  # Run all tests with default settings
  uv run graphene run-all --generate 20

  # Run Python tests only
  uv run graphene run-all --language python --generate 10

  # Run Java tests with custom timeout
  uv run graphene run-all --language java --timeout 15

  # Python-only native execution with process isolation
  uv run graphene run-all --python-only --generate 5 --process-mode

  # Run with increased repetitions and verbose output
  uv run graphene run-all --generate 10 --repeat 3 --verbose
"""

_LIST_HELP = """COMMAND: graphene list

DESCRIPTION:
  List available language analyzers and their capabilities.

USAGE:
  uv run graphene list [OPTIONS]

OPTIONS:
  --detailed             Show detailed analyzer capabilities and detection features

EXAMPLES:
  # List available analyzers
  uv run graphene list

  # Show detailed capabilities
  uv run graphene list --detailed
"""
