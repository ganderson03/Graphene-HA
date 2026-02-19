#!/usr/bin/env python3
"""
Direct escape detection measurement (bypass CLI issues).
Tests detection by running harness directly.
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "python"))

from graphene_ha.test_harness import PythonFunctionTestHarness
from graphene_ha.vulnerability_detector import VulnerabilityDetector
from collections import defaultdict

# Import test modules
import escape_threads
import no_escape
import escape_process
import escape_executor
import escape_pool
import advanced_escapes


# Test definitions: (module, function_name, should_detect_escape, description)
PYTHON_TESTS = [
    # Basic escapes - should detect
    (escape_threads, "spawn_non_daemon_thread", True, "Basic thread spawn"),
    (escape_threads, "spawn_daemon_thread", True, "Daemon thread"),
    (escape_threads, "spawn_timer_thread", True, "Timer thread"),
    (escape_threads, "spawn_named_thread", True, "Named thread"),
    (escape_threads, "spawn_multiple_threads", True, "Multiple threads"),
    
    # Process escapes - should detect
    (escape_process, "spawn_process", True, "Basic process"),
    (escape_process, "spawn_daemon_process", True, "Daemon process"),
    
    # Executor escapes - should detect
    (escape_executor, "leak_executor", True, "Leaked executor"),
    (escape_executor, "leak_new_executor", True, "New executor leak"),
    
    # Non-escapes - should NOT detect
    (no_escape, "no_threads", False, "No threads"),
    (no_escape, "join_thread", False, "Joined thread"),
    (no_escape, "join_daemon_thread", False, "Joined daemon"),
    (no_escape, "join_multiple_threads", False, "Joined multiple"),
    
    # Advanced escapes - should detect
    (advanced_escapes, "spawn_thread_via_function_ref", True, "Obfuscated - function ref"),
    (advanced_escapes, "spawn_thread_conditionally", True, "Conditional spawn"),
    (advanced_escapes, "spawn_thread_with_dynamic_key", True, "Dynamic key storage"),
    (advanced_escapes, "spawn_thread_weak_reference", True, "Weak reference"),
    (advanced_escapes, "leak_executor_on_exception", True, "Executor on exception"),
    (advanced_escapes, "spawn_process_without_join", True, "Process without join"),
    (advanced_escapes, "leak_pool_incrementally", True, "Pool leak incrementally"),
    (advanced_escapes, "spawn_threads_recursively", True, "Recursive threads"),
    
    # Advanced non-escapes - should NOT detect
    (advanced_escapes, "properly_joined_thread", False, "Properly joined"),
    (advanced_escapes, "properly_shutdown_executor", False, "Properly shutdown"),
    (advanced_escapes, "daemon_thread_cleanup", False, "Daemon with cleanup"),
]


def run_test(module, func_name, should_detect, description):
    """Run a single test"""
    try:
        func = getattr(module, func_name)
        
        # Run test
        harness = PythonFunctionTestHarness(func, timeout=3.0, prefer_main_thread=False)
        result = harness.run_test("test_input")
        
        # Detect escape
        detected = result.escape_detected or (result.error and "timeout" in result.error.lower())
        
        return (detected, should_detect, detected == should_detect, None)
    except Exception as e:
        return (False, should_detect, False, str(e))


def main():
    print("=" * 75)
    print("ESCAPE DETECTION SUCCESS RATE ANALYSIS")
    print("=" * 75)
    
    stats = {
        "tp": 0,  # True Positive
        "tn": 0,  # True Negative
        "fp": 0,  # False Positive
        "fn": 0,  # False Negative
    }
    
    categories = defaultdict(lambda: {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0})
    
    print("\nRunning Tests:")
    print("-" * 75)
    
    for i, (module, func_name, should_detect, description) in enumerate(PYTHON_TESTS, 1):
        print(f"[{i:2d}/{len(PYTHON_TESTS):2d}]  {func_name:35} ", end="", flush=True)
        
        detected, expected, correct, error = run_test(module, func_name, should_detect, description)
        
        if error:
            print(f"❌ ERROR: {error[:40]}")
            continue
        
        # Classify result
        if expected and detected:
            result_type = "TP"
            stats["tp"] += 1
            symbol = "✓"
        elif not expected and not detected:
            result_type = "TN"
            stats["tn"] += 1
            symbol = "✓"
        elif expected and not detected:
            result_type = "FN"
            stats["fn"] += 1
            symbol = "✗"
        else:
            result_type = "FP"
            stats["fp"] += 1
            symbol = "✗"
        
        # Category tracking
        cat = "escape" if expected else "clean"
        categories[cat]["total"] += 1
        categories[cat][result_type.lower()] += 1
        
        expected_str = "ESCAPE" if expected else "CLEAN"
        detected_str = "ESCAPE" if detected else "CLEAN"
        
        print(f"{symbol} [{result_type:2}] {expected_str:8} -> {detected_str:8}  {description}")
    
    # Summary statistics
    print("\n" + "=" * 75)
    print("RESULTS SUMMARY")
    print("=" * 75)
    
    total = sum(stats.values())
    correct = stats["tp"] + stats["tn"]
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Escape detection metrics
    escape_count = stats["tp"] + stats["fn"]
    precision = stats["tp"] / (stats["tp"] + stats["fp"]) if (stats["tp"] + stats["fp"]) > 0 else 0
    recall = stats["tp"] / escape_count if escape_count > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nOverall Accuracy: {accuracy:.1f}% ({correct}/{total})")
    print(f"\nClassification Breakdown:")
    print(f"  ✓ True Positives  (TP): {stats['tp']:3} - Correctly detected escapes")
    print(f"  ✓ True Negatives  (TN): {stats['tn']:3} - Correctly identified clean code")
    print(f"  ✗ False Positives (FP): {stats['fp']:3} - Incorrectly flagged as escape")
    print(f"  ✗ False Negatives (FN): {stats['fn']:3} - Missed escape detection")
    
    print(f"\nEscape Detection Metrics:")
    print(f"  Precision (TP/(TP+FP)): {precision:.1%} - When detector flags escape, is it correct?")
    print(f"  Recall (TP/(TP+FN)):    {recall:.1%} - How many escapes does detector catch?")
    print(f"  F1-Score:               {f1:.3f}  - Harmonic mean of precision & recall")
    
    print(f"\nDetection Rate by Category:")
    for cat in ["escape", "clean"]:
        if categories[cat]["total"] > 0:
            cat_stats = categories[cat]
            cat_acc = (cat_stats["tp"] + cat_stats["tn"]) / cat_stats["total"]
            label = "Escape Detection" if cat == "escape" else "False Negative Avoidance"
            print(f"  {label:30} {cat_acc:.1%} ({cat_stats['tp'] + cat_stats['tn']}/{cat_stats['total']})")
    
    print("\n" + "=" * 75)
    print("KEY INSIGHTS")
    print("=" * 75)
    
    if recall < 0.5:
        print("⚠️  LOW RECALL: Detector is missing many actual escapes")
        print("    This is concerning - the system needs to catch escapes reliably")
    elif recall > 0.8:
        print("✓ GOOD RECALL: Detector catches most actual escapes")
    
    if precision < 0.5:
        print("⚠️  LOW PRECISION: Many false alarms / incorrect detections")
        print("    This can lead to false confidence or debugging misdirection")
    elif precision > 0.8:
        print("✓ GOOD PRECISION: Detections are usually correct")
    
    if f1 < 0.6:
        print("⚠️  SYSTEM NEEDS IMPROVEMENT")
        print("    Current detection is not reliable enough for production use")
    elif f1 > 0.8:
        print("✓ SYSTEM PERFORMS WELL")
        print("    Detector shows good balance of recall and precision")
    
    print("=" * 75)


if __name__ == "__main__":
    main()
