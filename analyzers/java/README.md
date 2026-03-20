# Java Bridge

Bridge for Java object/data escape analysis.

## Files

- src/main/java/com/escape/analyzer/AnalyzerBridge.java
- pom.xml

## Build

```bash
cd analyzers/java
mvn clean package
```

## Example

```bash
echo '{"session_id":"s1","target":"com.escape.tests.cases.Case001CacheProfile:execute","inputs":["sample"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | java -jar target/escape-analyzer.jar
```
