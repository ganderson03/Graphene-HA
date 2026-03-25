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

## Graphene vs Competitor Benchmark Workflow

Use this workflow to run Graphene test suites through competitor analyzers and
generate the same dashboard-style graphs used by Graphene performance analysis.

1. Run Graphene baseline (writes Graphene logs):

```bash
uv run graphene run-all --generate 1 --log-dir logs
```

1. Collect competitor results in Graphene-compatible `results.csv` sessions:

```bash
python scripts/collect_competitor_benchmarks.py --log-dir logs_competitors --limit 100
```

1. Build combined comparison dashboard:

```bash
python scripts/build_comparison_dashboard.py \
 --graphene-logs logs \
 --competitor-logs logs_competitors \
 --combined-logs logs_comparison \
 --output-dir comparison_dashboard
```

1. Open:

```text
comparison_dashboard/performance_dashboard.html
```

### One-Command Full Run

Run Graphene baseline, collect competitor data, and build the HTML dashboard in one command:

```bash
python scripts/run_full_comparison.py
```

Common overrides:

```bash
python scripts/run_full_comparison.py \
 --generate 1 \
 --competitor-limit 100 \
 --graphene-logs logs \
 --competitor-logs logs_competitors \
 --combined-logs logs_comparison \
 --output-dir comparison_dashboard
```

Notes:

- Comparison labels appear as prefixed language keys (for example `graphene__python`, `competitor__go_native_escape__go`).
- Competitor collection uses escape-focused analyzers: native Go compiler escape analysis, language-specific escape pattern analyzers, and cross-language heuristic profiles (`mea2_heuristic`, `retained_state_rules`, `async_handoff_rules`).

### Open-Source Benchmark Mode

To complement synthetic suites with real-world code, clone/sample OSS repositories and run static analysis targets:

```bash
python scripts/run_open_source_benchmarks.py --per-project 25 --timeout 5 --log-dir logs_oss_bench
```

This writes a CSV report at `benchmarks/oss_benchmark_report.csv` and Graphene session logs in the selected log directory.

## 300-Case Suites Per Language

Each language now includes an annotated 300-case suite with realistic and adversarial data-flow patterns.

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
