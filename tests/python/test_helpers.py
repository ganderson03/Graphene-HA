"""Common helpers for Python concurrency escape tests"""
import threading
import time


def spawn_worker(daemon=False, delay=2):
    """Spawn a thread with given parameters"""
    def worker():
        time.sleep(delay)
    thread = threading.Thread(target=worker, daemon=daemon)
    thread.start()
    return "ok"


def spawn_named_worker(name="worker", delay=2):
    """Spawn a named thread"""
    def worker():
        time.sleep(delay)
    thread = threading.Thread(target=worker, name=name)
    thread.start()
    return "ok"


def spawn_timer(interval=2.0):
    """Spawn a timer"""
    timer = threading.Timer(interval, lambda: None)
    timer.start()
    return "ok"


def spawn_multiple_workers(count=3, delay=2):
    """Spawn multiple threads"""
    def worker():
        time.sleep(delay)
    threads = [threading.Thread(target=worker) for _ in range(count)]
    for t in threads:
        t.start()
    return "ok"


def spawn_nested_workers(delay=2):
    """Spawn nested threads"""
    def inner_worker():
        time.sleep(delay)
    def worker():
        inner = threading.Thread(target=inner_worker)
        inner.start()
        time.sleep(delay)
    thread = threading.Thread(target=worker)
    thread.start()
    return "ok"


def spawn_event_waiter(delay=2):
    """Spawn thread waiting on event"""
    event = threading.Event()
    def worker():
        event.wait()
    thread = threading.Thread(target=worker)
    thread.start()
    return "ok"


def join_worker(delay=0.1):
    """Spawn and join thread"""
    def worker():
        time.sleep(delay)
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    return "ok"


def join_daemon_worker(delay=0.1):
    """Spawn, join daemon thread"""
    def worker():
        time.sleep(delay)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join()
    return "ok"


def join_multiple_workers(count=3, delay=0.1):
    """Spawn and join multiple threads"""
    def worker():
        time.sleep(delay)
    threads = [threading.Thread(target=worker) for _ in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return "ok"


def cancel_timer(interval=0.5):
    """Spawn, cancel timer"""
    timer = threading.Timer(interval, lambda: None)
    timer.start()
    timer.cancel()
    timer.join()
    return "ok"

