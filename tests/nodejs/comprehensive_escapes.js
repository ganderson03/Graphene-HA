/**
 * Comprehensive JavaScript/Node.js escape patterns
 * Tests async/await, promises, callbacks, timers, and child processes
 */

// ============================================================================
// PROMISE & ASYNC ESCAPES - Unresolved chains, missing await
// ============================================================================

function createUnresolvedPromiseChain(_input) {
    // Create promise chain that never completes
    const promise = Promise.resolve(1)
        .then(() => new Promise(() => {
            // Never resolves or rejects
        }))
        .then(() => console.log('never runs'))
        .catch(() => console.log('never catches'));
    
    // Don't return it, don't await it
    return "ok";
}

function createAbandonedPromiseWithCallback(_input) {
    // Promise with callback that hangs
    Promise.resolve()
        .then(() => {
            return new Promise(() => {
                // Callback never resolves
                setInterval(() => {}, 1000);
            });
        })
        .catch(err => console.error(err));
    
    return "ok";
}

function createNestedPromiseEscape(_input) {
    // Deeply nested unfulfilled promises
    const escapePromise = Promise.resolve(1)
        .then(x => Promise.resolve(x + 1))
        .then(x => Promise.resolve(x + 1))
        .then(() => new Promise(() => {
            // Infinite pending at bottom of chain
        }));
    
    return "ok";
}

function createPromiseAllWithPending(_input) {
    // Promise.all with some unresolved promises
    const promises = [
        Promise.resolve(1),
        Promise.resolve(2),
        new Promise(() => {
            // Never resolves
        }),
        Promise.resolve(3)
    ];
    
    Promise.all(promises)
        .then(() => console.log('never runs'))
        .catch(() => console.log('never catches'));
    
    return "ok";
}

function createPromiseRaceWithPending(_input) {
    // Promise.race where non-winning promises never resolve
    const promises = [
        new Promise(() => {
            // Never resolves, loses race
        }),
        new Promise(() => {
            // Never resolves, loses race
            setInterval(() => {}, 500);
        })
    ];
    
    Promise.race(promises)
        .then(val => console.log('waits on one of them'))
        .catch(err => console.error(err));
    
    return "ok";
}

// ============================================================================
// ASYNC/AWAIT ESCAPES - Broken await chains
// ============================================================================

async function createDanglingAsyncTask(_input) {
    // Create and launch async without awaiting
    (async () => {
        await new Promise(() => {
            // Never resolves
        });
    })();  // No await on IIFE
    
    return "ok";
}

async function createFireAndForgetAsync(_input) {
    // Async function fire-and-forget in variables
    const hangingTask = (async () => {
        await new Promise(() => {
            setInterval(() => {}, 1000);
        });
    })();
    
    // Not awaited when function returns
    return "ok";
}

async function createUnawaitedAsyncArray(_input) {
    // Array of async operations, some not awaited
    const tasks = [
        Promise.resolve(1),
        (async () => {
            await new Promise(() => {});
        })(),
        Promise.resolve(3)
    ];
    
    // Only await some
    await Promise.resolve(tasks[0]);
    // tasks[1] and others hang
    
    return "ok";
}

async function createMissingAwaitInLoop(_input) {
    // Loop that doesn't properly await all tasks
    const promises = [];
    for (let i = 0; i < 3; i++) {
        promises.push(
            new Promise(() => {
                setInterval(() => {}, 500);
            })
        );
    }
    
    // Only await first few
    await promises[0];
    // Others leak
    
    return "ok";
}

// ============================================================================
// CALLBACK ESCAPES - Unresolved callbacks and hanging listeners
// ============================================================================

function createHangingCallback(_input) {
    // Callback registered but never called
    const handle = setTimeout(() => {
        // This executes after function returns
        setInterval(() => {}, 1000);
    }, 10);
    
    // Never clear the timeout
    return "ok";
}

function createMultipleHangingCallbacks(_input) {
    // Multiple pending callbacks
    for (let i = 0; i < 5; i++) {
        setInterval(() => {
            // These run forever
        }, Math.random() * 1000);
    }
    
    return "ok";
}

function createNestedCallbackEscape(_input) {
    // Callbacks nested multiple levels
    setTimeout(() => {
        setTimeout(() => {
            setInterval(() => {
                // Infinite pending callback
            }, 1000);
        }, 100);
    }, 100);
    
    return "ok";
}

function createCallbackWithPromiseMix(_input) {
    // Mix of callbacks and promises that hang
    setTimeout(async () => {
        await new Promise(() => {
            // Never resolves
        });
    }, 50);
    
    return "ok";
}

// ============================================================================
// EVENT EMITTER ESCAPES
// ============================================================================

function createEventEmitterEscape(_input) {
    const EventEmitter = require('events');
    const emitter = new EventEmitter();
    
    // Register many listeners
    emitter.on('data', () => {
        // Handler that never unregisters
        setInterval(() => {}, 1000);
    });
    
    emitter.on('update', async () => {
        // Async handler that never completes
        await new Promise(() => {});
    });
    
    // Listeners registered but never cleaned up
    return "ok";
}

function createEmitterLeak(_input) {
    const EventEmitter = require('events');
    const emitter = new EventEmitter();
    
    // Add many listeners without cleanup
    for (let i = 0; i < 10; i++) {
        emitter.on(`event${i}`, () => {
            // Each handler hangs
            new Promise(() => {});
        });
    }
    
    return "ok";
}

// ============================================================================
// CHILD PROCESS ESCAPES  
// ============================================================================

function createChildProcessEscape(_input) {
    const { spawn } = require('child_process');
    
    // Spawn child process but never wait for it
    const child = spawn('sleep', ['10']);
    
    // Don't listen to close event, don't kill it
    return "ok";
}

function createMultipleChildProcesses(_input) {
    const { spawn } = require('child_process');
    
    // Spawn multiple processes, not all are managed
    const processes = [];
    for (let i = 0; i < 3; i++) {
        const child = spawn('node', ['-e', 'setInterval(() => {}, 1000)']);
        processes.push(child);
        
        if (i === 0) {
            // Only manage first one
            child.on('close', () => console.log('process done'));
        }
        // Others are not managed
    }
    
    return "ok";
}

function createChildProcessWithUnhandledOutput(_input) {
    const { spawn } = require('child_process');
    
    const child = spawn('node', ['-e', 'setInterval(() => console.log("x"), 100)']);
    
    child.stdout.on('data', (data) => {
        // Handler that could hang or be incomplete
        // No cleanup
    });
    
    // Process never properly terminated
    return "ok";
}

// ============================================================================
// WORKER THREAD ESCAPES (Node.js worker_threads)
// ============================================================================

function createWorkerThreadEscape(_input) {
    try {
        const { Worker } = require('worker_threads');
        
        const worker = new Worker('./worker.js');
        
        worker.on('message', (msg) => {
            console.log(msg);
        });
        
        // Worker created but never terminated
        return "ok";
    } catch (e) {
        return "ok"; // Fallback if worker_threads not available
    }
}

function createMultipleWorkerThreads(_input) {
    try {
        const { Worker } = require('worker_threads');
        
        const workers = [];
        for (let i = 0; i < 5; i++) {
            const w = new Worker('./infinite-worker.js');
            workers.push(w);
        }
        
        // Workers never terminated
        return "ok";
    } catch (e) {
        return "ok";
    }
}

// ============================================================================
// STREAM ESCAPES
// ============================================================================

function createStreamEscape(_input) {
    const fs = require('fs');
    
    const readStream = fs.createReadStream('/dev/zero');
    const writeStream = fs.createWriteStream('/dev/null');
    
    readStream.pipe(writeStream);
    
    // Streams never properly closed or errorhandled
    return "ok";
}

function createNestedStreamEscape(_input) {
    const fs = require('fs');
    const zlib = require('zlib');
    
    const readStream = fs.createReadStream('/dev/zero');
    const gzip = zlib.createGzip();
    const writeStream = fs.createWriteStream('/dev/null');
    
    readStream.pipe(gzip).pipe(writeStream);
    
    // Chain created but never properly managed
    return "ok";
}

// ============================================================================
// CLOSURE & SCOPE ESCAPES
// ============================================================================

let globalTasks = [];  // Global task registry

function createTaskInGlobalRegistry(_input) {
    // Create task and store in global
    const task = new Promise(() => {
        setInterval(() => {}, 1000);
    });
    
    globalTasks.push(task);
    // Never cleaned up
    
    return "ok";
}

function createEscapeViaModuleState(_input) {
    // Store escape in module-level variable
    const moduleLevel = (async () => {
        await new Promise(() => {
            // Infinite pending
        });
    })();
    
    // Stored in module scope, never cleaned
    return "ok";
}

// ============================================================================
// EXCEPTION HANDLING ESCAPES
// ============================================================================

function createEscapeInCatchBlock(_input) {
    Promise.resolve()
        .then(() => {
            throw new Error("trigger");
        })
        .catch(err => {
            // Unresolved promise in error handler
            setInterval(() => {}, 1000);
            return new Promise(() => {});
        });
    
    return "ok";
}

function createEscapeInFinally(_input) {
    try {
        // Code
    } finally {
        // Finally with pending async
        const pending = new Promise(() => {
            setInterval(() => {}, 1000);
        });
    }
    
    return "ok";
}

// ============================================================================
// RACE CONDITIONS & TIMING ESCAPES
// ============================================================================

function createRaceConditionPendingTask(_input) {
    // Create task that might or might not settle depending on timing
    const task = Promise.race([
        new Promise(() => {
            // Never resolves
            setInterval(() => {}, 1000);
        }),
        new Promise(resolve => {
            setTimeout(resolve, 1000);
        })
    ]);
    
    // Even if second resolves, first waits forever
    return "ok";
}

function createTimingBasedEscape(_input) {
    // Escape behavior depends on timing
    const start = Date.now();
    
    setInterval(() => {
        if (Date.now() - start > 100) {
            // Might run, might not, depending on exit timing
            new Promise(() => {});
        }
    }, 10);
    
    return "ok";
}

// ============================================================================
// PROPER COMPLETIONS - For comparison
// ============================================================================

async function properlyAwaitedAsyncTask(_input) {
    // Proper async pattern
    const result = await new Promise(resolve => {
        setTimeout(() => resolve("done"), 100);
    });
    
    return "ok";
}

async function properlyAwaitedAsyncArray(_input) {
    // Array of tasks properly awaited
    const tasks = [
        new Promise(resolve => setTimeout(() => resolve(1), 50)),
        new Promise(resolve => setTimeout(() => resolve(2), 50)),
        new Promise(resolve => setTimeout(() => resolve(3), 50))
    ];
    
    const results = await Promise.all(tasks);
    return "ok";
}

function properClosedStream(_input) {
    const fs = require('fs');
    
    const readStream = fs.createReadStream('/dev/zero');
    const writeStream = fs.createWriteStream('/dev/null');
    
    readStream.pipe(writeStream);
    
    // Properly handle close
    writeStream.on('close', () => {
        console.log('stream closed');
    });
    
    // Close after reasonable time
    setTimeout(() => {
        readStream.destroy();
        writeStream.destroy();
    }, 1000);
    
    return "ok";
}

function properChildProcessManagement(_input) {
    const { spawn } = require('child_process');
    
    const child = spawn('sleep', ['1']);
    
    child.on('close', (code) => {
        console.log(`Child exited with code ${code}`);
    });
    
    return "ok";
}

module.exports = {
    // Promise escapes
    createUnresolvedPromiseChain,
    createAbandonedPromiseWithCallback,
    createNestedPromiseEscape,
    createPromiseAllWithPending,
    createPromiseRaceWithPending,
    
    // Async/await escapes
    createDanglingAsyncTask,
    createFireAndForgetAsync,
    createUnawaitedAsyncArray,
    createMissingAwaitInLoop,
    
    // Callback escapes
    createHangingCallback,
    createMultipleHangingCallbacks,
    createNestedCallbackEscape,
    createCallbackWithPromiseMix,
    
    // Event emitter escapes
    createEventEmitterEscape,
    createEmitterLeak,
    
    // Child process escapes
    createChildProcessEscape,
    createMultipleChildProcesses,
    createChildProcessWithUnhandledOutput,
    
    // Worker thread escapes
    createWorkerThreadEscape,
    createMultipleWorkerThreads,
    
    // Stream escapes
    createStreamEscape,
    createNestedStreamEscape,
    
    // Closure/scope escapes
    createTaskInGlobalRegistry,
    createEscapeViaModuleState,
    
    // Exception escapes
    createEscapeInCatchBlock,
    createEscapeInFinally,
    
    // Race conditions
    createRaceConditionPendingTask,
    createTimingBasedEscape,
    
    // Proper patterns (non-escapes)
    properlyAwaitedAsyncTask,
    properlyAwaitedAsyncArray,
    properClosedStream,
    properChildProcessManagement
};
