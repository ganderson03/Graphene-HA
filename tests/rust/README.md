# Rust Escape Detection Tests

This directory contains comprehensive Rust concurrency escape examples for testing the escape analyzer.

## Location

This directory was previously named `escape_tests_rust/` and has been moved to `tests/rust/` for better organization alongside tests from other languages.

## Test Categories

### 1. Thread-Based Escapes (`escape_threads.rs`)

Examples of thread leaks using `std::thread`:

- **`spawn_detached_thread`** - Spawns thread without joining
- **`spawn_multiple_detached_threads`** - Multiple threads without cleanup
- **`spawn_thread_in_loop`** - Infinite loop thread
- **`spawn_nested_detached_thread`** - Nested thread spawning
- **`spawn_panicking_thread`** - Thread that panics (escape + crash)
- **`spawn_with_shared_state`** - Threads with Arc/Mutex but no join
- **`spawn_with_builder`** - Thread builder pattern without join

### 2. Async/Tokio Escapes (`escape_async.rs`)

Examples of tokio task leaks:

- **`spawn_detached_task`** - Spawns task without awaiting
- **`spawn_multiple_detached_tasks`** - Multiple detached tasks
- **`spawn_infinite_task`** - Task with infinite loop
- **`spawn_nested_tasks`** - Nested task spawning
- **`spawn_blocking_detached`** - `spawn_blocking` without await
- **`spawn_local_detached`** - LocalSet task without await
- **`create_joinset_without_waiting`** - JoinSet dropped without awaiting tasks
- **`spawn_panicking_task`** - Task that panics
- **`spawn_with_cancellation_token`** - CancellationToken not cancelled
- **`create_detached_interval`** - Interval in infinite loop

### 3. Safe Thread Examples (`no_escape_threads.rs`)

Proper thread cleanup patterns:

- **`spawn_and_join_thread`** - Single thread with join
- **`spawn_and_join_multiple`** - Multiple threads with joins
- **`use_scoped_threads`** - Scoped threads (compile-time safety!)
- **`use_thread_pool`** - Thread pool with proper cleanup
- **`use_arc_channels`** - Arc/Mutex with join
- **`use_thread_with_timeout`** - Timeout + join
- **`use_barrier_sync`** - Barrier synchronization
- **`use_raii_thread_guard`** - RAII pattern (Drop trait)

### 4. Safe Async Examples (`no_escape_async.rs`)

Proper tokio task cleanup:

- **`spawn_and_await_task`** - Single task with await
- **`spawn_and_await_multiple`** - Multiple tasks with join_all
- **`use_joinset_properly`** - JoinSet with join_next loop
- **`use_select_properly`** - tokio::select! macro
- **`use_timeout_properly`** - Timeout wrapper
- **`use_spawn_blocking_properly`** - spawn_blocking with await
- **`use_cancellation_properly`** - CancellationToken with cancel
- **`use_interval_properly`** - Interval with bounded loop
- **`use_channels_properly`** - mpsc channels with await
- **`use_try_join`** - try_join! macro
- **`use_localset_properly`** - LocalSet with run_until

## Building

```bash
# Build the library
cargo build --release

# Build examples
cargo build --release --examples

# Run escape thread examples
cargo run --release --example run_escape_threads

# Run escape async examples
cargo run --release --example run_escape_async
```

## Running Tests with Orchestrator

Once the Rust bridge is built:

```bash
# Analyze thread escape (note: currently shows architecture, not full detection)
./target/release/graphene-ha analyze \
  --target tests_rust::escape_threads::spawn_detached_thread \
  --language rust \
  --input "test"

# Analyze multiple examples
./target/release/graphene-ha run-all \
  --test-dir tests/rust \
  --language rust
```

## Rust-Specific Detection Challenges

For detailed information about Rust-specific detection challenges, future enhancements, and the Rust safety philosophy, see [RUST_ANALYZER_NOTES.md](../../RUST_ANALYZER_NOTES.md).

### Key Challenges

- **No Thread Enumeration**: Rust's std library doesn't expose thread lists
- **Tokio Task Opacity**: No public APIs to list spawned tasks
- **Compile-Time Safety**: Many escapes prevented at compile time (scoped threads)
- **Current Implementation**: Demonstrates architecture with heuristic-based detection

See [RUST_ANALYZER_NOTES.md](../RUST_ANALYZER_NOTES.md) for platform-specific solutions and future improvements.

## Testing Philosophy

These examples demonstrate:

1. **Escapes that compile** - Rust prevents many but not all escapes
2. **Runtime patterns** - What actually leaks at runtime
3. **Safe alternatives** - How to properly handle concurrency
4. **Real-world patterns** - Common mistakes developers make

The goal is to teach developers to:

- Recognize escape patterns
- Use Rust's safety features (scoped threads, RAII)
- Properly await tokio tasks
- Understand when compiler can't help
