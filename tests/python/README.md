# Python Concurrency Escape Tests

This directory contains Python test programs demonstrating various concurrency escape patterns and safe alternatives.

## Test Files

### Escape Patterns (Unsafe)

**escape_threads.py** - Thread-based escapes:

- `spawn_non_daemon_thread()` - Non-daemon thread without join
- `spawn_daemon_thread()` - Daemon thread (still tracked)
- `spawn_timer_thread()` - Timer thread without cancel

**escape_process.py** - Process escapes:

- `spawn_process()` - Child process without join
- `spawn_multiple_processes()` - Multiple process leaks

**escape_pool.py** - Pool management issues:

- `leak_process_pool()` - Pool created but not closed
- `leak_process_pool_map_async()` - Async map without join

**escape_executor.py** - ThreadPoolExecutor leaks:

- `leak_executor()` - Executor not shut down
- `leak_new_executor()` - New executor per call
- `leak_new_executor_multiple()` - Multiple executors

**escape_global_thread.py** - Global state issues:

- `spawn_global_thread()` - Module-level thread
- `spawn_global_timer_thread()` - Global timer thread
- `spawn_multiple_global_threads()` - Multiple global threads

### Safe Patterns

**no_escape.py** - Proper thread cleanup:

- `join_thread()` - Thread properly joined
- `thread_with_timeout()` - Thread with timeout and join

**no_escape_process.py** - Proper process cleanup:

- `join_process()` - Process properly joined

**no_escape_pool.py** - Proper pool cleanup:

- `close_and_join_pool()` - Pool explicitly closed and joined

## Running Tests

**See [../../UV_COMMANDS.md](../../UV_COMMANDS.md) for comprehensive examples and command options.**

### Quick Examples

Single test:

```bash
uv run graphene tests.python.escape_threads:spawn_non_daemon_thread --input "hello"
```

All Python tests:

```bash
uv run graphene --run-all --python-only --generate 50
```

With multiple inputs:

```bash
uv run graphene tests.python.escape_threads:spawn_non_daemon_thread \
  --input "test1" \
  --input "test2" \
  --input "test3" \
  --repeat 5
```

## Detection Mechanisms

The test harness detects escapes by:

1. **Baseline Capture**: Record all threads/processes before execution
2. **Execute Function**: Run the test function
3. **Grace Period**: Wait 100ms for cleanup
4. **Compare State**: Check for new threads/processes
5. **Classify**: Distinguish daemon vs non-daemon threads

## Creating New Tests

Template for new test functions:

```python
import threading
import time

def my_escape_pattern(input_data):
    """
    Brief description of the escape pattern.
    
    Expected Behavior: ESCAPE
    Reason: Non-daemon thread spawned without join
    """
    def worker():
        time.sleep(10)  # Simulate work
    
    thread = threading.Thread(target=worker)
    thread.start()  # Not joined - ESCAPES!
    return f"processed: {input_data}"

def my_safe_pattern(input_data):
    """
    Safe alternative to the escape pattern above.
    
    Expected Behavior: SAFE
    Reason: Thread properly joined
    """
    def worker():
        time.sleep(0.1)
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()  # Properly cleaned up
    return f"processed: {input_data}"
```

## Common Pitfalls

### Windows vs Linux

On Windows, multiprocessing tests should use `--main-thread-mode`:

```bash
uv run graphene tests.python.escape_process:spawn_process \
  --main-thread-mode \
  --input "test"
```

### Daemon Threads

Daemon threads are still tracked as escapes even though Python will terminate them:

```python
thread = threading.Thread(target=work, daemon=True)
thread.start()  # Still detected as escape
```

### Timer Threads

Timer threads must be explicitly cancelled:

```python
import threading

def leak_timer():
    timer = threading.Timer(10.0, lambda: None)
    timer.start()  # ESCAPES - not cancelled

def safe_timer():
    timer = threading.Timer(10.0, lambda: None)
    timer.start()
    timer.cancel()  # Properly cleaned up
```

## Integration with Rust Orchestrator

These tests can also be run through the Rust orchestrator:

```bash
./target/release/graphene-ha analyze \
  --target tests/python/escape_threads.py:spawn_non_daemon_thread \
  --input "test" \
  --language python
```
