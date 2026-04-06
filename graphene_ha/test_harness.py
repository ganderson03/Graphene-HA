import os
import pickle
import queue
import time
import multiprocessing
import asyncio
import sys
import threading
import io
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from pathlib import Path


def _invoke_target(func, input_data, fixed_kwargs):
    """Invoke target function, supporting both zero-arg and single-arg targets."""
    if input_data is None:
        try:
            return func(**fixed_kwargs)
        except TypeError:
            # Fallback to legacy single-input call shape when target expects one arg.
            return func(input_data, **fixed_kwargs)
    return func(input_data, **fixed_kwargs)

@dataclass
class TestResult:
    input_data: str
    success: bool
    crashed: bool
    output: str
    error: str
    return_code: int
    anomaly: bool = False
    escape_detected: bool = False
    escape_details: str = ""
    returned_value_type: str = ""  # Type of returned value for escape analysis
    raised_exception: bool = False


class PythonFunctionTestHarness:
    """Test harness for object escape analysis.
    
    Combines static AST analysis with dynamic verification to:
    1. Validate function executes without error (dynamic)
    2. Capture return value type for escape inference (dynamic)
    3. Cross-reference with static escape findings
    """

    def __init__(self, func, timeout=5.0, prefer_thread=False, prefer_main_thread=False, **fixed_kwargs):
        self.func = func
        self.timeout = timeout
        self.prefer_thread = prefer_thread
        self.prefer_main_thread = prefer_main_thread
        self.fixed_kwargs = fixed_kwargs

    def run_test(self, input_data):
        """Run test and capture dynamic information for escape verification."""
        if self.prefer_main_thread:
            return self._run_in_main_thread(input_data)
        if self.prefer_thread:
            return self._run_in_thread(input_data)
        if self._can_pickle(self.func):
            return self._run_in_process(input_data)
        return self._run_in_thread(input_data)

    def _can_pickle(self, func):
        try:
            pickle.dumps(func)
            return True
        except Exception:
            return False

    def _analyze_return_type(self, value) -> str:
        """Analyze type of returned value for escape verification."""
        if value is None:
            return "None"
        type_name = type(value).__name__
        if hasattr(value, '__self__'):  # Method
            return f"method_{type_name}"
        if callable(value):  # Closure or function
            return f"callable_{type_name}"
        if isinstance(value, (list, dict, tuple, set)):
            return f"container_{type_name}"
        return f"object_{type_name}"

    def _run_in_process(self, input_data):
        """Run function in separate process."""
        ctx = multiprocessing.get_context("spawn")
        result_queue = ctx.Queue()

        def worker(func, input_data, fixed_kwargs, result_queue):
            try:
                buffer = io.StringIO()
                with redirect_stdout(buffer), redirect_stderr(buffer):
                    returned_value = _invoke_target(func, input_data, fixed_kwargs)
                captured = buffer.getvalue()
                output = captured if captured else str(returned_value)
                error = ""
                crashed = False
                returned_type = type(returned_value).__name__
            except Exception as e:
                output = ""
                error = f"{type(e).__name__}: {str(e)}"
                crashed = True
                returned_type = "exception"
            result_queue.put({
                "output": output,
                "error": error,
                "crashed": crashed,
                "returned_type": returned_type
            })
            result_queue.close()
            result_queue.join_thread()
            os._exit(0)

        proc = ctx.Process(target=worker, args=(self.func, input_data, self.fixed_kwargs, result_queue))
        proc.start()
        proc.join(timeout=self.timeout)

        if proc.is_alive():
            proc.terminate()
            proc.join()
            time.sleep(0.2)
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error=f"Process timeout after {self.timeout}s",
                return_code=-1,
                anomaly=True,
                escape_detected=False,
                escape_details="",
                returned_value_type="timeout"
            )

        time.sleep(0.1)
        try:
            payload = result_queue.get_nowait()
        except queue.Empty:
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error=f"Child process did not return result",
                return_code=-1,
                anomaly=True,
                escape_detected=False,
                escape_details="",
                returned_value_type="no_response"
            )

        if payload.get("crashed"):
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error=payload.get("error", ""),
                return_code=-1,
                escape_detected=False,
                escape_details="",
                returned_value_type=payload.get("returned_type", "exception"),
                raised_exception=True
            )

        return TestResult(
            input_data=input_data,
            success=True,
            crashed=False,
            output=payload.get("output", ""),
            error="",
            return_code=0,
            escape_detected=False,
            escape_details="",
            returned_value_type=payload.get("returned_type", "")
        )

    def _run_in_thread(self, input_data):
        """Run function in separate thread."""
        result = {"output": None, "error": None, "completed": False, "returned_type": ""}

        def run_with_timeout():
            try:
                buffer = io.StringIO()
                with redirect_stdout(buffer), redirect_stderr(buffer):
                    returned_value = _invoke_target(self.func, input_data, self.fixed_kwargs)
                captured = buffer.getvalue()
                result["output"] = captured if captured else str(returned_value)
                result["returned_type"] = self._analyze_return_type(returned_value)
                result["completed"] = True
            except Exception as e:
                result["error"] = f"{type(e).__name__}: {str(e)}"
                result["returned_type"] = "exception"
                result["completed"] = True

        try:
            t = threading.Thread(target=run_with_timeout, daemon=True)
            t.start()
            t.join(timeout=self.timeout)

            if not result["completed"]:
                time.sleep(0.1)
                return TestResult(
                    input_data=input_data,
                    success=False,
                    crashed=True,
                    output="",
                    error=f"Thread timeout after {self.timeout}s",
                    return_code=-1,
                    anomaly=True,
                    escape_detected=False,
                    escape_details="",
                    returned_value_type="timeout"
                )

            if result["error"]:
                return TestResult(
                    input_data=input_data,
                    success=False,
                    crashed=True,
                    output="",
                    error=result["error"],
                    return_code=-1,
                    escape_detected=False,
                    escape_details="",
                    returned_value_type=result.get("returned_type", "exception"),
                    raised_exception=True
                )

            return TestResult(
                input_data=input_data,
                success=True,
                crashed=False,
                output=result["output"] or "",
                error="",
                return_code=0,
                escape_detected=False,
                escape_details="",
                returned_value_type=result.get("returned_type", "")
            )
        except Exception as e:
            import traceback
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error=f"{type(e).__name__}: {str(e)}",
                return_code=-1,
                escape_detected=False,
                escape_details="",
                returned_value_type="exception",
                raised_exception=True
            )

    def _run_in_main_thread(self, input_data):
        """Run function in main thread."""
        start = time.time()
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer), redirect_stderr(buffer):
                returned_value = _invoke_target(self.func, input_data, self.fixed_kwargs)
            captured = buffer.getvalue()
            output = captured if captured else str(returned_value)
            error = ""
            crashed = False
            returned_type = self._analyze_return_type(returned_value)
        except Exception as e:
            output = ""
            error = f"{type(e).__name__}: {str(e)}"
            crashed = True
            returned_type = "exception"

        elapsed = time.time() - start

        if elapsed > self.timeout:
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error="Timeout exceeded",
                return_code=-1,
                anomaly=True,
                escape_detected=False,
                escape_details="",
                returned_value_type="timeout"
            )

        if crashed:
            return TestResult(
                input_data=input_data,
                success=False,
                crashed=True,
                output="",
                error=error,
                return_code=-1,
                escape_detected=False,
                escape_details="",
                returned_value_type=returned_type,
                raised_exception=True
            )

        return TestResult(
            input_data=input_data,
            success=True,
            crashed=False,
            output=output,
            error="",
            return_code=0,
            escape_detected=False,
            escape_details="",
            returned_value_type=returned_type
        )

