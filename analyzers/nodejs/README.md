# Node.js Bridge

Bridge for Node.js object/data escape analysis.

## Files

- analyzer_bridge.js
- static_analyzer.js
- package.json

## Capabilities

- Dynamic execution with async_hooks-backed runtime observations
- Static source analysis for retention and escape patterns

## Example (dynamic bridge request)

```bash
echo '{"session_id":"s1","target":"tests/nodejs/cases/case_001_cache_profile.js:case001CacheProfile","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | node analyzer_bridge.js
```

## Static analyzer usage

```bash
node static_analyzer.js <source_file> <function_name>
```

## Dependencies

- Node.js 14+
