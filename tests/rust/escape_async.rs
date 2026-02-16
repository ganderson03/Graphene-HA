// Rust concurrency escape examples - Async/Tokio-based

use tokio::time::{sleep, Duration};
use tokio::task;

/// Spawns a tokio task without awaiting - ESCAPE
pub async fn spawn_detached_task(input: String) -> String {
    task::spawn(async move {
        sleep(Duration::from_secs(10)).await;
        println!("Task completed: {}", input);
    });
    "ok".to_string()
}

/// Spawns multiple tokio tasks without awaiting - ESCAPE
pub async fn spawn_multiple_detached_tasks(input: String) -> String {
    for i in 0..5 {
        let input_clone = input.clone();
        task::spawn(async move {
            sleep(Duration::from_secs(2)).await;
            println!("Task {} completed: {}", i, input_clone);
        });
    }
    "ok".to_string()
}

/// Spawns a task with infinite loop - ESCAPE
pub async fn spawn_infinite_task(input: String) -> String {
    task::spawn(async move {
        loop {
            sleep(Duration::from_secs(1)).await;
            println!("Infinite task: {}", input);
        }
    });
    "ok".to_string()
}

/// Spawns nested tasks without awaiting - ESCAPE
pub async fn spawn_nested_tasks(input: String) -> String {
    task::spawn(async move {
        let input_clone = input.clone();
        task::spawn(async move {
            sleep(Duration::from_secs(2)).await;
            println!("Nested task: {}", input_clone);
        });
    });
    "ok".to_string()
}

/// Spawns blocking task without awaiting - ESCAPE
pub async fn spawn_blocking_detached(input: String) -> String {
    task::spawn_blocking(move || {
        std::thread::sleep(Duration::from_secs(5));
        println!("Blocking task: {}", input);
    });
    "ok".to_string()
}

/// Spawns local task (on LocalSet) without awaiting - ESCAPE
pub async fn spawn_local_detached(input: String) -> String {
    use tokio::task::LocalSet;
    
    let local = LocalSet::new();
    local.spawn_local(async move {
        sleep(Duration::from_secs(2)).await;
        println!("Local task: {}", input);
    });
    
    "ok".to_string()
}

/// Creates a JoinSet but doesn't wait for completion - ESCAPE
pub async fn create_joinset_without_waiting(input: String) -> String {
    use tokio::task::JoinSet;
    
    let mut set = JoinSet::new();
    
    for i in 0..3 {
        let input_clone = input.clone();
        set.spawn(async move {
            sleep(Duration::from_secs(2)).await;
            format!("Result {}: {}", i, input_clone)
        });
    }
    
    // Don't await any of the tasks - they're leaked when set drops
    "ok".to_string()
}

/// Spawns task that panics - ESCAPE + CRASH
pub async fn spawn_panicking_task(input: String) -> String {
    task::spawn(async move {
        sleep(Duration::from_millis(100)).await;
        panic!("Task panic: {}", input);
    });
    "ok".to_string()
}

/// Spawns task with cancellation but no abort - ESCAPE
pub async fn spawn_with_cancellation_token(input: String) -> String {
    use tokio_util::sync::CancellationToken;
    
    let token = CancellationToken::new();
    let token_clone = token.clone();
    
    task::spawn(async move {
        tokio::select! {
            _ = token_clone.cancelled() => {
                println!("Task cancelled");
            }
            _ = sleep(Duration::from_secs(10)) => {
                println!("Task completed: {}", input);
            }
        }
    });
    
    // Don't cancel the token - task keeps running
    "ok".to_string()
}

/// Creates interval stream without dropping - ESCAPE
pub async fn create_detached_interval(input: String) -> String {
    use tokio::time::interval;
    
    let mut interval = interval(Duration::from_secs(1));
    
    task::spawn(async move {
        loop {
            interval.tick().await;
            println!("Interval tick: {}", input);
        }
    });
    
    "ok".to_string()
}
