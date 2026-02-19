# Node.js Bridge

This bridge connects the Rust orchestrator to Node.js/JavaScript code for escape analysis.

## Files

- **analyzer_bridge.js** - Dynamic analyzer that executes JavaScript functions and detects escaping async resources
- **static_analyzer.js** - Static analyzer that detects timer leaks and async patterns
- **package.json** - Node.js package configuration

## Dynamic Analysis

The dynamic analyzer uses Node.js `async_hooks` to:
- Track async resources created during function execution
- Detect timers, promises, and other async operations that escape
- Measure execution times and detect crashes

### Usage
```bash
echo '{"session_id":"test","target":"module:function","inputs":["data"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | node analyzer_bridge.js
```

## Static Analysis

The static analyzer performs text-based pattern matching to:
- Detect `setTimeout` without `clearTimeout`
- Detect `setInterval` without `clearInterval`
- Identify `process.nextTick` and `setImmediate` patterns
- Track timer handles

### Usage
```bash
node static_analyzer.js <source_file> <function_name>
```

## Dependencies

- Node.js 14+
- No external dependencies (uses built-in modules)
