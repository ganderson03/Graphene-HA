# Rust Bridge

## Files

- src/main.rs
- Cargo.toml

## Functionality

- parses Rust crate/module/function targets
- builds a temporary runner for target invocation
- executes probes with timeout controls
- captures heap and thread escape signals
- emits normalized protocol results

## Build

```bash
cd analyzers/rust
cargo build --release
```

## Target Format

- escape_tests_rust::module::function
