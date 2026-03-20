# Python Bridge

Bridge for Python object/data escape analysis.

## Files

- analyzer_bridge.py
- static_analyzer.py

## What it does

- Parses requests from orchestrator
- Runs target functions when required
- Produces protocol-shaped escape findings

## Example

```bash
echo '{"session_id":"s1","target":"tests/python/cases/case_001_cache_profile.py:case_001_cache_profile","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | python analyzer_bridge.py
```
