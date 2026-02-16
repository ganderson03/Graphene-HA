// Rust concurrency escape examples - Thread-based

use std::thread;
use std::time::Duration;

/// Spawns a thread that never completes - ESCAPE
pub fn spawn_detached_thread(input: String) -> String {
    thread::spawn(move || {
        thread::sleep(Duration::from_secs(10));
        println!("Thread completed: {}", input);
    });
    "ok".to_string()
}

/// Spawns multiple threads without joining - ESCAPE
pub fn spawn_multiple_detached_threads(input: String) -> String {
    for i in 0..3 {
        let input_clone = input.clone();
        thread::spawn(move || {
            thread::sleep(Duration::from_secs(2));
            println!("Thread {} completed: {}", i, input_clone);
        });
    }
    "ok".to_string()
}

/// Spawns a thread in a loop - ESCAPE
pub fn spawn_thread_in_loop(input: String) -> String {
    let input_clone = input.clone();
    thread::spawn(move || loop {
        thread::sleep(Duration::from_secs(1));
        println!("Loop iteration: {}", input_clone);
    });
    "ok".to_string()
}

/// Spawns a scoped thread but doesn't wait - ESCAPE (doesn't compile without scope.join())
/// This example shows the escape would occur if scope drops early
pub fn spawn_scoped_detached(_input: String) -> String {
    // Note: This won't actually escape because scoped threads
    // automatically join when scope ends. This is Rust's safety!
    thread::scope(|s| {
        s.spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
        // If we could drop scope here, it would be an escape
        // but Rust prevents this at compile time
    });
    "ok".to_string()
}

/// Spawns nested detached thread - ESCAPE
pub fn spawn_nested_detached_thread(input: String) -> String {
    thread::spawn(move || {
        let input_clone = input.clone();
        // Spawn another thread from within
        thread::spawn(move || {
            thread::sleep(Duration::from_secs(2));
            println!("Nested thread: {}", input_clone);
        });
    });
    "ok".to_string()
}

/// Spawns a thread with a panic - ESCAPE + CRASH
pub fn spawn_panicking_thread(input: String) -> String {
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        panic!("Thread panic: {}", input);
    });
    "ok".to_string()
}

/// Spawns threads with shared state but no cleanup - ESCAPE
pub fn spawn_with_shared_state(input: String) -> String {
    use std::sync::{Arc, Mutex};
    
    let data = Arc::new(Mutex::new(vec![input]));
    
    for _ in 0..3 {
        let data_clone = Arc::clone(&data);
        thread::spawn(move || {
            thread::sleep(Duration::from_secs(2));
            let mut d = data_clone.lock().unwrap();
            d.push("modified".to_string());
        });
    }
    
    "ok".to_string()
}

/// Builder pattern thread - ESCAPE
pub fn spawn_with_builder(input: String) -> String {
    thread::Builder::new()
        .name(format!("worker-{}", input))
        .spawn(move || {
            thread::sleep(Duration::from_secs(5));
            println!("Builder thread completed");
        })
        .expect("Failed to spawn thread");
    
    "ok".to_string()
}
