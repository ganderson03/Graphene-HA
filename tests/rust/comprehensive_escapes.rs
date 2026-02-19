use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

// ============================================================================
// DROP IMPLEMENTATION ESCAPES
// ============================================================================

struct SpawnerOnDrop {
    should_spawn: bool,
}

impl Drop for SpawnerOnDrop {
    fn drop(&mut self) {
        if self.should_spawn {
            thread::spawn(|| {
                thread::sleep(Duration::from_secs(2));
            });
        }
    }
}

pub fn escape_via_drop_impl(_input: String) -> String {
    let _spawner = SpawnerOnDrop { should_spawn: true };
    // Drop runs when _spawner goes out of scope, spawning thread
    "ok".to_string()
}

// ============================================================================
// PANIC HOOK ESCAPES
// ============================================================================

pub fn escape_via_panic_hook(_input: String) -> String {
    let old_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |panic_info| {
        old_hook(panic_info);
        thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
    }));
    "ok".to_string()
}

// ============================================================================
// UNSAFE THREAD SPAWNING
// ============================================================================

pub fn escape_via_unsafe_spawn(_input: String) -> String {
    let value = 42;
    let ptr = &value as *const i32;
    
    unsafe {
        let handle = thread::spawn(move || {
            // Unsafe dereference - thread escapes with invalid pointer
            let _v = *ptr;
            thread::sleep(Duration::from_secs(2));
        });
        // Don't join - thread escapes
    }
    
    "ok".to_string()
}

// ============================================================================
// ARC & MUTEX ESCAPES
// ============================================================================

pub fn escape_via_arc_cycle(_input: String) -> String {
    let counter = Arc::new(Mutex::new(0));
    let counter_clone = Arc::clone(&counter);
    
    thread::spawn(move || {
        let mut num = counter_clone.lock().unwrap();
        *num += 1;
        // Thread never finishes work
        thread::sleep(Duration::from_secs(2));
    });
    // Thread escapes - counter never released
    
    "ok".to_string()
}

pub fn escape_via_poisoned_mutex(_input: String) -> String {
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    
    let handle = thread::spawn(move || {
        let mut vec = data_clone.lock().unwrap();
        vec[10] = 99;  // Will panic - out of bounds
    });
    
    // Thread panics and poisons mutex
    // Handle not joined - thread escapes
    "ok".to_string()
}

// ============================================================================
// JOINHANDLE MISUSE
// ============================================================================

pub fn escape_ignore_joinhandle(_input: String) -> String {
    let _handle = thread::spawn(|| {
        thread::sleep(Duration::from_secs(2));
    });
    
    // Handle dropped without calling join()
    // Thread escapes
    "ok".to_string()
}

pub fn escape_drop_joinhandle_explicitly(_input: String) -> String {
    let handle = thread::spawn(|| {
        thread::sleep(Duration::from_secs(2));
    });
    
    drop(handle);  // Explicitly drop without joining
    "ok".to_string()
}

pub fn escape_joinhandle_in_vec(_input: String) -> String {
    let mut handles = vec![];
    
    for i in 0..5 {
        let handle = thread::spawn(move || {
            thread::sleep(Duration::from_secs(2));
        });
        handles.push(handle);
    }
    
    // Only join first thread
    if !handles.is_empty() {
        let _ = handles[0].join();
    }
    
    // Others escape
    "ok".to_string()
}

pub fn escape_partial_handle_collection(_input: String) -> String {
    let handles: Vec<_> = (0..5)
        .map(|_| {
            thread::spawn(|| {
                thread::sleep(Duration::from_secs(2));
            })
        })
        .collect();
    
    // Collect handles but iterate only halfway
    for (i, handle) in handles.into_iter().enumerate() {
        if i >= 2 {
            drop(handle);  // Drop remaining handles
        } else {
            let _ = handle.join();  // Only join first 2
        }
    }
    
    "ok".to_string()
}

// ============================================================================
// SCOPE ESCAPE PATTERNS
// ============================================================================

pub fn escape_builder_incomplete(_input: String) -> String {
    let builder = thread::Builder::new()
        .name("worker".to_string())
        .stack_size(2 * 1024 * 1024);
    
    let handle = builder.spawn(|| {
        thread::sleep(Duration::from_secs(2));
    }).unwrap();
    
    // Handle not joined
    "ok".to_string()
}

pub fn escape_builder_chain(_input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|i| {
            thread::Builder::new()
                .name(format!("worker-{}", i))
                .spawn(|| {
                    thread::sleep(Duration::from_secs(2));
                })
                .unwrap()
        })
        .collect();
    
    // Handles created but some not joined
    // This creates a mix of escaped threads
    "ok".to_string()
}

// ============================================================================
// CLOSURE & LIFETIME ESCAPES
// ============================================================================

pub fn escape_via_move_partial(_input: String) -> String {
    let owned = String::from("data");
    let shared = Arc::new(owned);
    let shared_clone = Arc::clone(&shared);
    
    let handle = thread::spawn(move || {
        let _data = &*shared_clone;
        thread::sleep(Duration::from_secs(2));
    });
    
    // Not joined, thread escapes with shared reference
    "ok".to_string()
}

pub fn escape_via_static_lifetime(_input: String) -> String {
    let data = "static lifetime";
    
    let handle = thread::spawn(move || {
        let _ref: &'static str = data;  // This is actually safe with static str
        thread::sleep(Duration::from_secs(2));
    });
    
    // Still not joined - thread escapes
    "ok".to_string()
}

// ============================================================================
// CHANNEL ESCAPES
// ============================================================================

pub fn escape_via_channel_send(_input: String) -> String {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(500));
        let _ = tx.send(42);  // Send after function returns
    });
    
    // Thread escapes, sent value might not be processed
    "ok".to_string()
}

pub fn escape_via_channel_recv_hang(_input: String) -> String {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        // Wait for message that never comes
        let _ = rx.recv();  // Hangs forever
    });
    
    // Receiver thread escapes
    "ok".to_string()
}

pub fn escape_via_bounded_channel(_input: String) -> String {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        for i in 0..100 {
            // Eventually blocks on full channel
            let _ = tx.send(i);
        }
    });
    
    // Thread might be blocked indefinitely
    "ok".to_string()
}

// ============================================================================
// PANIC IN SPAWNED THREAD
// ============================================================================

pub fn escape_thread_with_panic(_input: String) -> String {
    let handle = thread::spawn(|| {
        panic!("panic in thread");
    });
    
    // Thread panics but handle not checked
    // Panic is silent if not checked
    "ok".to_string()
}

pub fn escape_conditional_panic(_input: String) -> String {
    let handle = thread::spawn(|| {
        if thread::current().id().as_u64().get() > 0 {
            panic!("conditional panic");
        }
        thread::sleep(Duration::from_secs(2));
    });
    
    // Don't check result or join
    "ok".to_string()
}

// ============================================================================
// COMPLEX SHARED STATE ESCAPES
// ============================================================================

pub fn escape_via_refcell_cell(_input: String) -> String {
    use std::cell::RefCell;
    
    let data = Arc::new(RefCell::new(vec![1, 2, 3]));
    let clone = Arc::clone(&data);
    
    thread::spawn(move || {
        // RefCell is not Send, but we're moving it
        // This would normally be a compile error, so skip for safety
        thread::sleep(Duration::from_secs(2));
    });
    
    "ok".to_string()
}

pub fn escape_via_weak_ref(_input: String) -> String {
    use std::sync::Weak;
    
    let data = Arc::new(vec![1, 2, 3]);
    let weak = Arc::downgrade(&data);
    
    thread::spawn(move || {
        if let Some(strong) = weak.upgrade() {
            thread::sleep(Duration::from_secs(2));
            drop(strong);
        }
    });
    
    // Weak reference thread escapes
    "ok".to_string()
}

// ============================================================================
// RECURSIVE THREAD ESCAPES
// ============================================================================

pub fn escape_recursive_threads(_input: String, depth: usize) -> String {
    if depth > 0 {
        thread::spawn(move || {
            let _ = escape_recursive_threads(String::new(), depth - 1);
        });
        // Spawned thread escapes
    } else {
        thread::spawn(|| {
            thread::sleep(Duration::from_secs(2));
        });
        // Base case spawns thread that escapes
    }
    
    "ok".to_string()
}

// ============================================================================
// PROPER PATTERNS - For comparison
// ============================================================================

pub fn properly_joined_thread(_input: String) -> String {
    let handle = thread::spawn(|| {
        thread::sleep(Duration::from_millis(100));
    });
    
    let _ = handle.join();
    "ok".to_string()
}

pub fn properly_joined_multiple(_input: String) -> String {
    let handles: Vec<_> = (0..5)
        .map(|_| {
            thread::spawn(|| {
                thread::sleep(Duration::from_millis(100));
            })
        })
        .collect();
    
    for handle in handles {
        let _ = handle.join();
    }
    
    "ok".to_string()
}

pub fn properly_scoped_threads(_input: String) -> String {
    let data = vec![1, 2, 3];
    
    thread::scope(|s| {
        for item in &data {
            s.spawn(move || {
                let _ = item;
                thread::sleep(Duration::from_millis(100));
            });
        }
        // scope waits for all threads
    });
    
    "ok".to_string()
}

pub fn properly_used_channels(_input: String) -> String {
    use std::sync::mpsc;
    
    let (tx, rx) = mpsc::channel();
    
    let handle = thread::spawn(move || {
        for i in 0..5 {
            let _ = tx.send(i);
            thread::sleep(Duration::from_millis(50));
        }
    });
    
    for val in rx {
        let _ = val;
    }
    
    let _ = handle.join();
    "ok".to_string()
}

pub fn properly_locked_mutex(_input: String) -> String {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..5 {
        let counter = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        }));
    }
    
    for handle in handles {
        let _ = handle.join();
    }
    
    "ok".to_string()
}
