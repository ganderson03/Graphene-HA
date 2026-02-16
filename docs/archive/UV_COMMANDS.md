# UV Commands for Python CLI

This document provides `uv` commands for running the Python-based escape detection CLI.

## Setup

Ensure uv is installed and the environment is set up:

```powershell
# Install dependencies (if needed)
uv sync
```

## Basic Commands

### 1. Run All Tests

Run all tests across languages with generated inputs:

```powershell
# Windows
uv run llmpa --run-all --generate 20

# Linux/macOS
uv run llmpa --run-all --generate 20
```

This is equivalent to:

```powershell
.\target\release\escape-sentinel.exe run-all --test-dir tests --generate 20
```

### 2. Test a Specific Function

Test a single function from a test module:

```powershell
# Test thread escape
uv run llmpa tests.python.escape_threads:spawn_non_daemon_thread --input "test" --repeat 3

# Test process pool leak
uv run llmpa tests.python.escape_pool:leak_process_pool --input "data" --generate 10

# Test executor leak
uv run llmpa tests.python.escape_executor:leak_executor --input "hello" --repeat 5
```

### 3. Test Multiple Inputs

```powershell
# Multiple explicit inputs
uv run llmpa tests.python.escape_threads:spawn_daemon_thread `
  --input "test1" `
  --input "test2" `
  --input "test3" `
  --repeat 2

# Generate 20 random inputs
uv run llmpa tests.python.escape_process:spawn_process --generate 20

# Use input file
uv run llmpa tests.python.escape_pool:leak_process_pool_map_async --input-file inputs.txt
```

### 4. Execution Modes

Python CLI supports different execution modes for handling multiprocessing on Windows:

```powershell
# Main thread mode (recommended for Windows multiprocessing tests)
uv run llmpa tests.python.escape_process:spawn_process --main-thread-mode --generate 10

# Thread mode (no process isolation, faster)
uv run llmpa tests.python.escape_threads:spawn_non_daemon_thread --thread-mode --generate 10

# Process mode (full isolation, may fail on Windows for multiprocessing tests)
uv run llmpa tests.python.no_escape:join_thread --process-mode --generate 5
```

### 5. Timeout and Logging Options

```powershell
# Longer timeout for slow tests
uv run llmpa tests.python.escape_global_thread:spawn_global_thread --timeout 10 --generate 5

# Verbose logging (Python-only mode)
uv run llmpa --run-all --python-only --generate 10 --verbose

# Show successful test details (Python-only mode)
uv run llmpa --run-all --python-only --generate 10 --show-ok

# Custom log directory and test name
uv run llmpa tests.python.escape_executor:leak_new_executor `
  --generate 10 `
  --log-dir my_logs `
  --test-name executor_leak_test
```

## Common Use Cases

### Full Test Suite (Comprehensive)

```powershell
# Run all tests with 20 generated inputs (multi-language)
uv run llmpa --run-all --generate 20
```

### Quick Smoke Test

```powershell
# Run all tests with minimal inputs, fast
uv run llmpa --run-all --generate 3
```

### Windows Multiprocessing Tests

```powershell
# Run all Python tests using main thread mode (best for Windows)
uv run llmpa --run-all --python-only --generate 10 --main-thread-mode
```

### Reproduce Specific Issue

```powershell
# Test specific function with seeded inputs for reproducibility
uv run llmpa tests.python.escape_pool:leak_process_pool `
  --generate 20 `
  --seed 42 `
  --repeat 5 `
  --timeout 10 `
  --verbose
```

### Test Safe Patterns (Should Not Detect Escapes)

```powershell
# Test properly cleaned up threads
uv run llmpa tests.python.no_escape:join_thread --generate 10

# Test properly cleaned up processes
uv run llmpa tests.python.no_escape_process:join_process --generate 10

# Test properly managed pool
uv run llmpa tests.python.no_escape_pool:close_and_join_pool --generate 10
```

## Output Location

All test results are saved to:

```text
logs/run_YYYYMMDD_HHMMSS/test_name/
  ├── test_name.log          # Detailed test log
  ├── README.md              # Test summary (if run-all)
  └── results/               # Individual test results
```

## Command Comparison: Rust vs Python

| Task | Rust CLI | Python CLI (uv) |
| ---- | -------- | --------------- |
| Run all tests | `.\target\release\escape-sentinel.exe run-all --test-dir tests --generate 20` | `uv run llmpa --run-all --generate 20` |
| Test single function | `.\target\release\escape-sentinel.exe analyze --target tests/python/escape_threads.py:spawn_thread --input "test"` | `uv run llmpa tests.python.escape_threads:spawn_thread --input "test"` |
| Generate inputs | `--generate 20` | `--generate 20` |
| Timeout | `--timeout 10` | `--timeout 10` |
| Verbose output | `--verbose` (if available) | `--verbose` |

## Tips

1. **Use `--main-thread-mode` on Windows** for tests that use `multiprocessing` to avoid spawn context issues
2. **Use `--thread-mode`** for faster execution when testing pure thread leaks (no multiprocessing)
3. **Use `--generate` with `--seed`** for reproducible test runs
4. **Check logs/** directory after runs for detailed results
5. **Use `--show-ok`** during development to see all test outputs, not just failures

## Installation Note

The `llmpa` command is defined in [pyproject.toml](pyproject.toml):

```toml
[project.scripts]
llmpa = "escape_sentinel.cli:main"
```

This means `uv run llmpa` calls the `main()` function in [escape_sentinel/cli.py](escape_sentinel/cli.py).
