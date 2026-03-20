# Language Analyzers

This directory contains language bridges used by the Rust orchestrator.

## Purpose

Each bridge executes or parses language-specific targets and reports escape findings using a shared JSON protocol.

## Structure

```text
analyzers/
	python/
	nodejs/
	go/
	java/
	rust/
```

## Protocol Summary

Request fields:
- session_id
- target
- inputs
- repeat
- timeout_seconds
- options

Response fields:
- session_id
- language
- analyzer_version
- analysis_mode
- results
- vulnerabilities
- summary

## Build Notes

- Python: no build step
- Node.js: runtime-dependent
- Go: go build
- Java: maven package
- Rust: cargo build --release
