# Java Bridge

This bridge connects the Rust orchestrator to Java code for escape analysis.

## Files

- **src/main/java/com/escape/analyzer/AnalyzerBridge.java** - Dynamic analyzer that executes Java methods and detects escaping threads
- **pom.xml** - Maven project configuration

## Structure

```
java-bridge/
├── pom.xml
└── src/
    └── main/
        └── java/
            └── com/
                └── escape/
                    └── analyzer/
                        └── AnalyzerBridge.java
```

## Dynamic Analysis

The dynamic analyzer uses Java's ThreadMXBean to:
- Track threads before and after method execution
- Detect non-daemon threads that escape
- Identify thread states (RUNNABLE, WAITING, etc.)
- Measure execution times and detect exceptions

### Usage
```bash
# Build the JAR first
mvn clean package

# Run analysis
echo '{"session_id":"test","target":"class:method","inputs":["data"],"repeat":1,"timeout_seconds":5.0,"options":{}}' | java -jar target/escape-analyzer.jar
```

## Static Analysis

Java static analysis is performed by the Rust code using text-based pattern matching to:
- Detect `new Thread()` creation
- Track `.start()` and `.join()` calls
- Identify ExecutorService creation and shutdown
- Report threads/executors that are not properly cleaned up

## Dependencies

- Java 11+
- Maven 3.6+
- Gson (for JSON serialization) - specified in pom.xml

## Building

```bash
cd analyzers/java-bridge
mvn clean package
```

This creates `target/escape-analyzer.jar` which can be executed by the Rust orchestrator.
