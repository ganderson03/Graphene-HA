#!/usr/bin/env python3
"""Python analyzer bridge for object escape analysis.

Dynamic execution now uses direct heap/object tracing to measure memory growth
around each target invocation while preserving the bridge's existing result
packaging and report contract.
"""

import gc
import json
import sys
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
import tracemalloc


ESCAPE_DESTINATIONS = {
    "heap": "heap_container",
}


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
            # Register module before execution so decorators (e.g., dataclass)
            # can resolve module globals through sys.modules during import.
            sys.modules[spec.name] = module
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


def _normalize_path(path_value: str) -> Optional[Path]:
    try:
        return Path(path_value).resolve()
    except Exception:
        return None


def summarize_heap_allocations(
    allocations: List[Dict[str, Any]],
    total_growth_bytes: int,
    function_name: str,
) -> str:
    """Create a compact heap-growth summary for bridge and vulnerability output."""
    if total_growth_bytes <= 0 and not allocations:
        return ""

    fragments = [f"heap_growth:{total_growth_bytes}B"]
    if function_name:
        fragments.append(f"target:{function_name}")

    for allocation in allocations[:3]:
        fragments.append(
            f"{Path(allocation['file']).name}@L{allocation['line']}+{allocation['size_diff']}B"
        )

    return "; ".join(fragments)


def convert_heap_allocations_to_protocol(
    allocations: List[Dict[str, Any]],
    source_file: str,
    function_name: str,
    total_growth_bytes: int,
    peak_bytes: int,
) -> Dict[str, Any]:
    """Convert heap-growth observations to protocol-compatible escape details."""
    details = empty_escape_details()

    for allocation in allocations:
        allocation_site = allocation["allocation_site"]
        details["escaping_references"].append(
            {
                "variable_name": function_name or "<heap>",
                "object_type": "heap_allocation",
                "allocation_site": allocation_site,
                "escaped_via": "heap",
            }
        )
        details["escape_paths"].append(
            {
                "source": function_name or "<heap>",
                "destination": ESCAPE_DESTINATIONS["heap"],
                "escape_type": "heap",
                "confidence": "high" if allocation["size_diff"] >= 1024 else "medium",
            }
        )

    details["heap_growth_bytes"] = total_growth_bytes
    details["heap_peak_bytes"] = peak_bytes
    details["source_file"] = source_file or "unknown"
    details["heap_allocations"] = allocations
    return details


def collect_heap_trace(
    before_snapshot: tracemalloc.Snapshot,
    after_snapshot: tracemalloc.Snapshot,
    source_file: str,
    function_name: str,
    limit: int = 5,
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Compare snapshots and keep the positive allocation deltas for the target source."""
    source_path = _normalize_path(source_file) if source_file else None
    growth_candidates: List[Dict[str, Any]] = []
    fallback_candidates: List[Dict[str, Any]] = []
    total_growth_bytes = 0

    for stat in after_snapshot.compare_to(before_snapshot, "lineno"):
        if stat.size_diff <= 0:
            continue

        traceback_frame = stat.traceback[0]
        frame_path = _normalize_path(traceback_frame.filename)
        candidate = {
            "file": traceback_frame.filename,
            "line": traceback_frame.lineno,
            "size_diff": int(stat.size_diff),
            "count_diff": int(stat.count_diff),
            "traceback": [f"{frame.filename}:{frame.lineno}" for frame in stat.traceback[:5]],
            "allocation_site": f"{traceback_frame.filename}:{traceback_frame.lineno}",
            "function_name": function_name,
        }
        fallback_candidates.append(candidate)

        if source_path is None or frame_path == source_path:
            growth_candidates.append(candidate)
            total_growth_bytes += int(stat.size_diff)

    if source_path is not None and not growth_candidates:
        growth_candidates = fallback_candidates[:limit]
        total_growth_bytes = sum(candidate["size_diff"] for candidate in growth_candidates)

    return total_growth_bytes, len(growth_candidates), growth_candidates[:limit]


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
    if not inputs:
        # Run one dynamic probe with no positional input when the CLI omits --input.
        inputs = [None]
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

    harness = PythonFunctionTestHarness(func, timeout=timeout_seconds, prefer_main_thread=True)
    all_results = []
    source_file = resolve_source_file(target, func)
    tracemalloc.start(25)

    try:
        for input_data in inputs:
            for _ in range(repeat):
                gc.collect()
                before_snapshot = tracemalloc.take_snapshot()

                start_time = time.time()
                result = harness.run_test(input_data)
                execution_time_ms = int((time.time() - start_time) * 1000)

                gc.collect()
                after_snapshot = tracemalloc.take_snapshot()
                current_bytes, peak_bytes = tracemalloc.get_traced_memory()
                total_growth_bytes, matched_allocation_count, allocations = collect_heap_trace(
                    before_snapshot,
                    after_snapshot,
                    source_file,
                    function_name,
                )
                heap_summary = summarize_heap_allocations(allocations, total_growth_bytes, function_name)
                heap_details = convert_heap_allocations_to_protocol(
                    allocations,
                    source_file,
                    function_name,
                    total_growth_bytes,
                    int(peak_bytes),
                )

                escape_detected = bool(total_growth_bytes > 0 or matched_allocation_count > 0)

                all_results.append({
                    "input_data": input_data,
                    "success": result.success,
                    "crashed": result.crashed,
                    "output": result.output,
                    "error": result.error,
                    "execution_time_ms": execution_time_ms,
                    "escape_detected": escape_detected,
                    "escape_details": heap_details if escape_detected else empty_escape_details(),
                    "heap_growth_bytes": int(total_growth_bytes),
                    "heap_current_bytes": int(current_bytes),
                    "heap_peak_bytes": int(peak_bytes),
                    "heap_summary": heap_summary,
                })
    finally:
        tracemalloc.stop()
    
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
            self.escape_details = data.get("heap_summary", "")
    
    result_proxies = [TestResultProxy(r) for r in all_results]
    analysis = detector.categorize_results(result_proxies)
    vulnerabilities = [
        {
            "input": v.input,
            "vulnerability_type": v.vulnerability_type,
            "severity": v.severity,
            "description": v.error_message,
            "escape_details": next(
                (r["escape_details"] for r in all_results if r["input_data"] == v.input and r["escape_detected"]),
                empty_escape_details(),
            ),
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
