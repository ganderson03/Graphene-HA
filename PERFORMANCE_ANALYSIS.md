# Performance Analysis Dashboard

Visual reporting tool for Graphene-HA analyzer performance across all languages.

## Overview

The `analyze_performance.py` script aggregates data from all stored analysis sessions and generates comprehensive visual reports showing:

- **Success Rates** - Percentage of analyses that completed successfully per language
- **Crash Rates** - Percentage of analyses that crashed per language  
- **Escape Detection** - Percentage of analyses that detected object escapes
- **Execution Time** - Distribution of analysis execution times by language
- **Executive Summary** - Key statistics and trends

## Installation

Required Python packages:

```bash
pip install pandas matplotlib seaborn
```

Or using the project's uv environment:

```bash
uv pip install pandas matplotlib seaborn
```

## Usage

### Command Line

```bash
# From project root
python analyze_performance.py

# Or with uv
uv run python analyze_performance.py
```

### Output

The script generates:

1. **PNG Charts** (individual visualizations):
   - `performance_success_rates.png` - Bar chart of success rates by language
   - `performance_crash_rates.png` - Bar chart of crash rates by language
   - `performance_escape_detection.png` - Bar chart of escape detection rates
   - `performance_execution_times.png` - Box plot of execution time distributions
   - `performance_metrics_grid.png` - 2×2 grid view of all key metrics

2. **HTML Dashboard** (interactive report):
   - `performance_dashboard.html` - Open in any browser for an interactive view with:
     - Summary metrics cards
     - Embedded chart images
     - Language-specific statistics table
     - Responsive design

### Console Output

The script prints a summary to the console:

```
PERFORMANCE SUMMARY
==============================================
Total Results:           12,450
Languages:               go, java, javascript, python, rust
Total Successes:         12,340
Total Crashes:           110
Escapes Detected:        4,521
Overall Success Rate:    98.9%
Overall Crash Rate:      0.9%
Avg Execution Time:      342.5ms
==============================================
```

## Data Collection

The tool reads from the `logs/` directory structure:

```
logs/
  ├── go/
  │   ├── session_YYYYMMDD_HHMMSS.../
  │   │   ├── results.csv         ← Analyzed
  │   │   ├── README.md           ← Target extracted
  │   │   └── vulnerabilities.md
  │   └── ...
  ├── java/
  ├── javascript/
  ├── python/
  └── rust/
```

### CSV Format

Each `results.csv` contains per-execution metrics:

```
input,success,crashed,escape_detected,escape_summary,error,execution_time_ms
"",true,false,true,"1 escaping object(s) via 1 path(s)","",0
```

Columns:
- `input` - Test input provided to the function
- `success` - Whether execution completed without errors
- `crashed` - Whether the function crashed during execution
- `escape_detected` - Whether object escapes were detected
- `escape_summary` - Human-readable escape summary
- `error` - Error message if applicable
- `execution_time_ms` - Execution duration in milliseconds

## Metrics Explained

### Success Rate
Percentage of analyses where the target function executed and completed analysis without fatal errors. A high success rate indicates robust analyzer implementation.

### Crash Rate
Percentage of analyses where the target function crashed or hung during execution. A low crash rate is critical for production use.

### Escape Detection Rate
Percentage of analyses where at least one object escape was detected. This varies by test case design—not all functions are designed to have escaping objects.

### Execution Time
Wall-clock time for each individual analysis run. Includes:
- Startup overhead (interpreter initialization)
- Function invocation
- Escape analysis computation
- Result serialization

Longer times in Rust/Go are expected due to compilation overhead on first run.

## Interpreting Results

### High Success Rate + Low Crash Rate = Stability ✓
- Indicates production-ready analyzer
- Consistent behavior across test cases

### Variable Escape Detection
- Expected and normal—depends on test case design
- Compare with known baseline if available

### Outlier Execution Times
- May indicate:
  - Compilation/startup overhead (first run)
  - Complex escape analysis scenarios
  - Language-specific performance characteristics
- Box plot shows median and quartile ranges

## HTML Dashboard Features

The generated `performance_dashboard.html`:

- **Responsive Design** - Works on mobile, tablet, desktop
- **Color-Coded Metrics** - Green (success), Red (crash), Blue (detection), Purple (count)
- **Sortable Statistics Table** - Per-language breakdown
- **Embedded Charts** - All visualizations self-contained in single file
- **Static Output** - No JavaScript framework dependencies, fully offline

## Example Workflow

```bash
# 1. Run analysis suites (generates logs/*/results.csv)
uv run graphene run-all --test-dir tests --generate 10

# 2. Collect and visualize performance data
python analyze_performance.py

# 3. View dashboard in browser
start performance_dashboard.html  # Windows
open performance_dashboard.html   # macOS
xdg-open performance_dashboard.html  # Linux
```

## Troubleshooting

### "No results.csv files found!"
- Run analyses first: `uv run graphene run-all --test-dir tests`
- Verify logs directory exists: `ls logs/*/*/results.csv`

### "Required packages not found"
```bash
pip install pandas matplotlib seaborn
```

### Charts appear blank
- Ensure execution times are being recorded (check a sample results.csv)
- Verify sufficient results exist (minimum ~10 per language recommended)

## Performance Baselines

Typical performance ranges (may vary by hardware):

| Metric | Range | Target |
|--------|-------|--------|
| Success Rate | 98-100% | > 99% |
| Crash Rate | 0-2% | < 1% |
| Avg Exec Time | 100-500ms | < 200ms |
| Escape Detection | 30-70% | Case-dependent |

## Future Enhancements

Potential additions:
- Time-series trends (success rate over time)
- Comparison between analysis modes (static vs dynamic vs both)
- Error categorization and frequency analysis
- Performance regression detection
- Export to CSV/JSON for external analysis tools
- Real-time dashboard updates via log file monitoring
