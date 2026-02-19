#!/usr/bin/env python3
"""
Comprehensive escape detection measurement
Tests the full suite of advanced and comprehensive escape patterns
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "python"))

from graphene_ha.test_harness import PythonFunctionTestHarness
from collections import defaultdict
import time

# Import all test modules
import advanced_escapes
import comprehensive_escapes
import escape_threads
import escape_process
import no_escape
import escape_executor
import escape_pool

# Test definitions combining all patterns
ALL_TESTS = [
    # ========== BASIC ESCAPES (from advanced_escapes) ==========
    (escape_threads, "spawn_non_daemon_thread", True, "Basic thread"),
    (escape_threads, "spawn_daemon_thread", True, "Daemon thread"),
    (escape_process, "spawn_process", True, "Basic process"),
    
    # ========== INTERMEDIATE PATTERNS (advanced_escapes) ==========
    (advanced_escapes, "spawn_thread_via_function_ref", True, "Func ref"),
    (advanced_escapes, "spawn_thread_conditionally", True, "Conditional"),
    (advanced_escapes, "spawn_thread_with_dynamic_key", True, "Dynamic key"),
    (advanced_escapes, "leak_executor_on_exception", True, "Executor on exc"),
    (advanced_escapes, "spawn_process_without_join", True, "Process no join"),
    
    # ========== ADVANCED PATTERNS (comprehensive_escapes) ==========
    # External module & decorator escapes
    (comprehensive_escapes, "escape_via_concurrent_map", True, "Concurrent map"),
    (comprehensive_escapes, "escape_thread_in_decorator", True, "Decorator thread"),
    (comprehensive_escapes, "escape_thread_in_context_manager", True, "Context mgr thread"),
    
    # Metaclass escapes
    (comprehensive_escapes, "escape_via_metaclass", True, "Metaclass spawn"),
    
    # Closure/state escapes
    (comprehensive_escapes, "escape_via_global_registry", True, "Global registry"),
    (comprehensive_escapes, "escape_via_closure_capture", True, "Closure capture"),
    
    # Special method escapes
    (comprehensive_escapes, "escape_via_del_method", True, "__del__ spawn"),
    (comprehensive_escapes, "escape_via_property_setter", True, "Property setter"),
    
    # Weak reference escapes
    (comprehensive_escapes, "escape_via_weakref_callback", True, "Weakref callback"),
    
    # Exception handling escapes
    (comprehensive_escapes, "escape_in_exception_handler", True, "Exception handler"),
    (comprehensive_escapes, "escape_via_finally_block", True, "Finally block"),
    
    # Execution escapes
    (comprehensive_escapes, "escape_via_dynamic_import", True, "Dynamic import"),
    (comprehensive_escapes, "escape_with_random_condition", True, "Random condition"),
    
    # Multi-layer escapes
    (comprehensive_escapes, "escape_via_multiple_indirections", True, "Multi-indirect"),
    (comprehensive_escapes, "escape_via_nested_context", True, "Nested context"),
    
    # Process escapes
    (comprehensive_escapes, "escape_via_process_pool", True, "Process pool"),
    (comprehensive_escapes, "escape_multiple_processes_partial", True, "Partial join"),
    
    # Executor escapes
    (comprehensive_escapes, "escape_executor_with_active_tasks", True, "Executor tasks"),
    (comprehensive_escapes, "escape_nested_executors", True, "Nested executors"),
    
    # ========== PROPER PATTERNS (non-escapes) ==========
    (no_escape, "no_threads", False, "No threads"),
    (no_escape, "join_thread", False, "Joined thread"),
    (comprehensive_escapes, "thread_with_immediate_join", False, "Immediate join"),
    (comprehensive_escapes, "thread_via_context_manager_proper", False, "Context proper"),
    (comprehensive_escapes, "executor_with_context_proper", False, "Executor context"),
    (comprehensive_escapes, "exception_safely_joins_thread", False, "Safe join in exception"),
    (comprehensive_escapes, "process_properly_joined", False, "Process joined"),
]


def run_test(module, func_name, should_detect, description):
    """Run a single test"""
    try:
        func = getattr(module, func_name)
        harness = PythonFunctionTestHarness(func, timeout=3.0, prefer_main_thread=False)
        result = harness.run_test("test_input")
        
        # Detect escape
        detected = result.escape_detected or (result.error and "timeout" in result.error.lower())
        
        return (detected, should_detect, detected == should_detect, None)
    except Exception as e:
        return (False, should_detect, False, str(e)[:50])


def main():
    print("="*80)
    print("COMPREHENSIVE ESCAPE DETECTION MEASUREMENT")
    print("="*80)
    
    stats = {
        "tp": 0,  # True Positive
        "tn": 0,  # True Negative
        "fp": 0,  # False Positive
        "fn": 0,  # False Negative
    }
    
    categories = defaultdict(lambda: {"tp": 0, "tn": 0, "fp": 0, "fn": 0})
    
    print(f"\nRunning {len(ALL_TESTS)} comprehensive tests:")
    print("-"*80)
    
    failed_tests = []
    
    for i, (module, func_name, should_detect, description) in enumerate(ALL_TESTS, 1):
        print(f"[{i:2d}/{len(ALL_TESTS):2d}]  {func_name:40} ", end="", flush=True)
        
        detected, expected, correct, error = run_test(module, func_name, should_detect, description)
        
        if error:
            print(f"⚠️  ERROR: {error}")
            stats["fn"] += 1 if expected else 0
            stats["fp"] += 1 if not expected else 0
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
            failed_tests.append(func_name)
        else:
            result_type = "FP"
            stats["fp"] += 1
            symbol = "✗"
            failed_tests.append(func_name)
        
        cat = "escape" if expected else "clean"
        categories[cat][result_type.lower()] += 1
        
        expected_str = "ESCAPE" if expected else "CLEAN"
        detected_str = "ESCAPE" if detected else "CLEAN"
        
        print(f"{symbol} [{result_type:2}] {expected_str:8} -> {detected_str:8}")
    
    # Summary
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    total = sum(stats.values())
    correct = stats["tp"] + stats["tn"]
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\nOverall Accuracy: {accuracy:.1f}% ({correct}/{total})")
    
    print(f"\nClassification Breakdown:")
    print(f"  ✓ True Positives  (TP):  {stats['tp']:2d} - Correctly detected escapes")
    print(f"  ✓ True Negatives  (TN):  {stats['tn']:2d} - Correctly identified clean code")
    print(f"  ✗ False Positives (FP):  {stats['fp']:2d} - Incorrectly flagged as escape")
    print(f"  ✗ False Negatives (FN):  {stats['fn']:2d} - Missed escape detection")
    
    # Metrics
    escape_count = stats["tp"] + stats["fn"]
    precision = stats["tp"] / (stats["tp"] + stats["fp"]) if (stats["tp"] + stats["fp"]) > 0 else 0
    recall = stats["tp"] / escape_count if escape_count > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nEscape Detection Metrics:")
    print(f"  Precision: {precision*100:.1f}% - When detector flags escape, is it correct?")
    print(f"  Recall:    {recall*100:.1f}% - How many escapes does detector catch?")
    print(f"  F1-Score:  {f1:.3f}  - Harmonic mean of precision & recall")
    
    print(f"\nPattern-level Detection:")
    for cat_name in ["escape", "clean"]:
        cat = categories[cat_name]
        cat_total = sum(cat.values())
        cat_correct = cat.get("tp" if cat_name == "escape" else "tn", 0)
        cat_pct = (cat_correct / cat_total * 100) if cat_total > 0 else 0
        label = "Escape Detection" if cat_name == "escape" else "Clean Code Detection"
        print(f"  {label:25} {cat_pct:5.1f}% ({cat_correct}/{cat_total})")
    
    if failed_tests:
        print(f"\n⚠️  Failed Tests ({len(failed_tests)}):")
        for test in failed_tests[:10]:
            print(f"    - {test}")
        if len(failed_tests) > 10:
            print(f"    ... and {len(failed_tests) - 10} more")
    
    print("\n" + "="*80)
    print("ASSESSMENT")
    print("="*80)
    
    if accuracy >= 95:
        print("✅ EXCELLENT: System handles complex patterns very well")
    elif accuracy >= 85:
        print("✅ GOOD: System reliably detects most escapes")
    elif accuracy >= 75:
        print("⚠️  ACCEPTABLE: System detects basic patterns, some advanced patterns missed")
    else:
        print("⚠️  NEEDS WORK: Several pattern categories need improvement")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
