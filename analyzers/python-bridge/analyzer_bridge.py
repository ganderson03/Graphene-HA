#!/usr/bin/env python3
"""
Python Analyzer Bridge - Connects existing Python analyzer to Rust orchestrator
"""
import json
import sys
import os
from pathlib import Path

# Add parent directories to path to import existing modules
BRIDGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BRIDGE_DIR.parent.parent
GRAPHENE_HA_DIR = ROOT_DIR / "graphene_ha"

sys.path.insert(0, str(GRAPHENE_HA_DIR))
sys.path.insert(0, str(ROOT_DIR))

from test_harness import PythonFunctionTestHarness  # type: ignore[import-not-found]
from vulnerability_detector import VulnerabilityDetector  # type: ignore[import-not-found]
import importlib
import importlib.util
import time


def load_function_from_target(target: str):
    """Load a Python function from module:function or file.py:function format"""
    if ":" not in target:
        raise ValueError(f"Target must be in 'module:function' or 'file.py:function' format")
    
    module_part, func_name = target.rsplit(":", 1)
    
    # Check if it's a file path
    if module_part.endswith(".py"):
        spec = importlib.util.spec_from_file_location("target_module", module_part)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        # Regular module import
        module = importlib.import_module(module_part)
    
    if not hasattr(module, func_name):
        raise ValueError(f"Function '{func_name}' not found in module")
    
    return getattr(module, func_name)


def convert_escape_details_to_protocol(escape_details_str: str) -> dict:
    """Convert Python escape details string to protocol format"""
    details = {
        "threads": [],
        "processes": [],
        "async_tasks": [],
        "goroutines": [],
        "other": []
    }
    
    if not escape_details_str:
        return details
    
    for item in escape_details_str.split(";"):
        item = item.strip()
        if not item:
            continue
            
        if item.startswith("thread:"):
            parts = item.split(":", 2)
            if len(parts) >= 3:
                details["threads"].append({
                    "thread_id": parts[1],
                    "name": parts[1],
                    "is_daemon": parts[2] == "daemon",
                    "state": "alive",
                    "stack_trace": None
                })
        elif item.startswith("process:"):
            pid_str = item.split(":", 1)[1]
            try:
                pid = int(pid_str)
                details["processes"].append({
                    "pid": pid,
                    "name": f"Process-{pid}",
                    "cmdline": None
                })
            except ValueError:
                details["other"].append(item)
        else:
            details["other"].append(item)
    
    return details


def analyze(request: dict) -> dict:
    """Main analysis function"""
    session_id = request["session_id"]
    target = request["target"]
    inputs = request["inputs"]
    repeat = request["repeat"]
    timeout_seconds = request["timeout_seconds"]
    
    # Load the target function
    try:
        func = load_function_from_target(target)
    except Exception as e:
        return {
            "session_id": session_id,
            "language": "python",
            "analyzer_version": "1.0.0",
            "results": [],
            "vulnerabilities": [],
            "summary": {
                "total_tests": 0,
                "successes": 0,
                "crashes": 1,
                "timeouts": 0,
                "escapes": 0,
                "genuine_escapes": 0,
                "crash_rate": 1.0
            },
            "error": f"Failed to load function: {str(e)}"
        }
    
    # Create test harness
    harness = PythonFunctionTestHarness(
        func,
        timeout=timeout_seconds,
        prefer_main_thread=True  # Better for multiprocessing on Windows
    )
    
    # Run tests
    all_results = []
    for input_data in inputs:
        for _ in range(repeat):
            start_time = time.time()
            result = harness.run_test(input_data)
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            all_results.append({
                "input_data": input_data,
                "success": result.success,
                "crashed": result.crashed,
                "output": result.output,
                "error": result.error,
                "execution_time_ms": execution_time_ms,
                "escape_detected": result.escape_detected,
                "escape_details": convert_escape_details_to_protocol(result.escape_details)
            })
    
    # Analyze vulnerabilities
    detector = VulnerabilityDetector()
    
    # Convert results back to TestResult-like objects for detector
    class TestResultProxy:
        def __init__(self, data):
            self.input_data = data["input_data"]
            self.success = data["success"]
            self.crashed = data["crashed"]
            self.error = data["error"]
            self.escape_detected = data["escape_detected"]
            self.escape_details = ""  # Simplified for now
    
    result_proxies = [TestResultProxy(r) for r in all_results]
    analysis = detector.categorize_results(result_proxies)
    
    # Convert vulnerabilities to protocol format
    vulnerabilities = []
    for vuln in analysis["vulnerabilities"]:
        vulnerabilities.append({
            "input": vuln.input,
            "vulnerability_type": vuln.vulnerability_type,
            "severity": vuln.severity,
            "description": vuln.error_message,
            "escape_details": convert_escape_details_to_protocol(vuln.error_message)
        })
    
    # Build response
    response = {
        "session_id": session_id,
        "language": "python",
        "analyzer_version": "1.0.0",
        "results": all_results,
        "vulnerabilities": vulnerabilities,
        "summary": {
            "total_tests": analysis["total_tests"],
            "successes": analysis["successes"],
            "crashes": analysis["crashes"],
            "timeouts": analysis["timeouts"],
            "escapes": analysis["escapes"],
            "genuine_escapes": analysis["genuine_escapes"],
            "crash_rate": analysis["crash_rate"]
        }
    }
    
    return response


def main():
    """Read JSON request from stdin, process, and return JSON response"""
    try:
        # Read request from stdin
        request_json = sys.stdin.read()
        request = json.loads(request_json)
        
        # Process request
        response = analyze(request)
        
        # Write response to stdout
        print(json.dumps(response, indent=2))
        sys.exit(0)
        
    except Exception as e:
        error_response = {
            "session_id": "unknown",
            "language": "python",
            "analyzer_version": "1.0.0",
            "results": [],
            "vulnerabilities": [],
            "summary": {
                "total_tests": 0,
                "successes": 0,
                "crashes": 1,
                "timeouts": 0,
                "escapes": 0,
                "genuine_escapes": 0,
                "crash_rate": 1.0
            },
            "error": f"Bridge error: {str(e)}"
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
