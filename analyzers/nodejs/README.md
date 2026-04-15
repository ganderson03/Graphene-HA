# Node.js Bridge

## Files

- analyzer_bridge.js
- static_analyzer.js
- package.json

## Functionality

- resolves module/function targets
- executes dynamic probes with timeout control
- collects heap and async-resource escape signals
- performs optional static pattern analysis
- emits protocol-shaped results

## Example Invocation

```bash
echo '{"session_id":"s1","target":"tests/nodejs/cases/case_001_cache_profile.js:case001CacheProfile","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{},"analysis_mode":"dynamic"}' | node analyzer_bridge.js
```
