# Performance Analysis

This document covers current performance-reporting structure and functionality.

## Purpose

The performance analysis workflow aggregates session outputs and produces summary metrics and visual dashboards.

## Input Data

Expected input is session-level CSV output under log directories.

Typical per-row fields:

- input
- success
- crashed
- escape_detected
- error
- execution_time_ms

## Primary Utility

- scripts/analyze_performance.py

Functionality:

- aggregate run results across languages
- compute success/crash/escape rates
- compute execution-time distributions
- generate chart images
- generate an HTML dashboard

## Generated Outputs

- performance_success_rates.png
- performance_crash_rates.png
- performance_escape_detection.png
- performance_execution_times.png
- performance_metrics_grid.png
- performance_dashboard.html

## Run

```bash
python scripts/analyze_performance.py
```

or

```bash
uv run python scripts/analyze_performance.py
```

## Expected Log Layout

```text
artifacts/logs/
  <language>/
    <session_id>/
      results.csv
      README.md
      vulnerabilities.md
```

## Interpretation Focus

- stability: success vs crash rate
- detection behavior: escape detection rate
- runtime cost: execution-time distribution by language
