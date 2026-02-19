#!/usr/bin/env python3
"""
Quick demo of escape detection accuracy.
Tests a selection of simple cases to show detection rates.
"""

import subprocess
import json
import sys
from pathlib import Path
from collections import defaultdict


def test_python_escape(func_name, module_name):
    """Test a Python escape function"""
    try:
        result = subprocess.run(
            ["uv", "run", "graphene", "analyze", 
             f"tests/python/{module_name}.py:{func_name}",
             "--repeat", "1", "--timeout", "3"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent
        )
        
        # Check for escape detection in output
        output_lower = result.stdout.lower() + result.stderr.lower()
        detected = ("detected: true" in output_lower or 
                   "genuine_escapes" in result.stdout and "1" in result.stdout or
                   "escapes" in output_lower and "1" in output_lower)
        
        return detected
    except Exception as e:
        print(f"    Error: {e}", file=sys.stderr)
        return None


def test_nodejs_escape(func_name, module_name):
    """Test a Node.js escape function"""
    try:
        request = {
            "session_id": f"test_{func_name}",
            "language": "javascript",
            "target": f"tests/nodejs/{module_name}.js:{func_name}",
            "inputs": ["test"],
            "repeat": 1,
            "timeout_seconds": 3
        }
        
        result = subprocess.run(
            ["node", "analyzers/nodejs/analyzer_bridge.js"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=15,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            response = json.loads(result.stdout)
            escapes = response.get("summary", {}).get("escapes", 0)
            detected = escapes > 0
        except:
            detected = "escape" in result.stdout.lower()
        
        return detected
    except Exception as e:
        print(f"    Error: {e}", file=sys.stderr)
        return None


# Test suite: (function, module, should_detect, language)
TESTS = [
    # Python - Should Detect Escapes
    ("spawn_non_daemon_thread", "escape_threads", True, "python"),
    ("spawn_process", "escape_process", True, "python"),
    ("spawn_thread_via_function_ref", "advanced_escapes", True, "python"),
    ("spawn_thread_conditionally", "advanced_escapes", True, "python"),
    ("spawn_thread_with_dynamic_key", "advanced_escapes", True, "python"),
    ("leak_executor_on_exception", "advanced_escapes", True, "python"),
    
    # Python - Should NOT Detect (Clean Code)
    ("join_thread", "no_escape", False, "python"),
    ("properly_joined_thread", "advanced_escapes", False, "python"),
    ("properly_shutdown_executor", "advanced_escapes", False, "python"),
    ("daemon_thread_cleanup", "advanced_escapes", False, "python"),
    
    # Node.js - Should Detect Escapes
    ("createLeakingInterval", "escape_async", True, "javascript"),
    ("createPromiseViaFactory", "advanced_escapes", True, "javascript"),
    ("hideAsyncInArray", "advanced_escapes", True, "javascript"),
    ("leakAsyncConditionally", "advanced_escapes", True, "javascript"),
    
    # Node.js - Should NOT Detect (Clean Code)
    ("clearIntervalSafely", "no_escape_async", False, "javascript"),
    ("properlyAwaitTimeout", "advanced_escapes", False, "javascript"),
    ("properlyShutdownInterval", "advanced_escapes", False, "javascript"),
]


def main():
    print("=" * 70)
    print("ESCAPE DETECTION SUCCESS RATE QUICK TEST")
    print("=" * 70)
    
    results = defaultdict(lambda: {"correct": 0, "total": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0})
    
    # Python tests
    print("\n🐍 Python Tests:")
    print("-" * 70)
    for func, module, should_detect, lang in TESTS:
        if lang != "python":
            continue
        
        print(f"  {func:35} ", end="", flush=True)
        detected = test_python_escape(func, module)
        
        if detected is None:
            print("❌ ERROR")
            continue
        
        is_correct = detected == should_detect
        results[lang]["total"] += 1
        results[lang]["correct"] += int(is_correct)
        
        if should_detect and detected:
            results[lang]["tp"] += 1
            symbol = "✓"
        elif not should_detect and not detected:
            results[lang]["tn"] += 1
            symbol = "✓"
        elif should_detect and not detected:
            results[lang]["fn"] += 1
            symbol = "✗ (FN)"
        else:
            results[lang]["fp"] += 1
            symbol = "✗ (FP)"
        
        expected = "ESCAPE" if should_detect else "CLEAN"
        detected_str = "ESCAPE" if detected else "CLEAN"
        print(f"{symbol:8} {expected:8} -> {detected_str:8}")
    
    # Node.js tests
    print("\n⚡ Node.js Tests:")
    print("-" * 70)
    for func, module, should_detect, lang in TESTS:
        if lang != "javascript":
            continue
        
        print(f"  {func:35} ", end="", flush=True)
        detected = test_nodejs_escape(func, module)
        
        if detected is None:
            print("❌ ERROR")
            continue
        
        is_correct = detected == should_detect
        results[lang]["total"] += 1
        results[lang]["correct"] += int(is_correct)
        
        if should_detect and detected:
            results[lang]["tp"] += 1
            symbol = "✓"
        elif not should_detect and not detected:
            results[lang]["tn"] += 1
            symbol = "✓"
        elif should_detect and not detected:
            results[lang]["fn"] += 1
            symbol = "✗ (FN)"
        else:
            results[lang]["fp"] += 1
            symbol = "✗ (FP)"
        
        expected = "ESCAPE" if should_detect else "CLEAN"
        detected_str = "ESCAPE" if detected else "CLEAN"
        print(f"{symbol:8} {expected:8} -> {detected_str:8}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n{'Language':15} {'Correct':10} {'Total':8} {'Accuracy':10} {'TP':4} {'TN':4} {'FP':4} {'FN':4}")
    print("-" * 70)
    
    total_correct = 0
    total_tests = 0
    total_tp = 0
    total_tn = 0
    total_fp = 0
    total_fn = 0
    
    for lang in ["python", "javascript"]:
        if results[lang]["total"] == 0:
            continue
        
        correct = results[lang]["correct"]
        total = results[lang]["total"]
        accuracy = (correct / total * 100) if total > 0 else 0
        tp = results[lang]["tp"]
        tn = results[lang]["tn"]
        fp = results[lang]["fp"]
        fn = results[lang]["fn"]
        
        print(f"{lang:15} {correct:10} {total:8} {accuracy:9.1f}% {tp:4} {tn:4} {fp:4} {fn:4}")
        
        total_correct += correct
        total_tests += total
        total_tp += tp
        total_tn += tn
        total_fp += fp
        total_fn += fn
    
    if total_tests > 0:
        total_accuracy = (total_correct / total_tests * 100)
        print("-" * 70)
        print(f"{'TOTAL':15} {total_correct:10} {total_tests:8} {total_accuracy:9.1f}% {total_tp:4} {total_tn:4} {total_fp:4} {total_fn:4}")
    
    print("\n" + "=" * 70)
    print("LEGEND:")
    print("  ✓ = Correct classification")
    print("  ✗ (FP) = False Positive (should be CLEAN, detected ESCAPE)")
    print("  ✗ (FN) = False Negative (should be ESCAPE, detected CLEAN)")
    print("  TP = True Positives, TN = True Negatives")
    print("  FP = False Positives, FN = False Negatives")
    print("=" * 70)


if __name__ == "__main__":
    main()
