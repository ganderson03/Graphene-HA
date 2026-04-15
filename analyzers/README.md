# Language Analyzers

This directory contains language bridge implementations used by the orchestrator.

## Structure

```text
analyzers/
  python/
  nodejs/
  go/
  java/
  rust/
```

## Bridge Responsibilities

- parse protocol request payloads
- resolve and execute target functions or methods
- collect runtime/static escape signals
- emit normalized response payloads

## Protocol Shape

Request fields:

- session_id
- target
- inputs
- repeat
- timeout_seconds
- options
- analysis_mode

Response fields:

- session_id
- language
- analyzer_version
- analysis_mode
- results
- vulnerabilities
- summary

## Build Summary

- Python: no build step
- Node.js: runtime execution via Node
- Go: go build
- Java: mvn clean package
- Rust: cargo build --release
