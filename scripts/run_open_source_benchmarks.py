#!/usr/bin/env python3
"""Clone open-source projects and run Graphene static analysis samples.

This script is intended to complement synthetic benchmarks with real-world code,
similar to evaluation setups used in escape-analysis papers.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OSS_ROOT = ROOT / "benchmarks" / "oss_sources"


@dataclass(frozen=True)
class Project:
    language: str
    repo: str


PROJECTS = [
    Project("python", "psf/requests"),
    Project("python", "pallets/flask"),
    Project("javascript", "axios/axios"),
    Project("javascript", "expressjs/express"),
    Project("go", "gin-gonic/gin"),
    Project("go", "spf13/cobra"),
    Project("rust", "serde-rs/serde"),
    Project("rust", "tokio-rs/bytes"),
    Project("java", "google/gson"),
    Project("java", "google/guava"),
]

SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "target",
    "dist",
    "build",
    "out",
    ".venv",
    "venv",
}

EXTENSION_BY_LANGUAGE = {
    "python": ".py",
    "javascript": ".js",
    "go": ".go",
    "rust": ".rs",
    "java": ".java",
}

PATTERNS = {
    "python": re.compile(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "javascript": re.compile(r"^(?:async\s+)?function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(", re.MULTILINE),
    "go": re.compile(r"^func\s+(?:\([^\)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE),
    "rust": re.compile(r"^(?:pub\s+)?fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
    "java": re.compile(r"(?:public|private|protected)\s+static\s+[\w<>,\[\]\s]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("),
}


@dataclass
class Candidate:
    language: str
    repo: str
    file_path: Path
    function: str


@dataclass
class RunResult:
    language: str
    repo: str
    target: str
    success: bool
    elapsed_ms: float
    exit_code: int
    note: str


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str, float]:
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return proc.returncode, proc.stdout, proc.stderr, elapsed_ms


def clone_project(project: Project, refresh: bool) -> Path:
    dest = OSS_ROOT / project.language / project.repo.replace("/", "__")
    if refresh and dest.exists():
        for _ in range(3):
            try:
                subprocess.run(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", "HEAD"], check=False)
                subprocess.run(["git", "-C", str(dest), "reset", "--hard", "FETCH_HEAD"], check=False)
                return dest
            except Exception:
                break
    if dest.exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{project.repo}.git"
    rc, out, err, _ = run_command(["git", "clone", "--depth", "1", url, str(dest)])
    if rc != 0:
        raise RuntimeError(f"clone failed for {project.repo}: {(err or out).strip()[:300]}")
    return dest


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def collect_candidates(project: Project, root: Path, per_project: int) -> list[Candidate]:
    ext = EXTENSION_BY_LANGUAGE[project.language]
    pattern = PATTERNS[project.language]
    found: list[Candidate] = []

    for file_path in root.rglob(f"*{ext}"):
        rel = file_path.relative_to(root)
        if should_skip(rel):
            continue
        if project.language == "python" and file_path.name == "__init__.py":
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for m in pattern.finditer(text):
            fn = m.group(1)
            if fn.startswith("_"):
                continue
            found.append(Candidate(project.language, project.repo, file_path, fn))
            if len(found) >= per_project:
                return found

    return found


def candidate_target(candidate: Candidate) -> str:
    rel = candidate.file_path.relative_to(ROOT).as_posix()
    return f"{rel}:{candidate.function}"


def analyze_candidate(candidate: Candidate, log_dir: str, timeout: float) -> RunResult:
    target = candidate_target(candidate)
    cmd = [
        sys.executable,
        str(ROOT / "graphene_ha" / "cli.py"),
        "analyze",
        target,
        "--language",
        candidate.language,
        "--analysis-mode",
        "static",
        "--timeout",
        str(timeout),
        "--log-dir",
        log_dir,
    ]
    rc, out, err, elapsed = run_command(cmd, cwd=ROOT)
    note = ""
    if rc != 0:
        note = (err or out).strip().replace("\n", " ")[:300]
    return RunResult(candidate.language, candidate.repo, target, rc == 0, elapsed, rc, note)


def write_report(path: Path, rows: list[RunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "language",
                "repo",
                "target",
                "success",
                "elapsed_ms",
                "exit_code",
                "note",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "language": r.language,
                    "repo": r.repo,
                    "target": r.target,
                    "success": str(r.success).lower(),
                    "elapsed_ms": f"{r.elapsed_ms:.2f}",
                    "exit_code": r.exit_code,
                    "note": r.note,
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Graphene static analysis on sampled open-source projects")
    parser.add_argument("--per-project", type=int, default=25, help="Max sampled functions per project (default: 25)")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-target timeout in seconds (default: 5)")
    parser.add_argument("--log-dir", default="logs_oss_bench", help="Graphene log directory for OSS runs")
    parser.add_argument("--report", default="benchmarks/oss_benchmark_report.csv", help="CSV report output path")
    parser.add_argument("--refresh", action="store_true", help="Refresh existing clones with git fetch/reset")
    parser.add_argument("--clone-only", action="store_true", help="Clone/sync repos and exit without analysis")
    args = parser.parse_args()

    if not shutil_which("git"):
        print("ERROR: git executable is required", file=sys.stderr)
        return 2

    rows: list[RunResult] = []
    total_candidates = 0

    for project in PROJECTS:
        print(f"[clone] {project.language} {project.repo}")
        try:
            repo_path = clone_project(project, refresh=args.refresh)
        except Exception as exc:
            rows.append(RunResult(project.language, project.repo, "<clone>", False, 0.0, 1, str(exc)[:300]))
            continue

        if args.clone_only:
            continue

        candidates = collect_candidates(project, repo_path, args.per_project)
        total_candidates += len(candidates)
        print(f"[sample] {project.repo}: {len(candidates)} targets")

        for cand in candidates:
            rows.append(analyze_candidate(cand, log_dir=args.log_dir, timeout=args.timeout))

    if args.clone_only:
        print("Done cloning repositories.")
        return 0

    report_path = ROOT / args.report
    write_report(report_path, rows)

    total = len(rows)
    succeeded = sum(1 for r in rows if r.success)
    failed = total - succeeded
    print(f"Done. candidates={total_candidates} runs={total} success={succeeded} failed={failed}")
    print(f"Report: {report_path}")
    return 0 if failed == 0 else 1


def shutil_which(name: str) -> str | None:
    try:
        import shutil

        return shutil.which(name)
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
