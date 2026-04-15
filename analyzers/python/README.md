# Python Bridge

## Files

- analyzer_bridge.py
- static_analyzer.py

## Functionality

- loads Python targets from file or module references
- executes target functions with configured inputs and timeout
- captures dynamic heap signals
- emits protocol-shaped results and vulnerability entries

## Example Invocation

```bash
echo '{"session_id":"s1","target":"tests/python/cases/case_001_cache_profile.py:case_001_cache_profile","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{},"analysis_mode":"dynamic"}' | python analyzer_bridge.py
```
