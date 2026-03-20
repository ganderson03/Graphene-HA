#!/usr/bin/env python3
"""Python analyzer bridge for object escape analysis.

Dynamic execution verifies runtime behavior (timeouts/crashes), while escape
findings are sourced from static object escape analysis so results focus on
traditional escapes (return, parameter, global, closure, heap).
"""

import json
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add parent directories to path
BRIDGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BRIDGE_DIR.parent.parent
GRAPHENE_HA_DIR = ROOT_DIR / "graphene_ha"
TESTS_DIR = ROOT_DIR / "tests"
TESTS_PYTHON_DIR = TESTS_DIR / "python"

# Setup paths in correct order
sys.path.insert(0, str(GRAPHENE_HA_DIR))
sys.path.insert(0, str(TESTS_PYTHON_DIR))  # Add tests/python for imports
sys.path.insert(0, str(TESTS_DIR))         # Add tests for general test modules
sys.path.insert(0, str(ROOT_DIR))

from test_harness import PythonFunctionTestHarness  # type: ignore[import-not-found]
from vulnerability_detector import VulnerabilityDetector  # type: ignore[import-not-found]
import importlib
import importlib.util
import time


TRADITIONAL_ESCAPE_TYPES = {"return", "parameter", "global", "closure", "heap"}
ESCAPE_DESTINATIONS = {
    "return": "caller",
    "parameter": "callee",
    "global": "module_scope",
    "closure": "closure_scope",
    "heap": "heap_container",
}
STATIC_ANALYZER_MODULE = None


def parse_target(target: str) -> Tuple[str, str]:
    """Parse target format: module:function or file.py:function."""
    if ":" not in target:
        raise ValueError(
            f"Invalid target format '{target}': must be 'module:function' or 'file.py:function'"
        )
    module_part, func_name = target.rsplit(":", 1)
    if not module_part or not func_name:
        raise ValueError(
            f"Invalid target format '{target}': must include module/file and function"
        )
    return module_part, func_name


def load_function_from_target(target: str):
    module_part, func_name = parse_target(target)
    try:
        if module_part.endswith(".py"):
            if not Path(module_part).exists():
                raise FileNotFoundError(f"Source file not found: {module_part}")
            spec = importlib.util.spec_from_file_location("target_module", module_part)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load spec for {module_part}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            try:
                module = importlib.import_module(module_part)
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(f"Module not found: '{module_part}' (check PYTHONPATH or imports)")
    except (FileNotFoundError, ImportError, SyntaxError) as e:
        raise ValueError(f"Failed to load module '{module_part}': {str(e)}")
    
    if not hasattr(module, func_name):
        available = [n for n in dir(module) if not n.startswith("_")]
        raise AttributeError(f"Function '{func_name}' not found in module (available: {', '.join(available[:5])}{'...' if len(available) > 5 else ''})")
    return getattr(module, func_name)


def resolve_source_file(target: str, func: Any) -> str:
    """Resolve source file path for static analysis."""
    module_part, _ = parse_target(target)
    if module_part.endswith(".py"):
        return str(Path(module_part).resolve())

    source_path = inspect.getsourcefile(func)
    if source_path:
        return str(Path(source_path).resolve())
    return ""


def _load_static_analyzer_module():
    """Lazily load the Python static analyzer module."""
    global STATIC_ANALYZER_MODULE
    if STATIC_ANALYZER_MODULE is not None:
        return STATIC_ANALYZER_MODULE

    analyzer_path = ROOT_DIR / "analyzers" / "python" / "static_analyzer.py"
    if not analyzer_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("graphene_static_analyzer", analyzer_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    STATIC_ANALYZER_MODULE = module
    return module


def run_traditional_static_escape_analysis(source_file: str, function_name: str) -> List[Dict[str, Any]]:
    """Return only traditional object escapes from static analyzer output."""
    if not source_file or not Path(source_file).exists() or not function_name:
        return []

    analyzer_module = _load_static_analyzer_module()
    if analyzer_module is None or not hasattr(analyzer_module, "analyze_file"):
        return []

    try:
        result = analyzer_module.analyze_file(source_file, function_name)
    except Exception:
        return []

    if not result.get("success", False):
        return []

    escapes = result.get("escapes", [])
    return [
        escape
        for escape in escapes
        if escape.get("escape_type") in TRADITIONAL_ESCAPE_TYPES
    ]


def summarize_static_escapes(escapes: List[Dict[str, Any]]) -> str:
    """Create compact text summary for vulnerability descriptions."""
    if not escapes:
        return ""

    parts = []
    for escape in escapes:
        escape_type = escape.get("escape_type", "unknown")
        variable_name = escape.get("variable_name", "<value>")
        line = escape.get("line")
        if isinstance(line, int) and line > 0:
            parts.append(f"{escape_type}:{variable_name}@L{line}")
        else:
            parts.append(f"{escape_type}:{variable_name}")

    return "; ".join(parts)


def convert_static_escapes_to_protocol(escapes: List[Dict[str, Any]], source_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """Convert static escape findings to protocol-compatible object escape details."""
    details = empty_escape_details()
    for escape in escapes:
        escape_type = escape.get("escape_type", "unknown")
        variable_name = escape.get("variable_name", "<value>")
        line = escape.get("line", 0)
        column = escape.get("column", 0)
        confidence = escape.get("confidence", "medium")

        allocation_site = (
            f"{source_file}:{line}:{column}"
            if source_file and isinstance(line, int) and isinstance(column, int)
            else source_file or "unknown"
        )

        details["escaping_references"].append(
            {
                "variable_name": variable_name,
                "object_type": "unknown",
                "allocation_site": allocation_site,
                "escaped_via": escape_type,
            }
        )

        details["escape_paths"].append(
            {
                "source": variable_name,
                "destination": ESCAPE_DESTINATIONS.get(escape_type, "unknown"),
                "escape_type": escape_type,
                "confidence": confidence,
            }
        )

    return details


def diagnose_bridge_error(error_msg: str):
    raw = (error_msg or "").strip()
    lower = raw.lower()

    if "timeout" in lower or "timed out" in lower or "exceeded" in lower:
        return (
            "Timeout",
            "Inspect blocking operations and missing joins/awaits before increasing timeout.",
        )
    if (
        "target resolution" in lower
        or "missing required field: 'target'" in lower
        or "target loading failed" in lower
        or "failed to load" in lower
        or "invalid target" in lower
        or "module not found" in lower
        or "not found" in lower
    ):
        return (
            "Target Resolution",
            "Verify target signature/path and ensure the target symbol exists in the selected language module.",
        )
    if (
        "protocol/input" in lower
        or "invalid json" in lower
        or "failed to parse" in lower
        or "empty input" in lower
        or "expected json" in lower
        or "json" in lower
        or "parse" in lower
        or "stdin" in lower
        or "protocol" in lower
    ):
        return (
            "Protocol/Input",
            "Validate request JSON and ensure bridge stdin/stdout protocol fields match the orchestrator contract.",
        )
    if (
        "environment" in lower
        or "permission denied" in lower
        or "not available" in lower
        or "not found in path" in lower
        or "command not found" in lower
        or "missing tools" in lower
        or "python not found" in lower
    ):
        return (
            "Environment",
            "Check runtime/toolchain installation and PATH configuration for the selected language analyzer.",
        )
    if (
        "runtime crash" in lower
        or "panic" in lower
        or "exception" in lower
        or "traceback" in lower
        or "segmentation" in lower
    ):
        return (
            "Runtime Crash",
            "Re-run with --verbose and inspect bridge stack traces for runtime exceptions.",
        )

    return (
        "Unknown",
        "Re-run with --verbose and inspect bridge stdout/stderr for additional diagnostics.",
    )


def empty_escape_details() -> dict:
    return {"escaping_references": [], "escape_paths": []}


def _error_response(language, error_msg, session_id="unknown", analysis_mode="dynamic"):
    category, suggested_action = diagnose_bridge_error(error_msg)
    return {
        "session_id": session_id,
        "language": language,
        "analyzer_version": "1.0.0",
        "analysis_mode": analysis_mode,
        "results": [
            {
                "input_data": "<bridge-startup>",
                "success": False,
                "crashed": True,
                "output": "",
                "error": f"{category}: {error_msg}",
                "execution_time_ms": 0,
                "escape_detected": False,
                "escape_details": empty_escape_details(),
            }
        ],
        "vulnerabilities": [],
        "summary": {
            "total_tests": 1,
            "successes": 0,
            "crashes": 1,
            "timeouts": 1 if category == "Timeout" else 0,
            "escapes": 0,
            "genuine_escapes": 0,
            "crash_rate": 1.0,
        },
        "error": error_msg,
        "error_category": category,
        "suggested_action": suggested_action,
    }

def analyze(request: dict) -> dict:
    session_id = request.get("session_id", "unknown")
    target = request.get("target")
    if not target:
        return _error_response("python", "Missing required field: 'target'", session_id)
    
    inputs = request.get("inputs", [])
    repeat = request.get("repeat", 1)
    timeout_seconds = request.get("timeout_seconds", 30.0)
    analysis_mode = request.get("analysis_mode", "dynamic")

    try:
        _, function_name = parse_target(target)
    except ValueError as e:
        return _error_response("python", str(e), session_id, analysis_mode)
    
    try:
        func = load_function_from_target(target)
    except (ValueError, FileNotFoundError, ModuleNotFoundError, AttributeError) as e:
        return _error_response("python", f"Target loading failed: {str(e)}", session_id, analysis_mode)
    except Exception as e:
        return _error_response("python", f"Unexpected error loading target '{target}': {type(e).__name__}: {str(e)}", session_id, analysis_mode)

    source_file = resolve_source_file(target, func)
    static_escapes = run_traditional_static_escape_analysis(source_file, function_name)
    static_escape_detected = bool(static_escapes)
    static_escape_summary = summarize_static_escapes(static_escapes)
    static_escape_details = convert_static_escapes_to_protocol(static_escapes, source_file)

    harness = PythonFunctionTestHarness(func, timeout=timeout_seconds, prefer_main_thread=True)
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
                "escape_detected": bool(result.escape_detected or static_escape_detected),
                "escape_details": static_escape_details if static_escape_detected else empty_escape_details(),
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
            self.escape_details = static_escape_summary
    
    result_proxies = [TestResultProxy(r) for r in all_results]
    analysis = detector.categorize_results(result_proxies)
    vulnerabilities = [
        {
            "input": v.input,
            "vulnerability_type": v.vulnerability_type,
            "severity": v.severity,
            "description": v.error_message,
            "escape_details": static_escape_details if static_escape_detected else empty_escape_details(),
        }
        for v in analysis["vulnerabilities"]
    ]
    return {
        "session_id": session_id,
        "language": "python",
        "analyzer_version": "1.0.0",
        "analysis_mode": analysis_mode,
        "results": all_results,
        "vulnerabilities": vulnerabilities,
        "summary": {
            "total_tests": analysis["total_tests"],
            "successes": analysis["successes"],
            "crashes": analysis["crashes"],
            "timeouts": analysis["timeouts"],
            "escapes": analysis["escapes"],
            "genuine_escapes": analysis.get("genuine_escapes", analysis["escapes"]),
            "crash_rate": analysis["crash_rate"],
        },
    }


def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            error_msg = _error_response("python", "Empty input: expected JSON request on stdin")
            print(json.dumps(error_msg), file=sys.stderr)
            sys.exit(1)
        
        try:
            request = json.loads(input_data)
        except json.JSONDecodeError as e:
            error_msg = _error_response("python", f"Invalid JSON input: {str(e)} at line {e.lineno}, column {e.colno}")
            print(json.dumps(error_msg), file=sys.stderr)
            sys.exit(1)
        
        result = analyze(request)
        print(json.dumps(result, indent=2))
        sys.exit(0 if "error" not in result else 1)
    except BrokenPipeError:
        sys.exit(0)
    except Exception as e:
        error_msg = _error_response("python", f"Bridge critical error: {type(e).__name__}: {str(e)}")
        print(json.dumps(error_msg), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
