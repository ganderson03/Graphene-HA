#!/usr/bin/env python3
"""Build a combined Graphene vs competitor dashboard using existing plot style."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analyze_performance import PerformanceAnalyzer  # noqa: E402


def copy_logs_with_prefix(src_root: Path, dst_root: Path, prefix: str) -> None:
    if not src_root.exists():
        return

    for lang_dir in sorted(src_root.iterdir()):
        if not lang_dir.is_dir():
            continue
        target_name = f"{prefix}__{lang_dir.name}"
        target_dir = dst_root / target_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(lang_dir, target_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Graphene vs competitor dashboard")
    parser.add_argument("--graphene-logs", default="logs/graphene", help="Graphene logs dir (default: logs/graphene)")
    parser.add_argument("--graphene-static-logs", default="logs/graphene_static", help="Graphene static-only logs dir (default: logs/graphene_static)")
    parser.add_argument("--graphene-dynamic-logs", default="logs/graphene_dynamic", help="Graphene dynamic-only logs dir (default: logs/graphene_dynamic)")
    parser.add_argument("--competitor-logs", default="logs/competitors", help="Competitor logs dir (default: logs/competitors)")
    parser.add_argument("--oss-logs", default="logs/oss_bench", help="OSS Graphene logs dir (default: logs/oss_bench)")
    parser.add_argument("--combined-logs", default="logs/comparison", help="Temporary combined logs dir (default: logs/comparison)")
    parser.add_argument("--output-dir", default="comparison_dashboard", help="Dashboard output folder (default: comparison_dashboard)")
    args = parser.parse_args()

    graphene_logs = (ROOT / args.graphene_logs).resolve()
    graphene_static_logs = (ROOT / args.graphene_static_logs).resolve()
    graphene_dynamic_logs = (ROOT / args.graphene_dynamic_logs).resolve()
    competitor_logs = (ROOT / args.competitor_logs).resolve()
    oss_logs = (ROOT / args.oss_logs).resolve()
    combined_logs = (ROOT / args.combined_logs).resolve()
    output_dir = (ROOT / args.output_dir).resolve()

    if combined_logs.exists():
        shutil.rmtree(combined_logs)
    combined_logs.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_logs_with_prefix(graphene_logs, combined_logs, "graphene")
    copy_logs_with_prefix(graphene_static_logs, combined_logs, "graphene_static")
    copy_logs_with_prefix(graphene_dynamic_logs, combined_logs, "graphene_dynamic")
    copy_logs_with_prefix(competitor_logs, combined_logs, "competitor")
    copy_logs_with_prefix(oss_logs, combined_logs, "oss")

    # Run existing dashboard generator from output directory so generated plots/html
    # are grouped together and don't overwrite root-level files.
    prev_cwd = Path.cwd()
    try:
        import os

        os.chdir(output_dir)
        analyzer = PerformanceAnalyzer(logs_dir=str(combined_logs))
        analyzer.run()
    finally:
        os.chdir(prev_cwd)

    print("\nDashboard generated in:", output_dir)
    print("Open:", output_dir / "performance_dashboard.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
