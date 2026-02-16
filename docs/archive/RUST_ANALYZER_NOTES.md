# Rust-Specific Notes for Escape Sentinel

## Why Rust Has Its Own Analyzer

While the orchestrator is written in Rust, the **Rust analyzer bridge** is needed to analyze **other Rust projects** for concurrency escapes. This is similar to how the Python analyzer can analyze other Python projects.

## What the Rust Analyzer Detects

### Thread-Based Escapes

- `std::thread::spawn()` without `.join()`
- Nested thread spawning
- Threads with infinite loops
- Panicking threads
- Thread builder pattern without cleanup

### Async/Tokio Escapes

- `tokio::spawn()` without `.await`
- Detached blocking tasks (`spawn_blocking`)
- JoinSet without waiting
- LocalSet tasks without await
- Cancellation tokens not cancelled
- Infinite interval loops

## Rust's Compile-Time Safety

Rust prevents many escapes at **compile time** that other languages only catch at runtime:

### Scoped Threads (Safe by Design)

```rust
thread::scope(|s| {
    s.spawn(|| {
        // Work here
    });
    // ✅ Automatically joins when scope ends!
});
```

This is **impossible to get wrong** - the compiler enforces cleanup.

### What Rust Can't Prevent

```rust
// ❌ This compiles but leaks the thread
thread::spawn(|| {
    loop { /* forever */ }
});

// ❌ This compiles but leaks the task
tokio::spawn(async {
    loop { /* forever */ }
});
```

## Detection Challenges

### 1. No Thread Enumeration

Unlike Python (`threading.enumerate()`) or Java (JMX), Rust's standard library doesn't expose:

- List of all threads
- Thread names/IDs
- Thread states

**Solution:** Use platform-specific APIs or track threads manually.

### 2. Tokio Task Opacity

Tokio doesn't provide:

- List of spawned tasks
- Task states
- Task handles for unowned tasks

**Solution:** Would need tokio-console integration or runtime instrumentation.

### 3. Dynamic Loading

To analyze arbitrary Rust functions, we need:

- Dynamic library (cdylib) builds
- Function export via C ABI
- libloading for runtime loading

**Current Implementation:** Demonstrates architecture but uses simplified detection.

## Test Examples

### Escape Examples (`tests/rust/`)

**Threads:**

- `spawn_detached_thread` - Thread without join
- `spawn_multiple_detached_threads` - Multiple leaks
- `spawn_thread_in_loop` - Infinite loop thread
- `spawn_with_builder` - Builder pattern leak

**Async:**

- `spawn_detached_task` - Tokio task without await
- `spawn_infinite_task` - Infinite async loop
- `create_joinset_without_waiting` - Dropped JoinSet
- `spawn_blocking_detached` - Blocking task leak

### Safe Examples

**Threads:**

- `spawn_and_join_thread` - Proper join
- `use_scoped_threads` - Scoped threads (compile-time safe!)
- `use_raii_thread_guard` - RAII pattern (Drop trait)

**Async:**

- `spawn_and_await_task` - Proper await
- `use_joinset_properly` - JoinSet with join_next
- `use_cancellation_properly` - CancellationToken

## Running Examples

```bash
# Build everything
./scripts/build.sh  # or scripts/build.bat on Windows

# Run thread escape examples (observe escaped threads)
cd tests/rust
cargo run --release --example run_escape_threads

# Run async escape examples (observe escaped tasks)
cargo run --release --example run_escape_async

# Analyze with orchestrator
cd ../..
./target/release/escape-sentinel analyze \
  --target tests_rust::escape_threads::spawn_detached_thread \
  --input "test" \
  --language rust
```

## Future Enhancements

### Platform-Specific Thread Enumeration

**Linux:**

```rust
use std::fs;

fn enumerate_threads_linux() -> Vec<ThreadInfo> {
    let entries = fs::read_dir("/proc/self/task")?;
    // Parse thread info from /proc
}
```

**Windows:**

```rust
use winapi::um::tlhelp32::*;

fn enumerate_threads_windows() -> Vec<ThreadInfo> {
    unsafe {
        let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        // Enumerate threads from snapshot
    }
}
```

### Tokio Console Integration

```toml
[dependencies]
console-subscriber = "0.2"
```

```rust
console_subscriber::init();

tokio::spawn(async {
    // Task will be visible to `tokio-console`
});
```

### Thread Registry Pattern

```rust
use lazy_static::lazy_static;
use std::sync::Mutex;

lazy_static! {
    static ref THREAD_REGISTRY: Mutex<HashSet<ThreadId>> = 
        Mutex::new(HashSet::new());
}

fn tracked_spawn<F>(f: F) -> JoinHandle<()>
where F: FnOnce() + Send + 'static {
    let id = /* generate ID */;
    THREAD_REGISTRY.lock().unwrap().insert(id);
    
    thread::spawn(move || {
        f();
        THREAD_REGISTRY.lock().unwrap().remove(&id);
    })
}
```

## Rust Safety Philosophy

Rust's approach to concurrency escapes:

1. **Prevent at compile time** (scoped threads)
2. **Make unsafe patterns explicit** (Arc, Mutex, channels)
3. **Provide safe abstractions** (join handles, RAII)
4. **Runtime detection for remaining cases** (this tool!)

The Rust analyzer focuses on detecting the escapes that **pass the compiler** but are still dangerous at runtime.

## Key Takeaways

✅ Rust prevents many escapes at compile time
✅ Scoped threads are the safest pattern
✅ Always `.await` spawned tasks
✅ Use RAII (Drop) for automatic cleanup
✅ Detection is harder but still valuable for:

- Audit existing code
- Educational purposes
- Finding subtle runtime leaks
- Enforcing team coding standards

❌ Not all escapes can be prevented by the compiler
❌ Runtime detection has platform limitations
❌ Dynamic analysis requires careful setup

## See Also

- [tests/rust/README.md](tests/rust/README.md) - Detailed test documentation
- [Rust Nomicon - Concurrency](https://doc.rust-lang.org/nomicon/concurrency.html)
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial)
- [Scoped Threads RFC](https://rust-lang.github.io/rfcs/3151-scoped-threads.html)
