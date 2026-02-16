// Rust safe concurrency examples - Thread-based (NO ESCAPE)

use std::thread;
use std::time::Duration;

/// Spawns thread and properly joins - SAFE
pub fn spawn_and_join_thread(input: String) -> String {
    let handle = thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        format!("Processed: {}", input)
    });
    
    handle.join().unwrap()
}

/// Spawns multiple threads and joins all - SAFE
pub fn spawn_and_join_multiple(input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|i| {
            let input_clone = input.clone();
            thread::spawn(move || {
                thread::sleep(Duration::from_millis(50));
                format!("Thread {}: {}", i, input_clone)
            })
        })
        .collect();
    
    let results: Vec<_> = handles
        .into_iter()
        .map(|h| h.join().unwrap())
        .collect();
    
    results.join(", ")
}

/// Uses scoped threads (automatically joined) - SAFE
pub fn use_scoped_threads(input: String) -> String {
    let mut result = String::new();
    
    thread::scope(|s| {
        let handles: Vec<_> = (0..3)
            .map(|i| {
                s.spawn(move || {
                    thread::sleep(Duration::from_millis(50));
                    format!("Scoped {}: {}", i, input.clone())
                })
            })
            .collect();
        
        result = handles
            .into_iter()
            .map(|h| h.join().unwrap())
            .collect::<Vec<_>>()
            .join(", ");
    });
    
    result
}

/// Uses thread pool pattern with cleanup - SAFE
pub fn use_thread_pool(input: String) -> String {
    use std::sync::{Arc, Mutex};
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    let input = Arc::new(Mutex::new(input));
    
    let handles: Vec<_> = (0..3)
        .map(|_| {
            let tx = tx.clone();
            let input = Arc::clone(&input);
            thread::spawn(move || {
                let data = input.lock().unwrap();
                tx.send(format!("Processed: {}", data)).unwrap();
            })
        })
        .collect();
    
    // Drop original sender so rx.recv() can complete
    drop(tx);
    
    // Join all threads
    for handle in handles {
        handle.join().unwrap();
    }
    
    // Collect results
    rx.iter().collect::<Vec<_>>().join(", ")
}

/// Uses Arc and channels properly - SAFE
pub fn use_arc_channels(input: String) -> String {
    use std::sync::{Arc, Mutex};
    
    let data = Arc::new(Mutex::new(vec![input]));
    let data_clone = Arc::clone(&data);
    
    let handle = thread::spawn(move || {
        thread::sleep(Duration::from_millis(50));
        let mut d = data_clone.lock().unwrap();
        d.push("modified".to_string());
    });
    
    handle.join().unwrap();
    
    let final_data = data.lock().unwrap();
    final_data.join(", ")
}

/// Uses thread with timeout and proper cleanup - SAFE
pub fn use_thread_with_timeout(input: String) -> String {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    
    let handle = thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        tx.send(format!("Result: {}", input)).ok();
    });
    
    // Wait with timeout
    let result = rx
        .recv_timeout(Duration::from_secs(1))
        .unwrap_or_else(|_| "Timeout".to_string());
    
    // Still join the thread
    handle.join().unwrap();
    
    result
}

/// Uses barrier synchronization properly - SAFE
pub fn use_barrier_sync(input: String) -> String {
    use std::sync::{Arc, Barrier};
    
    let barrier = Arc::new(Barrier::new(3));
    let mut handles = vec![];
    
    for i in 0..3 {
        let barrier_clone = Arc::clone(&barrier);
        let input_clone = input.clone();
        
        let handle = thread::spawn(move || {
            thread::sleep(Duration::from_millis(50 * i));
            barrier_clone.wait();
            format!("Thread {}: {}", i, input_clone)
        });
        
        handles.push(handle);
    }
    
    handles
        .into_iter()
        .map(|h| h.join().unwrap())
        .collect::<Vec<_>>()
        .join(", ")
}

/// Uses RAII pattern for thread cleanup - SAFE
pub fn use_raii_thread_guard(input: String) -> String {
    struct ThreadGuard(Option<thread::JoinHandle<String>>);
    
    impl Drop for ThreadGuard {
        fn drop(&mut self) {
            if let Some(handle) = self.0.take() {
                handle.join().ok();
            }
        }
    }
    
    let handle = thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        format!("Guarded: {}", input)
    });
    
    let guard = ThreadGuard(Some(handle));
    
    // Guard ensures thread is joined even if we panic or return early
    guard.0.unwrap().join().unwrap()
}
