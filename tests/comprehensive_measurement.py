#!/usr/bin/env python3
"""
Comprehensive split-case measurement using the Python function harness.
"""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphene_ha.test_harness import PythonFunctionTestHarness


CASE_RE = re.compile(r"^case_(\d{3})_(.+)\.py$")


@dataclass
class CaseDef:
    file_path: Path
    function_name: str
    expected_escape: bool


def expected_escape(file_path: Path) -> bool:
    return "SAFE:" not in file_path.read_text(encoding="utf-8")


def load_case_function(file_path: Path, function_name: str):
    module_name = f"full_split_case_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module for {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)


def collect_cases(root: Path):
    cases_dir = root / "tests" / "python" / "cases"
    collected = []
    for file_path in sorted(cases_dir.glob("case_*.py")):
        if not CASE_RE.match(file_path.name):
            continue
        collected.append(
            CaseDef(
                file_path=file_path,
                function_name=file_path.stem,
                expected_escape=expected_escape(file_path),
            )
        )
    return collected


def run_case(case: CaseDef):
    fn = load_case_function(case.file_path, case.function_name)
    harness = PythonFunctionTestHarness(fn, timeout=3.0, prefer_main_thread=False)
    result = harness.run_test("sample")
    detected = bool(result.escape_detected or (result.error and "timeout" in result.error.lower()))
    return detected, result.error or ""


def classify(expected: bool, detected: bool) -> str:
    if expected and detected:
        return "tp"
    if not expected and not detected:
        return "tn"
    if expected and not detected:
        return "fn"
    return "fp"


def main():
    root = Path(__file__).resolve().parent.parent
    cases = collect_cases(root)

    print("=" * 82)
    print(f"COMPREHENSIVE SPLIT-CASE MEASUREMENT ({len(cases)} CASES)")
    print("=" * 82)

    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    failures = []

    for idx, case in enumerate(cases, 1):
        print(f"[{idx:03d}/{len(cases):03d}] {case.function_name:36}", end=" ", flush=True)
        detected, error = run_case(case)

        if error and "timeout" not in error.lower():
            print(f"ERROR ({error})")
            failures.append((case.function_name, "error", error))
            continue

        bucket = classify(case.expected_escape, detected)
        counts[bucket] += 1

        expected_label = "ESCAPE" if case.expected_escape else "SAFE"
        actual_label = "ESCAPE" if detected else "SAFE"
        ok = "PASS" if case.expected_escape == detected else "FAIL"
        print(f"{ok:4} [{bucket.upper()}] expected={expected_label:6} actual={actual_label:6}")

        if ok == "FAIL":
            failures.append((case.function_name, bucket.upper(), f"expected={expected_label}, actual={actual_label}"))

    total = sum(counts.values())
    accuracy = ((counts["tp"] + counts["tn"]) / total) if total else 0.0
    precision = (counts["tp"] / (counts["tp"] + counts["fp"])) if (counts["tp"] + counts["fp"]) else 0.0
    recall = (counts["tp"] / (counts["tp"] + counts["fn"])) if (counts["tp"] + counts["fn"]) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    print("\n" + "=" * 82)
    print("SUMMARY")
    print("=" * 82)
    print(f"Total: {total}")
    print(f"TP: {counts['tp']}  TN: {counts['tn']}  FP: {counts['fp']}  FN: {counts['fn']}")
    print(f"Accuracy:  {accuracy:.1%}")
    print(f"Precision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")
    print(f"F1-score:  {f1:.3f}")

    if failures:
        print("\nFailures:")
        for name, kind, detail in failures[:20]:
            print(f"- {name}: {kind} ({detail})")
        if len(failures) > 20:
            print(f"- ... and {len(failures) - 20} more")


if __name__ == "__main__":
    main()
