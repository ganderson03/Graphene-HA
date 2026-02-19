/**
 * Advanced/tricky escape patterns for Node.js
 * Designed to challenge async/await detection
 */

// === Obfuscated Promise Escapes ===

function createLeakyPromiseFactory() {
    return new Promise((resolve) => {
        setTimeout(() => resolve('leaked'), 2000);
    });
}

module.exports.createPromiseViaFactory = function(_input) {
    // Create promise but don't await - it stays pending
    createLeakyPromiseFactory();
    return 'ok';
};

module.exports.createPromiseInArray = function(_input) {
    // Hide promise in data structure
    const promises = [
        new Promise(resolve => setTimeout(resolve, 2000))
    ];
    // Don't await - promise escapes
    return 'ok';
};

module.exports.createPromiseWithoutAwait = function(_input) {
    // Create async context but don't await
    (async () => {
        await new Promise(resolve => setTimeout(resolve, 2000));
    })();
    return 'ok';
};

// === Dynamic/Hidden Async Operations ===

const hiddenAsyncQueue = [];

module.exports.hideAsyncInArray = function(_input) {
    hiddenAsyncQueue.push(
        new Promise(resolve => setTimeout(resolve, 2000))
    );
    return 'ok';
};

module.exports.hideAsyncViaFunction = function(_input) {
    function scheduleWork() {
        return new Promise(resolve => {
            setInterval(() => 'working', 1000);
            resolve();
        });
    }
    // Start work but don't await
    scheduleWork();
    return 'ok';
};

// === Conditional Escapes ===

module.exports.leakAsyncConditionally = function(_input) {
    if (_input.length > 3) {
        // Promise only created sometimes
        new Promise(resolve => setTimeout(resolve, 2000));
    }
    return 'ok';
};

module.exports.leakAsyncInCatch = function(_input) {
    Promise.reject('trigger error')
        .catch(() => {
            // Schedule work in catch without awaiting
            setTimeout(() => 'work', 2000);
            return 'ok';
        });
    return 'ok';
};

// === Weak/Detached References ===

const WeakMap = require('util').inspect;

module.exports.storePromiseWeakly = function(_input) {
    const promise = new Promise(resolve => setTimeout(resolve, 2000));
    
    // Store in way that doesn't hold strong reference
    Promise.resolve().then(() => promise);
    
    return 'ok';
};

// === Event Handler Escapes ===

const eventTracking = {};

module.exports.leakViaEventListener = function(_input) {
    const emitter = { once: (event, handler) => {} };
    
    // Schedule work via event (but event never fires)
    emitter.once('custom', () => setTimeout(() => 'work', 2000));
    
    return 'ok';
};

module.exports.leakMultipleListeners = function(_input) {
    const listeners = [];
    
    for (let i = 0; i < 3; i++) {
        listeners.push(() => setTimeout(() => 'work', 2000));
    }
    
    // Create async work from listeners
    listeners.forEach(l => l());
    
    return 'ok';
};

// === Interval/Timeout Obfuscation ===

module.exports.createIntervalDynamically = function(_input) {
    const timers = [];
    
    for (let i = 0; i < 2; i++) {
        timers.push(setInterval(() => {}, 1000 + i * 100));
    }
    
    // Store but never clear
    return 'ok';
};

module.exports.timeoutChain = function(_input) {
    // Chain of timeouts that re-schedule
    function recurse() {
        setTimeout(() => {
            if (Math.random() > 0.1) {
                recurse();  // Keep scheduling
            }
        }, 100);
    }
    recurse();
    return 'ok';
};

module.exports.createLeakingTimer = function(_input) {
    const timer = setInterval(() => {}, 1000);
    
    // Lose reference by not storing it
    return 'ok';
};

// === Promise Chain Escapes ===

module.exports.breakPromiseChain = function(_input) {
    Promise.resolve()
        .then(() => new Promise(resolve => setTimeout(resolve, 2000)))
        .then(() => 'done')
        // Chain doesn't complete - promise escapes
    
    return 'ok';
};

module.exports.multipleUnboundPromises = function(_input) {
    for (let i = 0; i < 3; i++) {
        Promise.resolve()
            .then(() => new Promise(resolve => setTimeout(resolve, 1000)))
            // Multiple dangling promises
    }
    return 'ok';
};

// === Async Function Escapes ===

async function slowAsyncWork() {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return 'done';
}

module.exports.callAsyncWithoutAwait = function(_input) {
    // Call async function but don't await
    slowAsyncWork();
    return 'ok';
};

module.exports.asyncInCallback = function(_input) {
    setImmediate(() => {
        // Async work scheduled in callback
        slowAsyncWork();
    });
    return 'ok';
};

// === Race Conditions ===

module.exports.racePromisesNotAll = function(_input) {
    const promises = [
        new Promise(resolve => setTimeout(resolve, 2000)),
        new Promise(resolve => setTimeout(resolve, 3000)),
        new Promise(resolve => setTimeout(resolve, 4000))
    ];
    
    // Use race - only 1 completes, others leak
    Promise.race(promises);
    return 'ok';
};

// === Recursive Async ===

function recursiveAsync(depth) {
    if (depth <= 0) return Promise.resolve();
    
    return new Promise(resolve => {
        setTimeout(() => {
            recursiveAsync(depth - 1);  // Don't await recursion
            resolve();
        }, 100);
    });
}

module.exports.recursiveAsyncChain = function(_input) {
    // Don't await the recursion
    recursiveAsync(3);
    return 'ok';
};

// === Cleanup Should Work (False Negatives) ===

module.exports.properlyAwaitTimeout = function(_input) {
    // This should NOT flag - properly awaited
    return new Promise(resolve => setTimeout(resolve, 50));
};

module.exports.properlyAwaitPromise = function(_input) {
    // This should NOT flag - properly awaited
    return slowAsyncWork();
};

module.exports.properlyAbortController = function(_input) {
    // This should NOT flag - timer properly cleared
    const timer = setTimeout(() => {}, 10);
    clearTimeout(timer);
    return 'ok';
};

module.exports.properlyShutdownInterval = function(_input) {
    // This should NOT flag - interval cleared
    const interval = setInterval(() => {}, 10);
    clearInterval(interval);
    return 'ok';
};

module.exports.properlyResolvePromises = function(_input) {
    // This should NOT flag - all promises wait for resolution
    return Promise.all([
        new Promise(resolve => setTimeout(resolve, 50)),
        new Promise(resolve => setTimeout(resolve, 50))
    ]);
};
