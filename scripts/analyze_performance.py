#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
Performance analysis and visualization dashboard for Graphene-HA.
Aggregates results from all analysis sessions and generates visual reports.
"""

import os
import csv
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

try:
    import pandas as pd  # type: ignore[import-not-found]
    import matplotlib.pyplot as plt  # type: ignore[import-not-found]
    import seaborn as sns  # type: ignore[import-not-found]
except ImportError:
    print("Error: Required packages not found.")
    print("Install with: pip install pandas matplotlib seaborn")
    sys.exit(1)


class PerformanceAnalyzer:
    """Aggregates and analyzes Graphene-HA performance data."""

    OUTPUT_FILES = [
        "performance_success_rates.png",
        "performance_crash_rates.png",
        "performance_escape_detection.png",
        "performance_execution_times.png",
        "performance_metrics_grid.png",
        "performance_correctness_accuracy.png",
        "performance_correctness_confusion.png",
        "performance_dashboard.html",
    ]

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.data = []
        self.df = None
        self.repo_root = Path(__file__).resolve().parents[1]
        self._expected_cache: Dict[Tuple[str, str], Optional[bool]] = {}
        sns.set_theme(style="whitegrid")
        plt.rcParams["figure.figsize"] = (14, 8)

    def collect_results(self) -> None:
        """Aggregate all results.csv files from session directories."""
        print("📊 Collecting performance data...")

        # Always rebuild the in-memory dataset from scratch per run.
        self.data = []
        self.df = None

        if not self.logs_dir.exists():
            print(f"❌ Logs directory not found: {self.logs_dir}")
            return
        
        for language_dir in self.logs_dir.iterdir():
            if not language_dir.is_dir():
                continue
            
            language = language_dir.name
            session_count = 0
            
            for session_dir in language_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                
                results_file = session_dir / "results.csv"
                readme_file = session_dir / "README.md"
                
                if not results_file.exists():
                    continue
                
                session_count += 1
                # Extract timestamp from session directory name
                timestamp = self._parse_timestamp(session_dir.name)
                
                # Parse target from README if available
                target = self._extract_target(readme_file)
                
                # Read results CSV
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            self.data.append({
                                'timestamp': timestamp,
                                'language': language,
                                'session': session_dir.name,
                                'target': target,
                                'input': row.get('input', ''),
                                'success': row.get('success', '').lower() == 'true',
                                'crashed': row.get('crashed', '').lower() == 'true',
                                'escape_detected': row.get('escape_detected', '').lower() == 'true',
                                'execution_time_ms': float(row.get('execution_time_ms', 0)),
                                'error': row.get('error', ''),
                            })
                except Exception as e:
                    print(f"⚠️  Error reading {results_file}: {e}")
            
            if session_count > 0:
                print(f"  ✓ {language:12} - {session_count:4} sessions")
        
        if self.data:
            self.df = pd.DataFrame(self.data)
            self._attach_correctness_columns()
            print(f"\n✓ Collected {len(self.data)} total results across {self.df['language'].nunique()} languages")
        else:
            print("❌ No results.csv files found!")

    def _resolve_source_from_target(self, language: str, target: str) -> Optional[Path]:
        """Resolve analyzed target string to an expected-label source file, if available."""
        # Comparison dashboards may prefix language names (e.g., graphene__python).
        if "__" in language:
            language = language.rsplit("__", 1)[-1]

        if not target or target == "Unknown":
            return None

        # Generic target format: file_or_jar:function_or_class[:method]
        parts = target.split(":")
        first_part = parts[0].strip()

        if language == "rust":
            if first_part:
                candidate = (self.repo_root / first_part).resolve()
                if candidate.exists():
                    return candidate

            # Graphene Rust targets are typically crate::module::function.
            # Resolve module names back to benchmark case files.
            if "::" in target:
                rust_parts = [part.strip() for part in target.split("::") if part.strip()]
                if len(rust_parts) >= 3:
                    module = rust_parts[-2]
                    rust_candidates = [
                        self.repo_root / "tests" / "rust" / "cases" / f"{module}.rs",
                        self.repo_root / "tests" / "rust" / f"{module}.rs",
                    ]
                    for rust_candidate in rust_candidates:
                        resolved = rust_candidate.resolve()
                        if resolved.exists():
                            return resolved
            return None

        if language in {"python", "javascript", "go"}:
            if not first_part:
                return None
            candidate = (self.repo_root / first_part).resolve()
            return candidate if candidate.exists() else None

        if language == "java":
            # Either direct .java target or jar:fully.qualified.Class:method target.
            if first_part.endswith(".java"):
                candidate = (self.repo_root / first_part).resolve()
                return candidate if candidate.exists() else None

            # Classpath-style targets may include multiple entries before class name,
            # e.g. tests/java/target/app.jar;tests/java/target/classes:pkg.Class:execute
            if len(parts) >= 3:
                class_name = parts[-2].strip()
                if class_name:
                    java_rel = Path("tests/java/src/main/java") / Path(class_name.replace(".", "/")).with_suffix(".java")
                    candidate = (self.repo_root / java_rel).resolve()
                    return candidate if candidate.exists() else None

            if first_part.endswith(".jar") and len(parts) >= 2:
                class_name = parts[1].strip()
                if not class_name:
                    return None
                java_rel = Path("tests/java/src/main/java") / Path(class_name.replace(".", "/")).with_suffix(".java")
                candidate = (self.repo_root / java_rel).resolve()
                return candidate if candidate.exists() else None

        return None

    def _display_language_name(self, language: str) -> str:
        """Convert internal language keys to concise graph-friendly labels."""
        raw = language
        if "__" in language:
            parts = language.split("__")
            if parts[0] == "competitor" and len(parts) >= 2:
                tool = parts[1]
                lang = parts[2] if len(parts) >= 3 else ""
                cross_language_profiles = {
                    "mea2_heuristic",
                    "retained_state_rules",
                    "async_handoff_rules",
                }
                raw = f"{tool}-{lang}" if tool in cross_language_profiles and lang else tool
            elif parts[0] == "oss" and len(parts) >= 2:
                raw = f"oss-{parts[1]}"
            elif parts[0] == "graphene_static" and len(parts) >= 2:
                raw = f"graphene-static-{parts[1]}"
            elif parts[0] == "graphene_dynamic" and len(parts) >= 2:
                raw = f"graphene-dynamic-{parts[1]}"
            elif parts[0] == "graphene" and len(parts) >= 2:
                raw = f"graphene-both-{parts[1]}"
            else:
                raw = parts[-1]

        normalized = raw.replace("_", "-")
        return normalized

    def _style_x_labels(self, ax) -> None:
        """Apply readable spacing for dense category axes."""
        ax.tick_params(axis='x', labelsize=10)
        for label in ax.get_xticklabels():
            label.set_rotation(25)
            label.set_ha('right')

    def _expected_escape_for_target(self, language: str, target: str) -> Optional[bool]:
        """Return expected escape for known benchmark files, otherwise None."""
        cache_key = (language, target)
        if cache_key in self._expected_cache:
            return self._expected_cache[cache_key]

        source_path = self._resolve_source_from_target(language, target)
        if source_path is None:
            self._expected_cache[cache_key] = None
            return None

        try:
            text = source_path.read_text(encoding="utf-8", errors="replace")
            # SAFE marker denotes expected non-escape benchmark cases.
            expected = "SAFE:" not in text
            self._expected_cache[cache_key] = expected
            return expected
        except Exception:
            self._expected_cache[cache_key] = None
            return None

    def _attach_correctness_columns(self) -> None:
        """Attach expected labels and TP/TN/FP/FN classifications to the dataframe."""
        if self.df is None or self.df.empty:
            return

        expected_values = []
        labels = []
        known_values = []

        for _, row in self.df.iterrows():
            expected = self._expected_escape_for_target(str(row['language']), str(row['target']))
            expected_values.append(expected)
            known_values.append(expected is not None)

            if expected is None:
                labels.append("unknown")
                continue

            detected = bool(row['escape_detected'])
            if expected and detected:
                labels.append("tp")
            elif (not expected) and (not detected):
                labels.append("tn")
            elif expected and (not detected):
                labels.append("fn")
            else:
                labels.append("fp")

        self.df['expected_escape'] = expected_values
        self.df['correctness_known'] = known_values
        self.df['correctness_label'] = labels

    def _correctness_counts(self) -> Dict[str, int]:
        """Get overall correctness confusion counts for known benchmark cases."""
        if self.df is None or self.df.empty:
            return {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0}

        known_df = self.df[self.df['correctness_known']]
        counts = {
            "tp": int((known_df['correctness_label'] == "tp").sum()),
            "tn": int((known_df['correctness_label'] == "tn").sum()),
            "fp": int((known_df['correctness_label'] == "fp").sum()),
            "fn": int((known_df['correctness_label'] == "fn").sum()),
            "total": int(len(known_df)),
        }
        return counts

    def _correctness_metrics(self, tp: int, tn: int, fp: int, fn: int) -> Dict[str, float]:
        total = tp + tn + fp + fn
        accuracy = ((tp + tn) / total * 100.0) if total else 0.0
        precision = (tp / (tp + fp) * 100.0) if (tp + fp) else 0.0
        recall = (tp / (tp + fn) * 100.0) if (tp + fn) else 0.0
        mismatch_rate = ((fp + fn) / total * 100.0) if total else 0.0
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "mismatch_rate": mismatch_rate,
        }

    def _correctness_by_language(self) -> pd.DataFrame:
        """Build per-language correctness breakdown for known benchmark cases."""
        if self.df is None or self.df.empty:
            return pd.DataFrame()

        known_df = self.df[self.df['correctness_known']]
        rows = []
        for language in sorted(self.df['language'].unique()):
            lang_df = known_df[known_df['language'] == language]
            tp = int((lang_df['correctness_label'] == "tp").sum())
            tn = int((lang_df['correctness_label'] == "tn").sum())
            fp = int((lang_df['correctness_label'] == "fp").sum())
            fn = int((lang_df['correctness_label'] == "fn").sum())
            total = len(lang_df)
            metrics = self._correctness_metrics(tp, tn, fp, fn)
            rows.append({
                "language": language,
                "total": int(total),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "mismatch_rate": metrics["mismatch_rate"],
            })

        return pd.DataFrame(rows)

    def clear_previous_outputs(self) -> None:
        """Remove old generated dashboard assets before each run."""
        for output_file in self.OUTPUT_FILES:
            path = Path(output_file)
            if path.exists():
                path.unlink()

    def generate_empty_html_report(self) -> None:
        """Create an explicit empty-state dashboard when no log data exists."""
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Graphene-HA Performance Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            margin: 0;
            padding: 40px 20px;
            color: #1f2937;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        }}
        h1 {{
            margin: 0 0 12px 0;
            font-size: 30px;
        }}
        .muted {{
            color: #6b7280;
        }}
        .empty {{
            margin-top: 24px;
            padding: 20px;
            border-radius: 8px;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
        }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Performance Dashboard</h1>
            <p class="muted">Generated at {generated_at}</p>
            <div class="empty">
                <strong>No analysis data found.</strong>
                <p class="muted">The dashboard was rebuilt from the current logs folder and found no <code>results.csv</code> files.</p>
                <p class="muted">Run new analyses, then rerun <code>python scripts/analyze_performance.py</code>.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

        with open('performance_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print("✓ Saved: performance_dashboard.html (empty state)")

    def _parse_timestamp(self, session_name: str) -> datetime:
        """Extract timestamp from session directory name."""
        try:
            # Format: session_20260319_202115_2b276da9
            date_time = session_name.split('_')[1:3]
            if len(date_time) == 2:
                date_str, time_str = date_time
                # YYYYMMDD format
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                # HHMMSS format
                hour = int(time_str[:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6]) if len(time_str) >= 6 else 0
                return datetime(year, month, day, hour, minute, second)
        except (ValueError, IndexError):
            pass
        return datetime.now()

    def _extract_target(self, readme_file: Path) -> str:
        """Extract target function from README.md."""
        if not readme_file.exists():
            return "Unknown"
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("**Target:**"):
                        return line.replace("**Target:**", "").strip().strip("`")
        except Exception:
            pass
        return "Unknown"

    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        if self.df is None or self.df.empty:
            return {}
        
        summary = {
            'total_results': len(self.df),
            'languages': sorted(self.df['language'].unique().tolist()),
            'total_successes': self.df['success'].sum(),
            'total_crashes': self.df['crashed'].sum(),
            'total_escapes_detected': self.df['escape_detected'].sum(),
            'overall_success_rate': (self.df['success'].sum() / len(self.df) * 100),
            'overall_crash_rate': (self.df['crashed'].sum() / len(self.df) * 100),
            'avg_execution_time': self.df['execution_time_ms'].mean(),
        }

        correctness = self._correctness_counts()
        cmetrics = self._correctness_metrics(
            correctness["tp"],
            correctness["tn"],
            correctness["fp"],
            correctness["fn"],
        )

        summary.update({
            'correctness_total': correctness['total'],
            'correctness_tp': correctness['tp'],
            'correctness_tn': correctness['tn'],
            'correctness_fp': correctness['fp'],
            'correctness_fn': correctness['fn'],
            'overall_accuracy_rate': cmetrics['accuracy'],
            'overall_precision_rate': cmetrics['precision'],
            'overall_recall_rate': cmetrics['recall'],
            'overall_mismatch_rate': cmetrics['mismatch_rate'],
        })
        return summary

    def print_summary(self) -> None:
        """Print summary statistics to console."""
        summary = self.generate_summary()
        if not summary:
            return
        
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        print(f"Total Results:           {summary['total_results']:,}")
        display_langs = [self._display_language_name(lang) for lang in summary['languages']]
        print(f"Languages:               {', '.join(display_langs)}")
        print(f"Total Successes:         {summary['total_successes']:,}")
        print(f"Total Crashes:           {summary['total_crashes']:,}")
        print(f"Escapes Detected:        {summary['total_escapes_detected']:,}")
        print(f"Overall Success Rate:    {summary['overall_success_rate']:.1f}%")
        print(f"Overall Crash Rate:      {summary['overall_crash_rate']:.1f}%")
        print(f"Avg Execution Time:      {summary['avg_execution_time']:.1f}ms")
        print("-"*70)
        print("Correctness (known benchmark targets):")
        print(f"Known Cases:             {summary['correctness_total']:,}")
        print(f"TP/TN/FP/FN:            {summary['correctness_tp']}/{summary['correctness_tn']}/{summary['correctness_fp']}/{summary['correctness_fn']}")
        print(f"Overall Accuracy:        {summary['overall_accuracy_rate']:.1f}%")
        print(f"Overall Precision:       {summary['overall_precision_rate']:.1f}%")
        print(f"Overall Recall:          {summary['overall_recall_rate']:.1f}%")
        print(f"Overall Mismatch Rate:   {summary['overall_mismatch_rate']:.1f}%")
        print("="*70 + "\n")

    def plot_success_rates_by_language(self) -> None:
        """Create bar chart of success rates by language."""
        if self.df is None or self.df.empty:
            return
        
        success_by_lang = self.df.groupby('language')['success'].agg(['sum', 'count'])
        success_by_lang['rate'] = (success_by_lang['sum'] / success_by_lang['count'] * 100)
        
        display_index = [self._display_language_name(lang) for lang in success_by_lang.index]

        fig, ax = plt.subplots(figsize=(13, 7))
        bars = ax.bar(display_index, success_by_lang['rate'], 
                      color=sns.color_palette("husl", len(success_by_lang)))
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Success Rate (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Analysis Success Rate by Language', fontsize=14, fontweight='bold')
        ax.set_ylim([0, 105])
        self._style_x_labels(ax)
        
        plt.tight_layout()
        plt.savefig('performance_success_rates.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_success_rates.png")
        plt.close()

    def plot_execution_times(self) -> None:
        """Create boxplot of execution times by language."""
        if self.df is None or self.df.empty or self.df['execution_time_ms'].max() == 0:
            return
        
        fig, ax = plt.subplots(figsize=(13, 7))
        
        # Only include runs with non-zero execution times
        df_filtered = self.df[self.df['execution_time_ms'] > 0]
        if df_filtered.empty:
            print("⚠️  No execution time data available")
            plt.close()
            return
        
        languages = sorted(df_filtered['language'].unique())
        display_languages = [self._display_language_name(lang) for lang in languages]
        data_by_lang = [df_filtered[df_filtered['language'] == lang]['execution_time_ms'].values for lang in languages]
        
        bp = ax.boxplot(data_by_lang, tick_labels=display_languages, patch_artist=True)
        
        # Color the boxes
        colors = sns.color_palette("husl", len(languages))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_ylabel('Execution Time (ms)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Execution Time Distribution by Language', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        self._style_x_labels(ax)
        
        plt.tight_layout()
        plt.savefig('performance_execution_times.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_execution_times.png")
        plt.close()

    def plot_crash_rates(self) -> None:
        """Create bar chart of crash rates by language."""
        if self.df is None or self.df.empty:
            return
        
        crash_by_lang = self.df.groupby('language')['crashed'].agg(['sum', 'count'])
        crash_by_lang['rate'] = (crash_by_lang['sum'] / crash_by_lang['count'] * 100)
        
        display_index = [self._display_language_name(lang) for lang in crash_by_lang.index]

        fig, ax = plt.subplots(figsize=(13, 7))
        bars = ax.bar(display_index, crash_by_lang['rate'],
                      color=sns.color_palette("Reds", len(crash_by_lang)))
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Crash Rate (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Analysis Crash Rate by Language', fontsize=14, fontweight='bold')
        ax.set_ylim([0, max(105, crash_by_lang['rate'].max() + 5)])
        self._style_x_labels(ax)
        
        plt.tight_layout()
        plt.savefig('performance_crash_rates.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_crash_rates.png")
        plt.close()

    def plot_escape_detection(self) -> None:
        """Create bar chart of escape detection by language."""
        if self.df is None or self.df.empty:
            return
        
        escape_by_lang = self.df.groupby('language')['escape_detected'].agg(['sum', 'count'])
        escape_by_lang['rate'] = (escape_by_lang['sum'] / escape_by_lang['count'] * 100)
        
        display_index = [self._display_language_name(lang) for lang in escape_by_lang.index]

        fig, ax = plt.subplots(figsize=(13, 7))
        bars = ax.bar(display_index, escape_by_lang['rate'],
                      color=sns.color_palette("Blues", len(escape_by_lang)))
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylabel('Escapes Detected (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Escape Detection Rate by Language', fontsize=14, fontweight='bold')
        ax.set_ylim([0, 105])
        self._style_x_labels(ax)
        
        plt.tight_layout()
        plt.savefig('performance_escape_detection.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_escape_detection.png")
        plt.close()

    def plot_metrics_grid(self) -> None:
        """Create a 2x2 grid showing all key metrics."""
        if self.df is None or self.df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(20, 14))
        languages = sorted(self.df['language'].unique())
        
        # 1. Success Rates
        success_by_lang = self.df.groupby('language')['success'].agg(['sum', 'count'])
        success_by_lang['rate'] = (success_by_lang['sum'] / success_by_lang['count'] * 100)
        display_success = [self._display_language_name(lang) for lang in success_by_lang.index]
        axes[0, 0].bar(display_success, success_by_lang['rate'],
                       color=sns.color_palette("husl", len(success_by_lang)))
        axes[0, 0].set_title('Success Rate by Language', fontsize=12, fontweight='bold')
        axes[0, 0].set_ylabel('Rate (%)')
        axes[0, 0].set_ylim([0, 105])
        axes[0, 0].grid(axis='y', alpha=0.3)
        
        # 2. Crash Rates
        crash_by_lang = self.df.groupby('language')['crashed'].agg(['sum', 'count'])
        crash_by_lang['rate'] = (crash_by_lang['sum'] / crash_by_lang['count'] * 100)
        display_crash = [self._display_language_name(lang) for lang in crash_by_lang.index]
        axes[0, 1].bar(display_crash, crash_by_lang['rate'],
                       color=sns.color_palette("Reds", len(crash_by_lang)))
        axes[0, 1].set_title('Crash Rate by Language', fontsize=12, fontweight='bold')
        axes[0, 1].set_ylabel('Rate (%)')
        axes[0, 1].grid(axis='y', alpha=0.3)
        
        # 3. Escape Detection
        escape_by_lang = self.df.groupby('language')['escape_detected'].agg(['sum', 'count'])
        escape_by_lang['rate'] = (escape_by_lang['sum'] / escape_by_lang['count'] * 100)
        display_escape = [self._display_language_name(lang) for lang in escape_by_lang.index]
        axes[1, 0].bar(display_escape, escape_by_lang['rate'],
                       color=sns.color_palette("Blues", len(escape_by_lang)))
        axes[1, 0].set_title('Escape Detection Rate by Language', fontsize=12, fontweight='bold')
        axes[1, 0].set_ylabel('Rate (%)')
        axes[1, 0].set_ylim([0, 105])
        axes[1, 0].grid(axis='y', alpha=0.3)
        
        # 4. Execution Count
        exec_by_lang = self.df.groupby('language').size()
        display_exec = [self._display_language_name(lang) for lang in exec_by_lang.index]
        axes[1, 1].bar(display_exec, exec_by_lang.values,
                       color=sns.color_palette("viridis", len(exec_by_lang)))
        axes[1, 1].set_title('Analysis Execution Count by Language', fontsize=12, fontweight='bold')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].grid(axis='y', alpha=0.3)

        self._style_x_labels(axes[0, 0])
        self._style_x_labels(axes[0, 1])
        self._style_x_labels(axes[1, 0])
        self._style_x_labels(axes[1, 1])
        
        plt.tight_layout()
        plt.savefig('performance_metrics_grid.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_metrics_grid.png")
        plt.close()

    def plot_correctness_accuracy(self) -> None:
        """Create bar chart of semantic accuracy by language (known benchmark cases only)."""
        if self.df is None or self.df.empty:
            return

        correctness_df = self._correctness_by_language()
        if correctness_df.empty or int(correctness_df['total'].sum()) == 0:
            print("⚠️  No known expected labels found; skipping correctness accuracy chart")
            return

        fig, ax = plt.subplots(figsize=(13, 7))
        display_languages = [self._display_language_name(lang) for lang in correctness_df['language']]
        bars = ax.bar(
            display_languages,
            correctness_df['accuracy'],
            color=sns.color_palette("crest", len(correctness_df)),
        )

        for bar, _, total in zip(bars, correctness_df['accuracy'], correctness_df['total']):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}%\n(n={int(total)})",
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold',
            )

        ax.set_ylabel('Semantic Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Correctness Accuracy by Language (Known Cases)', fontsize=14, fontweight='bold')
        ax.set_ylim([0, 105])
        ax.grid(axis='y', alpha=0.3)
        self._style_x_labels(ax)

        plt.tight_layout()
        plt.savefig('performance_correctness_accuracy.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_correctness_accuracy.png")
        plt.close()

    def plot_correctness_confusion(self) -> None:
        """Create grouped bar chart of TP/TN/FP/FN counts by language."""
        if self.df is None or self.df.empty:
            return

        correctness_df = self._correctness_by_language()
        if correctness_df.empty or int(correctness_df['total'].sum()) == 0:
            print("⚠️  No known expected labels found; skipping correctness confusion chart")
            return

        fig, ax = plt.subplots(figsize=(14, 7))
        x = range(len(correctness_df))
        width = 0.2

        ax.bar([i - 1.5 * width for i in x], correctness_df['tp'], width=width, label='TP', color='#10b981')
        ax.bar([i - 0.5 * width for i in x], correctness_df['tn'], width=width, label='TN', color='#3b82f6')
        ax.bar([i + 0.5 * width for i in x], correctness_df['fp'], width=width, label='FP', color='#f59e0b')
        ax.bar([i + 1.5 * width for i in x], correctness_df['fn'], width=width, label='FN', color='#ef4444')

        ax.set_xticks(list(x))
        ax.set_xticklabels([self._display_language_name(lang) for lang in correctness_df['language']])
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_xlabel('Language', fontsize=12, fontweight='bold')
        ax.set_title('Correctness Confusion Counts by Language', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        self._style_x_labels(ax)

        plt.tight_layout()
        plt.savefig('performance_correctness_confusion.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: performance_correctness_confusion.png")
        plt.close()

    def generate_html_report(self) -> None:
        """Generate interactive HTML report."""
        if self.df is None or self.df.empty:
            return
        
        summary = self.generate_summary()
        correctness_by_language = self._correctness_by_language()
        correctness_available = (not correctness_by_language.empty) and int(correctness_by_language['total'].sum()) > 0
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Graphene-HA Performance Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-card.success {{ border-left-color: #10b981; }}
        .metric-card.crash {{ border-left-color: #ef4444; }}
        .metric-card.escape {{ border-left-color: #f59e0b; }}
        .metric-card.correctness {{ border-left-color: #0ea5e9; }}
        .metric-card.mismatch {{ border-left-color: #f97316; }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .chart-container img {{
            width: 100%;
            height: auto;
        }}
        .language-stats {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 40px;
        }}
        .language-stats h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .stats-table th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e5e7eb;
        }}
        .stats-table td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        .stats-table tr:hover {{
            background: #f8f9fa;
        }}
        footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Performance Dashboard</h1>
            <p class="subtitle">Real-time analysis of escape detection across multiple languages</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Analyses</div>
                <div class="metric-value">{summary['total_results']:,}</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{summary['overall_success_rate']:.1f}%</div>
            </div>
            <div class="metric-card crash">
                <div class="metric-label">Crash Rate</div>
                <div class="metric-value">{summary['overall_crash_rate']:.1f}%</div>
            </div>
            <div class="metric-card escape">
                <div class="metric-label">Escapes Detected</div>
                <div class="metric-value">{summary['total_escapes_detected']:,}</div>
            </div>
            <div class="metric-card correctness">
                <div class="metric-label">Correctness Accuracy</div>
                <div class="metric-value">{summary['overall_accuracy_rate']:.1f}%</div>
            </div>
            <div class="metric-card mismatch">
                <div class="metric-label">Mismatch Rate</div>
                <div class="metric-value">{summary['overall_mismatch_rate']:.1f}%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <img src="performance_success_rates.png" alt="Success Rates">
            </div>
            <div class="chart-container">
                <img src="performance_crash_rates.png" alt="Crash Rates">
            </div>
            <div class="chart-container">
                <img src="performance_escape_detection.png" alt="Escape Detection">
            </div>
            <div class="chart-container">
                <img src="performance_execution_times.png" alt="Execution Times">
            </div>
        </div>
        
        <div class="chart-container" style="margin-bottom: 40px;">
            <img src="performance_metrics_grid.png" alt="Metrics Grid">
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <img src="performance_correctness_accuracy.png" alt="Correctness Accuracy">
            </div>
            <div class="chart-container">
                <img src="performance_correctness_confusion.png" alt="Correctness Confusion">
            </div>
        </div>
        
        <div class="language-stats">
            <h2>Language-Specific Statistics</h2>
            <table class="stats-table">
                <tr>
                    <th>Language</th>
                    <th>Analyses</th>
                    <th>Success Rate</th>
                    <th>Crash Rate</th>
                    <th>Escape Detection</th>
                    <th>Known Cases</th>
                    <th>TP/TN/FP/FN</th>
                    <th>Accuracy</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>Mismatch</th>
                </tr>
"""
        
        for lang in sorted(self.df['language'].unique()):
            lang_data = self.df[self.df['language'] == lang]
            display_lang = self._display_language_name(lang)
            success_rate = (lang_data['success'].sum() / len(lang_data) * 100) if len(lang_data) > 0 else 0
            crash_rate = (lang_data['crashed'].sum() / len(lang_data) * 100) if len(lang_data) > 0 else 0
            escape_rate = (lang_data['escape_detected'].sum() / len(lang_data) * 100) if len(lang_data) > 0 else 0

            c_row = None
            if correctness_available:
                matches = correctness_by_language[correctness_by_language['language'] == lang]
                if not matches.empty:
                    c_row = matches.iloc[0]

            if c_row is not None:
                known_total = int(c_row['total'])
                confusion = f"{int(c_row['tp'])}/{int(c_row['tn'])}/{int(c_row['fp'])}/{int(c_row['fn'])}"
                accuracy = f"{float(c_row['accuracy']):.1f}%"
                precision = f"{float(c_row['precision']):.1f}%"
                recall = f"{float(c_row['recall']):.1f}%"
                mismatch = f"{float(c_row['mismatch_rate']):.1f}%"
            else:
                known_total = 0
                confusion = "-"
                accuracy = "-"
                precision = "-"
                recall = "-"
                mismatch = "-"
            
            html_content += f"""
                <tr>
                    <td><strong>{display_lang}</strong></td>
                    <td>{len(lang_data)}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{crash_rate:.1f}%</td>
                    <td>{escape_rate:.1f}%</td>
                    <td>{known_total}</td>
                    <td>{confusion}</td>
                    <td>{accuracy}</td>
                    <td>{precision}</td>
                    <td>{recall}</td>
                    <td>{mismatch}</td>
                </tr>
"""
        
        html_content += """
            </table>
        </div>
        
        <footer>
            <p>Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>Graphene-HA Multi-Language Escape Analysis System</p>
        </footer>
    </div>
</body>
</html>
"""
        
        with open('performance_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Saved: performance_dashboard.html")

    def run(self) -> None:
        """Execute full analysis pipeline."""
        print("\n🚀 Starting Performance Analysis...\n")
        self.clear_previous_outputs()
        self.collect_results()
        self.print_summary()
        
        if self.df is not None and not self.df.empty:
            print("📈 Generating visualizations...\n")
            self.plot_success_rates_by_language()
            self.plot_crash_rates()
            self.plot_escape_detection()
            self.plot_execution_times()
            self.plot_metrics_grid()
            self.plot_correctness_accuracy()
            self.plot_correctness_confusion()
            self.generate_html_report()
            print("\n✅ Analysis complete! Open 'performance_dashboard.html' to view results.")
        else:
            self.generate_empty_html_report()
            print("❌ No data collected. Empty-state dashboard was generated.")


if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    analyzer.run()
