"""Realistic application patterns that happen to leak concurrency resources.

These are modeled after real-world code: caches, connection pools, loggers,
pub/sub systems, rate limiters, etc. Each function looks like normal
application code but contains a subtle escape.
"""
import threading
import time
import queue
import functools
import weakref
from concurrent.futures import ThreadPoolExecutor


# ============================================================================
# CACHE WITH BACKGROUND REFRESH
# A common pattern: a cache that refreshes itself in the background.
# The refresh thread outlives the caller.
# ============================================================================

class BackgroundCache:
    """Cache that refreshes entries in the background."""

    def __init__(self, ttl=10):
        self._store = {}
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key, loader):
        with self._lock:
            entry = self._store.get(key)
            if entry and (time.monotonic() - entry["ts"]) < self._ttl:
                return entry["value"]

        # Cache miss — load synchronously, then schedule background refresh
        value = loader()
        with self._lock:
            self._store[key] = {"value": value, "ts": time.monotonic()}

        # Background refresh thread is the escape
        def _refresh():
            time.sleep(self._ttl * 0.8)
            fresh = loader()
            with self._lock:
                self._store[key] = {"value": fresh, "ts": time.monotonic()}

        threading.Thread(target=_refresh, name="cache-refresh", daemon=False).start()
        return value


def cache_with_background_refresh(_input_data):
    """Application initializes a cache and reads a value.
    The background refresh thread escapes."""
    cache = BackgroundCache(ttl=2)
    result = cache.get("user:1", loader=lambda: {"name": "alice", "input": _input_data})
    return str(result)


# ============================================================================
# LAZY SINGLETON SERVICE
# The service starts a heartbeat thread on first access.
# Once started it never stops.
# ============================================================================

class _ServiceRegistry:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._running = True
        self._heartbeat = threading.Thread(target=self._heartbeat_loop, daemon=False)
        self._heartbeat.start()

    def _heartbeat_loop(self):
        for _ in range(8):
            if not self._running:
                break
            time.sleep(1)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def lookup(self, name):
        return f"service:{name}"


def lazy_singleton_heartbeat(_input_data):
    """Look up a service. First call starts an immortal heartbeat thread."""
    registry = _ServiceRegistry.get_instance()
    return registry.lookup(_input_data)


# ============================================================================
# DATABASE CONNECTION POOL
# A minimal connection pool with a reaper thread that culls idle connections.
# The reaper never gets shut down.
# ============================================================================

class ConnectionPool:
    def __init__(self, max_size=5, idle_timeout=30):
        self._pool = queue.Queue(maxsize=max_size)
        self._idle_timeout = idle_timeout
        for _ in range(max_size):
            self._pool.put({"created": time.monotonic(), "last_used": time.monotonic()})
        # Reaper thread — the escape
        self._reaper = threading.Thread(target=self._reap_idle, daemon=False, name="pool-reaper")
        self._reaper.start()

    def _reap_idle(self):
        for _ in range(5):
            time.sleep(self._idle_timeout / 2)
            temp = []
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    if (time.monotonic() - conn["last_used"]) < self._idle_timeout:
                        temp.append(conn)
                except queue.Empty:
                    break
            for conn in temp:
                self._pool.put(conn)

    def acquire(self):
        conn = self._pool.get(timeout=5)
        conn["last_used"] = time.monotonic()
        return conn

    def release(self, conn):
        conn["last_used"] = time.monotonic()
        self._pool.put(conn)


def connection_pool_with_reaper(_input_data):
    """Use a connection pool. The idle-connection reaper thread escapes."""
    pool = ConnectionPool(max_size=3, idle_timeout=4)
    conn = pool.acquire()
    _ = f"SELECT * FROM users WHERE name = '{_input_data}'"
    pool.release(conn)
    return "query_complete"


# ============================================================================
# EVENT-DRIVEN LOGGER
# A logger that batches writes in a background flusher thread.
# ============================================================================

class AsyncBatchLogger:
    def __init__(self, flush_interval=2.0):
        self._buffer = []
        self._lock = threading.Lock()
        self._flusher = threading.Thread(target=self._flush_loop, daemon=False, name="log-flusher")
        self._flusher.start()
        self._flush_interval = flush_interval

    def _flush_loop(self):
        for _ in range(5):
            time.sleep(self._flush_interval)
            with self._lock:
                if self._buffer:
                    self._buffer.clear()

    def log(self, message):
        with self._lock:
            self._buffer.append({"ts": time.monotonic(), "msg": message})


def async_batch_logger(_input_data):
    """Create a logger, write a few messages. Flusher thread escapes."""
    logger = AsyncBatchLogger(flush_interval=1)
    logger.log(f"request started: {_input_data}")
    logger.log("processing...")
    logger.log("done")
    return "logged"


# ============================================================================
# RATE LIMITER WITH TOKEN REFILL
# A token-bucket rate limiter that refills in the background.
# ============================================================================

class TokenBucket:
    def __init__(self, rate=10, capacity=100):
        self._tokens = capacity
        self._capacity = capacity
        self._lock = threading.Lock()
        self._refiller = threading.Thread(target=self._refill_loop, args=(rate,),
                                          daemon=False, name="token-refiller")
        self._refiller.start()

    def _refill_loop(self, rate):
        for _ in range(50):
            time.sleep(1.0 / rate if rate else 1.0)
            with self._lock:
                self._tokens = min(self._tokens + 1, self._capacity)

    def consume(self, tokens=1):
        with self._lock:
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False


def rate_limiter_token_refill(_input_data):
    """Check rate limit for a request. Refill thread escapes."""
    limiter = TokenBucket(rate=5, capacity=50)
    allowed = limiter.consume()
    return f"allowed={allowed}"


# ============================================================================
# PUB/SUB DISPATCHER
# A publish/subscribe message bus with a dedicated dispatch thread.
# ============================================================================

class PubSubBus:
    def __init__(self):
        self._subscribers = {}
        self._queue = queue.Queue()
        self._dispatcher = threading.Thread(target=self._dispatch_loop, daemon=False,
                                            name="pubsub-dispatch")
        self._dispatcher.start()

    def _dispatch_loop(self):
        for _ in range(20):
            try:
                topic, data = self._queue.get(block=False)
            except queue.Empty:
                time.sleep(0.2)
                continue
            for callback in self._subscribers.get(topic, []):
                try:
                    callback(data)
                except Exception:
                    pass

    def subscribe(self, topic, callback):
        self._subscribers.setdefault(topic, []).append(callback)

    def publish(self, topic, data):
        self._queue.put((topic, data))


def pubsub_dispatcher(_input_data):
    """Set up a pub/sub bus, publish a message. Dispatcher thread escapes."""
    bus = PubSubBus()
    results = []
    bus.subscribe("events", lambda d: results.append(d))
    bus.publish("events", {"user_input": _input_data})
    time.sleep(0.05)  # Give it a moment to deliver
    return f"delivered={len(results)}"


# ============================================================================
# WATCHDOG / HEALTH MONITOR
# A health-check watchdog that pings a service at intervals.
# ============================================================================

def health_monitor_watchdog(_input_data):
    """Start a health-check watchdog. The monitoring thread escapes."""
    health_status = {"ok": True, "checks": 0}

    def monitor():
        for _ in range(8):
            if not health_status["ok"]:
                break
            health_status["checks"] += 1
            time.sleep(1)

    threading.Thread(target=monitor, name="health-monitor", daemon=False).start()
    # Application proceeds without stopping the monitor
    return f"status=healthy, checks={health_status['checks']}"


# ============================================================================
# DEFERRED RESULT COMPUTATION
# Submit work, return a handle. The underlying thread is leaked.
# ============================================================================

class DeferredResult:
    """A simple future-like wrapper."""
    def __init__(self, fn, *args):
        self._result = None
        self._done = threading.Event()
        self._worker = threading.Thread(target=self._run, args=(fn, args), daemon=False)
        self._worker.start()

    def _run(self, fn, args):
        self._result = fn(*args)
        self._done.set()

    def get(self, timeout=None):
        self._done.wait(timeout=timeout)
        return self._result


def deferred_computation(_input_data):
    """Start a deferred computation but never retrieve the result."""
    def expensive_work(data):
        time.sleep(2)
        return data.upper()

    handle = DeferredResult(expensive_work, _input_data)
    # Return immediately without calling handle.get() — thread escapes
    return "submitted"


# ============================================================================
# RETRY WITH BACKGROUND FALLBACK
# On failure, kick off a background retry. The retry thread is leaked.
# ============================================================================

def retry_with_background_fallback(_input_data):
    """Try an operation; on failure, launch a background retry that escapes."""
    def send_request(data):
        # Simulate transient failure
        if len(data) % 2 == 0:
            raise ConnectionError("server unreachable")
        return "ok"

    def background_retry(data, retries=3):
        for attempt in range(retries):
            time.sleep(1)
            try:
                send_request(data)
                return
            except ConnectionError:
                continue

    try:
        return send_request(_input_data)
    except ConnectionError:
        # Fire-and-forget retry — thread escapes
        threading.Thread(target=background_retry, args=(_input_data,),
                         name="bg-retry", daemon=False).start()
        return "retrying_in_background"


# ============================================================================
# METRICS COLLECTOR
# Periodically flushes accumulated metrics. The flush thread escapes.
# ============================================================================

class MetricsCollector:
    def __init__(self, flush_interval=5):
        self._counters = {}
        self._lock = threading.Lock()
        self._flusher = threading.Thread(target=self._flush_loop, daemon=False,
                                         name="metrics-flush",
                                         args=(flush_interval,))
        self._flusher.start()

    def _flush_loop(self, interval):
        for _ in range(5):
            time.sleep(interval)
            with self._lock:
                snapshot = dict(self._counters)
                self._counters.clear()
            # In real code this would ship to a metrics backend
            _ = snapshot

    def increment(self, name, value=1):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value


def metrics_collector_flush(_input_data):
    """Record some metrics. The flush thread escapes."""
    collector = MetricsCollector(flush_interval=2)
    collector.increment("requests")
    collector.increment("bytes_in", len(_input_data))
    return "metrics_recorded"


# ============================================================================
# FILE WATCHER (inotify-style)
# Watches a path for changes. The watcher thread escapes.
# ============================================================================

def file_watcher_escape(_input_data):
    """Start a file watcher that polls for changes. Thread escapes."""
    changes_detected = []

    def watch(path, poll_interval=1):
        import os
        last_mtime = None
        for _ in range(10):
            try:
                mtime = os.path.getmtime(path)
                if last_mtime is not None and mtime != last_mtime:
                    changes_detected.append(mtime)
                last_mtime = mtime
            except OSError:
                pass
            time.sleep(poll_interval)

    threading.Thread(target=watch, args=("/tmp",), name="file-watcher", daemon=False).start()
    return f"watching, changes={len(changes_detected)}"


# ============================================================================
# TASK SCHEDULER (CRON-LIKE)
# Schedules a periodic task. The scheduler thread escapes.
# ============================================================================

class SimpleScheduler:
    def __init__(self):
        self._tasks = []
        self._runner = threading.Thread(target=self._run_loop, daemon=False, name="scheduler")
        self._runner.start()

    def _run_loop(self):
        for _ in range(50):
            now = time.monotonic()
            for task in self._tasks:
                if now >= task["next_run"]:
                    try:
                        task["fn"]()
                    except Exception:
                        pass
                    task["next_run"] = now + task["interval"]
            time.sleep(0.1)

    def every(self, seconds, fn):
        self._tasks.append({"interval": seconds, "fn": fn, "next_run": time.monotonic()})


def task_scheduler_escape(_input_data):
    """Register a periodic task. The scheduler thread escapes."""
    scheduler = SimpleScheduler()
    call_count = [0]
    scheduler.every(1.0, lambda: call_count.__setitem__(0, call_count[0] + 1))
    return f"scheduled, runs={call_count[0]}"


# ============================================================================
# THREAD THAT LOOKS JOINED BUT ISN'T
# The join has a timeout that expires, so the thread is still running.
# ============================================================================

def join_with_insufficient_timeout(_input_data):
    """Join a thread but with a timeout too short. Thread escapes silently."""
    def slow_work():
        time.sleep(2)

    t = threading.Thread(target=slow_work, name="slow-work")
    t.start()
    t.join(timeout=0.001)  # Returns immediately, thread still running
    return "finished"


# ============================================================================
# EXECUTOR THAT APPEARS SHUT DOWN
# shutdown(wait=False) returns immediately but threads keep running.
# ============================================================================

def executor_shutdown_nowait(_input_data):
    """Shut down executor with wait=False — threads still alive."""
    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="nowait")
    pool.submit(time.sleep, 2)
    pool.submit(time.sleep, 2)
    pool.shutdown(wait=False)  # Returns instantly, workers still live
    return "shutdown_requested"


# ============================================================================
# MEMOIZATION DECORATOR THAT LEAKS A PREFETCH THREAD
# ============================================================================

def memoize_with_prefetch(fn):
    """Decorator that caches results and prefetches related keys."""
    cache = {}
    lock = threading.Lock()

    @functools.wraps(fn)
    def wrapper(key):
        with lock:
            if key in cache:
                return cache[key]
        result = fn(key)
        with lock:
            cache[key] = result

        # Prefetch nearby keys in background — thread escapes
        def _prefetch():
            for related in [key + "_related", key + "_alt"]:
                val = fn(related)
                with lock:
                    cache[related] = val

        threading.Thread(target=_prefetch, name="prefetch", daemon=False).start()
        return result

    return wrapper


@memoize_with_prefetch
def _fetch_config(key):
    time.sleep(0.5)
    return f"config_value_for_{key}"


def memoized_prefetch_escape(_input_data):
    """Call a memoized function. The prefetch thread escapes."""
    value = _fetch_config(_input_data or "default_key")
    return str(value)


# ============================================================================
# PRODUCER/CONSUMER WHERE CONSUMER OUTLIVES CALLER
# ============================================================================

def producer_consumer_leak(_input_data):
    """Producer finishes, but consumer thread keeps waiting for more."""
    q = queue.Queue()
    results = []

    def consumer():
        empties = 0
        while empties < 3:
            try:
                item = q.get(block=False)
            except queue.Empty:
                empties += 1
                time.sleep(0.5)
                continue
            if item is None:
                break
            results.append(item.upper())

    worker = threading.Thread(target=consumer, name="consumer", daemon=False)
    worker.start()

    # Produce items
    for word in (_input_data or "hello world").split():
        q.put(word)

    # BUG: forgot to send the sentinel None, so consumer blocks forever
    return f"produced={len((_input_data or 'hello world').split())}"
