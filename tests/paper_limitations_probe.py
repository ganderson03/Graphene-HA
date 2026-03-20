#!/usr/bin/env python3
"""
Run paper-inspired adversarial cases to expose analyzer limitations.

This probe focuses on limitations discussed in the junior seminar related work:
- Interprocedural precision tradeoffs (Choi et al., Weingarten et al.)
- Scheduler-sensitive dynamic detection limits (ThreadSanitizer-style discussions)
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PaperCase:
    id: str
    language: str
    target: str
    expected_escape: bool
    limitation_theme: str
    source_reference: str
    analysis_mode: str = "both"


def parse_total_escapes(output: str) -> int | None:
    match = re.search(r"total escapes:\s*(\d+)", output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'"total_escapes"\s*:\s*(\d+)', output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def parse_crash(output: str) -> bool:
    match = re.search(r"Crashes:\s*(\d+)", output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1)) > 0
    return False


def compact_error(output: str, fallback: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if "error" in lower or "failed" in lower or "exception" in lower:
            return line[:260]
    if lines:
        return lines[-1][:260]
    return fallback


def detect_escape(root: Path, case: PaperCase, timeout_seconds: int = 8) -> tuple[bool, bool, str, float]:
    started = time.time()
    completed = subprocess.run(
        [
            "uv",
            "run",
            "graphene",
            "analyze",
            case.target,
            "--language",
            case.language,
            "--analysis-mode",
            case.analysis_mode,
            "--input",
            "sample",
            "--repeat",
            "1",
            "--timeout",
            str(timeout_seconds),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds + 20,
    )

    output = f"{completed.stdout}\n{completed.stderr}"
    total_escapes = parse_total_escapes(output)
    crashed = parse_crash(output)

    if total_escapes is not None:
        detected_escape = total_escapes > 0
    else:
        detected_escape = "escape_detected: true" in output.lower() or "escapes detected: 1" in output.lower()

    elapsed_ms = (time.time() - started) * 1000.0

    detail = ""
    if completed.returncode != 0:
        detail = compact_error(output, f"analyze exit code {completed.returncode}")

    return detected_escape, crashed, detail, elapsed_ms


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    cases = [
        PaperCase(
            id="P1",
            language="python",
            target="tests/python/cases/case_101_interprocedural_precision.py:case_101_interprocedural_precision",
            expected_escape=False,
            limitation_theme="Interprocedural/context sensitivity",
            source_reference="Choi et al. (connection-graph interprocedural precision); Weingarten et al.",
            analysis_mode="both",
        ),
        PaperCase(
            id="P2",
            language="javascript",
            target="tests/nodejs/cases/case_101_queue_microtask_escape.js:case101QueueMicrotaskEscape",
            expected_escape=True,
            limitation_theme="Scheduler-sensitive async behavior",
            source_reference="Serebryany & Iskhodzhanov (dynamic schedule-dependent diagnostics)",
            analysis_mode="both",
        ),
        PaperCase(
            id="P3",
            language="go",
            target="tests/go/cases/case_101_transient_goroutine_escape.go:Case101TransientGoroutineEscape",
            expected_escape=True,
            limitation_theme="Transient goroutine lifetime after return",
            source_reference="Thread/race runtime limits + Go escape-analysis precision discussions",
            analysis_mode="dynamic",
        ),
        PaperCase(
            id="P4",
            language="java",
            target="tests/java/target/escape-tests-1.0-SNAPSHOT.jar:com.escape.tests.cases.Case101TransientThreadEscape:execute",
            expected_escape=True,
            limitation_theme="Transient thread lifetime after return",
            source_reference="Runtime detector scheduling sensitivity; Java escape-analysis correctness boundaries",
            analysis_mode="dynamic",
        ),
    ]

    print("=" * 108)
    print("PAPER-INSPIRED LIMITATION PROBE")
    print("=" * 108)

    mismatches = 0
    rows: list[tuple[PaperCase, bool, bool, str, float]] = []

    for idx, case in enumerate(cases, 1):
        expected = "ESCAPE" if case.expected_escape else "SAFE"
        print(f"[{idx}/{len(cases)}] {case.id} {case.language:10} expected={expected:6} theme={case.limitation_theme}")

        detected_escape, crashed, detail, elapsed_ms = detect_escape(root, case)
        actual = "ESCAPE" if detected_escape else "SAFE"
        status = "PASS" if detected_escape == case.expected_escape else "FAIL"
        if status == "FAIL":
            mismatches += 1

        crash_txt = "CRASH" if crashed else "OK"
        if detail:
            print(f"      {status:4} actual={actual:6} run={crash_txt:5} time={elapsed_ms:8.1f}ms note={detail}")
        else:
            print(f"      {status:4} actual={actual:6} run={crash_txt:5} time={elapsed_ms:8.1f}ms")
        rows.append((case, detected_escape, crashed, detail, elapsed_ms))

    print("\n" + "-" * 108)
    print("Per-case rationale")
    print("-" * 108)
    for case, detected_escape, crashed, detail, _ in rows:
        expected = "ESCAPE" if case.expected_escape else "SAFE"
        actual = "ESCAPE" if detected_escape else "SAFE"
        status = "PASS" if detected_escape == case.expected_escape else "FAIL"
        print(f"{case.id} [{status}] {case.language} expected={expected} actual={actual} | {case.source_reference}")

    print("\n" + "=" * 108)
    print(f"Mismatch count: {mismatches}/{len(cases)}")
    print("(mismatch means analyzer output disagreed with expected safety/escape semantics)")
    print("=" * 108)


if __name__ == "__main__":
    main()
