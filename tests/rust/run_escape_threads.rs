// Example runner for escape_threads tests
use escape_tests_rust::escape_threads;

fn main() {
    println!("=== Rust Thread Escape Examples ===\n");

    println!("1. spawn_detached_thread:");
    let result = escape_threads::spawn_detached_thread("test".to_string());
    println!("   Result: {}\n", result);

    println!("2. spawn_multiple_detached_threads:");
    let result = escape_threads::spawn_multiple_detached_threads("test".to_string());
    println!("   Result: {}\n", result);

    println!("3. spawn_nested_detached_thread:");
    let result = escape_threads::spawn_nested_detached_thread("test".to_string());
    println!("   Result: {}\n", result);

    println!("4. spawn_with_shared_state:");
    let result = escape_threads::spawn_with_shared_state("test".to_string());
    println!("   Result: {}\n", result);

    println!("All tests completed. Threads are still running in background (ESCAPED!)");
    println!("Press Ctrl+C to exit...");
    
    std::thread::sleep(std::time::Duration::from_secs(15));
}
