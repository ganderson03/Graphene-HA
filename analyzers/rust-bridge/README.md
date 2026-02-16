# Rust Bridge

This bridge enables the Rust orchestrator to analyze Rust code for escape patterns.

## Files

- **src/main.rs** - Dynamic analyzer that executes Rust functions and detects escaping threads
- **Cargo.toml** - Rust package manifest

## Structure

```
rust-bridge/
├── Cargo.toml
└── src/
    └── main.rs
```

## Dynamic Analysis

The dynamic analyzer:
- Uses dynamic loading to execute Rust functions
- Tracks threads spawned during execution
- Detects threads that are not joined
- Measures execution times and detects panics

### Usage
```bash
# Build the analyzer first
cargo build --release

# Run analysis
echo '{"session_id":"test","target":"module::function","inputs":["data"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | ./target/release/rust-analyzer
```

## Static Analysis

Rust static analysis is performed by the main Rust orchestrator directly, analyzing:
- `thread::spawn` and `tokio::spawn` patterns
- Thread handle creation and `.join()`/`.await` calls
- Heap allocations
- Return value escapes

The static analyzer uses text-based pattern matching on Rust source code.

## Dependencies

- Rust 1.70+
- tokio (for async runtime)
- serde, serde_json (for JSON serialization)

## Building

```bash
cd analyzers/rust-bridge
cargo build --release
```

This creates an executable at `target/release/rust-analyzer` which can be invoked by the orchestrator.
