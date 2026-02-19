#!/usr/bin/env python3
"""
Escape Detection Success Rate Analyzer

Measures how well Graphene-HA detects various escape patterns.
Categorizes results and identifies:
- True Positives (correctly detected escapes)
- True Negatives (correctly identified clean code)
- False Positives (incorrectly flagged)
- False Negatives (missed escapes)
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from collections import defaultdict


@dataclass
class TestCase:
    """Represents a single test case"""
    language: str
    function_name: str
    module: str
    should_detect_escape: bool  # Expected result
    category: str  # Type of escape pattern
    description: str


@dataclass
class TestResult:
    """Result of running a test case"""
    test_case: TestCase
    detected_escape: bool  # Actual result
    execution_time_ms: float
    error: str = ""
    details: str = ""


@dataclass
class CategoryStats:
    """Statistics for a category of tests"""
    name: str
    total: int = 0
    tp: int = 0  # True positives
    tn: int = 0  # True negatives
    fp: int = 0  # False positives
    fn: int = 0  # False negatives
    avg_time_ms: float = 0.0
    execution_times: List[float] = field(default_factory=list)
    
    @property
    def detected_count(self):
        return self.tp + self.fp
    
    @property
    def accuracy(self):
        if self.total == 0:
            return 0.0
        return (self.tp + self.tn) / self.total
    
    @property
    def precision(self):
        if self.detected_count == 0:
            return 0.0
        return self.tp / self.detected_count
    
    @property
    def recall(self):
        escape_count = self.tp + self.fn
        if escape_count == 0:
            return 0.0
        return self.tp / escape_count
    
    @property
    def f1_score(self):
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


class EscapeDetectionTester:
    """Main tester class"""
    
    def __init__(self, workspace_root: str):
        self.workspace = Path(workspace_root)
        self.results: List[TestResult] = []
        self.categories: Dict[str, CategoryStats] = defaultdict(
            lambda: CategoryStats(name="")
        )
    
    def get_python_tests(self) -> List[TestCase]:
        """Define Python test cases"""
        return [
            # === True Escapes (Should Detect) ===
            # Obfuscated
            TestCase("python", "spawn_thread_via_function_ref", "advanced_escapes", True, "obfuscated", "Thread spawn via function reference"),
            TestCase("python", "spawn_thread_via_lambda", "advanced_escapes", True, "obfuscated", "Thread spawn via lambda"),
            TestCase("python", "spawn_thread_in_generator", "advanced_escapes", True, "obfuscated", "Thread spawn in generator"),
            
            # Delayed
            TestCase("python", "spawn_thread_with_delayed_start", "advanced_escapes", True, "delayed", "Thread with delayed start"),
            TestCase("python", "spawn_thread_to_registry", "advanced_escapes", True, "delayed", "Thread stored in registry"),
            
            # Conditional
            TestCase("python", "spawn_thread_conditionally", "advanced_escapes", True, "conditional", "Conditional thread spawn"),
            TestCase("python", "spawn_thread_in_try_except", "advanced_escapes", True, "conditional", "Thread in exception handler"),
            
            # Dynamic
            TestCase("python", "spawn_thread_with_dynamic_key", "advanced_escapes", True, "dynamic", "Thread with dynamic key"),
            TestCase("python", "spawn_thread_via_setattr", "advanced_escapes", True, "dynamic", "Thread via setattr"),
            
            # Weak references
            TestCase("python", "spawn_thread_weak_reference", "advanced_escapes", True, "weak_ref", "Thread with weak reference"),
            
            # Executor
            TestCase("python", "leak_executor_on_exception", "advanced_escapes", True, "executor", "Executor leaked on exception"),
            TestCase("python", "leak_pool_incrementally", "advanced_escapes", True, "executor", "Thread pool leaked incrementally"),
            
            # Process
            TestCase("python", "spawn_process_without_join", "advanced_escapes", True, "process", "Process without join"),
            TestCase("python", "spawn_multiple_processes_mixed", "advanced_escapes", True, "process", "Mixed joined/unjoined processes"),
            
            # Deferred
            TestCase("python", "schedule_thread_for_later", "advanced_escapes", True, "deferred", "Thread spawned deferred"),
            
            # Recursive
            TestCase("python", "spawn_threads_recursively", "advanced_escapes", True, "recursive", "Recursive thread spawning"),
            
            # Interrupt
            TestCase("python", "spawn_thread_interrupt_cleanup", "advanced_escapes", True, "interrupt", "Thread with interrupted cleanup"),
            
            # Local storage
            TestCase("python", "spawn_thread_with_local_storage", "advanced_escapes", True, "local_storage", "Thread with TLS"),
            
            # === False Negatives (Should NOT Detect) ===
            TestCase("python", "properly_joined_thread", "advanced_escapes", False, "cleanup", "Properly joined thread"),
            TestCase("python", "properly_shutdown_executor", "advanced_escapes", False, "cleanup", "Properly shutdown executor"),
            TestCase("python", "daemon_thread_cleanup", "advanced_escapes", False, "cleanup", "Daemon thread (auto cleanup)"),
            
            # Original tests
            TestCase("python", "spawn_non_daemon_thread", "escape_threads", True, "basic", "Basic thread spawn"),
            TestCase("python", "join_thread", "no_escape", False, "cleanup", "Basic joined thread"),
            TestCase("python", "spawn_process", "escape_process", True, "basic", "Basic process spawn"),
        ]
    
    def get_nodejs_tests(self) -> List[TestCase]:
        """Define Node.js test cases"""
        return [
            # === True Escapes ===
            TestCase("javascript", "createPromiseViaFactory", "advanced_escapes", True, "obfuscated", "Promise via factory"),
            TestCase("javascript", "createPromiseInArray", "advanced_escapes", True, "obfuscated", "Promise in array"),
            TestCase("javascript", "createPromiseWithoutAwait", "advanced_escapes", True, "obfuscated", "Promise without await"),
            
            TestCase("javascript", "hideAsyncInArray", "advanced_escapes", True, "dynamic", "Hidden async in array"),
            TestCase("javascript", "hideAsyncViaFunction", "advanced_escapes", True, "dynamic", "Hidden async via function"),
            
            TestCase("javascript", "leakAsyncConditionally", "advanced_escapes", True, "conditional", "Conditional async leak"),
            TestCase("javascript", "leakAsyncInCatch", "advanced_escapes", True, "conditional", "Async in catch handler"),
            
            TestCase("javascript", "leakViaEventListener", "advanced_escapes", True, "event", "Async via event listener"),
            TestCase("javascript", "leakMultipleListeners", "advanced_escapes", True, "event", "Multiple event listeners"),
            
            TestCase("javascript", "createIntervalDynamically", "advanced_escapes", True, "timer", "Dynamic intervals"),
            TestCase("javascript", "timeoutChain", "advanced_escapes", True, "timer", "Chained timeouts"),
            TestCase("javascript", "createLeakingTimer", "advanced_escapes", True, "timer", "Leaking timer"),
            
            TestCase("javascript", "breakPromiseChain", "advanced_escapes", True, "promise_chain", "Broken promise chain"),
            TestCase("javascript", "multipleUnboundPromises", "advanced_escapes", True, "promise_chain", "Multiple unbound promises"),
            
            TestCase("javascript", "callAsyncWithoutAwait", "advanced_escapes", True, "async_func", "Async call without await"),
            TestCase("javascript", "asyncInCallback", "advanced_escapes", True, "async_func", "Async in callback"),
            
            TestCase("javascript", "racePromisesNotAll", "advanced_escapes", True, "race", "Promise.race unresolved"),
            TestCase("javascript", "recursiveAsyncChain", "advanced_escapes", True, "recursive", "Recursive async"),
            
            # === False Negatives ===
            TestCase("javascript", "properlyAwaitTimeout", "advanced_escapes", False, "cleanup", "Properly awaited timeout"),
            TestCase("javascript", "properlyAwaitPromise", "advanced_escapes", False, "cleanup", "Properly awaited promise"),
            TestCase("javascript", "properlyAbortController", "advanced_escapes", False, "cleanup", "Properly cleared timer"),
            TestCase("javascript", "properlyShutdownInterval", "advanced_escapes", False, "cleanup", "Properly cleared interval"),
            TestCase("javascript", "properlyResolvePromises", "advanced_escapes", False, "cleanup", "Properly resolved promises"),
            
            # Original tests
            TestCase("javascript", "createLeakingInterval", "escape_async", True, "basic", "Basic leaking interval"),
            TestCase("javascript", "clearIntervalSafely", "no_escape_async", False, "cleanup", "Properly cleared interval"),
        ]
    
    def run_python_test(self, test: TestCase) -> TestResult:
        """Run a single Python test"""
        start = time.time()
        try:
            cmd = [
                "uv", "run", "graphene", "analyze",
                f"tests/python/{test.module}:{test.function_name}",
                "--repeat", "1",
                "--timeout", "5"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            execution_time = (time.time() - start) * 1000
            
            # Parse output for escape detection
            detected = "escape" in result.stdout.lower()
            
            return TestResult(
                test_case=test,
                detected_escape=detected,
                execution_time_ms=execution_time,
                details=result.stdout[:200] if result.stdout else ""
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                test_case=test,
                detected_escape=False,
                execution_time_ms=10000,
                error="Timeout"
            )
        except Exception as e:
            return TestResult(
                test_case=test,
                detected_escape=False,
                execution_time_ms=(time.time() - start) * 1000,
                error=str(e)
            )
    
    def run_nodejs_test(self, test: TestCase) -> TestResult:
        """Run a single Node.js test"""
        start = time.time()
        try:
            # Create JSON request for bridge
            request = {
                "session_id": f"test_{test.function_name}",
                "language": "javascript",
                "target": f"tests/nodejs/{test.module}.js:{test.function_name}",
                "inputs": ["test"],
                "repeat": 1,
                "timeout_seconds": 5
            }
            
            cmd = ["node", "analyzers/nodejs-bridge/analyzer_bridge.js"]
            
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=15
            )
            
            execution_time = (time.time() - start) * 1000
            
            # Parse JSON response
            try:
                response = json.loads(result.stdout)
                detected = response.get("summary", {}).get("escapes", 0) > 0
            except:
                detected = "escape" in result.stdout.lower()
            
            return TestResult(
                test_case=test,
                detected_escape=detected,
                execution_time_ms=execution_time,
                details=result.stdout[:200] if result.stdout else ""
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                test_case=test,
                detected_escape=False,
                execution_time_ms=15000,
                error="Timeout"
            )
        except Exception as e:
            return TestResult(
                test_case=test,
                detected_escape=False,
                execution_time_ms=(time.time() - start) * 1000,
                error=str(e)
            )
    
    def run_all_tests(self):
        """Run all test suites"""
        print("=" * 70)
        print("ESCAPE DETECTION SUCCESS RATE ANALYSIS")
        print("=" * 70)
        
        # Python tests
        print("\n🐍 Running Python Tests...")
        py_tests = self.get_python_tests()
        for i, test in enumerate(py_tests, 1):
            print(f"  [{i}/{len(py_tests)}] {test.category:15} {test.function_name:30}", end=" ", flush=True)
            result = self.run_python_test(test)
            self.results.append(result)
            print(f"{'✓' if result.detected_escape == test.should_detect_escape else '✗'}")
        
        # Node.js tests
        print("\n⚡ Running Node.js Tests...")
        js_tests = self.get_nodejs_tests()
        for i, test in enumerate(js_tests, 1):
            print(f"  [{i}/{len(js_tests)}] {test.category:15} {test.function_name:30}", end=" ", flush=True)
            result = self.run_nodejs_test(test)
            self.results.append(result)
            print(f"{'✓' if result.detected_escape == test.should_detect_escape else '✗'}")
        
        self._process_results()
    
    def _process_results(self):
        """Process and print results"""
        # Categorize results
        for result in self.results:
            cat_name = result.test_case.category
            cat = self.categories[cat_name]
            cat.name = cat_name
            cat.total += 1
            cat.execution_times.append(result.execution_time_ms)
            
            expected = result.test_case.should_detect_escape
            actual = result.detected_escape
            
            if expected and actual:
                cat.tp += 1
            elif not expected and not actual:
                cat.tn += 1
            elif expected and not actual:
                cat.fn += 1
            else:
                cat.fp += 1
        
        # Calculate averages
        for cat in self.categories.values():
            cat.avg_time_ms = sum(cat.execution_times) / len(cat.execution_times) if cat.execution_times else 0
        
        self._print_summary()
    
    def _print_summary(self):
        """Print summary statistics"""
        print("\n" + "=" * 70)
        print("RESULTS BY CATEGORY")
        print("=" * 70)
        print(f"\n{'Category':20} {'Total':6} {'TP':4} {'TN':4} {'FP':4} {'FN':4} {'Acc':6} {'Prec':6} {'Rec':6} {'F1':6}")
        print("-" * 70)
        
        total_stats = CategoryStats(name="TOTAL")
        
        for cat_name in sorted(self.categories.keys()):
            cat = self.categories[cat_name]
            total_stats.total += cat.total
            total_stats.tp += cat.tp
            total_stats.tn += cat.tn
            total_stats.fp += cat.fp
            total_stats.fn += cat.fn
            
            print(f"{cat_name:20} {cat.total:6} {cat.tp:4} {cat.tn:4} {cat.fp:4} {cat.fn:4} " 
                  f"{cat.accuracy*100:5.1f}% {cat.precision*100:5.1f}% {cat.recall*100:5.1f}% {cat.f1_score:5.3f}")
        
        print("-" * 70)
        print(f"{'TOTAL':20} {total_stats.total:6} {total_stats.tp:4} {total_stats.tn:4} {total_stats.fp:4} {total_stats.fn:4} " 
              f"{total_stats.accuracy*100:5.1f}% {total_stats.precision*100:5.1f}% {total_stats.recall*100:5.1f}% {total_stats.f1_score:5.3f}")
        
        # Print detailed failures
        print("\n" + "=" * 70)
        print("MISCLASSIFIED TESTS (False Positives & False Negatives)")
        print("=" * 70)
        
        failures = [r for r in self.results if r.detected_escape != r.test_case.should_detect_escape]
        
        if not failures:
            print("✓ All tests correctly classified!")
        else:
            for result in sorted(failures, key=lambda r: r.test_case.function_name):
                test = result.test_case
                expected = "ESCAPE" if test.should_detect_escape else "CLEAN"
                actual = "ESCAPE" if result.detected_escape else "CLEAN"
                error_type = "FN" if test.should_detect_escape else "FP"
                
                print(f"\n  {error_type}: {test.function_name}")
                print(f"      Language:  {test.language}")
                print(f"      Category:  {test.category}")
                print(f"      Expected:  {expected}")
                print(f"      Detected:  {actual}")
                print(f"      Reason:    {test.description}")
                if result.error:
                    print(f"      Error:     {result.error}")


def main():
    workspace = Path(__file__).parent.parent.parent
    tester = EscapeDetectionTester(str(workspace))
    tester.run_all_tests()


if __name__ == "__main__":
    main()
