// Example runner for escape_async tests
use escape_tests_rust::escape_async;

#[tokio::main]
async fn main() {
    println!("=== Rust Async Escape Examples ===\n");

    println!("1. spawn_detached_task:");
    let result = escape_async::spawn_detached_task("test".to_string()).await;
    println!("   Result: {}\n", result);

    println!("2. spawn_multiple_detached_tasks:");
    let result = escape_async::spawn_multiple_detached_tasks("test".to_string()).await;
    println!("   Result: {}\n", result);

    println!("3. spawn_infinite_task:");
    let result = escape_async::spawn_infinite_task("test".to_string()).await;
    println!("   Result: {}\n", result);

    println!("4. create_joinset_without_waiting:");
    let result = escape_async::create_joinset_without_waiting("test".to_string()).await;
    println!("   Result: {}\n", result);

    println!("All tests completed. Tasks are still running in background (ESCAPED!)");
    println!("Press Ctrl+C to exit...");
    
    tokio::time::sleep(tokio::time::Duration::from_secs(15)).await;
}
