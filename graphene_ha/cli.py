#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent




def _ensure_rust_binary():
    """Build Rust workspace if it doesn't exist."""
    binary_name = "graphene-ha.exe" if os.name == "nt" else "graphene-ha"
    binary_path = ROOT_DIR / "target" / "release" / binary_name
    
    # Also check for rust-analyzer which is in the workspace
    rust_analyzer_name = "rust-analyzer.exe" if os.name == "nt" else "rust-analyzer"
    rust_analyzer_path = ROOT_DIR / "target" / "release" / rust_analyzer_name
    
    if not binary_path.exists() or not rust_analyzer_path.exists():
        print(f"Building Rust workspace (first time only)...", file=sys.stderr)
        result = subprocess.run(
            ["cargo", "build", "--release", "--workspace"],
            cwd=ROOT_DIR,
            check=False
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to build Rust workspace. Run 'cargo build --release --workspace' manually.")
        if not binary_path.exists():
            raise FileNotFoundError(f"Build succeeded but binary not found: {binary_path}")
        if not rust_analyzer_path.exists():
            raise FileNotFoundError(f"Build succeeded but rust-analyzer not found: {rust_analyzer_path}")
    
    return binary_path


def _run_analyze(args):
    """Delegate analyze command to Rust binary."""
    binary_path = _ensure_rust_binary()
    
    cmd = [str(binary_path), "analyze", "--target", args.target]
    
    for inp in args.input:
        cmd.extend(["--input", inp])
    
    cmd.extend(["--repeat", str(args.repeat)])
    cmd.extend(["--timeout", str(args.timeout)])
    cmd.extend(["--output-dir", args.log_dir])
    
    if args.language:
        cmd.extend(["--language", args.language])
    
    if hasattr(args, "analysis_mode"):
        cmd.extend(["--analysis-mode", args.analysis_mode])
    
    if args.verbose:
        cmd.append("--verbose")
    
    result = subprocess.run(cmd, check=False)
    return result.returncode


def _run_run_all(args):
    """Delegate run-all command to Rust binary."""
    binary_path = _ensure_rust_binary()
    
    cmd = [
        str(binary_path),
        "run-all",
        "--test-dir",
        str(ROOT_DIR / "tests"),
        "--generate",
        str(args.generate),
        "--output-dir",
        args.log_dir,
    ]
    
    if args.language:
        cmd.extend(["--language", args.language])
    
    result = subprocess.run(cmd, check=False)
    return result.returncode


def _run_list(args):
    """Delegate list command to Rust binary."""
    binary_path = _ensure_rust_binary()
    
    cmd = [str(binary_path), "list"]
    
    if args.detailed:
        cmd.append("--detailed")
    
    result = subprocess.run(cmd, check=False)
    return result.returncode


def _run_clear(args):
    """Delegate clear command to Rust binary."""
    binary_path = _ensure_rust_binary()
    
    cmd = [str(binary_path), "clear", "--output-dir", args.log_dir]
    
    if args.archive_csv:
        cmd.extend(["--archive-csv", args.archive_csv])
    
    result = subprocess.run(cmd, check=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        prog="graphene",
        description="Multi-language object escape analysis with unified orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog="""Examples:
      uv run graphene analyze my_module:my_function --input "hello" --repeat 3
      uv run graphene analyze tests/python/cases/case_001_cache_profile.py:case_001_cache_profile --input "test"
  uv run graphene run-all --language python
  uv run graphene run-all --generate 10
  uv run graphene list --detailed
  uv run graphene clear --log-dir logs
  uv run graphene clear --log-dir logs --archive-csv logs/cleared_results.csv
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a function for object escapes")
    analyze_parser.add_argument("target", help="Function target in format: module:function or file.ext:function")
    analyze_parser.add_argument("--input", action="append", default=[], help="Input data for the function (repeatable)")
    analyze_parser.add_argument("--repeat", type=int, default=3, help="Repeat each input N times (default: 3)")
    analyze_parser.add_argument("--timeout", type=float, default=5.0, help="Timeout per execution in seconds (default: 5.0)")
    analyze_parser.add_argument("--log-dir", default="logs", help="Output directory for reports (default: logs)")
    analyze_parser.add_argument("--language", help="Language (python, java, javascript, go, rust). Auto-detected if not specified")
    analyze_parser.add_argument(
        "--analysis-mode",
        choices=["dynamic", "static", "both"],
        default="both",
        help="Analysis mode: dynamic, static, or both (default: both).",
    )
    analyze_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # Run-all command
    runall_parser = subparsers.add_parser("run-all", help="Run all test suites across languages")
    runall_parser.add_argument("--test-dir", default="tests", help="Root test directory (default: tests)")
    runall_parser.add_argument("--generate", type=int, default=10, help="Number of inputs to generate per test (default: 10)")
    runall_parser.add_argument("--log-dir", default="logs", help="Output directory for reports (default: logs)")
    runall_parser.add_argument("--language", help="Filter by language (python, java, javascript, go, rust)")
    runall_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available analyzers")
    list_parser.add_argument("--detailed", action="store_true", help="Show detailed analyzer capabilities")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear log output directories")
    clear_parser.add_argument("--log-dir", default="logs", help="Output directory for reports (default: logs)")
    clear_parser.add_argument("--archive-csv", help="Archive results into a single CSV file before clearing")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route all commands to Rust binary
    if args.command == "analyze":
        return _run_analyze(args)
    elif args.command == "run-all":
        return _run_run_all(args)
    elif args.command == "list":
        return _run_list(args)
    elif args.command == "clear":
        return _run_clear(args)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
