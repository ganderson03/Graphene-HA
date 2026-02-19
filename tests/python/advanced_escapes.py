"""Advanced escape patterns designed to challenge detection"""
import threading
import multiprocessing as mp
import time
import functools
from concurrent.futures import ThreadPoolExecutor


# === Obfuscated Escapes ===

def spawn_thread_via_function_ref(_input_data):
    """Spawn thread via function reference - hides thread creation"""
    def create_worker():
        def worker():
            time.sleep(2)
        t = threading.Thread(target=worker)
        t.start()
    create_worker()
    return "ok"


def spawn_thread_via_lambda(_input_data):
    """Spawn thread using lambda instead of direct call"""
    create = lambda: (
        t := threading.Thread(target=lambda: time.sleep(2)),
        t.start()
    )[-1]
    create()
    return "ok"


def spawn_thread_in_generator(_input_data):
    """Spawn thread inside generator - harder to analyze"""
    def thread_factory():
        def worker():
            time.sleep(2)
        yield threading.Thread(target=worker)
    gen = thread_factory()
    thread = next(gen)
    thread.start()
    return "ok"


# === Delayed Escapes ===

def spawn_thread_with_delayed_start(_input_data):
    """Create thread but delay start - escape becomes visible only later"""
    def worker():
        time.sleep(0.5)  # Short initial delay
        time.sleep(2)    # Long work
    thread = threading.Thread(target=worker)
    thread.daemon = False
    # Small delay before starting
    time.sleep(0.01)
    thread.start()
    return "ok"


_thread_registry = []

def spawn_thread_to_registry(_input_data):
    """Store thread reference in global registry - exit without cleanup"""
    def worker():
        time.sleep(2)
    thread = threading.Thread(target=worker)
    thread.start()
    _thread_registry.append(thread)  # Store but never join
    return "ok"


# === Conditional Escapes ===

def spawn_thread_conditionally(_input_data):
    """Spawn thread only under certain conditions"""
    should_leak = len(_input_data) > 3
    if should_leak:
        def worker():
            time.sleep(2)
        thread = threading.Thread(target=worker)
        thread.start()
    return "ok"


def spawn_thread_in_try_except(_input_data):
    """Spawn thread inside exception handler - harder to track"""
    try:
        raise ValueError("trigger escape")
    except ValueError:
        def worker():
            time.sleep(2)
        thread = threading.Thread(target=worker)
        thread.start()
    return "ok"


# === Dynamically Hidden Escapes ===

_thread_storage = {}

def spawn_thread_with_dynamic_key(_input_data):
    """Store thread under dynamically computed key"""
    key = f"worker_{id(_input_data)}"
    def worker():
        time.sleep(2)
    thread = threading.Thread(target=worker)
    thread.start()
    _thread_storage[key] = thread
    return "ok"


def spawn_thread_via_setattr(_input_data):
    """Use setattr to store thread - hides from static analysis"""
    class Container:
        pass
    
    def worker():
        time.sleep(2)
    
    container = Container()
    thread = threading.Thread(target=worker)
    thread.start()
    setattr(container, f"thread_{id(thread)}", thread)
    return "ok"


# === Weak Reference Escapes ===

import weakref

def spawn_thread_weak_reference(_input_data):
    """Store weak reference that becomes invalid - escape not obvious"""
    def worker():
        time.sleep(2)
    thread = threading.Thread(target=worker)
    thread.start()
    
    # Store weak ref (will become invalid but thread still runs)
    weak_ref = weakref.ref(thread)
    
    # Let weak ref go out of scope, but thread still runs
    return "ok"


# === Executor Escapes Without Context Manager ===

def leak_executor_on_exception(_input_data):
    """Executor leaked when exception occurs before cleanup"""
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        executor.submit(time.sleep, 2)
        if "error" in _input_data:
            raise ValueError("Simulated error")
    except ValueError:
        pass  # Exit without shutdown
    return "ok"


# === Process Escapes ===

def _process_worker():
    """Helper for process escapes"""
    time.sleep(2)


def spawn_process_without_join(_input_data):
    """Spawn process and return without joining"""
    process = mp.Process(target=_process_worker)
    process.start()
    return "ok"


def spawn_multiple_processes_mixed(_input_data):
    """Mix of joined and unjoined processes"""
    p1 = mp.Process(target=_process_worker)
    p1.start()
    p1.join()  # This one is joined
    
    p2 = mp.Process(target=_process_worker)
    p2.start()
    # p2 is NOT joined - leaks
    
    return "ok"


# === Thread Pool Escapes ===

_pool = None

def leak_pool_incrementally(_input_data):
    """Slowly leak pool by adding more work"""
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=2)
    
    # Submit work but never retrieve results or shutdown
    for _ in range(3):
        _pool.submit(time.sleep, 2)
    
    return "ok"


# === Deferred/Delayed Spawning ===

_pending_threads = []

def schedule_thread_for_later(_input_data):
    """Schedule thread to be spawned but not immediately"""
    def worker():
        time.sleep(2)
    
    def spawn_later():
        t = threading.Thread(target=worker)
        t.start()
        _pending_threads.append(t)
    
    # Register to spawn later, but it will happen
    spawn_later()
    return "ok"


# === Recursive/Nested Escapes ===

def spawn_threads_recursively(_input_data, depth=0):
    """Recursively spawn threads - hard to track call stack"""
    if depth >= 2:
        return "ok"
    
    def worker():
        time.sleep(1)
    
    thread = threading.Thread(target=worker)
    thread.start()
    
    # Recursive call
    spawn_threads_recursively(_input_data, depth + 1)
    return "ok"


# === Cleanup with Exceptions ===

def spawn_thread_interrupt_cleanup(_input_data):
    """Spawn thread and fail to join due to exception"""
    def worker():
        time.sleep(2)
    
    thread = threading.Thread(target=worker)
    thread.start()
    
    try:
        thread.join(timeout=0.01)
        if not thread.is_alive():
            raise RuntimeError("Thread died unexpectedly")
    except RuntimeError:
        pass  # Thread still running but we return
    
    return "ok"


# === Thread Local Storage Escapes ===

_local = threading.local()

def spawn_thread_with_local_storage(_input_data):
    """Spawn thread that uses thread-local storage"""
    def worker():
        _local.data = str(_input_data) * 1000  # Store large object
        time.sleep(2)
    
    thread = threading.Thread(target=worker)
    thread.start()
    # Thread not joined, local storage persists
    return "ok"


# === False Negative Cases (Should NOT detect as escape) ===

def properly_joined_thread(_input_data):
    """This should NOT be flagged - thread is properly cleaned up"""
    def worker():
        time.sleep(0.05)
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    return "ok"


def properly_shutdown_executor(_input_data):
    """This should NOT be flagged - executor properly shutdown"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(time.sleep, 0.05)
        future.result()
    return "ok"


def daemon_thread_cleanup(_input_data):
    """Daemon thread - should be OK since it gets cleaned up on exit"""
    def worker():
        time.sleep(0.05)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return "ok"
