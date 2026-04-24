#!/usr/bin/env python3
"""
Static analyzer accuracy check on split Python case files.
"""

from __future__ import annotations

import importlib.util
from collections import defaultdict
from pathlib import Path


def load_analyze_file(root: Path):
    analyzer_path = root / "analyzers" / "python" / "static_analyzer.py"
    spec = importlib.util.spec_from_file_location("static_analyzer", analyzer_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load analyzer from {analyzer_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.analyze_file


def expected_escape(file_path: Path) -> bool:
    return "SAFE:" not in file_path.read_text(encoding="utf-8")


def sample_cases(limit: int = 20):
    root = Path(__file__).resolve().parents[1]
    cases = sorted((root / "tests" / "python" / "cases").glob("case_*.py"))
    for file_path in cases[:limit]:
        yield file_path


def main():
    root = Path(__file__).resolve().parents[1]
    analyze_file = load_analyze_file(root)
    results = defaultdict(lambda: {"pass": 0, "fail": 0})

    print("=" * 80)
    print("DIRECT ANALYZER SPLIT-CASE ACCURACY")
    print("=" * 80)
    print(f"{'Case':42} {'Expected':10} {'Detected':10} {'Result':8}")
    print("-" * 80)

    total = 0
    passed = 0

    for case_file in sample_cases(limit=20):
        function_name = case_file.stem
        expected = expected_escape(case_file)
        analysis = analyze_file(str(case_file.as_posix()), function_name)
        detected = len(analysis.get("escapes", [])) > 0
        ok = expected == detected

        expected_label = "ESCAPE" if expected else "SAFE"
        detected_label = "ESCAPE" if detected else "SAFE"
        result_label = "PASS" if ok else "FAIL"

        print(f"{function_name:42} {expected_label:10} {detected_label:10} {result_label:8}")

        bucket = "escaped" if expected else "safe"
        results[bucket]["pass" if ok else "fail"] += 1
        total += 1
        passed += int(ok)

    accuracy = (passed / total) if total else 0.0

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Overall: {passed}/{total} ({accuracy:.1%})")
    for bucket in ("escaped", "safe"):
        b = results[bucket]
        subtotal = b["pass"] + b["fail"]
        if subtotal:
            print(f"{bucket.upper():8}: {b['pass']}/{subtotal} ({(b['pass'] / subtotal):.1%})")


if __name__ == "__main__":
    main()
