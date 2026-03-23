#!/usr/bin/env python3
"""Run Graphene + competitor benchmarks and build one HTML dashboard.

This wraps the existing workflow scripts into one command.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_step(cmd: list[str], title: str) -> int:
    print(f"\n=== {title} ===")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Graphene + native and heuristic escape detectors and generate comparison HTML dashboard"
    )
    parser.add_argument("--generate", type=int, default=1, help="Graphene input count per test (default: 1)")
    parser.add_argument("--competitor-limit", type=int, default=100, help="Competitor cases per language (default: 100)")
    parser.add_argument("--oss-per-project", type=int, default=25, help="OSS sampled functions per project (default: 25)")
    parser.add_argument("--oss-timeout", type=float, default=7.0, help="OSS per-target timeout seconds (default: 7.0)")
    parser.add_argument("--graphene-logs", default="logs", help="Graphene log directory (default: logs)")
    parser.add_argument("--competitor-logs", default="logs_competitors_escape", help="Competitor log directory (default: logs_competitors_escape)")
    parser.add_argument("--oss-logs", default="logs_oss_bench", help="OSS Graphene log directory (default: logs_oss_bench)")
    parser.add_argument("--combined-logs", default="logs_comparison", help="Combined log directory (default: logs_comparison)")
    parser.add_argument("--output-dir", default="comparison_dashboard", help="Dashboard output directory (default: comparison_dashboard)")
    parser.add_argument("--skip-oss", action="store_true", help="Skip OSS benchmark sampling step")
    args = parser.parse_args()

    py = sys.executable

    graphene_cmd = [
        py,
        str(ROOT / "graphene_ha" / "cli.py"),
        "run-all",
        "--generate",
        str(args.generate),
        "--log-dir",
        args.graphene_logs,
    ]

    competitors_cmd = [
        py,
        str(ROOT / "scripts" / "collect_competitor_benchmarks.py"),
        "--log-dir",
        args.competitor_logs,
        "--limit",
        str(args.competitor_limit),
    ]

    oss_cmd = [
        py,
        str(ROOT / "scripts" / "run_open_source_benchmarks.py"),
        "--per-project",
        str(args.oss_per_project),
        "--timeout",
        str(args.oss_timeout),
        "--log-dir",
        args.oss_logs,
    ]

    dashboard_cmd = [
        py,
        str(ROOT / "scripts" / "build_comparison_dashboard.py"),
        "--graphene-logs",
        args.graphene_logs,
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
    print(f"Open: {ROOT / args.output_dir / 'performance_dashboard.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
