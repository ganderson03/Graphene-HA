# Python Bridge

This bridge connects the Rust orchestrator to Python code for escape analysis.

## Files

- **analyzer_bridge.py** - Dynamic analyzer that executes Python functions and detects escaping threads/processes
- **static_analyzer.py** - Static AST-based analyzer that detects potential escapes without execution

## Dynamic Analysis

The dynamic analyzer uses the `test_harness.py` and `vulnerability_detector.py` from the `graphene_ha` package to:
- Execute Python functions in isolation
- Track threads, processes, and async tasks created during execution
- Detect which concurrency objects escape (are not joined/closed)

### Usage
```bash
echo '{"session_id":"test","target":"module:function","inputs":["data"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | python3 analyzer_bridge.py
```

## Static Analysis

The static analyzer uses Python's AST module to:
- Parse Python source code
- Identify thread/process/pool creation
- Track `.join()` and `.close()` calls
- Report concurrency objects that may leak

### Usage
```bash
python3 static_analyzer.py <source_file> <function_name>
```

## Dependencies

- Python 3.7+
- No external dependencies (uses standard library)
