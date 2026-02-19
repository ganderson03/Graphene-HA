"""Comprehensive escape patterns - expanded test suite for advanced detection"""
import threading
import multiprocessing as mp
import time
import functools
import atexit
import signal
import weakref
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import contextmanager
import sys


# ============================================================================
# EXTERNAL MODULE ESCAPES - Using library functions
# ============================================================================

def escape_via_concurrent_map(_input_data):
    """Escape by using concurrent.futures.map without proper cleanup"""
    def worker(x):
        time.sleep(2)
        return x * 2
    
    executor = ThreadPoolExecutor(max_workers=2)
    # Never shut down executor - threads escape
    list(executor.map(worker, [1, 2, 3]))
    return "ok"


def escape_thread_in_decorator(_input_data):
    """Thread spawned via decorator"""
    def spawn_thread_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t = threading.Thread(target=lambda: time.sleep(2))
            t.start()
            return func(*args, **kwargs)
        return wrapper
    
    @spawn_thread_decorator
    def my_func():
        return "result"
    
    return my_func()


def escape_thread_in_context_manager(_input_data):
    """Thread spawned in context manager __enter__"""
    @contextmanager
    def thread_spawning_context():
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
        try:
            yield
        finally:
            pass  # Deliberately not joined
    
    with thread_spawning_context():
        pass
    return "ok"


# ============================================================================
# METACLASS ESCAPES - Threads spawned in metaclass methods
# ============================================================================

class ThreadSpawningMeta(type):
    """Metaclass that spawns threads"""
    def __new__(mcs, name, bases, dct):
        if name == "LeakyServiceClass":
            t = threading.Thread(target=lambda: time.sleep(2))
            t.start()  # Escape in metaclass initialization
        return super().__new__(mcs, name, bases, dct)


def escape_via_metaclass(_input_data):
    """Create class with thread-spawning metaclass"""
    class LeakyServiceClass(metaclass=ThreadSpawningMeta):
        pass
    
    return "ok"


# ============================================================================
# CLOSURE & STATE ESCAPES - Threads stored in closures and shared state
# ============================================================================

_global_threads = []  # Global registry


def escape_via_global_registry(_input_data):
    """Store thread references in global state"""
    def worker():
        time.sleep(2)
    
    t = threading.Thread(target=worker)
    _global_threads.append(t)  # Stored but never joined
    t.start()
    
    return "ok"


def escape_via_closure_capture(_input_data):
    """Thread captured in closure, stored globally"""
    def create_escaped_closure():
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
        
        def get_thread():
            return t
        
        return get_thread
    
    closure_func = create_escaped_closure()
    # Thread is captured in closure, never accessed/joined
    return "ok"


# ============================================================================
# SPECIAL METHOD ESCAPES - __del__, __getattr__, property setters
# ============================================================================

def escape_via_del_method(_input_data):
    """Thread spawn triggered by __del__"""
    class LeakyObject:
        def __del__(self):
            t = threading.Thread(target=lambda: time.sleep(2))
            t.start()
    
    obj = LeakyObject()
    del obj  # Triggers __del__, spawns untracked thread
    return "ok"


def escape_via_property_setter(_input_data):
    """Thread spawned in property setter"""
    class LeakyClass:
        def __init__(self):
            self._value = None
        
        @property
        def value(self):
            return self._value
        
        @value.setter
        def value(self, val):
            t = threading.Thread(target=lambda: time.sleep(2))
            t.start()
            self._value = val
    
    obj = LeakyClass()
    obj.value = 42  # Triggers setter, spawns thread
    return "ok"


# ============================================================================
# WEAK REFERENCE ESCAPES - Escapes via weak references and finalization
# ============================================================================

def escape_via_weakref_callback(_input_data):
    """Thread spawned in weakref callback"""
    def callback(ref):
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
    
    class DummyObject:
        pass
    
    obj = DummyObject()
    weakref.ref(obj, callback)
    del obj  # Triggers callback, spawns thread
    return "ok"


# ============================================================================
# EXCEPTION HANDLING ESCAPES
# ============================================================================

def escape_in_exception_handler(_input_data):
    """Thread escape in except block"""
    try:
        raise ValueError("trigger exception")
    except ValueError:
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
    
    return "ok"


def escape_via_finally_block(_input_data):
    """Thread escape in finally block"""
    try:
        pass
    finally:
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
    
    return "ok"


# ============================================================================
# ATEXIT & SIGNAL HANDLER ESCAPES
# ============================================================================

def escape_via_atexit(_input_data):
    """Register atexit handler that spawns thread"""
    def exit_handler():
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
    
    atexit.register(exit_handler)
    return "ok"


# ============================================================================
# CONDITIONAL & DYNAMIC ESCAPES - Hard-to-analyze patterns
# ============================================================================

def escape_via_dynamic_import(_input_data):
    """Import and execute code that spawns threads"""
    import importlib
    import threading as threading_module
    
    # Get Thread class dynamically
    Thread = getattr(threading_module, 'Thread')
    t = Thread(target=lambda: time.sleep(2))
    t.start()
    return "ok"


def escape_with_random_condition(_input_data):
    """Escape only under certain conditions"""
    import random
    
    if random.random() > 0.0:  # Always true, but hard to analyze statically
        t = threading.Thread(target=lambda: time.sleep(2))
        t.start()
    
    return "ok"


def escape_via_variable_indirection(_input_data):
    """Spawn thread via indirection through variables"""
    thread_class = threading.Thread
    worker_func = lambda: time.sleep(2)
    t = thread_class(target=worker_func)
    t.start()
    return "ok"


# ============================================================================
# MULTI-LAYER ESCAPES - Complex nesting and indirection
# ============================================================================

def escape_via_multiple_indirections(_input_data):
    """Thread escape through multiple levels of indirection"""
    def create_factory():
        def factory():
            def create_thread():
                def worker():
                    time.sleep(2)
                return threading.Thread(target=worker)
            return create_thread()
        return factory()
    
    thread = create_factory()
    thread.start()
    return "ok"


def escape_via_nested_context(_input_data):
    """Escape through nested context managers"""
    @contextmanager
    def outer_context():
        @contextmanager
        def inner_context():
            t = threading.Thread(target=lambda: time.sleep(2))
            t.start()
            yield
        with inner_context():
            yield
    
    with outer_context():
        pass
    
    return "ok"


# ============================================================================
# PROCESS ESCAPES - Multiprocessing variants
# ============================================================================

def _mp_worker():
    time.sleep(2)


def escape_via_process_pool(_input_data):
    """Escape via ProcessPoolExecutor without shutdown"""
    pool = ProcessPoolExecutor(max_workers=2)
    futures = [pool.submit(_mp_worker) for _ in range(2)]
    # Never shut down or wait for completion
    return "ok"


def escape_via_process_context(_input_data):
    """Start process in context manager without proper cleanup"""
    p = mp.Process(target=_mp_worker)
    p.start()
    # Exit function without joining - process escapes
    return "ok"


def escape_multiple_processes_partial(_input_data):
    """Start multiple processes but only partially join"""
    processes = [mp.Process(target=_mp_worker) for _ in range(3)]
    for p in processes:
        p.start()
    # Only join first process
    if processes:
        processes[0].join()
    # Others escape
    return "ok"


# ============================================================================
# EXECUTOR ESCAPES - ThreadPoolExecutor/ProcessPoolExecutor variants
# ============================================================================

def escape_executor_with_active_tasks(_input_data):
    """Executor with tasks that don't complete"""
    executor = ThreadPoolExecutor(max_workers=2)
    
    def slow_worker():
        time.sleep(5)
    
    # Submit tasks but don't wait for them
    for _ in range(3):
        executor.submit(slow_worker)
    
    # Exit without shutdown
    return "ok"


def escape_executor_via_map(_input_data):
    """Executor.map without consuming results"""
    executor = ThreadPoolExecutor(max_workers=2)
    
    def worker(x):
        time.sleep(2)
        return x
    
    # Create iterator but never consume it
    result_iterator = executor.map(worker, [1, 2, 3])
    # Exit without consuming or shutdown
    return "ok"


def escape_nested_executors(_input_data):
    """Nested executor submission"""
    outer_executor = ThreadPoolExecutor(max_workers=2)
    
    def submit_inner():
        inner_executor = ThreadPoolExecutor(max_workers=2)
        inner_executor.submit(lambda: time.sleep(2))
        # Both executors leak
    
    outer_executor.submit(submit_inner)
    # Outer executor also leaks
    return "ok"


# ============================================================================
# TRICKY NON-ESCAPES - Legitimate code that might look like escapes
# ============================================================================

def thread_with_immediate_join(_input_data):
    """Thread that joins before return"""
    t = threading.Thread(target=lambda: time.sleep(0.1))
    t.start()
    t.join()  # Properly joined
    return "ok"


def thread_via_context_manager_proper(_input_data):
    """Proper thread management via context"""
    @contextmanager
    def managed_thread():
        t = threading.Thread(target=lambda: time.sleep(0.1))
        t.start()
        try:
            yield
        finally:
            t.join()  # Properly joined in finally
    
    with managed_thread():
        pass
    return "ok"


def executor_with_context_proper(_input_data):
    """Executor properly managed with context manager"""
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(lambda: time.sleep(0.1))
        # Context manager ensures proper shutdown
    return "ok"


def exception_safely_joins_thread(_input_data):
    """Thread that gets joined even on exception"""
    t = threading.Thread(target=lambda: time.sleep(0.1))
    t.start()
    try:
        pass
    finally:
        t.join()  # Properly joined in finally
    return "ok"


def process_properly_joined(_input_data):
    """Process that is properly joined"""
    p = mp.Process(target=_mp_worker)
    p.start()
    p.join()  # Properly waited
    return "ok"
