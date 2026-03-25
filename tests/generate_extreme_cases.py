#!/usr/bin/env python3
"""Generate case_201..case_300 stress suites across all languages.

These cases push harder on false-positive/false-negative boundaries with:
- multi-hop aliasing and helper indirection
- closure retention with delayed execution
- mixed branch predicates and dead-sink decoys
- serialization/copy confusion patterns
- interface/container handoff patterns
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
    ("alias_hop_chain", True),
    ("helper_sink_dispatch", True),
    ("closure_registry_delay", True),
    ("container_handoff_global", True),
    ("interface_sink_bridge", True),
    ("thread_pool_capture", True),
    ("dead_sink_decoy", False),
    ("copy_then_drop", False),
    ("local_clone_named_retained", False),
    ("serialization_roundtrip_safe", False),
    ("shadowed_sink_local", False),
    ("ephemeral_lambda_use", False),
]


def to_pascal(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def make_ident(idx: int) -> tuple[str, bool]:
    variant, is_escape = VARIANTS[(idx - 201) % len(VARIANTS)]
    batch = ((idx - 201) // len(VARIANTS)) + 1
    slug = f"{variant}_{batch:02d}"
    return slug, is_escape


def py_content(idx: int, slug: str) -> str:
    fn_name = f"case_{idx:03d}_{slug}"
    if slug.startswith("alias_hop_chain"):
        body = """    first = payload\n    second = first\n    third = second\n    # ESCAPE: multi-hop alias chain ends in retained sink.\n    RETAINED_CACHE['hop'] = third\n    return 'ok'\n"""
    elif slug.startswith("helper_sink_dispatch"):
        body = """    def sink(obj):\n        RETAINED_AUDIT.append(obj)\n    # ESCAPE: helper function dispatch hides sink call site.\n    sink(payload)\n    return 'ok'\n"""
    elif slug.startswith("closure_registry_delay"):
        body = """    def later() -> str:\n        RETAINED_AUDIT.append(payload)\n        return payload['input']\n    # ESCAPE: retained closure mutates global sink when invoked later.\n    RETAINED_HANDLERS.append(later)\n    return 'ok'\n"""
    elif slug.startswith("container_handoff_global"):
        body = """    envelope = {'x': {'inner': payload}}\n    # ESCAPE: nested container handoff to global cache.\n    RETAINED_CACHE['nested'] = envelope['x']['inner']\n    return 'ok'\n"""
    elif slug.startswith("interface_sink_bridge"):
        body = """    class Sink:\n        def put(self, obj):\n            RETAINED_AUDIT.append(obj)\n    # ESCAPE: interface-like method bridge stores payload globally.\n    Sink().put(payload)\n    return 'ok'\n"""
    elif slug.startswith("thread_pool_capture"):
        body = """    import threading\n    # ESCAPE: thread captures payload and retains after return edge.\n    threading.Thread(target=lambda: RETAINED_AUDIT.append(payload), daemon=True).start()\n    return 'ok'\n"""
    elif slug.startswith("dead_sink_decoy"):
        body = """    if 2 + 2 == 5:\n        RETAINED_AUDIT.append(payload)\n    # SAFE: sink exists but dead arithmetic branch blocks execution.\n    return payload['checksum']\n"""
    elif slug.startswith("copy_then_drop"):
        body = """    clone = dict(payload)\n    _ = clone['task']\n    # SAFE: clone stays local and is dropped at return.\n    return payload['checksum']\n"""
    elif slug.startswith("local_clone_named_retained"):
        body = """    retained_local = [dict(payload)]\n    _ = retained_local[0]['task']\n    # SAFE: misleading local name but no global retention.\n    return payload['checksum']\n"""
    elif slug.startswith("serialization_roundtrip_safe"):
        body = """    import json\n    roundtrip = json.loads(json.dumps(payload))\n    _ = roundtrip['task']\n    # SAFE: roundtrip data is local and not retained globally.\n    return payload['checksum']\n"""
    elif slug.startswith("shadowed_sink_local"):
        body = """    RETAINED_CACHE = {}\n    RETAINED_CACHE['tmp'] = payload\n    # SAFE: shadowed local variable hides global sink symbol.\n    return payload['checksum']\n"""
    else:
        body = """    handler = lambda: payload['task']\n    _ = handler()\n    # SAFE: lambda consumed inline and never persisted.\n    return payload['checksum']\n"""

    return f'''"""\nTask case {idx:03d}: {slug} deep stress pattern.\n"""\n\nRETAINED_CACHE = {{}}\nRETAINED_AUDIT = []\nRETAINED_HANDLERS = []\n\ndef {fn_name}(input_data):\n    task_name = '{slug}'\n    raw = input_data or 'sample'\n    payload = {{\n        'task': task_name,\n        'entity': 'extreme',\n        'stage': 'stress',\n        'input': raw,\n        'checksum': f'{{task_name}}:{{len(raw)}}',\n    }}\n{body}'''


def js_content(idx: int, slug: str) -> str:
    fn_name = f"case{idx:03d}{to_pascal(slug)}"
    if slug.startswith("alias_hop_chain"):
        body = """  const a = payload;\n  const b = a;\n  const c = b;\n  // ESCAPE: multi-hop alias chain into retained sink.\n  retainedAudit.push(c);\n  return 'ok';\n"""
    elif slug.startswith("helper_sink_dispatch"):
        body = """  const sink = (obj) => retainedCache.set('helper', obj);\n  // ESCAPE: helper function obscures sink dispatch.\n  sink(payload);\n  return 'ok';\n"""
    elif slug.startswith("closure_registry_delay"):
        body = """  const later = () => { retainedAudit.push(payload); return payload.input; };\n  // ESCAPE: retained closure executes after caller returns.\n  retainedHandlers.push(later);\n  return 'ok';\n"""
    elif slug.startswith("container_handoff_global"):
        body = """  const box = { deep: { value: payload } };\n  // ESCAPE: nested indirection retained globally.\n  retainedCache.set('nested', box.deep.value);\n  return 'ok';\n"""
    elif slug.startswith("interface_sink_bridge"):
        body = """  const sink = { put(obj) { retainedAudit.push(obj); } };\n  // ESCAPE: object method bridge to retained sink.\n  sink.put(payload);\n  return 'ok';\n"""
    elif slug.startswith("thread_pool_capture"):
        body = """  // ESCAPE: async task captures payload.\n  setTimeout(() => retainedAudit.push(payload), 0);\n  return 'ok';\n"""
    elif slug.startswith("dead_sink_decoy"):
        body = """  if (1 === 2) { retainedAudit.push(payload); }\n  // SAFE: dead branch only.\n  return payload.checksum;\n"""
    elif slug.startswith("copy_then_drop"):
        body = """  const copy = { ...payload };\n  void copy.task;\n  // SAFE: local copy never retained globally.\n  return payload.checksum;\n"""
    elif slug.startswith("local_clone_named_retained"):
        body = """  const retainedLocal = [payload];\n  void retainedLocal.length;\n  // SAFE: local retained* name only.\n  return payload.checksum;\n"""
    elif slug.startswith("serialization_roundtrip_safe"):
        body = """  const roundtrip = JSON.parse(JSON.stringify(payload));\n  void roundtrip.task;\n  // SAFE: roundtrip object remains local.\n  return payload.checksum;\n"""
    elif slug.startswith("shadowed_sink_local"):
        body = """  const retainedCache = new Map();\n  retainedCache.set('tmp', payload);\n  // SAFE: local shadow hides global sink symbol.\n  return payload.checksum;\n"""
    else:
        body = """  const f = () => payload.task;\n  void f();\n  // SAFE: lambda used immediately and discarded.\n  return payload.checksum;\n"""

    return f'''/**\n * Task case {idx:03d}: {slug} deep stress pattern.\n */\n\nconst retainedCache = new Map();\nconst retainedAudit = [];\nconst retainedHandlers = [];\n\nfunction {fn_name}(input) {{\n  const taskName = '{slug}';\n  const raw = input || 'sample';\n  const payload = {{\n    task: taskName,\n    entity: 'extreme',\n    stage: 'stress',\n    input: raw,\n    checksum: `${{taskName}}:${{raw.length}}`,\n  }};\n{body}}}\n\nmodule.exports = {{ {fn_name} }};\n'''


def go_content(idx: int, slug: str) -> str:
    fn_name = f"Case{idx:03d}{to_pascal(slug)}"
    extra = ""
    if slug.startswith("alias_hop_chain"):
        body = f"""\ta := payload\n\tb := a\n\tc := b\n\t// ESCAPE: multi-hop alias chain retained globally.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, c)\n\treturn \"ok\"\n"""
    elif slug.startswith("helper_sink_dispatch"):
        body = f"""\tsink := func(obj map[string]string) {{ retainedCase{idx:03d} = append(retainedCase{idx:03d}, obj) }}\n\t// ESCAPE: helper sink function hides retention edge.\n\tsink(payload)\n\treturn \"ok\"\n"""
    elif slug.startswith("closure_registry_delay"):
        body = f"""\thandler := func() string {{ retainedCase{idx:03d} = append(retainedCase{idx:03d}, payload); return payload[\"input\"] }}\n\t_ = handler\n\t// ESCAPE: retained closure-like dispatch.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, map[string]string{{\"h\": payload[\"task\"]}})\n\treturn \"ok\"\n"""
    elif slug.startswith("container_handoff_global"):
        body = f"""\tbox := map[string]map[string]string{{\"v\": payload}}\n\t// ESCAPE: nested container handoff retained globally.\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, box[\"v\"])\n\treturn \"ok\"\n"""
    elif slug.startswith("interface_sink_bridge"):
        extra = f"""type case{idx:03d}Sinker interface{{ Put(map[string]string) }}\ntype case{idx:03d}Bridge struct{{}}\n\nfunc (case{idx:03d}Bridge) Put(v map[string]string) {{\n\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, v)\n}}\n\n"""
        body = f"""\tvar s case{idx:03d}Sinker = case{idx:03d}Bridge{{}}\n\t// ESCAPE: interface bridge dispatch to sink.\n\ts.Put(payload)\n\treturn \"ok\"\n"""
    elif slug.startswith("thread_pool_capture"):
        body = f"""\t// ESCAPE: goroutine captures payload and retains it.\n\tgo func(v map[string]string) {{ retainedCase{idx:03d} = append(retainedCase{idx:03d}, v) }}(payload)\n\treturn \"ok\"\n"""
    elif slug.startswith("dead_sink_decoy"):
        body = f"""\tif 1 == 0 {{\n\t\tretainedCase{idx:03d} = append(retainedCase{idx:03d}, payload)\n\t}}\n\t// SAFE: dead branch never executes sink.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("copy_then_drop"):
        body = """\tcopyObj := map[string]string{}\n\tfor k, v := range payload { copyObj[k] = v }\n\t_ = copyObj[\"task\"]\n\t// SAFE: local copy is not retained globally.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("local_clone_named_retained"):
        body = """\tretainedLocal := []map[string]string{payload}\n\t_ = retainedLocal\n\t// SAFE: misleading local name only.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("serialization_roundtrip_safe"):
        body = """\tflat := payload[\"task\"] + ":" + payload[\"input\"]\n\t_ = flat\n\t// SAFE: serialized primitive only.\n\treturn payload[\"checksum\"]\n"""
    elif slug.startswith("shadowed_sink_local"):
        body = """\tretainedCase := []map[string]string{}\n\tretainedCase = append(retainedCase, payload)\n\t// SAFE: local shadow variable only.\n\treturn payload[\"checksum\"]\n"""
    else:
        body = """\tf := func() string { return payload[\"task\"] }\n\t_ = f()\n\t// SAFE: immediate lambda usage only.\n\treturn payload[\"checksum\"]\n"""

    return f'''package escape_tests\n\nvar retainedCase{idx:03d} = []map[string]string{{}}\n\n{extra}func {fn_name}(input string) string {{\n\traw := input\n\tif raw == \"\" {{\n\t\traw = \"sample\"\n\t}}\n\tpayload := map[string]string{{\n\t\t\"task\": \"{slug}\",\n\t\t\"entity\": \"extreme\",\n\t\t\"stage\": \"stress\",\n\t\t\"input\": raw,\n\t\t\"checksum\": \"{slug}:\" + raw,\n\t}}\n{body}}}\n'''


def rust_content(idx: int, slug: str) -> str:
    fn_name = f"case_{idx:03d}_{slug}"
    if slug.startswith("alias_hop_chain"):
        body = """    let a = payload;
    let b = a;
    let c = b;
    // ESCAPE: multi-hop alias chain retained globally.
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(c);
    "ok".to_string()
"""
    elif slug.startswith("helper_sink_dispatch"):
        body = """    fn sink(v: HashMap<String, String>) {
        RETAINED_AUDIT
            .get_or_init(|| Mutex::new(Vec::new()))
            .lock()
            .expect("audit lock")
            .push(v);
    }
    // ESCAPE: helper sink function receives payload.
    sink(payload);
    "ok".to_string()
"""
    elif slug.startswith("closure_registry_delay"):
        body = """    let handler_sig = payload.get("input").cloned().unwrap_or_default();
    // ESCAPE: closure metadata retained for delayed execution.
    RETAINED_HANDLERS.get_or_init(|| Mutex::new(Vec::new())).lock().expect("handlers lock").push(handler_sig);
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(payload);
    "ok".to_string()
"""
    elif slug.startswith("container_handoff_global"):
        body = """    let mut outer: HashMap<String, HashMap<String, String>> = HashMap::new();
    outer.insert("v".to_string(), payload);
    // ESCAPE: nested container handoff retained globally.
    let v = outer.remove("v").expect("v");
    RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(v);
    "ok".to_string()
"""
    elif slug.startswith("interface_sink_bridge"):
        body = """    trait Sink { fn put(&self, v: HashMap<String, String>); }
    struct Bridge;
    impl Sink for Bridge {
        fn put(&self, v: HashMap<String, String>) {
            RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(v);
        }
    }
    // ESCAPE: trait bridge dispatch retains payload.
    Bridge.put(payload);
    "ok".to_string()
"""
    elif slug.startswith("thread_pool_capture"):
        body = """    // ESCAPE: background thread captures payload.
    let p = payload.clone();
    std::thread::spawn(move || {
        RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(p);
    });
    "ok".to_string()
"""
    elif slug.startswith("dead_sink_decoy"):
        body = """    if 1 == 2 {
        RETAINED_AUDIT.get_or_init(|| Mutex::new(Vec::new())).lock().expect("audit lock").push(payload.clone());
    }
    // SAFE: dead branch cannot execute sink.
    payload.get("checksum").cloned().unwrap_or_default()
"""
    elif slug.startswith("copy_then_drop"):
        body = """    let copy_obj = payload.clone();
    let _ = copy_obj.get("task").cloned().unwrap_or_default();
    // SAFE: local copy is dropped and never retained.
    payload.get("checksum").cloned().unwrap_or_default()
"""
    elif slug.startswith("local_clone_named_retained"):
        body = """    let retained_local = vec![payload.clone()];
    let _ = retained_local.len();
    // SAFE: misleading local variable naming only.
    payload.get("checksum").cloned().unwrap_or_default()
"""
    elif slug.startswith("serialization_roundtrip_safe"):
        body = """    let flat = format!(
        "{}:{}",
        payload.get("task").cloned().unwrap_or_default(),
        payload.get("input").cloned().unwrap_or_default()
    );
    let _ = flat;
    // SAFE: primitive serialization only.
    payload.get("checksum").cloned().unwrap_or_default()
"""
    elif slug.startswith("shadowed_sink_local"):
        body = """    let mut retained_audit: Vec<HashMap<String, String>> = Vec::new();
    retained_audit.push(payload.clone());
    // SAFE: local shadow does not touch global sink.
    payload.get("checksum").cloned().unwrap_or_default()
"""
    else:
        body = """    let f = || payload.get("task").cloned().unwrap_or_default();
    let _ = f();
    // SAFE: closure is consumed locally.
    payload.get("checksum").cloned().unwrap_or_default()
"""

    return f'''#![allow(unused)]

use std::collections::HashMap;
use std::sync::{{Mutex, OnceLock}};

#[allow(dead_code)]
static RETAINED_AUDIT: OnceLock<Mutex<Vec<HashMap<String, String>>>> = OnceLock::new();
#[allow(dead_code)]
static RETAINED_HANDLERS: OnceLock<Mutex<Vec<String>>> = OnceLock::new();

pub fn {fn_name}(input: String) -> String {{
    let task_name = "{slug}".to_string();
    let raw = if input.is_empty() {{ "sample".to_string() }} else {{ input }};
    let mut payload: HashMap<String, String> = HashMap::new();
    payload.insert("task".to_string(), task_name.clone());
    payload.insert("entity".to_string(), "extreme".to_string());
    payload.insert("stage".to_string(), "stress".to_string());
    payload.insert("input".to_string(), raw.clone());
    payload.insert("checksum".to_string(), format!("{{}}:{{}}", task_name, raw.len()));
{body}}}
'''


def java_content(idx: int, slug: str) -> str:
    class_name = f"Case{idx:03d}{to_pascal(slug)}"
    if slug.startswith("alias_hop_chain"):
        body = """        Map<String, String> a = payload;
        Map<String, String> b = a;
        Map<String, String> c = b;
        // ESCAPE: multi-hop alias retained globally.
        RETAINED_AUDIT.add(c);
        return "ok";
"""
    elif slug.startswith("helper_sink_dispatch"):
        body = """        // ESCAPE: helper method dispatch to retained sink.
        sink(payload);
        return "ok";
"""
    elif slug.startswith("closure_registry_delay"):
        body = """        Supplier<String> later = () -> { RETAINED_AUDIT.add(payload); return payload.get("input"); };
        // ESCAPE: retained closure executes after method return.
        RETAINED_HANDLERS.add(later);
        return "ok";
"""
    elif slug.startswith("container_handoff_global"):
        body = """        Map<String, Object> outer = new HashMap<>();
        outer.put("v", payload);
        // ESCAPE: nested container handoff to retained sink.
        RETAINED_AUDIT.add((Map<String, String>) outer.get("v"));
        return "ok";
"""
    elif slug.startswith("interface_sink_bridge"):
        body = """        Sink bridge = obj -> RETAINED_AUDIT.add(obj);
        // ESCAPE: interface bridge retains payload.
        bridge.put(payload);
        return "ok";
"""
    elif slug.startswith("thread_pool_capture"):
        body = """        // ESCAPE: background thread captures payload.
        new Thread(() -> RETAINED_AUDIT.add(payload)).start();
        return "ok";
"""
    elif slug.startswith("dead_sink_decoy"):
        body = """        if (1 == 2) {
            RETAINED_AUDIT.add(payload);
        }
        // SAFE: dead branch only.
        return payload.get("checksum");
"""
    elif slug.startswith("copy_then_drop"):
        body = """        Map<String, String> copy = new HashMap<>(payload);
        copy.get("task");
        // SAFE: local copy not retained globally.
        return payload.get("checksum");
"""
    elif slug.startswith("local_clone_named_retained"):
        body = """        List<Map<String, String>> retainedLocal = new ArrayList<>();
        retainedLocal.add(payload);
        // SAFE: misleading local name only.
        return payload.get("checksum");
"""
    elif slug.startswith("serialization_roundtrip_safe"):
        body = """        String serialized = payload.toString();
        serialized.length();
        // SAFE: primitive serialization only.
        return payload.get("checksum");
"""
    elif slug.startswith("shadowed_sink_local"):
        body = """        List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
        RETAINED_AUDIT.add(payload);
        // SAFE: local shadow does not escape.
        return payload.get("checksum");
"""
    else:
        body = """        Supplier<String> f = () -> payload.get("task");
        f.get();
        // SAFE: closure consumed locally only.
        return payload.get("checksum");
"""

    return f'''package com.escape.tests.cases;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Task case {idx:03d}: {slug} deep stress pattern. */
public class {class_name} {{
    private static final List<Map<String, String>> RETAINED_AUDIT = new ArrayList<>();
    private static final List<Supplier<String>> RETAINED_HANDLERS = new ArrayList<>();

    private interface Sink {{
        void put(Map<String, String> obj);
    }}

    private static void sink(Map<String, String> obj) {{
        RETAINED_AUDIT.add(obj);
    }}

    public static String execute(String input) {{
        String taskName = "{slug}";
        String raw = (input == null || input.isEmpty()) ? "sample" : input;
        Map<String, String> payload = new HashMap<>();
        payload.put("task", taskName);
        payload.put("entity", "extreme");
        payload.put("stage", "stress");
        payload.put("input", raw);
        payload.put("checksum", taskName + ":" + raw.length());
{body}    }}
}}
'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def regenerate_rust_lib() -> None:
    files = sorted(RUST_CASES.glob("case_*.rs"))
    lines = ["#![allow(non_snake_case)]", "", "// Re-export split-case test modules"]
    for f in files:
        lines.append(f'#[path = "cases/{f.name}"]')
        lines.append(f"pub mod {f.stem};")
    lines.append("")
    RUST_LIB.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for idx in range(201, 301):
        slug, _ = make_ident(idx)
        write(PY_CASES / f"case_{idx:03d}_{slug}.py", py_content(idx, slug))
        write(JS_CASES / f"case_{idx:03d}_{slug}.js", js_content(idx, slug))
        write(GO_CASES / f"case_{idx:03d}_{slug}.go", go_content(idx, slug))
        write(RUST_CASES / f"case_{idx:03d}_{slug}.rs", rust_content(idx, slug))
        java_class = f"Case{idx:03d}{to_pascal(slug)}"
        write(JAVA_CASES / f"{java_class}.java", java_content(idx, slug))

    regenerate_rust_lib()
    print("Generated cases 201..300 for python, javascript, go, rust, and java.")


if __name__ == "__main__":
    main()
