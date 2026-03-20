#!/usr/bin/env python3
"""
Direct split-case measurement using the Python function test harness.
"""

from __future__ import annotations

import argparse
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
    module_name = f"split_case_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module for {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)


def collect_cases(root: Path, limit: int):
    cases_dir = root / "tests" / "python" / "cases"
    collected = []
    for file_path in sorted(cases_dir.glob("case_*.py")):
        match = CASE_RE.match(file_path.name)
        if not match:
            continue
        collected.append(
            CaseDef(
                file_path=file_path,
                function_name=file_path.stem,
                expected_escape=expected_escape(file_path),
            )
        )
        if limit and len(collected) >= limit:
            break
    return collected


def run_case(case: CaseDef):
    fn = load_case_function(case.file_path, case.function_name)
    harness = PythonFunctionTestHarness(fn, timeout=3.0, prefer_main_thread=False)
    result = harness.run_test("sample")
    detected = bool(result.escape_detected or (result.error and "timeout" in result.error.lower()))
    return detected, result.error or ""


def main():
    parser = argparse.ArgumentParser(description="Direct harness measurement for split Python cases")
    parser.add_argument("--limit", type=int, default=20, help="How many cases to test (default: 20)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    cases = collect_cases(root, args.limit)

    print("=" * 78)
    print(f"DIRECT HARNESS MEASUREMENT ({len(cases)} CASES)")
    print("=" * 78)

    tp = tn = fp = fn = 0

    for idx, case in enumerate(cases, 1):
        print(f"[{idx:02d}/{len(cases):02d}] {case.function_name:36}", end=" ", flush=True)
        detected, error = run_case(case)

        if error and "timeout" not in error.lower():
            print(f"ERROR ({error})")
            continue

        expected = case.expected_escape
        if expected and detected:
            tp += 1
            status = "TP"
            ok = "PASS"
        elif not expected and not detected:
            tn += 1
            status = "TN"
            ok = "PASS"
        elif expected and not detected:
            fn += 1
            status = "FN"
            ok = "FAIL"
        else:
            fp += 1
            status = "FP"
            ok = "FAIL"

        expected_label = "ESCAPE" if expected else "SAFE"
        actual_label = "ESCAPE" if detected else "SAFE"
        print(f"{ok:4} [{status}] expected={expected_label:6} actual={actual_label:6}")

    total = tp + tn + fp + fn
    accuracy = ((tp + tn) / total) if total else 0.0
    precision = (tp / (tp + fp)) if (tp + fp) else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) else 0.0

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"Total: {total}")
    print(f"TP: {tp}  TN: {tn}  FP: {fp}  FN: {fn}")
    print(f"Accuracy:  {accuracy:.1%}")
    print(f"Precision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")


if __name__ == "__main__":
    main()
