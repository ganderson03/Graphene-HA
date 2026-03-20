#!/usr/bin/env python3
"""
Quick smoke test for the split 100-case suites.

This script samples a few Python and Node.js cases and reports classifier accuracy.
"""

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


WORKSPACE = Path(__file__).parent.parent

# (language, target_file, function_name, should_detect_escape)
TESTS = [
    ("python", "tests/python/cases/case_001_cache_profile.py", "case_001_cache_profile", True),
    ("python", "tests/python/cases/case_005_cache_ticket.py", "case_005_cache_ticket", False),
    ("python", "tests/python/cases/case_014_publish_shipment.py", "case_014_publish_shipment", True),
    ("python", "tests/python/cases/case_020_stage_ledger.py", "case_020_stage_ledger", False),
    ("javascript", "tests/nodejs/cases/case_001_cache_profile.js", "case001CacheProfile", True),
    ("javascript", "tests/nodejs/cases/case_005_cache_ticket.js", "case005CacheTicket", False),
    ("javascript", "tests/nodejs/cases/case_014_publish_shipment.js", "case014PublishShipment", True),
    ("javascript", "tests/nodejs/cases/case_020_stage_ledger.js", "case020StageLedger", False),
]


def detect_python_escape(target_file: str, function_name: str):
    target = f"{target_file}:{function_name}"
    try:
        result = subprocess.run(
            ["uv", "run", "graphene", "analyze", target, "--repeat", "1", "--timeout", "3"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
            cwd=WORKSPACE,
        )
    except Exception as exc:
        print(f"python error for {target}: {exc}", file=sys.stderr)
        return None

    output = f"{result.stdout}\n{result.stderr}".lower()
    return "detected: true" in output or "escapes" in output and "1" in output


def detect_node_escape(target_file: str, function_name: str):
    target = f"{target_file}:{function_name}"
    request = {
        "session_id": f"quick_{function_name}",
        "language": "javascript",
        "target": target,
        "inputs": ["sample"],
        "repeat": 1,
        "timeout_seconds": 3,
    }

    try:
        result = subprocess.run(
            ["node", "analyzers/nodejs/analyzer_bridge.js"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
            cwd=WORKSPACE,
        )
    except Exception as exc:
        print(f"node error for {target}: {exc}", file=sys.stderr)
        return None

    try:
        response = json.loads(result.stdout)
        return response.get("summary", {}).get("escapes", 0) > 0
    except Exception:
        output = f"{result.stdout}\n{result.stderr}".lower()
        return "escape" in output and "0" not in output


def update_counts(bucket, expected, detected):
    if expected and detected:
        bucket["tp"] += 1
    elif not expected and not detected:
        bucket["tn"] += 1
    elif expected and not detected:
        bucket["fn"] += 1
    else:
        bucket["fp"] += 1


def main():
    print("=" * 72)
    print("SPLIT-CASE QUICK TEST")
    print("=" * 72)

    stats = defaultdict(lambda: {"total": 0, "correct": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0})

    for language, target_file, function_name, expected in TESTS:
        label = f"{function_name} ({language})"
        print(f"{label:50}", end=" ", flush=True)

        if language == "python":
            detected = detect_python_escape(target_file, function_name)
        else:
            detected = detect_node_escape(target_file, function_name)

        if detected is None:
            print("ERROR")
            continue

        ok = detected == expected
        stats[language]["total"] += 1
        stats[language]["correct"] += int(ok)
        update_counts(stats[language], expected, detected)

        expected_s = "ESCAPE" if expected else "SAFE"
        actual_s = "ESCAPE" if detected else "SAFE"
        outcome = "PASS" if ok else "FAIL"
        print(f"{outcome:4} expected={expected_s:6} actual={actual_s:6}")

    print("\n" + "=" * 72)
    print(f"{'Language':12} {'Correct':>7} {'Total':>7} {'Accuracy':>10} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4}")
    print("-" * 72)

    total_correct = 0
    total_cases = 0
    total = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}

    for language in ("python", "javascript"):
        bucket = stats[language]
        if bucket["total"] == 0:
            continue
        accuracy = 100.0 * bucket["correct"] / bucket["total"]
        print(
            f"{language:12} {bucket['correct']:7} {bucket['total']:7} {accuracy:9.1f}%"
            f" {bucket['tp']:4} {bucket['tn']:4} {bucket['fp']:4} {bucket['fn']:4}"
        )
        total_correct += bucket["correct"]
        total_cases += bucket["total"]
        for key in total:
            total[key] += bucket[key]

    if total_cases:
        accuracy = 100.0 * total_correct / total_cases
        print("-" * 72)
        print(
            f"{'TOTAL':12} {total_correct:7} {total_cases:7} {accuracy:9.1f}%"
            f" {total['tp']:4} {total['tn']:4} {total['fp']:4} {total['fn']:4}"
        )


if __name__ == "__main__":
    main()
