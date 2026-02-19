"""Sneaky escape patterns that exploit edge cases in the detection mechanism.

The detector snapshots threads/processes ~0.5s after the target function returns.
These tests use timing, naming, indirection, and other tricks to make detection
harder — while still containing genuine escapes.
"""
import threading
import multiprocessing as mp
import time
import os
import sys
import ctypes
import signal
import importlib
import types
import gc


# ============================================================================
# DELAYED SPAWN — thread appears AFTER the 0.5s detection window
# The function installs a "detonator" daemon that waits, then spawns a
# non-daemon thread. The detector might miss it if it only checks once.
# ============================================================================

def delayed_spawn_after_window(_input_data):
    """A daemon thread spawns a non-daemon thread after the detection window."""
    def detonator():
        time.sleep(0.8)  # After the 0.5s snapshot window
        def lingering():
            time.sleep(2)
        threading.Thread(target=lingering, name="late-arrival", daemon=False).start()

    # Daemon threads aren't themselves an escape, but they spawn one
    threading.Thread(target=detonator, daemon=True).start()
    return "clean_return"


# ============================================================================
# THREAD NAME MIMICRY — thread names itself like a Python internal
# ============================================================================

def thread_name_mimicry(_input_data):
    """Leaked thread names itself like a CPython internal thread."""
    def work():
        time.sleep(2)

    # Name that looks like it belongs to the runtime
    t = threading.Thread(target=work, name="pydevd.Reader", daemon=False)
    t.start()
    return "started"


# ============================================================================
# SELF-RESTARTING THREAD — completes, but spawns a replacement before dying
# ============================================================================

def self_restarting_thread(_input_data):
    """Thread finishes its work, then starts a successor before exiting."""
    gen = [0]

    def worker(generation):
        time.sleep(0.1)
        gen[0] = generation
        if generation < 3:
            threading.Thread(target=worker, args=(generation + 1,),
                             name=f"worker-gen{generation+1}", daemon=False).start()

    threading.Thread(target=worker, args=(0,), name="worker-gen0", daemon=False).start()
    return f"started generation chain"


# ============================================================================
# THREAD HIDDEN BEHIND A GENERATOR — escape occurs during iteration
# ============================================================================

def _lazy_items(data):
    """Generator that spawns a prefetch thread mid-iteration."""
    items = data.split(",") if data else ["a", "b", "c"]
    for i, item in enumerate(items):
        if i == 1:
            # Prefetch remaining items in background
            def prefetch():
                time.sleep(3)
            threading.Thread(target=prefetch, name="gen-prefetch", daemon=False).start()
        yield item.strip()


def generator_hidden_thread(_input_data):
    """Iterate a generator that sneaks in a thread spawn mid-yield."""
    results = list(_lazy_items(_input_data))
    return ",".join(results)


# ============================================================================
# ESCAPE VIA __del__ ON GARBAGE COLLECTION
# Object starts a thread in its finalizer when it goes out of scope.
# ============================================================================

class _CleanupResource:
    def __init__(self, data):
        self.data = data

    def __del__(self):
        def cleanup_work():
            time.sleep(3)
        threading.Thread(target=cleanup_work, name="gc-cleanup", daemon=False).start()


def gc_triggered_escape(_input_data):
    """Object's __del__ spawns a thread when it gets collected."""
    resource = _CleanupResource(_input_data)
    _ = resource.data  # Use it
    del resource        # Trigger __del__
    gc.collect()        # Force collection
    return "resource_released"


# ============================================================================
# ESCAPE VIA CLASS DESCRIPTOR (__set__)
# Setting an attribute spawns a background validator thread.
# ============================================================================

class _ValidatedField:
    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __set__(self, instance, value):
        setattr(instance, self._name, value)
        # Background async validation — thread escapes
        def validate():
            time.sleep(2)
        threading.Thread(target=validate, name="field-validator", daemon=False).start()

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self._name, None)


class _Config:
    api_key = _ValidatedField()

    def __init__(self, key):
        self.api_key = key  # Triggers __set__, which spawns a thread


def descriptor_escape(_input_data):
    """Assigning to a descriptor field spawns a validation thread."""
    cfg = _Config(_input_data or "secret-key")
    return f"config={cfg.api_key}"


# ============================================================================
# ESCAPE VIA CONTEXT VARIABLE / threading.local()
# Storing a value in thread-local triggers a background sync thread.
# ============================================================================

_local_store = threading.local()


def _sync_to_central():
    time.sleep(2)


def thread_local_escape(_input_data):
    """Storing a thread-local value starts a background sync."""
    _local_store.user = _input_data
    _local_store.session = "abc123"
    # Sync the local store to some central place in background
    threading.Thread(target=_sync_to_central, name="tls-sync", daemon=False).start()
    return f"user={_local_store.user}"


# ============================================================================
# PROCESS ESCAPE VIA DOUBLE FORK
# A child process forks a grandchild, then the child exits. The grandchild
# is reparented to init, making it hard to track.
# ============================================================================

def _double_fork_worker():
    """Child forks a grandchild, then exits. Grandchild lingers."""
    pid = os.fork()
    if pid == 0:
        # Grandchild — hangs around
        time.sleep(2)
        os._exit(0)
    else:
        # Child — exits immediately, orphaning the grandchild
        os._exit(0)


def double_fork_escape(_input_data):
    """Classic double-fork. Grandchild is reparented to init."""
    p = mp.Process(target=_double_fork_worker)
    p.start()
    p.join(timeout=1)  # Child exits fast
    return "child_exited"


# ============================================================================
# THREAD POOL WITH submit() AFTER shutdown(cancel_futures=False)
# Python 3.9+ allows pending futures to complete even after shutdown.
# ============================================================================

def pool_submit_then_shutdown(_input_data):
    """Submit long tasks, then shutdown(wait=False). Workers still alive."""
    from concurrent.futures import ThreadPoolExecutor

    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tricky")
    # Submit work that takes a while
    pool.submit(time.sleep, 2)
    # Non-blocking shutdown — thread stays alive
    pool.shutdown(wait=False)
    return "pool_dead_right?_wrong"


# ============================================================================
# ESCAPE VIA FUNCTOOLS.PARTIAL + MAP IN THREAD
# The thread is created through composition that obscures the source.
# ============================================================================

def composed_thread_escape(_input_data):
    """Thread is created via functools.partial composition."""
    import functools

    sleeper = functools.partial(time.sleep, 2)
    t = threading.Thread(target=sleeper, name="partial-thread", daemon=False)
    t.start()
    return "composed"


# ============================================================================
# ESCAPE VIA MONKEY-PATCHED METHOD
# An object's method is replaced at runtime; the replacement spawns threads.
# ============================================================================

class _SafeProcessor:
    """Looks safe — process() is synchronous."""
    def process(self, data):
        return data.upper()


def monkey_patched_escape(_input_data):
    """Monkey-patch a safe method to spawn threads."""
    processor = _SafeProcessor()

    original = processor.process

    def patched_process(data):
        result = original(data)
        # Also kick off background indexing
        threading.Thread(target=lambda: time.sleep(3), name="bg-index", daemon=False).start()
        return result

    processor.process = patched_process
    result = processor.process(_input_data or "test")
    return result


# ============================================================================
# ESCAPE HIDDEN IN EXCEPTION HANDLER
# The happy path is clean; the thread only spawns on exception.
# ============================================================================

def exception_handler_escape(_input_data):
    """Thread escapes only in the error-handling path."""
    def fallback_recovery():
        time.sleep(3)

    try:
        # Deliberately trigger an error
        result = int(_input_data or "not_a_number")
        return str(result)
    except (ValueError, TypeError):
        # Recovery thread escapes
        threading.Thread(target=fallback_recovery, name="recovery", daemon=False).start()
        return "error_recovery_started"


# ============================================================================
# CHAINED CALLBACKS THAT EVENTUALLY SPAWN A THREAD
# Each callback looks harmless; the escape is 3 levels deep.
# ============================================================================

def chained_callback_escape(_input_data):
    """Chain of callbacks where the last one spawns a thread."""
    def step1(data, next_cb):
        next_cb(data.lower())

    def step2(data, next_cb):
        next_cb(data.strip())

    def step3(data):
        # The actual escape, buried in the chain
        threading.Thread(target=lambda: time.sleep(3), name="chained",
                         daemon=False).start()

    step1(_input_data or "HELLO", lambda d: step2(d, step3))
    return "chain_complete"


# ============================================================================
# IMPLICIT ESCAPE VIA collections.abc HOOK
# An object that spawns threads in __len__ or __iter__
# ============================================================================

class _SneakyList:
    """List-like that prefetches more data on len() call."""
    def __init__(self, data):
        self._items = list(data)

    def __len__(self):
        # Prefetch — thread escapes
        threading.Thread(target=lambda: time.sleep(3), name="prefetch-len",
                         daemon=False).start()
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]


def dunder_len_escape(_input_data):
    """Calling len() on a custom object leaks a thread."""
    items = _SneakyList((_input_data or "a,b,c").split(","))
    count = len(items)
    return f"count={count}"


# ============================================================================
# ESCAPE VIA TIMER THAT RESCHEDULES ITSELF
# A threading.Timer that, when it fires, schedules another timer.
# ============================================================================

def self_scheduling_timer(_input_data):
    """Timer reschedules itself on fire — creates an infinite timer chain."""
    counter = [0]

    def tick():
        counter[0] += 1
        if counter[0] < 10:
            t = threading.Timer(0.5, tick)
            t.name = f"tick-{counter[0]}"
            t.daemon = False
            t.start()

    first = threading.Timer(0.1, tick)
    first.name = "tick-0"
    first.daemon = False
    first.start()
    return f"timer_chain_started"


# ============================================================================
# ESCAPE VIA __init_subclass__
# Defining a subclass triggers a background thread in the parent.
# ============================================================================

class _PluginBase:
    _registry = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _PluginBase._registry.append(cls)
        # Background registration — thread escapes
        threading.Thread(target=lambda: time.sleep(3), name="plugin-register",
                         daemon=False).start()


def init_subclass_escape(_input_data):
    """Defining a class triggers a background thread via __init_subclass__."""
    # Creating this class definition triggers the metaclass hook
    class UserPlugin(_PluginBase):
        name = _input_data or "my_plugin"

    return f"registered={len(_PluginBase._registry)} plugins"


# ============================================================================
# ESCAPE VIA WEAKREF CALLBACK
# When an object is garbage-collected, a weak reference callback fires
# and spawns a thread.
# ============================================================================

def weakref_finalize_escape(_input_data):
    """Weak reference callback spawns a thread on object deletion."""
    import weakref

    class Resource:
        pass

    def on_destroy(ref):
        threading.Thread(target=lambda: time.sleep(3), name="weak-cleanup",
                         daemon=False).start()

    obj = Resource()
    ref = weakref.ref(obj, on_destroy)
    del obj  # Triggers callback
    gc.collect()
    return "ref_dead"


# ============================================================================
# NON-ESCAPE DECOYS — functions that LOOK like they leak but don't
# ============================================================================

def daemon_only_no_escape(_input_data):
    """Starts daemon threads which don't count as escapes."""
    for i in range(3):
        threading.Thread(target=lambda: time.sleep(2), daemon=True,
                         name=f"daemon-{i}").start()
    return "all_daemons"


def joined_thread_no_escape(_input_data):
    """Thread is fully joined before return — no escape."""
    def quick_work():
        time.sleep(0.05)

    t = threading.Thread(target=quick_work)
    t.start()
    t.join()  # Properly waited
    return "joined"


def completed_thread_no_escape(_input_data):
    """Thread finishes before the function returns — no escape."""
    result = [None]

    def instant():
        result[0] = "done"

    t = threading.Thread(target=instant)
    t.start()
    time.sleep(0.1)  # Give it time to finish
    t.join(timeout=0.5)
    return result[0]
