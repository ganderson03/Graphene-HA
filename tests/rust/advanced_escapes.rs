// Rust concurrency escape examples - Advanced patterns

use std::thread;
use std::time::Duration;
use std::sync::{Arc, Mutex};
use tokio::time::sleep;
use tokio::task;

// === Obfuscated Thread Escapes ===

fn create_worker_factory() -> impl Fn() {
    || {
        thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
    }
}

pub fn spawn_via_factory(_input: String) -> String {
    let factory = create_worker_factory();
    factory();
    "ok".to_string()
}

pub fn spawn_via_closure(_input: String) -> String {
    let spawner = || {
        thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
    };
    spawner();
    "ok".to_string()
}

// === Dynamic Storage ===

pub fn spawn_to_vec(_input: String) -> String {
    let mut threads = Vec::new();
    
    for _ in 0..3 {
        let t = thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
        threads.push(t);
    }
    
    // threads dropped without joining
    "ok".to_string()
}

pub fn spawn_to_vec_drop_explicit(_input: String) -> String {
    let mut threads = Vec::new();
    
    for _ in 0..3 {
        let t = thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
        threads.push(t);
    }
    
    // Explicitly drop without join
    drop(threads);
    "ok".to_string()
}

// === Conditional Escapes ===

pub fn spawn_conditionally(_input: String) -> String {
    if _input.len() > 3 {
        thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
    }
    "ok".to_string()
}

pub fn spawn_in_error_path(_input: String) -> String {
    match _input.parse::<i32>() {
        Ok(_) => "ok".to_string(),
        Err(_) => {
            thread::spawn(|| {
                thread::sleep(Duration::from_secs(2));
            });
            "ok".to_string()
        }
    }
}

// === Shared State Escapes ===

pub fn spawn_with_shared_data(_input: String) -> String {
    let data = Arc::new(Mutex::new(vec![_input]));
    
    for _ in 0..3 {
        let data = Arc::clone(&data);
        thread::spawn(move || {
            thread::sleep(Duration::from_millis(100));
            let mut d = data.lock().unwrap();
            d.push("leaked".to_string());
        });
    }
    
    // Arc clones released but threads still running
    "ok".to_string()
}

pub fn spawn_with_string_clone(_input: String) -> String {
    for _ in 0..3 {
        let input = _input.clone();
        thread::spawn(move || {
            thread::sleep(Duration::from_secs(2));
            println!("Thread: {}", input);
        });
    }
    "ok".to_string()
}

// === Partial Joins ===

pub fn spawn_join_only_first(_input: String) -> String {
    let mut threads = vec![];
    
    for _ in 0..3 {
        threads.push(thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        }));
    }
    
    if let Some(t) = threads.first() {
        let _result = t.join();
    }
    
    // Rest dropped without join
    "ok".to_string()
}

pub fn spawn_collect_join_incomplete(_input: String) -> String {
    let handles: Vec<_> = (0..5)
        .map(|i| {
            thread::spawn(move || {
                thread::sleep(Duration::from_secs(2));
                i
            })
        })
        .collect();
    
    // Only join first 2
    for handle in handles.iter().take(2) {
        let _ = handle.join();
    }
    
    "ok".to_string()
}

// === Recursive Threads ===

pub fn spawn_threads_recursive(_input: String, depth: usize) -> String {
    if depth == 0 {
        return "ok".to_string();
    }
    
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        spawn_threads_recursive(_input.clone(), depth - 1);
    });
    
    "ok".to_string()
}

// === Async Task Escapes ===

pub async fn spawn_task_no_await(_input: String) -> String {
    task::spawn(async {
        sleep(Duration::from_secs(10)).await;
    });
    "ok".to_string()
}

pub async fn spawn_multiple_tasks_no_join(_input: String) -> String {
    for _ in 0..5 {
        task::spawn(async {
            sleep(Duration::from_secs(2)).await;
        });
    }
    "ok".to_string()
}

pub async fn spawn_tasks_in_loop_no_collect(_input: String) -> String {
    for i in 0..3 {
        task::spawn(async move {
            sleep(Duration::from_secs(2)).await;
            println!("Task {}", i);
        });
    }
    "ok".to_string()
}

// === Panic/Error Path Escapes ===

pub fn spawn_with_panic_risk(_input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|_| {
            thread::spawn(|| {
                thread::sleep(Duration::from_secs(2));
            })
        })
        .collect();
    
    if _input == "panic" {
        panic!("User triggered panic - threads leak");
    }
    
    // Normal path drops handles without join
    "ok".to_string()
}

// === Builder Pattern Escapes ===

pub fn spawn_with_builder(_input: String) -> String {
    thread::Builder::new()
        .name(format!("worker-{}", _input))
        .spawn(|| {
            thread::sleep(Duration::from_secs(2));
        })
        .expect("Failed to spawn");
    
    "ok".to_string()
}

// === Properly Cleaned Up (False Negatives) ===

pub fn thread_properly_joined(_input: String) -> String {
    let handle = thread::spawn(|| {
        thread::sleep(Duration::from_millis(50));
        42
    });
    
    let _result = handle.join();
    "ok".to_string()
}

pub fn threads_collected_and_joined(_input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|i| {
            thread::spawn(move || {
                thread::sleep(Duration::from_millis(50));
                i
            })
        })
        .collect();
    
    for handle in handles {
        let _ = handle.join();
    }
    "ok".to_string()
}

pub async fn task_properly_awaited(_input: String) -> String {
    let handle = task::spawn(async {
        sleep(Duration::from_millis(50)).await;
        "done"
    });
    
    let _ = handle.await;
    "ok".to_string()
}

pub async fn tasks_properly_collected(_input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|i| {
            task::spawn(async move {
                sleep(Duration::from_millis(50)).await;
                i
            })
        })
        .collect();
    
    for handle in handles {
        let _ = handle.await;
    }
    "ok".to_string()
}

pub fn thread_scope_safe(_input: String) -> String {
    // Rust's scoped threads are safe - they must join before scope ends
    thread::scope(|s| {
        for i in 0..3 {
            s.spawn(move |_| {
                thread::sleep(Duration::from_millis(50));
                println!("Scoped thread {}", i);
            });
        }
        // Scope blocks until all threads join
    });
    "ok".to_string()
}
