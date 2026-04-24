#!/usr/bin/env python3
"""
Build baseline accuracy leaderboard and Graphene error buckets.

Step 1 output:
- Frozen per-language baseline table with accuracy/precision/recall/fp/fn/crash.
- Graphene vs best competitor gap by language.

Step 2 output:
- Top FP/FN miss buckets for Graphene by language, including sample targets.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional
import sys

import pandas as pd

# Reuse existing log parsing and expected-label resolution logic.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.analyze_performance import PerformanceAnalyzer


def _base_language(language_key: str) -> str:
    if "__" in language_key:
        return language_key.rsplit("__", 1)[-1]
    return language_key


def _tool_name(language_key: str) -> str:
    if language_key.startswith("graphene__"):
        return "graphene"
    if language_key.startswith("competitor__"):
        parts = language_key.split("__")
        return parts[1] if len(parts) >= 2 else "competitor"
    if language_key.startswith("oss__"):
        return "oss"
    if language_key in {"go", "java", "javascript", "python", "rust"}:
        return "graphene"
    return language_key


def _safe_round(value: float) -> float:
    return round(float(value), 2)


def _bucket_from_source(source_path: Optional[Path], target: str) -> str:
    """Map case paths to stable family buckets (e.g., helper_sink_dispatch)."""
    candidate = ""
    if source_path is not None:
        candidate = source_path.stem
    elif target and target != "Unknown":
        first = target.split(":", 1)[0].strip()
        candidate = Path(first).stem

    if not candidate:
        return "unknown"

    # case_202_helper_sink_dispatch_01 -> helper_sink_dispatch
    m = re.match(r"^case_\d+_(.+)$", candidate)
    if m:
        candidate = m.group(1)

    candidate = re.sub(r"_\d+$", "", candidate)
    candidate = candidate.strip("_")
    return candidate or "unknown"


def _compute_metrics(known_df: pd.DataFrame, full_df: pd.DataFrame, language_key: str) -> dict:
    known_lang = known_df[known_df["language"] == language_key]
    full_lang = full_df[full_df["language"] == language_key]

    tp = int((known_lang["correctness_label"] == "tp").sum())
    tn = int((known_lang["correctness_label"] == "tn").sum())
    fp = int((known_lang["correctness_label"] == "fp").sum())
    fn = int((known_lang["correctness_label"] == "fn").sum())
    total_known = tp + tn + fp + fn

    accuracy = ((tp + tn) / total_known * 100.0) if total_known else 0.0
    precision = (tp / (tp + fp) * 100.0) if (tp + fp) else 0.0
    recall = (tp / (tp + fn) * 100.0) if (tp + fn) else 0.0

    total_runs = int(len(full_lang))
    crashes = int(full_lang["crashed"].sum()) if total_runs else 0
    crash_rate = (crashes / total_runs * 100.0) if total_runs else 0.0

    return {
        "language_key": language_key,
        "base_language": _base_language(language_key),
        "tool": _tool_name(language_key),
        "known_total": int(total_known),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": _safe_round(accuracy),
        "precision": _safe_round(precision),
        "recall": _safe_round(recall),
        "total_runs": total_runs,
        "crashes": crashes,
        "crash_rate": _safe_round(crash_rate),
    }


def build_reports(logs_dir: Path, out_dir: Path) -> None:
    analyzer = PerformanceAnalyzer(str(logs_dir))
    analyzer.collect_results()
    if analyzer.df is None or analyzer.df.empty:
        raise RuntimeError(f"No benchmark rows found in {logs_dir}")

    df = analyzer.df.copy()
    known = df[df["correctness_known"] == True].copy()  # noqa: E712

    rows = []
    for language_key in sorted(df["language"].unique()):
        rows.append(_compute_metrics(known, df, language_key))

    metrics_df = pd.DataFrame(rows)

    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_csv = out_dir / "baseline_language_metrics.csv"
    metrics_df.sort_values(["base_language", "tool", "language_key"]).to_csv(baseline_csv, index=False)

    # Build Graphene vs best competitor leaderboard per base language.
    gap_rows = []
    for lang in sorted(metrics_df["base_language"].unique()):
        lang_metrics = metrics_df[metrics_df["base_language"] == lang]
        g = lang_metrics[lang_metrics["tool"] == "graphene"]
        if g.empty:
            continue
        g_row = g.iloc[0]

        competitors = lang_metrics[lang_metrics["language_key"].str.startswith("competitor__")]
        if competitors.empty:
            best_name = ""
            best_acc = float("nan")
            gap = float("nan")
        else:
            best_idx = competitors["accuracy"].astype(float).idxmax()
            best_row = competitors.loc[best_idx]
            best_name = str(best_row["language_key"])
            best_acc = float(best_row["accuracy"])
            gap = float(g_row["accuracy"]) - best_acc

        gap_rows.append(
            {
                "language": lang,
                "graphene_key": str(g_row["language_key"]),
                "graphene_accuracy": _safe_round(float(g_row["accuracy"])),
                "graphene_precision": _safe_round(float(g_row["precision"])),
                "graphene_recall": _safe_round(float(g_row["recall"])),
                "graphene_fp": int(g_row["fp"]),
                "graphene_fn": int(g_row["fn"]),
                "graphene_crash_rate": _safe_round(float(g_row["crash_rate"])),
                "best_competitor_key": best_name,
                "best_competitor_accuracy": _safe_round(best_acc) if best_acc == best_acc else None,
                "accuracy_gap_vs_best_competitor": _safe_round(gap) if gap == gap else None,
            }
        )

    if gap_rows:
        leaderboard_df = pd.DataFrame(gap_rows).sort_values("language")
    else:
        leaderboard_df = pd.DataFrame(
            columns=[
                "language",
                "graphene_key",
                "graphene_accuracy",
                "graphene_precision",
                "graphene_recall",
                "graphene_fp",
                "graphene_fn",
                "graphene_crash_rate",
                "best_competitor_key",
                "best_competitor_accuracy",
                "accuracy_gap_vs_best_competitor",
            ]
        )
    leaderboard_csv = out_dir / "baseline_graphene_vs_best_competitor.csv"
    leaderboard_df.to_csv(leaderboard_csv, index=False)

    # Step 2: Graphene miss buckets.
    graphene_miss = known[
        (known["language"].str.startswith("graphene__"))
        & (known["correctness_label"].isin(["fp", "fn"]))
    ].copy()

    bucket_rows = []
    for _, row in graphene_miss.iterrows():
        source = analyzer._resolve_source_from_target(str(row["language"]), str(row["target"]))
        bucket = _bucket_from_source(source, str(row["target"]))
        bucket_rows.append(
            {
                "language": _base_language(str(row["language"])),
                "language_key": str(row["language"]),
                "error_type": str(row["correctness_label"]),
                "bucket": bucket,
                "target": str(row["target"]),
                "session": str(row["session"]),
            }
        )

    miss_raw_df = pd.DataFrame(bucket_rows)
    miss_raw_csv = out_dir / "graphene_miss_cases_raw.csv"
    miss_raw_df.to_csv(miss_raw_csv, index=False)

    if not miss_raw_df.empty:
        grouped = (
            miss_raw_df.groupby(["language", "error_type", "bucket"])
            .agg(
                count=("bucket", "size"),
                sample_target=("target", "first"),
            )
            .reset_index()
            .sort_values(["language", "count"], ascending=[True, False])
        )

        top10 = grouped.groupby("language", group_keys=False).head(10)
    else:
        top10 = pd.DataFrame(columns=["language", "error_type", "bucket", "count", "sample_target"])

    top10_csv = out_dir / "graphene_error_buckets_top10.csv"
    top10.to_csv(top10_csv, index=False)

    # Markdown summary for quick review.
    md_lines = []
    md_lines.append("# Baseline Accuracy And Error Buckets")
    md_lines.append("")
    md_lines.append(f"Generated from logs: {logs_dir}")
    md_lines.append("")
    md_lines.append("## Graphene Vs Best Competitor")
    md_lines.append("")
    if leaderboard_df.empty:
        md_lines.append("No Graphene rows found.")
    else:
        md_lines.append("| Language | Graphene Acc | Best Competitor Acc | Gap | Graphene FP | Graphene FN |")
        md_lines.append("|---|---:|---:|---:|---:|---:|")
        for _, r in leaderboard_df.iterrows():
            md_lines.append(
                f"| {r['language']} | {r['graphene_accuracy']} | {r['best_competitor_accuracy']} | {r['accuracy_gap_vs_best_competitor']} | {r['graphene_fp']} | {r['graphene_fn']} |"
            )

    md_lines.append("")
    md_lines.append("## Top Graphene Miss Buckets")
    md_lines.append("")
    if top10.empty:
        md_lines.append("No Graphene FP/FN buckets found.")
    else:
        md_lines.append("| Language | Error Type | Bucket | Count | Sample Target |")
        md_lines.append("|---|---|---|---:|---|")
        for _, r in top10.iterrows():
            md_lines.append(
                f"| {r['language']} | {r['error_type']} | {r['bucket']} | {int(r['count'])} | {r['sample_target']} |"
            )

    summary_md = out_dir / "baseline_and_buckets.md"
    summary_md.write_text("\n".join(md_lines), encoding="utf-8")

    print("Wrote:")
    print(f"- {baseline_csv}")
    print(f"- {leaderboard_csv}")
    print(f"- {miss_raw_csv}")
    print(f"- {top10_csv}")
    print(f"- {summary_md}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build baseline leaderboard and Graphene miss buckets")
    parser.add_argument("--logs-dir", default="artifacts/logs/comparison", help="Combined logs directory")
    parser.add_argument("--out-dir", default="comparison_dashboard", help="Output directory")
    args = parser.parse_args()

    logs_dir = Path(args.logs_dir)
    out_dir = Path(args.out_dir)
    build_reports(logs_dir, out_dir)


if __name__ == "__main__":
    main()
