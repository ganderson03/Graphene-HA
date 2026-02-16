// Rust safe concurrency examples - Async/Tokio-based (NO ESCAPE)

use tokio::time::{sleep, Duration};
use tokio::task;

/// Spawns task and awaits it - SAFE
pub async fn spawn_and_await_task(input: String) -> String {
    let handle = task::spawn(async move {
        sleep(Duration::from_millis(100)).await;
        format!("Processed: {}", input)
    });
    
    handle.await.unwrap()
}

/// Spawns multiple tasks and awaits all - SAFE
pub async fn spawn_and_await_multiple(input: String) -> String {
    let handles: Vec<_> = (0..3)
        .map(|i| {
            let input_clone = input.clone();
            task::spawn(async move {
                sleep(Duration::from_millis(50)).await;
                format!("Task {}: {}", i, input_clone)
            })
        })
        .collect();
    
    let results: Vec<_> = futures::future::join_all(handles)
        .await
        .into_iter()
        .map(|r| r.unwrap())
        .collect();
    
    results.join(", ")
}

/// Uses JoinSet and waits for all tasks - SAFE
pub async fn use_joinset_properly(input: String) -> String {
    use tokio::task::JoinSet;
    
    let mut set = JoinSet::new();
    
    for i in 0..3 {
        let input_clone = input.clone();
        set.spawn(async move {
            sleep(Duration::from_millis(50)).await;
            format!("Result {}: {}", i, input_clone)
        });
    }
    
    let mut results = vec![];
    while let Some(res) = set.join_next().await {
        results.push(res.unwrap());
    }
    
    results.join(", ")
}

/// Uses select with proper cleanup - SAFE
pub async fn use_select_properly(input: String) -> String {
    let task1 = task::spawn(async move {
        sleep(Duration::from_millis(100)).await;
        format!("Task1: {}", input)
    });
    
    let task2 = task::spawn(async {
        sleep(Duration::from_millis(200)).await;
        "Task2: slow".to_string()
    });
    
    tokio::select! {
        res = task1 => res.unwrap(),
        res = task2 => res.unwrap(),
    }
}

/// Uses timeout with proper handling - SAFE
pub async fn use_timeout_properly(input: String) -> String {
    use tokio::time::timeout;
    
    let operation = async move {
        sleep(Duration::from_millis(100)).await;
        format!("Completed: {}", input)
    };
    
    match timeout(Duration::from_secs(1), operation).await {
        Ok(result) => result,
        Err(_) => "Timeout".to_string(),
    }
}

/// Uses spawn_blocking and awaits - SAFE
pub async fn use_spawn_blocking_properly(input: String) -> String {
    let handle = task::spawn_blocking(move || {
        std::thread::sleep(Duration::from_millis(100));
        format!("Blocking: {}", input)
    });
    
    handle.await.unwrap()
}

/// Uses cancellation token properly - SAFE
pub async fn use_cancellation_properly(input: String) -> String {
    use tokio_util::sync::CancellationToken;
    
    let token = CancellationToken::new();
    let token_clone = token.clone();
    
    let handle = task::spawn(async move {
        tokio::select! {
            _ = token_clone.cancelled() => {
                "Cancelled".to_string()
            }
            _ = sleep(Duration::from_secs(10)) => {
                format!("Completed: {}", input)
            }
        }
    });
    
    // Cancel after short delay
    sleep(Duration::from_millis(10)).await;
    token.cancel();
    
    handle.await.unwrap()
}

/// Uses interval with proper cleanup - SAFE
pub async fn use_interval_properly(input: String) -> String {
    use tokio::time::interval;
    
    let mut interval = interval(Duration::from_millis(50));
    let mut count = 0;
    
    loop {
        interval.tick().await;
        count += 1;
        if count >= 3 {
            break;
        }
    }
    
    format!("Ticked {} times: {}", count, input)
}

/// Uses async channels properly - SAFE  
pub async fn use_channels_properly(input: String) -> String {
    use tokio::sync::mpsc;
    
    let (tx, mut rx) = mpsc::channel(10);
    
    let sender_task = task::spawn(async move {
        for i in 0..3 {
            tx.send(format!("Message {}: {}", i, input)).await.unwrap();
            sleep(Duration::from_millis(50)).await;
        }
    });
    
    let mut results = vec![];
    while let Some(msg) = rx.recv().await {
        results.push(msg);
        if results.len() >= 3 {
            break;
        }
    }
    
    sender_task.await.unwrap();
    results.join(", ")
}

/// Uses try_join for parallel execution - SAFE
pub async fn use_try_join(input: String) -> String {
    let task1 = async {
        sleep(Duration::from_millis(50)).await;
        Ok::<_, String>(format!("Task1: {}", input))
    };
    
    let task2 = async {
        sleep(Duration::from_millis(100)).await;
        Ok::<_, String>("Task2: done".to_string())
    };
    
    match tokio::try_join!(task1, task2) {
        Ok((r1, r2)) => format!("{}, {}", r1, r2),
        Err(e) => format!("Error: {}", e),
    }
}

/// Uses LocalSet properly - SAFE
pub async fn use_localset_properly(input: String) -> String {
    use tokio::task::LocalSet;
    
    let local = LocalSet::new();
    
    local
        .run_until(async move {
            let handle = task::spawn_local(async move {
                sleep(Duration::from_millis(100)).await;
                format!("Local: {}", input)
            });
            
            handle.await.unwrap()
        })
        .await
}
