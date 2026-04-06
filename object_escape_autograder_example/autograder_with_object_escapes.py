"""
Simple autograder example that mirrors the report's first-chapter behavior.

The handler creates a rich SubmissionContext, queues the full object for later
reporting, and returns only a small summary. That keeps the object escape
pattern clear without adding extra demo layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# Long-lived queue used by deferred report work.
GLOBAL_REPORT_QUEUE: list["SubmissionContext"] = []


@dataclass
class SubmissionContext:
    """Rich request state created by the submission handler."""

    # Assignment currently being graded.
    assignment_id: str
    # Student who submitted the work.
    student_id: str
    # Rubric version in effect for this run.
    rubric_version: str
    # Temporary directory used by the handler.
    temp_build_path: str
    # Quick pass/fail decision for the request.
    quick_status: str
    # Test and runtime settings captured with the submission.
    test_config: dict[str, object]
    # Diagnostic notes that will be reported later.
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class SubmissionSummary:
    """Compact summary returned to the caller after the handler finishes."""

    # Assignment identifier echoed back to the caller.
    assignment_id: str
    # Student identifier echoed back to the caller.
    student_id: str
    # Final status for the request.
    status: str
    # Points awarded for the quick grading decision.
    points_awarded: int
    # Short human-readable outcome message.
    feedback: str


def build_report_job(context: SubmissionContext) -> Callable[[], None]:
    """Create deferred report work that captures the full context."""

    # Closure escape: the returned function keeps the original context alive.
    # The print call makes the retained fields visible in the demo output.
    return lambda: print(
        "[Report] "
        f"{context.assignment_id}/{context.student_id} "
        f"rubric={context.rubric_version} "
        f"temp={context.temp_build_path} "
        f"status={context.quick_status} "
        f"diagnostics={'; '.join(context.diagnostics)}"
    )


def analyze_entry(student_id: str) -> SubmissionSummary:
    """Analyzer-friendly entrypoint that mirrors the report's handler workflow."""

    # The handler creates a rich context object and keeps it alive for reporting.
    context = SubmissionContext(
        # Fixed assignment id for the demo scenario.
        assignment_id="assignment-07",
        # Use the target input as the student id.
        student_id=student_id,
        # Keep the rubric version in the retained request state.
        rubric_version="2026.04",
        # Keep a temporary path in the retained object.
        temp_build_path=rf"C:\temp\graphene\{student_id}",
        # Start in a pending state before grading completes.
        quick_status="pending",
        # Store the grading configuration together with the request data.
        test_config={
            # Number of checks represented by this simplified example.
            "test_count": 3,
            # Timeout included for realism, even though the demo is small.
            "timeout_seconds": 5,
            # Language tag carried through the context.
            "language": "python",
        },
    )

    # A simple id rule controls whether this submission passes or fails.
    if student_id.endswith("1"):
        # Pass path: mark the context as successful.
        context.quick_status = "pass"
        # Keep a short note for the deferred report.
        context.diagnostics.append("quick grading passed")
    else:
        # Fail path: mark the context as unsuccessful.
        context.quick_status = "fail"
        # Keep a short note for the deferred report.
        context.diagnostics.append("quick grading failed")

    # Global escape: the full context is placed on a module-level queue.
    GLOBAL_REPORT_QUEUE.append(context)

    # Closure escape: the deferred report job captures the full context directly.
    report_job = build_report_job(context)
    # Run the deferred report immediately to show the retained state.
    report_job()

    # Return only a compact summary, not the full context.
    points_awarded = 10 if context.quick_status == "pass" else 0
    # The returned object is intentionally smaller than the retained context.
    return SubmissionSummary(
        # Copy the assignment id into the summary.
        assignment_id=context.assignment_id,
        # Copy the student id into the summary.
        student_id=context.student_id,
        # Return the quick pass/fail decision.
        status=context.quick_status,
        # Return the computed score.
        points_awarded=points_awarded,
        # Keep the message short and predictable.
        feedback="Deferred report job queued",
    )


if __name__ == "__main__":
    # Run one sample submission when the file is executed directly.
    print(analyze_entry("s001"))
