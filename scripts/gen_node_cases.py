#!/usr/bin/env python3
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PYTHON_CASES_DIR = ROOT / "tests" / "python" / "cases"
NODE_CASES_DIR = ROOT / "tests" / "nodejs" / "cases"
CASE_RE = re.compile(r"^case_(\d{3})_(.+)\.py$")


def to_camel_case(parts):
  return "".join(part[:1].upper() + part[1:] for part in parts if part)


def parse_slug(slug):
  if slug.startswith("_"):
    return "", slug[1:]
  stage, _, entity = slug.partition("_")
  return stage, entity


def build_case_js(idx, slug):
  stage, entity = parse_slug(slug)
  task_name = slug
  fn_name = f"case{idx}{to_camel_case(slug.split('_'))}"
  case_id = f"case_{idx}"

  header = [
    "/**",
    f" * Task case {idx}: {task_name}",
    " */",
    "",
    "const retainedCache = new Map();",
    "const retainedAudit = [];",
    "const retainedHandlers = [];",
    "",
    f"function {fn_name}(input) {{",
    f"  // Task: {stage or 'internal'} {entity} records and prepare transport-ready payload.",
    f"  const taskName = '{task_name}';",
    "  const raw = input || 'sample';",
    "  const payload = {",
    "    task: taskName,",
    f"    entity: '{entity}',",
    f"    stage: '{stage}',",
    "    input: raw,",
    "    checksum: `${taskName}:${raw.length}`,",
    "  };",
  ]

  selector = int(idx) % 5
  if selector == 1:
    behavior = [
      "  // ESCAPE: payload is promoted to module-level retained cache for cross-request reuse.",
      f"  retainedCache.set('{case_id}', payload);",
      "  return 'ok';",
    ]
  elif selector == 2:
    behavior = [
      "  // ESCAPE: payload is appended to retained audit state, outliving function scope.",
      "  retainedAudit.push(payload);",
      "  return 'ok';",
    ]
  elif selector == 3:
    behavior = [
      "  // ESCAPE: closure captures payload and handler is retained in module-level handlers.",
      "  retainedHandlers.push(() => payload.checksum);",
      "  return 'ok';",
    ]
  elif selector == 4:
    behavior = [
      "  // ESCAPE: payload is nested inside retained envelope persisted to retained audit state.",
      "  const envelope = { kind: 'audit-envelope', payload };",
      "  retainedAudit.push(envelope);",
      "  return 'ok';",
    ]
  else:
    behavior = [
      "  // SAFE: payload remains local; only primitive checksum string is returned.",
      "  return payload.checksum;",
    ]

  footer = [
    "}",
    "",
    "module.exports = {",
    f"  {fn_name},",
    "};",
    "",
  ]

  return "\n".join(header + behavior + footer)


def main():
  NODE_CASES_DIR.mkdir(parents=True, exist_ok=True)

  for path in NODE_CASES_DIR.glob("case_*.js"):
    path.unlink()

  python_cases = sorted(PYTHON_CASES_DIR.glob("case_*.py"))
  generated = 0

  for py_case in python_cases:
    match = CASE_RE.match(py_case.name)
    if not match:
      continue
    idx, slug = match.group(1), match.group(2)
    node_name = f"case_{idx}_{slug}.js"
    node_path = NODE_CASES_DIR / node_name
    node_path.write_text(build_case_js(idx, slug), encoding="utf-8")
    generated += 1

  print(f"Generated {generated} Node cases in {NODE_CASES_DIR}")


if __name__ == "__main__":
  main()

