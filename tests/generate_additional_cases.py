#!/usr/bin/env python3
"""Generate case_101..case_200 suites across all languages.

New cases are intentionally designed to stress detectors with patterns that can
induce false positives/false negatives:
- ESCAPE-labeled cases with indirect/conditional/asynchronous retention.
- SAFE-labeled cases with decoy retention names or dead branches.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

PY_CASES = ROOT / "python" / "cases"
JS_CASES = ROOT / "nodejs" / "cases"
GO_CASES = ROOT / "go" / "cases"
RUST_CASES = ROOT / "rust" / "cases"
JAVA_CASES = ROOT / "java" / "src" / "main" / "java" / "com" / "escape" / "tests" / "cases"
RUST_LIB = ROOT / "rust" / "lib.rs"

VARIANTS = [
    ("alias_shadow_cache", True),
    ("deferred_sink_gate", True),
    ("closure_chain_async", True),
    ("indirect_container_write", True),
    ("thread_handoff_late", True),
    ("decoy_retained_string", False),
    ("dead_branch_global", False),
    ("local_cache_named_retained", False),
    ("serialized_copy_only", False),
    ("closure_no_escape", False),
]


def to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def make_ident(idx: int) -> tuple[str, bool]:
    variant, is_escape = VARIANTS[(idx - 101) % len(VARIANTS)]
    batch = ((idx - 101) // len(VARIANTS)) + 1
    slug = f"{variant}_{batch:02d}"
    return slug, is_escape


def py_content(idx: int, slug: str, is_escape: bool) -> str:
    fn_name = f"case_{idx:03d}_{slug}"
    if slug.startswith("alias_shadow_cache"):
        body = f"""    alias = payload\n    # ESCAPE: alias of payload is stored in retained cache (aliasing false-negative stress).\n    RETAINED_CACHE['case_{idx:03d}'] = alias\n    return 'ok'\n"""
    elif slug.startswith("deferred_sink_gate"):
        body = f"""    if raw.startswith('x'):\n        # ESCAPE: conditional sink persists payload only on specific branch.\n        RETAINED_AUDIT.append(payload)\n    return 'ok'\n"""
    elif slug.startswith("closure_chain_async"):
        body = """    def handler() -> str:\n        return payload['input']\n    # ESCAPE: closure captures payload and retained handler outlives function scope.\n    RETAINED_HANDLERS.append(handler)\n    return 'ok'\n"""
    elif slug.startswith("indirect_container_write"):
        body = """    envelope = {'wrapped': payload}\n    # ESCAPE: payload is indirectly persisted through nested container indirection.\n    RETAINED_AUDIT.append(envelope['wrapped'])\n    return 'ok'\n"""
    elif slug.startswith("thread_handoff_late"):
        body = """    import threading\n    # ESCAPE: payload is captured by background thread closure.\n    threading.Thread(target=lambda: RETAINED_AUDIT.append(payload), daemon=True).start()\n    return 'ok'\n"""
    elif slug.startswith("decoy_retained_string"):
        body = """    marker = 'RETAINED_CACHE is only a string marker, not a sink'\n    _ = marker + payload['task']\n    # SAFE: no object escapes local scope; only primitive output leaves.\n    return payload['checksum']\n"""
    elif slug.startswith("dead_branch_global"):
        body = f"""    if False:\n        RETAINED_CACHE['case_{idx:03d}'] = payload\n    # SAFE: sink exists only in dead branch and never executes.\n    return payload['checksum']\n"""
    elif slug.startswith("local_cache_named_retained"):
        body = """    retained_cache_local = {}\n    retained_cache_local['tmp'] = payload\n    # SAFE: payload is only stored in local container that dies at return.\n    return payload['checksum']\n"""
    elif slug.startswith("serialized_copy_only"):
        body = """    import json\n    serialized = json.dumps(payload)\n    # SAFE: only serialized primitive string leaves, payload object does not escape.\n    return serialized\n"""
    else:
        body = """    def consume() -> str:\n        return payload['task']\n    _ = consume()\n    # SAFE: closure is invoked locally and never retained.\n    return payload['checksum']\n"""

    return f'''"""\nTask case {idx:03d}: {slug} false-positive/false-negative stress pattern.\n"""\n\nRETAINED_CACHE = {{}}\nRETAINED_AUDIT = []\nRETAINED_HANDLERS = []\n\ndef {fn_name}(input_data):\n    task_name = '{slug}'\n    raw = input_data or 'sample'\n    payload = {{\n        'task': task_name,\n        'entity': 'stress',\n        'stage': 'evaluation',\n        'input': raw,\n        'checksum': f'{{task_name}}:{{len(raw)}}',\n    }}\n{body}'''


def js_content(idx: int, slug: str) -> str:
    fn_camel = f"case{idx:03d}{to_pascal(slug)}"
    if slug.startswith("alias_shadow_cache"):
        body = f"""  const alias = payload;\n  // ESCAPE: alias of payload is retained (aliasing false-negative stress).\n  retainedCache.set('case_{idx:03d}', alias);\n  return 'ok';\n"""
    elif slug.startswith("deferred_sink_gate"):
        body = """  if (raw.startsWith('x')) {\n    // ESCAPE: conditional sink only on selected path.\n    retainedAudit.push(payload);\n  }\n  return 'ok';\n"""
    elif slug.startswith("closure_chain_async"):
        body = """  const handler = () => payload.input;\n  // ESCAPE: retained closure captures payload.\n  retainedHandlers.push(handler);\n  return 'ok';\n"""
    elif slug.startswith("indirect_container_write"):
        body = """  const envelope = { wrapped: payload };\n  // ESCAPE: payload stored via indirection into retained sink.\n  retainedAudit.push(envelope.wrapped);\n  return 'ok';\n"""
    elif slug.startswith("thread_handoff_late"):
        body = """  // ESCAPE: async microtask captures payload beyond return edge.\n  queueMicrotask(() => retainedAudit.push(payload));\n  return 'ok';\n"""
    elif slug.startswith("decoy_retained_string"):
        body = """  const marker = 'retainedCache literal only';\n  void (marker + payload.task);\n  // SAFE: no retained sink receives payload object.\n  return payload.checksum;\n"""
    elif slug.startswith("dead_branch_global"):
        body = f"""  if (false) {{\n    retainedCache.set('case_{idx:03d}', payload);\n  }}\n  // SAFE: sink is dead branch only.\n  return payload.checksum;\n"""
    elif slug.startswith("local_cache_named_retained"):
        body = """  const retainedCacheLocal = new Map();\n  retainedCacheLocal.set('tmp', payload);\n  // SAFE: local map does not escape.\n  return payload.checksum;\n"""
    elif slug.startswith("serialized_copy_only"):
        body = """  const serialized = JSON.stringify(payload);\n  // SAFE: only primitive serialized data leaves scope.\n  return serialized;\n"""
    else:
        body = """  const consume = () => payload.task;\n  void consume();\n  // SAFE: closure invoked locally and not retained.\n  return payload.checksum;\n"""

    return f'''/**\n * Task case {idx:03d}: {slug} false-positive/false-negative stress pattern.\n */\n\nconst retainedCache = new Map();\nconst retainedAudit = [];\nconst retainedHandlers = [];\n\nfunction {fn_camel}(input) {{\n  const taskName = '{slug}';\n  const raw = input || 'sample';\n  const payload = {{\n    task: taskName,\n    entity: 'stress',\n    stage: 'evaluation',\n    input: raw,\n    checksum: `${{taskName}}:${{raw.length}}`,\n  }};\n{body}}}\n\nmodule.exports = {{\n  {fn_camel},\n}};\n'''


def go_content(idx: int, slug: str) -> str:
    fn_name = f"Case{idx:03d}{to_pascal(slug)}"
    if slug.startswith("alias_shadow_cache"):
        body = f"""\talias := payload\n\t// ESCAPE: alias retained in package-level sink.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, alias)\n\treturn \"ok\"\n"""
    elif slug.startswith("deferred_sink_gate"):
        body = f"""\tif len(raw) > 0 && raw[0] == 'x' {{\n\t\t// ESCAPE: conditional path retention.\n\t\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, payload)\n\t}}\n\treturn \"ok\"\n"""
    elif slug.startswith("closure_chain_async"):
        body = f"""\thandler := func() string {{ return payload[\"input\"] }}\n\t_ = handler\n\t// ESCAPE: closure payload persisted indirectly via retained metadata map.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, map[string]string{{\"h\": payload[\"input\"]}})\n\treturn \"ok\"\n"""
    elif slug.startswith("indirect_container_write"):
        body = f"""\tenvelope := map[string]map[string]string{{\"wrapped\": payload}}\n\t// ESCAPE: indirection writes payload into retained sink.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, envelope[\"wrapped\"])\n\treturn \"ok\"\n"""
    elif slug.startswith("thread_handoff_late"):
        body = f"""\t// ESCAPE: goroutine captures payload and appends to retained sink.\n\tgo func(p map[string]string) {{\n\t\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, p)\n\t}}(payload)\n\treturn \"ok\"\n"""
    elif slug.startswith("decoy_retained_string"):
        body = """\tmarker := \"retainedCase literal only\"\n\t_ = marker + payload[\"task\"]\n\t// SAFE: no retained sink receives payload object.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("dead_branch_global"):
        body = f"""\tif false {{\n\t\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, payload)\n\t}}\n\t// SAFE: dead branch retention.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("local_cache_named_retained"):
        body = """\tretainedLocal := []map[string]string{}\n\tretainedLocal = append(retainedLocal, payload)\n\t// SAFE: local slice dies at return.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("serialized_copy_only"):
        body = """\tserialized := payload[\"task\"] + ":" + payload[\"input\"]\n\t// SAFE: only primitive string leaves function.\n\treturn serialized\n"""
    else:
        body = """\tconsume := func() string { return payload[\"task\"] }\n\t_ = consume()\n\t// SAFE: closure invoked locally only.\n\treturn payload[\"checksum\"]\n"""

    return f'''package escape_tests\n\nvar retainedCase{idx:03d} = []map[string]string{{}}\n\nfunc {fn_name}(input string) string {{\n\traw := input\n\tif raw == \"\" {{\n\t\traw = \"sample\"\n\t}}\n\tpayload := map[string]string{{\n\t\t\"task\": \"{slug}\",\n\t\t\"entity\": \"stress\",\n\t\t\"stage\": \"evaluation\",\n\t\t\"input\": raw,\n\t\t\"checksum\": \"{slug}:\" + raw,\n\t}}\n{body}}}\n'''


def rust_content(idx: int, slug: str) -> str:
    fn_name = f"case_{idx:03d}_{slug}"
    if slug.startswith("alias_shadow_cache"):
        body = """    let alias = payload;\n    // ESCAPE: alias retained in global cache.\n    RETAINED_CACHE.get_or_init(|| Mutex::new(Vec::new())).lock().expect(\"cache lock\").push(alias);\n    \"ok\".to_string()\n"""
    elif slug.startswith("deferred_sink_gate"):
        body = """    if raw.starts_with('x') {\n        // ESCAPE: conditional retained write on selected path.\n        RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect(\"audit lock\").push(payload);\n    }\n    \"ok\".to_string()\n"""
    elif slug.startswith("closure_chain_async"):
        body = """    let handler_sig = payload.get(\"input\").cloned().unwrap_or_default();\n    // ESCAPE: closure-derived metadata retained globally.\n    RETAINED_HANDLERS.get_or_init(|| Mutex::new(Vec::new())).lock().expect(\"handlers lock\").push(handler_sig);\n    \"ok\".to_string()\n"""
    elif slug.startswith("indirect_container_write"):
        body = """    let mut envelope: HashMap<String, HashMap<String, String>> = HashMap::new();\n    envelope.insert(\"wrapped\".to_string(), payload);\n    // ESCAPE: payload retained through map indirection.\n    let wrapped = envelope.remove(\"wrapped\").expect(\"wrapped\");\n    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect(\"audit lock\").push(wrapped);\n    \"ok\".to_string()\n"""
    elif slug.startswith("thread_handoff_late"):
        body = """    // ESCAPE: thread closure captures payload beyond function return.\n    let payload_for_thread = payload.clone();\n    std::thread::spawn(move || {\n        RETAINED_AUDIT\n            .get_or_init(|| Mutex::new(Vec::new()))\n            .lock()\n            .expect(\"audit lock\")\n            .push(payload_for_thread);\n    });\n    \"ok\".to_string()\n"""
    elif slug.startswith("decoy_retained_string"):
        body = """    let marker = \"RETAINED_CACHE literal only\".to_string();\n    let _ = marker + payload.get(\"task\").map(String::as_str).unwrap_or(\"\");\n    // SAFE: payload object is never persisted globally.\n    payload.get(\"checksum\").cloned().unwrap_or_default()\n"""
    elif slug.startswith("dead_branch_global"):
        body = """    if false {\n        RETAINED_CACHE.get_or_init(|| Mutex::new(Vec::new())).lock().expect(\"cache lock\").push(payload.clone());\n    }\n    // SAFE: dead branch retention cannot execute.\n    payload.get(\"checksum\").cloned().unwrap_or_default()\n"""
    elif slug.startswith("local_cache_named_retained"):
        body = """    let mut retained_local: Vec<HashMap<String, String>> = Vec::new();\n    retained_local.push(payload);\n    // SAFE: local vector does not escape.\n    retained_local[0].get(\"checksum\").cloned().unwrap_or_default()\n"""
    elif slug.startswith("serialized_copy_only"):
        body = """    let serialized = format!(\n        \"{}:{}\",\n        payload.get(\"task\").cloned().unwrap_or_default(),\n        payload.get(\"input\").cloned().unwrap_or_default()\n    );\n    // SAFE: only serialized string escapes.\n    serialized\n"""
    else:
        body = """    let consume = || payload.get(\"task\").cloned().unwrap_or_default();\n    let _ = consume();\n    // SAFE: closure is consumed locally and not retained.\n    payload.get(\"checksum\").cloned().unwrap_or_default()\n"""

    return f'''#![allow(unused)]\n\nuse std::collections::HashMap;\nuse std::sync::{{Mutex, OnceLock}};\n\n#[allow(dead_code)]\nstatic RETAINED_CACHE: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();\n#[allow(dead_code)]\nstatic RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();\n#[allow(dead_code)]\nstatic RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();\n\npub fn {fn_name}(input: String) -> String {{\n    let task_name = \"{slug}\".to_string();\n    let raw = if input.is_empty() {{ \"sample\".to_string() }} else {{ input }};\n    let mut payload: HashMap<String, String> = HashMap::new();\n    payload.insert(\"task\".to_string(), task_name.clone());\n    payload.insert(\"entity\".to_string(), \"stress\".to_string());\n    payload.insert(\"stage\".to_string(), \"evaluation\".to_string());\n    payload.insert(\"input\".to_string(), raw.clone());\n    payload.insert(\"checksum\".to_string(), format!(\"{{}}:{{}}\", task_name, raw.len()));\n{body}}}\n'''


def java_content(idx: int, slug: str) -> str:
    class_name = f"Case{idx:03d}{to_pascal(slug)}"
    if slug.startswith("alias_shadow_cache"):
        body = f"""        Map<String, String> alias = payload;\n        // ESCAPE: alias retained in class-level cache.\n        RETAINED_CACHE.put(\"case_{idx:03d}\", alias);\n        return \"ok\";\n"""
    elif slug.startswith("deferred_sink_gate"):
        body = """        if (raw.startsWith(\"x\")) {\n            // ESCAPE: conditional retained write.\n            RETAINED_AUDIT.add(payload);\n        }\n        return \"ok\";\n"""
    elif slug.startswith("closure_chain_async"):
        body = """        Supplier<String> handler = () -> payload.get(\"input\");\n        // ESCAPE: retained closure captures payload.\n        RETAINED_HANDLERS.add(handler);\n        return \"ok\";\n"""
    elif slug.startswith("indirect_container_write"):
        body = """        Map<String, Object> envelope = new HashMap<>();\n        envelope.put(\"wrapped\", payload);\n        // ESCAPE: payload retained through object indirection.\n        RETAINED_AUDIT.add((Map<String, String>) envelope.get(\"wrapped\"));\n        return \"ok\";\n"""
    elif slug.startswith("thread_handoff_late"):
        body = """        // ESCAPE: payload captured by background thread.\n        new Thread(() -> RETAINED_AUDIT.add(payload)).start();\n        return \"ok\";\n"""
    elif slug.startswith("decoy_retained_string"):
        body = """        String marker = \"RETAINED_CACHE literal only\";\n        String _ignore = marker + payload.get(\"task\");\n        // SAFE: payload object never written to retained sinks.\n        return payload.get(\"checksum\");\n"""
    elif slug.startswith("dead_branch_global"):
        body = f"""        if (false) {{\n            RETAINED_CACHE.put(\"case_{idx:03d}\", payload);\n        }}\n        // SAFE: dead branch retention cannot execute.\n        return payload.get(\"checksum\");\n"""
    elif slug.startswith("local_cache_named_retained"):
        body = """        Map<String, Map<String, String>> retainedLocal = new HashMap<>();\n        retainedLocal.put(\"tmp\", payload);\n        // SAFE: local map does not escape.\n        return payload.get(\"checksum\");\n"""
    elif slug.startswith("serialized_copy_only"):
        body = """        String serialized = payload.toString();\n        // SAFE: only primitive serialized copy leaves scope.\n        return serialized;\n"""
    else:
        body = """        Supplier<String> consume = () -> payload.get(\"task\");\n        consume.get();\n        // SAFE: closure is used locally and never retained.\n        return payload.get(\"checksum\");\n"""

    return f'''package com.escape.tests.cases;\n\nimport java.util.ArrayList;\nimport java.util.HashMap;\nimport java.util.List;\nimport java.util.Map;\nimport java.util.function.Supplier;\n\n/** Task case {idx:03d}: {slug} false-positive/false-negative stress pattern. */\npublic class {class_name} {{\n    private static final Map<String, Map<String, String>> RETAINED_CACHE = new HashMap<>();\n    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();\n    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();\n\n    public static String execute(String input) {{\n        String taskName = \"{slug}\";\n        String raw = (input == null || input.isEmpty()) ? \"sample\" : input;\n        Map<String, String> payload = new HashMap<>();\n        payload.put(\"task\", taskName);\n        payload.put(\"entity\", \"stress\");\n        payload.put(\"stage\", \"evaluation\");\n        payload.put(\"input\", raw);\n        payload.put(\"checksum\", taskName + \":\" + raw.length());\n{body}    }}\n}}\n'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def regenerate_rust_lib() -> None:
    files = sorted(RUST_CASES.glob("case_*.rs"))
    lines = ["#![allow(non_snake_case)]", "", "// Re-export split-case test modules"]
    for f in files:
        stem = f.stem
        lines.append(f'#[path = "cases/{f.name}"]')
        lines.append(f"pub mod {stem};")
    lines.append("")
    RUST_LIB.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for idx in range(101, 201):
        slug, _is_escape = make_ident(idx)

        py_file = PY_CASES / f"case_{idx:03d}_{slug}.py"
        js_file = JS_CASES / f"case_{idx:03d}_{slug}.js"
        go_file = GO_CASES / f"case_{idx:03d}_{slug}.go"
        rust_file = RUST_CASES / f"case_{idx:03d}_{slug}.rs"
        java_class = f"Case{idx:03d}{to_pascal(slug)}"
        java_file = JAVA_CASES / f"{java_class}.java"

        write(py_file, py_content(idx, slug, _is_escape))
        write(js_file, js_content(idx, slug))
        write(go_file, go_content(idx, slug))
        write(rust_file, rust_content(idx, slug))
        write(java_file, java_content(idx, slug))

    regenerate_rust_lib()
    print("Generated cases 101..200 for python, javascript, go, rust, and java.")


if __name__ == "__main__":
    main()
