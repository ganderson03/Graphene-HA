# Go Bridge

## Files

- main.go
- static_analyzer.go
- go.mod

## Functionality

- parses Go target references
- builds temporary target runners for dynamic execution
- executes probes under timeout constraints
- records heap and goroutine-related escape signals
- emits normalized protocol results

## Build

```bash
cd analyzers/go
go build -o escape-analyzer main.go
go build -o static-escape-analyzer static_analyzer.go
```

## Target Format

- tests/go/cases/file.go:ExportedFunction
