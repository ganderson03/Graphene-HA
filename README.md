# Graphene HA

Graphene HA is a multi-language object escape analysis workflow.

## Scope

The project detects object retention patterns where data leaves local function scope, including:

- return-based escape
- global or module-level retention
- closure retention
- handoff into retaining sinks

## Supported Languages

- Python
- Java
- JavaScript/Node.js
- Go
- Rust

## Command Surface

### Analyze one target

```bash
uv run graphene analyze <target> --input "sample"
```

### Run discovered suites

```bash
uv run graphene run-all --generate 10
```

### List analyzers

```bash
uv run graphene list --detailed
```

### Clear logs

```bash
uv run graphene clear --log-dir logs
```

## Target Formats

- Python: tests/python/cases/file.py:function_name
- JavaScript: tests/nodejs/cases/file.js:functionName
- Go: tests/go/cases/file.go:ExportedFunction
- Rust: escape_tests_rust::module::function
- Java: com.escape.tests.cases.ClassName:methodName

## Repository Structure

```text
Graphene-HA/
  src/                  Rust orchestrator and shared protocol handling
  analyzers/            Language bridges
  tests/                Cross-language case suites
  graphene_ha/          Python CLI wrapper
  scripts/              Utility scripts for batch runs and reporting
  comparison_dashboard/ Generated comparison dashboard assets
```

## Outputs

Runs produce session artifacts per language/session:

- README.md
- results.csv
- vulnerabilities.md (when findings exist)

## Related Documentation

- analyzers/README.md
- tests/README.md
- PERFORMANCE_ANALYSIS.md
