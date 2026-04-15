# Java Bridge

## Files

- src/main/java/com/escape/analyzer/AnalyzerBridge.java
- pom.xml

## Functionality

- resolves class and method targets
- executes method probes with timeout handling
- captures heap-retention signals via JVM APIs
- performs Java static escape checks
- emits protocol-shaped results

## Build

```bash
cd analyzers/java
mvn clean package
```

## Example Invocation

```bash
echo '{"session_id":"s1","target":"com.escape.tests.cases.Case001CacheProfile:execute","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{},"analysis_mode":"dynamic"}' | java -jar target/escape-analyzer.jar
```
