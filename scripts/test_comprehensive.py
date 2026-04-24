#!/usr/bin/env python3
"""
Comprehensive static-analyzer validation against split Python case files.
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


def all_cases(root: Path):
    return sorted((root / "tests" / "python" / "cases").glob("case_*.py"))


def category_from_case(file_path: Path) -> str:
    parts = file_path.stem.split("_", 2)
    if len(parts) < 3:
        return "internal"
    slug = parts[2]
    if slug.startswith("_"):
        return "internal"
    return slug.split("_", 1)[0] or "internal"


def main():
    root = Path(__file__).resolve().parents[1]
    analyze_file = load_analyze_file(root)
    cases = all_cases(root)

    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    by_category = defaultdict(lambda: {"total": 0, "correct": 0})
    failures = []

    print("=" * 88)
    print(f"COMPREHENSIVE SPLIT-CASE ANALYZER TEST ({len(cases)} CASES)")
    print("=" * 88)

    for idx, case_file in enumerate(cases, 1):
        function_name = case_file.stem
        expected = expected_escape(case_file)
        result = analyze_file(case_file.as_posix(), function_name)
        detected = len(result.get("escapes", [])) > 0

        category = category_from_case(case_file)
        by_category[category]["total"] += 1

        if expected and detected:
            bucket = "tp"
            ok = True
        elif not expected and not detected:
            bucket = "tn"
            ok = True
        elif expected and not detected:
            bucket = "fn"
            ok = False
        else:
            bucket = "fp"
            ok = False

        counts[bucket] += 1
        by_category[category]["correct"] += int(ok)

        expected_label = "ESCAPE" if expected else "SAFE"
        detected_label = "ESCAPE" if detected else "SAFE"
        status = "PASS" if ok else "FAIL"

        print(f"[{idx:03d}/{len(cases):03d}] {function_name:36} {status:4} expected={expected_label:6} actual={detected_label:6}")

        if not ok:
            failures.append((function_name, expected_label, detected_label, category))

    total = sum(counts.values())
    accuracy = ((counts["tp"] + counts["tn"]) / total) if total else 0.0
    precision = (counts["tp"] / (counts["tp"] + counts["fp"])) if (counts["tp"] + counts["fp"]) else 0.0
    recall = (counts["tp"] / (counts["tp"] + counts["fn"])) if (counts["tp"] + counts["fn"]) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    print("\n" + "=" * 88)
    print("SUMMARY")
    print("=" * 88)
    print(f"Total: {total}")
    print(f"TP: {counts['tp']}  TN: {counts['tn']}  FP: {counts['fp']}  FN: {counts['fn']}")
    print(f"Accuracy:  {accuracy:.1%}")
    print(f"Precision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")
    print(f"F1-score:  {f1:.3f}")

    print("\nCategory accuracy:")
    for category in sorted(by_category):
        subtotal = by_category[category]["total"]
        correct = by_category[category]["correct"]
        pct = (correct / subtotal) if subtotal else 0.0
        print(f"- {category:12} {correct:3}/{subtotal:3} ({pct:.1%})")

    if failures:
        print("\nFailures:")
        for name, expected_label, detected_label, category in failures[:20]:
            print(f"- {name} [{category}] expected={expected_label}, actual={detected_label}")
        if len(failures) > 20:
            print(f"- ... and {len(failures) - 20} more")


if __name__ == "__main__":
    main()
