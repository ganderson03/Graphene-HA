# Graphene HA

Graphene HA is a multi-language object and data escape analyzer.

It detects when locally allocated data escapes function scope through patterns such as:
- return of local objects
- storage in module/global state
- capture by retained closures
- passing objects into retaining sinks

## Supported Languages

- Python
- Java
- JavaScript/Node.js
- Go
- Rust

## Quick Start

```bash
# List analyzers
uv run graphene list --detailed

# Analyze one function
uv run graphene analyze tests/python/cases/case_001_cache_profile.py:case_001_cache_profile --input "sample"

# Run all discovered suites
uv run graphene run-all --generate 10

# Run one language only
uv run graphene run-all --language python --generate 10

# Clear logs
uv run graphene clear --log-dir logs
```

## 100-Case Suites Per Language

Each language now includes an annotated 100-case suite with realistic data-flow patterns.

See [tests/README.md](tests/README.md#language-reference) for language-specific suite locations and example targets.

Annotation style used in code comments:
- ESCAPE: explains where the object leaves local scope
- SAFE: explains why the object remains local

## CLI Commands

### analyze
Analyze a target function.

```bash
uv run graphene analyze <target> [--input VALUE ...] [--repeat N] [--timeout SECONDS] [--language LANG] [--analysis-mode dynamic|static|both] [--log-dir DIR] [--verbose]
```

Notes:
- Analysis mode defaults to `both` in both the Python wrapper and Rust CLI.
- Target format: module:function or file.ext:function.

### run-all
Run all discovered test targets.

```bash
uv run graphene run-all [--generate N] [--language LANG] [--log-dir DIR] [--verbose]
```

### list
List available analyzers.

```bash
uv run graphene list [--detailed]
```

### clear
Clear logs and optionally archive to CSV.

```bash
uv run graphene clear --log-dir logs [--archive-csv path/to/archive.csv]
```

## Project Layout

```text
graphene-ha/
	src/            # Rust orchestrator and static analyzers
	analyzers/      # Language bridges
	tests/          # Language test suites, including 100-case data-escape suites
	graphene_ha/    # Python CLI wrapper
```
