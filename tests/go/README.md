# Go Escape Tests

This folder contains Go functions for escape detection examples.

## Notes

- The Go analyzer currently does not load plugins (see analyzers/go/main.go).
- Go plugins are not supported on Windows, so these examples are primarily for reference.

## Example (Linux/macOS)

```bash
cd tests/go
# Build a plugin for a specific file set
# go build -buildmode=plugin -o escape_tests.so
```
