#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Add parent directories to path
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
    if ":" not in target:
        raise ValueError(f"Target must be in 'module:function' or 'file.py:function' format")
    module_part, func_name = target.rsplit(":", 1)
    if module_part.endswith(".py"):
        spec = importlib.util.spec_from_file_location("target_module", module_part)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(module_part)
    if not hasattr(module, func_name):
        raise ValueError(f"Function '{func_name}' not found in module")
    return getattr(module, func_name)


def convert_escape_details_to_protocol(escape_details_str: str) -> dict:
    details = {"threads": [], "processes": [], "async_tasks": [], "goroutines": [], "other": []}
    if not escape_details_str:
        return details
    for item in escape_details_str.split(";"):
        item = item.strip()
        if not item:
            continue
        if item.startswith("thread:"):
            parts = item.split(":", 2)
            if len(parts) >= 3:
                details["threads"].append({"thread_id": parts[1], "name": parts[1], "is_daemon": parts[2] == "daemon", "state": "alive", "stack_trace": None})
        elif item.startswith("process:"):
            try:
                pid = int(item.split(":", 1)[1])
                details["processes"].append({"pid": pid, "name": f"Process-{pid}", "cmdline": None})
            except ValueError:
                details["other"].append(item)
        else:
            details["other"].append(item)
    return details


def _error_response(language, error_msg, session_id="unknown"):
    return {"session_id": session_id, "language": language, "analyzer_version": "1.0.0", "results": [], "vulnerabilities": [], "summary": {"total_tests": 0, "successes": 0, "crashes": 1, "timeouts": 0, "escapes": 0, "genuine_escapes": 0, "crash_rate": 1.0}, "error": error_msg}

def analyze(request: dict) -> dict:
    session_id = request["session_id"]
    target = request["target"]
    inputs = request["inputs"]
    repeat = request["repeat"]
    timeout_seconds = request["timeout_seconds"]
    try:
        func = load_function_from_target(target)
    except Exception as e:
        return _error_response("python", f"Failed to load function: {str(e)}", session_id)
    harness = PythonFunctionTestHarness(func, timeout=timeout_seconds, prefer_main_thread=True)
    detector = VulnerabilityDetector()
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
    vulnerabilities = [{"input": v.input, "vulnerability_type": v.vulnerability_type, "severity": v.severity, "description": v.error_message, "escape_details": convert_escape_details_to_protocol(v.error_message)} for v in analysis["vulnerabilities"]]
    return {"session_id": session_id, "language": "python", "analyzer_version": "1.0.0", "results": all_results, "vulnerabilities": vulnerabilities, "summary": {"total_tests": analysis["total_tests"], "successes": analysis["successes"], "crashes": analysis["crashes"], "timeouts": analysis["timeouts"], "escapes": analysis["escapes"], "genuine_escapes": analysis["genuine_escapes"], "crash_rate": analysis["crash_rate"]}}


def main():
    try:
        request = json.loads(sys.stdin.read())
        print(json.dumps(analyze(request), indent=2))
        sys.exit(0)
    except Exception as e:
        print(json.dumps(_error_response("python", f"Bridge error: {str(e)}")), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
