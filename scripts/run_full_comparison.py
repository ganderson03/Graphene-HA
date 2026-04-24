#!/usr/bin/env python3
"""Run Graphene + competitor benchmarks and build one HTML dashboard.

This wraps the existing workflow scripts into one command.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_step(cmd: list[str], title: str) -> int:
    print(f"\n=== {title} ===")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
    return proc.returncode


def _graphene_run_all_cmd(py_exe: str, generate: int, log_dir: str, analysis_mode: str) -> list[str]:
    return [
        py_exe,
        str(ROOT / "graphene_ha" / "cli.py"),
        "run-all",
        "--generate",
        str(generate),
        "--log-dir",
        log_dir,
        "--analysis-mode",
        analysis_mode,
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Graphene + native and heuristic escape detectors and generate comparison HTML dashboard"
    )
    parser.add_argument("--generate", type=int, default=10, help="Graphene input count per test (default: 10; use 1 for quick test)")
    parser.add_argument("--competitor-limit", type=int, default=10, help="Competitor cases per language (default: 10; use 5 for quick test; 0 for all)")
    parser.add_argument("--oss-per-project", type=int, default=10, help="OSS sampled functions per project (default: 10; use 2 for quick test; 0 for all)")
    parser.add_argument("--oss-timeout", type=float, default=5.0, help="OSS per-target timeout seconds (default: 5.0)")
    parser.add_argument(
        "--oss-report",
        default="benchmarks/oss_benchmark_report.csv",
        help="OSS benchmark CSV report path (default: benchmarks/oss_benchmark_report.csv)",
    )
    parser.add_argument("--graphene-logs", default="artifacts/logs/graphene", help="Graphene BOTH-mode log directory (default: artifacts/logs/graphene)")
    parser.add_argument("--graphene-static-logs", default="artifacts/logs/graphene_static", help="Graphene STATIC-mode log directory (default: artifacts/logs/graphene_static)")
    parser.add_argument("--graphene-dynamic-logs", default="artifacts/logs/graphene_dynamic", help="Graphene DYNAMIC-mode log directory (default: artifacts/logs/graphene_dynamic)")
    parser.add_argument("--competitor-logs", default="artifacts/logs/competitors_escape", help="Competitor log directory (default: artifacts/logs/competitors_escape)")
    parser.add_argument("--oss-logs", default="artifacts/logs/oss_bench", help="OSS Graphene log directory (default: artifacts/logs/oss_bench)")
    parser.add_argument("--combined-logs", default="artifacts/logs/comparison", help="Combined log directory (default: artifacts/logs/comparison)")
    parser.add_argument("--output-dir", default="comparison_dashboard", help="Dashboard output directory (default: comparison_dashboard)")
    parser.add_argument("--skip-oss", action="store_true", help="Skip OSS benchmark sampling step")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing logs/report before running the full pipeline",
    )
    args = parser.parse_args()

    py = sys.executable

    graphene_logs_path = ROOT / args.graphene_logs
    graphene_static_logs_path = ROOT / args.graphene_static_logs
    graphene_dynamic_logs_path = ROOT / args.graphene_dynamic_logs
    competitor_logs_path = ROOT / args.competitor_logs
    oss_logs_path = ROOT / args.oss_logs
    combined_logs_path = ROOT / args.combined_logs
    output_dir_path = ROOT / args.output_dir
    oss_report_path = ROOT / args.oss_report

    if args.clean:
        for path in [
            graphene_logs_path,
            graphene_static_logs_path,
            graphene_dynamic_logs_path,
            competitor_logs_path,
            oss_logs_path,
            combined_logs_path,
        ]:
            if path.exists():
                shutil.rmtree(path)
        if oss_report_path.exists():
            oss_report_path.unlink()

    graphene_cmd = _graphene_run_all_cmd(py, args.generate, args.graphene_logs, "both")
    graphene_static_cmd = _graphene_run_all_cmd(py, args.generate, args.graphene_static_logs, "static")
    graphene_dynamic_cmd = _graphene_run_all_cmd(py, args.generate, args.graphene_dynamic_logs, "dynamic")

    competitors_cmd = [
        py,
        str(ROOT / "scripts" / "collect_competitor_benchmarks.py"),
        "--log-dir",
        args.competitor_logs,
        "--limit",
        str(args.competitor_limit),
    ]
    if args.clean:
        competitors_cmd.append("--clean")

    oss_cmd = [
        py,
        str(ROOT / "scripts" / "run_open_source_benchmarks.py"),
        "--per-project",
        str(args.oss_per_project),
        "--timeout",
        str(args.oss_timeout),
        "--log-dir",
        args.oss_logs,
        "--report",
        args.oss_report,
    ]

    dashboard_cmd = [
        py,
        str(ROOT / "scripts" / "build_comparison_dashboard.py"),
        "--graphene-logs",
        args.graphene_logs,
        "--graphene-static-logs",
        args.graphene_static_logs,
        "--graphene-dynamic-logs",
        args.graphene_dynamic_logs,
        "--competitor-logs",
        args.competitor_logs,
        "--oss-logs",
        args.oss_logs,
        "--combined-logs",
        args.combined_logs,
        "--output-dir",
        args.output_dir,
    ]

    rc = run_step(graphene_cmd, "Graphene Baseline")
    if rc != 0:
        return rc

    rc = run_step(graphene_static_cmd, "Graphene Static-Only Baseline")
    if rc != 0:
        return rc

    rc = run_step(graphene_dynamic_cmd, "Graphene Dynamic-Only Baseline")
    if rc != 0:
        return rc

    rc = run_step(competitors_cmd, "Competitor Collection")
    if rc != 0:
        return rc

    if not args.skip_oss:
        rc = run_step(oss_cmd, "OSS Sampling")
        if rc != 0:
            return rc

    rc = run_step(dashboard_cmd, "Dashboard Build")
    if rc != 0:
        return rc

    print("\nDone.")
    print("Saved artifacts:")
    print(f"- Artificial test logs (Graphene, both): {graphene_logs_path}")
    print(f"- Artificial test logs (Graphene, static): {graphene_static_logs_path}")
    print(f"- Artificial test logs (Graphene, dynamic): {graphene_dynamic_logs_path}")
    print(f"- Artificial test logs (Competitors): {competitor_logs_path}")
    if not args.skip_oss:
        print(f"- Open-source benchmark logs: {oss_logs_path}")
        print(f"- Open-source benchmark CSV: {oss_report_path}")
    print(f"- Combined logs feeding graphs: {combined_logs_path}")
    print(f"- Graph output directory: {output_dir_path}")
    print(f"Open: {output_dir_path / 'performance_dashboard.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
