# Quick Start Guide - Escape Sentinel

## Overview

Escape Sentinel is a multi-language concurrency escape detector with a Rust orchestrator and language-specific analyzers. It detects when concurrent resources (threads, processes, goroutines, async tasks) outlive their intended scope.

## Installation

### Prerequisites

- **Rust** (required): Install from <https://rustup.rs/>
- **Python 3** (optional): For Python analysis
- **Java 17+** and **Maven** (optional): For Java analysis
- **Node.js** (optional): For JavaScript analysis
- **Go 1.21+** (optional): For Go analysis
- **Rust** (required): Already installed for orchestrator

### Build

**Linux/macOS:**

```bash
chmod +x build.sh
./build.sh
```

**Windows:**

```powershell
.\build.bat
```

This will:

1. Build the Rust orchestrator
2. Build all available language-specific analyzers
3. Set up the execution environment

## Quick Examples

### 1. Check what analyzers are available

```bash
./target/release/escape-sentinel list --detailed
```

### 2. Analyze a Python function

```bash
./target/release/escape-sentinel analyze \
  --target tests/python/escape_threads.py:spawn_non_daemon_thread \
  --input "hello" \
  --repeat 3
```

### 3. Analyze with multiple inputs

```bash
./target/release/escape-sentinel analyze \
  --target tests/python/escape_pool.py:leak_process_pool \
  --input "test1" \
  --input "test2" \
  --input "test3" \
  --repeat 2 \
  --timeout 10
```

### 4. Analyze Rust concurrency

```bash
./target/release/escape-sentinel analyze \
  --target tests_rust::escape_async::spawn_detached_task \
  --input "test" \
  --language rust
```

### 5. Run all tests in a directory

```bash
./target/release/escape-sentinel run-all \
  --test-dir tests \
  --generate 20
```

## Alternative: Python CLI with UV

For Python-only testing, you can use the native Python CLI with `uv`:

### Setup

```bash
# Install dependencies
uv sync
```

### Python CLI Examples

```bash
# Run all Python tests
uv run llmpa --run-all --python-only --generate 20

# Test specific function
uv run llmpa tests.python.escape_threads:spawn_non_daemon_thread --input "hello"

# Multiple inputs with repeat
uv run llmpa tests.python.escape_pool:leak_process_pool \
  --input "test1" \
  --input "test2" \
  --generate 10 \
  --repeat 3

# Windows multiprocessing mode
uv run llmpa tests.python.escape_process:spawn_process \
  --main-thread-mode \
  --generate 10
```

**See [UV_COMMANDS.md](UV_COMMANDS.md) for comprehensive Python CLI documentation.**

## Understanding Results

### Clean Execution (No Escape)

```text
✅ No vulnerabilities detected

Total Tests: 3
Successes: 3 ✓
Escapes Detected: 0 🚨
```

### Escape Detected

```text
⚠️  VULNERABILITIES FOUND:
   • [HIGH] concurrent_escape - 1 thread(s), thread:Worker-1:nondaemon
   
Total Tests: 3
Escapes Detected: 2 🚨
Genuine Escapes: 2
```

### Reports Location

All reports are saved in `logs/session_TIMESTAMP/`:

- `README.md` - Summary with tables
- `results.csv` - Detailed results
- `vulnerabilities.md` - Vulnerability details

## Writing Test Functions

### Python Example

```python
def spawn_non_daemon_thread(input_data):
    """This will be detected as an escape"""
    import threading
    import time
    
    def worker():
        time.sleep(2)
    
    thread = threading.Thread(target=worker)
    thread.start()  # Thread not joined - ESCAPE!
    return "ok"

def safe_thread(input_data):
    """This is safe - no escape"""
    import threading
    
    def worker():
        pass
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()  # Properly cleaned up
    return "ok"
```

### Java Example

```java
public class EscapeTest {
    public static String spawnThread(String input) {
        new Thread(() -> {
            try { Thread.sleep(2000); } 
            catch (InterruptedException e) {}
        }).start();  // Thread not joined - ESCAPE!
        return "ok";
    }
}
```

### Node.js Example

```javascript
function createLeakingPromise(input) {
    // Promise never resolves - async resource escapes
    new Promise((resolve) => {
        setTimeout(() => {}, 10000);
    });
    return "ok";
}

function cleanAsync(input) {
    // Properly awaited or resolved
    return Promise.resolve("ok");
}
```

## Advanced Usage

### Custom Timeout

```bash
./target/release/escape-sentinel analyze \
  --target mymodule:slow_function \
  --input "data" \
  --timeout 30.0
```

### Language Override

```bash
./target/release/escape-sentinel analyze \
  --target MyClass:method \
  --language java \
  --input "test"
```

### Verbose Logging

```bash
./target/release/escape-sentinel analyze \
  --target test.py:func \
  --input "x" \
  --verbose
```

## Troubleshooting

### "No analyzer found for target"

- Ensure the file extension matches (.py, .java, .js, .go)
- Or specify `--language` explicitly
- Check that the analyzer was built successfully

### "Failed to spawn analyzer"

- Verify the language runtime is installed (python3, java, node, go)
- Check that bridge was built (`ls analyzers/*/`)
- Try running bridge directly for debugging

### Java analyzer not working

- Ensure Java 17+ is installed: `java -version`
- Build the JAR: `cd analyzers/java-bridge && mvn package`
- Check `analyzers/java-bridge/target/escape-analyzer.jar` exists

## Next Steps

1. **Run existing tests**: `./target/release/escape-sentinel run-all`
2. **Create your own tests**: Add functions to `tests/python/`
3. **Integrate into CI/CD**: Use exit codes to fail builds on escapes
4. **Read full docs**: See [MULTI_LANGUAGE_README.md](MULTI_LANGUAGE_README.md)

## Getting Help

```bash
# General help
./target/release/escape-sentinel --help

# Command-specific help
./target/release/escape-sentinel analyze --help
./target/release/escape-sentinel run-all --help
./target/release/escape-sentinel list --help
```
