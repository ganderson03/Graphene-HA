#!/usr/bin/env python3
"""
Measure escape detection quality across split case suites.

All language options follow the same workflow:
- Build target from case metadata
- Invoke `uv run graphene analyze` with explicit language
- Parse static summary for total escapes
"""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


CASE_RE = re.compile(r"^case_(\d{3})_(.+)$")
JAVA_CASE_RE = re.compile(r"^Case(\d{3})(.*)$")
LANGUAGE_ORDER = ("python", "javascript", "go", "rust", "java")


@dataclass
class TestCase:
    language: str
    target_file: str
    function_name: str
    expected_escape: bool
    category: str
    description: str


@dataclass
class TestResult:
    case: TestCase
    detected_escape: bool
    elapsed_ms: float
    error: str = ""


def to_camel_case(parts: List[str]) -> str:
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def camel_to_snake(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", value).lower()


def slug_category(slug: str) -> str:
    if slug.startswith("_"):
        return "internal"
    stage, _, _ = slug.partition("_")
    return stage or "internal"


def node_function_name(stem: str) -> str:
    match = CASE_RE.match(stem)
    if not match:
        raise ValueError(f"invalid node case stem: {stem}")
    idx, slug = match.group(1), match.group(2)
    return f"case{idx}{to_camel_case(slug.split('_'))}"


def go_function_name(stem: str) -> str:
    match = CASE_RE.match(stem)
    if not match:
        raise ValueError(f"invalid go case stem: {stem}")
    idx, slug = match.group(1), match.group(2)
    return f"Case{idx}{to_camel_case(slug.split('_'))}"


def expected_escape_from_file(file_path: Path) -> bool:
    text = file_path.read_text(encoding="utf-8")
    return "SAFE:" not in text


def category_from_stem(language: str, stem: str) -> str:
    if language == "java":
        match = JAVA_CASE_RE.match(stem)
        if not match:
            return "internal"
        suffix = camel_to_snake(match.group(2)).lstrip("_")
        if not suffix:
            return "internal"
        return slug_category(suffix)

    match = CASE_RE.match(stem)
    if not match:
        return "internal"
    return slug_category(match.group(2))


def case_glob(language: str) -> tuple[str, str]:
    if language == "python":
        return "tests/python/cases", "case_*.py"
    if language == "javascript":
        return "tests/nodejs/cases", "case_*.js"
    if language == "go":
        return "tests/go/cases", "case_*.go"
    if language == "rust":
        return "tests/rust/cases", "case_*.rs"
    if language == "java":
        return "tests/java/src/main/java/com/escape/tests/cases", "Case*.java"
    raise ValueError(f"unsupported language: {language}")


def function_name_for_case(language: str, stem: str) -> str:
    if language == "python":
        return stem
    if language == "javascript":
        return node_function_name(stem)
    if language == "go":
        return go_function_name(stem)
    if language == "rust":
        return stem
    if language == "java":
        return "execute"
    raise ValueError(f"unsupported language: {language}")


def collect_cases(root: Path, language: str, limit: int) -> List[TestCase]:
    directory, pattern = case_glob(language)
    cases_dir = root / directory
    found: List[TestCase] = []

    for file_path in sorted(cases_dir.glob(pattern)):
        stem = file_path.stem
        try:
            function_name = function_name_for_case(language, stem)
        except ValueError:
            continue

        category = category_from_stem(language, stem)
        found.append(
            TestCase(
                language=language,
                target_file=file_path.relative_to(root).as_posix(),
                function_name=function_name,
                expected_escape=expected_escape_from_file(file_path),
                category=category,
                description=f"{stem} ({category})",
            )
        )

        if limit and len(found) >= limit:
            break

    return found


def parse_total_escapes(output: str) -> Optional[int]:
    match = re.search(r"total escapes:\s*(\d+)", output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'"total_escapes"\s*:\s*(\d+)', output, flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def compact_error(output: str, fallback: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if "error" in lowered or "failed" in lowered:
            return line[:240]
    if lines:
        return lines[-1][:240]
    return fallback


def detect_escape_with_cli(root: Path, case: TestCase, timeout_seconds: int) -> TestResult:
    started = time.time()
    target = f"{case.target_file}:{case.function_name}"

    try:
        completed = subprocess.run(
            [
                "uv",
                "run",
                "graphene",
                "analyze",
                target,
                "--language",
                case.language,
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
            timeout=timeout_seconds + 15,
        )

        output = f"{completed.stdout}\n{completed.stderr}"
        parsed_total = parse_total_escapes(output)

        if parsed_total is not None:
            detected = parsed_total > 0
        else:
            lowered = output.lower()
            detected = "detected: true" in lowered

        error = ""
        if completed.returncode != 0:
            error = compact_error(output, f"analyze failed with exit code {completed.returncode}")

        return TestResult(
            case=case,
            detected_escape=detected,
            elapsed_ms=(time.time() - started) * 1000.0,
            error=error,
        )
    except Exception as exc:
        return TestResult(case=case, detected_escape=False, elapsed_ms=(time.time() - started) * 1000.0, error=str(exc))


def classify(result: TestResult) -> str:
    expected = result.case.expected_escape
    actual = result.detected_escape
    if expected and actual:
        return "tp"
    if not expected and not actual:
        return "tn"
    if expected and not actual:
        return "fn"
    return "fp"


def print_summary(results: List[TestResult]) -> None:
    buckets: Dict[str, Dict[str, int]] = defaultdict(lambda: {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "total": 0})

    for result in results:
        key = result.case.language
        tag = classify(result)
        buckets[key][tag] += 1
        buckets[key]["total"] += 1

    print("\n" + "=" * 88)
    print("SUMMARY")
    print("=" * 88)
    print(f"{'Language':12} {'Total':>7} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4} {'Accuracy':>10} {'Precision':>10} {'Recall':>8}")
    print("-" * 88)

    for language in LANGUAGE_ORDER:
        stats = buckets.get(language)
        if not stats:
            continue
        total = stats["total"]
        tp = stats["tp"]
        tn = stats["tn"]
        fp = stats["fp"]
        fn = stats["fn"]
        accuracy = ((tp + tn) / total) if total else 0.0
        precision = (tp / (tp + fp)) if (tp + fp) else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) else 0.0
        print(f"{language:12} {total:7} {tp:4} {tn:4} {fp:4} {fn:4} {accuracy:9.1%} {precision:9.1%} {recall:7.1%}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure split-case escape detection success rate")
    parser.add_argument("--language", choices=["all", *LANGUAGE_ORDER], default="all")
    parser.add_argument("--limit", type=int, default=0, help="Limit test cases per language (0 = all)")
    parser.add_argument("--timeout", type=int, default=5, help="Per-test timeout seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent

    selected: List[TestCase] = []
    languages = LANGUAGE_ORDER if args.language == "all" else (args.language,)
    for language in languages:
        selected.extend(collect_cases(root, language, args.limit))

    if not selected:
        print("No test cases selected.")
        return

    print("=" * 88)
    print(f"Running {len(selected)} split-case tests")
    print("=" * 88)

    results: List[TestResult] = []
    for index, case in enumerate(selected, 1):
        print(f"[{index:03d}/{len(selected):03d}] {case.language:10} {case.function_name:32}", end=" ", flush=True)
        result = detect_escape_with_cli(root, case, args.timeout)
        results.append(result)

        if result.error:
            print(f"ERROR ({result.error})")
            continue

        expected = "ESCAPE" if case.expected_escape else "SAFE"
        actual = "ESCAPE" if result.detected_escape else "SAFE"
        status = "PASS" if case.expected_escape == result.detected_escape else "FAIL"
        print(f"{status:4} expected={expected:6} actual={actual:6} time={result.elapsed_ms:7.1f}ms")

    print_summary(results)


if __name__ == "__main__":
    main()
