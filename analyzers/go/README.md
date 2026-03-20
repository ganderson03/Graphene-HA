# Go Bridge

Bridge for Go object/data escape analysis.

## Files

- main.go
- static_analyzer.go
- go.mod

## Build

```bash
cd analyzers/go
go build -o escape-analyzer main.go
go build -o static-escape-analyzer static_analyzer.go
```

## Example target style

- tests/go/cases/case_001_cache_profile.go:Case001CacheProfile
