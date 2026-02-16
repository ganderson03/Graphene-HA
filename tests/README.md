# Test Programs

This directory contains demonstration and test programs organized by programming language.

## Directory Structure

```text
tests/
├── python/          # Python concurrency escape tests
│   ├── escape_threads.py         # Thread leaks (non-daemon threads)
│   ├── escape_process.py         # Process escapes
│   ├── escape_pool.py            # Process pool leaks
├── java/            # Java concurrency escape tests
│   ├── pom.xml
│   └── src/main/java/com/escape/tests/ThreadEscapes.java
│
├── nodejs/          # Node.js async escape tests
│   ├── escape_async.js
│   └── no_escape_async.js
│
├── go/              # Go goroutine escape tests
│   ├── escape_goroutines.go
│   ├── no_escape_goroutines.go
│   └── README.md
│
└── rust/            # Rust concurrency escape tests
  ├── src/
  │   ├── escape_threads.rs     # std::thread leaks
  │   ├── escape_async.rs       # Tokio task leaks
  │   ├── no_escape_threads.rs  # Safe thread patterns
  │   └── no_escape_async.rs    # Safe async patterns
  ├── examples/                 # Runnable examples
  ├── Cargo.toml
  └── README.md                 # Detailed Rust test documentation
    │   ├── escape_async.rs       # Tokio task leaks
    │   ├── no_escape_threads.rs  # Safe thread patterns
    │   └── no_escape_async.rs    # Safe async patterns
    ├── examples/                 # Runnable examples
    ├── Cargo.toml
    └── README.md                 # Detailed Rust test documentation
```

## Language-Specific Documentation

- **Python**: See individual file docstrings
- **Java**: See [tests/java/src/main/java/com/escape/tests/ThreadEscapes.java](java/src/main/java/com/escape/tests/ThreadEscapes.java)
- **Node.js**: See [tests/nodejs/escape_async.js](nodejs/escape_async.js)
- **Go**: See [tests/go/README.md](go/README.md) for platform notes
- **Rust**: See [tests/rust/README.md](rust/README.md) for comprehensive documentation

## Running Tests

### Python Tests

```bash
# Run a specific test
uv run graphene analyze tests/python/escape_threads.py:spawn_non_daemon_thread \
  --input "test"

# Run all tests (all languages)
uv run graphene run-all --test-dir tests --generate 10
```

### Rust Tests

```bash
# Build Rust test examples
cd tests/rust
cargo build --release --examples

# Run example programs
cargo run --release --example run_escape_threads
cargo run --release --example run_escape_async

# Analyze with Graphene HA
cd ../..
uv run graphene analyze tests_rust::escape_threads::spawn_detached_thread \
  --language rust --input "test"
```

## Test Categories

### Escape Patterns (Unsafe)

Tests that demonstrate concurrency resources escaping their intended scope:

- **Thread Leaks**: Threads spawned without `.join()`
- **Process Leaks**: Child processes not waited for
- **Pool Leaks**: Thread/process pools not properly closed
- **Async Leaks**: Tasks/promises without proper await/join
- **Timeout Patterns**: Infinite loops in concurrent contexts

### Safe Patterns

Tests demonstrating proper cleanup and resource management:

- **Joined Threads**: Properly await thread completion
- **Scoped Threads**: Compile-time guaranteed cleanup (Rust)
- **RAII Patterns**: Automatic cleanup via Drop trait (Rust)
- **Proper Await**: Tokio tasks properly awaited
- **Pool Cleanup**: Explicit shutdown and join

## Adding New Tests

### Python

Create a new `.py` file in `tests/python/`:

```python
import threading
import time

def my_test_function(input_data):
    """
    Brief description of what this tests.
    
    Expected: ESCAPE or SAFE
    """
    # Your test implementation
    pass
```

### Rust

Add functions to existing modules in `tests/rust/src/` or create new modules:

```rust
pub fn my_test_function(input: &str) -> String {
    // Your test implementation
    String::from("result")
}
```

Update `tests/rust/src/lib.rs` to export your module.

## Contributing

When adding tests, include:

1. **Clear naming**: Function name indicates expected behavior
2. **Documentation**: Explain what pattern is being tested
3. **Expected outcome**: Note whether escape is expected
4. **Minimal reproduction**: Keep tests focused and simple
