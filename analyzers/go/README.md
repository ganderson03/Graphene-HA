# Go Bridge

This bridge connects the Rust orchestrator to Go code for escape analysis.

## Files

- **main.go** - Dynamic analyzer that executes Go functions and detects escaping goroutines
- **static_analyzer.go** - Static AST-based analyzer that detects goroutine spawns and channel usage
- **go.mod** - Go module definition

## Dynamic Analysis

The dynamic analyzer:
- Uses reflection to load and execute Go functions
- Tracks goroutines before and after function execution using `runtime.NumGoroutine()`
- Detects goroutines that escape the function boundary
- Measures execution times and detects panics

### Usage
```bash
# Build the analyzer first
go build -o escape-analyzer main.go

# Run analysis
echo '{"session_id":"test","target":"package:function","inputs":["data"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | ./escape-analyzer
```

## Static Analysis

The static analyzer uses Go's AST parser to:
- Parse Go source code
- Identify `go` statements (goroutine spawns)
- Track channel creation with `make(chan ...)`
- Detect channels that are created but never received on (potential leaks)

### Usage
```bash
# Build the static analyzer
go build -o static-escape-analyzer static_analyzer.go

# Run analysis
./static-escape-analyzer <source_file> <function_name>
```

## Dependencies

- Go 1.16+
- No external dependencies (uses standard library)

## Building

```bash
cd analyzers/go
go build -o escape-analyzer main.go
go build -o static-escape-analyzer static_analyzer.go
```
